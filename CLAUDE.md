# SIGHTBREAK: instructions for Claude Code

## Mission (permanent)

Take SIGHTBREAK, a native Godot 4.7.2 tactical 5v5 FPS, to a verified v1.0 release candidate: excellent gunplay, readable UI, credible weapons and animation, good offline bots, authoritative multiplayer, native Windows/macOS/Linux packages, Android/iOS kept building, and a safe Steam staging procedure. Counter-Strike 2 is the genre-quality reference. Identity, assets and mechanics stay original.

The mission survives across sessions. Do not stop because one task finished: pick the next unfinished milestone from the roadmap. If the session must end, commit and update `docs/engineering/NEXT_SESSION.md` first.

## Read first

1. `docs/engineering/NEXT_SESSION.md` - exact resume point.
2. `docs/roadmap/SIGHTBREAK_V1_PROGRESS.md` - acceptance matrix and open gaps. This is the authoritative roadmap.
3. `docs/roadmap/SIGHTBREAK_V1_MISSION.md` - goals, gates, constraints.
4. `docs/engineering/PARALLEL_WORK.md` - who owns what. Codex leans toward network, backend, native platform and build tooling. Claude leans toward gunplay, UI/UX, visuals, animation, audio feel, bots and independent criticism. These are preferences; read the current state before choosing work.

## Hard constraints

- Godot 4.7.2 only (pinned in `scripts/toolchain.py`). Protocol 6. Prediction stays opt-in, live rewind stays off, state privacy and account/inventory authorization stay intact. Earned-only economy; no real-money features.
- Work on your own branch and worktree (`claude/<topic>`), draft PRs only, stacked on the dependency they need. Never force-push or rewrite a shared branch, never merge unverified work, never edit another agent's branch. Push with `git push -u origin <your-branch>` explicitly; a bare `git push` may target the wrong upstream.
- No publishing, paid services, credentials, signing or Steam uploads without the owner's explicit approval.
- `IMPLEMENTED` is not `VERIFIED`. Untested stays `UNVERIFIED`. Report failures with their output. Never weaken or skip a test to get green.

## Quality process

- Every player-experience deliverable goes through `.claude/skills/sightbreak-gauntlet` (built on the vendored `gauntlet-loop`): real bar, native capture, a separate `harsh-critic` with fresh context, blind A/B where possible, measurable gates beside taste.
- The builder never certifies its own work. Agent roles are in `.claude/agents/`.
- Player-facing text, docs and release notes go through `.claude/skills/no-ai-slop` (see `docs/roadmap/COPY_STYLE.md`). That skill judges writing only, not visuals.
- Reference footage hosts (Steam, YouTube, counter-strike.net) were denied by the network policy on 2026-10-21. Do not fabricate comparisons; mark those gates `BLOCKED EXTERNALLY`. Recheck at session start with `docs/roadmap/BARS.md`.

## Commands

```sh
export SIGHTBREAK_TOOLS_DIR=/home/user/tools SIGHTBREAK_STATE_DIR=/home/user/sightbreak/.local
./scripts/setup.sh                      # pinned Godot + templates (checksum verified)
./scripts/godot.sh --headless --editor --import --quit
Xvfb :99 -screen 0 1920x1080x24 +extension GLX +render -noreset &   # native rendered tests
DISPLAY=:99 ./scripts/validate.sh       # full maintained suite (long)
./scripts/export.sh linux               # native package
```

Software rendering (llvmpipe) gives relative timings only. Never present it as device FPS.

## Operating notes (learned the hard way)

- A GDScript compile error makes `--headless --script` hang instead of failing. Run every test under `timeout`.
- Never edit `game/` files while a measurement run is going: each match loads the scripts when it starts, so a run that spans an edit mixes two builds. Stop it, then restart.
- Never `pkill -f` / `pgrep -f` a pattern that also appears in your own command line; the wrapper shell matches and dies (exit 144). Put the kill in a script file, or match on a pid.
- Look at pair-level properties, not only averages. A rotating tick order gave every actor an equal lead and still left ids 5 and 6 in order 90% of the time.
- A subagent that recomputes your numbers is worth running before the write-up, not after: it changed three of the claims in the fairness record.
