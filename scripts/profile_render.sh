#!/usr/bin/env bash
# Same fixed-work benchmark can target the archived baseline or current project.
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
project_dir="${SIGHTBREAK_PROFILE_PROJECT:-$repo_dir/game}"
output_dir="${1:-$repo_dir/builds/qa/v03/profile-current}"
quality="${2:-standard}"
godot_bin="${GODOT_BIN:-${SIGHTBREAK_TOOLS_DIR:-$(dirname "$repo_dir")/tools}/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64}"
[[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]] || { echo 'Native display required' >&2; exit 2; }
mkdir -p "$output_dir"
export XDG_DATA_HOME="$repo_dir/.local/profile/data" XDG_CONFIG_HOME="$repo_dir/.local/profile/config" XDG_CACHE_HOME="$repo_dir/.local/profile/cache"
export LP_NUM_THREADS=2 LIBGL_ALWAYS_SOFTWARE=1
# Both versions use the same two allowed CPUs and Mesa worker count. Shared-host noise remains.
profile_cpus="$(python3 -c 'import os; print(",".join(map(str,sorted(os.sched_getaffinity(0))[:2])))')"
for run in 1 2 3; do
  run_dir="$output_dir/run-$run"
  mkdir -p "$run_dir"
  timeout 180 taskset -c "$profile_cpus" "$godot_bin" --path "$project_dir" --audio-driver Dummy --script res://tests/render_benchmark.gd -- "--output=$run_dir" "--quality=$quality" 2>&1 | tee "$run_dir/render.log"
  if rg -q '^ERROR:|SCRIPT ERROR|Parse Error' "$run_dir/render.log"; then exit 1; fi
  test -s "$run_dir/metrics.json"
done
python3 - "$output_dir" "$project_dir" "$profile_cpus" <<'PY'
import json, pathlib, statistics,sys
out=pathlib.Path(sys.argv[1]); runs=[json.loads((out/f'run-{i}/metrics.json').read_text()) for i in (1,2,3)]
views=[]
for index,row in enumerate(runs[0]['views']):
 samples=[run['views'][index] for run in runs]
 views.append({'view':row['view'], 'median_of_run_medians_ms':statistics.median(s['median_frame_ms'] for s in samples),'run_medians_ms':[s['median_frame_ms'] for s in samples],'p95_ms':[s['p95_frame_ms'] for s in samples],'draw_calls':[s['draw_calls'] for s in samples],'primitives':[s['primitives'] for s in samples],'texture_bytes':[s['texture_bytes'] for s in samples]})
report={'context':runs[0]['context'],'project':sys.argv[2],'cpus':sys.argv[3],'mesa_workers':2,'quality':runs[0]['quality'],'runs':3,'frames_per_view_per_run':runs[0]['views'][0]['samples'],'construction_ms':[r['construction_ms'] for r in runs],'views':views}
(out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
PY
