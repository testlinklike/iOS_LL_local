#!/usr/bin/env python3
import argparse
import ctypes
import struct
from dataclasses import dataclass
from pathlib import Path


LZ4_LIBRARY = Path("/opt/homebrew/opt/lz4/lib/liblz4.dylib")


@dataclass
class Block:
    uncompressed_size: int
    compressed_size: int
    flags: int
    info_record_offset: int
    data_offset: int


@dataclass
class UnityFS:
    blob: bytes
    format_version: int
    bundle_size_offset: int
    compressed_info_size_offset: int
    flags: int
    info_start: int
    compressed_info_size: int
    uncompressed_info_size: int
    info: bytes
    blocks: list[Block]
    nodes: list[tuple[str, int, int]]
    blocks_end: int


def read_cstring(data: bytes, offset: int) -> tuple[str, int]:
    end = data.index(0, offset)
    return data[offset:end].decode("utf-8"), end + 1


def align(value: int, alignment: int) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def decompress_lz4_block(data: bytes, expected_size: int) -> bytes:
    source = 0
    output = bytearray()

    while source < len(data):
        token = data[source]
        source += 1

        literal_length = token >> 4
        if literal_length == 15:
            while True:
                value = data[source]
                source += 1
                literal_length += value
                if value != 255:
                    break

        literal_end = source + literal_length
        if literal_end > len(data):
            raise ValueError("LZ4 literal exceeds source block")
        output.extend(data[source:literal_end])
        source = literal_end

        if source == len(data):
            break
        if source + 2 > len(data):
            raise ValueError("truncated LZ4 match offset")

        match_offset = data[source] | (data[source + 1] << 8)
        source += 2
        if match_offset == 0 or match_offset > len(output):
            raise ValueError("invalid LZ4 match offset")

        match_length = token & 0x0F
        if match_length == 15:
            while True:
                value = data[source]
                source += 1
                match_length += value
                if value != 255:
                    break
        match_length += 4

        match_start = len(output) - match_offset
        for index in range(match_length):
            output.append(output[match_start + index])

    if len(output) != expected_size:
        raise ValueError(
            f"LZ4 size mismatch: expected {expected_size}, got {len(output)}"
        )
    return bytes(output)


def decompress_by_mode(data: bytes, expected_size: int, mode: int) -> bytes:
    if mode == 0:
        if len(data) != expected_size:
            raise ValueError(
                f"uncompressed size mismatch: expected {expected_size}, got {len(data)}"
            )
        return data
    if mode in (2, 3):
        return decompress_lz4_block(data, expected_size)
    raise ValueError(f"unsupported UnityFS compression mode: {mode}")


def lz4_library() -> ctypes.CDLL:
    if not LZ4_LIBRARY.is_file():
        raise FileNotFoundError(f"required LZ4 library not found: {LZ4_LIBRARY}")
    library = ctypes.CDLL(str(LZ4_LIBRARY))
    library.LZ4_compressBound.argtypes = [ctypes.c_int]
    library.LZ4_compressBound.restype = ctypes.c_int
    library.LZ4_compress_default.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
    ]
    library.LZ4_compress_default.restype = ctypes.c_int
    library.LZ4_compress_HC.argtypes = [
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
    ]
    library.LZ4_compress_HC.restype = ctypes.c_int
    return library


def compress_by_mode(data: bytes, mode: int, library: ctypes.CDLL) -> bytes:
    if mode == 0:
        return data
    if mode not in (2, 3):
        raise ValueError(f"unsupported UnityFS compression mode: {mode}")

    source = ctypes.create_string_buffer(data)
    capacity = library.LZ4_compressBound(len(data))
    destination = ctypes.create_string_buffer(capacity)

    if mode == 2:
        compressed_size = library.LZ4_compress_default(
            source, destination, len(data), capacity
        )
    else:
        compressed_size = library.LZ4_compress_HC(
            source, destination, len(data), capacity, 9
        )

    if compressed_size <= 0:
        raise ValueError("liblz4 failed to compress a UnityFS block")
    return destination.raw[:compressed_size]


def parse_unityfs(blob: bytes) -> UnityFS:
    signature, offset = read_cstring(blob, 0)
    if signature != "UnityFS":
        raise ValueError(f"unexpected signature: {signature}")

    format_version = struct.unpack_from(">I", blob, offset)[0]
    offset += 4
    _, offset = read_cstring(blob, offset)
    _, offset = read_cstring(blob, offset)

    bundle_size_offset = offset
    bundle_size, compressed_info_size, uncompressed_info_size, flags = (
        struct.unpack_from(">QIII", blob, offset)
    )
    compressed_info_size_offset = offset + 8
    offset += 20

    if bundle_size != len(blob):
        raise ValueError(f"bundle size mismatch: header={bundle_size}, file={len(blob)}")
    if flags & 0x80:
        raise ValueError("blocks info at end is not supported")
    if format_version >= 7:
        offset = align(offset, 16)

    info_start = offset
    compressed_info = blob[info_start : info_start + compressed_info_size]
    info = decompress_by_mode(
        compressed_info, uncompressed_info_size, flags & 0x3F
    )

    data_offset = info_start + compressed_info_size
    if flags & 0x200:
        data_offset = align(data_offset, 16)

    info_offset = 16
    block_count = struct.unpack_from(">I", info, info_offset)[0]
    info_offset += 4
    block_records: list[tuple[int, int, int, int]] = []
    for _ in range(block_count):
        record_offset = info_offset
        uncompressed_size, compressed_size, block_flags = struct.unpack_from(
            ">IIH", info, info_offset
        )
        info_offset += 10
        block_records.append(
            (uncompressed_size, compressed_size, block_flags, record_offset)
        )

    node_count = struct.unpack_from(">I", info, info_offset)[0]
    info_offset += 4
    nodes: list[tuple[str, int, int]] = []
    for _ in range(node_count):
        node_offset, node_size, _ = struct.unpack_from(">QQI", info, info_offset)
        info_offset += 20
        path, info_offset = read_cstring(info, info_offset)
        nodes.append((path, node_offset, node_size))

    blocks: list[Block] = []
    for uncompressed_size, compressed_size, block_flags, record_offset in block_records:
        blocks.append(
            Block(
                uncompressed_size=uncompressed_size,
                compressed_size=compressed_size,
                flags=block_flags,
                info_record_offset=record_offset,
                data_offset=data_offset,
            )
        )
        data_offset += compressed_size

    return UnityFS(
        blob=blob,
        format_version=format_version,
        bundle_size_offset=bundle_size_offset,
        compressed_info_size_offset=compressed_info_size_offset,
        flags=flags,
        info_start=info_start,
        compressed_info_size=compressed_info_size,
        uncompressed_info_size=uncompressed_info_size,
        info=info,
        blocks=blocks,
        nodes=nodes,
        blocks_end=data_offset,
    )


def rewrite_version(bundle: UnityFS, old: bytes, new: bytes) -> bytes:
    if len(old) != len(new):
        raise ValueError("old and new versions must have equal byte lengths")
    if not bundle.blocks:
        raise ValueError("UnityFS contains no data blocks")

    globalgamemanagers = [
        node for node in bundle.nodes if node[0] == "globalgamemanagers"
    ]
    if len(globalgamemanagers) != 1:
        raise ValueError("expected exactly one globalgamemanagers node")

    first = bundle.blocks[0]
    compressed_first = bundle.blob[
        first.data_offset : first.data_offset + first.compressed_size
    ]
    original_first = decompress_by_mode(
        compressed_first, first.uncompressed_size, first.flags & 0x3F
    )

    path, node_offset, node_size = globalgamemanagers[0]
    node_end_in_first = min(node_offset + node_size, len(original_first))
    node_in_first = original_first[node_offset:node_end_in_first]
    if node_in_first.count(old) != 1 or node_in_first.count(new) != 0:
        raise ValueError(
            f"unexpected {path} version counts: "
            f"old={node_in_first.count(old)} new={node_in_first.count(new)}"
        )

    version_offset = node_offset + node_in_first.index(old)
    modified_first = bytearray(original_first)
    modified_first[version_offset : version_offset + len(old)] = new

    differences = [
        index
        for index, (before, after) in enumerate(zip(original_first, modified_first))
        if before != after
    ]
    expected_differences = [
        version_offset + index
        for index, (before, after) in enumerate(zip(old, new))
        if before != after
    ]
    if differences != expected_differences:
        raise ValueError("unexpected uncompressed changes before recompression")

    library = lz4_library()
    new_compressed_first = compress_by_mode(
        bytes(modified_first), first.flags & 0x3F, library
    )

    new_info = bytearray(bundle.info)
    struct.pack_into(
        ">I",
        new_info,
        first.info_record_offset + 4,
        len(new_compressed_first),
    )
    new_compressed_info = compress_by_mode(
        bytes(new_info), bundle.flags & 0x3F, library
    )

    prefix = bytearray(bundle.blob[: bundle.info_start])
    struct.pack_into(
        ">I",
        prefix,
        bundle.compressed_info_size_offset,
        len(new_compressed_info),
    )

    padding_size = 0
    if bundle.flags & 0x200:
        padding_size = align(
            len(prefix) + len(new_compressed_info), 16
        ) - (len(prefix) + len(new_compressed_info))

    remaining_blocks_start = first.data_offset + first.compressed_size
    remaining_blocks = bundle.blob[remaining_blocks_start : bundle.blocks_end]
    trailing_data = bundle.blob[bundle.blocks_end :]

    output = bytearray(prefix)
    output.extend(new_compressed_info)
    output.extend(b"\0" * padding_size)
    output.extend(new_compressed_first)
    output.extend(remaining_blocks)
    output.extend(trailing_data)
    struct.pack_into(">Q", output, bundle.bundle_size_offset, len(output))

    rewritten = parse_unityfs(bytes(output))
    rewritten_first = rewritten.blocks[0]
    rewritten_compressed_first = rewritten.blob[
        rewritten_first.data_offset :
        rewritten_first.data_offset + rewritten_first.compressed_size
    ]
    rewritten_uncompressed_first = decompress_by_mode(
        rewritten_compressed_first,
        rewritten_first.uncompressed_size,
        rewritten_first.flags & 0x3F,
    )
    rewritten_node_in_first = rewritten_uncompressed_first[
        node_offset:node_end_in_first
    ]

    if rewritten_node_in_first.count(old) != 0:
        raise ValueError("old version remains after UnityFS rewrite")
    if rewritten_node_in_first.count(new) != 1:
        raise ValueError("new version count is not one after UnityFS rewrite")

    postflight_differences = [
        index
        for index, (before, after) in enumerate(
            zip(original_first, rewritten_uncompressed_first)
        )
        if before != after
    ]
    if postflight_differences != expected_differences:
        raise ValueError(
            "UnityFS postflight found unrelated uncompressed byte changes"
        )

    print(
        f"globalgamemanagers: {old.decode()} -> {new.decode()} "
        f"at uncompressed offset 0x{version_offset:X}"
    )
    print(
        f"first compressed block: {first.compressed_size} -> "
        f"{len(new_compressed_first)} bytes"
    )
    print(
        f"compressed blocks info: {bundle.compressed_info_size} -> "
        f"{len(new_compressed_info)} bytes"
    )
    print(f"verified uncompressed changed bytes: {len(postflight_differences)}")
    return bytes(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_bundle", type=Path)
    parser.add_argument("output_bundle", type=Path)
    parser.add_argument("--from-version", default="5.0.1")
    parser.add_argument("--to-version", default="5.1.0")
    args = parser.parse_args()

    source = args.input_bundle.read_bytes()
    bundle = parse_unityfs(source)
    rewritten = rewrite_version(
        bundle,
        args.from_version.encode("utf-8"),
        args.to_version.encode("utf-8"),
    )
    args.output_bundle.write_bytes(rewritten)


if __name__ == "__main__":
    main()
