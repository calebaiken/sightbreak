# Independent R2 exhausted-primary source review

Verdict: **ACCEPT source support for one bounded baseline**, at exact builder
freeze `b87afb717bf09a78c6d36b164d48906902734bdb`.
Root may now decide whether to release that single attempt with the registered
120-second outer wall bound. This review starts no engine or setup action and
approves no product policy, balance change or release gate.

The original `114150a06c4ae00f38c84e796e5b05054e25ac37` remains **REJECTED**.
Its [independent rejection at fb9b113](https://github.com/calebaiken/sightbreak/blob/fb9b113/docs/reports/gauntlet/m5-exhausted-primary-benchmark/independent-critic/REVIEW.md)
and the original registration/hash remain retrievable. R2 addresses its source
blockers; neither revision has executed game evidence in this review.

The largest remaining gap is actual source-bound output. The new mandatory
witnesses, parser/import availability, physics registration and cleanup have
not run. The pure witness oracle also needs a separate full raw-output auditor;
the limitations below must remain visible when reviewing the baseline.

## R1 blocker disposition

| Prior blocker | R2 source finding |
| --- | --- |
| Freight obstructed ordinary rays; longest poses left the yard | Probe lines 182–190 move ordinary distances through 45.5 m to `z=-20`. Independent arithmetic over all 26 stock solid boxes finds no center-ray obstruction at 2, 6, 20, 24 or 45.5 m. Both actors' actual 0.31 m capsule footprints stay inside the wall inner faces at 23.5 m. The 60 m diagonal is also in bounds and crosses freight; the revision declares it potentially obstructed and does not require it clear. Objective poses remain the site controls. |
| Physics-space registration unobserved | Lines 263–285 await two physics-frame signals with match physics disabled, require a complete crossed frame, then emit frame counters, actual mask-1 world ray endpoints/hit and stock center trace. Lines 337–341 require clear ordinary lines and target contact when within the active weapon range. These are future runtime gates, not observed clear physics. |
| Target and objective planning mutations not observable | Lines 319–349 capture shooter, full target including input, and objective authority state before decision, after decision and after action. Equality fences protect both actors and objective state during planning. Event-count fences reject a shot, damage or elimination emitted during planning. Damage/reward deltas begin after decision. |
| Missing positive shot/damage/reward witness | Lines 412–478 add the preregistered 2 m `kill_rifle` control with exactly one initial rifle round, no sidearm, and an explicitly artificial initial 10-health target. It must emit one real shot, positive damage totaling 10, one elimination, victim deaths +1, shooter kills +1 and ordinary credits +300. It forbids draws/reloads. A no-op fire, damage or reward path fails a mandatory assertion. |
| Missing accepted and completed reloads | Lines 455–486 require one full-duration reload start without ammo transfer and one correctly timed completion with legal reserve transfer for SMG, rifle, marksman and reserve-only sidearm. Hidden-target controls forbid shots/damage/eliminations and protect the target. The sidearm control must perform exactly one real fallback/equip with 0.3 s deploy. A no-op reload cannot satisfy them. |
| Replacement shooter omitted stock callbacks | Lines 85–94 restore all five connections in stock `TacticalMatch._spawn_actor`: eliminated, damage, shot, confirmed hit and impact. Probe recorders attach in addition. The original target retains its stock callbacks; damage/death recorders observe its ordinary path. |

Source AABB arithmetic is not a Godot physics observation. The runtime clear-line
and fired-hit gates remain necessary. The controlled standing aim points into
the target body at approximately 1.27 m height; the 2 m lane is physically
plausible even with the stock airborne spread. No hit, reward, collider or trace
is replaced to manufacture the witness.

## Authority, resources and raw evidence

The fixture calls `TacticalMatch._bot_input`, which calls
`SBBotAI.compute_bot_input`, then calls real `SBActor.tick_authority_actions(DT)`
without a replacement hit sink. The visibility subclass changes only `can_see`.
Stock `_fire` traces the settled world and real target volumes, calls
`resolve_shot_hit`/`apply_damage`, and emits damage/elimination signals before
the shot recorder. Stock match `_eliminated` owns deaths, kills and the +300
reward. The recorders retain serial order and event snapshots. The fixture
sets initial resources and target health once per scenario/control; it never
restores them between a control's steps or invokes damage/reward as a substitute.

All protected shooter/target and objective phases are emitted. Target damage is
clamped by stock `apply_damage`, so the declared kill records 10 actual damage
even though the rifle's nominal damage exceeds that value. Shot, damage and
elimination counts are mandatory only in the separate positive control; empty
matrix cells cannot falsely stand in for this witness.

Active ammo/reserve fields remain authoritative over contradictory active-cache
entries. Missing holstered state stays `unknown`; unowned state stays `unowned`.
Known-sidearm availability excludes both. The separate `equip_semantics_total`
projects stock `_equip` defaults only for conservation across a real equip.
The fixture asserts projected total after action plus emitted shots equals the
before total. Raw inventory, store, active fields, definitions and shot events
permit independent per-weapon recomputation. No missing entry becomes known
usable or known dry merely to produce a preferred switch.

The four registered reload control budgets are 19, 22, 27 and 20 steps. Stock
code implies primary start step 0 and completion steps 16/19/24; sidearm draws
at step 0, can start at step 1, and completes at step 14. These predictions are
source arithmetic only. The gates accept only a full configured start timer,
unchanged start ammo, positive legal completion transfer and completion within
one 0.12 s action tick after the configured duration. No assumption that deploy
and reload must occur sequentially was added.

The matrix remains 567 unique cells: core 324, loaded primary 54, reserve-only
sidearm 27, stale active cache 81, objective guards 54 and unowned sidearm 27.
There are still 72 eight-step sequences / 576 steps. Five mandatory controls
add 96 steps, totaling 1,239 decision/action rows. They preserve difficulty,
vision, range, `<20 m` fallback and objective guards. Inefficient commands are
observations; no later exhausted-primary selection rule is chosen here.

The fixture intentionally skips movement consumption and complete match ticks.
`look`, movement and crouch requests therefore do not move or aim the actor.
Initial fixed yaw/pitch, floor contact and actual action spread are logged.
This supports stationary action/resource diagnostics, not aim quality, cadence,
range effectiveness, objective timers, navigation or tactical reliability.
Offline match setup creates no economy bridge or server/client connection, and
the fixture retains protocol-6 and empty offline-ranked-payload assertions.

## Independent pure checks and limits

I ran the builder oracle tests independently: both unittest methods pass,
covering one explicitly synthetic legal set and all 14 named falsifiers.
These are parser/oracle tests, not executed action evidence.

I also retained two adversarial synthetic scope probes. `witness_oracle.py`
accepts a continuous 20 m in-bounds actor timeline in place of the registered
2 m lane, and accepts a kill timeline whose shot does not consume the shooter's
round. Its bounds checks do not bind exact preregistered poses, lane fields or
ray endpoints, and it does not recompute whole ammo conservation. The frozen
fixture itself fixes the poses and asserts conservation, so these are not
source blockers for one diagnostic run. They are a concrete limit on treating
this checker alone as an independent actual-output certificate.

Before accepting runtime evidence, the independent output review must compare
header definitions/profiles, all matrix/sequence/control identities, raw actual
poses/query endpoints/settlement, command consumption, complete per-weapon
transitions including unknown equip defaults, phase snapshots and event/reward
witnesses. The checker does not validate event serial/snapshot contents, bind
the terminal result to all diagnostic rows, or audit the full 567-cell matrix.
The source event-count planning fence is present; its intermediate counts are
not separately emitted as raw phase fields. Preserve that observation limit.

Reproducible retained files in this directory:

- `audit_source.py` / `source_audit.json`: exact frozen Git hashes, permitted
  diff, callback identity, independent matrix counts and source geometry.
- `oracle_unittest.log` / `pure_receipts.json`: independent pure test output,
  commands, exit status and SHA-256 receipts.
- `probe_oracle_scope.py` / `oracle_scope_probes.json`: the two accepted
  synthetic corruptions above, retained as checker limitations.

All eight R2 manifest hashes match the frozen Git objects and inspected files.
From product base `b2e0293a546961230afbd73e5cd2a1a307d69e94`, exactly nine
files change, all in the component report and new probe. `game/scripts`,
`scripts`, `backend`, maintained registrations and canonical engineering/roadmap
documents are unchanged. The probe has no generated UID in the freeze.

The review reused the installed originals of Gauntlet Loop, SIGHTBREAK Gauntlet
and No AI Slop including `eval.md`, and read AGENTS/CLAUDE, mission/progress/
acceptance, NEXT_SESSION, PARALLEL_WORK, BARS and the original rejection.
Per the parent task, only this own review directory changes; no canonical
documents or builder files are edited, and no nested agent is started.

Root's next boundary is one expressly released, pinned-Godot, private-state
baseline with exact source/hash, retained raw stdout/stderr, actual process
PID/start/exit and scoped cleanup receipts. Parsing/import/UID availability,
native positive-witness success, errors/leaks and cleanup stay unverified until
observed. Preserve any failed attempt. No engine, import, UID generation, native,
OCR, service, export or compile ran during this review.
