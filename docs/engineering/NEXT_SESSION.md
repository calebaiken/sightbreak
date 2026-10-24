# Next session

Updated 2026-10-24 (after the G22 qualification and the graphics tiers and impacts milestones) by Claude. A fresh session should be able to continue from this file alone.

## State

- Stack: `codex/desktop-playability-p1` (PR #23, `db3981e`) <- `claude/mission-foundation-v1` (draft PR #24: skills, agents, records, session brief) <- `claude/relay-yard-tactical-layout-v1` (draft PR #26: Relay Yard layout revision 2, measurement tools, evidence). Separately, off the Codex base: `claude/fair-actor-order-v1` (draft PR #28: tick-order shuffle and squad-symmetric bot habits, finding F2). Push with `git push -u origin <branch>` explicitly; the worktrees' upstreams are unset on purpose.
- Done and verified here: native baseline of PR #23 (full suite, no failures); Relay Yard layout revision 2 (full suite exit 0, four blind critic rounds won, data independently recomputed). Details: worklog entries "Session 1" and `docs/design/RELAY_YARD_LAYOUT.md`.
- Open defects found: **F2 is fixed on PR #28 and waits for Codex review** (ids 1-5 won 71% of normal rounds; the fixed build gives 49.9%, interval 46.8% to 53.1%, over 72 matches; hard is unresolved at 24 matches), hard difficulty rarely plants, sites bare, no long lane or elevation, mixed-layout handshake gap, native plant scenario route unverified. On the unchanged pad attackers win about a quarter of normal rounds; the layout's 59% and 67% were confounded and need re-measuring.
- Worktrees used in session 1: `/home/user/wt/mission-foundation`, `/home/user/wt/layout`, `/home/user/wt/fair`. Toolchain `/home/user/tools/godot-4.7.2`, state dir `/home/user/sightbreak/.local`. None survives a container reset; `./scripts/setup.sh` rebuilds them. Xvfb: `Xvfb :99 -screen 0 1920x1080x24 +extension GLX +render -noreset &`.

## Session 2 additions (2026-10-24)

- Stacked draft PRs off `codex/v1-mission-playability` (PR #27): #33 `claude/gunplay-v1-stack` (gunplay measurements, no game code), #34 `claude/g22-qualify-two-phase-v1` (squad-share qualification, evidence only), #35 `claude/graphics-tiers-v1` (four graphics tiers, shadow fill, capture tool, `docs/art/GRAPHICS_BACKLOG.md`), and #36 `claude/combat-impact-vfx-v1` (stacked on #35: surface-aware impacts and bullet holes). Worktrees `/home/user/wt/gunplay2`, `qualify`, `gfx`, `vfx`. PR #28 is superseded for authority code (comment posted); its evidence stays.
- The graphics ranked defect list, the measured renderer facts (what Compatibility does and does not do on 4.7.2) and the next graphics steps are in `docs/art/GRAPHICS_BACKLOG.md` on #35. Read it before touching lighting or effects. Rules learned: any post effect switches Compatibility to a post pass; shadow blur and the soft-shadow level do nothing; lit particles render about three times brighter than their tint; set every `MultiMesh.use_colors` before the instance count.
- Graphics next, in order: operator-in-shadow readability capture; skyline behind the attacker-end wall and a softer sun disc; crate-top albedo (MEDIUM clips 2.8% in view 11), crane cable thickness, floor moiré; tracers and muzzle flash; weapon art for the three procedural weapons (G5; partial generators `tools/art/kestrel_9.py` and `vectorline.py` live uncommitted in `/home/user/wt/art`); LightmapGI needs a GPU machine; device frame-time baselines.
- Shell notes: set `SIGHTBREAK_TOOLS_DIR=/home/user/tools` (the default path does not exist), `DISPLAY=:99` for rendering suites, and never `sleep` in the foreground; wait on a background `until` loop.

## Do next, in order

1. `git fetch origin`; check whether PR #23, #24 or any of #16-#22 moved. If the base moved, merge it into your branch (no rebase, no force-push) and re-run `./scripts/validate.sh`.
2. Recheck the reference hosts (`docs/roadmap/BARS.md`). If `*.steamstatic.com` or `youtube.com` now answer, fetch the CS2 references first, record URL, date and SHA-256 and start the viewmodel gauntlet against bar B1.
3. **F2 follow-up.** Check PR #28 for review comments from Codex. Once it merges (or the stack is integrated), merge the base into the layout branch and re-measure layout side balance and pacing with `scripts/measure_relay_yard.sh ... --both-starts` plus `scripts/squad_balance.py` (the 59% and 67% attacker wins were confounded). For hard difficulty run at least 72 matches before claiming anything.
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
