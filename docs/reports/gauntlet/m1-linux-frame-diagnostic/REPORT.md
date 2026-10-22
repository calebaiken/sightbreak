# Linux next-round scheduling investigation

2026-10-22. Source-only investigation on `review/linux-frame-diagnostic`, based
on root `ba5013d`. No game, arena, renderer, validator or canonical mission file
was changed. No engine, native client, OCR, export, server or CI was run. The
receipt builder retains the local engine lane, followed by root's aggregate.

The retained evidence points to sustained slow simulation across the match,
rather than a new stall beginning at the POST transition. Both Linux attempts
advance exactly **2,600 authority ticks across 325 drawn frames** between their
initial match capture and failure. Their final POST brackets advance 247 ticks
across 31 drawn frames. This supports testing whether the engine repeatedly
reaches its physics catch-up ceiling while presentation proceeds slowly. The
ceiling itself and the time spent in physics, scripts, rendering or OS scheduling
were not recorded. A specific cause or product fix is not established.

## Recomputed evidence

The named references are the actual `3c4d921` Linux plant rounds 3 and 4, the
`3b5cf764` Windows plant from run 39735001567, and the retained v0.3 fixed-work
render profiles. [audit.py](audit.py) reads original Linux receipts and the
original nested Windows archive, hashes its inputs and recomputes the intervals
in [recomputed.json](recomputed.json). It does not launch the game or modify
those inputs. No visual or shipped-game parity verdict is attempted.

| Measured bracket | Linux round 3 | Linux round 4 | Windows |
| --- | ---: | ---: | ---: |
| Initial match capture → terminal action, driver seconds | 118.084 | 117.274 | 49.359 |
| Observed authority ticks / drawn frames in that bracket | 2,600 / 325 | 2,600 / 325 | 2,639 / 565 |
| Observed ticks per drawn frame | 8.000 | 8.000 | 4.671 |
| Resolved capture → failure or accepted next buy, driver seconds | 12.053 | 12.052 | 4.843 |
| Observed authority ticks / drawn frames in that bracket | 247 / 31 | 247 / 31 | 286 / 59 |
| Observed simulation seconds in that bracket | 4.116667 | 4.116667 | 4.766667 |
| Terminal phase / round | POST / 1 | POST / 1 | BUY / 2 |

Each action contains an associated engine observation, which may precede the
action. The elapsed bracket uses only the driver clock. Ratios combining the
observed frame/tick deltas with that bracket are descriptive rates, not precise
frame-time distributions or synchronized cross-clock latency measurements.
In particular, the MP4's 10 Hz capture rate is not the game's draw rate.

The engine observation starts at tick 25 / drawn frame 6 and ends at tick 2625 /
frame 331 in each Linux run. Their initial-capture-to-failure simulation advances
43.333333 seconds, including buy, live, planted and post phases. Slow advancement
therefore predates the next-round wait. The POST bracket's observed draw rate is
about 2.572 frames per driver second. Its terminal timer remains positive at
0.650000000000013, with focused/unpaused UI. Both original failures and the
unreached restart remain failures; this audit changes no gate.

The Linux client logs select Mesa llvmpipe through GL Compatibility. The frozen
controller explicitly sets `LIBGL_ALWAYS_SOFTWARE=1` and `LP_NUM_THREADS=2`.
Both runs use the same exported ELF and clean shipping content hash
`f148106d4ed189f2a5d49e798f55bf0fb30f612126ec203037377f88d332855e`.
The no-recorder attempt reaches the same tick/frame endpoint and positive POST
timer. This still supplies no recorder-only explanation.

Windows independently proves the same shipping content can progress naturally
to next buy within the original twelve seconds. Its renderer is **ANGLE on
Microsoft Basic Render Driver**, also a software path. Its actual command,
captures and final window readback are **976×549**, while Linux is **1280×720**.
The initial graphics settings agree: Standard, render scale 1.0, FPS limit 60.
The receipts do not expose the actual 3D render-target dimensions. Different
native extents, renderer stacks and hosts prevent treating these attempts as a
controlled Linux-versus-Windows performance experiment or physical-GPU evidence.

## Source and previous performance evidence

`game/scripts/gameplay/match.gd` is byte-identical between frozen Linux source
`3c4d921` and this investigation's `ba5013d` base; SHA-256 is
`2db21ed6eb27d2095e899db836b417288c8a96e5e3239c8aa7affa6bb6a54173`.
The inspected main controller, arena and project settings also have no diff
between those sources. `_physics_process(delta)` advances match elapsed and
authority ticks. `_end_round` selects POST and sets five seconds;
`_authority_tick` subtracts physics delta and calls `_begin_round` when the timer
reaches zero. The observed POST timer has not reached that condition. These
receipts do not demonstrate a faulty timer or a failed `_begin_round` invocation.

The project requests 60 physics ticks per second. `apply_settings` selects the
stored FPS limit, 2× MSAA, full render scale and shadows for Standard. Neither
the project nor inspected game/scripts set `Engine.max_physics_steps_per_frame`.
Its actual native readback is missing. Eight observed ticks per drawn frame is
consistent with a ceiling of eight; this report does not substitute an assumed
engine default for that readback.

The existing `PERFORMANCE-0.3.md` and three-run raw profiles already measure slow
software presentation without match simulation. Standard fixed-view medians are
472.588–561.950 ms in the retained current fixture, versus 337.987–463.606 ms
in its older pre-art fixture. They use two pinned CPUs, two Mesa workers,
1280×720, five actors, four fixed cameras, eight warmup frames and 24 samples per
view. Bots and match simulation are absent. This makes renderer work a concrete
diagnostic target, but those old fixtures have different source, cameras,
actor count and CPU-affinity conditions from the failed plant. They cannot
attribute the current failure or establish a new UI regression. Their separate
Low-preset measurements are retained evidence, not a proposed acceptance
workaround. Prior source comparison also leaves the arena and graphics-selection
block unchanged across the named Relay AR integration anchor.

## Preregistered next diagnostic

First review a small **readback-only extension to existing debug/offline
observations**, then freeze its exact source before a separately coordinated
native slot. Keep the existing ordinary plant scenario, seed 42, actor count,
1280×720 native extent, Standard settings, render scale 1.0, FPS limit 60,
60 Hz physics, time scale 1, two Mesa workers, no recorder and every original
180/15/12-second deadline. Retain source/artifact/controller hashes and original
success or failure outputs. A diagnostic failure does not close the plant gate.

1. Add fields only to the existing `SBOfflineDiagnostics._snapshot` under its
   current debug/offline admission. Read `Engine.max_physics_steps_per_frame`,
   `physics_ticks_per_second`, `physics_jitter_fix`, `max_fps`, process/physics/
   drawn frame counters, `Performance.TIME_PROCESS`, `TIME_PHYSICS_PROCESS`, draw
   calls and primitives, plus actual window/viewport/render-texture dimensions.
   Record read timestamps and monitor units. Query sizes without image readback.
   Preserve the current status cadence and file writes; add no per-tick or
   per-frame disk logging, new callbacks, frame waits or scheduling changes.
   Performance monitors provide coarse engine timings, not a GPU profile or
   complete GDScript function attribution. Their sum need not partition wall time.
2. From the already-owned client PID, collect bounded one-second external CPU
   samples into a separate file: process/thread CPU counters, PID start identity,
   allowed affinity, cgroup CPU quota/throttling counters and sampling timestamps.
   Read only the selected graphics environment keys. Missing OS facilities must
   produce explicit unavailable fields. The sampler owns no game input or state,
   exits with the validator, and records actual cleanup. No broad process sweep,
   process termination or changes to priority, affinity or quota are needed.
3. Compare long buy/live/POST observation intervals within this one run. A
   readback of eight plus a near-eight authority-tick/process-frame ratio and
   process/drawn-frame agreement would support catch-up saturation. A different
   ceiling, materially lower tick/process-frame ratio, or divergence between
   process and drawn counters rejects or narrows that explanation. Keep sampling
   boundary uncertainty explicit; aggregate drawn-frame ratios alone cannot
   prove every individual frame saturated.
4. Use timing and CPU receipts to choose the next experiment. Predominant physics
   CPU time warrants a measured authority/visual-script profile. Small physics
   time with long presentation intervals and high Mesa-thread CPU time warrants
   an isolated unchanged-camera renderer profile. Rising cgroup throttling or
   CPU descheduling warrants a matched serialized host comparison. Mixed or
   unavailable counters leave attribution open. No result permits silently
   extending deadlines, increasing catch-up steps, lowering physics frequency,
   changing time scale, reducing quality or editing the arena to obtain a pass.

This is a diagnostic proposal, not implemented instrumentation or a runtime
verdict. The largest remaining gap is the absence of same-attempt engine-stage
and OS-scheduling measurements under the failing Linux workload. Obtain those
receipts before choosing a product change, and have a fresh critic review the
raw outputs and original deadline result. Physical-GPU pacing, sustained device
performance and the broader G19 gate remain externally blocked.

## Reproduction and verification

```sh
python3 docs/reports/gauntlet/m1-linux-frame-diagnostic/audit.py > /tmp/linux-frame-audit.json
cmp /tmp/linux-frame-audit.json docs/reports/gauntlet/m1-linux-frame-diagnostic/recomputed.json
git diff --check
```

The audit passes its raw-source/settings equality, native failure/pass,
phase/round, 60 Hz tick/elapsed and exact Linux frame/tick-delta assertions.
Only this report, its recomputation script and generated evidence are changed.
PR26 map content and contributor-owned source remain excluded. This investigation
has no independent acceptance verdict yet.
