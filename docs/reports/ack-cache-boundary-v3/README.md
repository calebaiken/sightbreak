# PR21 per-insertion cache-boundary evidence

**Review complete:** [outcome-only PASS](https://github.com/calebaiken/sightbreak/pull/21#issuecomment-6354593942)
was frozen before identity access; the same critic subsequently recorded
[capture/API-binding PASS](https://github.com/calebaiken/sightbreak/pull/21#issuecomment-6354660494).
These links are parent-recorded summaries, not full critic transcripts.

The original `blind-traces.zip` remains unchanged: two raw 121-row traces and
neutral method instructions, with no runtime-identity key, source report, author
audit or earlier campaign results inside it.

ZIP SHA256: `70a15c1f330c7e9e51bf50fc52673243dd3cbe62dd030acdc60081eba6443517`.

The adjacent JSON traces and native logs are byte-identical to the external
capture. `source-receipt.json` identifies the frozen workload, engine and shipping
source hashes without mapping the new neutral labels to source identities.
`audit.json` is an **author-run** exact-position/window/parity check, not the
critic's verdict. `publication-audit.json` checks packaging and Git source hashes;
`checksums.json` binds the files in this directory except itself. Scoped `-text`
attributes preserve the raw bytes in Git.

The previously withheld native commands and source key are now released in
[`controller/`](controller/README.md), copied byte-for-byte from
`C:/Users/blith/AppData/Local/Temp/opencode/ack-cache-boundary-capture-r1/controller/`
after the frozen outcome review and subsequent provenance PASS. Their hashes match
the commitments in the original `publication-audit.json` at evidence commit
`d5c738d367f3ba80f3cfc679e104a009d0a72183`; that historical receipt remains unchanged.

Offline recomputation (does not launch Godot):

```powershell
python scripts/measure_ack_cache_boundary.py --audit docs/reports/ack-cache-boundary-v3
```

[Report, exact workload and parent-recorded review summaries](../ACK_CACHE_BOUNDARY_FOLLOWUP.md).
The parent review summaries are explicitly not full critic transcripts. Earlier
TIE and R-WINS evidence lives in its original directories unchanged. This trace
checks one cache eviction boundary, not gameplay accuracy or wire-level coverage.
Machine execution and historical filesystem measurements are author-run
attestations, not authenticated process attestation. PR21 remains draft and ready
for Sol integration review; integration is not claimed.
