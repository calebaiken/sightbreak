# Linux frame diagnostic native result

The diagnostic receipt is complete. The original Linux player-plant journey
still **FAILS** its twelve-second next-round deadline. Exact runtime source is
`8afe0cc6b4c9051d3649a82bbcb4c8de8f947f9c`; raw evidence is committed separately
as `c0bf287`. No performance fix, complete plant pass or Linux release
qualification is claimed.

The run confirms the previously missing catch-up limit of eight, matching the
sustained eight-authority-ticks-per-drawn-frame trajectory. It also records long
process/render-window maxima, short individual physics-step maxima and most
observed client CPU time in llvmpipe-named workers. The readable cgroup has no
new throttling during the sampled interval. These receipts support a renderer/
process profiling investigation. They do not identify an expensive shader,
render pass or script function.

## Exact source, execution and preserved failure

Preregistration `e71e5d4` precedes source `8afe0cc`. A fresh critic independently
accepted that source for the bounded diagnostic in `e3dd5b1`, including eighteen
builder and eight independent sampler controls, four existing role controls,
fifteen capture controls and refetched pinned API evidence. Source acceptance
does not accept the product gate.

The executable is 84,232,632 bytes, SHA-256
`4f914edf046db5a4edff06aa165b70edf0c6e82ba70e7a411d4a577f4caf2189`.
Its manifest records game tree `4510bbb4ee295f96b6e9245aeb253288611bf1ee`,
shipping-content SHA-256
`f61d63f00b841cf243af747d8d198f164167f115d2b1bc04a1619bd548cdaa50`
and validation SHA-256
`b88317bf83633858eb02ca8a771be4eeec68e453c270a12fa91ae2375a42a73d`.
The actual engine is `4.7.2.stable.official.ed1daf0bf`. The editor binary is
rehash-matched to its member in the checksum-pinned cached editor archive.

Actual order was maintained import/export, existing offline-diagnostics source
fixture, then native plant. Import/export passed in 4.927 / 3.374 seconds; the
fixture passed sixty checks with zero failures in 0.867 seconds. The source
handoff had proposed fixture-first ordering; the cold checkout instead used the
maintained export's import stage before running that fixture. Raw commands and
timestamps retain the actual order. No fixture result was inferred from export.

The first preflight stopped before any engine call because the builder compared
the binary SHA-512 with the archive's expected SHA-512. That assertion failure
is retained explicitly. The corrected preflight verifies the archive hash and
then compares the extracted member with the installed binary. It does not relabel
the failed preflight as a native attempt.

Root released the local lane after its aggregate and the PostgreSQL parser run.
One plant attempt used fresh private state/output and Xvfb display `:122`, with
no recorder launched. The original driver command was:

```sh
python3 scripts/verify_offline_match.py --target linux --scenario plant \
  --timeout 180 --linux-frame-diagnostics --display :122 \
  --xvfb /workspace/tools/xvfb/usr/bin/Xvfb \
  --output /workspace/sightbreak-linux-frame-sampling/.local/linux-frame-sampling/runtime-r1/native-plant
```

The client command and sampler's selected child-environment readback agree on
ordinary plant/seed 42, software rendering, two Mesa workers and 1280×720.
Initial profile settings retain Standard, full render scale and FPS cap 60.
Every available frame observation confirms actual cap 60, 60 Hz physics,
catch-up limit eight, jitter 0.5, render scale 1 and 1280×720 viewport/output
texture. Every observed time scale is one. The native log identifies Mesa
llvmpipe through GL Compatibility. No quality, scheduling, physics, timeout,
scenario or authority state was changed to obtain a pass.

The ordinary interrupted E hold resets; the completed plant consumes 180 ticks /
three authority seconds, awards one contribution and moves funds 800→1100. The
original living guidance PNG shows `DEFEND THE DEVICE`, 100 health, 1100 funds,
the planted device and combat feed. The later PNG shows POST, defused device,
score 0:1 and eliminated spectator. Natural defender defuse is retained in the
authority event stream. The full driver fails at
`Natural next round after objective resolution` after 132.337 seconds. The
restart checks are unreached.

## Baseline and current observations

| Original-budget plant observation | Prior Linux round 3 | Prior Linux round 4 | New diagnostic |
| --- | ---: | ---: | ---: |
| Frozen source | `3c4d921` | `3c4d921` | `8afe0cc` |
| Original whole result | FAIL | FAIL | FAIL |
| Initial capture → failure driver seconds | 118.084 | 117.274 | 120.227 |
| Associated tick / drawn-frame delta | 2,600 / 325 | 2,600 / 325 | 2,600 / 325 |
| Resolution capture → failure driver seconds | 12.053 | 12.052 | 12.053808 |
| Associated tick / drawn-frame delta | 247 / 31 | 247 / 31 | 247 / 31 |
| Final POST timer | 0.65 | 0.65 | 0.383333 |

The current source also contains root's accepted receipt UI work. These are
unmatched sequential attempts, with no claim that instrumentation changed
performance. Natural resolution timing can differ; identical aggregate tick/
frame endpoints do not make all internal match events identical. The driver
bracket and engine observations use distinct clocks. Engine observations may
precede their associated action, so these are observed aggregate ratios, not
precise frame-time or cross-clock latency measurements.

The new POST bracket advances 247 ticks / 4.116667 authority seconds across 31
drawn frames. Final state is tick 2625 / round 1 / POST with
0.383333333333346 seconds remaining. The sampled process and drawn counters agree
throughout. The actual readback of eight plus the long-run ratio of exactly eight
ticks per drawn frame supports sustained catch-up saturation while presentation
is slow. Sampling within a physics batch leaves boundary uncertainty; the audit
does not prove the count of physics steps in every individual frame.

## What the new timing and CPU receipts establish

The owned worker wrote 132 samples and stopped without error. Its summary records
`sampling_completed=true`, `thread_alive=false` and `reason=controller_stop`.
This is separate from the original gameplay `passed=false` result.

Cadence is 1.000720–1.007352 seconds between successive sample starts, median
1.001302. External collection duration is 0.365–2.527 ms, median 0.902 ms.
There are 123 available frame observations. The first nine samples explicitly
report the not-yet-created offline status file as unavailable. No engine frame
value is substituted for those missing samples. Internal 3D target size remains
explicitly unavailable in every available frame row; the recorded dimensions
are viewport/output texture sizes.

| Available phase rows | BUY, 39 | LIVE, 71 | POST, 13 |
| --- | ---: | ---: | ---: |
| Median published process-window maximum, seconds | 0.321656 | 0.382271 | 0.389913 |
| Median published largest-physics-step maximum, seconds | 0.001572 | 0.002158 | 0.001692 |
| Median getter-collection duration, microseconds | 14 | 13 | 15 |

Godot publishes these timing maxima at its roughly one-second statistics
refresh; they can repeat and lag a phase transition. Process timing includes
process callbacks, renderer synchronization and draw. Physics timing measures
the largest individual step in that window. They do not partition frame time,
and their medians cannot be added or subtracted to attribute GPU/script cost.
The getter duration excludes JSON serialization, existing file writes and the
external sampler. It is not a measured whole-instrumentation overhead.

Across the POST sample bracket's own 12.018730 monotonic seconds, the process
accumulates 23.68 CPU seconds. Threads categorized by llvmpipe names accumulate
22.62 CPU seconds; the main thread accumulates 0.79 and other observed threads
0.26. CPU time can exceed wall time across workers. Per-thread deltas cover each
thread's first-to-last observations and need not sum exactly to aggregate
process CPU. This supports software-rasterizer work as the dominant measured
CPU category in that interval, while the process monitor still includes other
work. Thread names alone do not identify the expensive rendering feature.

Readable cgroup v2 root quota is 400000/100000 microseconds, equivalent to four
CPUs. Its observed `nr_throttled` and `throttled_usec` deltas are both zero.
Historical cumulative throttling is not evidence of throttling during this run.
These shared cgroup counters may include other processes and expose only the
readable namespace; they do not exclude every kind of host scheduling delay.
The selected proc/thread/affinity/quota/stat counters are available throughout.

## Ownership, archive and remaining work

Sampler and live critic observations bind client PID 137048 to start-time tick
3158785 and its exact exported executable. The sampler header records controller
PID 137004, SC_CLK_TCK 100 and the selected child environment. Its output retains
only the declared environment and numeric offline-frame whitelist; no account,
profile or actor object is copied into sampler rows.

Bounded failed-scenario cleanup terminates the client with exit -15; Xvfb exits
zero. The owned client/Xvfb proc entries and display socket are absent afterward,
the sampler worker is stopped, and the controller reports no cleanup errors.
Post-run source remains clean and identical to `8afe0cc`; its manifest still
validates before evidence files are added. These are failure cleanup receipts,
not a normal successful game close/restart.

[native-r1/payload-index.json](native-r1/payload-index.json), SHA-256
`002a01a91b1da23733574c1f514adaa954bd2a75ff326eeab1ac657abe216463`,
binds 33 retained original files / 3,607,695 bytes. It includes runtime source
copies, failed/corrected preflight, export/fixture/controller output, commands,
actions, events, status, all eight original PNGs, every sampler row and cleanup.
Generated private caches/state are omitted. The executable remains retained in
the worktree's build directory and bound by the archived manifest.

[audit_native.py](audit_native.py) verifies every payload hash and recomputes
[native-recomputed.json](native-recomputed.json) without running the game or
reading live processes. The original pre-diagnostic interval audit remains in
`m1-linux-frame-diagnostic`. Reproduction:

```sh
python3 docs/reports/gauntlet/m1-linux-frame-sampling/audit_native.py > /tmp/linux-frame-native-audit.json
cmp /tmp/linux-frame-native-audit.json docs/reports/gauntlet/m1-linux-frame-sampling/native-recomputed.json
```

The largest remaining gap is identifying the expensive full-quality render/
process work. The next supported experiment is a separately reviewed fixed-view
renderer profile reproducing the retained POST scene with unchanged graphics.
If the cost persists without match simulation, it narrows the renderer question;
if it does not, inspect live scene/controller work before selecting a fix.
Neither outcome authorizes weakening the original plant gate. No further native
attempt was run; the lane was released to root. Physical-GPU pacing, human
playability and the full Linux/RC gates remain open. Arena/PR26 content,
authority, protocol and canonical mission files are unchanged by this branch.

The fresh critic has independently recomputed the actual receipt and witnessed
owned identity/cleanup; its separate final archive verdict will remain the
acceptance record. This builder report does not approve itself.
