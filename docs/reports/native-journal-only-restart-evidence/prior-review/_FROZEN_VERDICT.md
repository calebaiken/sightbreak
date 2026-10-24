# Frozen independent blind verdict

**WIN: Set-8F5F7604, limited to the recorded stable postcommit / withheld-response / native-process-kill recovery scenario.** Set-8F5F7604 is **supported in 3/3 cases**; Set-673EECBC **failed exact receipt recovery in 3/3 cases**. Both groups settled each initial purchase once and showed no additional economic effect after either restart. This is a recovery distinction, not evidence of duplicate settlement in the failing group.

This verdict was fixed using only the supplied ZIP, before any source/version mapping or controller provenance was revealed. No application, database, native-client, or new behavioral test was executed.

## Integrity and independent reconstruction

- ZIP SHA-256: `35c9ddb2bda1198b90c57073f450cebca35d066796a34b36f775331b94e38c8a` — matched.
- MANIFEST.json SHA-256: `36f5f6610a2c8a43121ced32546bcceb0d313850e15cb1e1cce1f9d4ae04d6cf` — matched.
- All **122 manifest-listed payloads** matched their lengths and hashes; the extraction initially contained exactly those files plus the manifest.
- Independently parsed all **6 cases / 30 SQL-stage files**, all timelines, 18 native stdout captures, 18 empty stderr captures, and all journal captures/available bytes. Compared raw data before checking the producer's summaries. Python integers retained nanosecond precision; Decimal comparisons preserved native/HTTP numeric semantics.
- `_independent_audit.py` and `_independent_audit.json` in this extraction reproduce the row-level, request, response, journal, session, and ordering checks. The final analysis evaluated 2,078 consistency checks with zero unresolved mismatches. These are checks of supplied observations, not independent attestation of the recorder or new application tests.

## Exact economic result

Stage notation: **B** before, **C** committed-before-kill, **K** after-kill, **R** after-recovery, **S** after-second-restart. For every case, **C = K = R = S across all nine complete economic tables**, including existing unrelated rows and the exact Operation/Ledger/Audit rows.

The same per-case amounts occur in both groups:

| Case | Integer price | Buyer B -> C/K/R/S | Seller B -> C/K/R/S | Fee burn | Added Ledger amounts |
|---|---:|---:|---:|---:|---|
| case-01 | 400 | 2,000 -> 1,600 | 2,000 -> 2,388 | 12 | -400, +388 |
| case-02 | 401 | 2,001 -> 1,600 | 2,000 -> 2,389 | 12 | -401, +389 |
| case-03 | 10,000,000 | 10,001,600 -> 1,600 | 2,000 -> 9,702,000 | 300,000 | -10,000,000, +9,700,000 |

The 401-price case burns **12**, not 13. Fees equal the loss in total player credits, agree with the response and settlement audit, and are consistent with integer-floor application of the catalog's 300 basis points. Each player's entire ledger and every running balance reconcile with their recorded credits at all five stages.

Unfiltered table-count tuples below are **(Player, Item, Listing, Operation, Ledger, Audit)**. The right-hand tuple applies separately to C, K, R, and S. Loadouts/rewards/trades are zero at every stage.

| Packet path prefix | B -> C/K/R/S | Session counts B/C/K/R/S |
|---|---|---|
| `Set-673EECBC/case-01/` | (6,3,1,0,6,4) -> (6,3,1,1,8,5) | 6/7/7/8/9 |
| `Set-673EECBC/case-02/` | (6,3,2,1,8,6) -> (6,3,2,2,10,7) | 9/10/10/11/12 |
| `Set-673EECBC/case-03/` | (6,3,3,2,10,8) -> (6,3,3,3,12,9) | 12/13/13/14/15 |
| `Set-8F5F7604/case-01/` | (10,9,1,0,10,10) -> (10,9,1,1,12,11) | 10/11/11/12/13 |
| `Set-8F5F7604/case-02/` | (10,9,2,1,12,12) -> (10,9,2,2,14,13) | 13/14/14/15/16 |
| `Set-8F5F7604/case-03/` | (10,9,3,2,14,14) -> (10,9,3,3,16,15) | 16/17/17/18/19 |

Sources are each prefix's `01-before.json` through `05-after-second-restart.json`, not the summary counts. Each initial settlement changes only two Player credits, one Item's seller ownership/market reservation to buyer ownership/no reservation, and one Listing from active/no buyer to sold/original buyer; it adds exactly **1 Operation + 2 Ledger + 1 market_settled Audit**. Each buyer gains one item and each seller loses one; no item is minted, consumed, or duplicated by settlement. Prior-case rows stay unchanged. Between cases only the next fixture listing, its listing audit, and its item's reservation are introduced.

Total credits from first B to final S: **10,011,601 -> 9,711,577** for Set-673EECBC and **10,019,601 -> 9,719,577** for Set-8F5F7604; each burns **300,024**. The latter's extra initial rows are four Players/four fixture-credit Ledger rows, six Items/six item-mint Audits, and four Sessions, consistent with the packet's seed explanation. They are not extra purchases.

## Receipts, authentication, and process evidence

| Packet case | Original receipt UUID | Native PIDs send/recovery/second | Purchase requests send/recovery/second | Exact recovery |
|---|---|---|---|---|
| Set-673EECBC/case-01 | dcc30c2f-0ada-4814-82c9-36afb3e2fdaa | 11516/16844/14204 | 1/0/0 | failed |
| Set-673EECBC/case-02 | 2bd715ad-1347-43ae-80da-45a520755248 | 22392/8528/23872 | 1/0/0 | failed |
| Set-673EECBC/case-03 | 5790bbdf-d686-4496-8b98-43008b31abaf | 21492/21856/20904 | 1/0/0 | failed |
| Set-8F5F7604/case-01 | 5b738b74-378c-4b9e-a419-73572c984d86 | 22304/24420/22552 | 1/1/0 | supported |
| Set-8F5F7604/case-02 | 507c37e7-7de4-499d-b03e-4b60d5d1e206 | 14060/2368/21868 | 1/1/0 | supported |
| Set-8F5F7604/case-03 | 3ea73f56-634f-4436-be82-2eaa8075e58c | 16160/19404/21184 | 1/1/0 | supported |

In all six `timeline.jsonl` files, lines 18-27 bind the original purchase to upstream HTTP 200, response hold, independent SQL visibility, kill request, matching native exit (return code 1), kill confirmation, after-kill SQL, zero-byte discard, then recovery launch. SQL backend PID/database fields match the corresponding stage files. No original-purchase response-delivery event appears. Native authentication/perform events match the original buyer, path, receipt, and strict integer payload on the wire.

Example: `Set-8F5F7604/case-01/timeline.jsonl:20-27` records hold at `1792715863047789400`, SQL snapshot at `1792715863215748300`, kill request at `1792715863220625200`, confirmed exit at `1792715863282637900`, discard at `1792715863446702500`, and recovery start at `1792715863662415700` (wall ns). SQL clock `2026-10-22 20:37:43.153954-04:00`, connection PID 19404, lies between hold and kill. Original native PID 22304 is the PID terminated. Equivalent ordering was checked for all six. Adjacent events sometimes share a timestamp; event order and nondecreasing clocks are retained, without inventing strict sub-clock resolution. Monotonic values were never compared across group invocations.

Each case has **three distinct fresh login digests**, matched from native stdout and authenticated HTTP requests to newly added SQL Session rows, original buyer ID, and exact login expiry. Earlier sessions remain; no bearer reuse is required. The original server string agrees between fixture and saved transaction/native pending state where present; the timeline/database remains consistent. HTTP records retain paths rather than independently attested destination hosts.

For all six original purchases, **SHA256(captured raw request UTF-8) = Operation.request_hash**; Operation ID binds buyer, listing, and the UUID above; its full response equals the original held HTTP result. For Set-8F5F7604, all three recovery bodies are **byte-for-byte identical** to the original integer request. Recovery HTTP 200, stored Operation response, original held result, and full native recovery result agree semantically, allowing whole-number native floats and JSONB key order.

Set-8F5F7604's raw journals survive the kill byte-identically: **303/303/308 bytes** for cases 01/02/03. Independently recomputed SHA-256 values match their captures. Parsed contents contain only schema and transaction metadata: original owner/server/method/path/message/payload; no bearer, token, password, or authorization field/marker occurs in the actual journal bytes. After recovery, journals are absent and native pending state is empty. Second restart has empty pending state, zero purchase requests, and complete economic equality.

Set-673EECBC has captured journal absence before and after kill, empty pending state on both restarts, **no recovery purchase request**, and native `result: {}` despite refreshed balance/inventory. This is lost receipt recovery, not rejection or duplicate settlement.

## Strongest contradiction, gap, and next falsifier

The strongest demonstrated failure is **a committed sale whose receipt is forgotten** in all three Set-673EECBC cases. Their `result.json` files nevertheless mark `authoritative_pass`, `complete_result`, and `stable_journal_at_kill` true. Those flags cannot mean successful recovery: the same files explicitly say `recovered:false`, and `recovery.stdout.txt` plus the journal/HTTP records show the empty result and no replay. A stable absence is not a surviving journal. I found no contradictory economic or recovery trace in Set-8F5F7604.

The meaningful remaining gap is **causal/provenance independence**. The external driver and proxy/SQL-reader source are withheld; every restart logs `read_fixture`. The supplied records consistently show journal restoration, but cannot independently exclude fixture-assisted recovery or attest the proxy's zero-byte instrumentation. Hashes establish packet integrity, not truthful instrumentation or a shipping implementation's identity. This limits attribution, without turning a coherent observed comparison into a tie.

**Strongest next falsifier:** repeat the same declared boundary with a recovery process given only credentials/original server and the surviving journal, with the original purchase fixture/receipt unavailable and independently inspected or attested instrumentation. Failure to recover that exact original UUID/integer body/full committed result, or any additional Operation/Ledger/Audit effect, falsifies the supported recovery claim. This was not run here.

Scope exclusions: stable aftercommit process termination does not establish arbitrary instruction-window, interrupted journal write/rename, storage flush, backend crash, or power-loss durability. This is an existing-account headless native direct-method test (`_authenticate`, `_perform`, `_retry_pending`), not demonstrated human confirmation/manual UI behavior or physical-device qualification. The SQL records date the invocations October 19 and October 22, 2026 (-04:00); they are not a latency comparison. The three cases are specific examples sharing a database per group, not a statistical reliability study. The outside ancillary 36/37 and calibrated 37/37 claims are unverified here and contribute zero additional recovery cases.

**Frozen conclusion: Set-8F5F7604 wins this packet's scoped recovery comparison; broader durability, UI, instrumentation provenance, and source/shipping identity remain unestablished.**
