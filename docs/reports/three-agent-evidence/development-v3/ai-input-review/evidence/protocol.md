# Independent native bot QA protocol

## Fixed inputs and boundaries

- Baseline: frozen V2 `701ce2c` (resolve full commit in sealed manifest).
- Candidate: exact PR14 input `48eb0586e273f96dc20b346ed444d00ab0f3ac30`.
- Recovery source for retained probes: `d2439ac:docs/reports/three-agent-evidence/stabilization-v2/ai/` via byte-preserving `git show`.
- Engine: approved native Windows `Godot_v4.7.2-stable_win64.exe`; record executable SHA256 and `--version`.
- Separate detached `sol-ai-north-20261019` / `sol-ai-south-20261019` worktrees, random mapping. No owner/integration source edits, commits, or remote posts.
- Complete editor imports on both before any probe run. External GDScript tests launched with `--headless --path <frozen worktree>/game --script <absolute external probe>`.
- Runtime-only fixtures/mocks are permissible for isolating API effects, but distinguish them from production integration. No Python behavior simulation.

## Ordering and evidence rules

1. Recover/read retained V2 test scripts, not candidate claims.
2. Run retained scripts unchanged against both opaque labels; preserve exit codes and both output streams, including failures.
3. Compare neutral output and write an initial neutral assessment before reading source mapping/diff or candidate claims.
4. Inspect exact source for causal explanations; add native external probes for uncovered anchor arrival, 18 m hearing bypass, damage priority, `sound_noise`, equipment, API, and authority contracts.
5. Repeat decisive cases and record limitations. Source inspection is not a substitute for a native runtime result.
6. Preserve full command argument arrays, working directories, raw output hashes, test sources, tree identifiers, import failures, and final clean-status checks outside sources.

## Acceptance lens

- Evidence of improvement must be native and discriminate between the two frozen inputs, or identify a shared pre-existing gap explicitly.
- No new authority/API regression is acceptable merely because a behavior probe passes.
- Hearing, damage response, and objective movement must be assessed through production call paths when possible; helper-only probes are insufficient to establish integration.
- Sound events must be emitted/received using the actual production contract; equipment must respect actual item/lifecycle/API constraints.
- A process exit of zero is not proof of success if Godot logs script/resource errors. Read stdout and stderr.
- Largest remaining gap means strongest reproducible gameplay/source-contract failure, not the most extensive refactor opportunity.
- This is an independent same-model agent review, not human playtesting/acceptance or a claim that all multiplayer/platform behavior passes.
