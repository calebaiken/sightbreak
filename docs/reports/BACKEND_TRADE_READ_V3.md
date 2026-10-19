# Backend trade-read efficiency: frozen candidate and raw PostgreSQL evidence

**Focused development candidate, draft [PR19](https://github.com/calebaiken/sightbreak/pull/19).**
Independent critic and integration acceptance are pending. Query-count and
correctness gates pass on the source below; these are backend test cases, not
the full V3 native matrix.

## Identity and scope

| Input | Exact identity |
| --- | --- |
| Frozen V2 comparison | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` |
| PR16 branch point | `d2439acdd5f73df7bae5ada62ee1e3dec2cf30db` |
| Frozen implementation, tests and benchmark | **`4a8e9ea73aa8b286d9f1751b0a6b485479737294`** |
| Candidate backend Git tree | `4ef756639c2e90037bce79a30e2867aebcc798a7` |
| V2/PR16/PR15 backend Git tree | `67027b4fa17674ef067c84401af76eb1524419ac` |
| Benchmark file SHA256 | `6e4aac58ad913144e2c41455124afd6756e500c5d795636e15ba52b1aa5a3b19` |
| New fixture/test file SHA256 | `7106ccbbf657058087ed4b717143cdcea760513d8a513432b3445a2131a69eb1` |

Own worktree/branch: `sightbreak-backend-trade-read-v3` /
`astra/backend-trade-read-v3`. The source is based directly on PR16. Scope was
[announced on PR17 before editing](https://github.com/calebaiken/sightbreak/pull/17#issuecomment-6275004330).
This subsequent report/evidence commit does not alter the frozen implementation.

The runtime diff is **15 insertions / 4 deletions** in `backend/app.py`:

- `trade_json` at line 299 accepts request-local item/name maps. Each trade still
  returns only its own two participant names. Write callers use the existing
  direct-lookup path.
- `trades` at lines 310–324 first applies the existing authenticated-participant
  predicate, then loads its offered items and display names in 500-ID batches.
  Serialization follows the stored offer arrays, preserving their order and
  repeated historical references. It uses current item records, including
  transferred and consumed historical items.

The [source-preservation receipt](backend-trade-read-v3/source-preservation.json)
compares AST declarations and Git objects. Only `trade_json` and `trades` differ
inside `app.py`. Models, migrations, configuration, dependency lock, the original
economy tests, game and server trees match frozen V2. There is no shared
`validate_matrix.py` / `run_network_campaign.py` or B-21 client-journal change.

## Measured result

Same host, PostgreSQL **17.11**, Python **3.12.14**, locked dependencies, identical
fixture and benchmark hashes. Each side uses a newly created isolated database,
two warm-up requests and **ten measured requests per workload**. Each request
gets a new ORM session. Measurements were serial; host load was not controlled.

| Trades | Items per side | SQL statements: V2 → candidate | Median ms: V2 → candidate | P95 ms: V2 → candidate |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 3 → 3 | 12.74 → 10.61 | 14.30 → 12.48 |
| 1 | 0 | 4 → 4 | 14.51 → 13.10 | 17.13 → 14.09 |
| 1 | 2 | 8 → 5 | 23.61 → 17.19 | 44.47 → 18.98 |
| 10 | 1 | 33 → 5 | 66.73 → 21.05 | 98.30 → 22.62 |
| 40 | 1 | 123 → 5 | 220.83 → 33.63 | 295.20 → 64.62 |
| 40 | 20 | **1,643 → 8** | 3,309.75 → 249.12 | 4,141.71 → 369.75 |
| 501 | 0 | **504 → 5** | 1,176.57 → 101.95 | 3,303.80 → 177.52 |

The 1,600-item workload reduces application SQL statements **99.51%**. The
deterministic acceptance is query count plus complete payload/state equivalence.
Timing is supporting in-process TestClient/loopback evidence, not production
throughput, concurrent load, network HTTP latency or a hardware-independent
speedup guarantee. Ten-sample P95 here is the maximum observed sample.

Every **expected-fixture** canonical response hash matches between revisions in
these initial records. Each actual response was asserted equal to its expected
fixture; actual bodies and their hashes were not retained in this first round.
Canonicalization sorts
only top-level trades and JSON object keys; offer and confirmation array order
is preserved. Every workload also compares all authoritative table rows before
and after its requests. The first-round records retained comparison booleans,
not the snapshots or their hashes. All comparisons pass; all measured application SQL is
SELECT. The budget is `3 + ceil(unique item IDs / 500) + ceil(unique participant
IDs / 500)`, covering both item- and name-batch boundaries.

Raw [baseline measurements](backend-trade-read-v3/baseline-measurement/measurement.json),
[candidate measurements](backend-trade-read-v3/candidate-measurement/measurement.json)
and [matched comparison](backend-trade-read-v3/comparison.json) retain each
sample, SQL shapes, response hashes, source/file identities, package versions
and read-only outcomes. Source identity checks pass at the beginning and end.

## Correctness and sensitive-contract gates

| Workload | Actual result | Raw record |
| --- | --- | --- |
| Frozen701 original backend suite, Python3.12 | **61 passed**, 1 existing Starlette/httpx deprecation warning, 41.95 s | [log](backend-trade-read-v3/baseline-61-python312/pytest.log), [command/source](backend-trade-read-v3/baseline-61-python312/run.json) |
| Candidate complete backend suite | **74 passed**, same warning, 54.53 s | [log](backend-trade-read-v3/candidate-74/pytest.log), [command/source](backend-trade-read-v3/candidate-74/run.json) |
| New tests against unchanged frozen701 | **4 expected query-budget failures, 9 passes**; payload assertions preceding each failure pass | [negative-control log](backend-trade-read-v3/baseline-negative-control/pytest.log), [command/source](backend-trade-read-v3/baseline-negative-control/run.json) |

The four old-code failures are exactly `(1,2): 8 > 5`, `(40,1): 123 > 5`,
`(40,20): 1643 > 8`, `(501,0): 504 > 5`. These establish that the efficiency gate
detects the original per-item/per-partner round trips. They are not failures of
the original 61 economy cases.

The 13 new cases check complete payloads, participant membership in both `a` and
`b`, unrelated trade/name privacy, open/completed/cancelled histories, offer
ordering/reuse, changed current names/reservations/ownership, consumed keys,
all-table read-only behavior, and missing/expired/revoked/inactive authentication.

The unchanged original cases retain wallet conservation and concurrent buyers,
double spend, atomic case/trade transfers, reservations/loadouts, ticket
authority, match replay, history integrity/rollback and PR15 contracts: strict
bounded expected price, both mismatch directions, authoritative debit/fee,
concurrent exact receipts, changed-payload conflict, replay before later listing
state/price checks, and pre-guard omission/null receipt fingerprints.

**PR15 is already integrated.** `228c382` is an ancestor of PR16 and this
candidate. Its complete backend tree equals frozen701 and PR16. It remains a
separate reviewable draft PR; integration does not imply a main merge or rollout.
The older B-27 research request and receipt-only route summary in `docs/backend.md`
are stale relative to the implementation and `MARKET_EXPECTED_PRICE.md`.

## Environment, failed attempts and reproduction

[Portable Windows setup and exact workload instructions](../backend/TRADE_READ_EFFICIENCY.md)
use uv, the repository lock and an EDB PostgreSQL 17 binary archive under approved
`Temp/opencode`. Neither Docker nor a preinstalled psql nor a registered Windows
service is needed. The isolated instance listens only on **127.0.0.1:55439**.
[Environment receipt](backend-trade-read-v3/environment/environment.json) records
all package versions and PostgreSQL settings. The native Godot runtime is not
needed for this backend-only workload.

- System Python **3.14.6** installed the frozen dependencies but the untouched
  baseline crashed with `0xC0000005` in `anyio → asyncio.get_running_loop()`:
  [original failed run](backend-trade-read-v3/baseline-61/pytest.log),
  [exit/source receipt](backend-trade-read-v3/baseline-61/run.json).
  A [minimal program](backend-trade-read-v3/python314-minimal/minimal_testclient.py)
  with no Sightbreak/PostgreSQL imports reproduces the same
  [fatal trace](backend-trade-read-v3/python314-minimal/process.log) and
  [exit code](backend-trade-read-v3/python314-minimal/run.json). Python3.12 is the
  matched validation workaround, consistent with retained V2 evidence. The
  underlying Python3.14 host/runtime failure is not diagnosed or fixed here.
- The first portable-server startup wrapper used captured pipes and timed out
  after the server reported ready. Its log later records shutdown after a child
  startup failure. File-redirected `pg_ctl` startup then completed successfully.
  [Setup commands/hash](backend-trade-read-v3/environment/postgres-setup.json),
  [successful startup](backend-trade-read-v3/environment/postgres-start.json),
  [server log](backend-trade-read-v3/environment/postgres.log) retain both attempts.
- Host/tool restarts occurred during the task. The candidate test process
  survived and completed 74/74; it was not restarted or double-counted. Early
  transient PowerShell/CoreCLR allocation and Git-process failures are session
  infrastructure failures, not backend passes. Local disk cleanup was not used.
- All disposable databases created by the retained test/benchmark runs were
  dropped. The loopback cluster remains available for the coordinating session;
  its exact data directory and stop command are in the setup guide.

The original retained V2 PostgreSQL result remains **61 passed / 4.89 s** in
`three-agent-evidence/stabilization-v2/matrix-r2/postgresql.log`; the independent
review baseline remains **61 passed / 5.59 s** in its network-review log. Those
historical Linux timings are not compared as this Windows candidate's baseline.

## Latest backlog and largest remaining gap

At the coordinated PR17 `b5476a0` checkpoint, the active V3 integration work is
independent bot/art checks, source-provenance and Windows harness corrections,
then a frozen full matrix/network campaign and native exports. Main's B-21
durable receipt/journal/process-kill work is separately owned in PR18. This slice
is separately judgeable as PR19. The historical research backlog is not a live
completion ledger: B-27 is integrated; B-21 and B-28's remaining pagination and
trade-expiry work still require their own acceptance. SQL market filtering and
recent account history already exist in the baseline.

**Largest gap for this optimization:** `/trades` still returns an unpaginated
history, so total output and retained objects remain unbounded. The 500-ID
batches bound each SQL parameter list, not response size or total memory.
Large-database query plans, concurrent load and peak memory are not measured.
Global economy write serialization is still the documented throughput limit.

The next gate is the scheduled independent critic of this exact source and raw
evidence, followed by Sol's affected integration validation. Physical devices,
production deployment and full V3 acceptance are outside these measurements.
