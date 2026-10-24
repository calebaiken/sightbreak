# R5 phase boundaries before candidate execution

The deterministic main pass retains every existing assertion and lifecycle/direct
pipeline state update. It records immutable (row, owners_before) snapshots rather
than invoking the mutable queue model mid-pass. Foundation UNKNOWN and queue
UNKNOWN are deferred independently after that pass; a queue UNKNOWN stops further
queue inference because its state may be partially updated. This does not prove
closure of all unresolved receipt histories, and never resumes guessed state.

Ownership-independent necessities from InputTransitions also run in the first
pass: epoch order; global skipped-count versus observed pop/reset budget; live
consumed metadata identity/actor; ACK domain; empty newly connected/bound/absent
streams; live acceptance context; newly counted accepted header count/endpoints
and epoch within the observed interval. Context-dependent ACK/window, cardinality,
origin/immutable-command flow and bounded-search facts stay in the final model.
All original model assertions remain as well. A later independent definite row
can therefore reject before an earlier queue/foundation UNKNOWN escapes.

The packet ledger stores observed receive projections by their global ordinal,
not a reconstructed packet. For a direct outcome, or an interval whose completed
outcomes all have that kind, its latest outcome belongs to A+J. Compare only when
that receive ordinal was actually observed. A current direct receive may expose
the next pending ordinal, so the comparison may use the previous cached receive.
Mixed hidden A/J outcomes do not identify the latest kind ordering and do not
trigger an arbitrary latest-packet comparison. Both kinds receive the same raw
Dictionary in source; InputStream.accept sanitizes copies. Direct stream-rejected
rows are not source-emitted by the observer; tests will expose rejection metadata
at later emitted ticks, preserving that source fact. New actual tests use source
operation clocks and do not normalize incoming evidence.

Initial new report git-add was refused while outside inherited sparse paths;
adding only this report path allowed prereg0988ba43 to commit before source edits.
No candidate test has yet executed. R4 source/literal outputs remain immutable.
