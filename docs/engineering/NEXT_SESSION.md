# Next session

Updated 2026-10-22. Continue **SIGHTBREAK — Steam-Ready v1.0**, IN PROGRESS / PRIMARY,
tracked by [issue #25](https://github.com/calebaiken/sightbreak/issues/25).
No native Codex goal API is exposed; Linear needs reauthentication. Read AGENTS.md,
the mission and the canonical G1–G20 progress matrix. Reuse installed quality skills.

## Repository checkpoint

- Worktree: `/workspace/sightbreak-v1-execution`; branch: `codex/v1-mission-playability`.
- [Draft PR #27](https://github.com/calebaiken/sightbreak/pull/27) targets PR24 `claude/mission-foundation-v1` (`c84eaf3`), then PR23 `db3981e` → PR22 `82a03fc` → PR16 `d2439ac`.
- Combined native CI source: **`0ca125dfba637868e6e8e9772ff9c40400413e32`**, [run 39719407304](https://github.com/calebaiken/sightbreak/actions/runs/39719407304). It includes combat f13ed03/oracle 8571c78/native registration 40ffbae and iOS stack through 8f61180. Game tree `782c26464631f86ad63ddab9de36a969d4e44534`; content SHA256 `f8a849b90df3ff214037cace7bc32c0c7b5e184911558b424b0a6c0f798db781`; validation SHA256 `95844559cde01c1f9785d2835ea9f92a5e09e0315f87f0e7aa5029352456196c`. Later evidence commits do not relabel this build. Fetch live refs before integration; do not rewrite or merge shared branches.
- Last full integrated regression/export/CI source: **`6a0d8d5d85b4fb37943903886982f51b4ed230b0`**. Later tooling/evidence commits do not re-attest that binary to a new HEAD.
- That game tree is `13079ab8a3de9b18252a652ed57157e0776cf394`; content SHA256 `954b0a73cff89483a9270434da7902b2d128f1b9a99c30290dfe03862c038873`; validation SHA256 `9155b9c6a68fbeb459c4d0654b49ec4b250d1e11bea667747dfc4056e1ea2f03`.
- Its Linux ELF is `builds/mission-m1/candidate-build/linux/sightbreak.x86_64`, SHA256 `ef4ab16a1b7f13fe96822a102c139fb5964275701f1e92fe8bdcfacfbf29d9a4`.

## Implemented and verified slices

- Menu focus: `8de7331` + UID `aa0b0a4`; fresh native OS Tab/Shift-Tab/Return and safe focus recovery pass. [Independent archive](../reports/gauntlet/m1-menu-focus/INDEPENDENT_ARCHIVE.md).
- Ordinary native objective controller `44cb081`, X11 lifetime `2e158e2`: plant r2 passes 124.299 s, defuse 103.392 s, original 15 s movement and 3/5 simulation-second holds. Exact neutral ticks/restart/cleanup independently recomputed. The helper has an open queued-pulse model counterexample at 1.5 simulation-second delay, outside its tested 0–0.2 envelope. [Raw evidence and failed full layout](../reports/gauntlet/m1-exported-validation/RESULTS.md).
- Replay freshness `0917771`: consumed packets cannot renew authority/idle clocks. Blind native comparison 8/8 versus 4/8; eight snapshot trials stop in 316–334 ms within 350 ms. Same-host minimum margin is 16 ms; no ten-client RC qualification. [Reviews/evidence](../reports/gauntlet/m3-input-freshness/RESULTS.md).
- Source-suite isolation `05d9b43`, cleanup truthfulness `9290154`: nine Linux suites, save safety and injected cleanup/native failures independently pass. Original critic rejection preserved. Bounded QA packer `32c37fe` independently reconstructs actual Windows receipts. [Review](../reports/gauntlet/m2-isolation-independent-review/README.md). Combined CI source suites now pass on Windows, Linux and ARM Mac. ARM critic independently verifies 1,281 checks and bounded receipts. The HUD fixture leaves a separately owned inner marker; a builder is repairing it. Root combined 10-suite execution at 77147c5 passes after F2 integration; do not generalize outer cleanup to all fixture state.
- Intel render diagnostics `44b9ac0`: five isolated Linux feature controls, copied resources and subprocess/error cases independently reviewed. These are diagnostics, not a Mac fix. Standalone workflow `b9826d4` returned HTTP404 because unregistered; registered desktop workflow fallback `3bfc29b` independently reviewed. [Review](../reports/gauntlet/m2-macos-render/independent-critic/REPORT.md). Combined Intel default startup fails again; explicit OpenGL and feature attribution are pending. ARM iOS compilation reaches the linker and fails with five missing iOS 26 framework globals under default Xcode 16.4 / SDK 18.5. The runner inventory includes Xcode 26; a builder is selecting a compatible SDK process-locally and fixing the observed Ld-line parser. Unsigned Mach-O behavior remains unobserved.

`validate.sh` at 6a completed exit 0 with 16,355 reported checks. Raw logs are
`.local/validation/run-as4Oaj` and the committed exported-validation archive.
Rendered reload visibility and Windows-only cases skipped; backend SQL not run.
Separate catalog drift check matches 29 definitions. Bot F1 persists: 12 rounds,
78 kills, no plant.

## Current CI and failures

[Run 39719407304](https://github.com/calebaiken/sightbreak/actions/runs/39719407304),
frozen 0ca125d, is active. As of 04:05 UTC: Windows/Linux source suites, plant and
defuse steps pass; Linux ordinary journey passes; Windows ordinary journey fails
with raw diagnosis pending. Full-match/restart and layout stages are still running.
ARM default graphical startup and all ten source suites pass. Independent ARM
review verifies 136 indexed receipts and 1,281 checks. Intel unchanged startup
fails; retain upcoming explicit OpenGL/feature results before choosing a fix.

ARM unsigned iOS build fails exit 65 after 36.095 s: `_CADynamicRangeAutomatic`,
`_CADynamicRangeConstrainedHigh`, `_CADynamicRangeHigh`, `_CADynamicRangeStandard`
and `_MTLTensorDomain` are unresolved in pinned Godot metal_cpp. Xcode 16.4 uses
SDK 18.5; exact runner image also supplies Xcode 26.3 / SDK 26.2. Builder worktree
`/workspace/sightbreak-ios-compile` is selecting an actually installed compatible
SDK through child-process DEVELOPER_DIR, preserving the pinned engine and budget.
The real Ld action omits `arm64` on its summary line; fix that observer assumption,
then require the app Mach-O inspection to establish architecture/platform.

Previous [run 39712752860](https://github.com/calebaiken/sightbreak/actions/runs/39712752860)
at 6a failed all four jobs. Its shared-save, ammo OCR, focus and Intel failures
remain historical evidence. Windows raw full match/restart is independently
reviewed; Linux old raw artifact exceeded transfer limits. Do not erase those
failures or claim current raw review from step metadata.

## Live local qualification

Frozen detached checkout `/workspace/sightbreak-v1-qualification` is 0ca125d.
Ten-client soak passes 11 reports and 80 forced recoveries. Twelve-condition
18-second campaign passes all conditions. Fresh critic is recomputing all raw
reports; same-actor welcome timing and final fresh-input ACK are distinct gates.
Protocol and hostile-handshake scripts run next, followed by the historical
lost-close overlap case (blackout 7.8–9.3 s, close 8 s, retry 2 s). Do not run
concurrent local Godot workloads during timed network trials. Raw output is under
`builds/session-qualification`; preserve the self-matched first process-inventory
receipt and its corrected argv-aware inventory. Ten residual reservations after
an eight-second drain are expected under the 60-second expiry, not proof of expiry.

## Candidates executing; continue them

1. Layout: `/workspace/sightbreak-layout-ocr`, `codex/v1-layout-ocr`. Candidate `afe7b54` uses an aspect-correct narrow footer strip, retaining all words/exclusions/timeouts. Earlier `3a847af` native 1280 touch pass exposed a 1280×800 pixel limitation; afe fixes it. Full exact-source four-size run PASSES 304.692s under original 520/120s limits, independently reviewed. Code integrated as 3b76d26→285f6c8; final evidence 2b4f22b. See ITERATION_2.md; live classifier remains 1280-only, other sizes have actual native/saved-pixel proof.
2. Offline observer: `/workspace/sightbreak-offline-flow`, `codex/v1-offline-flow-observation`, commits `94dc6bb` → `ccfba93` → `0a12135`. Narrow ammo OCR and read-only release-guard acknowledgment. Source/pixel checks and strict native focus-only probe pass (58.943 s, fresh movement 0.427778 m, clean exit). Full local journey still fails its unchanged 35 s second-round wait under software rendering. Fresh critic accepted the scoped correction; integrated 785ece8→1afbdda plus corrected time wording e930ba4. New combined Linux journey passes by CI metadata; Windows still fails. Independent raw reviews are pending.
3. F2 authority order: product `f13ed03`, reviewed oracle `8571c78`, native CI registration `40ffbae` are integrated. Fresh independent native/source review accepts the bounded correction: 178 checks pass versus 152 intentional baseline failures. Full maintained validation on exact product 470fad5 passes; corrected active CPU samples count real shots/damage with stable bounded pools. Earlier depleted-trigger and missing-pose benchmark defects are retained. See `docs/reports/gauntlet/m3-authority-order/README.md` and its independent report. Simultaneous multiattacker credit, wipe, utility and contact policies remain open; no full competitive fairness claim.
4. Separate Claude-owned [PR26](https://github.com/calebaiken/sightbreak/pull/26), `claude/relay-yard-tactical-layout-v1` at `5288a69`, is not integrated. Its map changes require protocol/build compatibility and native route review. Do not edit arena/bot files concurrently or blindly import the newer bot rewrite.
5. After reviewed observer integration, commit a clean candidate and dispatch registered `desktop-alpha.yml` on the own branch. Verify nine suites on actual Windows/Mac, unchanged offline journeys, objective/full-match/progression and four-size captures. Download/review bounded receipts and Mac attribution. If one Mac ablation succeeds while full fails, repeat a warm full reference before choosing a shipping correction.
6. Mobile preservation: detached `/workspace/sightbreak-v1-mobile6a` is clean 6a. Both exports and package inspection pass; fresh critic reports 48/49 checks with upstream simulator architecture mismatch. Evidence 25e889e. Actual generic-device Xcode compile is now wired to ARM Mac CI; physical play remains unavailable. Do not treat simulator metadata as a device failure or mark all G14 passed.

Update progress, evidence, worklog and this resume point after each increment.
Commit/push recoverable changes, keep PR27 draft, then immediately continue the
next release blocker. Goal completion requires all RC gates, not these slices.

## Commands and constraints

Pinned Godot is 4.7.2 through `scripts/godot.sh`; `/usr/local/bin/godot` is wrong
(4.6.3). Tools are `/workspace/tools`; Xvfb is
`/workspace/tools/xvfb/usr/bin/Xvfb`. Use a fresh output directory and a clean,
frozen checkout. Exports reject existing artifacts; validators reject source/HEAD
changes. Do not commit or edit while a local source-bound validator is running.

```sh
cd /workspace/sightbreak-v1-execution
git fetch origin '+refs/heads/*:refs/remotes/origin/*'
./scripts/validate.sh
SIGHTBREAK_BUILDS_DIR="$PWD/builds/new-frozen-run" python3 scripts/export.py linux
SIGHTBREAK_BUILDS_DIR="$PWD/builds/new-frozen-run" XVFB_BIN=/workspace/tools/xvfb/usr/bin/Xvfb LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=2 python3 scripts/verify_offline_match.py --target linux --scenario plant --display :181 --timeout 180 --output builds/new-plant
gh workflow run desktop-alpha.yml --repo calebaiken/sightbreak --ref codex/v1-mission-playability
```

Start the raw read-only status retention watcher before launch when proving exact
settled ticks (`builds/mission-m1/retain_status.py`). Coordinate software rendering;
reap owned groups. Actual GPU/input latency, physical mobile/controller devices,
human play/listening, CS2 media and Steam signing/credentials remain unavailable.
CS2 official and identified GitHub image requests were denied; reference access is
recorded under `docs/research/cs2-access-2026-10-22`. No background execution is
promised after the session ends.

The authority evidence cherry-pick conflicted only with this newer resume file;
root preserved the current multi-milestone brief and incorporated the accepted
F2 state above. Original builder HANDOFF and review remain in milestone evidence.

## Final combined checks before dispatch

All ten native source suites pass locally at 77147c5, including authority 178,
input 36 and diagnostics 60, with source resources unchanged and cleanup complete.
iOS helper ten Linux controls pass at 8f61180; actual Xcode remains unverified.
Every subsequent remote run must identify its own exact commit/artifacts. It includes
Windows/Linux original full journeys/objectives/match/restart, four-size layouts,
Intel feature attribution and ARM unsigned iOS compilation. Preserve every failed
step; no whole RC gate is passed by implementation readiness.
