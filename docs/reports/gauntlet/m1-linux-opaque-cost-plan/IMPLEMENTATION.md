# Profiling-cadence diagnostic: implementation handoff

Source/pure candidate only. No engine, GDScript compilation, import, UID
generation, export, profiler, OCR or native workload ran. The shared native lane
remains reserved for root's separate bot diagnostic. Fresh exact-source
implementation review is required before preparing or running this experiment.

This own branch, `diagnostic/linux-profile-overhead-fixture`, starts from plan
`8b0598c40efaa98883ec2ef3f5f74cd499ebf3ce`. It applies independent plan review
[`fcb5276c`](https://github.com/calebaiken/sightbreak/blob/fcb5276ca620c86a1a1342e9ac1dd32bec4eecff/docs/reports/gauntlet/m1-linux-opaque-cost-plan/independent-plan-review/REVIEW.md).
The corrected [registration](PREREGISTRATION.md) preserves OFF/ON/ON/OFF, 32 warm
and 64 measured intervals, 10%/0.90 ratio boundaries and the original drift
screens. Shipping game bytes, `verify_offline_match.py`, its options/deadlines,
and canonical mission files are unchanged. No shipping optimization is proposed.

## Concrete files and temporary overlay

- `scripts/diagnostics/linux_profile_overhead.gd` and its `.tscn` define an
  unshipped static five-actor `approach` fixture. The world is disabled for
  automatic processing after construction. There is no match/authority/bot/
  visual tick. Authored arms already use manual AnimationPlayer processing;
  their source setting remains intact. Actor cryptographic RNG is untouched
  and omitted from the visual fingerprint.
- `scripts/linux_profile_overhead.py stage` copies tracked base game files to
  a fresh external stage, excludes tests, injects only the explicit fixture,
  source ledger and main-scene overlay, sets the existing default `safe` thread
  model explicitly and requires project profile printing false. Only the stage
  project/preset changes. It does not launch an importer or exporter.
- `seal` binds a separately exported x86_64 ELF/Godot 4.7.2 pack to the frozen
  source/stage ledger and artifact hash. It does not certify an export by itself;
  actual pinned export commands/logs, PCK resources and identities still require
  independent runtime review. Base source UIDs remain covered by the inventory;
  only a newly generated staged fixture `.gd.uid` and `.godot` cache are excluded.
- `run` consumes that seal, verifies source/stage/payload integrity, selects two
  allowed CPUs, owns the isolated display and executes exactly the fixed block.
  Repository/stage identities are checked before/after every condition and the
  payload is hashed before/after every process. ON receives one engine option
  before `--`; OFF omits it. Actual owned `/proc` argv and selected graphics/XDG/
  Mesa environment must match the launch receipt. OFF stdout containing profile
  output fails; ON needs an intact finite header and positive named row.

Staging and sealing are implemented for later use, not executed in the real
workspace. Pure stage tests use a temporary hand-created mini-project and mock
the tracked-file inventory. Future commands, after source acceptance and a
separate explicit runtime release, are:

```sh
python3 scripts/linux_profile_overhead.py stage --output "$PWD/.local/linux-profile-overhead-r1/project"
# Root first coordinates pinned import/export of exactly that staged project,
# retaining full commands, private export state and template/source identities.
python3 scripts/linux_profile_overhead.py seal --stage-record "$PWD/.local/linux-profile-overhead-r1/project-stage.json" --executable /exact/fresh/diagnostic.x86_64 --output "$PWD/builds/linux-profile-overhead-seal.json"
python3 scripts/linux_profile_overhead.py run --seal "$PWD/builds/linux-profile-overhead-seal.json" --output "$PWD/builds/linux-profile-overhead-r1" --xvfb /workspace/tools/xvfb/usr/bin/Xvfb --display :UNUSED_NUMBER --cpus CPU_A,CPU_B
```

The placeholders must be resolved in a later reviewed run plan. These commands
have not been run. The controller exposes no adaptive repeat, cap reduction,
warm-up extension or gameplay acceptance path.

## Post-draw boundaries and estimator

Construction-only queued deletions settle before initial fingerprinting. That
setup endpoint, a separately timed cold anchor, 32 warm intervals, 64 measured
intervals and a later readback callback have distinct retained identities.
Readiness/metrics and acknowledgement files publish atomically. Controller
hashes/library/CPU observations happen while the fixture holds before the anchor
or after readback; they do not run inside sampled intervals.

The pinned synchronous path emits post-draw before profile processing; main
increments drawn count after draw returns. Thus the cold anchor increments its
callback serial while retaining the pre-anchor drawn count. Each later interval
must chain exactly to the previous endpoint and add one drawn identity and one
callback. Duplicate/skipped counters, extra callbacks, missing/nonfinite/nonpositive
durations or wrong array lengths reject. The final proof-image readback has its
own later identity, and callback/drawn counts must stay fixed during readback.

The quantity is median warm wall cadence between consecutive post-draw
callbacks at the declared pacing. It includes previous-frame profile/probe tail,
scheduling and pacing; it does not isolate a draw call or prove GPU completion.
The safe CLI selection and project-setting evidence hold the thread model
constant. They are identified as source/argv evidence, rather than an invented
public getter of the engine's private separate-thread flag.

The evaluator uses the arithmetic mean of the middle two sorted values for an
even median, retains sample order and both endpoints, and reports cadence
sum/mean/largest interval separately. H1 still uses paired median ratios only.
Same-condition drift is `max/min-1 <= 0.05`; warm-half drift is `<= 0.10`, with
only 1e-12 floating-point boundary tolerance. All comparability rejections run
before classification. There is no new tail/mean decision threshold.

The retained explicitly synthetic sparse-stall example has 64 OFF intervals of
20 ms, and ON with 63 at 20 ms plus one at 260 ms. The median ratio stays 1.0;
mean/total ratio is 1.1875 and the largest ON interval is 260 ms. These invented
values exercise the estimator limitation; they are not observations or estimates
of stdout cost. A small median result cannot bound sparse stalls, complete
profiling overhead, uncapped render cost or the failed original gameplay wait.

## Stable work, host evidence and stopping

Initial and terminal canonical fingerprints include stable structural node
paths, local/global transforms, visibility/ranges, mesh/material overrides,
shader and instance parameters, multimesh transforms/colors/custom data,
skeleton poses, camera, lights, environment and actual settings. File resources
carry frozen content hashes; generated resource properties are traversed in
stable order and packed numeric data are hashed. Reference labels are assigned
by deterministic traversal; runtime IDs are used only for in-memory cycle
detection and never serialized. Texture pixel readback is excluded from this
traversal. An unsupported/generated texture without source identity fails closed.

The initial/terminal fingerprints, final pixel hashes, actual settings, adapter,
engine and measured visible draw/primitive counters must match across conditions.
Fingerprints include initial and terminal settings too. GDScript compilation and
actual property enumeration remain unverified; pure Python controls cannot
certify the eventual engine's fingerprint stability or pixel equality.

Every condition gets distinct initially empty XDG data/config/cache and Mesa
shader-cache paths. This controls those disk-cache paths, not page/CPU caches or
all system state. Driver-library hashes, affinity, cgroup/quota identity and
both declared throttling counters are read before/after the condition. Missing
readbacks or any counter increase/reset reject. Zero deltas do not imply an idle
host. Owned whole-process child CPU/rusage includes startup and all client
threads; it is not warm-region CPU or a partition of query intervals.

The real runner uses one isolated Xvfb, process groups and PID/start identities,
180 seconds per condition, bounded TERM/KILL cleanup and an advisory owned-lane
lock. Incomplete conditions stop later launches. Invalid-number failure
summaries retain symbolic nonfinite values without feeding repaired data back
to evaluation; original raw metrics/log files are preserved. Cleanup failure
also fails the block. This checks exact declared identities/groups, not arbitrary
escaped processes or host-wide resource state.

## Pure controls and open gap

`python3 scripts/test_linux_profile_overhead.py -v` passes 14 methods, no skips.
[Raw output](implementation-pure-controls/controller-evaluator.txt) is retained.
The hand-authored valid four-record input runs through the exact production
validator. Data mutations reject wrong/default/late flags, project profiling,
OFF profile output, missing ON capability, payload/source/driver/affinity/quota/
pixel/fingerprint/settings/cache drift, incomplete/nonfinite/nonpositive arrays,
duplicate/skipped counters/callbacks, failed warm-up/drift, timeout, throttling
and owned cleanup failure. Tests exercise all ratio outcomes and exact boundaries.

Controller mocks exercise the real OFF/ON/ON/OFF launch and stop policy, empty
paths and actual NativeRunner Popen/handshake/timeout/cleanup branches using fake
process objects. No mock test starts Xvfb, Godot or another native workload.
These are supplied synthetic inputs and control-flow checks, not an engine pass.
The [hash ledger](implementation-source.json) binds fixture, controller, tests,
scene and corrected registration. Source comparison and `git diff --check` pass.
No GDScript syntax/compile result or runtime result is claimed.

The next step is fresh implementation review at the exact pushed source.
Only afterward can root consider a separately coordinated staging/export/runtime
release. The four-process block supplies no confidence or repeatability estimate
and cannot rule out middle-only host disturbances. GPU stdout stays whole-process
corroboration without warm-phase tags, row/header sums, CPU-function attribution,
physical FPS or shipping/gameplay cost claims. Original Linux failures stay failed.
