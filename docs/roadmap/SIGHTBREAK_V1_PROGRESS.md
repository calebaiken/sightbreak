# SIGHTBREAK v1.0 progress

Last updated: 2026-10-21 (Claude, session `01K8r1xMjGNZtUR5CdGpJK3x`). Mission and gates: [SIGHTBREAK_V1_MISSION.md](SIGHTBREAK_V1_MISSION.md). Resume point: [../engineering/NEXT_SESSION.md](../engineering/NEXT_SESSION.md). Log: [../engineering/AUTONOMOUS_WORKLOG.md](../engineering/AUTONOMOUS_WORKLOG.md).

Statuses: `NOT STARTED`, `IN PROGRESS`, `FAILED`, `VERIFIED`, `BLOCKED EXTERNALLY`. **Verified by** says who ran it. "Reported" means a source document says so and nobody on this line has re-run it. Reported results are not promoted to `VERIFIED` until someone re-runs them.

## Acceptance matrix

| ID | Gate | Status | Evidence on record | Verified by | Next action |
| --- | --- | --- | --- | --- | --- |
| G1 | Offline 5v5 match runs start to finish (objectives, combat, economy, results, progression) | IN PROGRESS | Scripted native matches finish on Linux (6:6, 7:5) and Windows (6:6, 7:0) with earned XP/Credits reloaded after restart ([playability report](../reports/DESKTOP_PLAYABILITY_REPORT.md)). Several CI scenarios still fail: Linux plant approach and offline round observation, Windows offline OCR and reload timing. | Reported by Codex CI | Re-run the suite natively here (M1). No human has played a full match. |
| G2 | Bots: reliable navigation, objectives, cooperation, difficulty | IN PROGRESS | PR #14 frozen at `d66e72c` is inside the base. Independent review: "AI / objectives / difficulty: FAIL acceptance" ([three-agent report](../reports/THREE_AGENT_INTEGRATION_REPORT.md)). Tip of the Gemini branch (`48eb058`) is newer and not integrated. Claude measured all-bot matches (M2): on the old map attackers planted in 9% of normal rounds and first kills landed at spawn; on layout revision 2 plants reach 75% (normal) and 15% (hard). Hard bots still rarely plant. | Claude native, bots only | Hard-difficulty staging and utility; review the newer Gemini tip first. |
| G3 | Ten-client authoritative match: reliability, privacy, identity, integrity, impairment | IN PROGRESS | 12/12 ten-client loopback conditions pass at frozen `4316c58`; resume soaks pass. PRs #18-#21 (recovery, trade reads, input freshness, ACK diagnostics) not integrated. No ten-human run. | Reported by Codex | Codex-owned. Claude reviews #18-#21 when asked. |
| G4 | Gunplay: recoil, spread, fire cadence, hit and elimination feedback | IN PROGRESS | Rules are tested (`actor_test`, `hit_feedback_test`, `weapon_integrity_test`). Measured on the v1 stack in the real authority code (draft PR #33): the rifle beats the other three weapons in 900 of 900 chest-aim duels per pair at 8, 20 and 40 m; the marksman needs two body hits at every distance; the rifle collapses when walking at 30 m and beyond unless recoil is countered; the sidearm steps at 7.41, 25.93 and 38.27 m. Three seeds, byte-identical per seed, fifteen fresh-context reviews. Fixture only: no feel, no human assessment, no comparison to a shipped title. | Reported (same model family) | Design owner to read the four observations in the PR #33 README. Human feel testing is G17. |
| G5 | Viewmodel, reload and weapon switch animation | FAILED | Relay AR has authored art. Same-family review scored the weapon and hands slice 5.5/10 against 8.5. Kestrel 9, Vectorline and Longwatch are still procedural. | Reported (same-model reviewer, stills) | Native recapture, critic round, author the other three weapons. |
| G6 | Input responsiveness (mouse, movement, fire) measured | NOT STARTED | Movement prediction error is tested (max 0.0758 m). There is no input-to-photon or input-to-fire measurement. | none | Define a measurable proxy under llvmpipe; label it relative. |
| G7 | UI/UX across journeys (menu, deploy, LAN, settings, HUD, buy, scoreboard, pause, inventory, cases, results, error states) | IN PROGRESS | Native UI landed (PR #12) with state, layout and overflow suites. Independent review left four findings open on `2b2731a`; whether the base fixed them is unchecked. | Reported | Capture every journey at 1280x720, 1920x1080, 960x720, 1560x720; critic round. |
| G8 | Visual quality at least 8.5/10 in each applicable category | FAILED | 0.3 aggregate 8.1 (geometry, materials, lighting, models, effects below 8.5). Fresh sequence review about 5.5. Session 2 graphics work: an independent critic scored twelve native yard stills (old MEDIUM) lighting 4, grounding 4, materials 3, edges 5, depth 2, colour 4, finish 3. Draft PR #35: four tested graphics tiers and a shadow fill (pixels below luminance 40: 14.8% to 0.3%; blind critic chose it in 11 of 12 pairs); HIGH stops sunlit clipping (0.62% to 0.10%). Draft PR #36: surface-aware impacts and bullet holes (blind critic 14 of 16 pairs, 2 ties, +1 draw call). Open: far wall reads as a slab, no skyline, materials flat, sun disc, crane cable, signage, three procedural weapons, operators. | Reported (AI reviewers on software-rendered stills, not human, not GPU) | Environment readability pass (skyline, sun glow, crate-top albedo, crane cable), then material wear, then weapon art (G5). Ranked list: `docs/art/GRAPHICS_BACKLOG.md` on PR #35. |
| G9 | Audio: fire, reload, hit, objective cues consistent with animation | IN PROGRESS | All sound is synthesized in code. Capture-based tests pass; exit-time AudioStream leaks and one nondeterministic timing control were reported. Nobody has listened. | Reported | Check leaks in baseline; add timing measurements. A listening review needs a person. |
| G10 | Accessibility (contrast, text scale, reduced motion, controller/keyboard reach) | IN PROGRESS | Text scale and reduced motion exist. No audit, no screen-reader or physical-controller evidence. | none | Compute WCAG contrast from captures (bar B4). |
| G11 | Linux native package | IN PROGRESS | Exports and extracted-content inspection pass; Linux CI job FAILS on offline round observation, plant approach, layout. | Reported | Re-run export here. |
| G12 | Windows native package | IN PROGRESS | Full match and earned restart pass; offline OCR and controlled reload timing fail in CI. | Reported | Windows is not available here; track Codex CI. |
| G13 | macOS native package (Intel and Apple Silicon) | FAILED | ARM menu and controls pass, gameplay unverified. Intel game startup times out at 120 s in every trial. | Reported | Codex-owned diagnosis. Needs Mac hardware. |
| G14 | Android and iOS keep building | IN PROGRESS | Debug APK exports and unsigned Xcode project inspected structurally. No device, no Xcode build. | Reported | Re-export Android here when M-infra allows. Physical gates are `BLOCKED EXTERNALLY`. |
| G15 | Packaging, build provenance, Steam staging procedure | IN PROGRESS | Source-bound manifests exist. `STEAM_RELEASE_READINESS.md` is design only: no SteamPipe template, no App ID, Steamworks docs not retrievable (host denied). | Reported | Owner approval is needed for any upload or account step. |
| G16 | Economy and progression integrity | IN PROGRESS | PostgreSQL suites and HTTP economy checks pass in frozen runs. Production deployment review not done. | Reported | Codex-owned. |
| G17 | Human playtesting | BLOCKED EXTERNALLY | No human feedback exists. | none | Needs people. Use `docs/research/HUMAN_AND_DEVICE_TESTING_PLAN.md`. |
| G18 | Counter-Strike 2 comparison for weapon feel, animation, readability | BLOCKED EXTERNALLY | Steam, YouTube and counter-strike.net hosts denied by the network policy (see [BARS.md](BARS.md)). | none | Owner allows the hosts, or supplies reference captures. |
| G19 | Physical-device performance (frame pacing, thermals, memory) | BLOCKED EXTERNALLY | Only llvmpipe software-render timings exist. | none | Needs hardware. |
| G20 | Skills, agents, memory and session brief for the mission | IN PROGRESS | This branch adds them (M0). | Claude | Merge path: draft PR into `codex/desktop-playability-p1`. |
| G21 | Relay Yard tactical layout: spawn protection, routes, cover, round pacing | IN PROGRESS | Revision 2 (branch `claude/relay-yard-tactical-layout-v1`): 0 sightlines to the attacker spawn (was 1-3), route exposure 28-41% (was 97-100%), first kills out of spawn zones 94% -> 0%, normal plants 9% -> 75%, four blind critic rounds won (5.5 to 6 out of 10), full suite exit 0. [Design](../design/RELAY_YARD_LAYOUT.md), [evidence](../reports/gauntlet/relay-yard-layout/README.md). | Claude native (bots, stills); data independently recomputed | Sites need a plant pocket, a second entry and post-plant cover. No long lane, no elevation. Human playtest. Codex to confirm the native plant scenario route and the mixed-layout handshake. |
| G22 | Authoritative tick fairness: no actor id wins same-tick trades | IN PROGRESS | Finding F2 (ids 1-5 won 71% of normal rounds on the old tick) was first fixed by a shuffle (draft PR #28), now superseded by the two-phase tick on `codex/v1-mission-playability`. Independent qualification of that stack (draft PR #34): over 120 bot matches (normal and hard, both starts) ids 1-5 won 651 of 1284 rounds, 50.7% (95% interval 47.8 to 53.6, bootstrapped by match), against 66.2% (59.5 to 73.5) over 24 matches before; before minus after +15.5 points (+8.1 to +23.2). An independent re-parse of the raw logs reproduced every count; three squad-attribution methods agree in all 152 logs. Equivalence within 5 points holds; within 3 does not. The squad attacking first wins 47.0% of rounds (attackers win only 25.5% of bot rounds), a side effect that the paired start cancels. | Claude native, bots only; independent re-parse by a fresh-context subagent (same model family) | Not `VERIFIED` until merged and validated on the integrated stack. No multi-client run here; Codex owns the ten-client campaign (G3). Re-measure after any change to the tick, bot habits or layout. |

## Native baseline by Claude (M1)

Filled in as runs complete. Commit under test: `db3981e` (`codex/desktop-playability-p1`). Environment: Godot 4.7.2 official, Xvfb 1920x1080x24, Mesa llvmpipe, 4 vCPU.

| Item | Result |
| --- | --- |
| Asset import (`--import`) | Completed, exit 0 |
| `scripts/validate.sh` | Ran to completion on `db3981e`, no failing step, no leak warnings (worklog has the table). Skipped: backend-Python fixture drift check, Windows-only tests. |
| Bot match objective play | **Finding F1** (explained): 12-round real-engine bot match, `plant_observed=false`, rounds of 26-43 s. Cause: the 48 m open pad (see G21). On layout revision 2 the same maintained test observes a plant. |

## Branch and PR map (verified 2026-10-21 with `git fetch` and ancestry checks)

`main` is `4d8cdb3`. No PR has merged. Every other line stacks on `e67f2c8`.

| Line | Head | Contains |
| --- | --- | --- |
| PR #16 `integration/sightbreak-three-agent-alpha` (base `integration/sightbreak-reliability-refresh`) | `d2439ac` | Claude audit (PR #1) and native UI (PR #12), Claude art through `ed85754`, Gemini bots frozen at `d66e72c`, Codex network stack (PRs #3-#11), market price guard (PR #15). |
| PR #22 `codex/desktop-steam-readiness` (base PR #16) | `82a03fc` | Native Windows/macOS exports, packaging checks, Steam readiness design. |
| PR #23 `codex/desktop-playability-p1` (base PR #22) | `db3981e` | Input modes, focus recovery, objective hints, native full-match validation. **Base for Claude work.** |
| PR #17 `integration/sightbreak-v3-validation` (base PR #16) | `320e0ef` | PR #16 plus five commits. Not an ancestor of PR #23. "No verified V3 candidate." |
| PRs #18-#21 `astra/*` (base PR #16) | various | Receipt recovery, trade reads, input freshness, ACK diagnostics. Not integrated. |
| PR #2 `claude/cs2-fidelity-art-production` | `bb5212d` | Nine commits not in PR #23, including `scripts/ab_pair.py` (blind A/B pairs). |
| PR #14 `gemini/tactical-bot-intelligence-v1` | `48eb058` | Newer than the frozen copy inside PR #16. |
| `claude/reconcile-v10-on-pr16` (no PR) | `79a9591` | PR #16 plus the PR #2 tip. Superseded by PR #23 for everything except the nine art commits. |
| `claude/wip-gauntlet-T1-sunmetal`, `...T2-lowlight` | `0cb8239`, `43854ff` | Earlier Claude work-in-progress on metal and low-light viewmodel lighting. |
| `claude/mission-foundation-v1` (draft PR #24) | `c84eaf3` and later | M0 on top of PR #23. |
| `claude/relay-yard-tactical-layout-v1` | see worklog | M2 on top of `claude/mission-foundation-v1`. |

## Known blockers and limits

- Reference footage hosts are denied; CS2 parity cannot be measured here (G18).
- No GPU, no audio device, no humans, no Mac or Windows host in this container.
- Parallel contributors: Codex has PRs #18-#23 in flight. Avoid their files unless you coordinate (`PARALLEL_WORK.md`).
