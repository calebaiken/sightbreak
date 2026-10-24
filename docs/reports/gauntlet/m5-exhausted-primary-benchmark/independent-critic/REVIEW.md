# Independent exhausted-primary fixture review

Verdict: **CHANGES REQUIRED before supporting one bounded baseline run.**
This review covers exact builder freeze `114150a06c4ae00f38c84e796e5b05054e25ac37`,
whose parent is baseline `b2e0293a546961230afbd73e5cd2a1a307d69e94`.
It approves no engine run, product policy, gameplay quality or release gate.

The largest gap is a missing nonvacuous authority witness. Ordinary diagnostic
targets lie behind solid freight geometry; the nearest target is inside it.
The fixture can pass its reward check with no target damage or kill. Its raw
rows also cannot distinguish decision-time target damage from authority damage.

## Blocking findings and exact fixes

1. **Provide and require a real damage/reward witness in a clear sightline.**
   Fixture lines 179 and 184 place the ordinary shooter at `(-14, 0, -10)` and
   the 6 m target at `(-8, 0, -10)`. `arena.gd:120-121,178` creates a solid
   container spanning `x=[-8.5,-5.5]`, `y=[0,3.1]`, `z=[-15.5,-6.5]`.
   The target is inside this solid. The initial center-aim ray enters the solid
   at `x=-8.5`, height approximately `1.2992 m`, before reaching target volume.
   Every other ordinary target is farther along the same obstructed direction;
   the longest targets also lie outside the yard wall at `x=24`.
   Injected `can_see` intentionally bypasses this obstruction for acquisition,
   while `SBActor.trace_shot` still queries solid world geometry (actor lines
   783-805). This is suitable for decision labels, but cannot substantiate
   positive damage/reward behavior. The actual physics-space registration is
   unobserved: construction and all cases execute without a physics-frame
   barrier, making that another uncertainty, not evidence of a clear ray.

   Retain these diagnostic labels if useful. Add a separately labeled, bounded
   clear-line authority control, using the real bot decision and stock action,
   trace, damage and elimination/reward paths. Declare its initial target health,
   pose, resources, step budget and expected witness counts before running.
   Let the physics space settle explicitly without allowing full-match ticks.
   Require at least one actual emitted shot, target damage and ordinary kill
   reward; log the target damage/elimination events and shooter kills/credits
   and victim deaths. A low-health initial target may be used if clearly labeled
   as a fixture condition. Do not overwrite target health between steps, mock a
   hit, suppress collision, call a reward function as a substitute, or compensate
   by relaxing the existing assertions. This control measures authority, without
   imposing a new sidearm policy on the diagnostic matrix.

2. **Record and protect target state across the decision boundary.**
   `_observe` takes `enemy_before`, calls `_bot_input`, snapshots only the shooter,
   then emits target state only after `tick_authority_actions` (lines 231-265).
   A future AI change that directly lowers target health without killing it can
   pass every current check. The row cannot reveal whether that loss occurred
   in the decision or action. The conditional reward check is insufficient for
   nonlethal damage.

   Add `enemy_after_decision` before the authority call, and require target
   health/alive/deaths and relevant protected resources to match `enemy_before`.
   Record the same fields after action. Include the objective's authority fields
   before/after decision and assert that planning has not mutated them. Keep
   allowed bot/team memory changes separate. Compute damage/reward deltas from
   the post-decision target snapshot, and retain all three raw phases so an
   independent auditor can recompute them.

3. **Make action acceptance and observation checks nonvacuous.**
   `shot_delta` is never required to be positive; aggregate counts check rows,
   not action coverage (lines 105-108,244-256). A no-op `_fire` or no-op
   `start_reload` can satisfy the current conservation/reward checks. All 567
   independent decisions begin with reaction state zero and advance only 0.12 s,
   below even hard's 0.18 s reaction delay, so they do not provide loaded-primary
   firing witnesses. The repeated near sequences can emit sidearm shots, but no
   assertion requires them. Reloadable sequences last only 0.96 s, shorter than
   every reload; the documentation correctly disclaims completion.

   Require positive shot/damage/reward coverage in the separate authority control
   from finding 1. Also assert at least one real accepted reload start in an
   existing no-switch reloadable-primary case and verify its configured initial
   duration, with unchanged clip/reserve. Emit exact witness labels/counts in the
   result. Require observation/authority failure if a registered positive witness
   is absent. Root's review steering additionally requires completed-reload
   witnesses before baseline release: preregister separate bounded controls for
   reloadable primaries and a reserve-only sidearm, with enough action steps to
   exceed their configured reload plus initial start/draw delays. Require actual
   completion, legal reserve-to-clip transfer and shot-adjusted conservation;
   retain raw intermediate states without resource resets. The existing 0.96 s
   diagnostic sequences can remain unchanged and cannot substitute for these
   controls. Primary cadence remains outside scope. Preserve the original freeze
   and obtain fresh source review of the revised fixture/hash.

## What the freeze supports from source

| Review dimension | Finding |
| --- | --- |
| Source identity | All four SHA-256 entries match `SOURCE_FREEZE.json`. The freeze adds exactly the probe and two registration files. Product code, maintained test registration and canonical mission documents are unchanged from baseline. |
| Matrix completeness | The source loops match the registration: core 324, loaded primary 54, reserve-only sidearm 27, stale cache 81, objectives 54, unowned sidearm 27; 567 unique independent cells. Nine profile/primary pairs each have eight 8-step sequences: 72 sequences, 576 steps, 1,143 decision/action rows. This is completeness against the declared matrix, not exhaustive tactical coverage. |
| Real decision/action code | `TacticalMatch._bot_input` delegates to `SBBotAI.compute_bot_input`. The fixture then calls the actual `SBActor.tick_authority_actions`. `_equip`, `start_reload`, `_fire` and real traces are not replaced. The only overridden actor behavior is visibility. |
| Active versus stale cache | `_resources` prefers active ammo/reserve; contradictory active store entries are explicitly installed for exhausted, reloadable and loaded primaries. `_equip` saves active fields before changing weapon, so stale active cache is not treated as current availability. |
| Unknown/unowned sidearm | Missing owned entries remain `unknown`, unowned entries remain `unowned`, and `known_sidearm_resources` excludes both. Projected stock equip defaults are separately named and included solely in the conservation total. Unknown does not mean known usable or known dry. |
| Ammo accounting | Sum conservation is recomputable from raw inventory, active fields, store, definitions and actual shot count. It does not prove each weapon's legal clip/reserve transition by itself. Raw states permit a later independent per-weapon audit. |
| Rewards | There is no reward debit, target-damage override or artificial reward removal. Target actor 1 retains the match's damage/elimination connections, and `_eliminated` finds replacement shooter 6 in `m.actors`, permitting ordinary kill credit. Positive reward execution is not established; finding 1 must address it. |
| Raw evidence | Full shooter before/after-decision/after-action states, commands, actual shot directions and ammo, resource labels, bot states, definitions and profiles are emitted. Vector2i values are serialized as arrays. Target decision-phase state and damage/elimination event witnesses are missing. |
| Range/difficulty/objectives | Existing profiles and `<20 m` fallback are unchanged. Target labels distinguish 20,24,45.5,60 m and hidden target; 45.5 m is within hard vision and beyond sidearm trace volume. Carrier and defuser controls use real objective planning and assert interaction. These are stationary/injected-acquisition controls; there is no LOS, navigation, planting/defusing timer, range-effectiveness or tactical-quality qualification. |
| Assertions versus policy | The probe does not require a proposed new switch rule or hard-code a preferred exhausted-primary response. Inefficient commands remain observations. Source review selects no candidate policy. Later candidates need preregistered preserved controls and actual baseline comparison. |
| Runtime safety boundary | Offline configuration takes no server/client path and creates no economy bridge. Protocol is checked as 6; offline ranked payload is checked empty. No engine/import/UID/native/OCR/services/compile ran during this review. Runtime parsing, resource/import availability, leaks and cleanup remain unverified. |

The replacement shooter is not connected to the match callbacks normally wired
in `_spawn_actor` (match lines 175-187): only the probe's shot recorder is connected.
This omits shot-hearing/activity and confirmed-hit/impact callbacks. In this
offline, one-shooter scenario it does not remove target elimination rewards, and
the shooter ignores its own team's hearing events. Restore equivalent callback
wiring for production-equivalent observation, or state this omission explicitly;
do not present the fixture as complete match action-pipeline qualification.
`tick_authority_actions` also does not consume `look` or `crouch`; production
movement does. The fixture keeps its initial yaw/pitch and standing state and
logs actual floor contact/spread. Keep any eventual findings scoped to those
controlled poses rather than native aim or movement behavior.

## Evidence and next boundary

Run `python3 docs/reports/gauntlet/m5-exhausted-primary-benchmark/independent-critic/audit_source.py`
from this review checkout to regenerate `SOURCE_AUDIT.json`. It reads frozen Git
objects, verifies hashes and the product diff, independently enumerates the
registered matrix and records the geometry witness. It does not parse/compile or
execute GDScript. This review worktree changes only its own evidence directory.

Read guidance: `AGENTS.md`, `CLAUDE.md`, mission/progress/acceptance, `NEXT_SESSION`,
`PARALLEL_WORK`, `BARS`, the installed gauntlet-loop and sightbreak-gauntlet skills,
and no-ai-slop including its evaluation. Existing originals were reused. The
parent's narrower source-only instruction controls: canonical mission files are
not edited, and no nested agent or runtime lane is started.

After the three fixes, including the root-required completed-reload witnesses,
root can request fresh source review and decide whether
to release one bounded private-state baseline with retained raw logs, source
hashes, PID/start/exit and scoped cleanup receipts. This report does not release
that run. Full gameplay/balance, bot reliability, human experience, CS2 comparison
and all broad release gates remain open.
