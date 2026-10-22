---
name: sightbreak-gauntlet
description: Runs the builder/critic gauntlet loop on one SIGHTBREAK deliverable (a weapon animation, HUD element, menu, bot behavior, sound, map area). Use when starting or reviewing any player-experience milestone, before calling subjective work done, or when asked to "gauntlet" something in this repo. The upstream gauntlet-loop skill only writes the prompt; this one runs it with real captures.
---

# SIGHTBREAK gauntlet

Upstream `gauntlet-loop` (vendored beside this file) defines the idea: a real bar, small pieces, a builder and a separate harsh critic, a blind pick, no round-count exit. This skill makes that executable here.

## 1. Pick one piece

One piece is something a critic can judge alone from files: the rifle reload, the buy menu at 1280x720, the scoreboard, Relay Yard A-site sightlines, defender rotations in a recorded match. Not "the HUD" and not "the game".

## 2. Set the bar, then fetch it

A bar must be named, fetchable from this container and comparable side by side. Check `docs/roadmap/BARS.md` first, then add yours.

- Try to fetch before you promise anything. Known state on 2026-10-21: `store.steampowered.com`, `*.steamstatic.com`, `youtube.com`, `i.ytimg.com` and `counter-strike.net` are denied by the network policy. `github.com` and `raw.githubusercontent.com` work.
- If the named bar cannot be fetched, mark the gate `BLOCKED EXTERNALLY` with the host and stop treating it as a comparison. Do not describe a game from memory and compare against the description.
- Work that can still proceed: the measurable half (frame time, input-to-photon, clipping px, contrast ratio, reload duration), the previous verified build as a regression bar, and rule compliance. A win against the previous build proves improvement, not parity with a shipped title. Say which one you ran.
- Never commit third-party game footage or screenshots. Keep them out of the repo; record URL, retrieval date and SHA-256 in `docs/roadmap/BARS.md`.

## 3. Capture real output

Native build only. Display and flags:

```sh
export SIGHTBREAK_TOOLS_DIR=/home/user/tools SIGHTBREAK_STATE_DIR=/home/user/sightbreak/.local
Xvfb :99 -screen 0 1920x1080x24 +extension GLX +render -noreset &
DISPLAY=:99 ./scripts/godot.sh --audio-driver Dummy --rendering-method gl_compatibility --resolution 1280x720 --script res://tests/<capture>.gd -- --capture-dir=<dir>
```

Rendering is Mesa llvmpipe. Timings are relative only and never count as device FPS. Store evidence under `docs/reports/gauntlet/<milestone>/round-<n>/` with `sha256.txt` and the source commit. Keep failed rounds.

## 4. Blind pair

Build pairs with `scripts/ab_pair.py` (ours vs bar, or ours-new vs ours-old). The key file stays outside the folder the critic can read.

## 5. Critic in a fresh context

Spawn `harsh-critic` (read-only) with only: the paths to the A/B files, the question, and the measurable results. Do not tell it which side is ours, how long the builder worked or what changed. Required reply:

1. Winner, A or B, and why in two sentences.
2. The single largest remaining gap.
3. Any regression or correctness failure visible in the files.
4. Anything it could not judge from the evidence.

A critic score out of 10 can be recorded but never closes a gate alone.

## 6. Revise and exit

Return findings to the builder as evidence (file, region, number). The builder fixes, the pair is rebuilt with a new seed, the critic is a new instance. Exit when all hold:

- the blind pick goes to ours against a bar that was actually fetched, or the gate is `BLOCKED EXTERNALLY` with a handoff;
- measurable gates pass and `./scripts/validate.sh` shows no new failure;
- no accessibility, correctness or performance regression, whatever the picture looks like.

Stop on a real blocker or when the session must end. Write the state to `docs/engineering/NEXT_SESSION.md` first.

## 7. Record

Append the round to `docs/engineering/AUTONOMOUS_WORKLOG.md`: piece, bar and how it was fetched, source commit, commands, verdicts, the open gap. Update the matrix row in `docs/roadmap/SIGHTBREAK_V1_PROGRESS.md`. `IMPLEMENTED` is not `VERIFIED`.
