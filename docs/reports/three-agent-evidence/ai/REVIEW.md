# Independent AI review

Reviewed frozen Gemini PR14 commit `d66e72c763dfe4cdcbeb9f2a76a89ec97fdd1d26`, plus integration AI adapters at `4aa6263cdfe0a83f4ea69d3e819f6afb82f4a78f`. Review changes are confined to this evidence directory. No game source or shared integration files were edited by this reviewer.

**Disposition:** Frozen PR14 cannot compile. The integration adapters correctly repair its API contracts and smoke property access. Tactical acceptance remains blocked by the retained, now executable audio regression assertion. Several bounded-perception and navigation defects remain. Native two-round samples show mixed gameplay results and do not substantiate the original broad improvement claims.

## Findings

1. **P1, frozen source, repaired by integration — TacticalMatch calls nonexistent methods and wrong hook signatures.** Frozen `game/scripts/gameplay/match.gd:44,150,265,282,379,399,451` calls `new_team_state`, `new_bot_state`, `buy_equipment`, and `tick_bot`, while the module provides `create_team_state`, `create_state`, `choose_buy_weapon`, and `compute_bot_input`. Damage/elimination hooks also pass four arguments where five are required. Native `bot_match_test.gd` fails to compile its dependencies. Evidence: `frozen-existing-suite.log`. The dedicated new test likewise fails parsing on nonexistent APIs, including `get_profile`, `select_destination`, `get_site_hold_position`, and `SBWeapons.damage_at_distance`: `frozen-bot-regression.log`.

2. **P1, frozen source, repaired by integration — Every normal/hard bot tick without a visible enemy accesses a missing actor property.** `bot_ai.gd:538` reads `actor.smoke_charges`; actual `SBActor` declares `smokes` (`actor.gd:49` in the frozen tree). This aborts input generation even before a smoke throw is appropriate. Integration changes this single access to `actor.smokes`.

3. **P2, residual — Attacker bots record gunfire but do not investigate it.** `_update_auditory_and_team_memory` writes `heard_pos` and `heard_at`, but destination selection consumes them only in the defender branch (`bot_ai.gd:411-430`). A noncarrier attacker remains routed to the site/split waypoint. Native immutable-module probe: heard point `(10,0,-10)`, before/after destination `(-15,0,10)`. The adapted committed suite independently exits 1 with `Non-carrier attacker bot should respond to nearby audible enemy gunfire` (`integration-bot-regression.log`). Keep this assertion; changing its expected result would hide a missing promised behavior.

4. **P2, residual — Three defensive anchors are inside expanded solids; an intended recovery path can still return its origin.** New `DEFENDER_ANCHORS` (`bot_ai.gd:88-92`) includes `(-15,0,12)`, `(15,0,12)`, and `(0,0,9)`, all rejected by the real RelayYard `_clear_path(anchor, anchor + (0.01,0,0.01))`. Native `safe_navigate((-15,0,9), (-15,0,12))` returns `(-15,0,9)`. The bot remains 3m from its destination, receives zero movement through `bot_ai.gd:562-567`, and its stuck timer does not grow because no movement is requested. The navigation regression checks only a nonzero initial route to postplant offsets, which does not detect this endpoint deadlock.

5. **P2, residual — Damage direction is overwritten before input emission.** For an unseen attacker, `bot_ai.gd:554-560` computes a turn toward the hit indicator. The subsequent navigation (`562-567`) or idle scan (`568-575`) always replaces that look. Probe baseline and recently damaged yaw are both `2.498091` although the hit arrives from yaw `-1.570796`. This does not affect the separate intentional FOV bypass when the damaging attacker is directly visible.

6. **P2, residual — Easy defenders bypass their hearing radius.** The shared auditory update respects easy `hearing_range = 18`, but a second raw `_heard` scan (`bot_ai.gd:424-430`) uses a hardcoded 22m. Native easy probe at 20m leaves `heard_at = -100` in the bounded update, yet destination selection still routes directly to the sound point. This defeats the advertised difficulty bound.

7. **P3, residual — Hearing precision parameters are unused.** `sound_noise` is declared as 2.4/1.1/0.35 for easy/normal/hard (`bot_ai.gd:26,42,58`) but never applied; `heard_pos` gets the exact authoritative shot origin at line 326 on every difficulty. Native probes confirm exact equality for all three profiles. This is a perception-fairness/documentation gap, not evidence of a network information leak.

8. **P2, frozen wiring, repaired by integration — Round plan selector was never called.** Frozen `create_team_state()` initializes `primary_site` to zero, and frozen match never calls `select_round_plan`. All bot-carrier rounds therefore default to Site A. Integration calls the selector at round reset (`match.gd:330` at `4aa6263`), restoring the intended variety.

## Adapter review

The integration maps each hook to its actual module contract and passes existing authoritative dictionaries and elapsed game time. It keeps purchases through `actor.buy_weapon`, combat through `actor.input_state`, and existing actor cooldown/reload/damage methods. It does not grant ammo, health, credits, authority, or ranked eligibility directly. The smoke property rename is necessary compatibility repair. Test API replacements, protocol expectation 6 (the existing integrated network protocol), physics synchronization before wall queries, and disabling incidental match ticks in unit fixtures are appropriate.

The original test's `pursue_memory` expiration assertion is vacuous: this role is never assigned by the module. The stated clear-corridor positive LOS setup is overwritten before a positive assertion. Weapon-data equality does not by itself test damage/cooldown invariance across difficulty. The original Python simulation harness and raw seed results are not present in PR14; its detailed improvement figures cannot be reproduced from the committed changes. Native evidence below should be reported separately from those historical/self-assessed claims.

## Native comparison

Godot `4.7.2.stable.official.ed1daf0bf`, real physics at fixed 60Hz, 10 bots, three seeds (`1847`, `2026`, `3141`) on all three difficulties. Both conditions use the same `native_comparison.gd`, match RNG seeds, and actor RNG seeds. Only buy waits are skipped. Each condition naturally resolves two rounds without forced winners or injected objective states. Baseline is PR11 `11573e587f13dfd832613a0c09dbc615f46d3461`; integration AI source is `4aa6263` (subsequent unrelated UI edits do not affect this run). All 18 rounds per condition completed.

| Metric, baseline → integration | Easy | Normal | Hard |
| --- | ---: | ---: | ---: |
| Rounds observed | 6 → 6 | 6 → 6 | 6 → 6 |
| Attack / defense round wins | 0:6 → 2:4 | 2:4 → 3:3 | 5:1 → 5:1 |
| Target switches / engaged bot decisions | 9.46% → 4.21% | 9.36% → 13.17% | 17.08% → 25.67% |
| Commanded-movement stall ratio | 6.05% → 5.75% | 5.58% → 7.24% | 2.97% → 15.65% |
| Bot decisions with stuck >0.9s | 9 → 8 | 6 → 0 | 1 → 11 |
| Plants / defuses | 0/0 → 0/0 | 2/1 → 2/2 | 3/1 → 0/0 |
| Interact input decisions | 0 → 0 | 84 → 126 | 125 → 0 |
| Kills | 46 → 38 | 41 → 40 | 48 → 49 |
| Mean CPU microseconds per bot decision | 50.5 → 91.7 | 53.6 → 124.7 | 54.2 → 134.6 |

Stall means a bot requests movement but moved <0.05m since its previous decision. This is an observational proxy, not a direct A* failure counter. Target switches require a nonzero old and new target on consecutive decisions. Easy's improvement does not generalize to the other profiles in these samples. Hard had no objective interaction at all in these six integration rounds. This sample is deliberately small, covers only opening rounds, and cannot establish full-match balance, halftime behavior, mobile performance, or statistical significance. CPU timing is observational on an uncontrolled shared host; absolute decision cost remains modest.

Both comparison processes reported exit-only ObjectDB warnings (43 instances baseline, 4 integration). These are not attributed to the AI changes: the harness, static presentation caches and engine cleanup were not independently isolated. They did not produce script errors or stop the recorded rounds. The independent focused integration regression had no ObjectDB warning and failed only the retained audio assertion.

Reproduce after import:

```sh
XDG_DATA_HOME=/workspace/reviews/three-agent-20261016/ai-review/xdg-data \
XDG_CONFIG_HOME=/workspace/reviews/three-agent-20261016/ai-review/xdg-config \
XDG_CACHE_HOME=/workspace/reviews/three-agent-20261016/ai-review/xdg-cache \
/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64 \
  --headless --fixed-fps 60 --path TREE/game \
  -s /workspace/reviews/three-agent-20261016/ai-review/native_comparison.gd
```

Immutable-module behavioral probes use minimal match/actor stubs, plus an explicit `smoke_charges` alias solely to pass the separately identified frozen property mismatch; navigation probes instantiate the real frozen RelayYard. See `module_probe.gd` and `module-probe.log`. Raw native gameplay evidence is in `baseline-comparison.log`, `integration-comparison.log`, their JSON extracts, `comparison-summary.json`, and `integration-source-sha256.txt`.
