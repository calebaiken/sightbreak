# Next session

Updated 2026-10-22 by Claude. A fresh session should be able to continue from this file alone.

## State

- Stack: `codex/desktop-playability-p1` (PR #23, `db3981e`) <- `claude/mission-foundation-v1` (draft PR #24: skills, agents, records, session brief) <- `claude/relay-yard-tactical-layout-v1` (draft PR: Relay Yard layout revision 2, measurement tools, evidence). Push with `git push -u origin <branch>` explicitly; the worktrees' upstreams are unset on purpose.
- Done and verified here: native baseline of PR #23 (full suite, no failures); Relay Yard layout revision 2 (full suite exit 0, four blind critic rounds won, data independently recomputed). Details: worklog entries "Session 1" and `docs/design/RELAY_YARD_LAYOUT.md`.
- Open defects found: **F2** (actors 1-5 win 71% of bot rounds in either role, from the id-ordered authoritative tick), hard difficulty rarely plants, sites bare, no long lane or elevation, mixed-layout handshake gap, native plant scenario route unverified.
- Worktrees used in session 1: `/home/user/wt/mission-foundation`, `/home/user/wt/layout`. Toolchain `/home/user/tools/godot-4.7.2`, state dir `/home/user/sightbreak/.local`. None survives a container reset; `./scripts/setup.sh` rebuilds them. Xvfb: `Xvfb :99 -screen 0 1920x1080x24 +extension GLX +render -noreset &`.

## Do next, in order

1. `git fetch origin`; check whether PR #23, #24 or any of #16-#22 moved. If the base moved, merge it into your branch (no rebase, no force-push) and re-run `./scripts/validate.sh`.
2. Recheck the reference hosts (`docs/roadmap/BARS.md`). If `*.steamstatic.com` or `youtube.com` now answer, fetch the CS2 references first, record URL, date and SHA-256 and start the viewmodel gauntlet against bar B1.
3. **Fix F2.** Branch `claude/fair-actor-order-v1` off `codex/desktop-playability-p1`. In `match.gd` `_authority_tick`, process actors in a rotating or shuffled order each tick (deterministic from the tick or the match RNG). Add a regression test, then run `scripts/measure_relay_yard.sh ... --both-starts` and `bot_objective_metrics.gd --reverse-order`: ids 1-5 should win about half. Shared authority code: write the PR so Codex can review it quickly and say so in the PR text.
4. Weapon and viewmodel gauntlet (G4, G5): run `game/tests/presentation_gallery_capture.gd` (written, never run) to capture all four weapons and the operators in identical views; critic round; measurable fire/recoil/reload harness. Only the Relay AR has authored art.
5. Layout follow-ups from `docs/design/RELAY_YARD_LAYOUT.md` "Next": site structure, hard-difficulty tactics, a long lane, visual polish.
6. HUD and menu journeys (G7) at 1280x720, 1920x1080, 960x720, 1560x720.
7. After each: append to `AUTONOMOUS_WORKLOG.md`, update the matrix in `SIGHTBREAK_V1_PROGRESS.md`, commit, push, draft PR.

## Commands

```sh
export SIGHTBREAK_TOOLS_DIR=/home/user/tools SIGHTBREAK_STATE_DIR=/home/user/sightbreak/.local
./scripts/setup.sh && ./scripts/godot.sh --headless --editor --import --quit
DISPLAY=:99 ./scripts/validate.sh 2>&1 | tee /tmp/validate.log        # about 12 minutes
DISPLAY=:99 scripts/measure_relay_yard.sh out/yard --both-starts --seeds "41 42 43 44 45 46" --difficulties "normal hard" --jobs 4
```

A script compile error makes a `--headless --script` run hang rather than fail. Always use `timeout`.

## Evidence locations

- `docs/reports/gauntlet/relay-yard-layout/` (images, raw bot logs, sightline output, critic and data reviews, `sha256.txt`).
- Baseline logs of PR #23 were summarized in the worklog; the raw per-suite logs stayed in the session's worktree under `.local/validation` (gitignored).

## Blocked on the owner

- Allow the reference hosts in the cloud environment's network settings (`BARS.md`) for CS2 comparison.
- Human playtesters, Mac and Windows hardware, physical Android and iPhone, Steam account actions and signing are outside this container.
- Codex to confirm: the native plant scenario route (`scripts/verify_offline_match.py`), and how mixed layouts should be rejected at the handshake.
