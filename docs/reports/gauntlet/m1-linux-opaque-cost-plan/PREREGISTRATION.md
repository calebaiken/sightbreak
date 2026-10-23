# Linux opaque-render cost: source map and next controlled diagnostic

2026-10-23. Updated at the source implementation checkpoint following independent
plan review `fcb5276ca620c86a1a1342e9ac1dd32bec4eecff`. The separate fixture,
controller and pure controls are now implemented; their exact-source review is
pending. No engine, compile, profiler, OCR, export or native process ran. This
report authorizes no runtime process. The current implementation and limits are
in [IMPLEMENTATION.md](IMPLEMENTATION.md).

Own branch `diagnostic/linux-opaque-cost-preregistration`, sparse worktree
`/workspace/sightbreak-linux-opaque-cost`, exact root base
`373b6362f5ab253b9ded7e8a611cb68c9f2a3672`. Its entire game tree equals
`b2e0293a546961230afbd73e5cd2a1a307d69e94`: tree
`55691684d31d44f1680141954bbe530443de9d1f`, shipping-content SHA-256
`bcb872f6998ed8504c852dee354ab0acf5b6f19e58e40717267a1927e6d68a50`.
No game, script, contributor branch or canonical mission file changes.

## Inspected benchmark and known failure

The named output reference is the independently accepted one-attempt
[`b1a131ab` capability receipt](../m1-linux-gles-profile-recovered/independent-native-review/REVIEW.md),
review `bca8b7fd`, raw evidence `afb4d17`. Its 35 profile headers include 34
row-bearing blocks; `Render Opaque Pass` is the largest printed interval in each.
Their emitted averages are 260.764–1,403.713 ms. The header's separate values
are 0–486.349 ms. Those numbers neither identify a CPU function nor measure
profiler overhead. That attempt fails the original 45-second initial-LIVE wait
while still in BUY; plant, next buy and restart are unreached. Earlier Linux
next-buy failures remain FAILED. No second ordinary attempt is registered here.

The named fixed-work reference is this base's `game/tests/render_benchmark.gd`
and `scripts/profile_render.sh`, with original methods/results in
`docs/reports/PERFORMANCE-0.3.md`. Those actually inspected files define the
five-actor Relay Yard fixture and four camera poses. Their old timings are not
a current-source performance baseline. The wrapper runs three processes, uses
four views, advances visual animation, removes the frame cap and reuses cache
paths; it cannot be reused unchanged for the single-view experiment below.
`integration_render_profile.gd` also changes scenarios and directly sets match
phase/timer. It is unsuitable for preserving a single fixed workload.

## What the pinned opaque row covers

All engine references below use exact Godot
`ed1daf0bf001b61586d9930840f2f1394092c079`. Seven original fetched files were
reused with their byte hashes verified. The retained critic's original GLES
scene-renderer bytes also match the inspected copy exactly. Supplementary
header/shader/material sources were fetched at the same commit. URLs, lengths,
SHA-256 values, original cache paths and repository blobs are in
[`source-references.json`](source-references.json). No engine was built.

| Exact source boundary | Meaning |
| --- | --- |
| [`RenderingServerDefault::_draw`, lines 80–122](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/servers/rendering/rendering_server_default.cpp#L80) | Scene/canvas update and viewport rendering precede timestamp-profile processing. A printed task name is a timestamp interval label. |
| [`rasterizer_scene_gles3.cpp:2557–2568`](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/drivers/gles3/rasterizer_scene_gles3.cpp#L2557) | Shadow rendering, light/environment setup, opaque-list construction and sorting occur before the opaque timestamp. Their C++ work is not the body of the named opaque interval. |
| [`:2719–2811`](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/drivers/gles3/rasterizer_scene_gles3.cpp#L2719) | The optional depth prepass, framebuffer/depth/blend/scissor setup and ordinary clearing precede `RENDER_TIMESTAMP("Render Opaque Pass")` at 2811. |
| [`:2811–2865`](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/drivers/gles3/rasterizer_scene_gles3.cpp#L2811) | The label starts before pass specialization, render-region setup and `_render_list_template<PASS_MODE_COLOR>` at 2862, followed by depth/stencil state changes. It includes setup and opaque-list work. |
| [`:2837–2912`](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/drivers/gles3/rasterizer_scene_gles3.cpp#L2837) | The endpoint is the next actual timestamp. Camera feed inserts a marker at 2838 before opaque objects. Otherwise sky inserts one at 2868; without sky, screen/depth backbuffer copying can precede the transparent marker at 2912. There is no universal one-function endpoint. |
| [`_render_list_template`, :3170–3265](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/drivers/gles3/rasterizer_scene_gles3.cpp#L3170) | Color-pass environment/LTC texture binding and one-time LTC texture creation can precede surface traversal. Opaque mode skips surfaces without the opaque-pass flag. Cold allocation is a distinct possibility from warm draw cost. |
| [`:3321–3334`, `:3493–3529`, `:3683–3686`](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/drivers/gles3/rasterizer_scene_gles3.cpp#L3321) | A surface may have multiple additive light/shadow passes. Vertex/index/material binding, specialization and shader binding occur inside traversal. The label is not a pure fragment-shader or geometry counter. |
| [`:3913–4006`](https://github.com/godotengine/godot/blob/ed1daf0bf001b61586d9930840f2f1394092c079/drivers/gles3/rasterizer_scene_gles3.cpp#L3913) | Index/vertex counts and visible draw counters are updated, then ordinary or instanced `glDraw*` calls execute. The visible draw counter deliberately excludes depth and motion-vector passes; it cannot be treated as every GL submission. |

Relay Yard creates a sky background (`arena.gd:126–159`) rather than camera feed.
The retained output includes `Render Sky`, consistent with the ordinary
opaque-to-sky path. Repeated task names aggregate across emitted areas; stdout
does not identify a particular viewport, surface or draw. This source map does
not retroactively assign one exact CPU function to a historical averaged row.

One concrete later material hypothesis is available, but it is not the next
registered change. `arena.gd:61–73` selects world-triplanar albedo, normal and
roughness maps for three surface families. Batched materials retain that mapping
at 479–491. In the pinned `scene/resources/material.cpp:1465–1473`, the generated
triplanar helper has three weighted texture expressions; lines 1716–1725 emit
its normal-map use. `drivers/gles3/shaders/scene.glsl:2357–2365` reconstructs and
transforms the normal. This identifies source work to investigate, not actual
driver instruction counts or a measured expensive feature. Calling
`apply_detail_quality(false)` would disable both normal and roughness features;
it would not isolate either. Any feature-ablation study needs another explicit
registration and quality/restoration controls. None is proposed for runtime now.

## Smallest next contrast: incremental profiling cost

Testable hypothesis H1: **adding `--gpu-profile` increases median warm wall
cadence of consecutive post-draw intervals at the declared pacing by at least
10%** in the declared full-Standard
fixture. The threshold is an actionable screening resolution, not a release
target or a statistical confidence claim. This first contrast screens a
flag-associated median cadence effect. It does not measure complete incremental
profiling cost: rare stdout stalls can disappear from a median. Preserve total,
mean and largest interval as descriptive secondary data, without replacing H1
or adding retrospective decision thresholds. It preserves visual settings and
materials.

The pinned synchronous renderer emits `frame_post_draw` before its profile tail;
`main.cpp` increments the drawn counter after draw returns and applies frame
delay later. Consecutive post-draw intervals therefore include the previous
frame's profile tail, probe tail, pacing and scheduling. They do not isolate a
draw call, prove GPU completion or bound uncapped/full profiler cost. Hold the
default synchronous `safe` model explicitly in every argv and project overlay;
retain that source-bound selection, actual argv and project-setting readback.

This question comes first because the two existing ordinary attempts changed
instrumentation and did not complete the same flow. Comparing their outcomes
cannot estimate profiling cost. The unmodified GLES rasterizer also calls
internal timestamp begin/end unconditionally (`rasterizer_gles3.cpp:101–122`,
`utilities.cpp:343–367`). OFF therefore means the current engine without the
additional flag; it does not mean every engine query is removed.

Propose one bounded fixed-work block with only two distinct conditions:
**OFF, ON, ON, OFF**, each in a fresh process. The reversed final pair provides
a drift check. All four
use one frozen diagnostic payload. The only engine-argv difference is the
initial `--gpu-profile` option before `--`. Neither condition changes any
material, normal map, MSAA, shadow, resolution, render scale, physics setting,
timer, renderer implementation or game file. The existing original gameplay
controller and all of its deadlines remain untouched and are not run.

Future fixture specification, requiring implementation/source review first:

- Construct the existing five-actor Relay Yard reference once. Hold only its
  named `approach` pose: local actor at `(-14,0,-18)`, yaw PI, pitch -0.12;
  camera height 1.62, FOV 82, near 0.045, far 120; the local rifle is visible.
  Four other actors retain the reference's ID/team/position/yaw formulas.
  Freeze the constructed visual pose and transforms; call no authority tick,
  bot policy or visual animation after setup. No live match or HUD is claimed.
- Keep 1280x720, Standard/2x MSAA, bilinear scale 1, sun shadows, normal/roughness
  maps and stock sky/fog, cap 60 and time scale 1 in both conditions. Preserve
  the project's V-Sync selection and record its actual getter/log result.
  All actor/camera transforms, meshes, materials, lights and scene counters
  must be serialized into a stable setup fingerprint before measurement.
- Retain construction-only settling outside sampling, then a separately timed
  cold/anchor draw. In synchronous mode its callback advances while the drawn
  counter has not yet incremented. After that anchor, retain exactly 32 warm
  intervals and 64 measured consecutive post-draw intervals, with both clock,
  drawn-counter and callback-serial endpoints. Require one new drawn identity
  and callback per interval. Store arrays in memory; write no
  fixture telemetry, PNG or status file inside the measured region.
- Retain raw warm-up and measurement durations/counters. Take the proof PNG
  after the measured region closes. Pixel hashes and stable scene/material/
  transform fingerprints must match across all four processes. A mismatch
  invalidates comparability; it cannot be repaired by lowering image quality.
- Use a fresh isolated output/cache state for every process with the same
  empty initial cache policy, and identical fixed warm-up. Do not reuse ON's
  caches for OFF or compare a warmed process with a cold one. Retain cold
  construction/first-draw measurements separately. No adaptive warm-up or
  extra process is allowed to make a condition pass.

The camera and five actors are a declared synthetic fixture. It excludes the
original HUD, bots, ten-actor match and native input. It can estimate flag cost
for that workload only. It cannot establish the cause of the original failure,
the cost of one CPU function, or a shipping optimization.

## Source, host and overhead controls

Before a future block, freeze a complete temporary diagnostic-project tree,
fixture/controller hashes and package manifest. Keep the base game byte hashes
separate from the explicitly injected fixture/main-scene overlay. Reuse one
fresh pinned-4.7.2 export in every condition; independently inspect its ELF/PCK,
resources and source identities. Its diagnostic fixture must never enter the
shipping project or be mistaken for a release package. Native flags, extent,
readbacks and PNGs must prove actual runtime conditions.

Use the same isolated Xvfb instance and exact `Compatibility`/Mesa driver stack
for all four processes. Hash the editor/template archives and relevant loaded
driver libraries, record OS/kernel and actual renderer/version logs. Inherit
the same two selected allowed CPUs for each Godot process, record the exact
affinity/readback, use `LIBGL_ALWAYS_SOFTWARE=1` and `LP_NUM_THREADS=2`, and keep
priority/quota unchanged. Serialize the local native lane. Record cgroup
quota/throttling and owned process identity at the block/condition boundaries;
no host-wide process discovery or recurring CPU sampler is needed.

Collect owned-child CPU/rusage at process completion, with no other completed
child charged to that interval. Label it whole-process CPU including startup,
not warm-region CPU or a partition of the GPU-query intervals. Identical
per-frame clock/counter probes remain in every condition. GPU-profile stdout
goes to the same type of local file sink; its extra writes are part of the
treatment. Neither clock-probe overhead nor query-versus-stdout cost is isolated
by this design. Profiler attachment, OCR, video recording, image readback during
samples and the previous external CPU sampler stay off in all conditions.

Each proposed diagnostic process has a separate 180-second hard bound plus
bounded owned cleanup. It does not replace any gameplay acceptance budget.
Timeout, missing rows, renderer/source drift, failed fingerprint/pixel control,
remaining child, rising throttling or lost samples makes the block incomplete
or incomparable. No runtime release or extra retry follows from elapsed time.

## Preregistered computation and decision

Use each process's 64 raw cadence samples to compute its median, keeping order
and every sample. For even-length arrays use the arithmetic mean of the two
middle sorted values. Retain the sum, arithmetic mean and largest interval.
Do not treat samples as independent experiment replicates or create a
confidence interval by resampling individual frames. Compare two paired ratios:
`median(ON2)/median(OFF1)` and `median(ON3)/median(OFF4)`.

The block is interpretable only if all source/scene/pixel/counter controls pass,
throttling does not increase, the two OFF medians and the two ON medians each
satisfy `max(a,b)/min(a,b)-1 <= 0.05`, and each fixed warm-up's two 16-interval
halves satisfy the same formula `<= 0.10`. Durations must be finite and positive;
array/counter identities must be exact. A 1e-12 numerical tolerance applies only
to the drift boundary's floating-point evaluation. These are drift/stabilization screens,
not proof that all shared-host noise is absent. If the scene is frame-cap paced,
the result cannot bound underlying uncapped render cost; record that limitation
and require a separate pacing study before changing the cap.

- Both paired ratios greater than or equal to 1.10 support a flag-associated
  median cadence increase in this block and fixture.
- Both ratios at least 0.90 and strictly below 1.10 support only that this block did not resolve
  a 10% median cadence increase. They do not bound sparse stalls, total overhead,
  zero overhead or formal equivalence.
- Opposite signs, excessive drift, materially faster ON or failed controls
  leave attribution unresolved; retain the exact data and stop the block.

Retain every stdout profile block from ON. Because the entire process holds one
unchanged view/settings, it avoids gameplay-phase changes, but startup and
historical buffers still exist. Do not tag rows as warm-up/sample phases from
stdout order or receipt time. Use them only as whole-process named-interval
corroboration, not the H1 estimator. The header/row statistics remain different;
no summation, unique-frame count, CPU attribution or physical-FPS conversion.

The output gate is a source-bound table of four process medians, raw samples,
paired ratios, all comparability checks, driver/CPU/cache conditions, exact
commands/source/payload identities, PNG hashes, complete logs and owned cleanup.
A fresh critic must recompute those facts independently. A valid small flag
effect would justify designing a separate one-feature renderer study; a large
or unresolved effect would first require measuring with less intrusive timing.
Neither outcome changes quality defaults or closes any gameplay/release gate.

## Present checkpoint

Source implementation and pure synthetic/mock controls now accompany this
corrected registration. Their receipts establish evaluator/launch/stop behavior
under supplied synthetic data, not Godot behavior. The GDScript has not been
compiled or executed. The original source-map ledger and root/b2e0293 game
equality remain intact; game and canonical mission documents are unchanged.
Fresh exact implementation review, compilation/export and runtime are separate
unreleased steps. The largest gap remains actual source-bound unchanged-work
cadence data and the limits of a median in the presence of sparse stalls.
