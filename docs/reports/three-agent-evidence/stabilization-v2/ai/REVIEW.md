# Independent tactical AI review — stabilization V2

This is a read-only source review and native Godot investigation. The reviewer did not edit shipping files or agent branches. All probes, immutable archive snapshots, failed attempts, and native logs live in this evidence directory.

## Exact reviewed sources and disposition

| Source | Exact commit | Independent disposition |
| --- | --- | --- |
| Original Gemini AI | `d66e72c763dfe4cdcbeb9f2a76a89ec97fdd1d26` | Historical compile/API failures preserved in previous evidence. |
| Updated Gemini AI | `7397efd8d10be727840aa91def951f79bdfaff64` | Parses and dedicated native suite passes. New ammunition/utility authority defect reproduced; several previous tactical defects remain. |
| Previous integration | `a939f1e7e0c32a5ef7ffbad0a714beb3af365259` | Reproduced prior nine-condition native behavior exactly. |
| Narrow V2 AI integration | `a143629cb25eb2d3573fa6d854da27a2c2518595` | API integration and equipment correction accepted by source review and independent native controls. Dedicated native suite passes. Tactical 8.5 gate is not accepted. |
| Original PR11 baseline | `11573e587f13dfd832613a0c09dbc615f46d3461` | Repeated with the same original seeds, conditions, and native physics. |

`source-manifest.json` records source/probe hashes and verifies the reviewed snapshots match exact Git bytes. Tests ran against those immutable archives, not the moving integration worktree. This report concerns AI acceptance, not the later final build or the complete regression campaign.

## Findings and closures

### P1 — Updated Gemini equipment helper grants resources after a failed purchase; narrowly repaired in V2

At `7397efd`, `game/scripts/gameplay/bot_ai.gd:192-200`, `buy_equipment()` ignores `actor.buy_weapon()`'s failure and then assigns full equipped ammunition and reserve plus one smoke and grenade. The helper does not itself grant weapon ownership, bypass wallet debits, or expose a new client RPC; it improperly refills ammunition and utility.

Native minimal reproduction, using the real actor methods:

```text
credits=0, weapon=rifle, inventory=[sidearm,rifle], ammo=2, reserve=3, smokes=0, grenades=0
actor.buy_weapon("smg") -> false, every resource unchanged
SBBotAI.buy_equipment(actor,"normal",2)
credits=0, same weapon/inventory, ammo=30, reserve=90, smokes=1, grenades=1
```

`authority_contract_probe.gd` exits **1** on exact `7397efd`; see `authority-contract.log`. The proper invariant is unchanged resources after an unaffordable purchase, not merely unchanged weapon ownership. The original match calls this helper after `actor.reset_for_round()` (`match.gd:279-282`), so its current round-start caller has already replenished these resources legitimately. This limits the present gameplay impact; it does not make the helper's resource contract correct or safe to reuse.

At `a143629`, the integration removes only the five direct assignments and preserves the helper's parameters, purchase delegation, and return value. It keeps normal match purchases through `actor.buy_weapon(SBBotAI.choose_buy_weapon(...))`. The unchanged external invariant now exits **0**, with every depleted resource preserved (`repaired-authority-contract.log`). The committed negative and funded-positive purchase controls pass; the funded fixture uses the real `cost` field and resets prior ownership before purchasing. Existing `reset_loadout()` and `reset_for_round()` behavior is independently exercised and preserved.

**Correction accepted on the integration branch. Gemini's exact source branch still needs the same narrow correction; its published commit has not been rewritten.**

### P2 — Three defender anchors still sit inside expanded solids

`7397efd:game/scripts/gameplay/bot_ai.gd:88-92` retains `(-15,0,12)`, `(15,0,12)`, and `(0,0,9)`. The actual RelayYard rejects all three with `_clear_path(anchor, anchor + (0.01,0,0.01))`. `safe_navigate((-15,0,9),(-15,0,12))` returns its origin exactly in the static probe (`module-probe.log`).

The stronger V2 probe drives a real `SBActor` through 600 actual 60Hz physics steps, including `move_and_slide()` and normal AI decisions. Starting at `(-15,0.05,9)`, it oscillates near the fallback waypoint and ends at `(-15,0.000845,8.693333)`, still outside the 1.8m arrival radius of its intended anchor. Its stuck value is zero. The same actor then moves over 1m toward a reachable anchor, proving the physics fixture can move (`integration-controls.log`).

This is failure to converge, not a claim that the real actor never moves at all. An early probe expected absolute immobility and failed; that unsuccessful attempt is retained as `independent-controls-attempt2-anchor-expectation.log`. Correct the anchor coordinates and validate arrival with real movement, rather than accepting a nonzero initial navigation step as proof.

### P2 — Easy defender hearing still bypasses its 18m bound

`7397efd:bot_ai.gd:389-407` respects the profile hearing range, but the separate defender scan at `517-523` routes to raw shot events within a hardcoded 22m. A 20m event leaves `heard_at=-100` in the bounded update and nevertheless becomes the defender's destination. Reproduced on exact `7397efd`; this code is unchanged by the narrow V2 correction (`module-probe.log`). Consolidate consumption through the bounded auditory state and retain near/far negative controls.

### P2 — Unseen damage-direction turn still gets overwritten

`7397efd:bot_ai.gd:656-662` computes a look toward directional damage, then navigation at `664-669` or idle scanning at `670-677` overwrites it. Native probe baseline and damaged look are both `(2.498091,0)`, despite the hit arriving from yaw `-1.570796`. This is separate from visible rear-attacker acquisition, whose damage-triggered FOV bypass passes a real-LOS positive control. A correction should preserve the chosen look priority and transform movement into that frame, rather than indiscriminately replacing the look.

### P3 — Sound precision configuration still has no effect

`sound_noise` remains declared as easy/normal/hard `2.4/1.1/0.35` but unused. `7397efd:bot_ai.gd:406` copies the exact authoritative shot position into hearing memory on every difficulty; native probes confirm equality. This is a perception-fairness/configuration gap, not evidence of live hidden enemy tracking or a network information leak.

### Closed — Attacker sound investigation and functional memory-expiration coverage

The new noncarrier-attacker branch (`7397efd:bot_ai.gd:491-503`) now investigates nearby enemy gunfire. Both Gemini's dedicated suite and external controls pass. Independent negatives confirm no investigation for out-of-range, expired, or allied gunfire. A positive memory-pursuit assertion, hidden-enemy movement invariance, and behavior-changing expiration assertion all pass (`independent-controls.log` and `integration-controls.log`). The new `pursue_memory` role assignment at line 651 fixes the earlier completely vacuous expiration test condition, although the committed suite would still benefit from the stronger positive/behavior controls.

### Closed — Missing methods/properties and round-plan integration

The new aliases remove the original nonexistent-method errors. The smoke reference now correctly uses `actor.smokes`. Native `bot_ai_regression_test.gd` passes on exact `7397efd` (`gemini-bot-regression.log`) and on `a143629` (`v2-bot-regression.log`).

The round-plan API changed from `(round_number,rng)->int` to `(match_node,team)->Dictionary`; an unchanged old integration call would fail compilation. The narrow integration calls `select_round_plan(self,0)` and preserves protocol 6 in its test expectation. At `a143629`, it does so after fresh actor positions and the new objective carrier are established, avoiding stale previous-round carrier input. The standalone Gemini match still creates `primary_site=0` and does not invoke the selector during normal round setup; tests invoking it directly do not prove production site rotation. This wiring gap is corrected on the integration branch.

## Nonvacuous native controls

`independent_controls.gd` tests exact Gemini source; `integration_controls.gd` repeats the controls on frozen V2 with the corrected equipment expectation. They include:

- Near/far/expired/ally sounds; positive pursuit plus behavior-changing memory expiration; unchanged inputs under two different hidden live enemy positions.
- Fresh team-report consumption, expired report rejection, and easy-mode communications disabled.
- Actual RelayYard and SBActor clear-corridor acquisition; smoke occlusion followed by visibility restoration; solid-wall occlusion; rear-FOV rejection with clear LOS and damage-triggered visible acquisition.
- Direct failed player-purchase control, helper resource invariant, existing reset/loadout behavior, actual blocked-anchor movement, and a reachable-anchor movement control.

`objective_controls.gd` additionally passes actual authoritative plant and defuse timers, living-defender selection, and human-carrier redirection to both A and B. These are explicitly arranged correctness fixtures; their successful planted/defused states are **not** counted as natural gameplay outcomes below.

## Repeated native behavior comparison

Godot `4.7.2.stable.official.ed1daf0bf`; 10 bots; seeds `1847,2026,3141`; easy, normal, hard; fixed 60Hz; two naturally resolved rounds per condition. Both original and V2 harnesses use the real match `_physics_process`, actor authority tick, `move_and_slide`, world raycasts, utilities, weapon RNG, and combat. Only buy waits are skipped. No winners, planted states, or objective completion events are injected in these comparisons.

The unchanged original harness first compared `a939f1e` and `a143629`. The external extended harness then repeated all three source checkpoints to measure inactivity and interaction attempts. Every common non-CPU gameplay metric matched the original harness exactly across all nine conditions for each checkpoint. The `a939f1e` run also matches the prior `4aa6263` comparison exactly after excluding CPU timings. All 18 rounds per checkpoint complete.

Each table cell is **original PR11 → previous integration → V2 integration**. Each difficulty has six observed rounds per checkpoint.

| Metric | Easy | Normal | Hard |
| --- | ---: | ---: | ---: |
| Target switches / engaged decisions | 9.46% → 4.21% → 5.76% | 9.36% → 13.17% → 15.99% | 17.08% → 25.67% → 35.90% |
| Commanded-movement stall ratio | 6.05% → 5.75% → 4.79% | 5.58% → 7.24% → 10.46% | 2.97% → 15.65% → 11.82% |
| Inactive share of alive actor time | 11.51% → 6.01% → 6.30% | 12.11% → 10.87% → 8.76% | 15.06% → 22.50% → 22.18% |
| Plant attempts / successful plants | 0/0 → 0/0 → 0/0 | 2/2 → 3/2 → 3/2 | 5/3 → 0/0 → 0/0 |
| Defuse attempts / successful defuses | 0/0 → 0/0 → 0/0 | 1/1 → 2/2 → 0/0 | 1/1 → 0/0 → 0/0 |
| Attack / defense round wins | 0:6 → 2:4 → 2:4 | 2:4 → 3:3 → 4:2 | 5:1 → 5:1 → 3:3 |
| Mean microseconds per bot decision* | 52.3 → 76.5 → 71.2 | 52.0 → 126.2 → 117.4 | 56.0 → 126.8 → 121.5 |

*CPU observations from the supplemental run are not controlled performance benchmarks. Original unchanged-harness V2 means were 84.0/119.1/128.7 microseconds, illustrating host/timing variability. These are per-bot decision costs, not per-ten-bot group costs. They cannot establish mobile CPU/GPU performance.*

Stall means requested movement with <0.05m displacement since the previous decision; it is an observational proxy, not a count of A* failures. Inactive means alive, no movement input, no visible target, and no objective interaction at a real physics tick; intentional scanning can qualify. Objective attempts count transitions into positive authoritative `_interactions` progress, rather than merely asserted input. Role-decision counts and exact per-seed data are in the extended JSON/logs.

V2 fixes source/API behavior while tactical results remain mixed: easy movement stalls improve, normal stalls and target switching worsen, hard stalls improve relative to the previous integration but remain well above original PR11, and hard still has no objective participation in these six V2 rounds. More balanced hard round wins do not erase the absent objective behavior or other observed defects. This small opening-round sample does not establish full-match balance, human-team quality, halftime behavior, statistical significance, or an 8.5 quality score.

The comparison harnesses have exit-only ObjectDB warnings: original PR11 43, previous integration 4, V2 10 instances. These were preserved and not suppressed. They are not assigned to tactical AI without an independent lifecycle diagnosis. Focused V2 authority, objective, and strengthened-control processes exit cleanly without those warnings. Audio/resource review is a separate workstream.

## Evidence and narrow next actions

1. Preserve the accepted `a143629` authority correction and actual reset/purchase APIs. Send the exact resource-grant reproduction to Gemini; do not reintroduce the five assignments through a future source merge.
2. Ask Gemini to correct the three anchor positions, damage-look precedence, defender hearing bypass, and unused hearing precision. Keep the existing negative controls and add native arrival/behavior controls. No full AI rewrite is recommended.
3. Retain the dedicated suite pass as source correctness evidence. Retain the natural-gameplay sample as separate tactical evidence; do not mark the 8.5 gate accepted from the passing suite alone.

Primary evidence: `authority-contract.log`, `repaired-authority-contract.log`, `gemini-bot-regression.log`, `v2-bot-regression.log`, `module-probe.log`, `independent-controls.log`, `integration-controls.log`, `objective-controls.log`, `previous-comparison.log`, `v2-comparison.log`, all `*-extended.log/.json`, `extended-summary.json`, `source-manifest.json`, and both exact diff patches. Initial probe failures are preserved, including a probe indentation error and the overly strict immobility expectation; neither is classified as a shipping source defect.

Reproduce after a normal headless import with the XDG directories under this evidence directory:

```sh
GODOT --headless --fixed-fps 60 --path EXACT_SNAPSHOT/game \
  -s /workspace/reviews/stabilization-v2-20261016/ai/native_comparison_extended.gd
GODOT --headless --path EXACT_SNAPSHOT/game \
  -s /workspace/reviews/stabilization-v2-20261016/ai/authority_contract_probe.gd
```

`GODOT` is `/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64`. The source manifest maps snapshots to their immutable commits.
