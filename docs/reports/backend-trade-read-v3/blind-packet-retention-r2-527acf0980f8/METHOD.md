# Method, representations and evidence boundary

## Matched execution

Both variants used the same frozen measurement routine, deterministic fixture,
Python/dependency versions and PostgreSQL service on one shared Windows host.
The controller retained exact source/routine/fixture identities outside this
packet. The complete backend trees were checked against their runtime references
and backend file identities checked before/after execution. The common runtime
versions are copied into each anonymous measurement record.

Workloads `(visible trades, items per participant per trade)` are
`(0,0), (1,0), (1,2), (10,1), (40,1), (40,20), (501,0)`.
Each run created a unique isolated test database, loaded the same migrations,
truncated all authoritative tables between workloads, and dropped only its own
database afterward. All seven workloads on one variant preceded the other
variant's run. There was no interleaving, host-load isolation or concurrent-load
experiment. Another coordinating workload could use the same PostgreSQL service
in a different database. Both original run exit codes were zero.

The fixture supplies a fictional viewing account, one distinct partner per
visible trade, and unrelated accounts plus a hidden trade. Thus zero visible
trades is not an entirely empty database. Viewer position alternates between
participants; histories cycle through open/completed/cancelled states. Offered
item order is reversed relative to construction order. Current item records,
display names and fixture IDs are deterministic. Password fields are unusable
fixture markers; session rows contain only hashes of fictional fixture tokens.
Request authorization headers and raw tokens are not retained.

Players have zero starting balances. Players, sessions and trades are populated;
items are populated in the four item-bearing workloads. Audit, game tickets,
ledger, listings, loadouts, operations, rate buckets and rewards are empty in
every workload. The snapshots prove their retained emptiness, not successful
execution or replay of monetary transactions against populated receipt/ledger
histories.

## Request timing and SQL

Two warm-up requests precede ten timed FastAPI TestClient GET `/trades` requests
per workload. PostgreSQL is real and loopback-connected; the HTTP client runs
in-process. Each request has a fresh application ORM session. Timing brackets
only the TestClient call; response parsing, assertions and artifact writes occur
afterward. Setup and table snapshots are outside the counting/timing window.
Artifact writes between requests may still affect cache or scheduling behavior.

`samples[*].statements` counts SQLAlchemy `before_cursor_execute` callbacks,
excluding driver pool pings and transaction protocol messages. The routine
checks captured SQL begins with SELECT. `sql_shapes` contains unique SQL strings
from only the final timed request of the workload, without bound parameters; it
is not a full per-request SQL trace. Preserve the distinction between the number
of shapes and the number of executed statements.

`median_ms` is the ordinary median. `p95_ms` is nearest-rank selection, which is
the maximum for ten samples. Neither is a population confidence bound. Sample
order is preserved. `query_counts` is the sorted set of timed-request counts.
The common recorded budget is
`3 + ceil(unique offered item IDs / 500) + ceil(unique participants / 500)`.
The fixed three are authentication/session/account and participant-filtered
trade reads. Fixtures have `2 * trades * items_per_side` unique offered items
and `trades + 1` participants when trades is nonzero, otherwise zero. The
threshold is an acceptance target, not an observed query count.

## Received response evidence

For every warm-up and timed response, the routine saved `response.content`
bytes before comparing its parsed JSON to the expected fixture. Identical bodies
within a workload share a content-addressed file, but every returned response
retains its own status and raw/canonical hash references. The hash is SHA256 over
exact raw bytes, including their original object/array order.

Canonical JSON uses Python `json.dumps(value, sort_keys=True,
separators=(',', ':'), allow_nan=False)` with default `ensure_ascii=True`, encoded
as UTF-8 without a newline. Response canonicalization sorts the top-level trade
list by ID and JSON object keys. Every nested offer/confirmation/item array keeps
its original order. The endpoint promises no top-level trade order.

`expected_response_sha256` hashes only the separate expected fixture file.
`actual_response_sha256s` is the set of canonical hashes derived from the
received responses. The verifier rehashes raw bytes, parses and canonicalizes
them, checks the complete top-level envelope is exactly `{"trades": ...}`,
compares every actual body to the retained expected body, and compares actual
canonical payloads across variants. A matching expected-fixture hash alone is
not the acceptance criterion in this round.

## Authoritative rows

Immediately before warm-up and after the timed requests, the routine obtained
all rows in each of twelve authoritative ORM tables using:

```python
{
    name: db.execute(text(
        f'SELECT to_jsonb(t)::text FROM "{name}" t ORDER BY to_jsonb(t)::text'
    )).scalars().all()
    for name in sorted(Base.metadata.tables)
}
```

It parsed each PostgreSQL JSON row, sorted each table's rows by the canonical
JSON bytes above, and saved the entire array. Each per-table hash is over those
saved array bytes. The aggregate hash is over the canonical object mapping each
sorted table name to its full row array, reconstructed from all table files.
The table set is players, sessions, ledger, items, operations, audit, listings,
trades, rewards, rate_buckets, game_tickets and loadouts.

The verifier compares full before/after arrays, per-table hashes and aggregate
hashes **within each workload/run**. The original comparison of PostgreSQL JSON
strings is also retained as `read_only`. Cross-variant session expiry timestamps
are independently seeded and differ; aggregate state hashes across variants
are therefore not expected to match. Original rows/timestamps have not been
redacted, normalized or replaced to force equality. The symmetric comparison
also reports which cross-variant tables/columns differ.

This establishes no observed net row mutation across each captured interval for
these fixtures. It does not establish absence of transient changes subsequently
reverted, sequence/schema changes, server-wide activity, external side effects,
or universal read-only behavior. These are isolated fixture databases, not a
production snapshot or a concurrent-writer consistency experiment.

## Review scope

Use query counts as deterministic observations; report every timing regression
as well as improvement, and qualify extrapolations. No peak-memory, large-table
query-plan, production-network or concurrent-load data was collected. Histories
remain unpaginated; 500-ID query batches do not bound total response size or
retained memory.

Full artifact hashes make the retained data independently recomputable, not a
third-party attestation of capture. Assess capture/source provenance only after
saving the blind verdict and receiving the external key. Source authority,
adversarial authentication, wallet conservation, receipt fingerprints, exact
retries and expected-price contracts require their separately scoped evidence.
