# PRIVATE — exact-commit recovery source review

## Status and scope

Prepared by an independent source critic/evidence preparer. **This is not a blind outcome verdict or a new native replay. No baseline/candidate improvement is claimed.** Hand only `NEUTRAL/` to the next, fresh critic; withhold this directory, the root report, and the private key.

Reviewed Git objects:

- Recovery source: `7b6f379a3f8c809d0985a64e883cbadfdd78d135`.
- V2 source: `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`.
- Merge comparator: `d2439acdd5f73df7bae5ada62ee1e3dec2cf30db`.
- Published native-client/PostgreSQL evidence: `49268b8702c44a6a19adfc743727f5aad2a10e8b`, locally resolving from `origin/astra/pr18-native-pg-evidence`.
- Common measured tooling: `31438cbcea6ef08a131ae312c65b94f7e3e882c3`.

Only Git reads, standard-library offline Python 3.13.15, and writes to this new external review directory were used. No application, engine, database, service, GitHub comment, owner-latest assertion, or live network oracle was run/read. No project module was imported. Source citations below use canonical Git-blob line numbers, which are unchanged by the archive's CRLF line endings.

Workspace isolation limit: another actor's activity is evident during this review. HEAD moved from `2a026e61cabee3c66334066d45e92eb3ec6c2641` (initial clean status) to `88bfc51da026be42b3dec517817459ed89630ded` at the first verification, with unrelated modified/untracked files and no staged paths. None was edited or reverted by this agent. All reviewed source and evidence inputs came from the explicitly named immutable objects, not the changed checkout. The requested evidence ref still resolved exactly. The observed workspace changes are not credited as review output or treated as author evidence.

`701ce2c` and `d2439ac` have zero scoped differences in `backend/`, `game/scripts/ui/`, `game/scripts/profile.gd`, and `game/scripts/network/economy_bridge.gd`. The published native comparator was **701ce2c**, not a separately measured d2439ac runtime. Scoped source equivalence does not establish full-build runtime equivalence.

## Findings that prevent unconditional sign-off

### S1 — Partial or unrelated plausible successes can clear the receipt (P2 contract gap)

At recovery-source `game/scripts/ui/economy_ui.gd:559–566,584–608`, successful responses are validated only by:

- a nonempty string `item.id`;
- for cases, integral `roll` in 0..9999 and a nonempty string `table_version`;
- for store/market, a bounded integral `credits`; market additionally has a bounded integral `fee`.

`item` can otherwise be incomplete, the ID need not be a UUID, a market fee need not match the consented price/rate, and no response field binds the returned receipt to the original actor/route/key/body hash. After that shallow check, `_receipt_resolved()` treats any non-error as resolved and `clear()` removes the record. `game/tests/transaction_journal_test.gd:98–100,143–144` deliberately uses skeletal successes as clearing confirmations; its malformed-response loop at 83–97 does not test a skeletal item *plus* sufficient scalar fields.

Concrete source-level counterexamples are a market 2xx with `{"item":{"id":"unrelated"},"credits":0,"fee":0}`, or a case 2xx with `{"item":{"id":"partial"},"roll":0,"table_version":"anything"}`. They pass the implemented validator. This was established by inspecting the predicate, **not** by executing GDScript or fabricating a runtime result. It does not demonstrate a forged response from the pinned authoritative backend, whose normal response construction is complete. It blocks a broad assurance that *all* malformed or wrong-receipt successes retain uncertainty.

Countercontrol to require before that stronger assurance: inject these responses for each keyed route after a genuinely unresolved first attempt; retain the exact journal bytes and show no clear/reveal. Also try a wrong item/definition, an impossible fee for the saved consent, and a response for another key. Full success-schema validation helps; explicit server receipt identity/status (actor, route, key, canonical request hash) is needed for client-verifiable exact binding. Preserve legacy semantics deliberately rather than silently inventing a new authority contract.

### S2 — Newly acquired guard survives staging failure with no request (P2 liveness)

`game/scripts/ui/transaction_journal.gd:76–102` acquires the listener first. Returns for an invalid record, oversize record, missing/unwritable parent, failed temporary write/readback, rename failure, or failed published readback do not release a newly acquired guard. The only explicit release sites are a newly acquired stale `claim()` at 34–43 and successful `clear()` at 113–120. The long-lived EconomyUI retains the journal object after `_perform()` returns a storage error (`economy_ui.gd:543–550`). A second process can remain blocked even when the first failed before publishing any receipt and sent nothing.

This fails closed and is **not** a demonstrated double-spend or data-loss path. It is a concrete release/liveness asymmetry relative to the stale-claim fix. Countercontrol: keep process A alive after invalid/oversize/unwritable staging with no prior record; then attempt a valid stage from process B using the same canonical path. Check A's network count is zero, B's admission, and the listener lifetime. Release only a newly acquired claim when safe to do so; never delete an uncertain published record merely to make this control pass. Include failed-post-publication readback as a distinct case.

### S3 — No authoritative closure for a never-committed uncertain receipt (design limitation)

`economy_ui.gd:591–595` intentionally preserves **every** failed recovery, including 400/404/409/422, because a later refusal does not fence an older in-flight attempt. The backend remembers successes only (`backend/app.py:127–141` and keyed handlers at 218–245,280–297). If the first request never committed and the target is now permanently unavailable, there may be no successful receipt to recover; all further mutations through this UI remain blocked (`economy_ui.gd:538–540`).

The conservative retention is correct for current safety semantics. Do **not** “repair” it by clearing on a retry 409 or timeout. A durable, transactionally serialized status/abandonment fence would be needed for safe finite closure. Countercontrols: an older request delayed behind the economy lock while a recovery is refused, versus an original request definitely rolled back and a permanently invalid target. Distinguish those cases without weakening original-key replay. No such protocol exists in the reviewed source.

## Verified source contracts and their limits

| Contract | Exact source | Independent review conclusion / required control |
|---|---|---|
| Persist before dispatch | `economy_ui.gd:529–557`; journal `76–111` | Staging runs synchronously and must return OK before `_send_transaction()` calls the API. Temporary close/readback, same-directory rename, then published readback occur in that order. There is no await between staging and dispatch. Countercontrol: truncate/fail each write, close, readback, rename, and published-readback boundary and require zero mutation requests. |
| Buffer flush/readback | journal `91–111` | Checks `store_string`, `get_error`, length and exact bytes after close on both temporary and published files. This is stronger than trusting `flush()` alone. It proves neither fsync nor directory metadata durability after power loss; readback can be satisfied from the OS cache. Process-termination scope only. |
| Original route/body/key | `economy_ui.gd:507,523,541–552`; journal `70–74,122–152` | A deep copy of the payload, POST method, path, owner, server and message is saved. Retry sends the saved copy, not a newly generated key/current price. Non-whitelisted payload fields are refused. Recovery restores integral JSON price to an actual integer, preserving omitted/null semantics. |
| Consent capture | `economy_ui.gd:1305–1308,1367–1368`; store `1021`; case `1140–1145` | Actual market card captures integer displayed price and includes it in the confirmed request. Store/case generate a key for the confirmed action. The native restart probe enters `_perform()` directly and casts fixture price at probe line 19; it does not independently execute this market button gesture. |
| Original account/server and fresh auth | `economy_ui.gd:355–382,504–523`; `economy_api.gd:8–29,47–57` | Retry requires exact original `player_id` and normalized configured server string plus a nonempty current token. URL reconfiguration logs out; redirects are disabled. No automatic retarget, substitute account, token restoration or local-balance fallback occurs. Countercontrols: wrong account, same account/different server, expired/empty token, then correct fresh sign-in; no wrong-scope mutation request. |
| Sign-out/401 preservation | `economy_ui.gd:384–405,473–489` | Sign-out clears auth/account views, not the journal; 401 clears the online session/view and states that an older receipt remains unresolved. |
| Parse/transport/5xx uncertainty | `economy_api.gd:45–79`; `economy_ui.gd:559–608` | Unreadable/non-dictionary JSON, non-connection transport failures, 5xx, and insufficient success scalars retain the receipt. Recovery errors all retain it. S1 is the remaining success-validation gap. |
| First-attempt clear semantics | `economy_ui.gd:584–595` | A first-attempt `not_sent`, `not_reached`, or parsed refusal clears except 401/403/429. This relies on the authoritative backend returning errors without committed effects, not on an arbitrary proxy's truthful error. HTTP 3xx is also classified as rejected by the API; no redirects are followed. |
| Competing owners | journal `20–32,34–49,76–81,113–120` | A loopback TCP listener derived from the lowercased/simplified global journal path serializes owners; collisions fail closed. Stage and clear both read under the claim. No peer is accepted and no journal content is served. No sockets were opened by this review. The source comment about Windows SO_REUSEADDR is not independent engine verification. Physical path aliases/junctions are not resolved by this textual canonicalization; fixed production `user://` avoids user-selected path changes, but broader alias/platform claims are unproved. |
| Stale claim release | journal `34–43`; UI `513–522` | A newly acquired claimant whose disk record differs releases the guard, returns no-send and reloads the current state. An already-owned guard is intentionally retained. Clear rechecks the exact pending dictionary before removal and releases only after successful removal. |
| Storage corruption | journal `51–74,122–152`; UI `529–550` | Oversize/malformed/unsupported existing records are retained and block new transactions via a separate error state; they are not treated as a safe empty record. Temporary orphan files before publication cannot have preceded a compliant send. |
| Credential/privacy boundary | API `3–6,23–29,53–57`; journal `122–152`; UI `541–542` | Bearer/password remain in memory/request headers. Production staged fields are a small whitelist; owner/server identify the recovery scope but contain no auth secret. No offline profile balance is included in a payload (`profile.gd:65–88`). Message strings are production constants, not secret containers. This is not encryption of local transaction metadata. |
| Authoritative replay | `backend/app.py:45–48,61–67,127–141,218–245,280–297`; `models.py:50–54` | Global PostgreSQL transaction advisory lock serializes writes. Authentication precedes receipt lookup; operation ID scopes actor + route/listing + key, request hash is canonical validated body, mismatch refuses, and exact stored JSON response replays before live listing/ownership/price checks. Remembered response and economic rows share the transaction. JSONB preserves semantic data, not original HTTP property ordering. |
| Price/integer/fee/authority | `backend/app.py:143,157–166,283–297`; `economy_ui.gd:639–641`; `models.py:17–21,27–36,62–70` | Expected price is strict optional integer 1..10,000,000; extra fields are forbidden. Mismatch rolls back without debit/mint/operation. Omitted and explicit-null price preserve the older hash contract. Fee uses integer floor `price * basis_points // 10000`; UI uses integer division. Owned/reserved item, active seller, sufficient earned credits, exact buyer debit/seller credit/burn and one ownership transfer are server-controlled. The market listing form's 1,000,000 UI cap at UI line 1285 is unchanged; the 10,000,000 runtime fixture was service-seeded, not created through that form. |

The entire backend, API, profile, and bridge were unchanged across the scoped recovery diff. Existing participant-private trade checks remain at `backend/app.py:305–313`; trusted reward scope at 69–77 is unchanged. This supports **no source-diff weakening found in these boundaries**, not a new live security certification.

## Source countercontrols present, versus runtime evidence actually available

- `game/tests/transaction_journal_test.gd:55–107` covers stage-before-stub-send, no token in journal, live competing child, UI recreation, account/server mismatch, rejection/uncertainty retention, same saved payload, successful clear and unwritable storage.
- Lines 108–135 cover damaged records, forbidden credential fields and deliberately truncated temporary/published readback. Lines 136–150 cover stale claimant handoff and guard release using two existing panels.
- These are test **definitions**, not newly executed controls. The child test and panel test are not proof of repeated real PostgreSQL crash recovery. The native publication does not publish execution of those tests at this review's direction.
- The retained native campaign kills the original process after SQL-visible commit and a withheld response, then lets the recovering process complete, then starts a third process. It does **not** kill the recovering process during its replay, during clear, or between clear and refresh. It does not demonstrate competing live native owners against PostgreSQL or a stale panel spanning both process kills.
- Required next controls, under separate authorization: repeat a kill while the second process awaits the original keyed replay; restart again with the same record; and run an old observer that attempts to claim a record already resolved/replaced by another owner. Compare exact operation/ledger/audit/item rows, not just counters or exit status. No such control was run here.

## Native evidence audit (stored records; no outcome judgment)

The independently generated `bytebindings.json`, `independent-record-reanalysis.json`, and `additional-record-checks.json` are the detailed machine-readable audit. The original author's raw records remain byte-for-byte under `raw/`.

### Byte bindings

- Re-read and rehashed **237 Git blobs**, total **1,863,212 bytes**. All 237 path/blob-ID/SHA-256/length tuples match the publication's object list.
- Independently checked the inner publication manifest: 236 entries match; that manifest excludes its own content hash. Its own SHA-256 is checked through the outer object list. There is no count inflation to 237+236 measurements.
- Re-ran read-only `git archive --format=zip <exact revision> game backend`, hashing in memory/stream, without storing the ~8 MB archives in this bounded packet.
  - `701ce2c`: 7,986,991-byte archive SHA-256 `e059f5e213b5f1375c96200da7a2a203d5e45b087037f171bcf756170c1fbe33`; all **299** archived file hashes and the complete path set match.
  - `7b6f379`: 7,996,526-byte archive SHA-256 `2434610f47d0d7503d93cbab7155878fc886f48898c2f9fe85f6a4aaec6c9c01`; all **307** archived file hashes and the complete path set match.
- Canonical blob hashes differ from executed archive hashes for **278/286** text entries respectively. Every difference is resolved by **CRLF-to-LF only**; all entries were compared. The archive hashes themselves reproduce exactly with no normalization. The preliminary naive blob-vs-archive mismatch is retained as a diagnostic, not hidden or called a production failure.
- The common measured harness and restart probe are identical bytes between both complete record sets and equal the exact tooling commit modulo CRLF only. Source archive identity is verified; recorded clean-checkout flags alone were not used as proof.
- Engine binary and imported cache contents are not included in the Git publication. Their recorded digests/manifests cannot be independently re-derived from those objects. No binary/cache-runtime provenance beyond those records is certified.

### Commit/kill/ack ordering and exact rows

- Re-derived the 30 economic-state digests from the stored SQL snapshot bodies (five snapshots in each of six trials), without trusting pass flags.
- Each complete timeline has the ordered hold → separate SQL snapshot → kill requested → killed process acknowledged → held response discarded sequence. The SQL snapshot's own database clock precedes kill request. The SQL connection PID differs from the native client/harness IDs. No killed-client completion marker occurs before termination.
- In the frozen proxy, **all downstream status-line/header/body writes for the first held purchase** lie after the blocking branch (`validate_native_transaction_restart.py:190–212`); the branch returns after discarding it. Upstream response body is fully read before the barrier (177–189). Login/read responses are intentionally not held. The recorded `sent_bytes=0` is instrumentation, not an independent packet capture; no literal flag alone is treated as wire proof.
- New-connection SQL read-only repeatable-read snapshot code is at harness 110–124; kill ordering at 377–400. The captured SQL rows include the exact operation ID, canonical request hash and full response, two exact ledger rows, one exact settlement audit, the single transfer and sold listing, debit/credit/fee arithmetic. Full pre-existing rows and unrelated captured economic tables were checked, not merely row counts.
- Full captured economic state equals the committed state after kill, after recovery, and after the third process. **Sessions do change**: exactly one fresh token row is added for each login, and no new token at the kill snapshot. Each phase's native token hash matches the exact new SQL row for the original owner. Three distinct native PIDs and three distinct session hashes occur per trial.
- No non-auth, non-GET mutation request is recorded from the third process in any trial. This is a no-**economic**-mutation claim, not “the whole database never changes.” Snapshot coverage excludes rate buckets and game tickets; auth/read activity can affect uncaptured operational tables.
- Journal raw bytes, lengths, hashes, parsed records, saved owner/server/path/method/payload, and pre/post-kill identity were checked wherever raw journal artifacts exist. Missing-file metadata is retained as an author's observation corroborated by the native empty-pending record; it is not a present-day filesystem inspection.
- Any replay receipt equality stated by the audit means **semantic JSON equality**. The original and replay response raw JSON strings differ in property ordering where replay is recorded. Request raw body strings were compared separately. No bit-for-bit response claim is made.

### Price and negative-run coverage

- Each complete record set has one trial each at **400, 401, 10,000,000**, with 300 basis points and fee floors **12, 12, 300,000**. These are three different-price cases, not three repeats per price. The 401 case exercises a fractional pre-floor product; neither 400 nor 401 crosses the first zero-to-one fee boundary.
- The native restart records do not exercise prices 1/33/34, zero/negative/over-maximum/fractional/bool/string expected price, or a mismatched consent price during restart. Backend test definitions at `backend/tests/test_economy.py:117–167` cover mismatch, exact/changed-body replay, omitted/null legacy receipts and strict integer rejection; they were not executed by this review. Required native edge controls: 1 and 33 → fee 0, 34 → fee 1, 10,000,000 → fee 300,000, and atomic rejection of invalid/mismatched prices while preserving prior uncertainty.
- Retained original native economy oracle: **36/37, return code 1**, with the unreachable-server assertion failing and the trace reaching API line 66 (unknown outcome). The stored stdout/stderr are retained. It is not upgraded to a pass.
- Separately retained DNS calibration: **37/37, return code 0**. Byte comparison proves its executed probe differs only by replacing one port-9 URL with the reserved `.invalid` DNS URL. It is an externally altered oracle condition, not a rerun of the unchanged original test and not independent proof of a source improvement.
- Earlier retained failures are still failures/blocked attempts: r1 compile/SystemError (zero completed trials); r2 occupied native slot/preflight-only; r3 out-of-memory/tasklist failure; r4 resource window unavailable after 20 minutes; r5–r8 native request never reaching the response barrier (zero completed trials). Do not infer a common root cause for all startup failures from a later successful run.
- Cache/import preparation, startup and pipe diagnostics, PostgreSQL resume logs, preflights, and original failure records are retained in `raw/` and carried into the neutral packet as appropriately source-scrubbed ancillary diagnostics. No old failure is relabeled as a new pass. Preflight-only prose is marked as recorded status, not a newly demonstrated DB/native event.

## Assurance boundary / next judge

No P0/P1 exploit of the unchanged auth, consent-price, fee or server-authority boundary was established by this read-only review. S1–S3 and the unexecuted adversarial controls prevent an unconditional recovery-safety or liveness sign-off. The new neutral packet supports a fresh critic's record-based assessment; it does not itself establish an improvement, independent end-to-end replay, statistical repeatability, power-loss durability, or exact runtime behavior of d2439ac. Keep the mapping private until that critic freezes its verdict.
