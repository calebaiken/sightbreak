# Review chronology and strength of evidence

All times below are UTC on **2026-10-19**. This is a reconstruction from the original receipts and unchanged artifacts, not a new test campaign. Exact timestamp strings, argument arrays, hashes and ledger line numbers are in [chronology.json](provenance/chronology.json).

| Time | Event | Basis |
|---|---|---|
| 18:53:44–18:53:45 | Official native engine version queried | `evidence/commands.jsonl`, `engine-version` |
| 18:54:22.7319153 | Plaintext neutral-label source manifest created | Later-observed original NTFS creation/write metadata |
| 18:54:22.7843523–18:54:48.2980330 | North editor import completes, exit 0 | `north-import` receipt; both raw streams included |
| 18:54:48.3285839–18:55:02.2208329 | South editor import completes, exit 0 | `south-import` receipt; both raw streams included |
| 18:55:48.7552208 onward | Same retained probes run under neutral labels | Both `evidence/runtime-*/commands.jsonl` ledgers |
| By 18:56:02.4906154 | North module, authority, integration and objective probes complete | Original receipts |
| By 18:55:57.7017450 | South retained suite completes; four parse failures, standalone failed-buy control succeeds | Original receipts and raw errors |
| 18:56:02.5233639–18:57:21.8167726 | North extended sweep runs to completion | Original extended-sweep receipt |
| **18:57:36.2493789** | **Neutral first assessment authored** | Original artifact creation/write metadata; unchanged text included |
| 18:58:01.3020348 | First recorded candidate diff retrieval starts | Root `exact-diff-stat` receipt |
| 18:58:04.1290189–18:58:04.3512589 | Candidate commit-claim retrieval | Root `candidate-commit-claims` receipt; raw output included |
| 18:59 onward | Strict actor/API and adapted behavior diagnostics | `evidence/extra-*/commands.jsonl`; individual times preserved there |
| 19:08:12.1370977–19:08:13.7717557 | Fixture-free north match compile, exit 0 | Direct compile receipt |
| 19:08:15.5809779–19:08:16.2638817 | Fixture-free south match compile, exit 1 | Direct compile receipt and missing-API errors |

## Necessary qualifications

- The [original assessment](evidence/neutral-first-assessment.md) states that it was written before reading the label mapping, candidate diff or candidate claims. This reviewer attestation is preserved. No timestamped file-read audit exists to prove the absence of earlier reads.
- The mapping was a plaintext file created during setup, not encryption or a cryptographic blind. V2 source was read to understand the expected contracts. **Do not describe this as a perfect double-blind experiment.**
- The assessment calls the north extended sweep “long-running” and “not yet used.” Its receipt proves the process had actually finished about 14 seconds before the assessment file was written. The defensible distinction is **not yet consumed in the assessment**, not still executing. This clarification does not alter the original text or receipt.
- NTFS metadata was captured later during publication. It corroborates the recorded ordering but is mutable filesystem metadata, not a signed timestamp or read event. Copy timestamps in this publication are not treated as review event timestamps.
- The first retrieved candidate claim was the commit message. Its retrieval receipt is not proof of the exact instant the text was read.
- Original failures and retries are retained: [initial-attempts.md](evidence/initial-attempts.md), `evidence/host-failures/`, invalid neutral JSON, original import-status check and all retained-V2 `.log` files. Missing pre-ledger raw output is described as a recorded narrative, never reconstructed and labelled raw.

## Publication step

The later docs-only task copied and hashed evidence under this directory. It did not run native probes, import integration, modify owner/runtime branches or publish a GitHub review. The user's separately published PR14 comments are outside this package's execution record. The original report's historical statement that it did not modify `sightbreak-v3` applies to the original QA campaign; this authorized publication adds only this docs directory.
