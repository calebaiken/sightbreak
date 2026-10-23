# Prediction timeline V3 — gate-evidence slice

**No bounded shipping accuracy improvement is established. Prediction remains
default-off.** This focused PR takes the explicitly requested fallback: preserve
the activation gate, isolate one source-backed limitation and hand off the
smallest next experiment with raw matched native evidence.

## Source and ownership

- Branch: `astra/prediction-reconciliation-v3`, based directly on PR16
  `d2439acdd5f73df7bae5ada62ee1e3dec2cf30db`.
- Frozen V2 comparator: `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`.
- Frozen diagnostic/driver commit: `d5bdd538bb13e3cc97f4eae577c36d3d050a2a3e`.
- [Focused draft PR21](https://github.com/calebaiken/sightbreak/pull/21).
- [PR17 ownership handoff](https://github.com/calebaiken/sightbreak/pull/17#issuecomment-6275184071)
  and [frozen-run handoff](https://github.com/calebaiken/sightbreak/pull/17#issuecomment-6275381768).

There is no runtime delta between the comparator and this branch in gameplay,
network, art assets, backend or server. Only the new test, its separate Python
driver and documentation/evidence are added. `input_stream.gd`, actor/match hooks,
Sol's matrix/campaign harnesses, and PR18's EconomyUI/journal are untouched.
Protocol 6, live rewind off, authority/privacy and Claude/Gemini contracts remain.

## Finding and why it does not justify a guessed replay fix

During a short packet gap, `TacticalMatch._authority_tick` advances the actor with
held input. The input ACK changes only when a new command is popped. Consequently
the same ACK can refer to successive authoritative poses. The prediction routine
reconciles from each received pose and replays the remaining command history.
Its ACK-error metric samples only an ACK still in that history; after prefix
removal, later snapshots of the same ACK do not add a sample.

This follows the intentional authority rules: one physical step per tick,
bounded backlog discards, held-button edge preservation and a 300 ms silence
guard. Subtracting held steps from replay without a validated timeline would
risk dropping unconsumed direction/jump edges. Replacing server hold semantics
would change the authority contract and overlap another slice. This audit has
not established a safe correction to either behavior.

[Detailed design, exact source anchors, metric definitions and reproduction](../engineering/PREDICTION_TIMELINE_V3.md).
The experiment uses the inherited native authority tick, native actors and
replay on matched static floors, with deterministic packet delivery/loss inside
one process. It isolates timeline behavior; it is not a real ENet or game-map
accuracy comparison. Same-time separation includes intentional prediction lead.

## Frozen matched evidence

The serial matched run completed on Windows 11, official Godot
`4.7.2.stable.official.ed1daf0bf`, SHA256
`ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424`.
Python 3.14.6 was used only as a subprocess/archive driver. The clean driver/probe
source was `d5bdd538bb13e3cc97f4eae577c36d3d050a2a3e` for both runs. Native imports
completed before tests. Both game-only archives retained every shipping-file
hash; the two sources have identical shipping-file hashes.

- [Full source/engine/command/hash manifest](prediction-timeline-v3/matched/manifest.json).
- [Raw outcomes and native logs](prediction-timeline-v3/matched/).
- [Source-blob and historical-gate audit](prediction-timeline-v3/preflight/source-audit.json).
- [Position/receipt recomputation](prediction-timeline-v3/matched/metric-audit.json)
  and its [read-only verifier](../../scripts/audit_prediction_timeline.py).
- [Checksums](prediction-timeline-v3/checksums.json).

**The raw native outcomes are byte-identical between sources.** This is expected
for the unchanged shipping runtime and is evidence against claiming a candidate
accuracy gain. Each source passes 6,515 probe assertions (mostly per-tick step and
history-bound checks), plus all six maintained groups below. No script error,
ObjectDB-leak or leaked-instance warning appears in the captured imports/tests.

| Maintained group | Frozen701 | Probe source |
| --- | ---: | ---: |
| Movement replay | 725/725; max 0.075834 m | 725/725; max 0.075834 m |
| Input stream | 17/17 | 17/17 |
| State privacy | 55/55 | 55/55 |
| Snapshot buffer | 15/15 | 15/15 |
| Peer lifecycle | 16/16 | 16/16 |
| Diagnostic hit history | 638/638 | 638/638 |

The same outcomes apply to both labels:

| Nine-second condition | ACK p95 (m) | Max same-ACK authority drift (m) | Held snapshots / without ACK sample | Skipped commands |
| --- | ---: | ---: | ---: | ---: |
| Flat, zero added delay | 0.00000763 | 0 | 0 / 0 | 0 |
| Flat, 100 ms nominal RTT | 0.00000763 | 0 | 0 / 0 | 0 |
| Flat, 100 ms + bursts | 0.085000 | 0.510000 | 10 / 5 | 30 |
| Jump, 100 ms + bursts | 0.085000 | 0.510000 | 10 / 5 | 30 |
| Flat, 200 ms + bursts | 0.085000 | 0.510000 | 10 / 5 | 30 |
| Prediction disabled, 100 ms + bursts | Not scored | 0.510000 | 10 / 5 | 30 |

Each burst condition drops 18 of the 270 scheduled upstream batches. At 100 ms
nominal RTT there are 34 held authority ticks over the run. Jump authority reaches
0.985899 m, confirming actual airborne coverage. No condition records a hard
correction; that does not demonstrate acceptable feel.

One concrete repeated-ACK trace in the flat/100 ms/burst condition: ACK 82 was
first consumed at authority tick 86. Its authority position moved another
0.340000 m by the tick-90 snapshot, delivered at tick 94. The saved ACK pose and
ACK error for that later snapshot are null because the prefix had already left
client history. Raw per-tick authority drift reaches 0.510000 m before a fresh
command is consumed. These are distinct from the 0.085000 m aggregate sampled
ACK p95; neither should be substituted for the other.

Same-time separation p95 is 0.340001 m for the loss-free 100 ms condition,
0.381201 m with flat loss, 0.607213 m with jump/loss and 0.595002 m with flat
200 ms/loss. These are deliberately **not called accuracy improvements or pure
errors**: even the loss-free actor is intentionally ahead of delayed authority.
The raw data retain them so the critic can inspect correction/lead behavior.

The separate read-only verifier recomputes distances from raw positions,
percentiles, missing-sample counts and log/output hashes: 10,839 comparisons pass
at a 0.00002 m tolerance for float-to-JSON arithmetic. This is an author-run
verification, not an independent agent review or a broader network acceptance.

## Historical activation gate retained

The retained frozen V2 ten-client real-process campaign remains historical
evidence. Its ACK p95 values include 0.519256 m at 100 ms RTT, 0.566248 m at
150 ms, 0.469583 m combined impairment and 0.609490 m blackout. The blackout and
reconnect conditions recorded nine and eight hard corrections respectively.
The prediction-disabled ACK difference is not scored as prediction accuracy.
The prior 12/12 connectivity outcome does not grant prediction activation.

See [campaign.json](three-agent-evidence/stabilization-v2/network-r2-imported/campaign.json)
and [retained V2 report](STABILIZATION_V2_REPORT.md). This slice does not overwrite
those results, explain every historical error or establish an improved p95.

## Unsuccessful preflights

The first official-engine import failed with `realloc_static` / `LocalVector`
out-of-memory errors and exit `0xC000001D`. A concurrent own baseline worktree
checkout failed its allocation and then emitted pack-corruption wording; that
is not by itself evidence of repository corruption. The host then reported only
about 1 GiB free commit budget. Raw Godot failure output is retained. A serial
`--single-threaded-scene` import succeeded. The matched driver uses serial,
game-only archives to reduce memory pressure.

An exploratory dirty-tree probe preceded the frozen fixture. It is retained as
preflight, not substituted for the frozen run. The later fixture adds explicit
held-snapshot coverage and airborne checks. No failed attempt is relabelled a pass.

## Independent review and next experiment

The [blinded ZIP](prediction-timeline-v3/blind-outcomes.zip) contains only the
two unlabelled outcomes and instructions. The [same bundle unpacked](prediction-timeline-v3/matched/blind/)
and [separate mapping](prediction-timeline-v3/matched/mapping.json) are retained.
The harsh blind critic should record its outcome-only assessment before seeing
the mapping or this report. Independent critic/Sol acceptance remains pending.

Next: add test-only, out-of-band consumption-tick logs to a real ENet authority
fixture, join them with client snapshot/replay traces, and repeat loss-free and
short-loss conditions on a flat floor and Relay Yard with a moving blocker.
Evaluate alternate replay anchors offline against an independent authority-step
and button-edge oracle. Any eventual owner-only snapshot field requires explicit
protocol-owner review. Prediction enablement still requires the existing full
accuracy, authority/privacy, lifecycle and human-feel gates.
