#!/usr/bin/env bash
# Native graphics smoke; unlike Godot's exit status, logged renderer errors fail this check.
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -z "${DISPLAY:-}" && -z "${WAYLAND_DISPLAY:-}" ]]; then
  printf 'A graphical display is required. A headless run cannot validate rendering.\n' >&2
  exit 2
fi
mkdir -p "$repo_dir/.local/validation"
run_dir="$(mktemp -d "$repo_dir/.local/validation/native-XXXXXX")"
"$repo_dir/scripts/godot.sh" --audio-driver Dummy -- --demo "--capture=$run_dir/viewport.png" 2>&1 | tee "$run_dir/render.log"
if rg -q '^ERROR:|SCRIPT ERROR|Parse Error' "$run_dir/render.log"; then
  printf 'Native graphics check FAILED; inspect %s\n' "$run_dir/render.log" >&2
  exit 1
fi
rg -q SIGHTBREAK_DEMO_CAPTURED "$run_dir/render.log"
test -s "$run_dir/viewport.png"
"$repo_dir/scripts/godot.sh" --audio-driver Dummy --script res://tests/render_lifecycle_test.gd 2>&1 | tee "$run_dir/lifecycle.log"
if rg -q '^ERROR:|SCRIPT ERROR|Parse Error' "$run_dir/lifecycle.log"; then
  printf 'Native lifecycle check FAILED; inspect %s\n' "$run_dir/lifecycle.log" >&2
  exit 1
fi
rg -q 'NATIVE_LIFECYCLE_TEST checks=11 failures=0' "$run_dir/lifecycle.log"
printf 'Native graphics and lifecycle checks passed. Capture and logs: %s\n' "$run_dir"
