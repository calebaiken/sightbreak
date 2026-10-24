# R5 offline reader builder handoff

Frozen source `7d8ec7dda37764e0f45fd2ea1e8d330f84bc2508` is pushed on
`codex/windows-input-consumption-r5-20261024`. It starts from rejected R4
`642dd0e0543698cae5d90b9046d5875beabed111`. Source acceptance is pending a
different independent critic. No native attempt, engine/API behavior, acquisition
coverage, actual delivery, disconnect cause or release gate is accepted here.

The reader rejects all six new false accepts from independent R4 rejection
`ad12f7ae08ca9cf1eaf05807ea41c44104544fdc` while accepting its paired positives.
It retains coalesced calls, malformed prevalidation input, unordered/duplicate
endpoints and reset lifetimes. It does not reconstruct unreported packet commands.

## Preregistration and exact source scope

Preregistration `6f3a5bcd` precedes implementation. Expansion `09b476ae` precedes
the additional snapshot fixture correction. Both use the unchanged actual Match,
SBInputStream and peer lifecycle as the comparison bar. This is an attributed
correctness comparison; hidden labels would obscure the source oracle.

Exactly four non-document paths change: analyzer, identity fixture, lifecycle
restamping and new `test_input_consumption_stream.py`. The analyzer adds24 lines:

- Queue size is bounded by120, and a count0 projection has endpoints-1/-1.
- Accepted endpoints obey ACK+120. One/two-command batches expose every command
  and require a fresh endpoint. Larger batches may hide fresh middle commands;
  the positive `[1,2,1]` at ACK1 retains count3/first1/last1 and queue1.
- Newly counted metadata calls lie within the preceding/current emitted wall
  interval, inclusive. Unchanged counters retain old metadata and equal
  millisecond timestamps remain valid.
- Stream rejection state agrees with new observer rejection calls within a
  proved lifetime. Lobby replacement may reset state while retaining observer
  counters/latest. The rule permits a reset when the epoch advances with no
  continuous bound-peer witness; it never imposes global state==counter.

The source reset check tracks bindings through their disconnect observation,
which precedes actual removal. A live binding across an ordinary epoch change
preserves stream rejection state. A guest lobby reset advances epoch twice
(replacement then `_begin_round`), respawns the roster and resets stream state.
Tests cover state0/counter1 after replacement and later state1/counter2 after a
new rejection, as well as forbidden state drops without the required boundary.

The identity positive adds its missing stream_rejected1 after the hidden
rejection. Lifecycle restamping sets its first newly observed snapshot time to
the preceding welcome/emitted wall, caches it and recomputes ages. Independent
source adjudication confirmed this minimum timing correction. All45 inherited
test methods and79 assertion-call ASTs remain unchanged. Ten new stream methods
bring focused coverage to55 methods, all passing.

The full non-document Git union is513 paths with516 unique verified blobs:
four allowed changes and509 protected paths. Both views materialize473 paths
and retain40 exact sparse omissions with hashes/modes verified. Runtime hooks,
transport/RPC, authoritative behavior, controller/native paths, privacy/economy,
CI and canonical documents are unchanged. See `final-source-bindings.json`.

## Actual frozen results

All execution uses CPU4. The inherited pure union includes existing platform
parser fixtures; this task performs no Mac review or native/application run.

| Check | Own source | Initialized depth-one |
| --- | ---: | ---: |
| Pure union | 229 methods:226 pass, 3 inherited Windows skips | same |
| Shell syntax | exit0 | exit0 |
| Exact final independent R4 controls | 13/13 | 13/13 |
| Retained prior92 with explicit source adjudication | 92/92 required verdicts | same |
| New versions correcting rejection state only | 3/3 | 3/3 |
| Combined required verdicts | 108/108 | 108/108 |

Outputs are `final-full-pure/`, `final-depth-pure/`, `final-full-controls/`
and `final-depth-controls/`, with adjacent stdout/stderr. Every full/depth
control verdict and result body is byte-identical.

The old reader is SHA-256
`207beebe124a1ad5928a154fb77c99d2e43864ce236751dc7ce985878181bcb2`.
Before edits its exact independent13 replay reproduces7/13, with six false
accepts and no false rejects (`old-reader-fresh13/`). Its replay against the
new explicit108 requirements meets99/108; nine false accepts consist of the
six fresh falsifiers and three newly obsolete positive fixtures. The old reader
fails11 assertions in the ten new pure methods. This last comparison imports
the exact old analyzer with the new source-faithful helpers, not an entire old
checkout. All raw failures remain retained.

## Historical expectations and fixture versions

No old report or raw fixture is rewritten. `r4-builder-frozen/` contains exact
selected files from handoff `d139124e`, including its92-case inputs/results.
`r4-critic-frozen/` contains exact final13 inputs/results, executable rig, review
and stream-reset adjudication from `ad12f7ae`. `evidence-bindings.json` compares
each copied file against its committed Git object and binds historical source,
all45 inherited methods/assertions, original Windows logs and full/depth results.

The original six obsolete positives adjudicated in R4 remain rejected. R5 also
rejects three previously passing positive corpus fixtures: the two versioned
malformed receives and the earlier R3 malformed/coalesced positive. They counted
one rejection but retained stream_rejected0 in a fixed live epoch. Thus only
89 of the previous92 required outcomes remain unchanged. Their old expected
values, bytes and passing R4 outcomes are preserved in the copied R4 receipts.
The new replay records these as explicit newly obsolete positives, then adds
separate versions changing only stream_rejected to1 after rejection.

The affected copied builder cases have authority epoch7 and live peer71,
generation1; fresh independent13 uses epoch1. The critic's later clarification
corrects an earlier prose annotation of epoch1 for the old builder cases.
Actual fixture values and same-lifetime reset exclusion are unchanged.

The first R5 focused iteration retained one failure: the existing failed-attempt
restamp moved welcome to wall6000 while its first counted snapshot stayed4000.
The preceding row had no snapshot counter/cache, so this violated the new time
interval. The preregistered minimum helper fix places the first snapshot at6000,
preserves its header/counter and cached timestamp, and restores the original
assertion without weakening the timing guard. The exact old helper and failed
output are retained. New full-queue/reset helper refinements also retain their
earlier passing outputs; final tests use coherent network/tick timing and the
respawned roster at a real guest reset boundary.

Original raw Windows client/server log bytes remain at their tracked R2 paths,
SHA-256 `ec5fe22c681a9bd5ea0577773e9421d7f0eca6d2711b77c8c124f4cdefff4ba4`
and `61937ac0d1c75f29f790ffc339a4dabaa0a29eac65e9c5da5b4c526835ed0757`.
The original untraced inputs still return incomplete. Original R2/R3/R4 branches,
commits, failed iterations and every old control remain preserved.

## Source setup and reproduction

The own worktree is sparse, created with no checkout and explicitly populated
using read-tree before investigation. The initialized `.local/depth-one-source`
view is clean at exact frozen source, shallow, with one reachable commit and a
complete12057-path index. It shares `/workspace/sightbreak/.git/objects` as an
explicit alternate. Neither view is a self-contained clone or independent object
closure proof. Provenance helpers deliberately use named historical Git objects.
No full clone was made, and R4 remains untouched on its own branch.

From this checkout, use fresh output paths:

```sh
taskset -c 4 python3 docs/reports/gauntlet/windows-input-consumption-r5-20261024/run_pure.py --source . --output /tmp/r5-pure-fresh
taskset -c 4 python3 docs/reports/gauntlet/windows-input-consumption-r5-20261024/replay_controls.py --source . --output /tmp/r5-controls-fresh
taskset -c 4 python3 docs/reports/gauntlet/windows-input-consumption-r5-20261024/bind_source.py --source 7d8ec7dda37764e0f45fd2ea1e8d330f84bc2508 --output /tmp/r5-bindings-fresh.json
taskset -c 4 python3 docs/reports/gauntlet/windows-input-consumption-r5-20261024/verify_evidence.py --output /tmp/r5-evidence-fresh.json
```

For another initialized view, `initialize_depth.py --source <exact source>
--depth <fresh directory> --output <fresh receipt>` records explicit alternates,
sparse selection, populated index and exact shallow state. The immutable final13
also replay directly from the copied `fresh_controls.py`; fresh outputs are
required, and the original invalid inverse-rejection case remains invalid.

The largest remaining limitation is observation granularity: endpoints and
cumulative counters do not expose complete packets, terminal capture coverage,
real delivery or the old disconnect cause. A different independent critic must
assess this frozen implementation and its fixture changes. No source approval,
native admission, retry, workflow dispatch or release follows from this handoff.
