# Autonomous worklog

Chronological record of work on the SIGHTBREAK v1.0 mission: investigations, decisions, failed experiments, tests, reviews and source revisions. Newest entry last. Results in the acceptance matrix ([SIGHTBREAK_V1_PROGRESS.md](../roadmap/SIGHTBREAK_V1_PROGRESS.md)) must trace back to an entry here.

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

## 2026-10-22 - Independent M1 menu evidence preserved

`/root/menu_critic`, separate from the builder, reproduced baseline 561d0cb's
missing field-menu focus (9 checks/3 failures) and candidate 8de7331's scene pass
(30/0), plus the input-mode regression (31/0). The independent Linux OS keyboard
comparison chooses the candidate for initial RESUME focus, full Tab/Shift-Tab
navigation, explicit Return resume and observed pause/focus-recovery input safety.
Fresh import exposed the omitted test UID; root's aa0b0a4 repair was cherry-picked
onto the detached review candidate as 6767e97 with identical shipping main.gd bytes.
Exact561d0cb and 6767e97 clean source-bound exports supplied the native proof.

The [original review](../reports/gauntlet/m1-menu-focus/independent-review.md),
brief and commands are preserved verbatim with a bounded 123-file compressed
[archive](../reports/gauntlet/m1-menu-focus/INDEPENDENT_ARCHIVE.md). It includes
original screenshots/videos, OS actions, observer traces, source/ELF hash receipts,
the successful baseline and later candidate attempts, and the failed setup/export
and first native observer attempt. Separate manifests document excluded compiled
ELFs, launcher and caches. No downloaded template archive, key or cache is
committed. The archive branch starts at 6a0d8d5 and changes no implementation.

This is limited menu evidence. Root separately reports integrated validate.sh
PASS at 6a0d8d5 with intentional skips; that broader run was not re-reviewed by the
menu critic. Latest desktop CI 39712752860 has a reported source-suite isolation
failure, so no overall CI pass is recorded. Hardware/controller, complete
journeys/matches, visual quality and all complete G1–G20 acceptances stay outside
this verdict. Root owns the later aggregate mission-matrix update.


## 2026-10-22 — Codex product execution checkpoint

Goal registered through the supported GitHub connector as issue #25. The native
Codex tool list has no persistent goal API; connected Linear requires reauthentication.
Mission initialization `561d0cb` reused PR24 records and added the Codex resume contract.
The old `/workspace/sightbreak` quality-only branch was left intact.

Implemented and committed FIELD MENU keyboard focus (`8de7331`, UID repair `aa0b0a4`),
ordinary native objective approach (`44cb081`), checked X11 lifetime handling
(`2e158e2`), and consumed-input replay clock correction (`0917771`). The frozen
integrated test/export source is `6a0d8d5`; later evidence commits do not re-attest
those binary bytes to a new HEAD. Menu independent evidence is in `bcdc93a` and
network blind/repeat evidence in `954c1d7`.

Real fresh baseline planting failed after 68.384 s due to movement overshoot.
Candidate plant r1 passed but its external sampler started too late to prove the
exact settled ticks; r2 repeated unchanged criteria with retention active before
launch, passing in 124.299 s. Defuse passed in 103.392 s. A fresh critic recomputed
source/ELF identities, all raw snapshot hashes, neutral settled ticks, objective
hold durations (180/300 ticks), progression restart and clean process ownership.
The helper's dynamics coverage is bounded to 0–0.2 simulation seconds input delay;
a separate source review found queued-pulse false arrival at 1.5 s, retained as an
explicit limit rather than hidden or certified away.

The same critic independently reproduced nine real X11 controls, baseline fatal
BadWindow discovery/focus races, and the checked candidate. Actual full layout
capture then passed 960×540, 1920×1080 and 1280×800, but FAILED 1280×720 after touch
opt-out: the actual desktop HUD is visible, while small footer OCR misses required
labels. All owned processes were reaped; failed live session needed SIGTERM and
was not counted as success. Whole run 289.346 s, per-case budget unchanged 120 s;
configured whole budget 600 s differed from original 520 s, both exceed actual.
No visual-quality score or shipped-game parity is inferred.

`validate.sh` completed exit 0 at clean `6a0d8d5`, logs run-as4Oaj: 16,355 reported
checks including privacy, replay/prediction, UI, input, objectives and reload audio.
Rendered reload visibility and Windows-only cases skipped; backend SQL not run.
Catalog fixture drift was checked separately with the existing backend Python and
matches all 29 definitions. Bot lifecycle still has F1: 12 rounds/78 kills, no plant.

Network blind critic independently selected candidate A (revealed after verdict),
8/8 native conditions versus baseline 4/8, 32 clean peer exits. Six follow-up pairs
preserved unchanged gates: eight total snapshot trials stop in 316–334 ms with
zero stale-authority travel. Same-host minimum 16 ms margin and limited trial count
remain limitations. These two-peer results do not satisfy G3 ten-client RC gates.

Desktop CI 39712752860 was dispatched on published `6a0d8d5`. Windows and Linux
objective/full-stock match/earned restart steps pass; independent receipt review is
underway. Jobs still fail ordinary offline journey and reused suite save data.
Intel Mac still fails original 120 s startup despite minimal native controls passing;
ARM startup/controls pass without gameplay acceptance. Isolated builders immediately
began the suite isolation, OCR, offline journey and Mac render follow-ups. No shared
merge, production deployment or release was performed. CS2 reference fetch again
returned proxy CONNECT 403; hardware, human, listening and release gates remain open.
