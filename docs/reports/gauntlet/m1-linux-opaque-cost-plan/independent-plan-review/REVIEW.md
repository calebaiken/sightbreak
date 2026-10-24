# Independent review of the Linux profiling-cost plan

2026-10-23. Reviewed exact `8b0598c40efaa98883ec2ef3f5f74cd499ebf3ce`.
Verdict: **approve source-only implementation with the requirements below**.
The proposed unchanged-scene flag contrast is a useful next diagnostic. Its
current wording overstates what the timer and median can measure. Correct that
wording and make the controls executable in the implementation checkpoint.
A fresh independent review must inspect that exact fixture/controller and its
pure controls before any import, export, compilation or runtime release.

This review used retained upstream source bytes and Git objects. No engine,
workload, profiler, OCR, service, native game or compilation ran. No fixture,
controller, product source or canonical mission document was changed. The
review branch is `critic/linux-profile-overhead-plan`, in sparse worktree
`/workspace/reviews/linux-profile-overhead-plan`.

## Verified source and interpretation

[My independent audit](audit.py) and [recomputed evidence](recomputed.json)
verify all nine repository source entries and all eleven upstream source
lengths/hashes. The seven retained originals and the original critic's GLES
scene-renderer bytes equal the inspected copies. Upstream identities are those
in the plan's ledger, pinned to Godot
`ed1daf0bf001b61586d9930840f2f1394092c079`; I did not re-fetch or build an engine.
I independently recomputed all 128 shipping-file bytes from Git, obtaining
`bcb872f6998ed8504c852dee354ab0acf5b6f19e58e40717267a1927e6d68a50`.
The game tree is `55691684d31d44f1680141954bbe530443de9d1f`, identical to both
`373b6362` and `b2e0293`. The reviewed commit adds only its two plan documents.

The opaque source map is accurate within its stated limits. Shadows, list
construction, depth prepass and ordinary clears precede the opaque marker.
The interval includes pass setup and traversal, with an endpoint selected by
camera feed, sky or the next transparent marker. Texture/LTC setup, material
and shader binding, additive passes and ordinary/instanced draw submissions
support the plan's broader interpretation. The visible draw counter excludes
depth and motion-vector passes. The source cannot turn a historical averaged
label into one CPU function, draw, viewport or physical frame rate.

The triplanar/material hypothesis is also supported as source work: the helper
contains three weighted texture expressions, and the normal path reconstructs
and transforms a normal. This establishes neither executed driver instruction
counts nor feature cost. Disabling detail quality changes normal and roughness
features together. Keep that ablation outside this diagnostic.

The actual enabling and query path is:

| Pinned source | Consequence |
| --- | --- |
| `main/main.cpp:1982–1983`, `3571–3573` | Engine `--gpu-profile` sets `profile_gpu`, which calls `set_print_gpu_profile(true)`. The project setting `debug/settings/stdout/print_gpu_profile` can also enable it without the flag. |
| `rendering_server_default.cpp:364–367`; `servers/rendering/storage/utilities.h:159–171` | The setter enables both printing and `capturing_timestamps`. The flag adds the gated frame/named timestamp calls. |
| `rasterizer_gles3.cpp:112–122`; GLES utilities `:329–367` | Internal begin/end captures continue in OFF. On desktop GL, captures call `glQueryCounter`; ring reuse retrieves each query using `GL_QUERY_RESULT`. No availability test makes those retrievals nonblocking. Three slots aim to avoid waiting but do not guarantee it. |
| `rendering_server_default.cpp:136–207` | ON also constructs profiles and accumulates named task durations. Printing happens after more than one second; the printed averages and latest retained header total are separate statistics. |

OFF is a baseline with internal queries, so this experiment can screen only the
incremental flag treatment. It cannot isolate query insertion, query retrieval,
profile bookkeeping or stdout costs from one another. The retained startup and
historical profiles remain whole-process corroboration without warm-phase tags.

The original `b1a131ab` result remains FAILED. I directly reread its result bytes:
`passed=false`, `error="Objective scenario live phase"`, 58.557768 seconds,
empty `partial_checks` and `cleanup_errors`. The independent original-output
review records the 45-second initial-LIVE failure while BUY/round 1/tick 844,
with plant, next buy and restart unreached. That source differs from this plan's
game source. Its separately accepted capability, source/data and cleanup
receipts establish no profiling overhead, improvement or completed gameplay.

## Largest gap: the estimator does not bound all profiling cost

The phrase “combined incremental flag cost, including … stdout” is too broad
for a 64-frame median. In the pinned renderer, `_draw` invokes or defers
`_run_post_draw_steps` at lines 129–134. That method emits `frame_post_draw` at
line 229. Profile processing/printing follows the invocation at lines 136–207.
In the synchronous path a post-draw await therefore resumes before that frame's
profile tail. Consecutive post-draw-to-post-draw wall intervals include the
previous frame's tail, engine pacing and intervening scheduling. They do not
isolate one draw call or prove GPU completion. With a separate render thread,
post-draw steps are deferred; callback scheduling needs an explicit source-bound
interpretation too. Record and hold the actual thread model constant.

`main.cpp:5086–5096` increments `Engine.frames_drawn` after `draw` returns;
`:5174–5178` applies frame delay later. A first unanchored sample can consequently
have a zero counter delta. The fixture needs a cold/anchor draw before the 32
warm intervals, with that anchor reported separately and counted explicitly.
Do not change the registered 32 warm and 64 measured interval counts.

Rare printing stalls can also disappear from a median. The audit retains an
explicitly synthetic counterexample: 64 OFF intervals at 16.666667 ms, and ON
with the same intervals plus one 200 ms stall. The median ratio is 1.0 while
the mean/total-duration ratio is 1.1875. These invented values demonstrate an
estimator limitation; they are not measurements or an estimate of stdout cost.
The source's roughly once-per-second printing makes this limitation relevant.

For implementation, rename H1's quantity to **median warm wall cadence of
consecutive post-draw intervals at the declared pacing**, and explain the
shifted profile tail. Keep H1's 10% threshold and paired median ratios. Retain
sample order, both clock values and counter values; emit the sum/mean and
largest interval as descriptive secondary data, without new decision thresholds
or retrospective replacement of H1. A small median result cannot bound sparse
printing stalls, total overhead, uncapped render cost or the original failure.
If measuring total profiling cost remains the question, register a separate
whole-window timing method before running it.

## Requirements for the source implementation checkpoint

The fixed `approach` view, five actors, full Standard settings and OFF/ON/ON/OFF
order are concrete enough to implement. The existing render benchmark cannot
be reused unchanged: it animates actors, changes views, disables V-Sync, uncaps
frames and reuses cache paths. The new temporary overlay must preserve the
shipping game bytes and original gameplay controller/deadlines.

Implement these requirements and retain their pure test evidence:

1. **Prove the treatment.** Build exact argv with ON's one engine flag before
   `--`; OFF must omit it. Verify the project print-profile setting is false
   and the frozen fixture has no other profiling enabler. Retain full stdout:
   ON must demonstrate the capability; unexpected profile output in OFF is a
   failed control. Command-line absence alone does not prove the baseline.
2. **Make boundaries explicit.** Give the cold/anchor draw, 32 warm intervals,
   64 measurement intervals and later readback distinct identities. Reject
   skipped/duplicate drawn identities and unexpected callbacks. Probes and
   array storage must be identical; image readback, fingerprint traversal and
   file output stay outside all sampled intervals. Record render-thread mode,
   frame cap, V-Sync getter/warnings, time scale and physics settings. A getter
   alone does not prove actual pacing, which must remain an inference limit.
3. **Prove stable work.** Canonical fingerprints must encode resource content,
   shader parameters, visibility, transforms, multimesh data, camera, lights,
   environment and settings, using stable content identifiers rather than RIDs
   or process-specific instance IDs. Compare initial and terminal fingerprints
   in addition to the final pixel hashes across conditions. No authoritative,
   bot or visual-animation tick may occur after setup. The inspected actor
   configures cryptographic RNG state; do not serialize that unused state as
   visual content or modify shipping randomness to force equality. The arms
   player is already configured for manual processing by `weapon_model.gd`.
4. **Define the numerical screens.** Use the arithmetic mean of the two middle
   sorted values for each even-length median. State drift as
   `max(a,b)/min(a,b)-1 <= 0.05` for same-condition medians and `<= 0.10` for
   the two warm-up halves. Require finite positive durations and exact array
   sizes; keep all samples. Apply source/scene/cleanup/comparability rejection
   before ratio classification. Keep the preregistered 1.10/0.90 boundaries.
5. **Exercise real rejection paths.** A hand-constructed valid four-record
   fixture must pass the same validator used for eventual runtime data.
   Mutations must reject wrong flag placement, flag-on-by-default, altered
   settings/payload/driver/affinity/pixels/fingerprints, incomplete arrays,
   nonfinite or nonpositive values, duplicate/skipped counters, failed warm-up,
   excess drift, timeout, missing profile evidence, increased throttling and
   failed owned cleanup. Include boundary values and all ratio outcomes.
   Mock the controller's process runner so these tests prove the actual launch
   and stop decisions without starting an engine. A renamed copy of the
   validator's boolean result is not an independent control.
6. **Make isolation auditable.** Enumerate the fresh per-condition XDG data,
   config/cache and Mesa shader-cache locations and their empty initial state;
   hash the one reused payload before and after each condition. This controls
   application/driver disk-cache paths, not the host page cache, CPU caches or
   all system state. Hold the Xvfb/driver/CPU/quota choices fixed, serialize the
   owned lane, and define cgroup counter deltas and missing-readback rejection.
   Any increase in the declared throttling counters invalidates comparability;
   zero deltas cannot establish an otherwise idle host. Require bounded cleanup
   by exact owned identities and stop the block on an incomplete condition.

These controls can be source-reviewed and exercised with synthetic records and
mock process calls. They do not validate the eventual engine's behavior; actual
conditions, package identity, image equality and cleanup require separate
original-output review after an explicitly released runtime block.

OFF/ON/ON/OFF provides two opposed local contrasts and screens gross drift.
Matching OFF endpoints and matching ON middle runs cannot rule out a middle-only
host disturbance, CPU-frequency changes or shared-host contention. Four fresh
processes supply one screening block, with no statistical confidence,
repeatability estimate, hardware/physical-device qualification or gameplay
parity. The fixed warm-up can fail to stabilize; fresh empty disk caches do not
prove cold hardware state. The 180-second bound may truncate even a five-actor
software-render workload and must remain a stop condition, with no adaptive
warm-up, cap change or retry.

Positive and negative synthetic controls establish that the eventual evaluator
honors the declared boundaries. Runtime same-work fingerprints/pixels and
same-condition drift screens bound interpretation, while ON profile output
establishes capability. They cannot prove absence of shared-host confounding.
If both ratios clear 1.10 with every control passing, report a flag-associated
median cadence increase in this block and fixture. If both fall in the declared
small-effect band, report only that the block did not resolve a 10% median
cadence increase. All other outcomes remain unresolved. Neither result supplies
a causal fix, authorizes a renderer ablation or changes any release gate.

The next reviewable deliverable is the frozen temporary fixture/controller,
updated estimator registration and the passing/rejected pure-control receipts.
Runtime, export, compilation and game optimization remain unreleased.

## Review checks and retained setup failures

`python3 .../independent-plan-review/audit.py` passes the independent byte/tree
checks and synthetic arithmetic above. `git diff --check` is the document
whitespace check; no product test suite ran because product bytes are unchanged.
One shell read failed before execution when the exec-server transport briefly
disconnected; the successful retry read retained source only. One initial search
used nonexistent `game/scripts/visuals/*` paths and exited 2. `rg --files` located
the actual `gameplay`/`ui` paths, which were then read. Neither setup failure
started a workload or changed original evidence.
