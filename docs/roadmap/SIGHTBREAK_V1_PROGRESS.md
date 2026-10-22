# SIGHTBREAK v1.0 progress

Last updated: 2026-10-22 (Codex mission activation). Permanent tracker: [issue #25](https://github.com/calebaiken/sightbreak/issues/25), IN PROGRESS / PRIMARY. Existing Claude baseline and worklog remain historical evidence. Mission and gates: [SIGHTBREAK_V1_MISSION.md](SIGHTBREAK_V1_MISSION.md). Resume point: [../engineering/NEXT_SESSION.md](../engineering/NEXT_SESSION.md). Log: [../engineering/AUTONOMOUS_WORKLOG.md](../engineering/AUTONOMOUS_WORKLOG.md).

Statuses: `NOT STARTED`, `IN PROGRESS`, `FAILED`, `VERIFIED`, `BLOCKED EXTERNALLY`. **Verified by** says who ran it. "Reported" means a source document says so and nobody on this line has re-run it. Reported results are not promoted to `VERIFIED` until someone re-runs them.

## Current execution

Updated 2026-10-22, 06:13 UTC. The mission remains **IN PROGRESS / PRIMARY**.
Branch `codex/v1-mission-playability`, [draft PR27](https://github.com/calebaiken/sightbreak/pull/27),
is based on PR24 `c84eaf3` → PR23 `db3981e` → PR22 `82a03fc` → PR16 `d2439ac`.
Initialization is committed as `561d0cb`; [issue25](https://github.com/calebaiken/sightbreak/issues/25)
is the actual persistent tracker, not a native Codex goal registration.

- M1: native keyboard focus, ordinary player plant/defuse, window lifetime and
  observer corrections are integrated after fresh independent reviews. Combined
  Linux source `0ca125d` completes the ordinary journey in 229.587 s and a stock
  12-round draw, with exact 120 XP / 250 offline credits after restart.
- Windows `a8eb7eb`, run39728129445, now completes the original ordinary journey
  in 233.547 s. All sixteen original OCR outputs verify; exact LEAVE selection,
  saved settings, focus release and fresh movement pass independent raw review.
  Two unfenced named captures show the previous UI phase; they are not rendered
  proof of their filenames. The overall native job still fails the plant role
  wait after a valid 180-tick plant and reward. Final raw review is pending commit.
- M2: all four native hosts pass 1,281 source checks at `0ca125d`. Intel full-game
  default/OpenGL and all five feature ablations still time out at 120 s; minimal
  2D/3D controls pass. No shipping graphics correction is supported by those
  results. ARM graphical startup passes; actual keyboard/pointer qualification
  now starts with a non-requesting permission/window preflight. Actual ARM run39727011693 at `e7718ee` reports that step successful; independent raw review accepts all four positive permissions, exact owned window/internal PNG and clean profile/process outcome. No events were posted. Actual source3b97a00 menu attempt fails before input at foreground verification (zero events). Swift compiles; helper permission/capture/Vision are unreached. The independently retained failure is `a172934`/`5378b1f`; focus diagnostics and supported run-loop observation are the next M2 iteration.
- ARM source `2a2b732`, [run39721286005](https://github.com/calebaiken/sightbreak/actions/runs/39721286005),
  passes actual unsigned generic-device iOS compilation under Xcode26.3/SDK26.2
  after a forced-symbol SDK probe. [Independent review](../reports/gauntlet/m2-native-mac-ci-39721286005/independent-review/README.md)
  retains source/PCK/linker/codesign evidence; the 102 MB executable was not
  independently transferred/reparsed. Runtime, installation and physical play
  remain open. Earlier Android/iOS structural exports are source `6a0d8d5`.
- M3: consumed replay freshness and two-phase combat authority are independently
  accepted within their declared scope. Ten-client soak/campaign, protocol and
  hostile-input outputs are independently archived. The original 18-second
  impaired lost-close trial fails (3/10); a separate full-deadline diagnostic
  recovers all ten, with server ACK upper bound 14.890 s. No runtime recovery
  change was justified. [Network review](../reports/gauntlet/m3-network-qualification/independent-critic/REVIEW.md).
- Ten actual accounts complete a seven-round stock match at `471fbd8`, six real
  plants and automatic halftime, then recover the production earned result
  through process kills, database outage, lost reply and replay. Exactly one
  operation / ten rewards / ten ledger rows grant 2,875 credits and 2,650 XP.
  Separate critic queried the live owned database and checked raw receipts and
  cleanup. Final validator has 15 passing controls. [Account evidence](../reports/gauntlet/m3-account-match/RESULTS.md).
  Nine clients turn at spawn: this does not qualify meaningful activity or AFK resistance.
- A further M3 correction moves participation checks from discarded packet tails
  to immutable consumed commands. Actual ENet baseline renews activity 93 times
  without aim changes; candidate renews it zero times, while legitimate aim
  stays 13/13. A fresh critic accepts source and adversarial controls. The
  reward formula, real-yaw policy, ten-second window and qualification thresholds
  are unchanged. [Review](../reports/gauntlet/m3-activity-integrity/independent-critic/REVIEW.md).
  Complete unmodified aggregate retry PASSES at frozen `b85f936`, source unchanged, independently audited in `609913e` (52 mandatory Godot logs, ENet/lifecycle/catalog/Python). Five rendered checks, three Windows cases and optional backend SQL remain outside this run. The earlier sparse-fixture failure and 57 raw files remain retained. This aggregate predates the new planted-role source; final combined validation is required.
- M5: six bot habits now use corresponding squad slots, preserving the reviewed
  authority implementation and Claude authorship. Final independent engine
  oracle: 2,722 checks, zero candidate failures / zero unequal pairs versus
  300 intentional baseline failures / 181 of 480 unequal pairs. Nine independent
  focused steps pass. [Review](../reports/gauntlet/m5-bot-squad-symmetry/independent-critic/REVIEW.md).
  Full-match cooperation, navigation and competitive fairness remain open.
- Combined Linux layout at `0ca125d` fails three unchanged timing gates. A child-only
  one-thread OCR correction reduces measured CPU by 52.94% on 176 actual calls
  with identical TSVs; wall time changes only 1.5%, so a timeout fix is unproven.
  Separate per-size original-PNG artifacts and a Linux-only workflow lane are
  independently accepted. The new exact-source local four-size run at `872a576` passes in 280.215 s under the original limits; [independent raw/image review](../reports/gauntlet/m1-native-ci-39725980732/local/README.md) verifies all 22 named frames. Remote Linux run39725980732 passes the ordinary journey but its plant gate fails after successful180-tick arming and reward: repeated notifications prevent the15 s role-guidance wait before player death. Remote layouts pass201.314 s, defuse and full match/restart pass; independent raw archive is retained in `b85f936`.

Historical failures, original raw archives and earlier fixture rejections remain
in the worklog and milestone reports. Later commits do not relabel old binaries.
The reviewed local touch-enabled frame also exposes a MENU/device-label overlap and stale keyboard footer after live opt-in. First candidate wins a fresh blind still comparison, then a critic rejects its existing long-feed clipping. Final `589a52a` passes462 transition checks, independent4/4 clipping controls and actual71.891 s on/off capture. A fresh blinded still judge selects it; control contrast and whole UX quality remain open. Saved touch targets stay intact. No whole product gate below is closed by these bounded engineering results.

## Acceptance matrix

| ID | Gate | Status | Evidence on record | Verified by | Next action |
| --- | --- | --- | --- | --- | --- |
| G1 | Offline 5v5 match runs start to finish (objectives, combat, economy, results, progression) | IN PROGRESS | Real Linux/Windows plants, defuses, stock full matches and earned-training restart independently reviewed. Latest Windows ordinary journey passes 233.547 s. New planted-role source passes living guidance and natural defuse in two actual Linux attempts; both fail the unchanged next-round deadline, restart unreached. [Review](../reports/gauntlet/m1-postplant-guidance/independent-critic/REVIEW.md). | Fresh independent native critics | Qualify the new source on Windows; diagnose slow simulation under the original next-round budget. Human full matches remain open. |
| G2 | Bots: reliable navigation, objectives, cooperation, difficulty | IN PROGRESS | Six squad-habit corrections independently accepted: final engine oracle 2,722 checks, candidate zero failures / zero unequal pairs versus baseline 300 / 181 of 480. Nine independent focused steps pass. One lifecycle observes a plant; historical F1 is retained. [Review](../reports/gauntlet/m5-bot-squad-symmetry/independent-critic/REVIEW.md). | Fresh independent native critic | Measure representative full matches, objective reliability, navigation and cooperation; shared roster RNG and same-tick reports remain open. |
| G3 | Ten-client authoritative match: reliability, privacy, identity, integrity, impairment | IN PROGRESS | Reviewed replay freshness, phased combat authority, ten-client soak/campaign, protocol and hostile probes. Short impaired lost-close trial fails; separate full-deadline diagnostic recovers ten. Ten actual accounts complete stock rules and recover one earned result exactly once under outage/kill/lost reply. [Account evidence](../reports/gauntlet/m3-account-match/RESULTS.md). | Fresh independent source, blind-output and native/database critics | Qualify remote-host impairment, substantive activity, competitive policies and prediction feel. Complete V3 and PR18/19/21 remain unqualified. |
| G4 | Gunplay: recoil, spread, fire cadence, hit and elimination feedback | IN PROGRESS | Rules are tested (`actor_test`, `hit_feedback_test`, `weapon_integrity_test`). No measurement of feel, no human assessment, no comparison to a shipped title. | Reported | Build a measurement harness for all four weapons (milestone candidate). |
| G5 | Viewmodel, reload and weapon switch animation | FAILED | Relay AR has authored art. Same-family review scored the weapon and hands slice 5.5/10 against 8.5. Kestrel 9, Vectorline and Longwatch are still procedural. | Reported (same-model reviewer, stills) | Native recapture, critic round, author the other three weapons. |
| G6 | Input responsiveness (mouse, movement, fire) measured | IN PROGRESS | Keyboard FIELD MENU focus and safe resume independently verified with OS input. Replay-silence stopping measured at 316–334 ms in eight two-peer trials. Prediction error max 0.075834 m. No physical input-to-photon or input-to-fire measurement. | Fresh native/menu and blind network critics | Keep engineering measurements scoped; obtain device latency and human feel evidence. |
| G7 | UI/UX across journeys (menu, deploy, LAN, settings, HUD, buy, scoreboard, pause, inventory, cases, results, error states) | IN PROGRESS | FIELD MENU input and safe resume reviewed. Four-size native layouts pass original limits. Final live touch-mode candidate passes 462 checks, independent clipping controls and native on/off capture; fresh blinded judge chooses it. Planted-role guidance survives all 1,458 declared flood frames and actual living gameplay. | Fresh independent native/menu/layout/blind critics | Control contrast, all journeys, accessibility and shipped-game presentation comparison remain open. |
| G8 | Visual quality at least 8.5/10 in each applicable category | FAILED | 0.3 aggregate 8.1 (geometry, materials, lighting, models, effects below 8.5). Fresh sequence review about 5.5. | Reported (AI reviewers, not human) | Per-category rounds after G4-G7. |
| G9 | Audio: fire, reload, hit, objective cues consistent with animation | IN PROGRESS | All sound is synthesized in code. Capture-based tests pass; exit-time AudioStream leaks and one nondeterministic timing control were reported. Nobody has listened. | Reported | Check leaks in baseline; add timing measurements. A listening review needs a person. |
| G10 | Accessibility (contrast, text scale, reduced motion, controller/keyboard reach) | IN PROGRESS | Text scale and reduced motion exist. No audit, no screen-reader or physical-controller evidence. | none | Compute WCAG contrast from captures (bar B4). |
| G11 | Linux native package | IN PROGRESS | Source872 local/remote layouts pass 280.215/201.314 s; ordinary journey, defuse and full match/restart pass. New source3c4d921 fixes notification-starved planted roles, with independently inspected living pixels/video and natural defuse. Both full plant attempts fail the original next-round12 s deadline. | Fresh independent native/layout critic | Preserve failures; diagnose performance and verify next-round/restart on an exact corrected candidate. Whole Linux release gate stays open. |
| G12 | Windows native package | IN PROGRESS | Actual sourcea8eb7eb run39728129445 completes the original ordinary journey in 233.547 s; settings, focus release, fresh movement and exact LEAVE OCR pass. Defuse/full match and earned restart pass. Overall job fails old planted-role wait. Two unfenced captures show prior phases and provide no proof of their named phase. | Fresh independent native output critic | Finish raw review commit, then execute original native gates on integrated planted-role source. Preserve prior death, OCR and role failures. |
| G13 | macOS native package (Intel and Apple Silicon) | FAILED | ARM readiness passes exact owned-window checks. Actual3b97a00 menu run39729489971 fails foreground verification before any posted input or capture-helper invocation. All twelve source suites pass 4,461 assertions. Intel full-game rendering still times out; minimal controls pass. [Review](../reports/gauntlet/m2-macos-menu-input/native-run-39729489971/REPORT.md). | Fresh independent native output critics | Critique supported run-loop observer and independent owned-window capture, then run actual ARM pointer/keyboard journey. Intel/device qualification stays open. |
| G14 | Android and iOS keep building | IN PROGRESS | Fresh frozen 6a Android debug APK and unsigned iOS project export and structural inspection pass. Independent 48/49 package checks: simulator metadata claims ARM64+x86_64 but pinned debug archive contains x86_64 only; device archive is ARM64. [Evidence](../reports/gauntlet/m2-mobile-preservation/independent-package-critic/REPORT.md). Actual Xcode 16.4 / SDK 18.5 link fails on five iOS 26 framework globals. Reviewed SDK selection is integrated; retries39721286005 at2a2b732 and39727011693 ate7718ee pass independent unsigned-device compile review, with exact source/PCK and raw unsigned codesign evidence. Final binary reparse and runtime remain open. | Fresh independent mobile package critic | Preserve accepted exact-source unsigned compile; qualify simulator metadata, installation, older OS behavior and physical play. No credential/signing action is authorized. |
| G15 | Packaging, build provenance, Steam staging procedure | IN PROGRESS | Source-bound manifests exist. `STEAM_RELEASE_READINESS.md` is design only: no SteamPipe template, no App ID, Steamworks docs not retrievable (host denied). | Reported | Owner approval is needed for any upload or account step. |
| G16 | Economy and progression integrity | IN PROGRESS | Earned offline progression persists in actual Windows/Linux exports. Ten-account stock match creates a production payload and recovers exactly once after process/database/lost-reply failures: one operation, ten rewards/ledger rows, 2,875 credits / 2,650 XP. Independent live database queries, raw replay and 15 validator controls pass. A further accepted consumed-command correction prevents discarded packet tails renewing activity (93 baseline versus zero candidate); real aim remains eligible. | Fresh independent native/database critic | Qualify substantive activity/AFK policy, remote-host recovery and production deployment security separately; no deployment performed. |
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
| PR26 `claude/relay-yard-tactical-layout-v1` | `778c89a` | Separate map candidate and bot measurements; not integrated. Reports F2 actor-order bias. |
| PR27 `codex/v1-mission-playability` | see worklog / NEXT_SESSION | Active Codex mission, native input/validation, replay freshness and platform follow-ups, based on PR24. |

| PR28 `claude/fair-actor-order-v1` | `2641ddf` | Bot-only delta `0871bc9` adapted with attribution; authority shuffle is excluded in favor of independently reviewed phased authority. |

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

## Current objective-guidance and account qualification

M1 source `3c4d921` is integrated as `d7dc1be`; final independent review is
`e2c61ac`. Candidate wins the declared selector comparison: zero wrong frames
versus all 1,458 baseline flood frames, with 1,559 independent controls. Both
actual native trials show living planted guidance and a genuine natural defuse,
then fail the original next-round deadline. The no-recorder retry also fails;
recording alone cannot explain it. Original 130.400 s video, PNGs and failures
are retained. Thread overrides select llvmpipe with LP_NUM_THREADS=2 in both runs;
source diagnosis does not establish a graphics or UI regression.

The corrected-activity ten-account/backend qualification is authorized at exact
`e2c61ac2ecbd38ab55bc9edb712b028322c1490f`, game tree
`fb6be859e05812d8707be1ef5c6f747d2588c1e9`, on an isolated frozen checkout.
A fresh critic must observe committed SQL before the lost-worker checkpoint and
ACK release, then after replay. Runtime results are pending. Neither the bounded
M1 correction nor this qualification closes whole G1/G3/G16.
