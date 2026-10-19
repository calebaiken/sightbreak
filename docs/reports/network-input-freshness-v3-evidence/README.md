# Input freshness V3 evidence

See [the source-bound report](../NETWORK_INPUT_FRESHNESS_V3.md) for the defect,
declared gates, measured outcome, PR reconciliation, limitations and reproduction.

- Final baseline: [`baseline-r3/summary.json`](baseline-r3/summary.json), source
  `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`.
- Final candidate: [`candidate-r2/summary.json`](candidate-r2/summary.json), source
  `77f204083ab5bea4dc9149d3179daf540a994de4`; runtime change is `f3ceaad`.
- [`matched-run-r2-receipt.json`](matched-run-r2-receipt.json): exact outer commands,
  exits and wall durations of r2; [`baseline-r3-receipt.json`](baseline-r3-receipt.json)
  records the unchanged baseline retry after the r2 pre-admission allocation crash.
  [`baseline-r3-host-memory.json`](baseline-r3-host-memory.json) records available
  host physical/commit memory during that retry. Native workloads are sequential.
- [`verification.json`](verification.json): post-run recomputation from all raw
  authority/client timelines, exact identities and raw-log scans.
  Run `python verify_evidence.py` to repeat it without a game/source checkout.
- [`source-preservation-r2.json`](source-preservation-r2.json): protected Git-blob
  hashes, directory equivalence, all 13 RPC pairs and the one-file runtime diff.
- [`resume-gates/summary.json`](resume-gates/summary.json): the existing native
  interrupted-welcome and generation-bound alias confirmation gates on both sources.
  Their driver is [`test_resume_preservation.py`](test_resume_preservation.py).
- [`ATTEMPTS.md`](ATTEMPTS.md): chronology of all retained failed/preflight/earlier
  runs. `baseline-r1`, `candidate-r1`, `baseline-r2`, and all preflight directories are historical
  evidence; none is relabeled as the final baseline-r3 / candidate-r2 comparison.

Each final trial directory contains `server.json` and `client.json` (every sampled
physics row), `server.log` and `client.log` (unaltered native output), `metrics.json`
(declared measurements and gates), and the barrier/ready records. No credentials
are retained. The fixture uses guest sessions and an isolated collision platform.

The local `.gitattributes` preserves evidence bytes, including Windows newlines.
`checksums.json` hashes the published files except itself. These are native
headless source-engine tests, not rendered/exported-client, cellular, phone,
long-duration load or production deployment evidence. Independent critique and
aggregate integration acceptance remain separate.
