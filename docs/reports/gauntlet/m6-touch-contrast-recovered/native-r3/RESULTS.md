# R3 native acquisition: pixel gate failed

The approved immutable acquisition completed, and the original analyzer exited 1.
Both sources have valid provenance with no identity errors and equal geometry;
the declared overall pixel gate fails on both. No product or method was adjusted
after this result. Numeric subgroups do not close the boundary/accessibility gate.

| Original analyzer output | Baseline | Candidate |
| --- | --- | --- |
| Native scenes | 32 | 32 |
| Original/wrapped/diagnostic PNGs | 1,280 | 1,280 |
| Provenance valid | yes | yes |
| Identity errors | 0 | 0 |
| Pixel rows | 304 | 304 |
| Resolved rows | 216 | 240 |
| Overall declared pixel gate | failed | failed |

Candidate unresolved groups include action icons, borders, held borders and
inactive icons. The original complete-footprint and compositing failures remain
in `recomputed.json`, with the exact coordinates/counters and PNGs in the raw
archive. The independent actual-output critic must distinguish product overlap,
reconstruction assumptions and any other cause from those pixels. This report
makes no improvement or acceptance claim. The dark surround against external
backgrounds, text packing, plate occlusion and separate blind visual review are
independent scopes.

Exact source/method freeze is `a52022169241df9ff662039547a375e1c46ac1c5`, source
approval `da09733`, and baseline `138a1ab810a29e3c504f5811a0051a08e1ad52b9`.
The sole product drawing candidate remains `b4d0c1b`. Every producer had staged
source/fixture/UID checks before and after, 327 paths per checked project; all
remain unchanged. Normal and wrapped source renders are identical according to
the approved analyzer. Actual geometry matches across the complete native matrix.

The pinned 4.7.2 official engine's archive SHA-512 matches `scripts/toolchain.py`,
and its extracted member matches the executed binary. Binary SHA-256 is
`8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`.
Actual native logs report Mesa 25.0.7 llvmpipe, LLVM 19.1.7, GL 4.5 compatibility.
CPU selectors were taskset 0–3, LP_NUM_THREADS=2 and OMP_NUM_THREADS=2, under a
4-CPU cgroup quota. These are software renders and controlled fixture states,
not physical touch-device, GPU or ergonomic qualification.

Sixteen shared native white/gray/arena/smoke backgrounds were frozen and checked
unchanged before/after each control producer. Each source retains 32 actual
product PNGs, 32 wrapped-normal equivalence PNGs, and 1,216 underlay/black/white/
complete-isolated-footprint PNGs. All 2,576 native PNGs are retained unchanged.
No third-party reference images are included.

Fresh headless regressions on each exact source pass TOUCH_TEST 34/0 and
INPUT_MODE_TEST 462/0. The latter explicitly reports graphical_pointer=false and
simulated capabilities/input, not physical hardware. No live HUD export/capture,
OCR, new aggregate suite or unrelated native workload ran in this lane.

Lane start was 2026-10-23 05:39:33 UTC. Engine/capture/regression invocations were
sequential. The analyzer finished and owned cleanup completed at 05:54:50 UTC.
All 10 owned Godot PIDs and the owned Xvfb PID are absent; display :131 socket and
lock are absent. `lane-end.json` retains actual process receipts. A preflight-only
mistake compared the ZIP digest with the extracted binary before any engine
launch; its retained diagnostic explains the corrected archive/member check.

The untouched blind packet is outside Git at
`/workspace/sightbreak-touch-contrast-blind-recovered-r3`, with 32 paired original
native PNGs per A/B. Its key is outside that packet. Root owns the separate visual
judge and any unblinding record; this builder did not message the judge.

The immutable raw tree remains
`/workspace/sightbreak-touch-contrast-native-recovered-r3`. `payload-manifest.json`
lists every archived raw path, byte count and SHA-256. `ARCHIVE.json` records the
whole archive and <=24 MiB numbered parts; concatenate parts in listed order to
recover the exact `.tar.xz`. Every archive member is re-read and SHA-256 verified.
The full local archive and all raw files remain retained. Independent audit and
its committed verdict are required before iteration or acceptance.
