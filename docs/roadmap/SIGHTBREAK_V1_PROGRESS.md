# SIGHTBREAK v1.0 progress

Last updated: 2026-10-21 (Claude, session `01K8r1xMjGNZtUR5CdGpJK3x`). Mission and gates: [SIGHTBREAK_V1_MISSION.md](SIGHTBREAK_V1_MISSION.md). Resume point: [../engineering/NEXT_SESSION.md](../engineering/NEXT_SESSION.md). Log: [../engineering/AUTONOMOUS_WORKLOG.md](../engineering/AUTONOMOUS_WORKLOG.md).

Statuses: `NOT STARTED`, `IN PROGRESS`, `FAILED`, `VERIFIED`, `BLOCKED EXTERNALLY`. **Verified by** says who ran it. "Reported" means a source document says so and nobody on this line has re-run it. Reported results are not promoted to `VERIFIED` until someone re-runs them.

## Acceptance matrix

| ID | Gate | Status | Evidence on record | Verified by | Next action |
| --- | --- | --- | --- | --- | --- |
| G1 | Offline 5v5 match runs start to finish (objectives, combat, economy, results, progression) | IN PROGRESS | Scripted native matches finish on Linux (6:6, 7:5) and Windows (6:6, 7:0) with earned XP/Credits reloaded after restart ([playability report](../reports/DESKTOP_PLAYABILITY_REPORT.md)). Several CI scenarios still fail: Linux plant approach and offline round observation, Windows offline OCR and reload timing. | Reported by Codex CI | Re-run the suite natively here (M1). No human has played a full match. |
| G2 | Bots: reliable navigation, objectives, cooperation, difficulty | IN PROGRESS (F1: no plants in a 12-round match) | PR #14 frozen at `d66e72c` is inside the base. Independent review: "AI / objectives / difficulty: FAIL acceptance" ([three-agent report](../reports/THREE_AGENT_INTEGRATION_REPORT.md)). Tip of the Gemini branch (`48eb058`) is newer and not integrated. | Reported | Review the newer tip with `integration-reviewer`, then measure full matches. |
| G3 | Ten-client authoritative match: reliability, privacy, identity, integrity, impairment | IN PROGRESS | 12/12 ten-client loopback conditions pass at frozen `4316c58`; resume soaks pass. PRs #18-#21 (recovery, trade reads, input freshness, ACK diagnostics) not integrated. No ten-human run. | Reported by Codex | Codex-owned. Claude reviews #18-#21 when asked. |
| G4 | Gunplay: recoil, spread, fire cadence, hit and elimination feedback | IN PROGRESS | Rules are tested (`actor_test`, `hit_feedback_test`, `weapon_integrity_test`). No measurement of feel, no human assessment, no comparison to a shipped title. | Reported | Build a measurement harness for all four weapons (milestone candidate). |
| G5 | Viewmodel, reload and weapon switch animation | FAILED | Relay AR has authored art. Same-family review scored the weapon and hands slice 5.5/10 against 8.5. Kestrel 9, Vectorline and Longwatch are still procedural. | Reported (same-model reviewer, stills) | Native recapture, critic round, author the other three weapons. |
| G6 | Input responsiveness (mouse, movement, fire) measured | NOT STARTED | Movement prediction error is tested (max 0.0758 m). There is no input-to-photon or input-to-fire measurement. | none | Define a measurable proxy under llvmpipe; label it relative. |
| G7 | UI/UX across journeys (menu, deploy, LAN, settings, HUD, buy, scoreboard, pause, inventory, cases, results, error states) | IN PROGRESS | Native UI landed (PR #12) with state, layout and overflow suites. Independent review left four findings open on `2b2731a`; whether the base fixed them is unchecked. | Reported | Capture every journey at 1280x720, 1920x1080, 960x720, 1560x720; critic round. |
| G8 | Visual quality at least 8.5/10 in each applicable category | FAILED | 0.3 aggregate 8.1 (geometry, materials, lighting, models, effects below 8.5). Fresh sequence review about 5.5. | Reported (AI reviewers, not human) | Per-category rounds after G4-G7. |
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

## Native baseline by Claude (M1)

Filled in as runs complete. Commit under test: `db3981e` (`codex/desktop-playability-p1`). Environment: Godot 4.7.2 official, Xvfb 1920x1080x24, Mesa llvmpipe, 4 vCPU.

| Item | Result |
| --- | --- |
| Asset import (`--import`) | Completed, exit 0 |
| `scripts/validate.sh` | Ran to completion on `db3981e`, no failing step, no leak warnings (worklog has the table). Skipped: backend-Python fixture drift check, Windows-only tests. |
| Bot match objective play | **Finding F1**: 12-round real-engine bot match, `plant_observed=false`, all rounds ended by elimination in 26-43 s. Under investigation. |

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
| `claude/mission-foundation-v1` (this work) | see worklog | M0 on top of PR #23. |

## Known blockers and limits

- Reference footage hosts are denied; CS2 parity cannot be measured here (G18).
- No GPU, no audio device, no humans, no Mac or Windows host in this container.
- Parallel contributors: Codex has PRs #18-#23 in flight. Avoid their files unless you coordinate (`PARALLEL_WORK.md`).
