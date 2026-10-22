# Next session

Updated 2026-10-22 by Codex. The mission is IN PROGRESS / PRIMARY, tracked by
[GitHub issue #25](https://github.com/calebaiken/sightbreak/issues/25).
No native Codex goal API is exposed; Linear requires reauthentication.

## Active state

- Branch: `codex/v1-mission-playability`; worktree: `/workspace/sightbreak-v1-execution`.
- Base: PR24 `c84eaf3ce89105d071254f0654f9adbe50275e9e`, descendant of PR23 `db3981e` → PR22 `82a03fc` → PR16 `d2439ac`.
- The existing mission/progress/quality skills were reused. G1–G20 remain the canonical acceptance matrix; the new acceptance file links that matrix.
- Current milestone: M1 Linux exported-client playability. Latest CI has offline/plant/layout failures; Windows controlled reload and Intel Mac startup also remain failed.
- No new gameplay pass is claimed at this initialization checkpoint. The retained Claude baseline and worklog remain intact.

## Continue now

1. Fetch live branches and check PR24/23 movement and other ownership before modifying shared surfaces.
2. Read AGENTS.md and the mission/acceptance matrix. Reproduce Linux exported input/plant failures against the exact base; retain failing outputs before fixing.
3. Implement the smallest supported product correction, run targeted and exported regressions, obtain a separate fresh-context critic’s review of actual outputs, improve and reverify.
4. Commit, update evidence and matrix, then immediately begin the next achievable milestone. Do not treat a roadmap or one correction as mission completion.

## Current environment commands

```sh
cd /workspace/sightbreak-v1-execution
export SIGHTBREAK_TOOLS_DIR=/workspace/tools
export SIGHTBREAK_STATE_DIR=/workspace/sightbreak-v1-execution/.local
python3 scripts/toolchain.py setup --targets linux
./scripts/godot.sh --headless --editor --import --quit
python3 scripts/export.py linux
XVFB_BIN=/workspace/tools/xvfb/usr/bin/Xvfb python3 scripts/verify_offline_match.py --target linux --scenario plant --display :181 --timeout 180 --output builds/mission-m1/plant-baseline
```

Use new evidence directories for each attempt. `/usr/local/bin/godot` is 4.6.3 and
must not substitute for the pinned 4.7.2 toolchain. Xvfb is locally available at the
path above. Software-render timing is relative, never physical-device FPS.

## External blockers

Windows/Mac gameplay and physical Android/iOS, human playtests, actual GPU timing,
Steam credentials/signing and denied CS2 reference hosts require their missing
resources. Available Linux and correctness work must continue while those remain
blocked. No background execution or future CI result is claimed.
