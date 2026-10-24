# Four objective decision checks accepted; whole reader remains blocked

Independently accept only the four declared offline decision checks at frozen
`bc9f945d7fb0741307504381f4b95b2fa993e392`. R3 is better than rejected R2
`dce89495d04c9d3fefece0f8c7929e2e01b8e7df`: the corrected baseline accepts, while
wrong CALL actor, selected target without an eligible candidate, invented role
and forged nearest-defuser plan reject for their intended errors. Eight original
false accepts still reproduce, so the whole reader remains rejected.

This is a new subject reviewed independently of the root builder in a reused
critic thread. The supported thread limit prevented a new thread; no fresh-thread
claim is made. A secondary static-agent followup was also rejected by that limit.
The reviewer did not build this component. Own criteria were committed and pushed
as `78f39ddb2a94f3dcb49bf11d51ded5109e73cdea` before tests. Root criteria are
`2f7c878f`, expanded by `2c9caa98` and `86e09298`; builder seal is `b2370e68`.
The existing SIGHTBREAK gauntlet and No AI Slop instructions were reused.

## Actual evidence and comparison

All executions used CPU4, pure Python or static reads. No runtime source changed.
Full checkout HEAD is the report-only preregistration commit with an identical
non-document tree to frozen source. Separate depth-one HEAD is exact `bc9f945d`.

| Check | Independent full checkout | Initialized depth-one checkout |
| --- | --- | --- |
| Maintained suite | 15/15, no skips, 30.295s | 15/15, no skips, 66.139s |
| Component corpus | 30/30 | 30/30, identical input hashes/verdicts |
| Non-nearest defender pair | 2/2 | 2/2, identical hashes/verdicts |
| Full non-document source bytes/modes | 513/513, no omissions | 513/513, no omissions |
| Current game/scripts inventory | 451/451 | 451/451 |

The 30-case corpus consists of the five exact sealed builder inputs, one
independent `branch_change` CALL-actor mutation, ten isolated nearest-defender
decisions and fourteen role-schema controls. Additional non-nearest decisions
accept `retake_cover` and reject forged `defuser`. No false reject or false accept
appears within these 32 bounded component controls. Role-schema controls isolate
allowlist membership, and isolated decisions do not model the entire AI or arena.

Exact sealed inputs are retained under `full-component/builder-sealed/component-inputs/`.
The independent results compare their actual records against both reader versions:

| Actual input | R2 | R3 |
| --- | --- | --- |
| Corrected positive | Accept | Accept |
| Wrong CALL actor | False accept | Reject: `freshness call describes another actor` |
| Target without candidates | False accept | Reject: `direct perception selected an unperceived target` |
| Wrong defuser destination | False accept | Reject: `defuser destination contradicts device` |
| Invented role | False accept | Reject: `typed decision roles` |

`review_component.py` imports frozen source and compares the old verifier's
record-validation functions using retained old source. It does not relabel old
record validation as a new acquisition audit. `source_audit()` is independently
run against the actual current inventory in both checkouts.

The unchanged independent13 rig SHA-256 is
`9eaba9f1f567f4deb3d45890adf595dd4846ca9cee6833fcd1f138c58b263403`.
Its actual replay takes 87.0836s and exits1: corrected positive accepts, four
mutations reject and eight mutations still falsely accept. The wrapper retains
all13 actual distinct input streams as bounded gzip files under `original13/inputs/`
and binds the current verifier/helper hashes. Its hardcoded footer source label
still says `dce89495`; that legacy label is preserved and does not identify the
executed current reader. Actual reader SHA-256 is
`d6607324c8c6f06125c50455fe85a0b870031485f7976b882928280b29b6d671`, helper SHA-256
`145a8a4c1e37ca162d7280c059c98f4df3927752f51691cc220a615365f1f0b1`.

## Source basis and bypass controls

`bot_objective_observation_probe.gd:258` selects actor6 before every freshness
decision call. Both `live_complete` and `branch_change` actor substitution reject.
`bot_ai.gd:406` selects from eligible scored candidates; the direct perception
guard now requires eligible membership for a nonzero selected target. This closes
the declared no-candidate mutation, without qualifying complete perception typing,
score, FOV or visibility fidelity.

The role allowlist covers the fixed source role literals and the memory override.
All13 schema literals remain allowed, while an arbitrary string rejects. This is
not proof of reachability or correct role selection in every context: `rifle` is
an initializer literal, and global membership alone is not a full role oracle.

`bot_ai.gd:461` initializes a planted plan to the device position; lines467–468
give the nearest living defender the `defuser` role even outside interaction
range. The later `pursue_memory` override excludes planted objectives. Therefore
deriving the nearest actor from protected state closes the legal-role bypass.
Independent nearest controls cover distances0,2.5,2.7,4.0, a dead closer defender,
forged near/far destinations and legal `anchor`, `retake_cover`, `pursue_memory`
role forgeries. The separate non-nearest pair confirms another defender retains
its covering role and cannot claim `defuser`.

The fixed probe sets local_id0 and leaves peer ownership empty, so its ten actors
are bots in fixed insertion order. The source also has human-interaction priority,
squared-distance/approximate tie behavior and engine numeric details; the inherited
Python minimum is not qualified as a generic model of those cases. The controls
use unambiguous distances and robust inside/outside interaction values. No native
2.6m floating-point boundary, generic human priority, approximate-distance tie or
arena path/visibility equivalence is accepted.

## Original fixture fidelity

All five original compressed input00..04 streams, old helper and critic script
match recovery `acbe394332e91229048e5d4573f9a5de9d01bdfe` byte-for-byte.
`fixture-preservation.json` retains compressed/raw hashes. The original helper
plans the positive defuser at[15,0,10], while its device is[-15,0,10]. Source says
the nearest defender keeps the device destination. The original positive is
source-inconsistent; rejecting it alone cannot prove the four mutations fixed.

Actual replay preserves that distinction: R2 accepts all original00..04. R3
rejects00..03 for the inherited device-plan error, and04 for the invented role.
These outputs remain in `full-component/results.json`, separate from the new
corrected-baseline mutation verdicts above.

Independent complete typed-row comparison shows regenerated helper data equals
the builder's exact sealed positive. Compared with the old helper, it changes
exactly76 scalar values: x15→-15 in the plan and effective destinations of38
`control_defuse` decisions. All other generated fields are unchanged. The helper
predicate is based on planted objective, living team1 defenders and nearest
identity, rather than a test label or successful interaction. Independent far
defuser controls also exercise the corrected role outside interaction range.

All builder manifest entries are independently checked against sealed Git blobs.
Old inventory bytes remain exact (SHA-256
`a09ee54f03e4dbcaf1fdb0aa354d43ed2a80dbfa614b21e8e9a3f1dc0810b3dd`). The new451-path
inventory has the same path set and changes only verifier/test hashes.

## Eight blocking false accepts retained

The largest remaining gap is protected state continuity across the input/action/
objective boundaries. The reader binds commands, but still permits impossible
state to appear before the objective consumer, including team changes, credits
and planting without progress. A correct defuser plan does not repair that gap.

Actual `original13/results.json` and its retained raw inputs reproduce all eight:

- `fabricated_target_score_navigation_and_bot_memory`
- `in_range_in_fov_candidate_falsely_rejected_by_fov`
- `forward_credits_added_without_kill_or_reward`
- `forward_objective_plants_before_consumer_without_progress`
- `forward_progress_injected_then_correctly_cleared`
- `isolated_control_stationary_actor_teleports`
- `isolated_control_match_rng_changes_without_bot_call`
- `forward_action_phase_reassigns_actor_team`

No whole-reader/source-readiness, actual objective reliability, historical cause,
Godot/API, native runtime, gameplay, bot quality or release gate is promoted.

## Source and depth provenance

The complete tracked non-document union contains513 paths. Both own checkouts
materialize every path and match Git blob, mode and physical SHA-256 checks.
All515 unique comparison objects are available. Only
`scripts/verify_bot_objective_observation.py` and its meaningful existing test
change from R2. The full game tree is unchanged at
`d27f5a57cfc1e22d81d4cf584824d363ecc382d1`, including probe, AI, controller,
authority, protocol and economy. Reports are the only reviewer changes.

The new depth-one repository initializes its index before testing with
`read-tree -mu HEAD` and `update-index --refresh`, is clean/shallow=true and has
commit_count1 at frozen source. Its explicit local alternate is
`/workspace/sightbreak/.git/objects`. This is not a self-contained clone or object-
closure proof; external historical comparator and sealed artifact access remain
disclosed. The current maintained suite and current source audit run directly
from the initialized one-commit checkout without using historical Git commands.

`depth-one-setup.json`, both source bindings and `inventory-and-source-fidelity.json`
retain the full proof. Backend/tools paths were added before full physical-source
verification. One static search used the wrong `game/scripts/maps/arena.gd` path;
the corrected path is `game/scripts/gameplay/arena.gd`. No test failed or was skipped
because of that read. The builder's original empty-index and summary-reader
failures remain unchanged in its sealed manifest.

No full-blob clone, Godot/native/CI/dispatch/process inspection, Mac-file-handling
review, runtime fix or canonical-document edit occurred. Reproduction commands,
actual exits, bounded raw inputs and failed whole-reader results are retained in
this own pushed report branch. The next component still requires preregistration
and independent review against the remaining false accepts.
