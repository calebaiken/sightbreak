# Post-freeze mapped retention and trade-read assurance audit

## Decision

**Recommend accepting the unchanged `4a8e9ea73aa8b286d9f1751b0a6b485479737294` trade-read runtime slice for integration, with the new bounded test/fixture-provenance assurance and the qualifications below.** No new runtime change or concrete runtime bug was found in this bounded audit. This is **not** a new full-backend test run, independent performance execution, original-capture attestation, or production approval.

The new retained evidence substantially addresses the two original assurance findings:

1. Actual driver-bound parameter counts reject the 500→5000 mutant even though the old query ceilings and payload assertions still pass.
2. The current harness records/checks the **actually imported** fixture's `__file__`, resolved path and hash. Retained real import probes accept matching bytes, reject shadowing bytes, and report zero intercepted DB-connect calls.

There remain concrete blockers to stronger claims: original r1/r2 app-byte and fixture-import capture was not retained; the new source-byte reconstruction/import receipts are post hoc; monetary/history tables are empty with zero balances; and no full-backend, concurrent, large-history/memory, production, or general-latency gate is established here.

## 1. Identity release was inspected only after freeze verification

`verify_freeze_before_key.py` completed **28 checks, zero failures**, before the second mapping was opened. It checked archived/external exact-byte agreement, every external frozen-artifact hash/length, the report, freeze and ledger anchors, and the explicit blind-at-freeze statement.

| Second verdict anchor | Verified SHA-256 |
| --- | --- |
| `NEUTRAL_RETENTION_VERDICT.md` | `1248f66b7b80e2acbf69595ef084b164957547497f7c40c2e56c4489847fcf3e` |
| `FROZEN.json` | `185d7b4cd1dacde52d8d9cc48bc35b43fde9b1453ef98a362d798e9bb9ab0f9e` |
| External verdict `SHA256SUMS.txt` | `f34dec97780638ddba68a38dbf50d967000b8181eb00ad410e3060084612bc20` |
| Released second `mapping.json` | `28f0de31229e531e7164ce3905ae88cedcbd07ce89e62f046983000ebdecf93a` |

The original freeze time is `2026-10-23T00:26:09.129364+00:00`. The report/freeze/key copies at `866e2e1f38461fa245557c9015b6c1a1a97ad745:docs/reports/backend-trade-read-v3/identity-release-r2/` match. Local hash/time records are not trusted timestamp or historical execution attestation.

The released key, original measurements, Git backend trees, common harness/fixture fingerprints, and driver command receipts agree on these identities:

| Neutral label | Reported executed source checkout | Harness | Shipping runtime reference |
| --- | --- | --- | --- |
| M | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` | `8070436f53dd98e9529e8c21ea7b0f7e3ecb6daf` | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` |
| V | `8070436f53dd98e9529e8c21ea7b0f7e3ecb6daf` | `8070436f53dd98e9529e8c21ea7b0f7e3ecb6daf` | `4a8e9ea73aa8b286d9f1751b0a6b485479737294` |

**V's executed checkout is not falsely relabelled as 4a8.** The shipping backend Git diff is empty, and the app Git bytes match across 4a8, 807 and the new assurance freeze. The separately checked backend tree is `4ef756639c2e90037bce79a30e2867aebcc798a7` at 4a8/807. Clean labels alone are not treated as source-byte proof.

No Astra-side critic report/claim was read or used. A changed-path listing included `critic-r2-parent` filenames; those payloads were not opened.

## 2. Raw → neutral measurement, actual body, and state-array binding

`audit_retention_bindings.py` independently completed **2,312 checks, zero failures**. The audit read immutable original Git blobs at 866, not the original live source worktree. Original measurements bind to the key:

- M/baseline SHA-256: `ac104e8eb34640253cdb0e964a261311dbc9924351cf3b75d17c8abf88e40857`.
- V/candidate SHA-256: `81a934d30ba6feaa0f99d932c835cbf9676183d14b54c67fa74d42f0f5cc8a8c`.
- Original raw manifest: `b7aa36cb9a1186a7eeaec946791f9c5de582f2ee8d822838851a4db05226c52b`.
- Frozen neutral manifest: `dd07a3bfd69e09e27c43257be3a719d001c5d8446a9338746460829887c86d64`.

All raw/key file hashes, complete neutral inventory/key hashes, full withheld headers, and every neutral measurement row bind to the original. Row comparison uses exact decimal parsing; the final seal also compares JSON row tokens, ignoring only insignificant whitespace. Artifact paths were checked for traversal, Git object IDs were independently recomputed, and nonempty expected object IDs/contents and command exits were required. Empty stdout was not accepted as a generic proof of success.

### Independently recomputed retained quantities

| Quantity | Verified |
| --- | ---: |
| Workload records | 14 |
| Received response records | 168 |
| Timed / warm-up response records | 140 / 28 |
| Full before/after table arrays | 336 |
| Aggregate states reconstructed and hashed | 28 |
| Snapshot row instances | 11,728 |
| Empty table-array files | 236 |

For every response, the audit hashes received bytes, parses the received JSON with duplicate-key rejection, checks no top-level field was dropped, sorts only the top-level trade array, reserializes the exact documented canonical JSON, and compares the retained actual canonical file/digest and expected body. Nested offer/confirmation arrays are not sorted away. All 168 status/body/hash records agree. Canonical received bodies match across all seven M/V pairs.

For every table array, the audit checks raw/neutral byte equality, digest, full-row representation, row count, canonical JSON and table-row ordering. It then rebuilds and hashes each complete 12-table state object. All 14 **within-run before/after** intervals agree. Cross-variant aggregate state equality is **not assumed**: sessions and captured timestamps legitimately differ.

This closes the missing retained body/state-array evidence for these r2 intervals, not for r1 retrospectively. It proves retained-file consistency and captured net-row equality—not transient no-write behavior or trustworthy external capture. Eight tables (`audit`, `game_tickets`, `ledger`, `listings`, `loadouts`, `operations`, `rate_buckets`, `rewards`) are empty and all player credits are zero. Wallet conservation, settlement, receipts, expected-price/idempotency races and other write contracts were not exercised by those snapshots.

## 3. Exact app-byte derivation: distinguish the three evidence layers

### A. First-round result remains unchanged

At committed archive `7b6a71a`, the first source-binding audit still has **165 passes / 1 failure**. Its raw candidate app hash is:

`703c20b298d734395f292d4a8c5e415e55e6f35109e9a51dcb36fbcb62647441`

The recorded measured working-app hash is:

`9f94a55f1b19858eec3ac54036601b5c26a330749454a6cb89650d51e298f020`

None of that audit's named newline constructions matched. That valid failure and then-unknown cause are **not rewritten or retconned**. The original frozen verdicts, published receipts and source review are not modified.

### B. R2 alone does not retain or resolve the original working-app byte gap

The r2 key and both initial/final V source headers repeat `9f94…`, while its app Git blob is still `16f33c94da490c77a8ab930b88d8fc0662f3fa4c` / raw `703c…`. R2 retains no measured `app.py` byte snapshot or exact checkout/materialization derivation. It also does not retain the original imported fixture `__file__` identity. Matching commit/tree/clean labels, equal initial/final hashes and the runtime-preservation receipt cannot supply those absent bytes or import observations.

For M, explicit LF→CRLF expansion binds the recorded `78816607…` fingerprint to the baseline Git app; it is not raw-byte equality or capture attestation.

### C. NEW R3 post-hoc reverse-mutant evidence supplies a fingerprint preimage

The completed attempt-2 retained mutant at 172 has SHA-256:

`d3114f58ff9c0a4546765cca5be2b6e96092ddf90af49194424896c42cd182b2`

The independent audit parses its `trades` function, verifies exactly four 5000 constants, reverses **only those four byte edits** to 500, and hashes the complete resulting file. It obtains **exactly `9f94…`**. That independently reconstructed file has **510 CRLF and 21 bare-LF line endings**. Applying only CRLF→LF yields the shipping Git bytes exactly (`703c…`). The retained unified patch also regenerates exactly from those complete before/after bytes. Derived files and hashes are saved under `derived/`.

This is stronger than a clean label: a retained reversible full-file mutant provides a concrete preimage of the reported working-file hash and proves its normalized content matches the shipping app. It is **new, separate post-hoc R3 evidence**, not proof that r2 retained that source file, not a trusted observation of original import/execution, not a guessed old newline transform, and not a reason to convert the original failed check to pass. Why/when the original working file acquired those bytes is not established here.

Attempt 1 is different: reversing its mutant yields the all-LF `703c…` blob, not `9f94…`; its mutant fixture hash is a CRLF expansion, not the exact completed attempt's LF hash. Both negative checks are preserved in `ASSURANCE_AUDIT.json`. Explicit byte derivation explains this older materialization mismatch in the separate `FOLLOWUP_AUDIT.json`; it is not silently erased or counted as additional completed coverage.

## 4. New direct 500-ID guard: actual driver/log/JUnit evidence

Source/workload freeze: `8dc8e3715dcaeb99fe6e3544243ee591d68c337b`.
Completed control runner: `3e7ce7409322766d07afe504d97f47c5b3614875`.
Raw assurance publication: `172c900795c04f9b8706c4e80d72f55927f40da1`.
Raw manifest SHA-256: `38a72cbab4948e9144040626c3793e6310e74d0d73758ab8c83b6e18867c4f8c`.

All assurance manifest payloads and frozen source snapshots verify. These are the pertinent immutable source references:

- **8dc `backend/tests/test_trade_reads.py:88–112`**: `before_cursor_execute` records `len(parameters)` at the DBAPI boundary; the old query-count check remains at line 108; direct parameter cap is line 111. Query count/budget/parameter counts are retained as JUnit properties. Response status and full expected payload equality occur first, at lines 100–101.
- **3e `scripts/check_trade_read_assurance.py:40–67,118–135`**: exact current working-byte materialization and four-constant mutation, full mutant retention and mutation hashes.
- **3e runner `:143–185`**: only two explicitly named pytest cases; separate unique test DBs; subprocess exit recording; JUnit parsing and expected direct-assertion failure checks.
- **3e runner `:159–168,225–234`**: DROP in `finally`, receipt flags after successful DROP execution, and source before/after assertions. These are retained cleanup receipts/code, not this audit's live DB inspection.

Completed attempt 2 shows:

| Case | Original count / old ceiling | 5000-mutant count / old ceiling | Original actual parameter counts | Mutant actual parameter counts |
| --- | --- | --- | --- | --- |
| `[40-20]` | 8 / 8 | 5 / 8 | `[1,1,2,500,500,500,100,41]` | `[1,1,2,1600,41]` |
| `[501-0]` | 5 / 5 | 4 / 5 | `[1,1,2,500,2]` | `[1,1,2,502]` |

Candidate subprocess exit is **0**, JUnit has **2 passes / 0 errors / 0 skips**. Mutant exit is the expected **1**, JUnit has **2 failures / 0 errors / 0 skips**, and both failure stacks identify **only the new direct bound at line 111**, with the actual oversized count arrays. Old query ceilings still pass, and reaching line 111 means the earlier status/payload and count assertions passed. The text logs, JUnit properties, source, run hashes and driver agree; this is not merely a hand-computed predicted mutant outcome.

This addresses G1 for the relevant item-heavy and participant-heavy controls. It is two positive/two negative cases—not a full suite, exact 499/500/501 sweep, every possible parameter encoding/executemany shape, concurrency run, or new seven-workload benchmark.

The failed attempt 1 is retained: after its targeted cases it stopped on an actual historical fixture import mismatch. Its historical LF fixture `7106…` was materialized as CRLF `b8019a17…`; the audit independently reproduces that hash. The completed runner's unfiltered historical blob materialization fixes that replay problem. No earlier failure or duplicate coverage is hidden. Four distinct `_test` DB cleanup receipts are retained across both attempts; no DB was connected to here to re-certify them.

## 5. Actual imported fixture identity and bounded zero-connect controls

- **8dc `scripts/benchmark_trade_reads.py:35–42`** hashes `Path(module.__file__).resolve()` and rejects a mismatch while recording module name, original `__file__`, resolved path, actual and expected hashes.
- **8dc benchmark `:161–169,225–227`** uses that check on the actually imported `test_trade_reads` module in the real measurement path and rechecks it at completion.
- **3e runner `:70–94,187–224`** installs a failing `psycopg.connect` hook before the real fixture import, runs the actual benchmark identity helper, and retains actual imports/stdout/stderr/exit receipts. It does not substitute `PathFinder` speculation for an import.

The current positive import has matching `__file__`/resolved path and exact hash `5eb5d4a4…`, exit 0, accepted. The shadowing negative imports from the isolated source-side fixture path; its exact appended-byte hash is independently reproducible as `a2d93bde…`, differs from the expected hash, exits 1, and emits the actual `Imported fixture byte mismatch` traceback. Both report **zero intercepted DB-connect calls**. All six completed probe stdout records bind to their run receipts.

Important scope distinction: the zero-connect property covers these dedicated import probes. The normal benchmark creates its private DB before checking fixture identity (8dc lines 155–167). Do **not** claim a full benchmark rejects mismatches without any DB connection. The mismatch is still rejected before measurement/fixture population and cleanup remains in its `finally` path.

The four round1/round2 historical pinned import replays all match the recorded old fixture `7106…` and expected source/fallback resolution, but are explicitly `posthoc_import_replay_not_original_capture`. The old 4a8/807 helper sources and reported hash agree; neither old measurement captured actual fixture `__file__`. These receipts improve reconstruction confidence, not original-capture provenance. G2's check is fixed prospectively; history is qualified, not retrofitted.

## 6. What ran, what was inspected, and remaining gates

### Executed by this audit

Only serial, approved **CPython 3.13.15** standard-library file/JSON/XML/hash/AST arithmetic and read-only Git object/metadata commands. Programs, source hashes, command argv/exits, raw Git stdout/stderr, own execution logs, receipts and a final checksum ledger are in this external directory. No target module or retained runner/verifier/control was imported or executed.

The actual retained backend/PG/pytest executions were **earlier Python 3.12.14 runs**, inspected here through their sources and byte-bound logs/JUnit/receipts. Their exit 1 mutant/negative controls are expected results, not successful target exits. This audit did not reproduce them live.

### Not executed or changed

No DB, pytest, application/native test, service, network, GitHub, index, source, or primary-repository publication changes. Original Sol synthetic controls remain **UNEXECUTED**. Neither frozen verdict nor the committed round1 archive is modified or superseded. The final recommendation is narrower than full backend/performance execution.

### Concrete blockers to broader acceptance

1. **Original execution attestation remains absent.** R2 did not retain app source bytes or imported fixture identity; the new exact fingerprint preimage and historical imports are post hoc. Do not sell this as an original checkout/import capture.
2. **No monetary/write safety gate.** Zero balances and eight empty tables cannot certify settlement, price/retry/receipt or authority races.
3. **New assurance execution is targeted only.** No current full-backend suite, new seven-workload measurement, adversarial read/auth deletion/concurrency suite, or runtime execution by this critic is claimed.
4. **Scaling/production gates remain open.** No memory ceiling, unbounded-history, concurrent-load, deployment/device/human or general-latency acceptance is established.

Within that boundary, the unchanged runtime, independently verified retained r2 body/state intervals, completed real bound controls and prospective actual-import guard justify the qualified integration recommendation. The first-round 165/1 record, earlier failed replay, and all limits remain attached.
