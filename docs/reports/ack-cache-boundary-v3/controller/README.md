# Released PR21 controller archive

These are the **exact existing bytes** of `mapping.json` and `capture.json` from
`C:/Users/blith/AppData/Local/Temp/opencode/ack-cache-boundary-capture-r1/controller/`.
They were copied after both public review freezes and matched against the
`controller_only_commitments` in the already committed
[`publication-audit.json`](../publication-audit.json) at
`d5c738d367f3ba80f3cfc679e104a009d0a72183`. The parent directory's recursive `-text`
attribute preserves their original line endings.

| File | Bytes | SHA256 |
| --- | ---: | --- |
| [mapping.json](mapping.json) | 60 | `bb9e66d695b9d079fc5b55c99ba985aee4133052e55245b1de0315aeca7483b5` |
| [capture.json](capture.json) | 31,031 | `68aefbc9a5b3f0d397078b144f5e40993fdbe2e183a8154dcb1eecb488e393b2` |

## Review order

1. [Outcome-only PASS](https://github.com/calebaiken/sightbreak/pull/21#issuecomment-6354593942),
   GitHub timestamp **2026-10-23T00:42:29Z**, frozen before identity/source access.
2. The same critic then opened this existing controller and the source records.
3. [Capture/API-binding PASS](https://github.com/calebaiken/sightbreak/pull/21#issuecomment-6354660494),
   GitHub timestamp **2026-10-23T00:47:32Z**, recorded after the outcome freeze.
4. Byte-preserving public archive and docs closure.

These are **parent-recorded review summaries and links, not full critic transcripts**.
The [release receipt](release-receipt.json) pins both anchors and the existing
commitment blob. Machine execution and historical filesystem measurements remain
author-run attestations, not authenticated process attestation.

## Released identities

- **M**: frozen `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`.
- **T**: capture workload `b4b3db044fc762fbb5c9eb69da8713b316fdb496`, shipping content
  `0fbce120d8c17db58596d280f7d8401ab2aa0937`.
- Both used the same external workload; original raw evidence is
  `d5c738d367f3ba80f3cfc679e104a009d0a72183`.

The capture contains the native commands, raw trace/log hashes, three workload
hashes, engine/cache receipts and recorded before/after shipping checks.
[Report and reproduction](../../ACK_CACHE_BOUNDARY_FOLLOWUP.md#capture-and-review-procedure)
and [offline trace-audit command](../README.md) remain available. This closure is
docs/evidence-only; the original packets, native traces, logs and harness are intact.
