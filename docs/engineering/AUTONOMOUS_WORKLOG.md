# Autonomous worklog

Chronological record of what Claude did on the SIGHTBREAK v1.0 mission: investigations, decisions, failed experiments, tests, reviews and source revisions. Newest entry last. Results in the acceptance matrix ([SIGHTBREAK_V1_PROGRESS.md](../roadmap/SIGHTBREAK_V1_PROGRESS.md)) must trace back to an entry here.

## 2026-10-21 - Session 1: orientation and M0

**Environment.** Claude Code cloud container, Linux x86_64, 4 vCPU, 15 GB RAM, no GPU, no audio device. Present: Xvfb, ffmpeg, Python 3, Node 22. Installed this session: pinned Godot 4.7.2 and export templates through `scripts/setup.sh` (SHA-512 verified by the script) into `/home/user/tools/godot-4.7.2`, state in `/home/user/sightbreak/.local`.

**Repository state found.** Local clone had only `main` (`4d8cdb3`). `git fetch` of the stacked branches and `git merge-base --is-ancestor` checks gave the map in the progress file. The newest integrated line is PR #23 `codex/desktop-playability-p1` (`db3981e`, 216 commits over `e67f2c8`), which contains PRs #1, #2 (through `ed85754`), #12, #14 (frozen `d66e72c`), #16 and #22. It does not contain PR #17, PRs #18-#21, the nine newest commits of PR #2 (including `scripts/ab_pair.py`) or the newer tip of PR #14.

**Decision: base.** Work stacks on `codex/desktop-playability-p1`, matching the repo convention that each draft PR targets its dependency. Branch `claude/mission-foundation-v1`, worktree `/home/user/wt/mission-foundation`. The upstream was unset after creation so a bare `git push` cannot reach Codex's branch.

**Skills.** Cloned `robonuggets/gauntlet-loop` (`9b1975a`, CC BY 4.0) and `petergyang/no-ai-slop` (`000650b`, MIT). Read both in full: markdown only, no scripts, installers or network calls. Copied the skill files and licenses unchanged into `.claude/skills/` with `PROVENANCE.md` carrying commit, license and SHA-256. Upstream `gauntlet-loop` only writes a prompt, so `.claude/skills/sightbreak-gauntlet` was added to run the loop with real captures, blind pairs and a fresh-context critic.

**Claude Code capabilities checked.** `/loop` exists as a skill in this environment. No `/goal` or `ultracode` command was found in the skill list, so neither is used or assumed. Subagents work through the `Agent` tool; project agents in `.claude/agents/` load in future sessions. `SessionStart` hook added with a read-only brief script.

**Reference footage.** Fetch attempts to `store.steampowered.com`, `cdn.akamai.steamstatic.com`, `shared.akamai.steamstatic.com`, `cdn.cloudflare.steamstatic.com`, `steamcdn-a.akamaihd.net`, `www.youtube.com`, `i.ytimg.com`, `upload.wikimedia.org`, `counter-strike.net` and `partner.steamgames.com` all failed with a 403 on the proxy `CONNECT`. `raw.githubusercontent.com` works. Earlier Claude and Codex sessions recorded the same wall. Consequence: G18 is `BLOCKED EXTERNALLY` and no CS2 comparison is claimed anywhere. Bars B3 (previous build), B4 (WCAG contrast) and B5 (relative timing) stay usable.

**Gun data read.** `game/scripts/gameplay/weapons.gd` defines four weapons (interval in s, so Kestrel 9 semi 0.23, Vectorline 0.085 auto, Relay AR 0.105 auto, Longwatch 0.82 semi). `actor.gd:728-758`: spread is uniform random per axis around the aim; recoil climbs pitch by `spec.recoil` per shot up to 0.16 rad, adds a deterministic horizontal term `sin(shot_index * 1.7) * recoil * 0.55`, and recovers at 0.11 rad/s. Only the Relay AR has authored meshes and rigged arms; the other three are procedural.


**Baseline run (M1), commit `db3981e`.** `DISPLAY=:99 ./scripts/validate.sh` on the unmodified base, Godot 4.7.2 official, Xvfb 1920x1080x24, Mesa llvmpipe. It ran to its final line ("Validation completed") with no failing step, about 12 minutes of wall clock (23:55 to 00:07 UTC). Because the script runs under `set -e`, a failing suite would have stopped it earlier. Selected results from the 59 per-suite logs:

| Suite | Result |
| --- | --- |
| actor / world / hit-feedback / weapon-integrity / hit-volume / hit-history | 73 / 25 / 10 / 28 / 40 / 638 checks, 0 failures |
| match | 75/75 |
| state-privacy, snapshot-buffer, input-stream, movement-replay, input-lifecycle, peer-lifecycle, result-outbox | all 0 failures; movement replay max error 0.0758 m |
| reconnect (policy, independent, admission, alias, auth-loss, lost-welcome) | all pass |
| landscape-ui / hud-overflow / ux-contract / touch / main | 9217 / 2437 / 2227 / 34 / 42 checks, 0 failures |
| armory-ui / armory-state / economy-ui / economy-recovery | pass (746 / 2936 checks) |
| weapon-art / reload-sequence / reload-audio (+3 captures) / reload-contact | 179 / 92 / 29 / 24 checks, 0 failures |
| reload-visibility, reload-finish (sun, shade, skin), viewmodel-light | rendered probes pass |
| bot-ai-regression | `BOT_AI_REGRESSION_TESTS_OK` |
| bot-lifecycle (normal, seed 1847, real engine) | passed=true, 12 rounds, 6:6, 78 kills, **plant_observed=false** |

Not run: the catalog-fixture drift check (it needs the backend Python environment, absent here) and the Windows-only observation tests (skipped by the suite). The only `WARNING` lines are the Xvfb V-Sync one. No ObjectDB leak lines in any log.

**Finding F1 (bots never plant).** In the lifecycle test, 12 rounds took 26-43 simulated seconds each against a 100-second round timer, and the attackers never reached the `planted` state. Every round ended by elimination. The test still reports `passed=true` because it checks completion, halftime and a single report, not objective play. An older baseline recorded in `docs/ai/BOT_BEHAVIOR_QA.md` showed `plant_observed=true` on the main-line code (`148760e`). This has to be measured over many seeds and difficulties before a cause is claimed.

## 2026-10-22 - Session 1, M2: Relay Yard tactical layout

Branch `claude/relay-yard-tactical-layout-v1`, stacked on `claude/mission-foundation-v1`. Design, tables and limits: [RELAY_YARD_LAYOUT.md](../design/RELAY_YARD_LAYOUT.md). Evidence: [docs/reports/gauntlet/relay-yard-layout](../reports/gauntlet/relay-yard-layout/README.md).

**Why this piece.** The M1 baseline passed every maintained suite, but its bot match finished 12 rounds without a single plant. I wrote `tests/bot_objective_metrics.gd` (observation only) and ran complete all-bot matches on the real engine. On `db3981e`: median live round 12 s, first kill at 1.6 s, 94% of first kills inside a spawn zone at about 30 m, plants in 9% of rounds. A top-down render and a dump of the arena's obstacles (25 volumes, 15 of them cover, no elevation) showed the cause: a 48 m open pad. A sightline probe confirmed 95.7% of the yard is visible from defender hold positions and the attacker spawn is covered from 28 m. Picked over the weapon and viewmodel work because it breaks the core loop and is measurable headless without the blocked CS2 references.

**Built.** 13 container solids (screen wall with two exits, exit blocks, lane dividers, site shields, spine extensions), a 2 m navigation grid, unique stencils and hardware on the new containers, labels sized to their plates, floor stencils moved into the exits, deeper defender anchors. New tools: `map_sightline_probe.gd` (exposure map, route length and exposure), `map_overview_capture.gd`, `map_viewpoints_capture.gd`, `presentation_gallery_capture.gd` (all four weapons and operators; written, not yet run), `scripts/measure_relay_yard.sh`, `scripts/summarize_bot_metrics.py`, and `scripts/ab_pair.py` (blind pairs) cherry-picked from the PR #2 branch.

**Gauntlet.** Four builder/critic rounds with fresh critics and blind pairs against bar B3 (previous build). New layout won the overview each time and 7, 11, 9, 9 of 12 eye-level pairs. Findings that changed the build: blank unlabelled walls, inverted colour code, overprinted floor stencils, label overflow, a camera inside a container in my own capture script. An independent data reviewer recomputed the bot numbers and found two things I had not: the attacker win rate is confounded (F2 below) and the hard-difficulty plant "improvement" on seeds 31-36 was one round.

**Failures worth keeping.**
- Opening the mid exit looked right in renders. With a 6 m exit and a baffle, the two side passes were 1 m wide and the navigation graph had no node inside them: bots never used mid, a 45 m detour for a 16 m trip. I only found it because a critic called the exit a jam point. Widening it and adding nodes made every bot take it (shortest route), into a lane covered from the defender end: plants fell from 75% to 6%. Assigning bots to exits by slot did not help. Closed the mid exit; mid is a hub reached from the side lanes.
- A second mid baffle on x = 0 broke fixtures in `weapon_integrity_test` (7 failures), `actor_test` and `smoke_presentation_test`. Dropped rather than moving other people's fixtures.
- A cap of two defenders per sound had no demonstrable effect. Removed.
- The sunlit capture pose (3, -12) failed the finish-stability probe (receiver chroma shift 0.070 against 0.06) while the second baffle's shadow covered it. After the baffle was dropped the original pose passes (0.015). I had moved thirteen files' poses first; reverted.
- A test with a script compile error does not fail fast under `--headless --script`: it hangs. Every run in this session used a timeout.

**Finding F2 (open).** Under the stock tick order actors 1-5 win 71% of rounds on normal (62% hard) in both the old and the new layout, whichever side they play. With the processing order reversed they win 46% (87 rounds). The authoritative tick processes actors in id order, so lower ids win same-tick trades. Needs its own PR in `match.gd` with a regression test (rotate or shuffle the order per tick). Until then side balance cannot be read from bot matches.

**Measured, final build** (seeds 41-46, both start orders, 12 matches per cell; before is `db3981e`). Normal: median round 12.0 s -> 23.5 s, first kill 1.6 s -> 6.2 s, plant 9% -> 75%, kill distance 29.8 m -> 14.4 m, first kills in a spawn zone 94% -> 0%. Hard: first kill 0.4 s -> 6.1 s, plant 2% -> 15%, clock-outs 18% -> 0%, spawn-zone first kills 100% -> 0%, median round 15.4 s -> 13.4 s (mean 32.9 s -> 16.0 s). Geometry: route to site 36.7-39.2 m -> 47.8-55.8 m, route exposed 97-100% -> 28-41%, longest exposed stretch 30-38 m -> 14-18 m, yard visible from defender holds 95.7% -> 64.3%, spawn covered by 1-3 holds -> 0.

**Regression.** `DISPLAY=:99 ./scripts/validate.sh` on the final tree: ran to completion, exit 0, no ObjectDB leak lines. World stats `box_instances` 1,472 -> 2,544, shadow casters 793 -> 1,397, static batches 9 -> 9. The maintained bot lifecycle test now observes a plant (`plant_observed=true`; it was `false` on the base). The layout-rules step (`map_sightline_probe.gd --assert`, 35 checks) was added to `validate.sh` after that run: it passes on its own and, as a negative control, fails on the old map with spawn lines, 37 m routes and 97% to 100% exposure. Test changes: `world_test` and `actor_test` count the 13 declared layout solids on top of the original 25. No threshold relaxed, no fixture moved.

**Not done / unverified.** No human played it. `scripts/verify_offline_match.py` follows a new plant route (checked against the bots' obstacle map; not run natively). Mixed-layout networking: the handshake cannot tell layouts apart. Sites remain bare. Hard bots still rarely plant. `presentation_gallery_capture.gd` has not been run.
