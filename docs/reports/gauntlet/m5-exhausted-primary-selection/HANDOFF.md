# Exhausted-primary selection source handoff

This candidate is source and pure-check work only. Product/test savepoint
`eb02a62cd5c6cf22bb6901f89f35e4118d05a0b4` follows preregistrations `44c381d`
and `2624815`, all pushed on `codex/m5-exhausted-primary-selection-20261023`.
The own worktree is `/workspace/sightbreak-exhausted-primary-selection`, based
on root `c7c95521200490305ff035e01951215b5980e4bb`. No engine, import,
GDScript compile, candidate native output, export or service ran in this stage.
Fresh source review and root's explicit runtime release remain required.

`bot_ai.gd` adds ten lines. The existing `<20 m` fallback remains literal and
unchanged. The extension requires an enabled profile, a stock active primary
with authoritative clip/reserve both zero, owned sidearm with a recorded
positive holstered clip or reserve, and no interaction. An acquired target
must be within the sidearm's existing inclusive 45 m center-distance range;
no acquired target also qualifies. Easy remains disabled. Missing sidearm
state never qualifies for the extension. The previous known-dry primary-return
block, all profiles, actor authority, weapon definitions and audio remain
unchanged. This is a selection request, consumed by the ordinary draw/reload/
fire paths; it changes no weapon or difficulty value.

The old `b87afb7` diagnostic is copied byte-for-byte as
`game/tests/bot_exhausted_primary_probe.gd`, SHA-256
`540d24dda8e58f4685030e81b55ac3778ccbf31a89f76f9873ac598c32770731`.
Its prepared UID is copied from the actual baseline preparation output, with
matching SHA-256; it was not generated here. The new derived policy test has
no generated UID yet. It reuses all original 567 matrix / 576 sequence / 96
control rows and adds separately tagged supplements. No original pose, seed,
resource, health, timing, visibility or assertion was changed in the common
probe.

The maintained `bot_exhausted_primary_test.gd` adds a request assertion to each
actual row, then requires genuine sidearm shots and matching consumed rounds
without impossible reload repetition in all six normal/hard 24 m loaded
sidearm sequences. It also adds nine hard range cells at 44.9/45.0/45.1 m and
a 20-step normal 24 m reserve-only sidearm control. The latter requires one
actual draw, accepted 1.45 s reload, legal 0/15 → 15/0 completion at step 14,
no shots/damage, unchanged target and no impossible reload loop. The test
retains the original real kill/reward and four completed reload controls.
The total is 1,268 rows; common counters remain 1,239 plus separate supplement
counts. Both existing maintained registries call the derived policy test with
the existing Dummy-audio convention. They do not suppress strict leak checks.

The baseline bar is actual `700abf8`, with independent actual review `b5fa18a1`.
Its actual raw stdout SHA-256 remains
`e6606c22b5d5cc5c33090a97b1a832e60a376465a0edfa112146b7f743b10d7f`.
The exact baseline inputs predict 51 changed and 516 preserved matrix requests,
and 15 changed / 57 preserved first sequence requests. Normal's 45.5 m target
is outside vision, so that sequence qualifies as no target. Hard acquires the
same enemy and must preserve its beyond-range guard. Likewise the 60 m enemy
is not acquired and no hidden coordinate is used to choose the sidearm.

`audit_candidate.py` is a disclosed builder adaptation of the independently
reviewed `b5fa18a1` all-row auditor. The original reviewer file is untouched;
`AUDITOR_ADAPTATION.diff` retains the full changes. Thirteen original pure
geometry/math/helper ASTs remain identical. The adaptation extends exact
registration, selection predictions and new mandatory controls, keeps the
full resource/action/geometry/event reconstruction, and compares allowed
changes with immutable baseline rows. It demands 516 preserved matrix action
outputs, 57 preserved complete sequences and all 96 original control actions.
The 15 changed sequences receive independent per-row action/resource checks;
their later firing and damage can legitimately differ. Frame counters and
global event serial offsets are process-dependent, so the cross-run equality
comparison excludes them while the all-row audit separately verifies their
settlement and event order. It excludes auto-generated Node names from equality
and checks actual world-hit positions instead.

This adaptation is a builder audit, not fresh independent acceptance. Its full
candidate path has not consumed a legal candidate native run yet. Terminal
fixture assertion totals are reported rather than independently totaled;
acceptance comes from reconstructed rows and mandatory witnesses. Intermediate
planning event-array counts remain unlogged, as in the original probe. Those
source fences cannot be proved from a transient raw phase that was not emitted.

Ten pure unittest methods pass. They cover the exact retained-input forecast,
range boundaries, difficulty/interaction/resources/ownership guards, old near
semantics, active-field precedence, unknown/default distinction and preserved
primary priority. They reject the original output as a candidate missing the
new controls, unchanged baseline commands as an improvement, and missing
matrix identity. These are source/oracle tests, not emitted candidate actions.
`pure-checks/receipt.json` retains exact commands, exit codes and streams,
and the pure forecast lists every intended changed cell. Additional source
checks confirm unchanged protected files, common probe bytes, old near and
primary-return blocks, and both registrations. Creating the retained diff
uses Git's ordinary exit 1 for differing files; this is not a failed game test.

The review command for a future actual derived-test stdout is:

```sh
python3 -B docs/reports/gauntlet/m5-exhausted-primary-selection/audit_candidate.py --baseline docs/reports/gauntlet/m5-exhausted-primary-benchmark/actual-r2/baseline-probe.stdout.log.gz --source /workspace/sightbreak-exhausted-primary-selection --candidate /absolute/path/to/candidate.stdout.log
```

That command starts no engine. A later candidate run still needs root-selected
fresh staging/private state, pinned engine/hash, source before/after identity,
complete raw streams, actual PID/start/exit and scoped cleanup under the
registered 120 s import / 120 s test / 240 s whole bounds. No such attempt is
authorized by this handoff. Fresh actual-output criticism must consider the
strict native log and receipt independently of this parser.

The original baseline remains a strict failure from two unidentified ObjectDB
instances at exit. The separate verbose diagnostic also remains failed, with
typed WAV playback/stream leaks and an orphan StringName; common ownership and
cause are unproved. The selection change does not fix or suppress those
failures and does not block their separate audio investigation. Also unmeasured
are representative full matches, moving aim, real acquisition/occlusion,
multiple owned usable primaries, active reload entry into the new guard and
human difficulty/feel. No whole G1/G2/G9/G17 gate closes here.
