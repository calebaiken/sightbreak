# R6 interval necessities — registered before implementation

Root owns this NEW branch/worktree from frozen R5 handoff1e045025; Objective
continues the separate Linux protocol and will not edit R6. Old R5 stays frozen.
Root authored R3/R4, Objective R5; SAME different Windows critic will evaluate
new R6 and its composition. No self-approval or fresh/blind context claim.

Benchmark: sealed independent R5 REVISE43a89037, especially the source-complete
R2 callback witness and three later same-stream ACK/queue contradictions. The
original witness must remain UNKNOWN, and ACK clear/regression/queue growth must
be INVALID despite earlier anonymous ownership. R1 omitted post-tick pops; retain
it but do not treat it as complete-callback evidence. No actual207 replay/native.

Source model: InputStream.accept adds at most12 unique positive commands to its
selected peer; accepted queued duplicates may add zero. pop removes one command,
optionally discarding backlog first, and strictly advances that peer's ACK.
Observer C counts every nonempty pop before possible coalescing. skipped is global,
not a per-peer count. forget follows an always-emitted disconnect, and both reset
operations advance authority epoch. Connection generations are never reused.

For a previously observed still-bound (peer,generation,epoch), compare necessary
interval facts using its own earlier observation, even across other selected peers.
ACK cannot clear/regress; no global consumed increment means unchanged ACK. If
the latest newly consumed record identifies this stream, its ACK must equal that
immutable sequence. Queue size is bounded below by old size minus all global pops
and skips, and above by old size plus12 times all global acceptances, capped120.
These bounds are deliberately conservative: no anonymous packet allocation,
forced queue ordering, local skipped count or ACK-jump upper bound is invented.
Preserve uncertainty rather than resume the partially mutated inference engine.

Implementation scope: add one deterministic interval validator, initialize/call
it in analyze_role after existing direct/binding checks and before deferred queue
inference. Retain old InputTransitions and every old engine/schema/observer/game,
privacy/default flag, deadline and callback. Add dedicated operation-derived
tests, generated single-field contradictory siblings, mixed-owner/select-switch
positives, pending RX/queued duplicates and genuine epoch/disconnect boundaries.
No broad fixture normalizer/helper/assertion change. The separately supported
23-leaf old constructor amendment may be applied ONLY from its exact sealed data,
after verifying all other bytes/assertions/tail/mutations and retaining original
literal method/results. If not applied, label the original failure unchanged.

Run new pure controls, all frozen49 and independent3060 source-model expectations,
then the literal maintained suite with every failure preserved. Every legacy
failure remains individually visible; no whole-reader qualification follows.
Verify all source paths/modes and declared deltas; freeze a concrete candidate
for SAME independent critic. No proc/pidfd/signal/API/SDK/engine/helper/CI/study/
capability attempt or platform acquisition is authorized by this registration.
