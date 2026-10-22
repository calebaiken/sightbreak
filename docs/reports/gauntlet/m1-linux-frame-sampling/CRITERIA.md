# Linux frame diagnostic implementation criteria

2026-10-22. Builder branch `diagnostic/linux-frame-sampling`, own worktree
`/workspace/sightbreak-linux-frame-sampling`, base `9616f52`. This declaration
precedes instrumentation. Prior source-only investigation is `91881ac`; its
report and this proposal have no independent acceptance verdict yet.

The reference is the retained `3c4d921` ordinary Linux plant rounds 3 and 4:
2,600 authority ticks / 325 drawn frames across the initial-capture-to-failure
bracket, then 247 ticks / 31 drawn frames during the original failed next-round
wait. Windows run 39735001567 passes that deadline with the same old shipping
content, but uses a different software renderer, host and native extent. These
are concrete diagnostic references, not controlled performance comparisons.

1. Extend only the existing debug/offline `_snapshot`. Read the actual physics
   catch-up limit, tick rate, jitter setting, frame cap, process/physics/drawn
   counters, existing engine timing monitors, render submission counters and
   viewport/output-texture dimensions. Keep the existing status/event cadence,
   write paths, admission and authority behavior. Query dimensions without image
   readback, waits or new engine callbacks. Leave the internal 3D target size
   explicitly unavailable if the inspected API cannot provide it.
2. Verify each new Godot API against pinned 4.7.2 documentation/source and retain
   URLs, hashes and excerpts. The source implementation publishes process and
   physics timing **maxima at the engine's roughly one-second statistics
   refresh**. Process timing includes process callbacks, renderer sync and draw;
   physics timing is a maximum individual physics step. Label those semantics
   precisely. The values are not an exhaustive CPU/GPU breakdown and cannot be
   summed to recover a frame's elapsed time.
3. Add an explicit Linux plant-only controller option for an external sampler.
   Require the original 180-second whole-flow budget for that option. Sample the
   already-owned client only, once per second for at most 180 seconds, with a
   separate output file and bounded worker lifetime. Retain process start
   identity before/after reads to reject PID reuse and recheck the owned Popen
   object's exit. No process discovery, input, signals, subprocesses, network,
   scheduling changes or privileged profiler are allowed in the sampler.
4. Record monotonic/wall sampling timestamps, kernel CPU clock units, process and
   bounded per-thread CPU counters, allowed affinity and readable cgroup-v2 CPU
   quota/stat counters. Categorize known llvmpipe workers without retaining
   arbitrary thread names. Serialize only DISPLAY, LIBGL_ALWAYS_SOFTWARE and
   LP_NUM_THREADS from the child environment. Account, bearer, network payload,
   command-line, profile and arbitrary environment data stay outside the output.
   Missing/unsupported counters must carry explicit unavailable reasons.
5. Preserve the original controller default path and every gameplay/input/render
   budget. Preserve 1280×720, Standard/full render scale, FPS cap 60, 60 Hz physics,
   time scale 1, llvmpipe/two workers and the original twelve-second next-round
   wait. Optional diagnostic failure cannot be described as a product fix or a
   complete plant pass. Retain all earlier failed receipts.
6. Before runtime, run pure-Python controls against owned synthetic proc/cgroup
   trees and an inert fake process. Cover disappeared/reused PIDs, unavailable
   counters, traversal rejection, thread bounds, environment privacy, fresh
   output, sample/file errors, bounded termination and controller option guards.
   Review the exact diff and send it to a fresh separate critic. No engine,
   native client, OCR, service, export or CI runs before root releases its lane
   after the aggregate. Native parser/API/monitor behavior remains unverified
   until that later execution.

The largest remaining gap is the absent same-attempt timing/scheduling receipt
under the failing workload. A readback of eight with near-eight tick/process-frame
ratio and process/drawn agreement supports catch-up saturation. Different limits
or ratios narrow or reject it. Timing maxima and CPU/throttle counters then select
a separately reviewed next experiment; they do not alone identify the expensive
function or authorize quality/timer changes. Arena/PR26 ownership and canonical
mission files are outside this branch. Physical-device performance stays open.
