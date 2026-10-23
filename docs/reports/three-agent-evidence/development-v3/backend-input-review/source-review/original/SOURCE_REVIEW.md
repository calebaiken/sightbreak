# Backend trade-read source review

**Result:** no new runtime correctness, participant-visibility, authentication, or write-contract regression found in the authorized source slice. This is a scoped, source-only conclusion, not a test-suite pass or a performance verdict. Two assurance weaknesses are identified below: the query-count test does not enforce the 500-ID parameter bound, and the workload's fixed-fixture provenance promise is not enforced for arbitrary `--source` trees.

**Review directory:** `C:\Users\blith\AppData\Local\Temp\opencode\sol-backend-source-critic-20261019T194154Z`

## 1. Pins, scope, and evidence

| Label | Exact commit | `backend/app.py` blob |
| --- | --- | --- |
| Candidate runtime/tests/workload | `4a8e9ea73aa8b286d9f1751b0a6b485479737294` | `16f33c94da490c77a8ab930b88d8fc0662f3fa4c` |
| PR 16 baseline | `d2439acdd5f73df7bae5ada62ee1e3dec2cf30db` | `bb15f054d622fc4f6164248a2f4453d20a3e7fff` |
| V2 baseline | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` | `bb15f054d622fc4f6164248a2f4453d20a3e7fff` |

The candidate's immediate parent is the PR 16 baseline. The user string `PR16d243...` is interpreted as the PR label followed by the 40-character `d243...` commit, not as the invalid 42-character hash `16d243...`. PR 16 and V2 have **identical entire app blobs**. Their model blobs also match the candidate: `8dc03d668a696f889d89b71c07602b02593befaa`.

Reviewed:

- The candidate's `trade_json` and `GET /trades` diff against the pinned baselines.
- The candidate's own new `backend/tests/test_trade_reads.py` and `scripts/benchmark_trade_reads.py` source.
- Relevant immutable app helper/write definitions and model definitions solely to assess the requested contracts.

Excluded: current working-tree/integration source, owner evidence and performance reports, blind/private material, GitHub, other agents' files, unrelated product slices. A changed-file listing exposed the documentation/report filename; its contents were not opened. No agents were spawned.

All source line references below refer to **Git-object line numbers**, not current working-tree files. Unless stated otherwise, the commit is the candidate above. Line-numbered extracts are saved alongside this review.

### Reproduction integrity

- `pr16-to-candidate-app.diff` SHA-256: `c07b93646c716416f8751cf0229fa6d145d683043741a8b207a309f7e578b2e3`.
- `pr16-to-candidate-authorized.diff` SHA-256, including only app/new tests/new workload: `0d3736d44d7261f440df67763dc85dfd61f1bc61c31f8b2b2cfb02295749133f`.
- Candidate app SHA-256: `703c20b298d734395f292d4a8c5e415e55e6f35109e9a51dcb36fbcb62647441`.
- Both baseline app SHA-256 values: `478440d35840f2a60dad08793b73ec1aa983ce5b5cc2414445cf78f79ea19549`.
- New tests blob: `bb6910c333704983cc7df454913d7e929e76a595`; SHA-256: `7106ccbbf657058087ed4b717143cdcea760513d8a513432b3445a2131a69eb1`.
- New workload blob: `262d363eda0036b17719d273931ee08a04036028`; SHA-256: `6e4aac58ad913144e2c41455124afd6756e500c5d795636e15ba52b1aa5a3b19`.

`manifest.json` records full object identities and definition hashes. `git-commands.json` records the successful collection's exact argv, return codes, output byte lengths, and SHA-256 values. `COMMANDS.md` records invocation details, discovery commands, failed startups, and interpreter limitations.

## 2. Findings and assurance gaps

### G1 — Medium assurance gap: query budget does not prove 500-ID batches

**Source:** `backend/tests/test_trade_reads.py:L87-L104`, particularly the statement-only recorder at L91-L92 and upper-bound assertion at L102-L104. Related implementation: `backend/app.py:L316-L323`.

The current implementation correctly uses both a range step of 500 and a slice width of 500. The test, however, stores only statement text and asserts `len(statements) <= budget`. Fewer queries always pass. It never checks parameter-list cardinality or the individual hydration queries' maximum input size.

**Concrete source-level false-pass control:** in an isolated copy/AST only, change both item and player loops' step and slice width from 500 to 5000. This still fetches every referenced ID for every supplied fixture and preserves payload/order. It violates the stated 500-ID bound, but all supplied query-budget predicates accept it:

| Fixture `(trades, items per side)` | Existing budget | 5000-ID-batch statement count |
| --- | ---: | ---: |
| `(0, 0)` | 3 | 3 |
| `(1, 0)` | 4 | 4 |
| `(1, 2)` | 5 | 5 |
| `(40, 1)` | 5 | 5 |
| `(40, 20)` | 8 | 5 |
| `(501, 0)` | 5 | 4 |

These are static cardinality deductions, **not recorded database measurements**. An entirely unbounded single `IN` list has the same weakness for these fixtures.

The existing tests are still useful: `(40, 20)` exercises 1600 item IDs and `(501, 0)` exercises 502 participant IDs in the current implementation; exact payload comparison catches dropped batches/IDs and order corruption. Their budget meaningfully guards against ordinary per-row/per-offer query growth. The narrow claim not established is **bounded parameters per query**, not payload completeness or the usefulness of all query-count assertions.

**Suggested strengthening, not applied:** record bound parameters or instrument the hydration batch helper; assert each item/player batch has at most 500 distinct IDs, and add exact 499/500/501 boundary cases for both ID types. Keep the payload/order checks. An exact statement count alone would not prevent one oversized batch plus unrelated extra queries.

**Reproduction artifact:** `isolated_assurance_controls.py` extracts the pinned test's budget and statement assertions and evaluates the oversized-batch control without importing the app. It is saved but **not executed**, because no usable CPython 3.13 executable was available.

**Disposition:** not a current runtime defect; current source satisfies the bound. This is a regression-test coverage weakness.

### G2 — Low/conditional harness defect: recorded fixture hash need not identify imported fixture

**Source:** `scripts/benchmark_trade_reads.py:L65-L67`, `L79-L85`; fixed-fixture promise at L5-L6.

The report fingerprints `ROOT / 'backend/tests/test_trade_reads.py'`. Python's inserted search path instead puts `source / 'backend'` and `source / 'backend/tests'` **before** `ROOT / 'backend/tests'`. Consequently, a different clean `--source` tree containing its own `test_trade_reads.py` can supply `seed_workload`, `canonical_trades`, and `database_snapshot`, while the report still records the harness-root fixture's hash. A `test_trade_reads.py` under `source/backend` can shadow it as well.

**Concrete pure reproduction:** create two tiny differing `test_trade_reads.py` files in isolated `source/backend/tests` and `harness/backend/tests` directories. `PathFinder.find_spec` with the source's exact path ordering resolves the source-side file. Fingerprinting the harness-side file produces a different digest. No fixture module, application, database, or benchmark needs to execute to demonstrate the mismatch.

**Exact-pair qualification:** PR 16 predates the added fixture, and the reviewed candidate adds this exact fixture. This review does **not** establish an actual fixture mismatch for the pinned PR16/candidate pair, nor does it inspect a measurement output. The defect is the harness's unenforced general promise that `--source` cannot change the fixture while the report fingerprints a supposedly fixed fixture.

**Suggested strengthening, not applied:** explicitly load the fixture from the harness-root path under a unique module name, or verify and record the actual imported module's resolved file/hash and assert it equals the pinned fixture. The same-origin dependencies also need intentional treatment.

**Reproduction artifact:** the second control in `isolated_assurance_controls.py`; saved, **not executed**. It uses only tiny temporary fixture files and module-spec resolution.

## 3. Runtime semantics reviewed: no new findings

### Participant visibility and per-trade names

**Source:** `backend/app.py:L310-L324`, especially L312-L313, L316-L317, and L303-L304.

- Authentication still precedes the same participant predicate: `Trade.a == p.id OR Trade.b == p.id`. No broader trade query, state filter, owner filter, pagination, or auth bypass was added.
- Item IDs come only from those selected trades' stored offer arrays. Participant-name IDs come only from the selected trades' `a`/`b` pairs.
- Although one request-wide names map contains all participants in that request's history, `trade_json` rebuilds each trade's output names from **only `(t.a, t.b)`**. It does not expose the whole hydration map on each trade.
- The new maps are function locals, not global caches. There is no new cross-request or cross-user map sharing.
- Relevant tests use a hidden unrelated trade and a separate outsider session: `backend/tests/test_trade_reads.py:L68-L70`, `L98-L99`, `L144-L153`. Removing the participant filter would change the golden payload, including the zero-trade case.

### Participant, item, name, and list ordering

**Source:** `backend/app.py:L299-L304`, `L313-L324`; baseline `backend/app.py:L299-L313`.

- `a`, `b`, revision, offers, confirmations, and state are returned from the same trade attributes, unchanged.
- `offer_items` still iterates `t.offers.items()` and each original offer ID list. Global ID deduplication affects fetches only. SQL result order and set iteration order cannot substitute for the agreed offer order.
- Name-map construction still iterates `(t.a, t.b)`, preserving the serializer's participant/key construction order. JSON object-key order is not separately enforced by dict-equality assertions, but the source construction is unchanged.
- Neither version promises a top-level trade order: neither query has `ORDER BY`. The test's canonical sorting is therefore appropriately limited to the top-level trade array (`backend/tests/test_trade_reads.py:L74-L76`). It does not sort offer arrays or confirmations.
- The fixture reverses item arrays at L60-L61, providing a useful control against accidentally returning fetched SQL/set order.

### Current metadata, transferred/consumed items, cross-trade references, duplicates

**Source:** `backend/app.py:L97-L99`, `L302`, `L316-L324`; model `Item` at `backend/models.py:L37-L49`.

- The same unchanged `item_json` function supplies definitions, rarity, pattern seed, wear conversion, variant, collection/kind/name, reservation/eligibility flags, and acquired timestamp.
- Items are looked up by ID, not filtered to the current owner or unconsumed/unreserved items. This preserves the baseline's current-record metadata semantics for completed/cancelled trades whose items have since moved, been listed, or been consumed. Adding an owner check here would be a regression; this candidate does not.
- Repeated IDs across historical trades use the same hydrated current record in every original position. A repeated ID inside one offer array also remains repeated in output; only the fetch-ID collection is a set. Write-side rejection of duplicate offer IDs is unchanged (`backend/app.py:L341-L342`).
- References to an existing item now associated with a different trade/current owner remain serializable, just as with baseline `db.get`. This is not a new ownership/privacy rule: the read contract trusts stored trade offer IDs. Unreferenced item rows are not added to the output.
- Metadata changes and repeated historical references are directly covered at `backend/tests/test_trade_reads.py:L107-L141`. Those tests intentionally check current records, not a frozen trade-time item snapshot.

**Coverage limits:** there is no new fixture with a duplicated ID within one offer list, a malformed third offer-owner key, or missing referenced records. The source behavior is straightforward but those cases were not executed here. Historical cross-trade reuse is tested; arbitrary corrupted references are not.

### Missing/deleted IDs and partial maps

**Source:** `backend/app.py:L302-L303`, `L321-L324`; baseline `backend/app.py:L302-L303`; model offers JSON at `backend/models.py:L77`.

- A missing item is not silently dropped. Baseline `db.get(Item, id)` returns `None`, then `item_json(None)` dereferences `definition_id` and fails. Candidate hydration omits a nonexistent row, then `items[id]` fails with `KeyError`. Both are unhandled failures rather than a successful partial response; under normal non-debug FastAPI handling both produce a server error. The exception class changes, not a documented successful payload.
- A missing participant similarly changes an unhandled `None.display_name` failure into `KeyError`. The model's trade participant foreign keys normally prevent dangling player IDs; offer item IDs inside JSON do not have equivalent per-element foreign keys.
- A deleted reference or corrupt historical offer can therefore still make the entire history unreadable. This is an **inherited robustness limitation**, not a newly discovered supported-state regression.
- Supplied optional maps are assumed complete. The serializer deliberately distinguishes `None` from an empty map and does not fall back to per-ID database reads for missing entries. Existing write callers supply neither map; the one new caller fills them from all referenced IDs. There is no silent cross-trade fallback or skipped-ID behavior.

No deletion race or missing-record control was executed. The above is direct expression-level source analysis, not a live error-response result.

### 500-ID batch boundary correctness

**Source:** `backend/app.py:L316-L323`.

Both loops have matching `range(..., 500)` steps and `[start:start+500]` slice widths. For `k` distinct referenced IDs this covers every ID once, with an empty loop at zero, one batch at exactly 500, and two at 501. Items and participants have independent ID sets/maps/loops. Return order is reconstructed from the original trade structures, not from batch result order.

There is no apparent off-by-one, truncation, cross-kind-map contamination, or duplicate-output loss. This conclusion is source-only; G1 explains what the current query-count test fails to enforce about the cap.

### Transactions, Session mutation, authentication, writes, expected price

**Source:** `backend/app.py:L44-L48`, `L61-L67`, `L127-L138`, `L158-L159`, `L279-L297`, `L305-L308`, `L325-L385`.

The collector hashes relevant complete definitions, including decorators where present. `transaction`, `authenticated`, `item_json`, `owned`, `get_trade`, `new_trade`, `offer`, `confirm`, `cancel_trade`, `market_buy`, `replay`, and `MarketBuy` have matching definition hashes in all three pins. The app diff only changes `trade_json` and `GET /trades`.

- GET still opens one request-local `DBSession`, authenticates through that Session, and reads. It adds no rate bucket mutation, token renewal, session expiry update, auth cache, `add/delete/flush/commit`, explicit write, or write advisory lock.
- Authentication still requires a Bearer session, checks its expiry, fetches its player, and rejects inactive/missing players. Missing/expired/revoked/inactive auth cases are present in the new tests at L156-L168. They do not substitute for a concurrency guarantee.
- The modified serializer's `items is None` and `names is None` branches preserve the exact old lookup behavior for write endpoints. Every existing write caller still calls `trade_json(t)` without maps. They continue to serialize the current Session's pending item/trade state, rather than using stale hydrated GET maps.
- Write transactions retain the same PostgreSQL advisory-lock helper. Duplicate-offer rejection, reservation validation/release, revision checks, confirmations, transfers, cancellation, auditing, and idempotency code are unchanged in scope.
- `MarketBuy.expected_price` strict optional validation, changed-price rejection before settlement, and omission of unset expected price from the legacy-compatible replay fingerprint are unchanged. No expected-price or receipt-contract regression is introduced by this slice.

The new read-only test snapshots every registered model table before and after reads (`backend/tests/test_trade_reads.py:L79-L84`, `L144-L153`), and the query-budget test restricts observed statement prefixes to SELECT. Those are useful checks for persistent row mutation and ordinary DML. They are not proof against every possible transient side effect, sequence change, or mutating database function; no such new source behavior is present here.

## 4. Concurrency and memory limits

### Concurrency: no demonstrated new regression; no coherent-snapshot guarantee

**Source:** `backend/app.py:L29-L32`, `L310-L324`; baseline `backend/app.py:L310-L313`.

Both versions read trades, items, and names in multiple statements without taking the economy write advisory lock. The engine does not request repeatable-read isolation. Under ordinary PostgreSQL READ COMMITTED operation, concurrent writes can change item metadata/reservations or display names between statements. A response can combine an earlier trade revision with later item metadata. This limitation predates batching.

The candidate changes observation timing: each batch observes its rows together; repeated item IDs share one hydrated object; player-name column projections may see a newer viewer name than the Player object fetched during auth. Neither version promises an atomic trade/metadata/name snapshot. No supported-state failing interleaving unique to the new source was established.

Maps and Sessions remain request-local, and no new cross-request mutable cache or write lock was introduced. Actual PostgreSQL scheduling, SQLAlchemy identity-map behavior under concurrent mutation/deletion, and request cancellation were not exercised. Absence of a demonstrated new regression is not a concurrency-test pass.

### Memory and unbounded history remain important limits

**Source:** `backend/app.py:L313-L324`; workload sizes at `backend/tests/test_trade_reads.py:L87` and `scripts/benchmark_trade_reads.py:L90`.

The 500-ID bound limits **per-query bind lists**, not response size, total query count, database work, or request memory. The route has no history limit or pagination. It explicitly retains:

1. all selected trade rows;
2. all distinct referenced item IDs and participant IDs;
3. all hydrated Item objects and participant names;
4. all serialized output dictionaries, including every repeated historical offer occurrence.

Writing `T` for trades, `U` for unique item IDs, `P` for participants, and `H` for total offer occurrences, these structures grow with the full history, not the 500-ID chunk size. Output already grew with history in the baseline; the new hydration lists/maps additionally retain whole-history inputs/objects. No total-memory ceiling is introduced. Concurrent requests can multiply these per-request allocations.

The largest item-heavy supplied fixture is 40 trades / 1600 item IDs; the 501-trade fixture has no items. These do not establish safety for very long item-heavy history, and no stress/memory measurement was run. Host shell-startup allocation failures are recorded solely as tooling limitations, not attributed to this backend.

## 5. Test/workload assessment and limits

The golden expected payload is explicitly built from known fixture fields, rather than calling `trade_json` or `item_json` to generate its own oracle. Full HTTP JSON equality checks cover participants, names, revision, confirmations, state, offers, metadata, and item-array ordering. Closed-trade mutation checks and outsider/read-only/auth cases add meaningful semantic coverage. Each route invocation creates its own Session; the workload's two warm-ups do not create an ORM Session reused by later requests (`scripts/benchmark_trade_reads.py:L98-L118` versus `backend/app.py:L311`).

The workload records query counts and a `budget` field but does **not** assert `statements <= budget` (`scripts/benchmark_trade_reads.py:L96-L118`). That is not by itself a defect: the same workload can measure an unoptimized baseline. It must not be mistaken for a candidate budget gate. The pytest assertion is the actual gate, subject to G1.

The workload is source-reviewed only. Its unique test-database creation, truncation/migration logic, cleanup, package/runtime dependencies, and source identity checks were not executed or certified here. G2 narrows its fixed-fixture provenance claim. No owner's output, timing report, measured response hash, private packet, or blind critic material was consulted.

### Execution status

- Source extraction and hashing: **executed** through read-only Git commands; captured externally.
- CPython 3.13 synthetic controls: **not executed**. The registered 3.13 executable was absent; no substitute version, download, or installation was used.
- PostgreSQL / pytest / native tests / benchmark / exports / network / service changes: **not run**.
- Repository changes, commits, posts, agent spawning: **none**.

`isolated_assurance_controls.py` is a reproducible, explicitly unexecuted control artifact. `collect_review_sources.ps1` is the collector actually used; the Python collector present in this directory never ran. No control output or failure log is fabricated.

## 6. Bottom line

**No new runtime bug found in the requested backend trade-read slice against either pinned baseline.** Current participant scoping, offer ordering, current-item/name metadata semantics, write fallback behavior, authentication, transactions, and expected-price contracts are preserved on source inspection. The implementation itself correctly chunks both ID types at 500.

The review does identify a concrete batch-bound assertion gap (G1), a conditional fixed-fixture provenance defect in the new workload (G2), and explicit inherited/unverified limits around dangling historical references, coherent concurrent snapshots, and unbounded history/memory. These qualifications must remain attached to the no-runtime-findings conclusion. This review makes **no independent performance verdict**.
