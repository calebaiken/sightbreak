# Original R4 handoff component rejected

Frozen `f48c8461b3b6cb26c5ab2a79f2b51c444e94a0ec` is better than accepted decision
component `bc9f945d7fb0741307504381f4b95b2fa993e392`: it rejects six more original
mutations on byte-identical inputs. It still falsely accepts a carrier death
that leaves the device carried. Reject this frozen handoff component; its death
exception must require the source-mandated drop, not merely permit a drop.

The largest remaining handoff gap is this missing mandatory transition. The two
known target-score/FOV failures also remain BLOCKING. No whole-reader, runtime,
native/API, objective-quality or readiness approval follows.

This review is independent of the root builder in a NEW own sparse worktree and
branch. The existing critic agent thread is explicitly reused because of the
supported thread limit; no fresh-thread claim is made. Own preregistration was
committed/pushed as `206e71fcf756bbb81983cdc414a5b36af568d196`; independent drivers
were committed before tests in `e1feabe1` and `d7d5db3d`.

The requested pre-capture gate was honored: no verifier tests ran before inspecting
immutable root seal `3f7807abf63e6a7a8e20e6c93bd68ba7ff3ec874`, its F48_EVIDENCE.md,
root raw/hash/result and preceding `cf766006` maintained/independent outputs.
All16 sealed files are copied byte-for-byte under `builder-original-f48/`.
Any corrected source is a separate review subject; these results remain bound
to original f48 reader SHA-256
`6ab24010b0afe5860a257234f9a19f545f4bca55f2092e23be38bee11a6bf5b8`.

## Actual results

All execution is CPU4 pure Python/static. Full checkout HEAD is report-only
`d7d5db3d5f78df8aba4fdf0be8f448cf5283d1cc`, with the identical non-document tree to
frozen f48. The independently initialized depth-one view is exact f48.

| Evidence | Full source | Initialized depth-one source |
| --- | --- | --- |
| Maintained meaningful methods | 21/21, no skips, 108.814s | 21/21, no skips, 94.473s |
| Unchanged original13 rig | 11/13; two false accepts; exit1 | Same13 raw hashes/verdicts; exit1 |
| Independent handoff projections | 32/33; missing-drop false accept; exit1 | Same decoded inputs/verdicts; exit1 |
| Independent full-stream drop pair | Positive accepts; negative falsely accepts; exit1 | Same decoded records/verdicts; exit1 |
| Sealed root missing-drop raw | False accept; exit1 | Full-source replay retained separately |
| Non-document physical source/modes | 513/513, no omissions | 513/513, no omissions |

The maintained methods pass, but do not catch the missing-drop defect. There are
no false rejects in the 33 bounded necessary-field projection controls. Those
controls are conditional source projections, not a damage, physics, complete bot
or combat-attribution model. Timings are recorded execution evidence, not hardware
or comparative performance measurements.

The independent full original13 replay uses exactly the same13 input hashes as
the earlier R3 critic archive `e87aa1659e48c2d8b1d2fbea161c2816f42eb393`.
R3 meets5 expectations; R4 meets11. All four accepted decision guards remain
effective. R4 now rejects:

- `forward_credits_added_without_kill_or_reward`
- `forward_objective_plants_before_consumer_without_progress`
- `forward_progress_injected_then_correctly_cleared`
- `isolated_control_stationary_actor_teleports`
- `isolated_control_match_rng_changes_without_bot_call`
- `forward_action_phase_reassigns_actor_team`

The two unchanged failures still falsely accept in both views:
`fabricated_target_score_navigation_and_bot_memory` and
`in_range_in_fov_candidate_falsely_rejected_by_fov`.
`actual-r3-r4-same-input-comparison.json` records the exact comparison.

Each view's 13 actual streams is retained once as gzip, keyed by its actual raw
hash, with stdout/stderr and current source/helper hashes. The rig's hardcoded
footer still identifies historical `dce89495`; it is preserved as a legacy label,
while the wrapper binds the executed f48 bytes. Nothing is relabeled as a whole
reader pass. Independently generated drop-pair raw serialization differs between
views; decoded JSON values and outcomes agree, and both original byte streams
are retained rather than replaced with normalized data.

## Mandatory-drop falsifier and valid pair

`Match._eliminated` at `game/scripts/gameplay/match.gd:507` unconditionally drops
a carried device when its carrier is eliminated. It assigns the killed actor's
post-movement position and carrier0. Movement happens before queued hitscan
damage. The later `_objective_tick` can then recover a dropped device, plant,
defuse, progress or detonate.

`action_handoff` checks a changed objective only through its carried→dropped
exception. When the objective does not change, the final `else` merely requires
the previous carrier/position. It therefore accepts an otherwise counter-
consistent elimination while retaining `objective=carried` and the dead carrier.

The isolated pair is in `full-handoff-controls/`:

- `carrier_drop_uses_post_movement_position`: accepts the required drop after an
  opposing elimination, with the kill/credit/death fields correct.
- `carrier_death_suppresses_required_drop`: same elimination and awards, but
  restores the prior carried state/carrier/position. Expected reject, actual accept.

The independently authored complete-stream pair passes through normal parsing
and `verify`, including all original guards and stream consumers:

| Full-source input | Expected | Actual | Raw SHA-256 |
| --- | --- | --- | --- |
| `required_drop_then_consumer_recovery.log.gz` | Accept | Accept | `7d4fbd000e6c099668003a2c97da35db7d2a4571101f24cc27439c5fee4ce3c8` |
| `dead_carrier_stays_carried_complete_stream.log.gz` | Reject | False accept | `ff790f5120d1ae4ad28e1d0ab8455fcf27c99ef4aa93ddee162a8fa7b28a9734` |

These streams condition on an opposing elimination with consistent counter/
award fields. The valid-side consumer can recover the genuinely dropped device;
the invalid side never drops it. This isolates the mandatory relation without
claiming that the synthetic helper reconstructs the preceding shot or every
damage-memory side effect. Acceptance of the positive is a component/schema
control, not proof of a fully executable combat history. A future stronger
combat reader needs its own source-faithful fixtures; rejecting this positive
for another unmodeled predicate alone would not establish a drop fix.

The independently replayed root sealed stream is a second concrete form of the
same flaw: raw hash
`14458c5f6d9dd0d699679425393283a4acda08ea5e3c16b50b3658c9924ea418`, compressed hash
`a1e7ed4f17215bc528ec44a270eb3f472d2e75ce1bbdf9b2500edd29b5919c85`.
Actual f48 `verify` returns `observable_contract_passed=true`, no errors,202 decision
rows and605 interaction rows. `full-root-missing-drop.json` retains the actual
independent outcome; sealed input bytes match root's recorded hashes exactly.

This is one additional underlying defect demonstrated by unit, opposing-kill
stream and sealed-root stream variants. It is not three independent new causes.
All false accepts and the paired positives remain recoverable on this branch.

## Validity challenges and boundaries

The other 32 projection expectations pass in both views:

- Opposing kill awards at starting credits800,8800,8900,9000 produce +300,+200,
  +100,+0 respectively. Incorrect cap, unearned credit, absent opposing death
  and inconsistent alive/death transitions reject.
- Conditional mutual queued eliminations, independent eliminations and absent/
  self/same-team killer hook semantics remain permitted. `resolve_shot_hit` does
  not require a queued source to survive later damage. Source elimination gives
  no award to a missing, suicidal or same-team source. This does not establish
  world hazards, teammate damage, trajectories or killer attribution in gameplay.
- Ordinary damage without death, source-allowed actor RNG/resources, living
  carrier movement with unchanged stored objective_position and complete post-
  decision match RNG handoff remain permitted. No movement/damage model is claimed.
- Forged match RNG/input, team/phase changes, pre-consumer objective transitions,
  timer/progress/contribution changes, stale drop position and drop without death
  reject. Only the mandatory-drop obligation is missed by this corpus.

The new handoff runs only when there is a live objective consumer. Non-live
authority handling neutralizes inputs and advances round phases through separate
source branches; this review does not apply the helper as a generic whole-tick
oracle outside its synchronous interval. Utility callbacks do not interleave
with that interval through an await. Actor shots use actor RNG, not Match RNG.

Probe `_control` explicitly advances only actor6 movement/actions, so the
non-subject stationary-pose check follows the fixed probe. Subject resources and
movement can change; generic physics, human/server transport, independent utility
physics and full combat continuity remain unqualified. No new source false reject
was found in these bounded checks, which does not establish universal soundness.

## Source, inventory and depth proof

Both source bindings cover all513 tracked non-document paths, including full
physical SHA-256, Git blob/mode and complete path union. All515 unique comparison
objects exist. Only verifier and meaningful existing tests differ from bc9.
The complete game tree remains
`d27f5a57cfc1e22d81d4cf584824d363ecc382d1`: game/probe, AI, actor actions, controller,
protocol, authority, economy and runtime behavior are unchanged.

The current451-path game/scripts inventory has the same path set as R3 and only
the two declared updated hashes. Old R2 and R3 inventories remain byte-exact;
`inventory-preservation.json` records both SHA-256 values and the game-tree proof.
Reports are the only reviewer changes; original worktrees and all earlier raw
outputs remain untouched.

The own depth repository initializes its index before testing (`read-tree -mu HEAD`,
`update-index --refresh`), is clean, shallow=true and commit_count1 at exact f48.
Its explicit object alternate is `/workspace/sightbreak/.git/objects`. This is not
a self-contained clone or object-closure proof. Historical R3 comparator access
and immutable external rig/artifact use remain disclosed. The maintained current
suite itself reads current tracked fixtures and uses the initialized index for
inventory checks. No prior depth result is inherited.

The review performed no Godot/native/CI/dispatch/process inspection, Mac-file-
handling review, production fix, release, canonical-document edit or full-blob
clone. The original f48 failure remains rejected even if a later reader corrects
it. Any new source must be reviewed against these unchanged failures and valid
pairs, while preserving the two target-selection blockers and unsupported scopes.
