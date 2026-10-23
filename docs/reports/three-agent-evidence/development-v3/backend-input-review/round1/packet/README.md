# Anonymous trade-read measurement packet

Two opaque variants, **K** and **R**, were randomly assigned after the recorded
measurements completed. Neither label denotes a preferred implementation. This
packet contains the retained measurements, not a fresh execution or a source
review. Assess the evidence before learning the identities.

Start with `METHOD.md`, then inspect `K/measurement.json`, `R/measurement.json`
and `equivalence.json`. `REVIEW_QUESTIONS.md` defines the requested critique.
`SHA256SUMS.txt` covers every other packet file. The optional standard-library
`verify_packet.py` checks those files and recomputes summary arithmetic without
accessing a database, network, repository or implementation.

Give the reviewer **only this directory**, without surrounding conversation,
implementation branches, earlier reports or the external identity key. The
controller retains the mapping and original-input checksums outside this packet.
Do not navigate parent directories or search for the original measurements until
the pre-unblinding critique is saved. This is identity blinding, not a claim that
the measurements conceal their performance characteristics.

## Evidence boundary

- All fourteen workload records and all 140 timed samples are retained, including
  SQL shapes, statement counts, timing summaries, recorded budgets, response
  fingerprints and read-only results.
- The field named `response_sha256` hashes the canonical **expected fixture
  response**. The measurement routine asserted each actual response equalled
  that fixture. Actual response bodies were not retained in these records.
- The `read_only` result records equality of full authoritative-table snapshots
  before/after a workload. **The snapshots and their before/after hashes were not
  retained.** The packet marks those hashes as unavailable; there is no
  independent state-hash equivalence proof to recompute.
- Branch/checkout names, commit/tree/file identities, original timestamps,
  database identifiers and source-relative measurement filenames are withheld
  in the external key. Common runtime versions are retained.
- No author performance verdict, implementation diff or differently sized test
  suite results are included. Distinguish measurement acceptance from source,
  privacy, monetary-integrity and deployment acceptance.
