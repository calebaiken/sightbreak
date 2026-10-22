# Next session

Updated 2026-10-21 by Claude. A fresh session should be able to continue from this file alone.

## State

- Mission branch: `claude/mission-foundation-v1`, based on `origin/codex/desktop-playability-p1` (`db3981e`, PR #23). Draft PR target is that same branch.
- Contents: `CLAUDE.md`, `.claude/skills/{gauntlet-loop,no-ai-slop,sightbreak-gauntlet}`, `.claude/agents/*`, `.claude/settings.json` (SessionStart brief, narrow read-only permissions), `scripts/session_brief.sh`, `docs/roadmap/*`, `docs/engineering/{AUTONOMOUS_WORKLOG,NEXT_SESSION}.md`.
- Worktree used in the first session: `/home/user/wt/mission-foundation`. Toolchain: `/home/user/tools/godot-4.7.2`, state dir `/home/user/sightbreak/.local`. Neither survives a container reset; `./scripts/setup.sh` rebuilds them.
- Baseline suite result and the first player-experience milestone are in the worklog. If the worklog has no M1 result, the run did not finish: re-run it.

## Do next, in order

1. `git fetch origin` and check whether PR #23 or any of #16-#22 moved. If the base moved, merge it into your branch (no rebase, no force-push) and re-run the targeted tests.
2. Recheck reference hosts (`docs/roadmap/BARS.md`). If `*.steamstatic.com` or `youtube.com` now answer, fetch the CS2 references first, record URL, date and SHA-256, and start the viewmodel gauntlet against B1.
3. Take the top open row of the acceptance matrix in `docs/roadmap/SIGHTBREAK_V1_PROGRESS.md`. Current order: G4/G5 gunplay and viewmodel measurement and the three procedural weapons, then G7 UI journeys, then G2 bots (review the newer Gemini tip first).
4. Run it through `.claude/skills/sightbreak-gauntlet`: builder agent, native capture, blind pair, `harsh-critic` with fresh context, regression suite.
5. Append to the worklog, update the matrix, commit, push with `git push -u origin <branch>`.

## Commands

```sh
export SIGHTBREAK_TOOLS_DIR=/home/user/tools SIGHTBREAK_STATE_DIR=/home/user/sightbreak/.local
./scripts/setup.sh && ./scripts/godot.sh --headless --editor --import --quit
Xvfb :99 -screen 0 1920x1080x24 +extension GLX +render -noreset &
DISPLAY=:99 ./scripts/validate.sh 2>&1 | tee /tmp/validate.log
```

## Evidence locations

- Gauntlet rounds: `docs/reports/gauntlet/<milestone>/round-<n>/` (with `sha256.txt`).
- Baseline log of the first session: summarized in the worklog; the raw log lived in the session scratchpad and is not preserved unless the worklog says where it was copied.

## Blocked on the owner

- Allow the reference hosts in the cloud environment's network settings (`BARS.md`) for CS2 comparison.
- Human playtesters, Mac and Windows hardware, physical Android and iPhone, Steam account actions and signing are outside this container.
