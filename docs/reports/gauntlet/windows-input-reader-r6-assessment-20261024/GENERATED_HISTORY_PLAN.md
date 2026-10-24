# Independent persistent-history generation, registered before execution

This additive assessment remains bound to captured UNFROZEN analyzer SHA-256
60e619383050839113f1e11fcd9cfdf836dec93686367f27df86cd540307db26. Original
239792ce, both older snapshots and all previous raw results remain unchanged.
The already registered13+5 repeat passes on this snapshot. Builder's newer
0d5db0f85116ca1db2496a0f8726025ed2358e47 is a different target: no verdict or
result will be transferred to it. Later testing requires an additive delta/
registration and sealed handoff as directed by root.

Before importing or running the candidate model, independently enumerate concrete
source histories using map staging (last duplicate wins in a packet), immutable
first queue receipt, valid sequence>ACK, and sorted minimum pop. Keep no reset,
no skipping and one bound stream in these tiny families; all queues are at most4,
below the backlog threshold. The independent oracle supplies the ground truth,
not ReceiptHistory or the builder's expected values.

Registered finite families:

- Keys1..3, fireFalse/True, first packet length1..3, second length1; both accepts
  before final drain. This exercises unknown middle keys, duplicate payloads and
  alternative first-receipt origins across more than one packet.
- Same packets, with a real observed sorted pop between the two accepts; discard
  second packets that are fully acknowledged (source would reject them). Preserve
  the intermediate pop and ACK as part of the visible history. This challenges
  cached ACK/cardinality cutoffs and immutable earlier receipt budgets.
- Keys1..2, independent fire and reload bits, both packet lengths1..2, both accepts
  before final drain. This tests joint persistent action budgets across packets,
  rather than only one Boolean aggregate in one packet.

Group enumerated histories by BOTH packet projections/counts, observed queue
sizes and any intermediate pop/ACK/control values. Store ALL possible final
immutable queue payloads for each such prefix. Candidate completions enumerate
every sorted key set in the named key domain of the observed queue size and all
named control assignments. A completion is VALID iff one independently enumerated
source history has that prefix and final queue. Otherwise it is INVALID, not
merely different from one selected source witness.

For unexposed middle keys, the finite oracle is closed for these fully drained
completions: any additional first-receipt key outside the named domain would
remain queued or appear in a pop. There is no reset/skipping or unobserved removal,
and the optional first pop is fixed by the visible prefix. Therefore an outside
key cannot witness a final complete drain whose observed keys all lie inside the
named domain. This argument does not apply to an arbitrary incomplete capture;
no terminal runtime coverage or whole packet identity is inferred.

Use the independent SourceOracle to project callbacks with unchanged-control
coalescing and a flushing authority tick after each accepted packet/pop, keeping
at most one new local acceptance/pop per model interval. For VALID completions,
retain an actual source witness. For INVALID completions, retain the fixed
projected prefix and counterfactual drain, the complete oracle completion set,
and why no witness exists. Save every generated case/outcome in compressed JSONL
plus summary hashes/counts and individual mismatch fixtures. Cases expected from
the oracle are fixed before candidate execution; do not normalize mutated inputs.

Classify MODEL_ACCEPTED_INVALID, MODEL_REJECTED_VALID and UNKNOWN separately.
UNKNOWN is not a false complete verdict or proof of source invalidity. These
are isolated InputTransitions model tests, not full-analyzer/native/API approval.
All execution CPU4 pure Python, no process/native/Mac/CI/canonical changes.
