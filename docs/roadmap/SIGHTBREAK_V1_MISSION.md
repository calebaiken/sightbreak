# SIGHTBREAK v1.0 mission

This file holds the goal, the gates and the constraints. Current status lives in [SIGHTBREAK_V1_PROGRESS.md](SIGHTBREAK_V1_PROGRESS.md). The resume point lives in [../engineering/NEXT_SESSION.md](../engineering/NEXT_SESSION.md).

## Goal

Ship a Steam-ready v1.0 release candidate of SIGHTBREAK: a native Godot 4.7.2 tactical 5v5 first-person shooter with the responsiveness, gameplay depth, presentation, reliability and competitive integrity of an excellent tactical FPS. Counter-Strike 2 is the genre-quality reference for weapon feel, animation, visual readability, competitive clarity and presentation. SIGHTBREAK keeps its own identity, mechanics, environments and assets. No Counter-Strike asset, name, image, map, sound or animation is copied.

The game at release candidate provides:

- Complete 5v5 matches offline, with good bots.
- Gunplay and movement that feel right, with credible weapon handling, reloads, effects and animation.
- Authoritative multiplayer that holds up with ten clients.
- A readable, accessible interface and coherent visuals and audio.
- Reliable progression, inventory and cosmetics on an earned-only economy.
- Native Windows, macOS and Linux packages, with Android and iOS development kept building.
- Reproducible builds and a safe Steam staging procedure.

## Release-candidate gates

The status of each gate is in the acceptance matrix. A gate is `VERIFIED` only with evidence a stranger can re-run or re-open. A passing automated suite is not enough on its own.

| Gate | Requirement |
| --- | --- |
| Core gameplay | A player can start, play and finish complete offline matches with correct objectives, combat, economy, results and progression. |
| Competitive systems | A ten-client authoritative match passes the reliability, privacy, identity, integrity and impairment requirements. |
| Player experience | Fire, hit, reload, switch, buy, plant and defuse are responsive and understandable. UI, weapon presentation, audio and animation meet the project's standard. |
| Visual quality | Each applicable category scores at least 8.5/10 in documented independent evaluation. A strong category cannot cover a failing one. |
| Platform stability | Windows, macOS and Linux packages pass execution, gameplay, compatibility and stability gates. Hardware not available stays `UNVERIFIED`. |
| Packaging and Steam preparation | Source-bound packages, metadata, verification tooling and a safe staging procedure exist. Steam publication, signing, accounts and spending need the owner's separate approval. |
| Human playtesting | Real feedback is collected and release-blocking problems are fixed. Never fabricated. |

## Status vocabulary

`NOT STARTED`, `IN PROGRESS`, `FAILED`, `VERIFIED`, `BLOCKED EXTERNALLY`. "Implemented" is not a status. A gate that needs hardware, credentials, network hosts or humans this session lacks is `BLOCKED EXTERNALLY` with the exact missing thing named.

## Constraints that do not move

- Godot 4.7.2, pinned and checksum-verified in `scripts/toolchain.py`.
- Server-authoritative movement, ammunition, damage, objectives and results. Protocol 6. Prediction opt-in, live rewind off, recipient-authorized state, account and inventory authorization, durable result recovery.
- Offline training progress never becomes online value. Online currency is earned only. No real-money purchases, cash-outs, crypto or external marketplaces.
- Aesthetic work must not weaken security, correctness, fairness or stability.
- Android and iOS build compatibility and cross-platform desktop exports stay intact.

## Quality method

1. Research the current behavior and the player-visible output.
2. Fix a real, named, fetchable bar. If the bar cannot be fetched, the parity gate is blocked, and the work continues against the measurable half and the previous build.
3. Build with a builder agent. Capture native output. Judge with a separate `harsh-critic` that has fresh context and sees blind pairs.
4. Revise on evidence. Retest. Run the broad suite.
5. Record the round, then take the next milestone.

Details: `.claude/skills/sightbreak-gauntlet/SKILL.md`. Writing goes through `.claude/skills/no-ai-slop` (see [COPY_STYLE.md](COPY_STYLE.md)).

## Coordination

Codex tends toward network, backend, native desktop platform work and build tooling. Claude tends toward gunplay feel, UI/UX, visuals, animation, audio feedback, bots and independent criticism. Read `docs/engineering/PARALLEL_WORK.md` and the open PRs before picking work. Do not duplicate an implementation another agent has in flight. Review their work independently before incorporating it. Draft PRs stay drafts until their gates pass.

## Roadmap order

Ordered by release-blocking severity, then player-visible impact, then dependencies. Re-rank after each milestone from evidence.

1. **Foundation**: mission records, skills, agents, session brief (M0).
2. **Native baseline**: run the real build, capture menu, HUD and viewmodel states, run the maintained suite, list the worst player-visible gaps (M1).
3. **Gunplay and viewmodel**: measurable fire, recoil, reload and switch behavior for all four weapons. Only the Relay AR has authored art; the other three are procedural.
4. **HUD and menus**: audit each player journey at the supported resolutions and text scales. Fix by evidence.
5. **Bots**: evaluate complete matches against objective metrics. Review the unintegrated tactical-AI tip before touching bot code.
6. **Audio feel**: timing and consistency of fire, reload, hit and objective sounds, with the limits of having no listener.
7. **Environment and characters**: Relay Yard readability and lighting, then an authored operator.
8. **Integration**: independently review and bring in the unmerged Claude art tip and the networking PRs #18-#21 in coordination with Codex.
9. **Copy**: audit every player-facing surface with `no-ai-slop`.
10. **Release candidate**: re-run every gate on one frozen commit, then hand off what hardware, humans and credentials still owe.
