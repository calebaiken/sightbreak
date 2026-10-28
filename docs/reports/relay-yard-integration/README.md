# Relay Yard layout on the v1 playability stack

Base: `830bf2ba` (head of draft PR #31, `codex/v1-executor-recovery-20261023`). Layout source: draft PR #26 (`claude/relay-yard-tactical-layout-v1`, commits `641b0c2a` and `fc423c4f`).

This record covers one blocker, how it was reproduced on the stack, what was changed, what was measured before and after with a harness other than the one the layout's author used, and what was not verified. It is evidence for a development candidate. It is not human play, device performance or native-platform acceptance.

## The blocker

On the playability stack, an attacker spawn and a defender spawn see each other across the whole yard. All 25 attacker-to-defender spawn pairs have an unobstructed head-height line, 41.5 to 42.4 m long (`tools/spawn_los.gd`: a ray cast through the real physics world with the mask and head height `SBActor.can_see` uses). The result is that rounds are decided in seconds and the plant, the objective the game is built around, almost never happens.

| Measured on `830bf2ba` | easy | normal | hard |
| --- | ---: | ---: | ---: |
| Matches / rounds | 8 / 76 | 16 / 166 | 8 / 84 |
| Median live round (p10 to p90) | 12.8 s (8.8 to 21.3) | 12.1 s (6.4 to 28.3) | 14.9 s (3.7 to 100) |
| Rounds with a plant | 1% | 15% (10 to 21%) | 0% (0 to 4%) |
| Rounds won by the attackers | 42% | 25% (19 to 32%) | 19% (12 to 29%) |
| Rounds that ended by detonation | 0 | 0 | 0 |

Half of the `normal` rounds are over within 12.1 s of going live. The human always starts as an attacker (`local_id = 1`, team 0).

The same defect was measured independently on an earlier stack in PR #26 (median round 12.0 s, first kill at 1.6 s, 94% of first kills inside a spawn zone, plants in 9% of rounds). The two measurements use different bases, harnesses and seeds and agree.

**Deterministic reproduction.** `game/tests/map_sightline_probe.gd --assert` fails on the old yard and passes on the new one:

```
ERROR: a defender hold position has a line to attacker spawn (-4.4, 0.05, -21.0)      (x5 spawns)
ERROR: attacker route to site 0 is 36.7 m, under 44 m
ERROR: attacker route to site 0 is 97% exposed
ERROR: attacker route to site 0 has an unbroken exposed stretch of 30 m
```

Raw output: [`data/sightline-probe-before.txt`](data/sightline-probe-before.txt), [`data/sightline-probe-after.txt`](data/sightline-probe-after.txt).

## What changed

| Area | Change | Origin |
| --- | --- | --- |
| Yard | 13 container solids (`LAYOUT_REVISION = 2`): a screen wall with two exits, exit blocks, lane dividers with two 2.5 m doors, site shields, spine extensions. Spawns, sites and the shell are unchanged. | PR #26, three-way merged onto the stack against the true merge base `c84eaf3c`. No conflicts. |
| Navigation | Grid 3 m to 2 m. `DEFENDER_ANCHORS` moved deeper. | PR #26 |
| Navigation | Six door nodes (`DOOR_WAYPOINTS`): the 2.5 m outer lane-divider doors were not on the 2 m graph (found in review, below). The graph is 360 waypoints and 1,441 edges, was 176 and 504. | New here |
| Tests | `map_sightline_probe.gd --assert` (35 checks), `actor_test` and `world_test` assert the 25 original obstacles plus the 13 declared solids. | PR #26 |
| Handshake | The hello carries `layout`. A server refuses a client on another layout; a client refuses a server that sends none. A hello without the field is revision 1. Protocol stays 6. | New here. PR #26 listed this as open. |
| Layout guard | `handshake_layout_test.gd` fails if any collision shape in the yard changes without a new `LAYOUT_REVISION`. | New here |
| Traversal test | `layout_route_test.gd` walks a real attacker through the physics along the bots' route and the native verifier's scripted route (read from the verifier itself), to both sites, and plants, and walks a body through all four divider doors. | New here |
| Harness | `bot_objective_metrics.gd` raises the tick rate with `--time-scale`. | Fix to PR #26's tool |
| Docs | `docs/design/RELAY_YARD_LAYOUT.md` records the design and what this integration changed. | PR #26, edited |

Not ported from PR #26: its rendered gallery capture, the blind-pair script and its images and critic reviews (they remain on its branch).

## After

Same 32 seeds and the same harness, on the new yard (`audit.sh`, see Reproduce):

| Measured on the new yard | easy | normal | hard |
| --- | ---: | ---: | ---: |
| Matches / rounds | 8 / 89 | 16 / 179 | 8 / 82 |
| Median live round (p10 to p90) | 24.4 s (11.4 to 30.8) | 23.2 s (15.9 to 30.7) | 12.9 s (9.2 to 27.9) |
| Rounds with a plant | 84% (75 to 90%) | 72% (65 to 78%) | 18% (11 to 28%) |
| Rounds won by the attackers | 47% (37 to 57%) | 62% (55 to 69%) | 74% (64 to 83%) |
| Rounds that ended by detonation | 0 | 0 | 0 |
| Rounds that ran out the clock | 0 | 1 | 0 |
| Invariant violations in all matches | 0 | 0 | 0 |

Once a site is reached the device is planted in a median of 3.1 to 3.2 s on every difficulty (the plant takes 3 s), so the carrier plants on arrival.

How to read this:

- **The loop now works on easy and normal.** Plants go from 1% to 84% and from 15% to 72%, and the median round roughly doubles. `normal` is the difficulty the player meets first.
- **Hard improves least.** Plants go from 0% to 18% and the median round does not lengthen (14.9 s to 12.9 s), but the clock no longer runs out (12 of 84 rounds before, none after). Hard bots win the first fights at the exits. PR #26 saw the same (15%). That is bot tactics, not layout.
- **The attacker side is now favoured, not starved.** Attackers win 62% of `normal` rounds against 25% before. Both are far from an even game. This is bots with fair ordering (the stack's two-phase tick), not a balance verdict, and no human has played it. Tuning belongs to a separate change.
- **No round ends by detonation, before or after.** Defenders always defuse or are eliminated first. Not a defect found here, but a post-plant pressure question for tuning.

Raw per-match results: [`data/before.jsonl`](data/before.jsonl), [`data/after.jsonl`](data/after.jsonl). Seeded matches are deterministic: the final `normal` seed 3 was re-run with the committed tool and was identical to the stored run, and eight earlier seeds re-run with a later harness revision were identical.

![The old yard](images/overview-before.png) ![The new yard](images/overview-after.png)

Top-down native render (software GL, relative only). Left: open pad. Right: revision 2.

## Regression coverage and negative controls

Each new check was shown to fail without the change it guards.

| Check | Result on the final tree | Fails when |
| --- | --- | --- |
| `map_sightline_probe.gd --assert` | 35 checks, 0 failures | Run on the old yard: 5 spawn lines plus route length, exposure and run failures (above). |
| `layout_route_test.gd` | 30 checks, 0 failures. Seven plant routes (9.5 to 11.3 s of walking each) and four divider doors (9.0 to 10.6 m on the graph). Clean under the CI's strict log gate. | Dividers stretched from 5 m to 14 m: 25 of 30 fail. Door nodes removed: the two outer doors fail at 24.8 m. A verifier waypoint moved into the screen wall: 3 fail. |
| `handshake_layout_test.gd` | 26 checks, 0 failures | One solid moved by 0.5 m, or only the floor resized, with the revision unchanged: the fingerprint check fails. |
| `test_handshake_hardening.sh` | 11 scenarios pass, including stale and unreadable layouts refused in about 0.55 s and a layout-less accept refused by the stock client | With the layout comparison disabled, the stale-layout peer is admitted. |
| `test_protocol_compat.sh` | 10 combinations pass, real server and client processes | See below. |

Mixed builds, real processes ([`data/protocol-compat-matrix.md`](data/protocol-compat-matrix.md)). The two new rows use `830bf2ba` as a real legacy build: protocol 6, no layout field.

| Client | Server | Result |
| --- | --- | --- |
| stack before layout 2 | this branch | refused after 0.1 s: "This server uses Relay Yard layout 2; this client sent no layout (a build from before layouts were announced)." |
| this branch | stack before layout 2 | refused after 0.2 s: "This client uses Relay Yard layout 2; this server sent no layout (a build from before layouts were announced)." |

The eight existing rows (0.3.0, published PR8, next protocol) are unchanged and pass.

## Cost

Fixed-camera benchmark (`scripts/profile_render.sh`, standard quality, three runs per view, two CPUs, Xvfb and Mesa llvmpipe). Counters are exact; frame times are relative only and are not device FPS.

| View | Draw calls | Primitives | Median frame |
| --- | --- | --- | --- |
| approach | 155 to 183 | 109,948 to 138,368 | 453 to 531 ms (+17%) |
| site | 48 to 54 | 72,196 to 99,952 | 397 to 468 ms (+18%) |
| overview | 166 to 214 | 75,674 to 104,714 | 338 to 439 ms (+30%) |
| operators | 138 to 156 | 75,024 to 103,140 | 367 to 437 ms (+19%) |

The yard goes from 1,472 to 2,544 box instances (nine static batches both times; the shadow share stays under the 60% budget at 55%). Bot thinking costs more with the denser graph: for the same seed, user CPU per simulated second is 45.6 ms on the old yard and 50.9 ms on the new, about +12% (headless, one match each, two processes in parallel). `apply_detail_quality` only switches material features, so the cost applies in every tier. **This is a real cost to mobile.** It has not been measured on a device.

Where it comes from, measured with the same benchmark on two scratch copies of the game (`median_of_run_medians_ms`, three runs each):

| View | Old yard | New yard | New yard, 13 containers as plain boxes | New yard, no fittings on the 13 |
| --- | ---: | ---: | ---: | ---: |
| approach | 453 | 531 | 489 | 533 |
| site | 397 | 468 | 441 | 478 |
| overview | 338 | 439 | 396 | 459 |
| operators | 367 | 437 | 393 | 435 |

Plain boxes alone cost +7 to +17% over the old yard; the ribs, doors, placards and labels add the other +6 to +11%. Dropping only the corner castings and plates changes nothing measurable (primitives -9%, frame time within noise), so gating "the small fittings" would not recover the cost, and nothing short of fewer or smaller containers does. This matters for the hosted Linux lane (below).

## Independent review of this change

A fresh-context review of the five commits found eight things. Each was checked before acting on it.

| Finding | Checked | Outcome |
| --- | --- | --- |
| The outer 2.5 m lane-divider doors are not on the 2 m navigation graph. | True: `get_point_path` crossed 9 m in 22.5 m (a detour) at x = 17.25 and 8.0 m at the inner doors. | Fixed: `DOOR_WAYPOINTS`; crossing is 8.3 m. Covered by `layout_route_test.gd`. |
| The layout fingerprint hashes only the navigation obstacles. | True: the floor is the one collision solid that is not one. | Fixed: it hashes every collision shape. A floor-only change now fails. |
| `layout_route_test.gd` copies the verifier's route by hand. | True. | Fixed: the test reads the route from `verify_offline_match.py`. |
| The graph grows about 2.3 times and every bot call scans it. | Partly: 176 to 360 waypoints, 2.05 times; CPU per simulated second measured at +12%, not 2.3 times. | No change. Measured and recorded under Cost. |
| The compat matrix pins a SHA, and the legacy row does not check the reason; a comment sits above the wrong block. | True. | Fixed: the row requires the layout reason and `client_layout=1`; a missing ref fails with a message; the comment moved. |
| A hello with no layout field is reported as "sent layout 1". | True, and confusing. | Fixed: "sent no layout (a build from before layouts were announced)". |
| `world_test.gd` says 12 layout solids; the code and the assertion say 13. | True (PR #26's comment). | Fixed. |
| The `_container` refactor changes the placard of the six original containers. | True, and already stated in the design doc (the plate follows the stencil length). | No change. |

The same pass also showed that the first version of `layout_route_test.gd` leaked two ObjectDB instances at exit, which `validate.sh`'s `^ERROR:` rule does not catch but the CI's strict gate (`native_log.failed`) does. That was fixed in the same commit.

**A correction to the third row.** Reading the verifier's route from its source stopped the two copies drifting, but the test walked it from an attacker spawn slot. The plant fixture (`offline_diagnostics.gd`) starts the human at (-15, 2), so the route was wrong and the review did not see it. The hosted lanes did (next section), and `layout_route_test.gd` now starts from the fixture's own position.

## Findings that were not fixed here

1. **Carrier and escorts can deadlock at site A.** Seed 3, `normal`, round 2: the device carrier stops 4.9 m from the plant zone at (-11.4, 0, 13.2) between two attacker escorts holding at (-11.6, 13.8) and (-11.4, 12.6), which are the `SITE_HOLD_OFFSETS` positions for the open pad. Bots do not yield to each other and the unstick strafe and jump never clears it, so the round runs 100 s and the defenders win on time. It is the only such round in 350 (1 of 179 on `normal`). Reproduce with `tools/audit.sh out normal 3`: the second round reason is "Time expired" and `per_round[1].site_reached_t` is 12.7 with `plant_t` -1. A fix needs a way for a holding bot to give way to a blocked teammate, or hold offsets that stay out of the approach, and a measurement of both.
2. **Idle-bot detector hits are unexplained.** The detector flags a bot with no target that has not moved for 8 s while far from its destination. Twelve flagged positions from the pre-door-node run were replayed with a lone actor using the bots' own navigation step; every one walked out and reached its destination with no stall, so they are not geometry traps. The old yard shows the same kind of hit, more often (129 unique on `normal` before, 62 after; 148 on `hard`, 25 after). Not claimed as a defect.
3. **Existing bot tests step physics at 1/15 s.** `bot_match_test`, `bot_lifecycle_test` and `bot_squad_observation` set `Engine.time_scale = 4` without raising the tick rate, and Godot scales the physics delta by the time scale. Their results are valid for what they assert, but the statistics that rest on them (bot symmetry, the 12-round matches) were not taken at the production step. `gunplay_rules_probe` already asserts the 60 Hz step. Left unchanged here.

## Validation on the final tree

Commit `44c4b02e` (everything after it changes documentation only). Linux x86_64, Godot 4.7.2, Xvfb with Mesa llvmpipe for the rendered groups.

| Run | Result |
| --- | --- |
| `scripts/validate_matrix.py --render --protocol`, the CI entry point | **75 groups, 0 failed.** The tree was clean at start and end, and no child process log contains a leaked-object line (`nested-resource-cleanup`). It includes every Godot suite in `validate.sh` (the rendered reload and viewmodel groups under Xvfb), the two-client and ten-client network soaks, the connection lifecycle, the 10-combination protocol matrix, the 11 hostile-handshake scenarios and the render lifecycle. |
| The Python unit tests at the end of `validate.sh`, which the matrix does not run | 11 files, all OK (three skips in `test_native_observation` are inherited). `verify_offline_match.py` compiles. |
| 27 headless suites on `830bf2ba`, before any change | All passed. No existing test pointed at this defect; it was found by the audit above. |

One thing the first matrix run caught that `validate.sh` alone would not: the CI's log gate (`scripts/native_log.py`) fails on `ObjectDB ... leaked`, which `validate.sh`'s `^ERROR:` rule ignores. The new route test leaked two objects at exit until it waited for the audio server; that run is not counted above.

**Not run:** the `--backend` groups (PostgreSQL, account and economy, native economy). Docker is not usable in this container. They are unverified for this change, which touches no backend code.

**Also run locally (Linux x86_64, this container):** the CI's `scripts/run_native_regressions.py` (16 suites, `passed: true`, source unchanged); `./scripts/export.sh linux` (clean under the strict log gate); an iOS project export; and the exported Linux build's graphical menu startup. The exported build's `verify_offline_match.py --scenario plant` does not get past its first waits here (software rendering runs the simulation at 0.32 of real time; the base build gets further, at 0.36, and then fails at "Natural next round after objective resolution"), so it says nothing about the route; the hosted runs below are the native evidence. After the verifier fixes: `layout_route_test.gd` 43 checks, 0 failures; the ten Python test files that read the verifiers (`test_focus_resume_timing`, `test_native_focus_fence`, `test_offline_capture_fences`, `test_offline_role_guidance`, `test_offline_export_ocr`, `test_native_route_pulse`, `test_reopened_shutdown_diagnostic`, `test_linux_frame_sampler`, `test_linux_gpu_profile`, `test_native_approach`) all OK. The full matrix above was run before these last commits; see the validation line at the end of this section.

## Hosted native runs

The repository's own native lanes (`.github/workflows/desktop-alpha.yml`, "Native desktop alpha", `workflow_dispatch`, read-only permissions, no secrets) were run on this branch and on the stack base `830bf2ba`. Each lane exports the game for its host, drives the exported window with OS-level input and reads the result from the game's debug observation file. Only job logs were readable from this environment (artifact and blob downloads are blocked by its network policy), so a failing step's reason is whatever the step printed. Windows hosted runners render in software (ANGLE on the Microsoft Basic Render Driver) and Linux ones with Mesa llvmpipe; neither is a GPU and neither says anything about device frame rate.

**Windows**

| Step | Base `830bf2ba` | PR `18b285b0` | PR `85fc2d36` | PR `976fcd14` |
| --- | --- | --- | --- | --- |
| 27 Real keyboard and pointer input | pass | pass | fail (reason not retrievable) | pass |
| 30 Living-player input and settings restart | pass | fail: "Fresh W press moves actual player after focus recovery" | pass | pass |
| 31 Real player plant | pass | fail: "Legitimate native movement did not reach the requested floor position" | fail: "Native approach lost its living player or live round" | **pass** |
| 32 Defuse after a bot plant | pass | pass | pass | pass |
| 33 Full stock-rules match | pass, 7 m 42 s | ran (8 rounds, 7:1) | ran | **pass, 17 m 21 s** |
| Job | success | failure | failure | **success** |
| Run | [40655611147](https://github.com/calebaiken/sightbreak/actions/runs/40655611147) | [40655596107](https://github.com/calebaiken/sightbreak/actions/runs/40655596107) | [40662513575](https://github.com/calebaiken/sightbreak/actions/runs/40662513575) | [40666352140](https://github.com/calebaiken/sightbreak/actions/runs/40666352140) |

Step 27 is the armory menu navigation, which the layout does not touch; it failed once and passed on the next run, and is treated as a flake, but its reason was not read. The full match is longer than the base's because rounds are longer (an idle device carrier now runs the 100 s round out instead of the spawn fight ending it in about 12 s).

**What the failing runs found, all in my own work and all in the verifiers' assumptions about the old yard** (each now has a regression check in `layout_route_test.gd`, with a mutation that fails it):

1. *Plant route.* The route I added in the first commits started from the attacker spawn row. The fixture starts the human at (-15, 2), so the first leg went back across the lane divider. The detour that is needed is round the east end of the new site shield (`PLANT_ROUTE_SITE_A_REVISION_2`, three legs ending at the old plant point). The test now walks it from the fixture's own start, read from `offline_diagnostics.gd`, and shows the old straight line ends against the shield.
2. *Focus test.* It holds W through a focus loss, then presses W again and needs the body to move. The screen wall is 2.2 m ahead of the spawn row, so the held W ran the body square into it (the logged observation is at z = -18.81, yaw exactly pi, velocity 0). The old yard had 5.2 m of room, beyond what the hold covers. The test now turns the mouse 50 px first so the body slides along the wall. Checked in physics: square to the wall the body stops, after a turn of 0.03 rad or more it moves.
3. *Smoke.* The scenario throws a smoke due north from the fixture start so the defenders cannot see the walk. In the old yard it landed at (-15, 7.3), on the plant point. The new shield is directly in front of that throw, so the smoke dropped at (-15, 1.1) behind the player and the defenders shot the walk (Linux client log: "Slate > Operator", "Relay device dropped"). The verifier now names `PLANT_SMOKE_YAW` (pi + 0.25) and `PLANT_SMOKE_PITCH`; the smoke lands at (-13.7, 7.2). In the real physics with live defenders on the fixture's row: old yard, straight route, old smoke arms 4/4; new yard, detour, old smoke dies at about 5 s, 4/4; new yard, detour, new smoke arms 4/4, also with 3 s of rest at every waypoint. The route test now runs that scenario and checks the cloud lands on the plant point.

**Linux**

| Step | Base `830bf2ba` | PR `18b285b0` | PR `85fc2d36` | PR `976fcd14` |
| --- | --- | --- | --- | --- |
| 30 Living-player input and settings restart | pass | fail: "Natural exported round completion" | fail: "Second active round for weapon switching" | fail: "Natural exported round completion" |
| 31 Real player plant | fail (reason not read) | fail: route timeout | fail: lost living player | fail: "Natural next round after objective resolution", after "Relay device armed" |
| 32 Defuse | fail (reason not read) | pass | pass | pass |
| 33 Full match | pass, 19 m | fail: "Whole exported offline scenario deadline exceeded" (1800 s) | fail: "Standard first live round" | fail: "Standard first live round" |
| 34 Rendered layouts and touch toggle | pass | not read | fail: 1080p capture set incomplete | fail |
| Run | [40655606964](https://github.com/calebaiken/sightbreak/actions/runs/40655606964) | [40655592535](https://github.com/calebaiken/sightbreak/actions/runs/40655592535) | [40662517962](https://github.com/calebaiken/sightbreak/actions/runs/40662517962) | [40667132618](https://github.com/calebaiken/sightbreak/actions/runs/40667132618) |

On `976fcd14` the human now plants natively on Linux ("Relay device armed"), then the lane runs out of wall time. The pattern is the same on every Linux failure: the step waits a fixed number of wall seconds for simulation to advance (160 s for a round to end, 35 s for round 2 to go live, 45 s for the first live round, 1800 s for the match), and the hosted renderer draws 2 to 3 frames a second. Godot runs at most `max_physics_steps_per_frame` (8) physics steps per drawn frame, so the simulation runs at about a third of real time (measured in this container: 19.2 ticks/s on the PR build against 21.6 on the base, at 2.40 and 2.70 fps; 45 s for the 15 s buy phase needs 0.333, which sits between them). Two things from this change push the Linux lane over its margins: the new yard costs 17 to 30% more frame time (Cost, above), and rounds are longer by design. The budgets are pinned by tests (`test_reopened_shutdown_diagnostic.py` asserts `--timeout 300`; others pin 180) and were not changed here. The base already fails Linux steps 31 and 32, so this lane was not a clean gate before. **This is a regression in what the Linux lane can verify, not a game defect.** The follow-up is to derive these budgets from simulation time (the observation exposes `elapsed`, `time_scale` and `simulation_tick`), which is the owners' call because the budgets are deliberate.

**macOS (macos-15, arm64), two runs each**

| | Base | PR `18b285b0` |
| --- | --- | --- |
| Native authority and compatibility regressions | pass, pass | **fail**, pass |
| ARM Mac stock Deploy living sidearm | fail, fail ("OS screenshot does not bind the exact successful owned window") | fail, fail ("Original OS screenshot did not confirm menu screen" ×6, then "Deploy requires unique native corroboration and one exact derived caption at confidence .8") |
| iOS unsigned generic-device compile and link (Xcode 26.3, iPhoneOS SDK 26.2) | pass, pass | pass, pass |
| Runs | [40655614500](https://github.com/calebaiken/sightbreak/actions/runs/40655614500), [40657156286](https://github.com/calebaiken/sightbreak/actions/runs/40657156286) | [40655599814](https://github.com/calebaiken/sightbreak/actions/runs/40655599814), [40657152599](https://github.com/calebaiken/sightbreak/actions/runs/40657152599) |

The macOS gameplay step fails on the base too (screen recognition of the Deploy caption), so macOS gameplay is not verified either way. The strict native suite failed once in two PR runs and never in two base runs; the step's reason was not retrievable (earlier than the log window the tool returns), the same 16 suites pass in this container under the same script, and the repository's own notes record intermittent Mac `actor`/`input_mode` ObjectDB leaks. Two samples cannot tell a leak that my change made likelier from that. Recorded as open. The iOS result is for `18b285b0`; the commits after it change only `scripts/` and `game/tests/`, so the exported game is the same, but the compile was not re-run on the final head.

## Not verified

- **Windows** is verified on the hosted runner (software rendering) only: no physical GPU, no human play, no frame rate or input latency.
- **Linux** hosted steps 30, 31, 33 and 34 fail on this branch for the budget reasons above; the base fails 31 and 32. Linux gameplay is not verified by the hosted lane for this layout.
- **macOS** gameplay is not verified on either side (the Deploy step fails on the base). The macOS strict native suite failed in one of two PR runs; its cause is unknown.
- **Android**: not exported. The SDK download is blocked in this environment (`dl.google.com`, 403), so build compatibility is untouched in code but unverified. **iOS**: compile and link verified on `18b285b0` only (above); no device or simulator run.
- Any physical device, mobile frame rate or thermals. The yard costs more to draw in every quality tier.
- Human play: feel, fun, readability, balance. Every number above is bots.
- Online play beyond the handshake: no ten-client run on a network, no account or backend (PostgreSQL) checks (Docker is not usable here).
- Sound, accessibility and the 8.5-per-category visual gate.

## Reproduce

```sh
export SIGHTBREAK_TOOLS_DIR=/path/to/tools            # scripts/setup.sh --editor-only
./scripts/godot.sh --headless --editor --import --quit

# the defect, deterministically (fails on 830bf2ba, passes here)
./scripts/godot.sh --headless --script res://tests/map_sightline_probe.gd -- --assert

# bot matches, one process per match (about 80 s each); GAME_DIR selects the build under test
docs/reports/relay-yard-integration/tools/audit.sh out/after normal 1
docs/reports/relay-yard-integration/tools/audit.sh out/before normal 1 /path/to/830bf2ba/game
python3 docs/reports/relay-yard-integration/tools/compare.py out/before out/after

# the verifier's plant route, smoke and focus-test press in the real physics, with live defenders
./scripts/godot.sh --headless --audio-driver Dummy --script res://tests/layout_route_test.gd

# the numbers quoted for the smoke and the plant (scratch scripts; run from the repository root)
./scripts/godot.sh --headless --audio-driver Dummy --script "$PWD/docs/reports/relay-yard-integration/tools/smoke_landing.gd"
./scripts/godot.sh --headless --audio-driver Dummy --script "$PWD/docs/reports/relay-yard-integration/tools/plant_fixture_sim.gd" -- detour 0.25 -0.8 1.5   # route, smoke yaw offset, pitch, rest at each waypoint

# regression checks
./scripts/godot.sh --headless --script res://tests/handshake_layout_test.gd
scripts/test_handshake_hardening.sh && scripts/test_protocol_compat.sh
```

The before data used seeds 1 to 16 on `normal` and 1 to 8 on `easy` and `hard`; the after data used the same. The before data and the earliest `normal` seeds were taken with earlier revisions of `bot_match_audit.gd`; the later ones only added fields that describe a flagged bot (its input, neighbours and state). The tool observes and changes nothing, and a seed's results do not depend on those fields (checked on the after data).
