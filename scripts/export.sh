#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
target="${1:-linux}"
case "$target" in
  linux) preset=Linux; output="$repo_dir/builds/linux/sightbreak.x86_64" ;;
  android) preset=Android; output="$repo_dir/builds/android/sightbreak-debug.apk" ;;
  ios)
    if [[ "$(uname -s)" != Darwin ]]; then
      echo 'iOS export requires macOS and Xcode. Open game/ with Godot 4.7.2 on macOS, set your Apple team in the iOS export preset, export the Xcode project, then sign/build on the Mac.' >&2
      exit 1
    fi
    preset=iOS; output="$repo_dir/builds/ios/sightbreak.zip" ;;
  *) echo 'Usage: scripts/export.sh [linux|android|ios]' >&2; exit 2 ;;
esac
mkdir -p "$(dirname "$output")"
"$repo_dir/scripts/godot.sh" --headless --editor --import
"$repo_dir/scripts/godot.sh" --headless --export-debug "$preset" "$output"
cp "$repo_dir/docs/GODOT-LICENSE.txt" "$repo_dir/docs/GODOT-COPYRIGHT.txt" "$(dirname "$output")/"
printf 'Exported %s\n' "$output"
