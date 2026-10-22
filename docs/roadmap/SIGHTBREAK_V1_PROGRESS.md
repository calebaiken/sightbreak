# SIGHTBREAK v1.0 progress

Last updated: 2026-10-22 (Codex mission activation). Permanent tracker: [issue #25](https://github.com/calebaiken/sightbreak/issues/25), IN PROGRESS / PRIMARY. Existing Claude baseline and worklog remain historical evidence. Mission and gates: [SIGHTBREAK_V1_MISSION.md](SIGHTBREAK_V1_MISSION.md). Resume point: [../engineering/NEXT_SESSION.md](../engineering/NEXT_SESSION.md). Log: [../engineering/AUTONOMOUS_WORKLOG.md](../engineering/AUTONOMOUS_WORKLOG.md).

Statuses: `NOT STARTED`, `IN PROGRESS`, `FAILED`, `VERIFIED`, `BLOCKED EXTERNALLY`. **Verified by** says who ran it. "Reported" means a source document says so and nobody on this line has re-run it. Reported results are not promoted to `VERIFIED` until someone re-runs them.

## Current execution

- Active branch: `codex/v1-mission-playability`, worktree `/workspace/sightbreak-v1-execution`, [draft PR #27](https://github.com/calebaiken/sightbreak/pull/27) targeting PR24. Persistent goal: issue #25, IN PROGRESS / PRIMARY.
- Base: PR24 `c84eaf3ce89105d071254f0654f9adbe50275e9e`, stacked on PR23 `db3981e` → PR22 `82a03fc` → PR16 `d2439ac`. No shared branch was merged or rewritten. Mission initialization committed as `561d0cb`.
- M0 initialization verified: original skill hashes match, no reinstall; issue #25 registered. No native Codex goal API is exposed; Linear requires reauthentication.
- M1 implemented: FIELD MENU initial keyboard focus, native objective approach control, and X11 window-lifetime handling. Fresh independent critics reviewed actual native outputs. Exported Linux plant and defuse pass the original hold/movement budgets. Four-size native generation now passes under original 520/120 second limits, after a critic found and the builder corrected a 1280×800 pixel counterexample. Live classification remains 1280-only; all sizes have independent actual-image checks. [Menu evidence](../reports/gauntlet/m1-menu-focus/INDEPENDENT_ARCHIVE.md), [approach baseline/criteria](../reports/gauntlet/m1-native-approach/README.md), [X11 criteria](../reports/gauntlet/m1-native-window/REPORT.md).
- M3 increment implemented: consumed input replays no longer refresh authority/idle clocks. Blind output critic selected the candidate; native two-peer cases pass 8/8 versus baseline 4/8. Eight snapshot-gap trials stop in 316–334 ms within the unchanged 350 ms gate. Same-host timing has a 16 ms minimum observed margin; this does not qualify ten clients. [Evidence and separate reviews](../reports/gauntlet/m3-input-freshness/RESULTS.md).
- Frozen integrated source: `6a0d8d5d85b4fb37943903886982f51b4ed230b0`, game tree `13079ab8a3de9b18252a652ed57157e0776cf394`. `validate.sh` completed exit 0 (16,355 reported checks); catalog drift checked separately and matches. Rendered reload visibility, Windows-only observer cases and backend SQL were not covered by that aggregate. Bot lifecycle again reports no plant in its 12-round match (F1).
- Previous desktop CI [39712752860](https://github.com/calebaiken/sightbreak/actions/runs/39712752860), exact source `6a0d8d5`: Windows/Linux plant, defuse, complete stock match and earned restart steps pass. Windows raw-match review is complete; Linux raw review is blocked by transfer limits. Jobs are NOT green: authority suites share test save data; the ordinary offline journey fails. Intel Mac startup still times out; ARM startup/controls pass but gameplay is unqualified. Historical failures are retained, not erased by individual passes.
- M2 source-suite isolation now passes nine actual Linux suites with independent save-safety review. Critic found a cleanup receipt false-pass; follow-up `9290154` resolves it under independent injected-failure reruns. Windows, Linux and ARM Mac source suites pass in combined CI; ARM raw review verifies all 1,281 checks. An inner HUD fixture marker remains and is being repaired. The integrated 10-suite source run, including the new combat oracle, passes locally. A separately reviewed bounded QA receipts artifact addresses the Linux transfer limit.
- Intel render attribution is implemented and independently accepted as diagnostics only (`44b9ac0`). Standalone manual dispatch returned HTTP404 because the new workflow is unregistered; `3bfc29b` invokes it through the existing Intel desktop job after unchanged startup gates. No Mac product fix is claimed; combined Intel default and explicit OpenGL startup still fail, with feature attribution pending.
- Actual Windows stock-match/progression review is [retained](../reports/gauntlet/m1-native-ci-39712752860/README.md): seven rounds, 120 XP/250 offline credits, exact restarted profile. Local objective/full failed-layout/broad-suite archive is [retained](../reports/gauntlet/m1-exported-validation/RESULTS.md).
- M1 observer corrections are implemented and independently accepted: actual Windows ammo pixels and strict native Linux focus recovery pass. Full local journey still fails its unchanged 35second second-round wait; combined Linux CI journey passes; Windows still fails and needs raw diagnosis.
- M3 actor-order correction is implemented and independently accepted: movement precedes all action traces, then queued contacts commit. Oracle 178/178 passes versus 152 intentional baseline failures; full maintained suite on product 470fad5 passes. Revised active CPU samples verify real shots/damage and bounded pools. Simultaneous attribution/wipe policy and full G3 remain open.
- M2 mobile: fresh Android and unsigned iOS source 6a exports/inspection complete. Independent 48/49 checks, with an open upstream iOS simulator architecture metadata mismatch. The actual ARM Mac attempt fails at link under SDK 18.5; a compatible installed SDK correction is in progress. No compiler/device pass.
- Next increments executing: final combined native CI, actual Intel feature attribution and unsigned iOS device compilation. Fresh [PR26](https://github.com/calebaiken/sightbreak/pull/26) is a separate Claude-owned map candidate at `5288a69`; it is not integrated. Its F2 order-bias finding has been independently reproduced and corrected on this branch. The mission and complete G1–G19 gates remain open.

### Combined qualification at 0ca125d and SDK retry (04:19 UTC)

[Run 39719407304](https://github.com/calebaiken/sightbreak/actions/runs/39719407304)
is active. All four native source-suite steps pass; ARM raw review verifies
1,281 checks. Windows/Linux plant and defuse pass. Linux ordinary journey passes;
Windows fails from a real player death before living HUD analysis. A reviewed scheduler/context correction is integrated for exact native retry. Independent
Windows raw review verifies 10 stock rounds, local victory, 120 XP / 325 offline
credits and exact restarted profile; scripted player contributions remain zero.
Intel default/OpenGL and all five feature cases time out. No shipping graphics change is supported; actual Intel GPU/device qualification stays open.

ARM iOS compilation at 0ca fails on five iOS 26 framework globals under SDK 18.5.
Independently reviewed process-local SDK correction is integrated as 6b7e97f.
ARM-only [retry 39721286005](https://github.com/calebaiken/sightbreak/actions/runs/39721286005),
frozen 2a2b732, passes independent unsigned-device compile review. Native source/PCK and Mach-O
receipts agree; raw linker/codesign confirm success and no signature. The 102 MB
app executable was not transferred for separate reparse. Installation, runtime,
simulator, older devices and whole native gameplay remain open.

Independent combined networking review is [retained](../reports/gauntlet/m3-network-qualification/independent-critic/REVIEW.md):
80 soak recoveries, 12/12 campaign conditions, protocol 8/8, hostile probes 8/8.
Original impaired 18-second lost-close trial fails (3/10); separate full-deadline
diagnostic recovers all ten within 20 s (restored server ACK bounded by 14.890 s).
It does not change the shorter result. All evidence is loopback synthetic testing.
Complete account-backed stock match plus earned durable result is now being built.

## Acceptance matrix

| ID | Gate | Status | Evidence on record | Verified by | Next action |
| --- | --- | --- | --- | --- | --- |
| G1 | Offline 5v5 match runs start to finish (objectives, combat, economy, results, progression) | IN PROGRESS | Fresh source `6a0d8d5` exported Linux player plant (124.299 s) and defuse (103.392 s) independently verified, including interrupted holds, next round and restart. New combined Windows raw match/restart independently verifies ten rounds, victory and 120 XP/325 offline credits; Linux new raw review remains pending. New combined Linux journey passes by CI metadata; Windows still fails. | Fresh native critic for objective slices and Windows raw match; Linux CI reported separately | Diagnose current Windows journey, review bounded combined receipts and qualify complete player journey. No human full match. |
| G2 | Bots: reliable navigation, objectives, cooperation, difficulty | IN PROGRESS (historical F1 and whole-match quality remain open) | PR #14 frozen at `d66e72c` is inside the base. Independent review: "AI / objectives / difficulty: FAIL acceptance" ([three-agent report](../reports/THREE_AGENT_INTEGRATION_REPORT.md)). Separate M5 squad-habit candidate adapts Claude PR28 bot delta plus two phase habits on reviewed phased authority: final actual-engine oracle 2,722 checks, 480 equal paired outputs versus 181 unequal baseline pairs; full maintained suite passes. [M5 evidence](../reports/gauntlet/m5-bot-squad-symmetry/README.md). Independent verdict remains separate; no match-balance claim. | Scoped implementation and native evidence; independent review pending | Complete independent scoped acceptance, then qualify full-match objective/cooperation quality. |
| G3 | Ten-client authoritative match: reliability, privacy, identity, integrity, impairment | IN PROGRESS | Prior ten-client evidence remains historical. New consumed-replay clock correction at `6a0d8d5`: blind native two-peer comparison 8/8 versus 4/8; eight snapshot trials stop within 350 ms, no privacy regression. [Raw evidence/critics](../reports/gauntlet/m3-input-freshness/RESULTS.md). Independent 0ca ten-client soak/campaign and full-deadline lost-close diagnostic pass, with the short failed trial retained. PR18/19/21 and complete V3 remain unqualified. | Fresh independent source and blind output critics | Complete account-backed stock match and durable earned-result qualification; preserve loopback scope and open privacy/feel requirements. |
| G4 | Gunplay: recoil, spread, fire cadence, hit and elimination feedback | IN PROGRESS | Rules are tested (`actor_test`, `hit_feedback_test`, `weapon_integrity_test`). No measurement of feel, no human assessment, no comparison to a shipped title. | Reported | Build a measurement harness for all four weapons (milestone candidate). |
| G5 | Viewmodel, reload and weapon switch animation | FAILED | Relay AR has authored art. Same-family review scored the weapon and hands slice 5.5/10 against 8.5. Kestrel 9, Vectorline and Longwatch are still procedural. | Reported (same-model reviewer, stills) | Native recapture, critic round, author the other three weapons. |
| G6 | Input responsiveness (mouse, movement, fire) measured | IN PROGRESS | Keyboard FIELD MENU focus and safe resume independently verified with OS input. Replay-silence stopping measured at 316–334 ms in eight two-peer trials. Prediction error max 0.075834 m. No physical input-to-photon or input-to-fire measurement. | Fresh native/menu and blind network critics | Keep engineering measurements scoped; obtain device latency and human feel evidence. |
| G7 | UI/UX across journeys (menu, deploy, LAN, settings, HUD, buy, scoreboard, pause, inventory, cases, results, error states) | IN PROGRESS | FIELD MENU OS keyboard/safe-resume review passes. Critic-driven footer correction now passes exact four-size native generation in 304.692s with clean exits and original limits; all 22 images and wrong-screen controls independently checked. [Evidence](../reports/gauntlet/native-layout-ocr/ITERATION_2.md). Live HUD classification runs at 1280×720 only. | Fresh menu and separate layout revision critics | Verify combined native journeys; accessibility, full UX and aesthetic quality remain open. |
| G8 | Visual quality at least 8.5/10 in each applicable category | FAILED | 0.3 aggregate 8.1 (geometry, materials, lighting, models, effects below 8.5). Fresh sequence review about 5.5. | Reported (AI reviewers, not human) | Per-category rounds after G4-G7. |
| G9 | Audio: fire, reload, hit, objective cues consistent with animation | IN PROGRESS | All sound is synthesized in code. Capture-based tests pass; exit-time AudioStream leaks and one nondeterministic timing control were reported. Nobody has listened. | Reported | Check leaks in baseline; add timing measurements. A listening review needs a person. |
| G10 | Accessibility (contrast, text scale, reduced motion, controller/keyboard reach) | IN PROGRESS | Text scale and reduced motion exist. No audit, no screen-reader or physical-controller evidence. | none | Compute WCAG contrast from captures (bar B4). |
| G11 | Linux native package | IN PROGRESS | Exact 6a export, player plant/defuse and full four-size observer candidate independently pass. Combined 10 source suites pass after combat integration. Local software-rendered journey retains its unchanged 35 s second-round timeout; combined Linux CI journey now passes; new raw match/restart review is pending. | Fresh native/layout critics; coordinator combined suites | Run and independently review final combined native CI and bounded receipts. |
| G12 | Windows native package | IN PROGRESS | Current CI `39712752860`: graphical startup, OS input, controlled reload, plant, defuse, full match and earned restart steps pass. Combined 0ca125d source suites now pass; ordinary Windows journey fails from death before HUD analysis; reviewed scheduling correction is integrated, with exact Windows retry pending. Historical reload deadline failure remains in record. | Actual CI; fresh independent Windows raw-match/objective review | Fix the settings/resume life boundary, rerun the original native Windows journey and retain all failures. |
| G13 | macOS native package (Intel and Apple Silicon) | FAILED | Current CI `39712752860`: ARM startup/controls pass, no gameplay qualification. Intel minimal 2D/3D and minimal exported 3D pass; frozen and candidate game default/explicit OpenGL still timeout at 120 s. Candidate reaches first process, no capture. Combined ARM source suite now passes all 1,281 checks; Intel feature attribution remains pending. | Actual native CI; raw diagnostic receipts inspected by Codex | Diagnose retained native sample stacks; fix isolated state; rerun unchanged startup and actual gameplay gates. |
| G14 | Android and iOS keep building | IN PROGRESS | Fresh frozen 6a Android debug APK and unsigned iOS project export and structural inspection pass. Independent 48/49 package checks: simulator metadata claims ARM64+x86_64 but pinned debug archive contains x86_64 only; device archive is ARM64. [Evidence](../reports/gauntlet/m2-mobile-preservation/independent-package-critic/REPORT.md). Actual Xcode 16.4 / SDK 18.5 link fails on five iOS 26 framework globals. Reviewed SDK selection is integrated; retry 39721286005 at 2a2b732 passes independent unsigned-device compile review, with exact source/PCK and raw unsigned codesign evidence. Final binary reparse and runtime remain open. | Fresh independent mobile package critic | Preserve accepted exact-source unsigned compile; qualify simulator metadata, installation, older OS behavior and physical play. No credential/signing action is authorized. |
| G15 | Packaging, build provenance, Steam staging procedure | IN PROGRESS | Source-bound manifests exist. `STEAM_RELEASE_READINESS.md` is design only: no SteamPipe template, no App ID, Steamworks docs not retrievable (host denied). | Reported | Owner approval is needed for any upload or account step. |
| G16 | Economy and progression integrity | IN PROGRESS | PostgreSQL suites and HTTP economy checks pass in frozen runs. Production deployment review not done. | Reported | Codex-owned. |
| G17 | Human playtesting | BLOCKED EXTERNALLY | No human feedback exists. | none | Needs people. Use `docs/research/HUMAN_AND_DEVICE_TESTING_PLAN.md`. |
| G18 | Counter-Strike 2 comparison for weapon feel, animation, readability | BLOCKED EXTERNALLY | Steam, YouTube and counter-strike.net hosts denied by the network policy (see [BARS.md](BARS.md)). | none | Owner allows the hosts, or supplies reference captures. |
| G19 | Physical-device performance (frame pacing, thermals, memory) | BLOCKED EXTERNALLY | Only llvmpipe software-render timings exist. | none | Needs hardware. |
| G20 | Skills, agents, memory and session brief for the mission | VERIFIED (initialization scope) | Existing originals verified, AGENTS.md and mission/acceptance/progress/resume records committed `561d0cb`. Continuing task registered as [issue #25](https://github.com/calebaiken/sightbreak/issues/25); actual separate builder/critic cycles and evidence retained. No native Codex goal API claimed. | Codex, repository commits and supported GitHub issue | Continue updating after each increment; this does not complete the product. |

## Native baseline by Claude (M1)

Filled in as runs complete. Commit under test: `db3981e` (`codex/desktop-playability-p1`). Environment: Godot 4.7.2 official, Xvfb 1920x1080x24, Mesa llvmpipe, 4 vCPU.

| Item | Result |
| --- | --- |
| Asset import (`--import`) | Completed, exit 0 |
| `scripts/validate.sh` | Ran to completion on `db3981e`, no failing step, no leak warnings (worklog has the table). Skipped: backend-Python fixture drift check, Windows-only tests. |
| Bot match objective play | **Finding F1**: 12-round real-engine bot match, `plant_observed=false`, all rounds ended by elimination in 26-43 s. Under investigation. |

## Branch and PR map (baseline 2026-10-21; live fetch updated 2026-10-22)

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
| PR24 `claude/mission-foundation-v1` | `c84eaf3` | Existing mission foundation, base for the Codex execution stack. |
| PR26 `claude/relay-yard-tactical-layout-v1` | `5288a69` | Separate map candidate and bot measurements; not integrated. Reports F2 actor-order bias. |
| PR27 `codex/v1-mission-playability` | see worklog / NEXT_SESSION | Active Codex mission, native input/validation, replay freshness and platform follow-ups, based on PR24. |

## Known blockers and limits

- Reference footage hosts are denied; CS2 parity cannot be measured here (G18).
- No GPU, audio device, humans or local Mac/Windows host. Actual native GitHub runners are available; their observed results and failures remain distinct from local proof.
- Parallel contributors: preserve PR18–24 dependencies and Claude-owned PR26 map work; do not integrate newer bots or map changes without independent qualification (`PARALLEL_WORK.md`).

## M3 controlled account match, 2026-10-22

G3 and G16 remain **IN PROGRESS**. Frozen test source `471fbd8` completed a real
ten-account seven-round stock match in 525.962 wall seconds, then delivered its
earned production payload after Godot/worker SIGKILL, owned PostgreSQL outage,
lost acknowledgment, restart and duplicate spool replay. Exactly one match
operation, ten rewards and ten ledger rows produced 2,875 credits / 2,650 XP.
Independent critic `93f6b68` recomputed raw outputs, queried the actual temporary
database and verified cleanup. [Evidence and limits](../reports/gauntlet/m3-account-match/RESULTS.md).

This is scripted no-combat, current-policy look activity with loopback client
traffic; it does not verify substantive participation, AFK resistance, fairness,
prediction feel, impairment, remote hosting or human play. The game listener uses
inherited wildcard UDP; API/database use loopback. Followup `0aae3f8` strengthens
only pure validation/registration and was unit-tested/raw-replayed. Product
gameplay/backend/worker files remain identical to frozen `0ca125d`.

Final pure-validator followup `b38508e` corrects terminal-duration activity capping
and adds a float-boundary negative control. All 15 controls and frozen-raw replay
pass; no additional native execution or gate promotion is claimed.
