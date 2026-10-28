#!/usr/bin/env bash
# One seeded all-bot match per process, so every run starts clean. Observation only.
#   audit.sh OUTDIR DIFFICULTY SEED [GAME_DIR]
# GAME_DIR is any checkout's game/ directory (default: this repository's), which is how the same seeds were run on the
# old and the new yard. Needs the pinned toolchain (scripts/setup.sh --editor-only). Writes OUTDIR/DIFFICULTY-SEED.log.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$(cd "$here/../../../.." && pwd)"
out="${1:?usage: audit.sh OUTDIR DIFFICULTY SEED [GAME_DIR]}"; difficulty="${2:?}"; seed="${3:?}"
game_dir="${4:-$repo_dir/game}"
tools_dir="${SIGHTBREAK_TOOLS_DIR:-$(dirname "$repo_dir")/tools}"
godot_bin="${GODOT_BIN:-$tools_dir/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64}"
state="$(mktemp -d)"
trap 'rm -rf "$state"' EXIT
mkdir -p "$out"
XDG_DATA_HOME="$state/data" XDG_CONFIG_HOME="$state/config" XDG_CACHE_HOME="$state/cache" \
  timeout 900 "$godot_bin" --path "$game_dir" --headless --audio-driver Dummy --script "$here/bot_match_audit.gd" -- \
  --seed="$seed" --difficulty="$difficulty" --timescale=5 > "$out/$difficulty-$seed.log" 2>&1
