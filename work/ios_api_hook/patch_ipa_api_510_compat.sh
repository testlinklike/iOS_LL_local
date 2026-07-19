#!/bin/zsh
set -euo pipefail

spoof_resource=false
if (( $# > 0 )) && [[ $1 == '--spoof-resource-version' ]]; then
  spoof_resource=true
  shift
fi

if (( $# != 2 )); then
  print -u2 "usage: $0 [--spoof-resource-version] INPUT_IPA OUTPUT_IPA"
  exit 64
fi

script_dir=${0:A:h}
input_ipa=${1:A}
output_ipa=${2:A}

original_url='https://api.link-like-lovelive.app'
replacement_url='https://api-alfa-l4.hasu-link.club'
original_resource='R2604001'
replacement_resource='R2604100'
original_version='5.0.1'
replacement_version='5.1.0'

if (( ${#original_url} != ${#replacement_url} )); then
  print -u2 "URL lengths differ; refusing an in-place metadata edit"
  exit 65
fi

if (( ${#original_resource} != ${#replacement_resource} )); then
  print -u2 "resource-version lengths differ; refusing an in-place metadata edit"
  exit 66
fi

unityfs_rewriter="$script_dir/patch_unityfs_bundle_version.py"
if [[ ! -f $unityfs_rewriter ]]; then
  print -u2 "UnityFS version rewriter is missing: $unityfs_rewriter"
  exit 67
fi

temp_dir=$(mktemp -d "${TMPDIR:-/tmp}/linkura-api-510-compat.XXXXXX")
trap 'rm -rf "$temp_dir"' EXIT

unzip -q "$input_ipa" -d "$temp_dir"

metadata_files=("$temp_dir"/Payload/*.app/Data/Managed/Metadata/global-metadata.dat(N))
data_bundles=("$temp_dir"/Payload/*.app/Data/data.unity3d(N))
info_plists=("$temp_dir"/Payload/*.app/Info.plist(N))

if (( ${#metadata_files} != 1 )); then
  print -u2 "expected exactly one global-metadata.dat"
  exit 68
fi

if (( ${#data_bundles} != 1 )); then
  print -u2 "expected exactly one Data/data.unity3d"
  exit 69
fi

if (( ${#info_plists} != 1 )); then
  print -u2 "expected exactly one main-app Info.plist"
  exit 70
fi

metadata=${metadata_files[1]}
data_bundle=${data_bundles[1]}
info_plist=${info_plists[1]}

count_occurrences() {
  local needle=$1
  local file=$2
  (LC_ALL=C grep -aoF "$needle" "$file" || true) | wc -l | tr -d ' '
}

original_url_count=$(count_occurrences "$original_url" "$metadata")
replacement_url_count=$(count_occurrences "$replacement_url" "$metadata")
original_resource_count=$(count_occurrences "$original_resource" "$metadata")
replacement_resource_count=$(count_occurrences "$replacement_resource" "$metadata")
plist_version=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$info_plist")

if [[ $original_url_count != 2 || $replacement_url_count != 0 ]]; then
  print -u2 "unexpected URL counts: original=$original_url_count replacement=$replacement_url_count"
  exit 71
fi

if [[ $original_resource_count != 2 || $replacement_resource_count != 0 ]]; then
  print -u2 "unexpected resource-version counts: original=$original_resource_count replacement=$replacement_resource_count"
  exit 72
fi

if [[ $plist_version != $original_version ]]; then
  print -u2 "unexpected CFBundleShortVersionString: $plist_version"
  exit 73
fi

ORIGINAL_URL=$original_url REPLACEMENT_URL=$replacement_url \
  perl -0pi -e '
    BEGIN {
      $old_url = $ENV{"ORIGINAL_URL"};
      $new_url = $ENV{"REPLACEMENT_URL"};
    }
    s/\Q$old_url\E/$new_url/g;
  ' "$metadata"

if $spoof_resource; then
  ORIGINAL_RESOURCE=$original_resource REPLACEMENT_RESOURCE=$replacement_resource \
    perl -0pi -e '
      BEGIN {
        $old_resource = $ENV{"ORIGINAL_RESOURCE"};
        $new_resource = $ENV{"REPLACEMENT_RESOURCE"};
      }
      s/\Q$old_resource\E/$new_resource/g;
    ' "$metadata"
fi

rewritten_data_bundle="$temp_dir/data.unity3d.rewritten"
python3 "$unityfs_rewriter" \
  "$data_bundle" \
  "$rewritten_data_bundle" \
  --from-version "$original_version" \
  --to-version "$replacement_version"
mv "$rewritten_data_bundle" "$data_bundle"

plutil -replace CFBundleShortVersionString -string "$replacement_version" "$info_plist"

original_url_after=$(count_occurrences "$original_url" "$metadata")
replacement_url_after=$(count_occurrences "$replacement_url" "$metadata")
original_resource_after=$(count_occurrences "$original_resource" "$metadata")
replacement_resource_after=$(count_occurrences "$replacement_resource" "$metadata")
plist_version_after=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$info_plist")

if [[ $original_url_after != 0 || $replacement_url_after != 2 ]]; then
  print -u2 "URL verification failed: original=$original_url_after replacement=$replacement_url_after"
  exit 74
fi

if $spoof_resource; then
  if [[ $original_resource_after != 0 || $replacement_resource_after != 2 ]]; then
    print -u2 "resource-version verification failed: original=$original_resource_after replacement=$replacement_resource_after"
    exit 75
  fi
else
  if [[ $original_resource_after != 2 || $replacement_resource_after != 0 ]]; then
    print -u2 "resource version changed unexpectedly: original=$original_resource_after replacement=$replacement_resource_after"
    exit 76
  fi
fi

if [[ $plist_version_after != $replacement_version ]]; then
  print -u2 "CFBundleShortVersionString verification failed: $plist_version_after"
  exit 77
fi

rm -f "$output_ipa"
(
  cd "$temp_dir"
  zip -qry "$output_ipa" Payload
)

print "created: $output_ipa"
print "API URL: $original_url -> $replacement_url (2 occurrences)"
print "managed client version: $original_version -> $replacement_version (Unity PlayerSettings)"
print "CFBundleShortVersionString: $original_version -> $replacement_version"
if $spoof_resource; then
  print "resource version: $original_resource -> $replacement_resource (2 occurrences)"
else
  print "resource version: kept at $original_resource"
fi
