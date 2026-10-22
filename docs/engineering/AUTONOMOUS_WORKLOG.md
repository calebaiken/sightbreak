# Autonomous worklog

Chronological record of what Claude did on the SIGHTBREAK v1.0 mission: investigations, decisions, failed experiments, tests, reviews and source revisions. Newest entry last. Results in the acceptance matrix ([SIGHTBREAK_V1_PROGRESS.md](../roadmap/SIGHTBREAK_V1_PROGRESS.md)) must trace back to an entry here.

## 2026-10-21 - Session 1: orientation and M0

**Environment.** Claude Code cloud container, Linux x86_64, 4 vCPU, 15 GB RAM, no GPU, no audio device. Present: Xvfb, ffmpeg, Python 3, Node 22. Installed this session: pinned Godot 4.7.2 and export templates through `scripts/setup.sh` (SHA-512 verified by the script) into `/home/user/tools/godot-4.7.2`, state in `/home/user/sightbreak/.local`.

**Repository state found.** Local clone had only `main` (`4d8cdb3`). `git fetch` of the stacked branches and `git merge-base --is-ancestor` checks gave the map in the progress file. The newest integrated line is PR #23 `codex/desktop-playability-p1` (`db3981e`, 216 commits over `e67f2c8`), which contains PRs #1, #2 (through `ed85754`), #12, #14 (frozen `d66e72c`), #16 and #22. It does not contain PR #17, PRs #18-#21, the nine newest commits of PR #2 (including `scripts/ab_pair.py`) or the newer tip of PR #14.

**Decision: base.** Work stacks on `codex/desktop-playability-p1`, matching the repo convention that each draft PR targets its dependency. Branch `claude/mission-foundation-v1`, worktree `/home/user/wt/mission-foundation`. The upstream was unset after creation so a bare `git push` cannot reach Codex's branch.

**Skills.** Cloned `robonuggets/gauntlet-loop` (`9b1975a`, CC BY 4.0) and `petergyang/no-ai-slop` (`000650b`, MIT). Read both in full: markdown only, no scripts, installers or network calls. Copied the skill files and licenses unchanged into `.claude/skills/` with `PROVENANCE.md` carrying commit, license and SHA-256. Upstream `gauntlet-loop` only writes a prompt, so `.claude/skills/sightbreak-gauntlet` was added to run the loop with real captures, blind pairs and a fresh-context critic.

**Claude Code capabilities checked.** `/loop` exists as a skill in this environment. No `/goal` or `ultracode` command was found in the skill list, so neither is used or assumed. Subagents work through the `Agent` tool; project agents in `.claude/agents/` load in future sessions. `SessionStart` hook added with a read-only brief script.

**Reference footage.** Fetch attempts to `store.steampowered.com`, `cdn.akamai.steamstatic.com`, `shared.akamai.steamstatic.com`, `cdn.cloudflare.steamstatic.com`, `steamcdn-a.akamaihd.net`, `www.youtube.com`, `i.ytimg.com`, `upload.wikimedia.org`, `counter-strike.net` and `partner.steamgames.com` all failed with a 403 on the proxy `CONNECT`. `raw.githubusercontent.com` works. Earlier Claude and Codex sessions recorded the same wall. Consequence: G18 is `BLOCKED EXTERNALLY` and no CS2 comparison is claimed anywhere. Bars B3 (previous build), B4 (WCAG contrast) and B5 (relative timing) stay usable.

**Gun data read.** `game/scripts/gameplay/weapons.gd` defines four weapons (interval in s, so Kestrel 9 semi 0.23, Vectorline 0.085 auto, Relay AR 0.105 auto, Longwatch 0.82 semi). `actor.gd:728-758`: spread is uniform random per axis around the aim; recoil climbs pitch by `spec.recoil` per shot up to 0.16 rad, adds a deterministic horizontal term `sin(shot_index * 1.7) * recoil * 0.55`, and recovers at 0.11 rad/s. Only the Relay AR has authored meshes and rigged arms; the other three are procedural.

**Baseline run.** `scripts/validate.sh` started on `db3981e` under Xvfb with `DISPLAY=:99`. Result recorded in the next entry.
