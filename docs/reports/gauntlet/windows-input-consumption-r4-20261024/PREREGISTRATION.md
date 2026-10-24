# R4 source-state consistency correction

Registered before analyzer or test edits. Base is frozen R3 source
`342c3641ab2fccd1fc875c84188a8395a9b93a96`. The actual bar is its Match
observer, synchronous input RPC, peer lifecycle and input-stream implementation.
The fresh independent R3 critic owns preregistration `b22c2790`; its final exact
fixtures/report must arrive before implementation begins. This is an attributed
offline correctness comparison. It cannot qualify native behavior or identify
the original disconnect cause.

This branch/worktree is `codex/windows-input-consumption-r4-20261024` at
`/workspace/sightbreak-windows-input-consumption-r4`. It is sparse and shares
the existing `/workspace/sightbreak/.git` object store; it is not a full clone.
The R2/R3 builder checkout and its untracked packaging remain read-only.

The measurable requirements are:

- A peer cannot gain another live generation while its lifecycle entry exists.
  Keep binding-once, actor exclusivity, preceding connected identity, retirement
  and welcome/attempt requirements. A real disconnect permits peer/actor reuse
  with a fresh generation. Lifecycle reasons always emit; their counters must
  equal observed occurrences, including the current row.
- Every emitted reason increments its cumulative counter relative to the prior
  row. Counters remain monotonic. Metadata stages have persistent `latest` keys;
  a key cannot disappear or change while its stage counter stays unchanged.
  Coalesced calls may advance counters and metadata without direct event rows.
- Every synchronous receive ends in acceptance or stream rejection. Let R, A
  and J be their cumulative counters. Require R=A+J+1 on a current direct
  `input_received` row and R=A+J on all other rows. Accepted current metadata
  equals latest receive packet fields excluding `wall_msec`; the receive time
  may precede the acceptance time. A current accepted row has queue_count>0.
- A current consumed row has ACK equal to its command sequence, and its own
  actor input controls equal the consumed control projection. Its binding and
  sequence invariants remain. A freshly bound identity cannot consume without
  any subsequent acceptance counter progress, but coalesced acceptance is valid
  and requires no direct event per peer. Do not attribute a cumulative acceptance
  to a particular packet or infer complete per-peer traces.
- Preserve accepted unordered/duplicate endpoints, queued duplicates, cumulative
  metadata across attempts/epochs/disconnects, and positive coalesced second-peer
  input. Do not require queue growth, packet identity, complete observed events,
  a sorted batch or one-to-one receive/accept rows.

Source adjudication by the fresh R3 critic and root authorizes minimum correction
of the shared maintained `declared_rows` positive fixture: retain cumulative
latest (including welcome/snapshot), use nonempty accepted queue before pop, and
use the popped ACK and actor controls at consumption. Preserve all existing
assertion methods and falsifier mutations. If helper restamping resets cumulative
metadata, correct only that fixture construction. The exact old analyzer and
fixture source are retained under `historical-source/` before edits.

The original 29 and final nine old controls contain source-inconsistent positive
fixtures, independently confirmed by the fresh critic. Preserve their exact rig,
logs, outputs and expectations as historical evidence. Replay them unchanged and
report contradictory obsolete positives as rejected; never relabel that replay
as unchanged success. Add source-faithful replacements with only independently
adjudicated fixture normalization, preserving each intended falsifier. Retain
every old negative outcome and the original untraced native-log incompleteness.

Before implementation, retain the frozen old reader's actual verdicts for every
final fresh critic case. After source freeze, require all final critic fixtures,
source-correct replacements, old negative controls, maintained pure groups and
new meaningful state-consistency tests in both actual source and an initialized
depth-one repository. Bind the full tracked non-document Git union, including
sparse omissions, and disclose shared object alternates for the depth-one view.
Preserve failures and setup corrections. CPU 4 only; no Godot, native helper,
CI, runtime, dispatch or actual attempt.

Allowed code changes are the offline analyzer, minimum source-faithful fixture
construction in existing pure test files and a new pure state-consistency suite.
No runtime, transport, RPC, privacy, economy, controller or canonical documents
change. Commit and push frozen source, then builder evidence for a different
fresh independent critic. The builder cannot approve the source gate.

## Fixture call-order expansion before edits

The existing positive malformed-receive method in the identity suite changes
the first direct receive's epoch/endpoints while expecting later valid acceptance.
Keep that malformed direct record and mutation, then explicitly construct the
real intervening calls: stream rejection of that malformed packet, followed by
a valid receive and acceptance. Match 1066–1078 calls those synchronously.
The first rejection does not print: Match 1298–1300 excludes
`input_stream_rejected` from both lifecycle and control events. A later valid
receive with the same fire/reload/moving controls may coalesce because Match
1295 excludes packet epoch/endpoints from its per-reason edge. The later accepted
row must therefore retain rejection counter/latest, receive counter2 and valid
latest receive metadata. This adds no direct rejection row and invents no packet
identity. Independent source adjudication is required before this edit.

Old pure suites ran unchanged before implementation: 32 methods passed on CPU4,
with stdout/stderr retained under `historical-source/`. That result measures the
old suite, including its contradictory positive fixture. The identity source is
also retained byte-for-byte before its minimum fixture correction.

Fresh critic independently identified a second contradiction in that old positive:
its count1 packet has first=-1,last=-9. Match 1249–1264 reads both endpoints from
the same sole dictionary command, so even malformed input cannot emit unequal
endpoints at count1. Correct the intended malformed-payload mutation to
first=last=-9, epoch=-1; retain the old unequal projection historically and label
it impossible rather than valid prevalidation. Root separately authorized this
minimum correction. The reader must reject unequal count1 packet endpoints in
any current packet projection, including receive; this is projection fidelity,
not authority validation of received payloads. Other malformed receive values
remain allowed before stream validation.
