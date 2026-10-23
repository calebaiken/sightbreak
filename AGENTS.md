# SIGHTBREAK mission instructions for Codex

The primary continuing goal is **SIGHTBREAK — Steam-Ready v1.0**, IN PROGRESS.
Read and continue the existing mission; do not stop because one task, PR or milestone
finished. The goal is complete only when all defined RC acceptance gates are
independently verified. The owner’s latest instructions take precedence.

Read first:

1. `docs/engineering/NEXT_SESSION.md` for branch, exact source, commands and failures.
2. `docs/roadmap/SIGHTBREAK_V1_MISSION.md` for goal, constraints and dependency roadmap.
3. `docs/roadmap/SIGHTBREAK_V1_PROGRESS.md` and `SIGHTBREAK_V1_ACCEPTANCE.md` in that directory for the existing G1–G20 matrix.
4. `CLAUDE.md`, `docs/engineering/PARALLEL_WORK.md`, open PRs and relevant QA/device reports for contributor ownership and contracts. Historical branch identities must be rechecked live.
5. Both original `.claude/skills/gauntlet-loop/SKILL.md` and `.claude/skills/no-ai-slop/SKILL.md`, including its `eval.md`, before substantive development. These are already installed; verify and reuse them.

Use the existing `.claude/skills/sightbreak-gauntlet/SKILL.md` as the project workflow,
implemented with supported Codex tools and `collaboration.spawn_agent` critics with
`fork_turns: "none"`. Claude slash commands and named agent types are not assumed.
Declare real inspected benchmarks and measurable gates before each substantial
component. Retain native outputs, test results, failed iterations, comparison
verdicts, biggest remaining deficiency and fixes. Blind A/B only when comparable.
The builder cannot approve its own work. Keep unsupported criteria blocked.

Preserve Godot 4.7.2, protocol 6, opt-in prediction, live rewind off, state privacy,
authoritative gameplay/economy, earned-only currency and offline/online boundaries.
Use your own branch/worktree; preserve ownership, PR dependencies and other authors’
branches. No force-push, protected/shared merge, production deployment, Steam
publication, paid expense or live-credential changes without separate authorization.

After each verified increment, update the mission/evidence, commit recoverable
changes, reassess blockers, choose and begin the next highest-impact milestone.
If execution must end, update NEXT_SESSION with branch/commit, incomplete changes,
failing tests, blockers and exact next commands. Never claim background execution.
Apply No AI Slop to player-facing copy and project communications while preserving
SIGHTBREAK terminology, accessibility, meaning and precision.

# Workspace size and recovery

The report tree is large. Create new worktrees with `--no-checkout`, select
sparse code/instruction paths and the specific component report directories,
then populate only that new empty own checkout at the exact base. Avoid the
whole gauntlet directory by default. Preserve existing worktrees, ignored raw
outputs and HEADs when omitting tracked copies to recover storage.

Full aggregate validation also needs the tracked
`docs/reports/media/art-v9/hands/logs` fixtures. Saved layout OCR tests need
`docs/reports/gauntlet/native-layout-ocr`. A missing sparse fixture is a retained
setup failure; restore the exact tracked files and use fresh evidence output.
Do not skip the check or reinterpret that failure as passing.

After an executor interruption, inspect actual local HEAD/status before fetching
or integrating recovery notes. The last observed local root may contain unpushed
commits. Never reset it to the older remote head.
