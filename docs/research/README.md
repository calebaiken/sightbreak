# SIGHTBREAK design research (2026-10-15)

A synthesis of what the repository itself shows about the native mobile UI, the armory and its cosmetics economy, the first-person weapons, the reload, lighting and materials, accessibility and visual presentation. It is **research and recommendation only**: no game code, asset, test or branch other than this documentation was changed.

| File | What it is |
| --- | --- |
| [`DESIGN_RESEARCH_SYNTHESIS.md`](DESIGN_RESEARCH_SYNTHESIS.md) | The synthesis: what is known, by area; the recurring design problems; the Counter-Strike 2 benchmark; what automated evidence can and cannot show |
| [`EVIDENCE_LEDGER.md`](EVIDENCE_LEDGER.md) | Every finding with an ID, an evidence class, its source and its status. The other files cite these IDs |
| [`REVIEW_CONFLICTS.md`](REVIEW_CONFLICTS.md) | Where reviewers, documents and measurements disagree, and what would settle each |
| [`IMPLEMENTATION_BACKLOG.md`](IMPLEMENTATION_BACKLOG.md) | The prioritised backlog, the decisions only the owner can make, and a suggested order |
| [`HUMAN_AND_DEVICE_TESTING_PLAN.md`](HUMAN_AND_DEVICE_TESTING_PLAN.md) | The gaps that need a phone or a person, and a study plan with success criteria fixed in advance |

## Evidence classes

Every statement in these files carries one of these, and the synthesis never upgrades one class to another.

| Class | Meaning | Examples |
| --- | --- | --- |
| **M** Measured | A number produced by a script, probe or log that can be rerun | A dialog 1216 × 1628 px; 16 of 48 menu labels under a 4.5:1 contrast ratio |
| **V** Verified defect | Reproduced by someone other than the author, or a test that fails before a fix and passes after | The unbounded trade confirmation; `1840233.0` printed for a pattern seed |
| **R** Reviewer judgment | A score or opinion from a reviewing agent. All reviewers so far are AI agents; none is a human player or an outside professional | "Weapon and arms 6.1/10"; "lumpy putty gloves" |
| **A** Author observation | What I saw in a repository capture while writing this. Subjective, one observer | "The tan pistol grip and the tan magazine sit side by side and read alike" |
| **D** Derived | Arithmetic from stated assumptions; not a measurement on a device | Physical size of a 48 px button on a 6.1-inch phone |
| **H** Hypothesis | Plausible, untested | "Players will not notice the scroll hint on the confirmation sheet" |
| **U** Unverified | Needs a phone, a person, or a service the repository does not have | Frame time on a phone; whether a trade is understood |

## Ground rules this synthesis keeps

- **There is no player feedback in this repository.** A search of every document on the four branches finds no playtest, interview, survey or usability session. Every "players would…" below is a hypothesis (H) or an unverified gap (U), never a finding.
- **Automated tests establish behaviour, not quality.** A passing suite says a rule holds; it does not say a screen is clear, a hand looks like a hand, or a reload feels right. Where this synthesis cites a test it says what the test does and does not show.
- **Counter-Strike 2 is a benchmark of professional quality, not a source.** No CS2 imagery was studied in any session on this project (the project's own gap analysis says so), and none was used here. Statements about CS2 are marked as expectations from general knowledge, to be verified by someone who owns the game. No CS2 asset, layout, shape, name or palette is to be reproduced.
- **The author and one set of reviewers share a model family.** I am a Claude model, as were the author of most of the work and the reviewers behind the 4.5/10 scores. The Codex reviewer is a different model family, but it is still an AI agent posting under the same GitHub account as every other comment. I therefore treat all scores as opinions with unknown calibration.
- **Nothing was run that was excluded.** No Blender build, no change to the uncommitted two-magazine work in the graphics worktree, no merge, no push to any existing branch.

## Evidence base (exact identities)

| Source | Identity |
| --- | --- |
| PR #1, foundation and HUD | head `148760e`; 11 comments read (Codex reviews and my replies) |
| PR #2, graphics | head `68251a0`; 4 comments read; documents and evidence read as committed |
| PR #11, Codex validation follow-up | head `11573e5`, base `a6b913c`; body read; no comments or reviews at the time of writing |
| PR #12, native UI (draft) | head `7e41de6`; no comments or reviews at the time of writing |
| Graphics worktree | uncommitted: `actor.gd`, `tools/art/arms_build.py`, `reload_legibility_probe.gd` modified and `reload_phases.gd` new. **Read for its description only; unbuilt, untested and unreviewed** |
| Documents | `docs/art/*`, `docs/design/DESIGN_SYSTEM.md`, `docs/ui/*`, `docs/economy.md`, `docs/KNOWN_LIMITATIONS.md`, `docs/DEVICE_TESTING.md`, `docs/reports/QA*.md`, `docs/audits/*`, and Codex's integration reports on `integration/sightbreak-reliability-refresh` |
| Captures | the reload contact sheet, support-hand close-ups and firing burst (`art-v6`); the requisition, HUD and menu frames (`ui` increments 1–4); the case-reveal sheet. Video sequences were not viewed; their frame tables and sheets were |

The branch these files are on, `claude/design-research-synthesis`, was created from `7e41de6` and holds documentation only.
