# Final independent source verdict: REJECT

Target: `0f478a078277fdb0d711837bef67cf14262d9d8f`; handoff:
`99a864a8e1ab05d25ba0f0db92552326377e2a00`. This is the same existing critic
thread, reused explicitly, independent of the builder. The review accepts no
native execution, Windows qualification, resource-lifetime fix, or public study
collection. Public collection remains **BLOCKED**.

The default reader now rejects missing receipts and the wrapper permits the
unchanged driver's empty-output guard. Those improvements are supported. Source
acceptance is withheld because the reader also calls contradictory evidence
complete, rejects an equivalent permitted output spelling, and the wrapper can
overwrite its publication receipt without reporting failure.

## Findings and source links

Both initialized views reproduce the following results. `own-independent` and
`depth-independent` retain the exact baseline, each case's `INPUT.json`,
`CONTEXT.json`, `RESULT.json`, changed bytes/removals, and unmodified failure
stderr. These are synthetic format controls, never corrupted native recordings.

| Finding | Retained controls | Frozen producer requirement |
| --- | --- | --- |
| Four named-capture contradictions receive `strict_passed=true` and `evidence_complete=true`. | `capture-wrong-phase`, `capture-wrong-actor`, `capture-missing-two-frames`, `capture-dead-after-capture` | `verify_offline_export.py:93` requires the named living actor, buy phase, round and focus context; `capture_living_phase` at line 114 requires two additional drawn frames and validates subsequent snapshots. The new reader at `shutdown_study_evidence.py:322` checks receipt identity/schema and budget presence, without enforcing those snapshot relationships. |
| Five HUD/source-constant contradictions receive the same complete/strict acceptance. | `pause-not-paused`, `paused-time-advanced`, `reload-deadline-false`, `reload-watchdog-bool`, `settings-living-false` | The default driver's HUD pause checks at line 460 require an actual paused state and frozen elapsed/health. Its reload receipt at line 729 emits watchdog **15** and unchanged-deadline **true**; settings at line 868 emits same-living-player **true**. The new reader's `hud_and_subreceipts` at line 401 primarily requires keys and snapshot shape. |
| Five callback/accounting contradictions receive complete/strict acceptance. | `wrong-callback-job-label`, `job-before-callback-clock`, `missing-active-identities`, `controller-birth-u65`, `controller-handle-u65` | `windows_shutdown_study.py:192` constructs the outer callback clock before `owner.query('trialN/event')`. `WindowsOwner.query` at line 79 emits the label, current clocks and captured active identities. Controller birth uses `c_uint64` and its handle uses `c_void_p` in the required 64-bit host. Reader lines 341–370 do not enforce these label/clock/active-identity relationships or the controller's upper bounds, although native-root upper bounds are checked. |
| An equivalent caller-permitted relative output spelling is rejected. | `source-permitted-relative-output-positive` | `collect_trials` at line 175 accepts a relative `Path`; the unchanged driver resolves its output at `verify_offline_export.py:221`. Reader line 268 constructs its expected native trace path from an unresolved root. The coherent relative control fails `source_and_commands`; later missing reopened context errors are consequences of that first failure. |
| A preexisting publication receipt is overwritten and the wrapper returns success. | `wrapper-cases/receipt-collision`, `WRAPPER_RESULTS.json` | `real_driver` at line 294 correctly stages streams in a fresh sibling and publishes streams with exclusive destination creation. At line 320 it calls the generic truncating `write()` for `publication.json`. The fake invocation creates a unique marker there; the marker is lost, no publication error is raised. This is a pure collision witness, not an observed filesystem race. |

`SOURCE_ORACLE.json` additionally binds the default driver hash and executes only
its two extracted pure capture functions with fake callbacks. The local baseline
predicates pass; all four existing bad capture controls fail the actual source
predicates. It also extracts the three source constants with their types. This
corroborates local invariants, without claiming full trace or physical validity.

## Results and limits

Each source view passes **58 maintained methods**: all old 28 and new 30, with no
errors or skips. The unchanged 11 binding controls were not duplicated; their
original passing logs and protected source are verified separately. Each view's
fresh nine methods records **81 loader cases, 14 false accepts, one metamorphic
false rejection, 17 assertion failure events across five methods, zero errors,
zero skips, and zero candidate exceptions**. The 17 includes the wrapper's two
failed assertions. A separately saved verbose positive is not counted among the
81. These counts are not claims of 81 independent source-valid native histories.

All 53 individually derived required-file omissions reject with named errors.
PNG/JSON corruption and typed close-limit/exit negatives reject. Ordinary,
verbose, signed-seed, unknown-extra and coherently extended 301-second controls
pass. The extended control moves both trial finish and the subsequent job query;
the builder's maintained extended-positive construction leaves the latter clock
earlier and cannot establish that source order.

With all 53 files present, removing the first close observer callback still makes
the first trial strict-false despite an optimistic custom loader. All four arms
are attempted, the later three pass this format model, the collection fails, and
normal completion does not invoke safety cleanup. Literal old75 and its strictly
metadata-only adapted replay both reject all four attempts in both views with no
cleanup. Its old minimal context is no longer a valid positive, so that result
alone is not proof of the missing-file fix. The fresh omission and missing-close
controls provide the relevant isolation. Exact scripts, hashes and labels are
retained under `own-old75` and `depth-old75`.

The accepted baseline is a file-format and selected-relationship model, not a
complete producer-faithful successful history. Further source inspection confirms
two construction deficiencies: `native_reload.before` at wall 20500 follows a
saved fired-HUD pause/resume at 20100/20400, although the default driver obtains
the former before that HUD operation (lines 669–672); and its action list omits
mandatory successful `observed()` return trace actions (lines 590–601), including
five per named capture fence. These are additional limits of the original
positive construction, not retroactive edits or additional counted test cases.
Phase A permitted the exact constructor amendment while preserving old test
intent; it did not certify a complete producer history. The current review
therefore does not claim that every false-accept case has every other possible
full-history constraint satisfied. The source contradictions, local source
oracle, and publication data-loss witness still prevent source acceptance.
Future corrected constructor/action-plan versions must remain separate from this
original corpus and be adjudicated against producer source before being used as
positives. Passing assertions alone cannot adjudicate that model.

## Archived data and preservation

Read-only negative checks on original Windows runs 40089125575 and 40080238905
retain all 53 original files and match the previously sealed before/after byte
inventories. Both have only 51 of the new required paths: controller stdout and
stderr are absent, and no current observer close receipts can be supplied from
those originals. Both reject. Other historical-source/profile/context failures
are retained and are not attributed solely to the missing streams. Original
ANGLE warnings, leak evidence and driver verdicts remain intact. These are
availability/negative checks, not new native qualification or a replay of the
separate input-consumption analyzer.

`FINAL_AUDIT.json` verifies the 516-path non-doc union: five added/changed paths
and 511 protected identities. The default driver, game, workflow, timing/input
semantics and binding component are unchanged. Protected study functions and
`WindowsOwner` match their prior ASTs; all old 28 method bodies, 113 assertions
and fake `Owner` are unchanged; `run_generated` matches the exact adjudicated V3
AST and the fixture module matches e902 bytes. Builder handoff's 97 manifest
members and 98 tracked report files match the exact handoff Git blobs.

The independent exact-depth view has HEAD 0f478, count one, no parent, a complete
16262-entry index and clean status. Own/depth views each materialize 354 source
paths, with 162 sparse omissions explicitly inventoried; all 516 frozen builder
paths are physically verified. Shared objects at `/workspace/sightbreak/.git/objects`
are disclosed: this is an initialized shallow source view, not a self-contained
clone. The single historical-Git comparison in the old suite is served from
exact preread, hash-bound baseline bytes with a narrowly bound adapter; the tests
perform no actual historical Git or native process invocation.

All prior Phase A/archive manifests and all **849 interim members / 205366615
bytes** remain unchanged. Raw failure whitespace is preserved, not normalized.
`FINAL_WHITESPACE.json` records full historical-range and exact raw-path scoped
checks separately. The final manifest adds the completed audit/oracle/narrative
without rewriting the immutable 7f6e601e checkpoint.
The first packaging assertion incorrectly expected two raw whitespace paths;
the full historical range also includes the builder's retained first-failure
stderr, making three. Its complete initial record is preserved separately;
all source/authored checks already passed and no raw bytes were changed.

## Winner, reason and largest gap

The frozen producer requirements win over permissive loader agreement. The
missing-receipt regression is repaired, but the component remains **REJECTED**
because complete evidence can contradict mandatory producer facts and publication
can lose its own receipt. The largest component gap is a complete source-derived
relationship model, supported by independently adjudicated positive construction.
The larger public study also lacks accepted complete finite retention and Windows
qualification. No engine, helper, API, proc, signal, CI, capability or native trial
ran in this review, and this verdict authorizes none.
