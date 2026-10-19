# PR19: separately mapped blind evidence handoff

This is an **evidence-only addition** requested after the completed measurements.
The frozen implementation/tests/harness remain
`4a8e9ea73aa8b286d9f1751b0a6b485479737294`; original raw evidence remains at
`4a7ba36216bf354d266b508222aea4cfea30bfea`. No application or database tests were
rerun, no runtime/source-harness files changed, and no critic was spawned.
PR19 remains draft. The loopback PostgreSQL instance was left available for the
coordinating session's separate work.

## Blind packet

Give a fresh critic **only** this directory, without this handoff/report,
conversation history or the repository containing labelled results:

```text
C:\Users\blith\AppData\Local\Temp\opencode\blind-trade-read-f12a80a71bbd\packet
```

An exact-byte archival copy is committed at
[`backend-trade-read-v3/blind-packet-f12a80a71bbd/`](backend-trade-read-v3/blind-packet-f12a80a71bbd/).
Use the isolated Temp copy for the fresh review; browsing the surrounding
repository would expose labelled earlier results.

The **SHA256 of the packet's `SHA256SUMS.txt`** is:

```text
d9a6ea8e0721d573bea5437e84fcc25b899d7b8172f092c4ae7d1415b3c56c36
```

It covers seven files: the two anonymous measurement records, symmetric
equivalence data, method, README, acceptance questions and a read-only
standard-library file/arithmetic verifier. The packet contains **14 workload
records and all 140 timed samples**. A single cryptographic shuffle assigned
opaque K/R labels. The controller-only identity key, raw input paths/checksums,
original headers, transformation script and packet fingerprints are held in a
separate directory outside the packet and repository. Its exact path is supplied
privately to the coordinating session; the mapping is not committed or disclosed
in this handoff.

Original workload rows are copied without changing any counts, timing samples,
summaries, SQL shapes, recorded budgets, response fingerprints or read-only
booleans. Source/checkout labels, commit/tree/code fingerprints, absolute run
times and database IDs are withheld. Shared environment versions are retained.
Original raw-file checksums were verified against the prior evidence manifest
before the transformation. The file/arithmetic verifier checks all packet
checksums and recomputes all summary arithmetic without application/DB access.

## Explicit evidence gap

**Authoritative-state hashes cannot be supplied from these completed records.**
The routine compared full authoritative-table snapshots before/after each
workload and retained the equality boolean, but saved neither those snapshots
nor their hashes. The blind packet preserves the recorded booleans and marks
hashes `null / not_retained`; it never treats nulls as an equivalence proof.
Producing hashes would require a separate newly authorized measurement.

The raw `response_sha256` also needs precise interpretation: it hashes the
expected canonical fixture payload after each measured response was asserted
equal to it. Actual bodies/per-response digests are not retained. This is stated
in the blind method and made an explicit critique question. No stronger proof
was manufactured during packaging.

## Critic handoff

Ask the reviewer to read `README.md`, `METHOD.md`, both measurement files,
`equivalence.json` and `REVIEW_QUESTIONS.md`. The review should independently
recompute query/timing summaries, assess SQL/count consistency and both batching
boundaries, distinguish expected-response fingerprints from actual-body proof,
flag missing state hashes, limit latency extrapolation, separate monetary/source
contract safety from read measurements, and identify the largest residual gap.

Required verdicts are separated into packet integrity, measured query efficiency,
latency generalization, response equivalence, independently auditable state
preservation and source/monetary-contract safety. Save the label-specific verdict
outside the packet **before opening the external key**. Any later change of
judgment belongs in a separate post-unblinding addendum.
