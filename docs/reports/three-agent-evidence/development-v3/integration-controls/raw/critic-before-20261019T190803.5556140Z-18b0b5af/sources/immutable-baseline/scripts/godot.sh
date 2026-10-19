#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tools_dir="${SIGHTBREAK_TOOLS_DIR:-$(dirname "$repo_dir")/tools}"
export XDG_DATA_HOME="${SIGHTBREAK_STATE_DIR:-$repo_dir/.local}/data"
export XDG_CONFIG_HOME="${SIGHTBREAK_STATE_DIR:-$repo_dir/.local}/config"
export XDG_CACHE_HOME="${SIGHTBREAK_STATE_DIR:-$repo_dir/.local}/cache"
export ANDROID_USER_HOME="${SIGHTBREAK_STATE_DIR:-$repo_dir/.local}/android"
mkdir -p "$ANDROID_USER_HOME" "$XDG_DATA_HOME" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME"
godot_bin="${GODOT_BIN:-$tools_dir/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64}"
if [[ ! -x "$godot_bin" ]]; then
  printf 'Godot is missing; run scripts/setup.sh first (or set GODOT_BIN).\n' >&2
  exit 1
fi
exec "$godot_bin" --path "$repo_dir/game" "$@"
