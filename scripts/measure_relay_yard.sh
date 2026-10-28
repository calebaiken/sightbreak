#!/usr/bin/env bash
# Reproduces the Relay Yard layout evidence: route exposure, top-down render, eye-level views and
# all-bot match pacing. Observation only: it changes no game file.
#
#   scripts/measure_relay_yard.sh OUTDIR [--seeds "21 22 23"] [--difficulties "normal hard"] [--jobs 3] [--no-render] [--both-starts]
#
# --both-starts runs every seed twice, once with actors 1-5 attacking first and once with actors 6-10, so a squad
# effect is not mistaken for a role effect.
#
# Needs the pinned toolchain (scripts/setup.sh). Rendered captures need DISPLAY (Xvfb is enough) and
# use software rendering, so they show layout and look, never frame rate. Bot matches run headless.
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out="${1:?usage: measure_relay_yard.sh OUTDIR [options]}"
shift
seeds="21 22 23"
difficulties="normal hard"
jobs=3
render=1
both=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --seeds) seeds="$2"; shift 2 ;;
    --difficulties) difficulties="$2"; shift 2 ;;
    --jobs) jobs="$2"; shift 2 ;;
    --no-render) render=0; shift ;;
    --both-starts) both=1; shift ;;
    *) echo "unknown option $1" >&2; exit 2 ;;
  esac
done
mkdir -p "$out/bots"
cd "$repo_dir"
git rev-parse HEAD > "$out/source-commit.txt"
echo "== route exposure (defender anchors, 38 m)"
timeout 600 ./scripts/godot.sh --headless --script res://tests/map_sightline_probe.gd -- --range=38 > "$out/sightlines.log" 2>&1
grep -a -E 'SIGHTLINE_(SPAWNS|PATHS|RUNS|SUMMARY)' "$out/sightlines.log" | cut -c1-1200
if [[ "$render" == 1 ]]; then
  if [[ -z "${DISPLAY:-}" ]]; then echo "no DISPLAY: skipping rendered captures (use --no-render to silence)" >&2; else
    echo "== top-down overview and eye-level views"
    timeout 600 ./scripts/godot.sh --audio-driver Dummy --rendering-method gl_compatibility --script res://tests/map_overview_capture.gd -- --capture-dir="$out/captures" --name=overview --size=1200x1200 2>&1 | grep -a 'MAP OVERVIEW'
    timeout 900 ./scripts/godot.sh --audio-driver Dummy --rendering-method gl_compatibility --script res://tests/map_viewpoints_capture.gd -- --capture-dir="$out/captures" --prefix=view 2>&1 | grep -a -c VIEWPOINT
  fi
fi
echo "== all-bot matches ($difficulties; seeds $seeds)"
for d in $difficulties; do for s in $seeds; do echo "$d $s"; [[ "$both" == 1 ]] && echo "$d ${s}s"; done; done |
  xargs -P "$jobs" -L 1 bash -c 'seed="${1%s}"; flag=""; [[ "$1" == *s ]] && flag="--swap-start"; timeout 900 ./scripts/godot.sh --headless --script res://tests/bot_objective_metrics.gd -- --difficulty=$0 --seed=$seed $flag > "'"$out"'/bots/$0-$1.log" 2>&1'
python3 scripts/summarize_bot_metrics.py "$out/bots" --kills | tee "$out/bot-summary.txt"
