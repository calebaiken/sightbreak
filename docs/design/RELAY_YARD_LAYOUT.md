# Relay Yard layout, revision 2

Status: **implemented and measured with bots; not human-playtested.** The layout was designed and first measured in draft PR #26 (`claude/relay-yard-tactical-layout-v1`, where its images, critic reviews and raw logs live). It is integrated here onto the v1 playability stack (PR #31), re-measured there with fair actor ordering, and given a handshake identity so mixed builds are refused. See [the integration report](../reports/relay-yard-integration/README.md) for those numbers and their limits. The tables below are PR #26's original measurements, kept as the design record.

## Why the layout changed

Revision 1 was a 48 m x 48 m open pad: four boundary walls, six freight containers, nine crates and six poles (25 navigation obstacles, no elevation). A top-down render shows it plainly; a dump of the arena's collision volumes confirms it.

All-bot matches on the unmodified build (`codex/desktop-playability-p1` at `db3981e`, real engine, seeds 41-46, both start orders, normal difficulty, 12 matches, 114 rounds) showed what that does to play:

- The median round lasts 12.0 s. The first kill lands 1.6 s into the live phase.
- 94% of first kills happen inside a spawn zone, at a median kill distance of 29.8 m. Defenders at their hold positions shoot attackers at the attacker spawn across the open yard.
- Attackers plant in 9% of rounds.
- 95.7% of walkable cells are visible from at least one defender hold position, and the attacker route to a site is exposed along 97% to 100% of its length, in unbroken runs of 30 to 38 m.

A tactical shooter needs approach, contact, plant and post-plant. Revision 1 had contact at spawn.

## What changed

Spawns, sites, the outer shell, the hall and every existing container and crate are unchanged. `arena.gd` adds 13 solids (`LAYOUT_REVISION = 2`; `layout_solids` counts them). Coordinates are world metres; z runs from the attacker end (-) to the defender end (+).

| Solid | Position, size | Purpose |
| --- | --- | --- |
| Screen wall, 5 containers along x | z -17; x -24..-19, -14..-4, -4..4, 4..14, 19..24 | Hides the attacker spawn from the yard. Two exits, west x -19..-14 and east x 14..19. The middle is solid. |
| Exit blocks (2) | (+-16.5, -11), 6 m along x | The first thing an attacker sees outside an exit is a corner. |
| Lane dividers (2) | (+-13.5, -2), 5 m along x | Each side lane is crossed through two 2.5 m doors, in two hops. |
| Site shields (2) | (+-17.5, 4.5), 5 m along x | Break the lane's long line to each site; entrances on either side. |
| Spine extensions (2) | (+-7, 11), 6 m along z | Lengthen the two long spines south so each site sits in its own compartment and the site-to-site line along z = 10 is cut. |

Mid is a hub, reached from the side lanes through the crossings between the north and south spines (z -6.5..0). Its north end is a pocket behind the screen.

Supporting changes:

- Navigation grid 3 m -> 2 m (`NAVIGATION_STEP`). The 2.5 m divider doors are narrower than a 3 m grid could follow. Even at 2 m the outer doors (x = +-17.25) fall between grid columns that the bots' 0.55 m obstacle margin removes, so six explicit nodes (`DOOR_WAYPOINTS`) put them on the graph; `layout_route_test.gd` requires every door to be a crossing, not a detour.
- `_container` takes `along_x` and a `tag`. Every layout container gets the same hardware fittings as the originals and a unique stencil. The label plate follows the stencil length (it overflowed for 15-character lines); this also applies to the original containers.
- Floor stencils "01 / FREIGHT" and "02 / RELAY" moved into the west and east exits and shrunk so the new wall no longer overprints them.
- Colour code kept: west red, east teal, neutral grey for blocks and screen ends.
- `DEFENDER_ANCHORS` in `bot_ai.gd` moved from the front of the yard to deeper positions near the sites: (-17.5, 9), (17.5, 9), (-11.5, 11.5), (11.5, 11.5), (0, 14.5). The old anchors at z = 6 looked straight down every lane mouth.

## Tried and dropped

Kept here because each one looked fine in pictures and failed in measurement.

| Attempt | What happened | Evidence |
| --- | --- | --- |
| Open the mid exit (6 m, then 8 m, with a baffle in it) | With a 6 m exit and a 4 m baffle the two side passes were 1 m wide: the bots' navigation graph had no node inside them, so **bots never used mid at all** (a probe found a 45 m detour for a 16 m trip). Widening it and adding navigation nodes made mid usable, and then every bot took it, because it is the shortest route. All five funnel through two 2 m passes into a 30 m lane covered from the defender end. Plants fell from 75% to 6% (normal), clock-outs rose to 6% to 17%. | `data/bots-trial-mid-open-*` archives |
| Assign attackers to exits by slot | With mid open, two bots per squad via mid and three via the side exit. It did not rescue the pace (plants 5% to 7%). Removed. | same archives |
| Close the mid exit | Back to two exits plus a hub. This is the shipped version. | final data |
| Second mid baffle at (0, 3.5) | Blocked the lane that several tests use for fixtures: `weapon_integrity_test` failed seven checks and `actor_test` and `smoke_presentation_test` also failed. Dropped. | worklog |
| Limit defenders to two responders per sound | No demonstrable effect over six matches either way. Removed. | worklog |

## Measured effect

Seeds 41-46, each run twice (actors 1-5 attacking first and actors 6-10 attacking first), real engine, bots only, `scripts/measure_relay_yard.sh`. Rates are over rounds. Spawn zone = the first or last 8 m of the yard.

| Layout | Difficulty | Matches | Rounds | Median live round (p10-p90), mean | Median first kill | Plant | Carrier reached a site | Attacker wins | Clock ran out | Median kill distance | First kills in a spawn zone |
| --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| before | normal | 12 | 114 | 12.0 s (6.7-32.6), 18.1 s | 1.6 s | 9% | 9% | 26% | 4% | 29.8 m | 94% |
| after | normal | 12 | 117 | 23.5 s (13.3-30.5), 23.5 s | 6.2 s | 75% | 78% | 59% | 1% | 14.4 m | 0% |
| before | hard | 12 | 123 | 15.4 s (5.5-100), 32.9 s | 0.4 s | 2% | 2% | 21% | 18% | 41.5 m | 100% |
| after | hard | 12 | 115 | 13.4 s (9.1-29.5), 16.0 s | 6.1 s | 15% | 16% | 67% | 0% | 17.9 m | 0% |

Geometry, from `tests/map_sightline_probe.gd` (38 m, the "normal" bot vision range; each build's own defender hold positions):

| | Before | After |
| --- | --- | --- |
| Walkable cells visible from a defender hold position | 95.7% | 64.3% |
| Defender hold positions with a line to any attacker spawn | 1 to 3 per spawn | 0 |
| Attacker route spawn to site | 36.7 to 39.2 m | 47.8 to 55.8 m |
| Share of that route exposed | 97% to 100% | 28% to 41% |
| Longest unbroken exposed stretch | 30 to 38 m | 14 to 18 m |

Blind visual review: four critic agents (one per round, fresh context, read-only, Claude family, stills only) saw unlabelled before/after pairs. The new layout won the overview every round and won 7, 11, 9 and 9 of 12 eye-level pairs. Scores were 5.5, 5, 6 and 6 out of 10 (round 3 gave the old layout about 3.5). They named the sites and route structure as the largest gaps. This is a judgment from stills by agents of the author's model family, not human acceptance.

An independent agent recomputed the earlier seeds 31-36 numbers from the raw logs: all reproduced, with the caveats below. [stats review](../reports/gauntlet/relay-yard-layout/stats-review.md).

## What this does not show

- **The attacker win rate is not a balance measure.** See finding F2 below: one squad wins about 71% of rounds whichever side it plays. With both start orders the role rates mix that out only roughly (59% normal, 67% hard).
- **Hard difficulty still rarely plants** (15%, up from 2%), and the median round is slightly shorter (13.4 s against 15.4 s) because the 100 s stand-offs are gone: the mean falls from 32.9 s to 16.0 s. Hard bots win the lane fights at the exit blocks before anyone reaches a site. Fixing that is bot-tactics work (staging, smoke before crossing, trades), not layout work.
- Bots only. No human has played this layout. Sightlines and routes say nothing about how the sites feel.
- Sites are still bare apart from one or two crates: no protected plant pocket, no second entry, no post-plant cover.
- No long "power lane" and no elevation: the longest sightline is about 25 m and the yard is flat. A critic asked for both.
- Software rendering. `box_instances` rose from 1,472 to 2,544 and shadow-casting instances from 793 to 1,397, still nine static batches. Device cost is unmeasured.
- The final defender anchors were chosen using seeds 31-36 and the table above uses seeds 41-46, which no tuning saw. Seeds 11-23 were used for earlier iterations.

## Finding F2: the lower actor ids win

Under the stock tick order (`actors.values()` in id order), actors 1-5 win 71% of rounds on normal in both the old and the new layout (81 against 33 in 114 old rounds, 83 against 34 in 117 new rounds), and 62% and 72% on hard, whichever side they play. With the processing order reversed (`--reverse-order` in the harness, eight matches, 87 rounds) actors 1-5 win 46%.

The authoritative tick runs `tick_authority` for each actor in id order, so in a same-tick trade the lower id fires and kills first. It is probably a real fairness defect for networked play too, where player ids are seats. It lives in `match.gd` (Codex-owned shared code), so it is not changed here. A fix would rotate or shuffle the processing order each tick; it needs its own PR and a regression test. Logged in the worklog.

**Update (M3).** Fixed outside PR #26, in draft PR #28 (`claude/fair-actor-order-v1`). There were two causes: the id-ordered tick, and bot habits keyed on raw id parity. A per-tick shuffle alone left ids 1-5 at 61%; with the habits made squad-symmetric the pooled normal result is 49.9% (46.8% to 53.1%) over 72 matches. The attacker win rates in the table above (59% normal, 67% hard) were measured before the fix and are confounded.

**Update (integration).** The v1 playability stack (PR #31) resolves same-tick trades with its own movement, action and contact phases (`authority_order_test.gd`), so the table's win rates can be re-measured on it. They are in the [integration report](../reports/relay-yard-integration/README.md): with fair ordering, attackers win about 62% of normal rounds on this layout, against about 25% on the open pad. That is no longer an attacker-starved game, and it is now somewhat attacker-favoured; tuning it is separate work.

## Compatibility notes for other contributors

- **Mixed builds.** The layout is the collision world every authoritative move and shot resolves in, so it is part of the compatibility contract. The handshake hello now carries `layout` (`LAYOUT_REVISION`) beside the protocol, which stays 6. A hello without the field is a build from before it existed and counts as revision 1, so a server on this layout refuses it and this client refuses a server that sends none. **Increment `LAYOUT_REVISION` with any change to the solids that affect collision.** `handshake_layout_test.gd` covers the decision, `test_handshake_hardening.sh` the hostile cases and `test_protocol_compat.sh` a real legacy build against this one in both directions.
- **Native scenario scripts.** `scripts/verify_offline_match.py` walked the plant scenario in a straight line from spawn to site A. That line is now blocked. The script follows `PLANT_ROUTE_SITE_A_REVISION_2`: a route through the west exit, **re-checked against the final geometry** (every leg is clear under the bots' obstacle map). Not run natively here (no native Windows or Linux export or OCR stack); the native CI must confirm. What is checked: `layout_route_test.gd` walks that same route, leg by leg in a straight line, through the engine's physics and plants, so a corner that clips the body fails the test. The defuse route is unchanged geometry.
- **Frozen tests.** `world_test` and `actor_test` froze 25 obstacles and 26 bodies. They now assert 25 plus `layout_solids` (13) and the revision. No threshold was relaxed and no fixture needed to move.
- **Radar.** `radar.gd` draws `arena._obstacles`, so the minimap follows the layout with no change.
- **Bots.** Only `DEFENDER_ANCHORS` changed. Paths come from the navigation graph. `SITE_HOLD_OFFSETS` (the attackers' escort holds) still follow the open-pad layout; see the integration report for the one deadlock that follows from it.

## Reproduce

```sh
export SIGHTBREAK_TOOLS_DIR=/home/user/tools SIGHTBREAK_STATE_DIR=/home/user/sightbreak/.local
./scripts/setup.sh
Xvfb :99 -screen 0 1920x1080x24 +extension GLX +render -noreset &
DISPLAY=:99 scripts/measure_relay_yard.sh out/relay-yard --both-starts --seeds "41 42 43 44 45 46" --difficulties "normal hard" --jobs 4
```

`bot_objective_metrics.gd` raises the physics tick rate with `--time-scale`, so every step stays 1/60 s of game time (Godot scales the physics delta by `Engine.time_scale`). To measure the old layout, run the same script from a checkout of `db3981e` after copying `game/tests/{bot_objective_metrics,map_overview_capture,map_sightline_probe,map_viewpoints_capture}.gd` and `scripts/{measure_relay_yard.sh,summarize_bot_metrics.py}` into it. Matches take about two minutes each on four vCPUs.

## Next

1. F2 is fixed in PR #28 (pending Codex review). After it lands, re-measure side balance and pacing on this layout.
2. Site structure: a plant pocket, a second entry and post-plant cover at each site.
3. Hard-difficulty tactics so rounds reach the sites.
4. A long lane and a half-height position for variety.
5. Visual polish carried from the critics: floating hoist block, flat far wall, canopy overprinting signs, hard-edged floor decals, near-black shadow over the defender half (all present before this change).
6. A human playtest.
