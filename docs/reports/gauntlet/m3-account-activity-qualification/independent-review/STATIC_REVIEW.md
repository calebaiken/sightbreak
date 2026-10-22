# Fresh evidence-tooling review

A separate fresh-context critic reviewed the five independent evidence scripts
and unchanged builder harness/probe before current-source execution. It launched
no native program, API, container or database query and edited no files.

The first oracle allowed a committed SQL sample before the worker-restarted
checkpoint. That checkpoint is written after successful acknowledgement, so this
could accept a first observation after acknowledgement. The critic supplied the
counterexample; the corrected oracle requires a committed sample no later than
`lost-ack-worker-killed.at_utc`, before the proxy releases its held reply. A missed
sample remains an evidence gap. The observer reconnects with a 1 ms interval after
the intentional outage, while gameplay sampling remains 50 ms.

The critic also found that reusing an existing output directory could overwrite
prior SQL samples and errors. The observer now rejects existing observation
directories; every attempt retains a separate immutable directory.

The raw recomputation does not itself join source and live-process receipts.
The qualification reviewer must independently compare the before/after commit,
game tree, file hashes and observed native process identity. Blocking iteration
over psql output can exceed the nominal observer deadline if Docker or psql
stalls. That remains a liveness limitation; it cannot supply missing SQL evidence
or create an accepted match. No additional correctness blocker was found in the
inspected unchanged account harness or probe.
