# R6 offline reader builder handoff

Frozen source is `c8827e7d158431097a5413273b5a1e93715961b0`, pushed on
`codex/windows-input-consumption-r6-20261024`. Base is rejected R5
`7d8ec7dda37764e0f45fd2ea1e8d330f84bc2508`, sealed handoff `eb2dbc7c`.
Reader SHA-256 is
`c53b1ced5743c7440d0530874115d474da2a70f2416c7515e098109837182be8`.
Source readiness remains pending independent whole-reader review. No native,
engine/API, actual delivery, disconnect cause, capture completeness, physical
latency or release gate is accepted by these builder results.

The correction replaces direct-reason-only checks with an offline transition
model. It meets every exact final30 expectation from R5 rejection
`c909a9cb88d4ab77dfc1a5a5bba266ce15fc5e4d`, preserves the useful prior controls
and returns explicit UNKNOWN when observations cannot support a sound context.

## Registration and model

Initial registration `4f0a1906` precedes source edits. Expansions `0719aafb`,
`f28488bb` and `d458bbcb` precede their fixture, definite-fact and relational
state changes. The actual unchanged Match/InputStream/lifecycle source is the
bar. The architecture proposal was sent before implementation; the independent
isolated model/coverage assessment preceded source readiness consideration.

The source model retains these relationships:

- Snapshot cache equals its counted latest application header at every row.
  Counter persistence therefore prevents silent cache clearing/restamping.
- New direct and hidden accepted headers share epoch/count/sequence validation.
  A hidden acceptance uses a possible pre-pop ACK interval; a later pop cannot
  lend its ACK to an earlier acceptance. Larger packets may have stale endpoints
  and fresh unreported middle commands.
- Per-stream queue/ACK transitions use proved local accept/pop calls, skipped
  state and source reset boundaries. Direct count1 cannot inflate queue0 into2.
  ACK cannot advance/clear without its source operation. Replacement rejection
  state is old_state+new_calls or fresh0..new_calls, not an arbitrary partial drop.
- Definite queued keys and immutable control signatures survive unknown packet
  middles. Sorted pop, backlog ranks and unique sequence windows constrain
  consumed intent. An observed empty queue re-establishes exact emptiness.
- Persistent receipt groups retain new-entry cardinality, joint action budgets,
  possible first-receipt origins, observed pop origins and historical ACK/queue
  cutoffs. Integral circulation enforces one feasible assignment across the
  history, rather than independently choosing new payloads for every pop.
- Owner ledgers save the actual proved local call projections. Later global
  latest metadata from B cannot replace an earlier owned A header. Explicit
  unselected consumption is inferred when prior cardinality and a sole pop prove
  its state. Unresolved ownership stays UNKNOWN, not a guessed packet link.

The receipt representation uses only the Python standard library. Search is
bounded: excess origin-domain memberships or receipt alternatives produce UNKNOWN.
Multiple unexposed local call histories can also remain incomplete. These are
declared coverage limits, not source INVALID or native failure. The new
transition_status distinguishes CONSISTENT, INVALID and UNKNOWN; diagnostic_complete
is false for UNKNOWN. CONSISTENT describes the modeled observation constraints,
not complete packet reconstruction or end-to-end qualification.

No-pop epoch transitions distinguish older accepted input erased by reset from
new-epoch input accepted afterward. Local proved call deltas and cached projections
drive this interpretation. Ambiguous acceptance/pop order across an unobserved
epoch boundary remains UNKNOWN. Reset and multi-peer coverage need the exact
final independent review; prototype results below do not replace it.

## Exact scope and source proof

Four non-document paths change: analyzer, one construction line in the existing
queued-duplicate test, and two new pure test files. All55 inherited methods and
100 assertion-call ASTs remain unchanged. The new behavior suite has18 methods;
the separate receipt oracle has2. Focused coverage is75 passing methods.

`sealed-source-bindings.json` binds the full515-path non-document union,517
unique Git blobs, modes and working bytes. Exactly four paths change and511
remain protected. Every515 non-document path is physically materialized and
verified in both views; there are no non-document sparse omissions. Sparse
selection still omits the unrelated large document tree.

Game/runtime, controller/native, RPC/transport, authority, privacy/economy, CI,
backend/art source and canonical documents are unchanged. Materializing those
protected files is read-only; it executes no backend/art/workflow action.

## Final frozen checks

All executions use CPU4. Tests run in process; server-process and Mac groups are
excluded by this lane's explicit scope. No full maintained-union claim is made.

| Check | Own source | Initialized depth-one |
| --- | ---: | ---: |
| Selected pure union | 227 methods:224 pass, 3 inherited Windows skips | same |
| Shell parsing | exit0 | exit0 |
| Retained prior108, with explicit new adjudication | 108 required verdicts met | same |
| Exact independent R5 fresh corpus | 30/30 | 30/30 |
| Separate corrected queue-state version | 1/1 | 1/1 |
| Combined required verdicts/statuses | 139/139 | 139/139 |

Final outputs use `sealed-own-pure/`, `sealed-depth-pure/`,
`sealed-own-controls/` and `sealed-depth-controls/`. Every case's full/depth
verdict and result body is byte-identical. `sealed-evidence-bindings.json`
verifies this, exact copied Git bytes, old source, inherited assertions and raw
original Windows logs. The untraced original logs remain incomplete.

The old R5 reader reproduces15/30 before implementation and123/139 against
the newly explicit requirements. It fails30 assertions across the18 new behavior
methods when combined with source-faithful new helpers. That last view compares
exact analyzer bytes, not an entire older checkout. Its original SHA-256 is
`c0fe4d9f078a28043a7c89eaef2b0402ca03c486fb3a8c781040a5e6e517f7e0`.

The separate exhaustive receipt oracle matches1,002 complete one-receipt and
1,024 two-receipt candidate histories. Its ground truth independently stages
last duplicates, preserves first queued payloads and pops sorted keys. Those
2,026 pure comparisons do not represent acquired/native observations.

## Independent prototype assessment and its limits

`model-assessment/` retains exact `239792ce` files. It records the rejected
unfrozen9248/0ac models, including four invalid queue admissions, a valid
multi-peer false INVALID and four aggregate-history false accepts. None was
hidden by later fixture changes.

`model-assessment-v2/` retains additive files from
`5c5aca24205be4c2a9e57aa5ca12f9e8d63aa11f`. On explicitly captured core SHA
`60e619383050839113f1e11fcd9cfdf836dec93686367f27df86cd540307db26`, the
independent assessor reproduces13/13 queue and5/5 aggregate models, then
36,948/36,948 generated expectations from7,568 concrete source histories and
3,150 visible prefixes. The compressed all-case stream is retained and hash-bound.

Those results assess an isolated earlier InputTransitions core. They are not a
whole-reader verdict, do not cover final c882's epoch/owned-projection delta,
and grant no readiness/native release. The generated families use finite,
fully drained small queues, one peer, at most two receipts and at most one
new local call per observed interval. They do not establish general multi-call
ownership, arbitrary-length flows, reset interpretation or capture coverage.
Read `ASSESSMENT_60E619_ADDENDUM.md` for its exact finite bounds.

Final source additionally saves owned projections and has a paired epoch matrix.
The first recoverable R6 checkpoint `0d5db0f8` remains preserved. Its valid
delayed-A-header test fails because global latest B data is used for A; the
actual failing stdout/stderr is retained. Final c882 passes that test. All
first-checkpoint depth/source/pure outputs remain under their original names;
only `sealed-*` denotes final c882 evidence.

## Fixture adjudication and retained failures

All prior108 and fresh30 inputs/results/expectations remain byte-exact in
`r5-builder-frozen/` and `r5-critic-frozen/`. The R5 independent critic confirmed
two old positive contradictions before the authorized changes:

- The queued-duplicate unit copied receive queue0 after acceptance already left
  queue1, with no intervening pop. Only duplicate[0].queue_count becomes1 before
  restamping. Duplicate acceptance stays queue1 and original queued fireTrue;
  every old assertion is unchanged. The old file and first failing run remain.
- The old normalized seq21/22 case pops22 first with queue[21,22], C1/skipped0,
  then regresses ACK22 to21. That exact obsolete positive now rejects. A separate
  version retains latest accepted22/A2/R2 but pops oldest21, actor/ACK21 and
  queue1 retaining22 through the final tick. No historical input is repaired.

Thus107 of the previous108 verdicts remain unchanged; the other positive is
explicitly adjudicated as obsolete. The new139 requirements preserve its original
expected value/outcome alongside the new source-consistent rejection and distinct
valid replacement. No claim of108 unchanged expected passes is made.

Raw earlier model failures, duplicate-fixture failure, first candidate false
INVALID and the new test helper's same-clock timestamp correction remain retained.
Raw failing unittest output may contain its original trailing spaces; it is not
rewritten for formatting. Authored Python/Markdown/JSON pass whitespace checks.

Original raw Windows logs remain bound at their tracked R2 paths with hashes
`ec5fe22c681a9bd5ea0577773e9421d7f0eca6d2711b77c8c124f4cdefff4ba4`
and `61937ac0d1c75f29f790ffc339a4dabaa0a29eac65e9c5da5b4c526835ed0757`.
All older branches, preregistrations and failures remain intact.

## Setup and reproduction

Own sparse checkout used explicit read-tree before investigation. Final depth
`.local/depth-one-final` is initialized at exact c882, clean, shallow and has one
reachable commit plus the complete12489-path index. It explicitly shares
`/workspace/sightbreak/.git/objects`; it is not independent object storage or a
self-contained clone. No full clone was made. Named historical Git objects are
deliberate provenance dependencies of verification helpers.

From this R6 checkout, use fresh outputs:

```sh
taskset -c 4 python3 docs/reports/gauntlet/windows-input-consumption-r6-20261024/run_selected_pure.py --source . --output /tmp/r6-pure-NEW
taskset -c 4 python3 docs/reports/gauntlet/windows-input-consumption-r6-20261024/replay_controls.py --source . --output /tmp/r6-controls-NEW
taskset -c 4 python3 docs/reports/gauntlet/windows-input-consumption-r6-20261024/bind_source.py --source c8827e7d158431097a5413273b5a1e93715961b0 --depth .local/depth-one-final --output /tmp/r6-source-NEW.json
taskset -c 4 python3 docs/reports/gauntlet/windows-input-consumption-r6-20261024/verify_evidence.py --output /tmp/r6-evidence-NEW.json
```

`initialize_depth.py --source <exact source> --depth <fresh directory> --output
<fresh receipt>` initializes another disclosed alternate-based sparse view.
No Godot, engine API, native/helper/process inspection, OS input, Mac review,
CI dispatch, actual attempt, canonical edit or runtime change occurred.

The remaining gate is independent whole-reader review of exact c882, including
local/global projection ownership, epoch/cache causality and declared UNKNOWN
limits. Endpoints and counters still do not identify packets, prove delivery or
terminal capture coverage, or explain the historical disconnect. No new native
admission, retry or release follows from this builder handoff.
