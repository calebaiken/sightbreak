# PR19: actual-response and full-row retention follow-up

The seven matched workloads now retain **received response bodies and hashes**,
plus **full before/after authoritative table rows and hashes**. Offline checks
recompute actual-response equivalence and no observed net row mutation for these
captured workloads. This closes the first round's artifact-retention gap for
these measurements; broader source/monetary-contract acceptance remains a
separate review gate. PR19 stays draft.

## Frozen inputs and scope

| Input | Exact identity |
| --- | --- |
| Enhanced harness freeze, committed before either run | `8070436f53dd98e9529e8c21ea7b0f7e3ecb6daf` |
| `scripts/benchmark_trade_reads.py` SHA256 | `416cc212d3200b9351036b7ec205a5bb488748f19c09d7ea0ef1edc24d683dbd` |
| `scripts/verify_trade_read_artifacts.py` SHA256 | `06b5f522c9bdae065ddc44482a666566772bcece9efa29c43e6ceac9792ef62b` |
| Unchanged fixture SHA256 | `7106ccbbf657058087ed4b717143cdcea760513d8a513432b3445a2131a69eb1` |
| V2 runtime/reference | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` |
| Candidate runtime/reference | `4a8e9ea73aa8b286d9f1751b0a6b485479737294` |
| Candidate complete backend Git tree | `4ef756639c2e90037bce79a30e2867aebcc798a7` |

The candidate checkout's HEAD was the distinct harness commit `8070436`, while
its complete backend tree and every recorded backend file hash matched the
frozen runtime `4a8e9ea`. Both runs record source identity before/after; both
match. The fixture, migrations, dependency lock and shipping backend bytes were
preserved. [Runtime receipt](backend-trade-read-v3/retention-r2/runtime-preservation.json)
and [artifact audit](backend-trade-read-v3/retention-r2/artifact-audit.json) retain
these checks, including unchanged first-round raw evidence and neutral packet.

Only measurement retention/verification and documentation changed. The earlier
61/74 runtime test results were not rerun. The three new negative controls below
exercise offline artifact validation, not the application or database.

## Execution and retained evidence

Both sources completed all **seven** original workloads, with **two warm-ups and
ten timed responses** each, serially using Python **3.12.14**, PostgreSQL
**17.11** and identical package versions. [Exact commands, exits and durations](backend-trade-read-v3/retention-r2/runs.json)
record successful processes taking approximately 52.17 s and 22.97 s. There is
no workload coverage gap.

Each source created/dropped only a new uniquely named `*_test` database on the
shared **127.0.0.1:55439** service. The main session's separate database and the
server lifecycle were outside this work. The service was left running.

- **168 received responses**: 28 warm-ups and 140 timed responses. Every response
  has its status, raw-body SHA256, canonical-actual-body SHA256 and artifact paths.
  Identical bodies within a workload share a content-addressed file. All distinct
  received bodies are retained; expected fixture files are stored separately.
- **336 full-table snapshots**: 12 tables × 2 phases × 7 workloads × 2 sources.
  Each file contains all canonical rows, including `[]` for empty tables, with
  per-table SHA256 and row count. The aggregate state hash is reconstructable
  from the table-to-full-rows object. These are **full-row artifacts**, not
  hash-only claims. No separate aggregate-body file is needed or claimed.
- All original per-request timing/query counts, final-request unique SQL shapes,
  budgets and read-only booleans remain available in the enhanced records.
- Fictional fixture accounts only: unusable password markers and SQL hashes of
  fictional session tokens are retained. No request authorization headers or
  raw bearer credentials appear in the retained JSON/log evidence.

Raw records: [V2](backend-trade-read-v3/retention-r2/baseline/measurement.json),
[candidate](backend-trade-read-v3/retention-r2/candidate/measurement.json),
[comparison](backend-trade-read-v3/retention-r2/comparison.json),
[V2 console](backend-trade-read-v3/retention-r2/baseline-console.log),
[candidate console](backend-trade-read-v3/retention-r2/candidate-console.log).
The existing Starlette/httpx deprecation warning is retained in both logs.

## Results, including regressions

| Visible trades | Items per side | Statements: V2 → candidate | Median ms: V2 → candidate | Nearest-rank P95 ms: V2 → candidate |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 3 → 3 | **7.86 → 10.37** | **8.79 → 13.85** |
| 1 | 0 | 4 → 4 | **9.35 → 14.92** | **10.82 → 26.98** |
| 1 | 2 | 8 → 5 | 16.04 → 11.50 | 19.18 → 13.08 |
| 10 | 1 | 33 → 5 | 54.09 → 17.04 | 66.63 → 23.77 |
| 40 | 1 | 123 → 5 | 202.75 → 25.56 | 292.42 → 54.06 |
| 40 | 20 | **1,643 → 8** | 1,657.12 → 126.97 | 1,827.21 → 209.85 |
| 501 | 0 | **504 → 5** | 942.17 → 65.03 | 2,704.71 → 157.82 |

Query counts reproduce the first round, with no measured count regression. The
1,600-item boundary uses four item batches plus one participant batch; the
502-participant boundary uses two participant batches. The unchanged fixed
authentication/trade reads account for the other three statements.

**Small-read latency regressed in this round.** Serial, non-interleaved runs on
a shared host cannot establish why, or prove a universal latency win. Timing
brackets the TestClient call only; response artifact writes happen afterward but
can still affect scheduling/caches between calls. P95 is just the maximum of
ten samples. No production throughput, concurrent-load, network HTTP or stable
tail-latency claim follows from this table.

### Actual responses and row-state checks

Every retained actual response body rehashes successfully, has exactly the
`trades` top-level envelope, canonicalizes to its separately retained expected
fixture, and matches the corresponding actual canonical responses from the
other source. Canonicalization sorts top-level trades by ID and JSON object keys
while preserving all nested array order. The packet verifier additionally checks
the complete top-level envelope; it does not silently discard extra fields.

Every before/after full-row table array, per-table hash and aggregate hash
matches **within each workload/source**. Across sources, the only differing
state column is `sessions.expires_at`, seeded from each run's clock. Original
timestamps are retained; cross-source aggregate state hashes are not claimed
equal. There is no normalization or redaction of actual rows to force a match.

The first-round `response_sha256` fields remain **expected-fixture hashes**.
That evidence is unchanged. Actual-body verification is substantiated by this
new round's distinct `response.raw`, `response.canonical` and
`actual_response_sha256s` artifacts, not by relabeling the old digests.

### Offline verification and falsifiers

[V2 verification](backend-trade-read-v3/retention-r2/baseline-verification.json)
and [candidate verification](backend-trade-read-v3/retention-r2/candidate-verification.json)
each verify 84 received responses and 168 full-table snapshots. The neutral
packet's verifier also checks complete file-manifest coverage, budget/summary
arithmetic, full response envelopes, cross-source actual bodies and the exact
cross-source state-column difference.

Three [negative artifact controls](backend-trade-read-v3/retention-r2/artifact-negative-controls.json)
were rejected with `AssertionError` and nonzero exit:

1. Changed received-body bytes with the old checksum.
2. Changed actual response semantics and updated raw/canonical hashes, retaining
   the original expected fixture.
3. Changed an after-snapshot player balance and updated its per-table/aggregate
   hashes, retaining the original before snapshot.

The [control script](backend-trade-read-v3/retention-r2/verify_controls.py) and
individual failure logs are retained. Each control worked only on a newly
copied scratch artifact directory; successful evidence was not edited.

## New blind packet and external key

Give the existing critic **only** the following new directory, after the
first-round verdict is saved:

```text
C:\Users\blith\AppData\Local\Temp\opencode\blind-trade-retention-r2-527acf0980f8\packet
```

Read `README.md`, `METHOD.md`, `REVIEW_QUESTIONS.md`, both anonymous records and
their referenced bodies/rows. Run `python -B verify_packet.py` if desired. The
packet uses a new independently shuffled **M/V** assignment. Source identities,
original headers, input checksums and the generator are held in a separate
controller-only key directory outside the repository; the key path is supplied
directly to the coordinator. Save both blind verdicts before opening it.

The packet contains **387 files**, including its manifest. An exact-byte
[archive copy](backend-trade-read-v3/blind-packet-retention-r2-527acf0980f8/)
is committed for reproducibility. Use the isolated Temp copy for the blind
review, because the surrounding repository exposes labelled results. Fixture
timestamps and recognizable query signatures remain possible chronology or
cross-round association clues; label randomization does not eliminate them.

| Manifest | SHA256 of `SHA256SUMS.txt` |
| --- | --- |
| [Raw evidence](backend-trade-read-v3/retention-r2/SHA256SUMS.txt), 395 files including manifest | `b7aa36cb9a1186a7eeaec946791f9c5de582f2ee8d822838851a4db05226c52b` |
| [Neutral packet](backend-trade-read-v3/blind-packet-retention-r2-527acf0980f8/SHA256SUMS.txt), 387 files including manifest | `dd07a3bfd69e09e27c43257be3a719d001c5d8446a9338746460829887c86d64` |

The original 24 raw evidence files and all eight original packet files still
match their existing manifests. Neither the first packet nor its mapping was
replaced. The existing evidence-directory `.gitattributes` preserves raw bytes.
Windows Git operations on the archive use command-scoped
`-c core.longpaths=true` for the content-addressed artifact filenames.

## Reproduction from the frozen harness

The retained [run wrapper](backend-trade-read-v3/retention-r2/run_matched.py) and
[commands](backend-trade-read-v3/retention-r2/runs.json) show the executed paths.
For another matched run, create fresh detached source directories rather than
altering an existing worktree. With the previously established Python/PG setup:

```powershell
$Python = 'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-backend-trade-env\venv312\Scripts\python.exe'
$Tag = [guid]::NewGuid().ToString('N')
$Root = Join-Path $env:LOCALAPPDATA 'Temp\opencode'
$Harness = Join-Path $Root "trade-retention-harness-$Tag"
$Old = Join-Path $Root "trade-retention-old-$Tag"
$Out = Join-Path $Root "trade-retention-output-$Tag"
git worktree add --detach $Harness 8070436f53dd98e9529e8c21ea7b0f7e3ecb6daf
git worktree add --detach $Old 701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd
$env:SIGHTBREAK_TEST_ADMIN_URL = 'postgresql://sightbreak:sightbreak_local_only@127.0.0.1:55439/postgres'
& $Python -B "$Harness/scripts/benchmark_trade_reads.py" --source $Old --runtime-reference 701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd --out "$Out/old" --samples 10
& $Python -B "$Harness/scripts/benchmark_trade_reads.py" --source $Harness --runtime-reference 4a8e9ea73aa8b286d9f1751b0a6b485479737294 --out "$Out/batched" --samples 10
& $Python -B "$Harness/scripts/verify_trade_read_artifacts.py" "$Out/old"
& $Python -B "$Harness/scripts/verify_trade_read_artifacts.py" "$Out/batched"
```

These are reproduction instructions, not additional executions performed while
packaging. The harness refuses an existing output directory, dirty backend or
harness/fixture, or a backend tree different from the runtime reference.

## Honest remaining qualifications

- Full snapshots substantiate **no observed net row mutation across captured
  intervals**, not absence of transient/reverted mutations, sequence/schema
  changes, server-wide activity or external side effects.
- Eight tables, including ledger and operations/receipts, remain empty in these
  fixtures; player balances start at zero. This is not fresh wallet, purchase,
  exact-retry, receipt-fingerprint or expected-price validation. Prior runtime
  results retain their existing scope and provenance.
- Hashes make retained artifacts recomputable, not third-party-attested capture.
  Capture/source provenance is a post-blinding review step.
- **Largest code gap remains unpaginated history**: 500-ID batches bound query
  parameter lists, not total response size or retained memory. Peak memory,
  large-database query plans and concurrent load remain unmeasured.
- A second-round critic verdict and affected integration acceptance remain
  pending. This evidence is not a merge, deployment or full V3 acceptance.
