# Objective observation R2 source handoff

This is an unapproved correction candidate for independent re-review. Original
`c91d9b98` remains rejected. No bot-policy improvement, historical cause, native
readiness or G1/G2 acceptance follows from these source checks.

Frozen source: `dce89495d04c9d3fefece0f8c7929e2e01b8e7df`.
Preregistration before implementation: `41aa040d`.
Own branch: `codex/m5-objective-observability-r2-20261023`.
Own checkout: `/workspace/sightbreak-objective-observability-r2`.
Exact initialized shallow fixture:
`/workspace/sightbreak-objective-observability-r2-depth-one`.
The later handoff commit adds reports only; the game/scripts trees and the frozen
inventory identify the tested source independently of those report additions.

## Correction against the actual rejection

The optional production API replaces nonempty caller-owned output before gated
or early-return calls. It requires literal boolean true. Empty default
dictionaries stay empty. Requested calls report decision/perception operation and
disabled, blocked, dead, non_live, collecting or complete status. Public direct
perception calls cannot retain an old decision. Complete decisions carry null
values for branch fields that were not computed. The original selector body runs
once through a private helper; the public wrapper preserves its return behavior.
No added selector, visibility, navigation, physics or RNG draw appears in the
production observation path. All writes there target the caller-owned dictionary.

The test-only observer captures full before/after decision, objective and
authority state. The forward slice records all 120 authority ticks, even if a
natural terminal state stops objective calls. An explicit start record binds it
to event 122. Paired poses bind commands, actor/position/tick, profiles, goals and
current RNG state. Control commands bind to their thinking ticks and actual
objective inputs. Negative controls explicitly override interaction/movement as
declared in the fixture; positive controls use the actual generated command.

The version-2 reader requires complete commands and typed, finite records. It
checks fixed 1/60-second authority steps, consecutive ticks, continuous progress,
the first completion threshold, cleared progress, credits/contributions, scores,
phase, timer and objective position. It checks the objective consumer separately
from subsequent elimination/timer handling. Missing forward fields, fabricated
poses, omitted commands, contradictory outcomes and incomplete decision streams
are failures. Synthetic records exercise this schema; they are not engine output.

The five-file erasure check remains explicitly limited to preserving original
gameplay statements. A separate frozen inventory binds all 451 tracked game and
script files, including project settings, scenes, resources, UIDs, the probe,
utility, movement and the reader itself. Mutation controls remove the probe's
actual consumer, alter utility/project resources and hide an RNG draw inside an
erased block; the full inventory rejects each. The inventory does not approve the
inserted code. Fresh manual source inspection is still required.

Reset declarations and paired protection now include deploy time, weapon
cooldowns, shot index, stance/head/collision state, previous action-button edges,
damage history, interactions/contributions, bot clock and neutral input. Engine
floor contact is captured and explicitly declared unrestored. Utility state,
objective position/timer, resources, memory and RNG state are also protected.
These are declared reconstruction assumptions, not recovered historical state.

The experiment explicitly uses the newer `022d60f` gameplay baseline. A retained
historical AI source reference and the erasure result independently establish
the thirteen added fallback lines relative to `0527715`, without ancestor history
or network access. Restarting original initial seeds and resetting holstered
ammunition cannot recover the original later RNG/resource trajectory. This
experiment cannot establish why the historical carrier timed out.

## Original criticism and correction evidence

`original-critic/` preserves the original script and output, plus the critic's
`c3a89e53` rig correction. Script SHA-256 remains
`af4a712cdd9f195203ad4caec4c9351da4a0ebf221d80ef23e54cd2ec3489813`.
Its two identical no-op inputs require opposite outcomes. The original rejection
still stands, interpreted as nineteen distinct cases: one baseline smoke input
and eighteen actual mutations. No test-name branching or reader exception was
introduced to force the contradictory case to pass.

`pure-final/` contains exact frozen-source command receipts, original stdout and
stderr, before/after identities and grammar results. The unchanged rig retains
its process exit 1 for the contradictory no-op. The meaningful checks are the
accepted complete schema-positive input and rejection of all eighteen actual
mutations. New maintained controls explicitly delete forward evidence from that
complete baseline, and add command, type, freshness, context, continuity, reward,
stream and dependency boundaries. The final summary records the actual terminal
outcomes; the original rig's hardcoded candidate label is preserved, while outer
receipts identify the source it actually imported.

At the frozen source, both the own and initialized depth-one checkouts passed all
ten maintained methods and the complete 451-file source audit. Both accepted the
complete synthetic baseline and rejected all eighteen actual original mutations.
Both unchanged original-rig processes exited 1 solely for the contradictory no-op
expectation. `pure-final/summary.json` records these outcomes and exact timings.

The initialized depth-one fixture has exactly one reachable commit, no remotes
and no object alternates. It contains all 451 acquisition files and the component
records needed by the audit. Its pack is 8,931,186 bytes. Pure test processes use
CPU 4 and disable bytecode output so the fixture stays clean. Retained tree hashes
and inventory establish the same game/scripts source before and after checks.

The first implementation test failed because the synthetic generator retained an
alias to progress that later synthetic ticks changed. Its terminal tool receipt
is retained; earlier streamed chunks remain in the tool conversation, not a
claimed complete raw file. `pure-r1/` is a later pre-freeze development run, not
exact-source qualification. The synthetic alias was corrected before the frozen
source. Neither earlier failure nor the original rejection is relabeled a pass.

`gdtoolkit==4.5.0` accepts the two frozen GDScript grammars in both checkouts. This
does not establish pinned Godot 4.7.2 compilation, native freshness/parity,
release/online isolation, real geometry, timing/performance or strict shutdown.
Only source/pure work ran in this lane. No Godot, import, renderer, native
application, export, service, CI or nested agent was invoked. No native release
is requested or implied.

## Independent re-review

Read the actual inserted production code as well as the reader and emitter.
Check that clearing output cannot affect gameplay in the actual fresh-dictionary
callers, the strict gate covers direct and nested perception collection, and no
observation value feeds a decision. Inspect the full schema-positive synthetic
record and mutate it independently; passing method counts alone are insufficient.
Check full source/resource closure, the historical drift and every reset policy.

From either frozen-source checkout:

```sh
taskset -c 4 python3 -m unittest discover -s scripts -p test_bot_objective_observation.py -v
taskset -c 4 python3 scripts/verify_bot_objective_observation.py
taskset -c 4 python3 docs/reports/gauntlet/m5-objective-observability/correction-r2/original-critic/independent_controls.py "$PWD"
```

The third command deliberately retains the unchanged rig's contradictory exit 1;
inspect the result object using the critic's published correction. A fresh source
review must decide whether the corrected method is ready. Any native work then
needs separate preregistration, complete source-bound supervisor, fresh observer
admission and an explicit root release. The earlier proposed inner probe command
is not an approved acquisition recipe. Preserve original stock failures and all
whole gameplay gates while that evidence is absent.
