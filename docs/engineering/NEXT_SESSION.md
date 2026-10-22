# Next session

Updated 2026-10-22 by Codex. **SIGHTBREAK — Steam-Ready v1.0** remains
IN PROGRESS / PRIMARY, tracked by [issue #25](https://github.com/calebaiken/sightbreak/issues/25).
No native Codex goal API is exposed; Linear requires reauthentication. Continue
product work, not setup. Original quality skills are already installed and verified.

## Active source and evidence

- Main worktree `/workspace/sightbreak-v1-execution`, branch `codex/v1-mission-playability`.
- Base PR24 `c84eaf3` → PR23 `db3981e` → PR22 `82a03fc` → PR16 `d2439ac`. Fetch live refs/PRs before integration. No shared merge or branch rewrite was made.
- Last frozen integrated export/test commit: **`6a0d8d5d85b4fb37943903886982f51b4ed230b0`**. Later commits retain evidence/docs only until the next implementation is explicitly integrated.
- Game tree `13079ab8a3de9b18252a652ed57157e0776cf394`; shipping SHA256 `954b0a73cff89483a9270434da7902b2d128f1b9a99c30290dfe03862c038873`; validation SHA256 `9155b9c6a68fbeb459c4d0654b49ec4b250d1e11bea667747dfc4056e1ea2f03`.
- Linux ELF at `builds/mission-m1/candidate-build/linux/SIGHTBREAK.x86_64`, SHA256 `ef4ab16a1b7f13fe96822a102c139fb5964275701f1e92fe8bdcfacfbf29d9a4`. Check receipt for exact filename; never re-attest this binary to a newer HEAD.
- Commits: mission `561d0cb`, menu `8de7331` + UID `aa0b0a4`, objective observer `44cb081`, X11 lifetime `2e158e2`, replay clock `0917771`; evidence `954c1d7` and `bcdc93a`.

## Verified increments and open failures

- Fresh native Linux baseline planting failed movement settling. Candidate plant r2 passes 124.299 s and defuse 103.392 s with original 15 s approach and 3/5 simulation-second holds. Separate critic recomputed raw neutral ticks, identity, restart, process cleanup. r1 sampler gap retained; r2 resolves it. Helper has a retained queued-pulse counterexample at 1.5 simulation-second delivery delay, beyond tested 0–0.2 envelope; do not claim universal robustness.
- FIELD MENU keyboard focus independently passes actual OS Tab/Shift-Tab/Return and safe focus recovery. [Verbatim review/archive](../reports/gauntlet/m1-menu-focus/INDEPENDENT_ARCHIVE.md).
- Nine actual X11 lifetime cases pass independently versus fatal baseline. Four-size exported layout run FAILS 1280×720 touch-off OCR; other three sizes pass. Actual whole 289.346 s, unchanged 120 s per case, configured whole 600 vs original 520. Preserve failure; no complete layout/visual acceptance.
- Integrated `validate.sh` exit 0, 16,355 reported checks, `.local/validation/run-as4Oaj`. Bot F1 persists: no plant in 12-round lifecycle. Rendered reload visibility and Windows-specific cases skipped, backendSQL not run. Separate catalog drift check matches 29 definitions.
- Replay freshness native blind comparison 8/8 vs 4/8, eight snapshot-gap trials 316–334 ms within 350 ms. Separate source/output/repeat critics; same-host 16 ms minimum margin. [Evidence](../reports/gauntlet/m3-input-freshness/RESULTS.md). Full G3 ten-client and remaining PR18/19/21/V3 are not qualified.
- Current desktopCI [39712752860](https://github.com/calebaiken/sightbreak/actions/runs/39712752860) exact 6a: Windows/Linux plant,defuse,full-stock match,earned restart steps pass, independent rawreceipt review underway. Overall jobs FAIL: shared suite save data and ordinary offline flow OCR. Intel Mac default/explicitOpenGL120 s startup fails; ARM startup/controls pass without gameplay.

## Work already executing; continue without restarting the roadmap

1. Suite isolation builder: `/workspace/sightbreak-ci-isolation`, `codex/v1-native-test-isolation`, based 6a. Real local shared-save failure reproduced; three suites pass unique engine-reported paths. Final commit/review pending. Do not remove fresh-save guard. Obtain fresh independent review; run actual Windows/macOS CI on integrated candidate.
2. Layout OCR builder: `/workspace/sightbreak-layout-ocr`, `codex/v1-layout-ocr`, based 6a. Diagnose actual tiny desktop footer false negative aftertouch-off. Preserve actual rendered proof and wrong-screen/touch negative controls; no timeout increase or state-only acceptance.
3. Ordinary offline flow builder: `/workspace/sightbreak-offline-flow`, `codex/v1-offline-flow-observation`. Current Windows settings-resume screenshot visibly has ammo but OCR garbles region. Coordinate overlapping observation helpers with layout builder. Preserve native gates and review currentLinux artifact too.
4. Intel Mac builder: `/workspace/sightbreak-macos-render`, `codex/v1-macos-render`. QA ZIP `/workspace/attachments/a85df036-caeb-45f0-91f7-ef4d8fb0712e/github-actions-artifact-12398461742.zip`, SHA256 `c3179d25d87cce7030bc3d9c9700990094d799eb8610df221e38a8e321b5b8a5`. At 90 s main thread is active Apple Software Renderer fragment rasterization in glDrawElementsInstanced; not proven script deadlock. Controlled scene-feature diagnostic being implemented; shipping graphics/timeouts unchanged.
5. Independent native critic is reviewing currentCI rawfull-match/objective/failure receipts. Local critic report finalized in `builds/mission-m1/native-independent-review.md`. Native evidence archivist is preserving these under `docs/reports/gauntlet/m1-exported-validation` on ownbranch. Never substitute a builder verdict.
6. Integrate only reviewed candidates, test source-bound frozen candidate in fresh output dirs, update G1–G20, commit/push ownbranch, create/update draftPR targeting `claude/mission-foundation-v1`. Then immediately select and execute the next release blocker.

## Reproduction and tool constraints

```sh
cd /workspace/sightbreak-v1-execution
git fetch origin '+refs/heads/*:refs/remotes/origin/*'
export SIGHTBREAK_TOOLS_DIR=/workspace/tools
export SIGHTBREAK_STATE_DIR=/workspace/sightbreak-v1-execution/.local
./scripts/validate.sh
```

Use a clean isolated checkout at the exact intended commit for native export and
validation. Use a NEW `SIGHTBREAK_BUILDS_DIR`; export refuses existing artifacts,
and validators reject a dirty or changed source/validation fingerprint. Do not
commit/edit while a validator is checking exact HEAD. Pinned Godot is 4.7.2 via
`scripts/godot.sh`; `/usr/local/bin/godot` is 4.6.3 and wrong.

```sh
SIGHTBREAK_BUILDS_DIR="$PWD/builds/new-frozen-run" python3 scripts/export.py linux
SIGHTBREAK_BUILDS_DIR="$PWD/builds/new-frozen-run" XVFB_BIN=/workspace/tools/xvfb/usr/bin/Xvfb LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=2 python3 scripts/verify_offline_match.py --target linux --scenario plant --display :181 --timeout 180 --output builds/new-plant
```

Start the
read-only raw status retention watcher BEFORE launching if independently proving
exact settled ticks. Previous raw watcher is `builds/mission-m1/retain_status.py`.
Use fresh X displays and reap owned groups. CurrentCI export on 6a was dispatched
with `gh workflow run desktop-alpha.yml --repo calebaiken/sightbreak --ref codex/v1-mission-playability`.

## External blockers

CS2 reference hosts still return proxy CONNECT 403; actual reference parity is
unverified. No physical GPU/device, human gameplay/listening review, or physical
controller is available here. Steam signing/credentials/publication remain separate
owner actions. Native GitHub Windows/Mac runners are available for authorized CI
and should be used; do not label all platform work impossible because local host is
Linux. No execution is promised after the session ends. The mission is unfinished.
