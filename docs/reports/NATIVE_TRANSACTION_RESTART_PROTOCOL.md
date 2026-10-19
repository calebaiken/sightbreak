# B-21 real PostgreSQL/native restart oracle — frozen protocol

## Question and decision rule

Can a normal native `EconomyUI._perform` marketplace purchase recover its exact
committed receipt after process termination before the HTTP response arrives?
Compare immutable candidate `cda63723e6d9fe43e13fb39aa029b54cc63ecf24` with frozen
V2 `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` using the **same** external harness
and probe. Both revisions have the same backend tree.

For each revision run three serial cases, at integer prices **400, 401, and
10,000,000**. Each case uses new original accounts, item, listing, receipt key,
journal, proxy, and three separate native processes. A real disposable PostgreSQL
database is shared only among cases in that one invocation. Fixture balances are
explicitly marked `fictional_test_fixture` in actual PostgreSQL ledger rows.

The core authority checks must pass in both arms. Candidate recovery must pass
every recovery check; baseline is expected to lose the receipt. A baseline
negative control is not a candidate feature pass. Retain every failed or aborted
attempt; do not silently replace evidence when revising the harness.

## Fixed sequence

1. Copy `git archive <exact commit> game backend` into a private directory. Copy
   cached `.godot` import metadata from a clean checkout with the same game tree.
   Record archive, extracted-source manifest, cache manifest, executable,
   harness/probe hashes, checkout SHA/tree/status before and after measurement.
   No editor import or execution in the shared/main checkout is required.
2. Create only `sightbreak_receipt_<random hex>_test`; create the production schema
   and apply every committed migration. Start unmodified Uvicorn on ephemeral
   loopback. Verify `/health`, and record PostgreSQL version, actual database,
   server port, reader PID, transaction snapshot, and database clock on each read.
3. Seed fictional buyer/seller balances using production `credit`, and an item
   using `mint`, following the existing backend test helpers. Create the listing
   through real HTTP. Capture all economic tables before the purchase. Password
   hashes and plaintext credentials are excluded from published snapshots.
4. Launch the native external probe with Python `Popen`. It constructs the real
   UI, supplies its isolated journal path when supported, and calls the normal
   `_authenticate` method. This performs actual HTTP login and refresh. It calls
   `_perform` with the saved key and integer `expected_price`; neither API nor UI
   is mocked or patched. This probes the normal transaction method, not mouse or
   touch interaction with the confirmation sheet.
5. The HTTP proxy forwards the original request bytes unchanged. After receiving
   the entire real backend response it holds **all response headers and bytes**.
   A separate read-only PostgreSQL connection must observe the committed buyer
   debit, seller credit, fee burn, item transfer, sold listing, exact `Operation`,
   two new `Ledger` rows, and one `market_settled` `Audit` row. Capture journal
   bytes before termination. Assert kill occurs within six seconds of the hold
   barrier, before the production client's twelve-second request timeout.
6. Record wall/monotonic timestamps and PID; `kill()` and `communicate()` confirm
   native termination. There must be no native completion marker. Capture the
   journal and PostgreSQL state after death. Discard the held response without
   writing any client headers or bytes.
7. Restart the same UI against the same server and journal. Sign in to the
   original account through real HTTP, receiving a fresh token. Call
   `_retry_pending` without supplying a reconstructed pending receipt. Compare
   the full native result with the original committed response and the stored
   `Operation.response`; compare all economic rows with the committed snapshot.
   Check the retried key/body, including strict integer `expected_price`.
8. Restart and authenticate once more with a third distinct token. Call
   `_retry_pending`; require no saved pending receipt, empty result, no new
   purchase HTTP request, and exactly unchanged economic rows. Match every login
   token digest/account to its actual PostgreSQL session row. Token digests are
   evidence of distinct sessions, not reusable bearer credentials.
9. Stop the service, dispose connections, drop only the generated database and
   verify its absence. Publish raw safe transcripts, exact journal bytes,
   PostgreSQL snapshots, manifests, and per-check results.

## Optional existing native economy regression

For the candidate, retain a run of the existing `native_economy_test.gd` unchanged.
Also retain an external copy with exactly one declared test-only calibration:
`http://127.0.0.1:9` becomes `http://native-receipt-oracle.invalid`. The original
assumes Windows TCP failure is classified as `not_reached`; the calibration uses
the reserved `.invalid` DNS namespace to exercise a deterministic resolution
failure. Both run against the same real service with separate seed accounts.
Store both executed sources, hashes, stdout/stderr, exit codes, and tallies.
An original failure remains a failure and does not get relabelled by the
calibrated result. This supplemental test is reported separately from the crash
oracle's `core_pass`.

## Running

Freeze the added harness/probe/protocol in a clean commit first. Evidence output
must be outside tracked source (for example, a unique `.runtime` directory).
Use the Python 3.12.14 environment with Psycopg, SQLAlchemy, FastAPI and Uvicorn.
The default database connection is the provided portable PostgreSQL 17.11 on
`127.0.0.1:55439` with fictional development credentials. The harness refuses to
start a native process when the official Godot executable already has a process
running; coordinate a serial native-run slot on this shared host.

```powershell
python scripts/validate_native_transaction_restart.py `
  --source <clean-repository> --revision <exact-commit> `
  --cache-source <clean-same-revision-checkout>/game/.godot `
  --godot <Godot_v4.7.2-stable_win64.exe> --out <new-output-directory> `
  --repetitions 3 --expect-recovered <0-for-baseline-or-1-for-candidate>
```

Add `--native-economy` to the candidate invocation for the supplemental runs.
Evidence is an application-process-crash oracle. It does not measure machine
power loss, filesystem durability across power loss, or backend process failure.
Fresh independent blinded criticism is a separate main-session gate.
