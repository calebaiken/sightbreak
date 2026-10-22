# SIGHTBREAK v1.0 progress

Last updated: 2026-10-22 (Codex mission activation). Permanent tracker: [issue #25](https://github.com/calebaiken/sightbreak/issues/25), IN PROGRESS / PRIMARY. Existing Claude baseline and worklog remain historical evidence. Mission and gates: [SIGHTBREAK_V1_MISSION.md](SIGHTBREAK_V1_MISSION.md). Resume point: [../engineering/NEXT_SESSION.md](../engineering/NEXT_SESSION.md). Log: [../engineering/AUTONOMOUS_WORKLOG.md](../engineering/AUTONOMOUS_WORKLOG.md).

Statuses: `NOT STARTED`, `IN PROGRESS`, `FAILED`, `VERIFIED`, `BLOCKED EXTERNALLY`. **Verified by** says who ran it. "Reported" means a source document says so and nobody on this line has re-run it. Reported results are not promoted to `VERIFIED` until someone re-runs them.

## Current execution

Updated 2026-10-22, 07:39 UTC. The mission remains **IN PROGRESS / PRIMARY**.
Branch `codex/v1-mission-playability`, [draft PR27](https://github.com/calebaiken/sightbreak/pull/27),
retains PR24 → PR23 → PR22 → PR16 dependencies. Initialization is `561d0cb`;
[issue #25](https://github.com/calebaiken/sightbreak/issues/25) is the supported
persistent tracker. No native Codex goal registration is claimed.

- **M1 Windows selected native gates independently pass.** Actual run
  [39735001567](https://github.com/calebaiken/sightbreak/actions/runs/39735001567),
  exact `3b5cf764`, completes the ordinary journey in 118.234 s, player plant in
  69.485 s, natural defuse and next buy within the original 12 s limit, player
  defuse, OS-input schedules and all twelve native suites / 5,963 assertions.
  Corrected 06c and 10 captures show the intended living buy phases. A separate
  stock nine-round match grants 120 XP / 250 offline credits and reloads them
  exactly from disk. Review `b97fd81` retains 206 raw files and original PNGs.
  The plant scenario's default-profile restart is not earned-progression proof.
- **M1 Linux retains a real failure.** Planted-role source `3c4d921` wins the
  declared 1,458-frame notification comparison and shows living DEFEND guidance
  plus natural defuse in both native attempts. Both fail the unchanged next-round
  deadline; the no-recorder repeat also fails. Original video and failed receipts
  remain in `m1-postplant-guidance`. Earlier ordinary journey, layouts, defuse and
  stock full-match / earned restart passes remain exact-source historical results.
- **M2 ARM Mac latest clean native attempt independently passes**, run
  [39739927334](https://github.com/calebaiken/sightbreak/actions/runs/39739927334)
  at `ba5013d`: all original twelve suites / 5,963 checks, menu pointer/Escape
  navigation and separate unsigned iOS compilation. Root review `097b1e7` retains
  original PNGs, source/producer receipts and cleanup limits. The leak diagnostic
  did not run because strict suites passed. Prior actor six-leak and input_mode
  two-leak failures remain failures; types and cause are still unknown. This
  clean attempt does not establish stable leak resolution or full Mac gameplay.
  New ARM run 39741565795 at `0527715` qualifies the changed receipt source and
  fourteen-suite registration separately. Intel rendering still times out;
  mobile installation and physical play remain open.
- **M3 corrected-activity account trial 2 independently passes**, source
  `3b5cf764`, 521.837 s. Seven stock rounds / six plants / halftime deliver one
  operation, ten rewards and ten ledger rows: 2,875 credits / 2,650 XP. Actual SQL
  is retained before the lost-worker checkpoint, after replay, and in a distinct
  post-replay query; all owned resources are gone. Evidence `de37251`, `e097aa7`,
  `a3b7070`. Trial 1 stays independently BLOCKED by its missing post-replay witness;
  no observations are backfilled. Nine clients turning at spawn follow existing
  policy and do not qualify AFK resistance or meaningful participation.
- **M3 backend regression independently passes**, frozen `48da994`: 61 cases /
  44 existing test functions, all migrations, new owned PostgreSQL 17.11, two
  recorded TCP SQL identity routes and verified cleanup. Two failed preflights
  and one dependency warning remain retained. Critic `8b5f40d` verifies the raw
  archive and source; it did not itself query SQL while the database was live.
  No backend product code changed or production-deployment gate closed.
- **M3 keyed store/armory receipt recovery is independently accepted and integrated.**
  Exact native source `79e076e` recovers 12/12 process-kill cases versus baseline
  0/12 across store, case and market routes. Original HTTP method/route/body,
  expected price, one fixture mutation, credential-free journals and owned
  cleanup all pass independent audit. Five affected suites pass, including the
  unchanged strict armory transport check. Root runtime `52973a5` / `e51816c` /
  `e8c701a` preserves original PR18 authorship; critic `ecc2690` and archive
  `89393f3` retain findings, fixes and actual outputs. This uses local SQLite
  fixtures and a separate stub lifecycle, not production PostgreSQL or rendered
  player consent. Those boundaries are next; postmatch rewards remain separate.
  New fourteen-suite native registration is independently accepted. The strict
  selected Linux journal/gunplay run passes in 13.003 s; the new full aggregate
  is running at frozen `0527715`, with separate independent review.
- **M4 four-weapon engineering measurement independently passes**, exact source
  `fc5d677`: 2,840 native probe checks / 52 records plus 289 affected existing
  checks. Critic recomputes 5,121 predicates, real ray damage, friendly shielding,
  reload/deploy and complete cadence timelines. Maintained validator now registers
  the probe. No shipping weapon tuning, latency, feel, listening, CS2 comparison
  or whole M4 acceptance is claimed. Evidence through `cab5e42` / `132d2db`.
- Earlier accepted product work includes safe FIELD MENU focus/resume, consumed
  replay freshness, phased combat authority, consumed-command activity checks,
  six squad-relative bot habits, objective guidance and touch HUD transitions.
  Fresh critics and failed iterations remain alongside each component's report.
- Latest complete unmodified aggregate independently passes at **`b09cfe1`**,
  465.033 s, 52 mandatory Godot logs plus seven Python groups, ENet, lifecycle,
  catalog and fixture checks; source remains clean and identical. Later M4 adds
  a mandatory probe, and receipt work will add further checks. Do not relabel
  this older whole-source result as the latest HEAD. The new frozen aggregate
  at `0527715` is running; root owns local engine CPU. New Windows and ARM runs
  at that source independently qualify the fourteen-suite default and exports.

## Acceptance matrix

| ID | Gate | Status | Evidence on record | Verified by | Next action |
| --- | --- | --- | --- | --- | --- |
| G1 | Offline 5v5 match runs start to finish (objectives, combat, economy, results, progression) | IN PROGRESS | Windows 3b5cf764 selected native gates independently pass: ordinary controls, player plant / natural resolution / next buy, defuse, stock full match and exact earned restart. Both new Linux plant trials retain next-round timeout failures. [Windows evidence](../reports/gauntlet/m1-native-ci-39735001567/REPORT.md). | Fresh independent native critics | Diagnose Linux slow simulation under the original budget; human full matches and whole release qualification remain open. |
| G2 | Bots: reliable navigation, objectives, cooperation, difficulty | IN PROGRESS | Six squad-habit corrections independently accepted: final engine oracle 2,722 checks, candidate zero failures / zero unequal pairs versus baseline 300 / 181 of 480. Nine independent focused steps pass. One lifecycle observes a plant; historical F1 is retained. [Review](../reports/gauntlet/m5-bot-squad-symmetry/independent-critic/REVIEW.md). | Fresh independent native critic | Measure representative full matches, objective reliability, navigation and cooperation; shared roster RNG and same-tick reports remain open. |
| G3 | Ten-client authoritative match: reliability, privacy, identity, integrity, impairment | IN PROGRESS | Reviewed replay freshness, phased combat authority, ten-client soak/campaign, protocol and hostile probes. Short impaired lost-close trial fails; separate full-deadline diagnostic recovers ten. Ten actual accounts complete stock rules and recover one earned result exactly once under outage/kill/lost reply. [Account evidence](../reports/gauntlet/m3-account-match/RESULTS.md). | Fresh independent source, blind-output and native/database critics | Qualify remote-host impairment, substantive activity, competitive policies and prediction feel. Complete V3 and PR18/19/21 remain unqualified. |
| G4 | Gunplay: recoil, spread, fire cadence, hit and elimination feedback | IN PROGRESS | All four stock weapons measured at fc5d677: 2,840 native probe checks / 52 records and 289 existing controls pass; independent critic recomputes 5,121 predicates including complete cadence, actual health, friendly shielding and reload/deploy timelines. [Evidence](../reports/gauntlet/m4-gunplay-invariants/NATIVE_RESULTS.md). | Fresh independent source and native-output critics | Measure actual rendered handling, device latency and human feel against accessible shipped-game references. No tuning or feel acceptance inferred. |
| G5 | Viewmodel, reload and weapon switch animation | FAILED | Relay AR has authored art. Same-family review scored the weapon and hands slice 5.5/10 against 8.5. Kestrel 9, Vectorline and Longwatch are still procedural. | Reported (same-model reviewer, stills) | Native recapture, critic round, author the other three weapons. |
| G6 | Input responsiveness (mouse, movement, fire) measured | IN PROGRESS | Keyboard FIELD MENU focus and safe resume independently verified with OS input. Replay-silence stopping measured at 316–334 ms in eight two-peer trials. Prediction error max 0.075834 m. No physical input-to-photon or input-to-fire measurement. | Fresh native/menu and blind network critics | Keep engineering measurements scoped; obtain device latency and human feel evidence. |
| G7 | UI/UX across journeys (menu, deploy, LAN, settings, HUD, buy, scoreboard, pause, inventory, cases, results, error states) | IN PROGRESS | FIELD MENU input and safe resume reviewed. Four-size native layouts pass original limits. Final live touch-mode candidate passes 462 checks, independent clipping controls and native on/off capture; fresh blinded judge chooses it. Planted-role guidance survives all 1,458 declared flood frames and actual living gameplay. | Fresh independent native/menu/layout/blind critics | Control contrast, all journeys, accessibility and shipped-game presentation comparison remain open. |
| G8 | Visual quality at least 8.5/10 in each applicable category | FAILED | 0.3 aggregate 8.1 (geometry, materials, lighting, models, effects below 8.5). Fresh sequence review about 5.5. | Reported (AI reviewers, not human) | Per-category rounds after G4-G7. |
| G9 | Audio: fire, reload, hit, objective cues consistent with animation | IN PROGRESS | All sound is synthesized in code. Capture-based tests pass; exit-time AudioStream leaks and one nondeterministic timing control were reported. Nobody has listened. | Reported | Check leaks in baseline; add timing measurements. A listening review needs a person. |
| G10 | Accessibility (contrast, text scale, reduced motion, controller/keyboard reach) | IN PROGRESS | Text scale and reduced motion exist. No audit, no screen-reader or physical-controller evidence. | none | Compute WCAG contrast from captures (bar B4). |
| G11 | Linux native package | IN PROGRESS | Source872 local/remote layouts pass 280.215/201.314 s; ordinary journey, defuse and full match/restart pass. New source3c4d921 fixes notification-starved planted roles, with independently inspected living pixels/video and natural defuse. Both full plant attempts fail the original next-round12 s deadline. | Fresh independent native/layout critic | Preserve failures; diagnose performance and verify next-round/restart on an exact corrected candidate. Whole Linux release gate stays open. |
| G12 | Windows native package | IN PROGRESS | Actual run 39735001567 at 3b5cf764 independently passes all selected native gates, 5,963 source assertions, corrected phase captures, plant / natural defuse / next buy, ordinary defuse, stock full match and earned disk reload. [Evidence](../reports/gauntlet/m1-native-ci-39735001567/REPORT.md). | Fresh independent native critic | Preserve exact frozen qualification; repeat on final integrated candidate and obtain physical / human release evidence. |
| G13 | macOS native package (Intel and Apple Silicon) | FAILED | Latest ba5013d run 39739927334 independently passes original twelve suites / 5,963 checks and real menu navigation. Diagnostic not run because strict passed. Earlier actor six-leak and input_mode two-leak failures remain unresolved; Intel rendering still times out. [Latest evidence](../reports/gauntlet/m2-native-mac-ci-39739927334/independent-review/REPORT.md). | Fresh independent native critics | Qualify new receipt source / fourteen suites in run 39741565795; retain historical failures and obtain verbose types if a supported failure recurs. Full gameplay, stable leak resolution, Intel and physical-device gates remain open. |
| G14 | Android and iOS keep building | IN PROGRESS | Fresh frozen 6a Android debug APK and unsigned iOS project export and structural inspection pass. Independent 48/49 package checks: simulator metadata claims ARM64+x86_64 but pinned debug archive contains x86_64 only; device archive is ARM64. [Evidence](../reports/gauntlet/m2-mobile-preservation/independent-package-critic/REPORT.md). Actual Xcode 16.4 / SDK 18.5 link fails on five iOS 26 framework globals. Reviewed SDK selection is integrated; retries39721286005 at2a2b732 and39727011693 ate7718ee pass independent unsigned-device compile review, with exact source/PCK and raw unsigned codesign evidence. Final binary reparse and runtime remain open. | Fresh independent mobile package critic | Preserve accepted exact-source unsigned compile; qualify simulator metadata, installation, older OS behavior and physical play. No credential/signing action is authorized. |
| G15 | Packaging, build provenance, Steam staging procedure | IN PROGRESS | Source-bound manifests exist. `STEAM_RELEASE_READINESS.md` is design only: no SteamPipe template, no App ID, Steamworks docs not retrievable (host denied). | Reported | Owner approval is needed for any upload or account step. |
| G16 | Economy and progression integrity | IN PROGRESS | Corrected-source trial 2 at 3b5cf764 independently passes stock ten-account settlement and pre-ACK / post-replay SQL witnesses: one operation / ten rewards / ten ledger rows, 2,875 credits / 2,650 XP. Trial 1 remains blocked. Separate backend regression passes 61 cases. [Trial evidence](../reports/gauntlet/m3-account-activity/TRIAL_2_HANDOFF.md). | Fresh independent native / live-database and regression critics | Keyed store/armory receipt component independently passes 12/12 native fixture recoveries versus baseline 0/12. Next qualify production PostgreSQL lost-response settlement and rendered player recovery; meaningful activity, AFK policy, remote recovery and deployment security remain separate. |
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

The current execution block and gate table above supersede the earlier pending
states. Original Linux objective failures, account trial 1's missing post-replay
witness and all rejected fixtures remain unchanged. Trial 2 independently closes
its declared current-source stock settlement/recovery scope, and Windows independently
passes its selected native gates. Neither result closes whole G1/G3/G12/G16.
