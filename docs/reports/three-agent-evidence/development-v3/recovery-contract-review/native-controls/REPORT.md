# Bounded source-PR reproduction: S1 predicates and S2 journal guard

**Both requested component behaviors reproduced in official native Godot 4.7.2 against exact Git `7b6f379a3f8c809d0985a64e883cbadfdd78d135`.** This is a bounded predicate/journal reproduction, not full-client, backend, security-authority, recovery-safety, or performance assurance.

## Observed S1: exact production receipt predicates

Production region: `game/scripts/ui/economy_ui.gd:597-608`, containing both complete functions `_valid_receipt_result` and `_receipt_integer`. The region was copied verbatim into a native `RefCounted` predicate component, with only `extends RefCounted` plus a blank line prefixed. The full UI and its dependencies were not imported. No private API aliases were used.

| Native invocation | Exact body | Observed result |
| --- | --- | --- |
| `_valid_receipt_result("/market/requested-listing/buy", body)` | `{"item":{"id":"unrelated"},"credits":0,"fee":0}` | `true` |
| `_valid_receipt_result("/cases/open", body)` | `{"item":{"id":"partial"},"roll":0,"table_version":"anything"}` | `true` |

Controls: **25/25 expected outcomes**: the two finding fixtures above; three synthetic legitimate-shape positives (market/case/store); seventeen clearly malformed shape/range/type negatives; and three direct integer-helper controls (whole float accepted, NaN/infinity rejected). All three legitimate-shape positives were accepted and all seventeen malformed shape controls were rejected. These are synthetic fixtures, not backend-produced or forged server responses. No HTTP status was generated or tested.

Evidence: `raw/native-A-ready.json`, `raw/native-A.json`, and matching literal JSON lines in `raw/engine-A.log`. The final A record has 36 passing assertions: 25 S1 plus 11 S2 assertions.

### S1 source inference only

At `economy_ui.gd:559-563`, a pending success body is replaced only if the predicate rejects it, then clearing is conditional on `_receipt_resolved` and `clear()` succeeding. At `584-586`, a result without `_error` resolves. This links the accepted bodies to conditional clearing **by source logic only**. `_send_transaction`, `_receipt_resolved`, the full UI, client and backend were not invoked. No additional authority contract is asserted.

## Observed S2: complete unfiltered production journal, distinct processes

Production module: complete, unchanged `game/scripts/ui/transaction_journal.gd`, including `stage():76-102`. Both processes used the same new canonical path:

`C:/Users/blith/AppData/Local/Temp/opencode/sol-recovery-contract-controls-20261024T0909404264087Z/state/pending_transaction.json`

| Sequence | Native observation |
| --- | --- |
| A, PID **12368**, new journal with initially null guard and absent pending/tmp files | `stage({})` returned **30 / `ERR_INVALID_DATA`**. Its newly acquired guard remained listening; no pending or temporary file existed. `load_pending()` returned `{}`. |
| B, PID **16660**, while A remained alive | B's `valid(pending)` was `true`; `stage(pending)` returned **22 / `ERR_ALREADY_IN_USE`**. B acquired no guard and published no file. The driver independently observed both distinct native PIDs alive and the journal file absent. |
| A exits; same B remains alive | The driver observed A exited before issuing B's retry signal. A did not call a private release function or clear a receipt. |
| Same B retries the exact same valid pending dictionary and canonical path | `stage(pending)` returned **0 / `OK`**, acquired a listening guard, published the receipt, and `load_pending()` equaled the original pending dictionary exactly. No `.tmp` remained. |

The published positive-control receipt is deliberately retained unchanged. SHA-256: `edad5580569295be12e51a65f9395457ef150b5b42710ee45b0f1e29c3309a01`.

Evidence: `raw/native-B-blocked.json`, `raw/native-B.json`, literal matching lines in `raw/engine-B.log`, and `raw/timeline.json`. The final B record has 13 passing assertions. There are **49 unique final A+B assertions**, not 88: intermediate snapshots repeat earlier assertions and are not counted again.

### S2 source inference and limits

- `transaction_journal.gd:77` acquires before invalid data returns at `82-84`; the native invalid-empty control demonstrates retained ownership at that return.
- Oversize (`86-87`), open failure (`88-90`), and later stage early returns were inspected but **not executed**. This result is not proof of every failure branch or of a full-UI route reaching invalid `{}`.
- `economy_ui.gd:543-550` returns before `_send_transaction` on stage failure. This is source inference only; **network count is not independently measured**.

## Source binding, containment and retained failures

- Pre-import manifest was persisted at **09:11:08.675753Z**, before the first launch at **09:11:08.769994Z**, and hashes the driver, unchanged prepared probe/config, source blobs, extraction, supervisor, Python, engine and calibration evidence.
- Engine: `4.7.2-stable (official)`, build hash `ed1daf0bf001b61586d9930840f2f1394092c079`, independently computed executable SHA-256 `ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424`.
- Approved CPython **3.13.15** only. Prelaunch memory/commit/disk records passed before A and before B while A lived: physical free **1,398,054,912 / 1,320,165,376 bytes**, commit free **3,191,660,544 / 3,127,607,296 bytes**. Minimums were 768 MiB physical and 1536 MiB commit; disk minimum was 512 MiB.
- Exactly **two** native launches, at most two simultaneous. Each had a configured 15-second timeout and prelaunch Windows Job Object containment via the frozen shared `run_process`, called with an open log handle. No editor, version-query, Match, campaign, export or full-game launch occurred.
- Both process receipts are exactly `{"complete":true,"exit":0,"errors":[]}`. GUI stdout logs are empty; each of the four persisted native completion JSON records matches exactly one actual engine-log line. Engine logs contain no errors. Exit 0 alone was not credited.
- Both native PIDs were confirmed exited again by the independent post-run audit. No private release, forced receipt clear, or weakened valid record was used.
- Owner Git status before/after this attempt is identical. No owner/integration source, snapshot UID, CI-repair file, DB, PG, HTTP service, GitHub object or commit was modified by this attempt.
- Old blocked bundle `sol-recovery-contract-controls-20261024T0857266917001Z` remains intact. Every old indexed file and its final index were hash-verified unchanged before execution and again after execution. Its missing-engine failure is retained, not replaced by this success.
- The prepared Godot probe and project config remained byte-identical. Driver-only engine-path/verification/provenance changes are declared in `CALIBRATION.md` and `calibration-provenance.json`. No additional failed or partial native attempts occurred in this resumed bundle.
- `post-run-audit.json` independently rechecks exact Git bytes/OIDs, frozen inputs, all native assertions, exact persisted JSON/log equality, process receipts, observed sequence, published bytes and old-bundle preservation. It passed without launching another Godot process.

## Key hashes

| Artifact | SHA-256 |
| --- | --- |
| Frozen complete `economy_ui.gd` | `a6580d176216af48c447eacaf3d293d7862fb8af0f56db7a4a3b9fd4398f450b` |
| Complete production journal | `3a7e060f7d5c3a65f4b983edf3c56d008cb070a8948bdcb128681bd4ce562d03` |
| Production predicate region 597-608 | `d03956cc6edf8fad989827bfa6b7f69dbca0247d484f6156b4d12e41f0ea521b` |
| Native predicate wrapper | `60b5006ed7336c3755321fccb5b25069b1c975f1300a95fadd3619b978daa347` |
| Unchanged prepared probe | `bb734d09ee8a314a487a02d77c2c06706b6fb4d5583031ff72b174ba0c3dde58` |
| Independent post-run audit JSON | `a95896721a4834e2b389902333ae48cd35fc16ddaf32388b75b2378978f7ddf0` |

Git blob OIDs: EconomyUI `c482c553264781db2a66a373ab4e4496fb59531a`; journal `cbac7a494f14c88127196c848a3f874892e7b94c`.

The main session remains responsible for the source-PR disposition. No broad recovery-safety, exploitability or performance conclusion follows from these two component reproductions.
