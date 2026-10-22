# Next session

Updated 2026-10-22. Continue **SIGHTBREAK — Steam-Ready v1.0**, IN PROGRESS / PRIMARY,
tracked by [issue #25](https://github.com/calebaiken/sightbreak/issues/25).
No native Codex goal API is exposed; Linear needs reauthentication. Read AGENTS.md,
the mission and the canonical G1–G20 progress matrix. Reuse installed quality skills.

## Repository checkpoint

- Worktree: `/workspace/sightbreak-v1-execution`; branch: `codex/v1-mission-playability`.
- [Draft PR #27](https://github.com/calebaiken/sightbreak/pull/27) targets PR24 `claude/mission-foundation-v1` (`c84eaf3`), then PR23 `db3981e` → PR22 `82a03fc` → PR16 `d2439ac`.
- Reviewed tooling/evidence checkpoint: `42a0247`, plus this documentation update. Fetch live refs before integration; do not rewrite or merge shared branches.
- Last full integrated regression/export/CI source: **`6a0d8d5d85b4fb37943903886982f51b4ed230b0`**. Later tooling/evidence commits do not re-attest that binary to a new HEAD.
- That game tree is `13079ab8a3de9b18252a652ed57157e0776cf394`; content SHA256 `954b0a73cff89483a9270434da7902b2d128f1b9a99c30290dfe03862c038873`; validation SHA256 `9155b9c6a68fbeb459c4d0654b49ec4b250d1e11bea667747dfc4056e1ea2f03`.
- Its Linux ELF is `builds/mission-m1/candidate-build/linux/sightbreak.x86_64`, SHA256 `ef4ab16a1b7f13fe96822a102c139fb5964275701f1e92fe8bdcfacfbf29d9a4`.

## Implemented and verified slices

- Menu focus: `8de7331` + UID `aa0b0a4`; fresh native OS Tab/Shift-Tab/Return and safe focus recovery pass. [Independent archive](../reports/gauntlet/m1-menu-focus/INDEPENDENT_ARCHIVE.md).
- Ordinary native objective controller `44cb081`, X11 lifetime `2e158e2`: plant r2 passes 124.299 s, defuse 103.392 s, original 15 s movement and 3/5 simulation-second holds. Exact neutral ticks/restart/cleanup independently recomputed. The helper has an open queued-pulse model counterexample at 1.5 simulation-second delay, outside its tested 0–0.2 envelope. [Raw evidence and failed full layout](../reports/gauntlet/m1-exported-validation/RESULTS.md).
- Replay freshness `0917771`: consumed packets cannot renew authority/idle clocks. Blind native comparison 8/8 versus 4/8; eight snapshot trials stop in 316–334 ms within 350 ms. Same-host minimum margin is 16 ms; no ten-client RC qualification. [Reviews/evidence](../reports/gauntlet/m3-input-freshness/RESULTS.md).
- Source-suite isolation `05d9b43`, cleanup truthfulness `9290154`: nine Linux suites, save safety and injected cleanup/native failures independently pass. Original critic rejection preserved. Bounded QA packer `32c37fe` independently reconstructs actual Windows receipts. [Review](../reports/gauntlet/m2-isolation-independent-review/README.md). Actual Windows/macOS suite execution and CI transfer still need a new run.
- Intel render diagnostics `44b9ac0`: five isolated Linux feature controls, copied resources and subprocess/error cases independently reviewed. These are diagnostics, not a Mac fix. Standalone workflow `b9826d4` returned HTTP404 because unregistered; registered desktop workflow fallback `3bfc29b` independently reviewed. [Review](../reports/gauntlet/m2-macos-render/independent-critic/REPORT.md). Dispatch still pending.

`validate.sh` at 6a completed exit 0 with 16,355 reported checks. Raw logs are
`.local/validation/run-as4Oaj` and the committed exported-validation archive.
Rendered reload visibility and Windows-only cases skipped; backend SQL not run.
Separate catalog drift check matches 29 definitions. Bot F1 persists: 12 rounds,
78 kills, no plant.

## Current CI and failures

[Run 39712752860](https://github.com/calebaiken/sightbreak/actions/runs/39712752860),
source 6a: all four jobs fail. Windows/Linux objective, full-match and earned
restart steps pass. Independent Windows raw review verifies seven rounds, 120 XP,
250 offline credits and exact restart. Linux raw artifact is 47.9 MB, over the
32 MiB transfer cap; the official redirect is denied. Its figures stay CI-reported.
[Retained review](../reports/gauntlet/m1-native-ci-39712752860/README.md).

Failures: reused source-suite save data; Windows settings-resume ammo OCR; Linux
fresh W after focus release; Intel Mac default/explicit OpenGL startup at 120 s.
ARM startup/controls pass without gameplay acceptance. Local old four-size capture
failed 1280×720 touch-off OCR; other sizes passed. Preserve all original failures.

## Candidates executing; continue them

1. Layout: `/workspace/sightbreak-layout-ocr`, `codex/v1-layout-ocr`. Candidate `afe7b54` uses an aspect-correct narrow footer strip, retaining all words/exclusions/timeouts. Earlier `3a847af` native 1280 touch pass exposed a 1280×800 pixel limitation; afe fixes it. Full native four-size run is executing with original 520/120 s limits. New fresh critic reviews actual outputs. Integrate reviewed commits `931a35c`, `3a847af`, `ebf301d`, `afe7b54` and later evidence only after checking exact hashes/results.
2. Offline observer: `/workspace/sightbreak-offline-flow`, `codex/v1-offline-flow-observation`, commits `94dc6bb` → `ccfba93` → `0a12135`. Narrow ammo OCR and read-only release-guard acknowledgment. Source/pixel checks and strict native focus-only probe pass (58.943 s, fresh movement 0.427778 m, clean exit). Full local journey still fails its unchanged 35 s second-round wait under software rendering. Fresh critic is reviewing; no full journey or new Windows pass yet.
3. F2 authority order: `/workspace/sightbreak-v1-fair-tick`, `codex/v1-authority-tick-fairness`, based on 6a. Real engine baseline: first processed actor wins all 32 mirrored duels; insertion reversal reverses winners; moving target uses inconsistent geometry. Candidate separates movement/actions and defers hits. Correctness checks pass so far; measured CPU overhead exceeds its investigation threshold and is being investigated. Needs independent critic and regressions before integration. No invented kill-credit or simultaneous-wipe policy.
4. Separate Claude-owned [PR26](https://github.com/calebaiken/sightbreak/pull/26), `claude/relay-yard-tactical-layout-v1` at `5288a69`, is not integrated. Its map changes require protocol/build compatibility and native route review. Do not edit arena/bot files concurrently or blindly import the newer bot rewrite.
5. After reviewed observer integration, commit a clean candidate and dispatch registered `desktop-alpha.yml` on the own branch. Verify nine suites on actual Windows/Mac, unchanged offline journeys, objective/full-match/progression and four-size captures. Download/review bounded receipts and Mac attribution. If one Mac ablation succeeds while full fails, repeat a warm full reference before choosing a shipping correction.
6. Mobile preservation: detached `/workspace/sightbreak-v1-mobile6a` exists but no new mobile export ran yet. After native render window releases, export Android/iOS from a clean exact candidate using cached templates/state at `/workspace/sightbreak/.local`; no secret contents need reading. Inspect packages; physical devices/Xcode remain unavailable.

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
