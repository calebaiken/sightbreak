# R6 offline transition model

Registered before source edits. Base is rejected R5 frozen source
`7d8ec7dda37764e0f45fd2ea1e8d330f84bc2508`, sealed handoff `eb2dbc7c`.
Independent rejection `c909a9cb88d4ab77dfc1a5a5bba266ce15fc5e4d` demonstrates
15 false accepts in its exact30-case corpus, with no false rejects. The actual
unchanged Match observer/RPC, InputStream and lifecycle implementations are the
source bar. This is an attributed correctness comparison, not a native model.

Own branch/worktree `codex/windows-input-consumption-r6-20261024` lives at
`/workspace/sightbreak-windows-input-consumption-r6`. It is sparse, initialized
with explicit read-tree and a complete12057-path index before investigation.
It shares `/workspace/sightbreak/.git/objects`; no full clone was made. R5 and
all older branches/raw outputs remain untouched. Exact prior108 and new30 inputs,
results and report/rig are copied before implementation; old analyzer bytes are
retained under historical-source.

## Source-derived state model before implementation

The offline analyzer will retain schema/lifecycle checks and add a transition
validator, rather than attaching more rules only to directly emitted reasons.
Each transition uses observed cumulative call deltas, selected peer/generation,
authority epoch and cached stream observations. Its claim is limited to sound
constraints visible in those projections. Unknown ownership remains UNKNOWN and
diagnostically incomplete; it is not asserted to be invalid native behavior.

Snapshot cache and latest.snapshot_applied are copies of the same source header.
Require exact equality at every row, including both being empty before the first
application. The existing persistent metadata/counter rules then prevent cache
clearing, restamping or header changes without a counted application. Apply this
to all rows and retain inclusive millisecond timing bounds.

Every newly counted acceptance uses one shared header validator, whether direct
or coalesced: accepted epoch, count1..12, positive source endpoints, ACK+120 bounds
and fresh intent when all commands are exposed. A direct acceptance uses its
exact synchronous ACK. A hidden acceptance may precede a hidden consumption, so
its possible pre-accept ACK lies in a sound observed interval; do not compare
its sole command only with the later post-pop ACK. Count>=3 stale/duplicate
endpoints can hide a fresh middle command and remain valid.

Track selected stream state by peer/generation and epoch. ACK is absent-1 or a
positive popped sequence, never0. In the same lifetime it cannot regress or
clear, and cannot advance without a consumed call. Queue additions need accepted
calls; removals need consumption/skipping or a source-supported reset/forget.
Use local cardinality bounds from call deltas, tightening to the actual exposed
packet count when one acceptance is known. A direct same-peer receive-to-accept
interval has no await, so count1 cannot turn queue0 into2 or120. Epoch reset
clears queues/ACKs; stream replacement additionally resets rejection/skipped state.

Retain exact small queues only when ownership and all one/two-command keys are
exposed. Immutable queued identities and sorted pop/backlog truncation can then
be checked without inventing unobserved packet contents. Otherwise retain sound
cardinality/ACK bounds. For intervals containing one known accept and one known
pop, evaluate source-permitted event order using direct-row order/timestamps;
equal-clock hidden order may remain a set of alternatives. Never manufacture
packet identity from global latest metadata.

Acceptance ownership can be known from a direct current row, a single live
binding, or a forced one-call transition where a new empty stream must accept
before its sole observed consumption. This last case preserves the existing
coalesced second-peer positive. When multiple peers could own new global
metadata and the available evidence cannot determine a sound ACK context,
return explicit UNKNOWN/incomplete rather than a false complete report.

For rejection state with new calls dJ, a retained stream has state Cprevious+dJ.
If zero-peer epoch advance permits replacement, a fresh stream has state in
[0,dJ]. Validate the union of those alternatives, not every partial value up to
Cprevious+dJ. Ordinary live-binding epoch change cannot replace stream state.
Skipped state is also driven only by nonempty pops and optional replacement;
use its source bounds when validating queue removals.

## Evidence and scope gates

Before edits replay exact final30 with frozen old reader and retain its fifteen
false accepts. After freeze require exact30, prior108 separately, and meaningful
new transition positives/falsifiers in actual and initialized depth-one views.
Include valid hidden acceptance then consumption, stale endpoints hiding a fresh
middle, duplicate queued intent, reset/no-reset alternatives, snapshot persistence
and multi-peer UNKNOWN handling. Preserve original expectations and every failed
iteration. Any newly found historical positive contradiction needs independent
source adjudication and an explicit preregistered new fixture version; never
repair historical inputs or edit old report generators.

Allowed code is the offline analyzer and pure tests, including only independently
adjudicated minimum fixture corrections. No runtime, transport/RPC, controller,
authority, privacy/economy, native helpers, workflows or canonical documents
change. CPU4 Python/static/shell parsing only; no engine/API, native/process,
Mac review, CI, dispatch or actual attempt. Bind full non-document union, modes
and physical bytes including sparse omissions. Disclose initialized-depth object
storage and preserve setup failures. Freeze/push source then sealed builder
evidence for a different independent critic. Builder checks cannot approve
source readiness or any native/release gate.

## Independently adjudicated fixture expansion before edits

The R5 critic independently confirmed two older positive contradictions from
exact old bytes and InputStream source. Preserve both old inputs and verdicts.

The maintained queued-duplicate positive copies an original received queue0
after its first acceptance has already queued1, without any pop/skipped change.
Minimum correction is duplicate[0].queue_count=1 before restamp. Keep the duplicate
acceptance queue1, immutable original fireTrue, all mutations and assertion ASTs.
The old state test source and first failing focused output are retained here.

The prior normalized consumption_outside_accepted_batch positive has known
queue[21,22], only one pop and skipped0, but consumes22; its next tick also
regresses ACK22 to21. Label that exact source-inconsistent positive obsolete.
Add a distinct source-faithful version that keeps latest accepted22/A2/R2,
consumes21 with matching actor/ACK21 and queue1 retaining22, and carries those
consumed fields/queue through the terminal tick. This preserves the useful
distinction between latest accepted metadata and actual popped intent without
inventing packet identity. Do not change the historical case or expectation.
