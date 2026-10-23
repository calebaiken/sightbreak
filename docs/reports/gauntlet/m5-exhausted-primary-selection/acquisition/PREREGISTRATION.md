# Bounded candidate acquisition wrapper

Source-only component after candidate source acceptance
`66f31a6778930fb16de41594ec0bd11b7a70189a`, exact accepted candidate
`1b7ebc71290e6c4c23017f7a2d8539d7c5eec149`. Product, common probe, derived
test and policy auditor stay unchanged. No engine, import, GDScript compile,
native command or service is authorized here. A fresh independent critic must
review this concrete wrapper before root releases either block.

The wrapper will live in this own acquisition report directory. It will accept
only `--block candidate` or `--block regressions`, the exact source checkout,
a full immutable expected HEAD and a fresh output under that checkout's
ignored `.local`. The wrapper must itself be tracked in that clean checkout.
Both the game/scripts trees and the accepted candidate manifest bytes must
match `1b7ebc7`; adding this wrapper does not authorize product/test changes.
The concrete commands, once the wrapper freeze is committed, are:

```sh
python3 -B docs/reports/gauntlet/m5-exhausted-primary-selection/acquisition/run_acquisition.py --source /workspace/sightbreak-exhausted-primary-selection --expected-head <FULL_REVIEWED_WRAPPER_COMMIT> --block candidate --output /workspace/sightbreak-exhausted-primary-selection/.local/exhausted-selection-candidate-r1
python3 -B docs/reports/gauntlet/m5-exhausted-primary-selection/acquisition/run_acquisition.py --source /workspace/sightbreak-exhausted-primary-selection --expected-head <FULL_REVIEWED_WRAPPER_COMMIT> --block regressions --output /workspace/sightbreak-exhausted-primary-selection/.local/exhausted-selection-regressions-r1
```

These are separate one-shot blocks, with no automatic transition between them.
Root must release each explicitly. An exclusive per-HEAD/block journal in
`.local` prevents an adaptive retry merely by choosing another output path.
An existing output or journal is preserved and rejected before native launch.
No retry, `--observe`, threshold adjustment, verbose repeat or extra suite is
available. Setup failure also consumes that block's claim at that HEAD.

## Commands and fixed budgets

The sole executable is
`/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64`, SHA-256
`8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`.
Hash it before and after; do not add a version invocation. This wrapper is for
the sole local Linux lane. A recognized existing Godot process prevents launch.

Every native command has the common prefix
`<PINNED_ENGINE> --headless --audio-driver Dummy --path <OUTPUT>/staged/game`.
Their suffixes and order are fixed:

| Block | Stage | Suffix | Phase cap |
| --- | --- | --- | --- |
| Both | Native producer before first suite | `--script <OUTPUT>/producer.gd -- --receipt=<OUTPUT>/<suite>-before.json` | 30 s |
| Both | Sole preparation import | `--editor --import` | 120 s |
| Candidate | Maintained candidate | `--script res://tests/bot_exhausted_primary_test.gd` | 120 s |
| Candidate | Native producer after candidate, only on strict success | `--script <OUTPUT>/producer.gd -- --receipt=<OUTPUT>/bot_exhausted_primary-after.json` | 30 s |
| Regressions | Existing AI | `--script res://tests/bot_ai_regression_test.gd` | 120 s |
| Regressions | Existing dry-weapon | `--script res://tests/bot_dry_weapon_test.gd` | 120 s |
| Regressions | Existing squad-symmetry | `--script res://tests/bot_squad_symmetry_test.gd` | 120 s |

The regressions run in that order. Each has its own native producer before
and, only on strict success, after. The first before probe precedes the one
shared preparation import; later suites reuse that imported staged project.
There is no second import and no suite retry. These producer commands are
actual native startup measurements, not Python assertions about a path.

The candidate block has a **240 s whole bound**, including staging, probes,
import, fixture, pure raw audit and normal finalization. Every phase is capped
by its own cap and the remaining whole budget. The separate regression block
has a **480 s whole bound**, including the single preparation, six producer
probes, three suites and normal finalization. Its time does not extend the
candidate's 240 s budget. A Linux real-time alarm protects the whole block;
native phase polling enforces its smaller phase deadline. On interruption or
timeout, allow at most 5 s scoped process cleanup and 5 s emergency receipt
finalization, with no new engine launch. Exceeding a normal bound stays failed.

## Source, preparation and native userdata

Mechanically copy only every tracked game file from the exact clean source,
checking source bytes against Git and SHA-256. Keep a full index inventory,
hashes for present sparse files and a source-to-stage map. Preserve source and
copy hashes before/after all stages. The shipping project configuration stays
byte-identical: Linux XDG data/config/cache and Android homes are private under
the fresh output and distinct per suite. HOME and proxy settings are preserved.

Use the already accepted native userdata probe literal from
`scripts/run_native_regressions.py`, placed outside the staged project. Validate
its actual `OS.get_data_dir()`, `OS.get_user_data_dir()`, project path and
settings against the private Linux application directory. Reject profile or
diagnostic leftovers before a suite. Before/after producer paths must agree;
retain receipts and any resulting userdata files. This block touches no
canonical player state and deletes no evidence or user directories.

The derived test currently has no tracked UID. The preparation may add only
`game/tests/bot_exhausted_primary_test.gd.uid` outside `.godot` cache. Retain
that generated file, its hash, the complete stage inventories and first
observed preparation boundary. Every originally copied tracked file must stay
byte-identical. Report original-byte equality and the added UID separately;
never call an enlarged staged source set identical to the original. After
preparation, that prepared non-cache set must remain unchanged. Any other
added/removed/changed non-cache source fails the block.

## Stop policy, output and cleanup

Use `native_log.failed()` on the complete original stdout and stderr, including
ObjectDB/typed-leak warnings. Retain both streams and hashes. A derived combined
classification log concatenates the streams; it does not claim cross-stream
temporal order. No exit-0-only or validate.sh-only approval is sufficient.
Producer, import, phase-bound, source or cleanup failure stops all later
native stages in the block. A failed suite gets no after-producer launch and
no later suite. A candidate stdout, even from a strict leak failure, may still
receive the unchanged pure all-row resource/authority audit and comparison if
time remains; its result stays separate from strict failure. No complete or
missing raw result can override a strict failure.

The candidate requires exact 1,268-row registration, the 51/516 matrix and
15/57 sequence boundaries, all original positive controls and the new actual
24 m fire/reload controls through `audit_candidate.audit()` plus `compare()`.
Keep their receipts as builder checks, not independent acceptance. Existing
regressions require their unique success markers; dry weapon retains 84 cases,
48 steps, 590 checks; squad symmetry retains 960 samples, 2,722 checks, zero
failures in assertion mode. An incomplete marker or extra failure stays failed.

Every native process starts a new session. Record exact command, UTC/monotonic
start, PID/start ticks, PGID/SID, observed identities, exit, timeout, signals
and terminal scans. Track currently discoverable descendants and same-session
members, with stable identity checks; signal only verified owned identities,
using Linux pidfds to avoid PID-reuse signal races. Unexpected surviving
members or any forced cleanup fail the phase even if cleanup succeeds.
The helpers retain a concrete scope limit: an unobserved descendant that
escapes/reparents between scans can be missed. No generic descendant or
unexercised failure-path guarantee follows from a clean normal run.

Wrap process creation, registration, exceptions, signals and finalization in
cleanup/failure receipts. Preserve the original failure if later source or
receipt finalization also fails. Pure mocked controls should cover strict leak
classification, phase/whole limits, one-shot rejection, producer identity,
generated UID classification, non-cache corruption, launch/registration/wait/
cleanup failures, interruption and observed PID reuse. They launch no engine
or child process. No native/audio failure is reclassified by such mocks.

The baseline and verbose diagnostic remain strict failures. This wrapper
changes no audio owner, wait, shutdown behavior, game/test policy or criterion.
Actual output must go to a fresh independent critic before root integrates
or accepts selection behavior. Full matches and release gates remain open.
