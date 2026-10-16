# SIGHTBREAK Tactical Bot Intelligence Architecture (`SBBotAI`)

## 1. Executive Summary & Design Goals

`SBBotAI` (`game/scripts/gameplay/bot_ai.gd`) replaces the monolithic inline conditional block previously embedded inside `TacticalMatch._bot_input()` (`game/scripts/gameplay/match.gd`) with a modular, bounded-perception tactical AI architecture designed for 5v5 mobile tactical play on Relay Yard.

### Core Engineering Principles
1. **Strict Separation of World Truth vs. Permitted Bot Knowledge**: Bots never read hidden enemy live coordinates. Every tactical decision operates strictly on:
   - Direct visual line-of-sight (`SBActor.can_see()`, respecting world geometry, combatant body occlusion, and active `SBUtility` smoke clouds).
   - Difficulty-scaled field-of-view (FOV) cones and visual ranges.
   - Directional damage awareness (`SBBotAI.record_damage()`) when hit by a visible attacker.
   - Audible gunshot events (`TacticalMatch._heard`) within bounded hearing radius and decay windows.
   - Bounded individual and team contact memory (`_bot_state[id].last_seen`, `_team_ai_state[team].contacts`, `_team_ai_state[team].fallen_pos`) that expires deterministically.
2. **Full Preservation of Authoritative Gameplay & Network Contracts**:
   - Bots emit standard `actor.input_state` dictionaries (`move`, `look`, `fire`, `reload`, `jump`, `crouch`, `interact`, `weapon`, `smoke`, `grenade`) consumed by `SBActor.tick_authority(delta)` and `TacticalMatch._objective_tick(delta)`.
   - Zero modifications to weapon damage, hit registration, headshot volumes, weapon cooldowns, economy transactions, network RPCs, or `PROTOCOL_VERSION`.
   - Narrow integration footprint in `game/scripts/gameplay/match.gd` (replacing `_bot_input`, `_nearest_defender`, and `_cover_position` with single-line delegates to `SBBotAI`) to prevent merge conflicts with Codex's networking branches (`codex/network-lifecycle-v2`, PR #5-#11) and Claude's UI/art branches (PR #2, PR #12).

---

## 2. Baseline Technical Analysis (Pre-Slice Shortcomings)

Inspection of `game/scripts/gameplay/match.gd` (lines 447-564), `game/scripts/gameplay/arena.gd` (lines 234-268), and `game/scripts/gameplay/actor.gd` on base commit `148760e19ae14755ced379245df6c5510ad4cdd4` identified 10 structural shortcomings in the baseline bot implementation:

| Category | Baseline Implementation | Observed Shortcoming |
| :--- | :--- | :--- |
| **1. Perception Range & Damage Blindness** | Hardcoded `nearest = 28.0` m cap and `facing.dot(toward) > -0.15`; `_damaged()` did not notify bot state. | Relay Yard is 48m x 48m (`Relay AR` range 70m, `Longwatch` 100m). Bots ignored enemies >28m away and never turned toward visible enemies shooting them from outside their front FOV cone. |
| **2. Target Switching Oscillation** | Selected minimum Euclidean distance every `0.12s` tick with zero hysteresis; reset `state.reaction = 0.0` on every target ID change. | When two enemies stood at similar distances, bots rapidly switched `state.target` between them (`36.6%-43.8%` switch rate per engagement tick), repeatedly resetting `reaction` to `0.0` and failing to fire. |
| **3. Recoil & Spread Ignorance** | Aimed raw `desired.y = atan2(aim.y, dist_2d)` while strafing at `0.4` continuously during full-auto fire. | `SBActor._fire()` adds `recoil.y` (up to `+0.16` rad / `9.1 deg`) and movement spread (`0.026` rad). Bots never compensated pitch/yaw for accumulated `actor.recoil` and never counter-strafed or burst-fired at range. |
| **4. Predictable Lockstep Routing** | Attackers always targeted `arena.sites[0 if round_number % 2 == 0 else 1]` along identical A* paths. | All 5 attackers marched single-file along the same corridor to the same point; zero flank/mid split or human-carrier adaptation. |
| **5. Human Carrier Disconnect** | Non-carrier attackers ignored where `objective_carrier` actually moved. | If the human player (`local_id == 1`) carried the device to Site B on an even round, all 4 bot teammates went to Site A and waited indefinitely. |
| **6. Post-Plant Obstacle Deadlock** | `destination += Vector3(cos(hold_angle), 0, sin(hold_angle)) * 4.5` around `objective_position`. | On both Site A `(-15, 0, 10)` and Site B `(15, 0, 10)`, slot 2 of the 4.5m circle lands inside an expanded obstacle AABB (`(-18, 0.65, 13)` and `(15, 0.45, 12.4)`). Because `RelayYard._clear_path(to, waypoints[i])` returns `false` for all waypoints when `to` is inside an obstacle AABB, `bot_navigation()` returned `from` (`finish == -1`), stalling the bot. |
| **7. Asymmetric Audio & Zero Team Comms** | Only defenders checked `_heard` (and only for `2.0s` within `22m`); attackers ignored `_heard` completely. | Attackers never reacted to nearby defender gunfire; teammates shared neither enemy sightings nor elimination locations. |
| **8. Static Open-Site Defense** | Defenders walked to exact site center `arena.sites[actor_id % 2]` and stood in the open scanning `(0, 0, -18)`. | Defenders did not hold tactical cover anchors (West Box, Mid Crate, East Box) and were easily eliminated from multiple angles (`0%-8%` baseline defender round win rate). |
| **9. Cover & Survival Deficit** | `_cover_position()` was only called when `actor.reload_remaining > 0` and `target != null`. | Low-health bots never retreated to cover, and bots initiating a reload on the current tick (`ammo == 0`, before `tick_authority` sets `reload_remaining`) waited an extra tick exposed in the open. |
| **10. Loadout & Utility Neglect** | Hardcoded `actor.buy_weapon("rifle" if actor.credits >= 2400 else "smg")`. | Bots never bought `marksman` rifles, never switched to `sidearm` (`0.3s` deploy) when primary ammo ran dry in close quarters (`2.25s` rifle reload), and never deployed `smoke` utility. |

---

## 3. Modular Architecture (`SBBotAI`)

`SBBotAI` is organized into eight cohesive subsystems within `game/scripts/gameplay/bot_ai.gd`:

```
TacticalMatch (_authority_tick @ 8.33 Hz / 0.12s)
  └── SBBotAI.tick_bot(match_node, actor, delta)
        ├── 1. Difficulty Profile Lookup (PROFILES[difficulty])
        ├── 2. Perception & Bounded Memory (acquire_target, record_damage, record_elimination)
        ├── 3. Team Coordination & Round Plan (select_round_plan, report_team_contact, get_team_contact)
        ├── 4. Objective Priority & Role Selection (select_destination, nearest_defender, get_site_hold_position)
        ├── 5. Safe Navigation & Stuck Recovery (safe_navigate + RelayYard.bot_navigation fallback)
        ├── 6. Combat Decisions & Recoil/Spread Discipline (recoil_compensation, burst cooldown, counter-strafe, sidearm fallback)
        ├── 7. Cover Seeking & Low-HP Retreat (cover_position, cover_position_from_point)
        └── 8. Authoritative Input State Emission (actor.input_state)
```

### 3.1 Difficulty Configuration (`PROFILES`)
Difficulty is driven by explicit, measurable parameters rather than pure random aim error:

| Parameter | Easy | Normal | Hard | Purpose |
| :--- | :---: | :---: | :---: | :--- |
| `reaction_delay` | `0.60s` | `0.35s` | `0.18s` | Minimum continuous target lock before firing is permitted |
| `turn_speed` | `3.5 rad/s` | `5.0 rad/s` | `7.0 rad/s` | Maximum angular slew rate for yaw and pitch |
| `aim_error` | `0.045 rad` | `0.022 rad` | `0.008 rad` | Bounded angular aim jitter |
| `aim_height` | `1.10 m` | `1.18 m` | `1.26 m` | Vertical aim point (upper torso vs. high chest/neck) |
| `vision_range` | `28.0 m` | `38.0 m` | `46.0 m` | Maximum visual detection distance |
| `fov_dot` | `-0.05` | `-0.15` | `-0.25` | Forward FOV dot-product threshold |
| `memory_duration` | `2.0 s` | `3.8 s` | `5.5 s` | Duration a last-seen position remains actionable |
| `hearing_range` | `18.0 m` | `26.0 m` | `34.0 m` | Audible gunshot investigation radius |
| `recoil_compensation` | `0.15` | `0.65` | `0.92` | Fraction of `actor.recoil` counter-aimed |
| `retreat_hp` | `0.0` | `28.0` | `38.0` | Health threshold for tactical cover retreat |
| `team_comms` | `false` | `true` | `true` | Enables shared team contact and fallen-ally alerts |
| `counter_strafe` | `false` | `true` | `true` | Decelerates movement at medium/long range to tighten spread |
| `utility_use` | `false` | `true` | `true` | Enables tactical smoke deployment on site executes/retakes |
| `sidearm_fallback` | `false` | `true` | `true` | Switches to `sidearm` when primary is empty in CQC (`<14m`) |

### 3.2 Perception & Bounded Memory
- **Visual Channel**: `acquire_target()` checks `enemy.alive`, `distance <= vision_range`, `in_fov or took_recent_damage`, and `actor.can_see(enemy)`.
- **Target Priority & Hysteresis**: To eliminate rapid target switching when multiple enemies are visible, `acquire_target()` computes an effective priority score:
  - Current target receives `TARGET_HYSTERESIS_BONUS = 4.5m`.
  - Enemy actively defusing the planted device receives `+6.0m` priority bonus.
  - Enemy carrying the objective device receives `+3.5m` priority bonus.
  - Enemy who damaged this bot within the last `1.5s` receives `+4.0m` priority bonus.
- **No Hidden Coordinate Tracking**: When `target == null`, `state.last_seen` is never updated from `enemy.position`. Once `_elapsed - state.seen_at >= memory_duration`, the memory expires.

### 3.3 Team Coordination & Objective Behavior
- **Adaptive Site Selection (`select_round_plan`)**:
  - Rotates default target sites across rounds using a deterministic hash of `round_number` rather than a rigid even/odd alternation.
  - Dynamically adapts if the objective carrier (especially a human player) moves past `z > -8.0` toward Site A (`x < -4.0`) or Site B (`x > 4.0`), redirecting bot teammates to support the human carrier's chosen site.
- **Coordinated Roles (`select_destination`)**:
  - **Attackers**:
    - `carrier`: Moves to `target_site` and holds `interact` when `arena.is_at_site(actor.position) >= 0`.
    - `split_flank`: One support bot routes through mid/flank waypoints (`ATTACK_SPLIT_WAYPOINTS`) during the opening 22 seconds of the round before converging on the site.
    - `entry` / `escort`: Remaining bots escort the carrier or clear nearby audible/reported threats, then spread across validated `SITE_HOLD_OFFSETS` so they never stack on a single point.
    - `post_plant_hold`: Once planted, attackers hold distinct crossfire positions around `objective_position` validated via `get_site_hold_position()`.
  - **Defenders**:
    - `anchor`: Hold tactical cover anchors across Site A (`(-14, 0, 9)`, `(-18, 0, 10)`), Mid (`(0, 0, 11)`), and Site B (`(14, 0, 9)`, `(18, 0, 10)`).
    - `rotate_investigate`: Rotate toward confirmed team sightings, fallen-ally positions, or audible gunfire.
    - `defuser` / `retake_cover`: When the device is planted, `nearest_defender()` assigns a single defuser (giving priority to a human player holding `interact` within `2.8m`), while all other defenders hold cover angles around the site.

### 3.4 Safe Navigation & Multi-Stage Stuck Recovery
- **Obstacle AABB Endpoint Fallback (`RelayYard.bot_navigation` & `SBBotAI.safe_navigate`)**:
  - Previously, if `from` or `to` fell inside one of `RelayYard._obstacles` (which are expanded by `0.55m` around geometry), `_clear_path()` returned `false` for every waypoint and `bot_navigation()` returned `from`.
  - `RelayYard.bot_navigation()` now tracks `fallback_start` and `fallback_finish` (the nearest waypoints by Euclidean distance) when `start < 0` or `finish < 0`, ensuring A* always finds a valid path out of or toward near-obstacle positions.
- **Multi-Stage Stuck Recovery**:
  - `stuck > 0.9s`: Applies lateral strafe offset (`move.x = +-1`).
  - `stuck > 1.5s`: Triggers `jump = true`.
  - `stuck > 1.8s`: Selects an alternative unobstructed adjacent waypoint and reverses `move.y = -0.6` to un-wedge from container corners.

---

## 4. Shared-File Interface Contract (`game/scripts/gameplay/match.gd`)

To preserve clean merges with Codex's networking branches and Claude's UI branches, `match.gd` was modified at only 6 narrow hook points:
1. `var _team_ai_state: Dictionary = SBBotAI.new_team_state()`
2. `_reset_bot_state(actor)` -> `_bot_state[actor.actor_id] = SBBotAI.new_bot_state(actor.position)`
3. `_begin_round()` -> resets `_team_ai_state` and calls `SBBotAI.buy_equipment(actor, difficulty, round_number)`
4. `_damaged(victim, attacker, amount)` -> calls `SBBotAI.record_damage(self, victim, attacker, amount)`
5. `_eliminated(victim, killer)` -> calls `SBBotAI.record_elimination(self, victim, killer, killed.position)`
6. `_bot_input`, `_nearest_defender`, and `_cover_position` -> 1-line delegates to `SBBotAI`.

All existing keys in `_bot_state[actor_id]` (`reaction`, `target`, `last_position`, `stuck`, `last_seen`, `seen_at`) are preserved with identical types and semantics so existing unit tests (`game/tests/match_test.gd`, `bot_match_test.gd`, `bot_lifecycle_test.gd`) continue to pass without modification.