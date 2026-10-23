# SIGHTBREAK v1.0 mission

This file holds the goal, the gates and the constraints. Current status lives in [SIGHTBREAK_V1_PROGRESS.md](SIGHTBREAK_V1_PROGRESS.md). The resume point lives in [../engineering/NEXT_SESSION.md](../engineering/NEXT_SESSION.md).

## Goal

Title: SIGHTBREAK — Steam-Ready v1.0. Status: IN PROGRESS. Priority: PRIMARY.
Completion condition: every defined v1.0 release-candidate acceptance gate is independently verified.
Scope: full product development, integration, stability, player experience and release preparation.

Persistent tracker: [GitHub issue #25](https://github.com/calebaiken/sightbreak/issues/25).
No native Codex goal creation/update API or goal ID is exposed in this session;
only the active goal's stop operation is available. The connected Linear
project service requires reauthentication; no goal was registered there. Issue #25 is
the supported external task record, with status/priority declared in its description.
Repository records remain the authoritative recoverable development state.

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

## Roadmap and dependencies

Re-rank after each verified increment. A completed task never completes the product mission.

| Milestone | Product result and dependency | Acceptance gates |
| --- | --- | --- |
| M0 Mission activation | Reuse mission records and quality skills, register the continuing goal, commit the exact resume state. | G20; documentation scope only |
| M1 Exported desktop playability | Close real-client Linux/Windows input, plant/defuse, full-match and earned-training restart failures. Builds on PR24 → PR23 → PR22 → PR16. | G1, G6, G11, G12, G16 |
| M2 Native platform stability | Isolate Intel macOS startup; qualify ARM/Intel Mac and Windows actual gameplay, preserve mobile build regressions. Can proceed alongside M1 on available hosts. | G11–G14, G19 |
| M3 Network qualification/integration | Independently qualify PR18–21 and V3 on the desktop base. Preserve authority, privacy, protocol compatibility, recovery and prediction opt-in. | G3, G16 |
| M4 Weapon handling and feedback | Fire/reload/switch/movement timing, animation and audiovisual feedback with actual rendered comparisons. Depends on stable input and capture. | G4–G6, G8, G9, G18 |
| M5 Tactical match quality | Measure objective behavior, perception, navigation and difficulty over reproducible matches; independently review newer bot work before integrating. | G1, G2, G17 |
| M6 Presentation and usability | Player journeys, accessibility, original environment/characters, audio and measured performance. Preserve readability and engineering gates. | G7–G10, G18, G19 |
| M7 Distribution and frozen RC | Reproducible source-bound packages for all targets, Steam staging preparation, no P0/P1, independent full-gate review on one frozen candidate. Depends on all preceding applicable gates. | G1–G20 |

For each milestone: investigate, implement, test, critique, improve, verify, commit,
update acceptance and select the next achievable increment. Keep working while the
session and authorized resources permit. On a session limit or external blocker,
commit recoverable work and leave exact commands, failures and next actions in
`docs/engineering/NEXT_SESSION.md`. Never claim work continues after execution stops.
