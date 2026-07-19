#!/usr/bin/env python3
import argparse
import struct
from pathlib import Path


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


def parse_bundle(bundle: bytes) -> tuple[list[tuple[str, int, int]], bytes]:
    signature, offset = read_cstring(bundle, 0)
    if signature != "UnityFS":
        raise ValueError(f"unexpected signature: {signature}")

    format_version = struct.unpack_from(">I", bundle, offset)[0]
    offset += 4
    _, offset = read_cstring(bundle, offset)
    _, offset = read_cstring(bundle, offset)

    bundle_size, compressed_info_size, uncompressed_info_size, flags = (
        struct.unpack_from(">QIII", bundle, offset)
    )
    offset += 20

    if bundle_size != len(bundle):
        raise ValueError(f"bundle size mismatch: header={bundle_size}, file={len(bundle)}")
    if flags & 0x80:
        raise ValueError("blocks info at end is not supported by this verifier")
    if format_version >= 7:
        offset = align(offset, 16)

    compressed_info = bundle[offset : offset + compressed_info_size]
    info = decompress_by_mode(
        compressed_info, uncompressed_info_size, flags & 0x3F
    )
    offset += compressed_info_size
    if flags & 0x200:
        offset = align(offset, 16)

    info_offset = 16
    block_count = struct.unpack_from(">I", info, info_offset)[0]
    info_offset += 4
    block_records: list[tuple[int, int, int]] = []
    for _ in range(block_count):
        uncompressed_size, compressed_size, block_flags = struct.unpack_from(
            ">IIH", info, info_offset
        )
        info_offset += 10
        block_records.append((uncompressed_size, compressed_size, block_flags))

    node_count = struct.unpack_from(">I", info, info_offset)[0]
    info_offset += 4
    nodes: list[tuple[str, int, int]] = []
    for _ in range(node_count):
        node_offset, node_size, _ = struct.unpack_from(">QQI", info, info_offset)
        info_offset += 20
        path, info_offset = read_cstring(info, info_offset)
        nodes.append((path, node_offset, node_size))

    uncompressed_data = bytearray()
    for uncompressed_size, compressed_size, block_flags in block_records:
        compressed_block = bundle[offset : offset + compressed_size]
        offset += compressed_size
        uncompressed_data.extend(
            decompress_by_mode(
                compressed_block, uncompressed_size, block_flags & 0x3F
            )
        )

    return nodes, bytes(uncompressed_data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument(
        "--needle",
        action="append",
        default=["5.0.1", "5.1.0"],
        help="ASCII value to locate; may be specified more than once",
    )
    parser.add_argument(
        "--compare",
        type=Path,
        help="decompress a second UnityFS file and report every changed output byte",
    )
    args = parser.parse_args()

    nodes, data = parse_bundle(args.bundle.read_bytes())
    found = 0
    for path, node_offset, node_size in nodes:
        node = data[node_offset : node_offset + node_size]
        for needle_text in args.needle:
            needle = needle_text.encode("utf-8")
            position = node.find(needle)
            while position != -1:
                print(
                    f"{path}: node_offset=0x{position:X} "
                    f"bundle_data_offset=0x{node_offset + position:X} "
                    f"value={needle_text}"
                )
                found += 1
                position = node.find(needle, position + 1)

    if found == 0:
        raise SystemExit("no requested version strings found")

    if args.compare:
        other_nodes, other_data = parse_bundle(args.compare.read_bytes())
        if nodes != other_nodes:
            raise SystemExit("UnityFS node tables differ")
        if len(data) != len(other_data):
            raise SystemExit(
                f"uncompressed data sizes differ: {len(data)} != {len(other_data)}"
            )

        differences = [
            (index, before, after)
            for index, (before, after) in enumerate(zip(data, other_data))
            if before != after
        ]
        print(f"uncompressed_changed_bytes={len(differences)}")
        for index, before, after in differences[:64]:
            print(f"0x{index:X}: 0x{before:02X} -> 0x{after:02X}")


if __name__ == "__main__":
    main()
