#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
target="${1:-linux}"
case "$target" in
  linux) preset=Linux; output="$repo_dir/builds/linux/sightbreak.x86_64" ;;
  android) preset=Android; output="$repo_dir/builds/android/sightbreak-debug.apk" ;;
  ios)
    exec python3 "$repo_dir/scripts/export_ios.py" ;;
  *) echo 'Usage: scripts/export.sh [linux|android|ios]' >&2; exit 2 ;;
esac
mkdir -p "$(dirname "$output")"
python3 "$repo_dir/scripts/build_manifest.py" begin "$target"
"$repo_dir/scripts/godot.sh" --headless --editor --import --quit 2>&1 | tee "$(dirname "$output")/import.log"
"$repo_dir/scripts/godot.sh" --headless --export-debug "$preset" "$output" 2>&1 | tee "$(dirname "$output")/export.log"
if rg -q '^(SCRIPT ERROR|ERROR:)|Parse Error' "$(dirname "$output")/import.log" "$(dirname "$output")/export.log"; then
  echo 'Export emitted an error; artifact is not verified.' >&2
  exit 1
fi
[[ -s "$output" ]]
cp "$repo_dir/docs/GODOT-LICENSE.txt" "$repo_dir/docs/GODOT-COPYRIGHT.txt" "$(dirname "$output")/"
python3 "$repo_dir/scripts/build_manifest.py" finish "$target"
printf 'Exported %s\n' "$output"
