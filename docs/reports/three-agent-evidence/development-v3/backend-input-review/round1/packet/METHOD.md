# Measurement method and limitations

## Workloads and environment

Both variants used the same deterministic fixture, measurement routine,
dependency versions, interpreter and PostgreSQL version on one Windows host.
The controller verified matching original routine/fixture fingerprints; the
fingerprints themselves are held with the identity key. The common versions are
copied into each anonymous record.

Workloads are `(trades, items per participant per trade)`:
`(0,0), (1,0), (1,2), (10,1), (40,1), (40,20), (501,0)`.
Each has two warm-up requests followed by ten timed requests. All records and
samples are retained in original within-workload order. Independent runs were
sequential, not interleaved; host load was uncontrolled. Absolute run times and
cross-variant execution order are withheld to avoid identity clues.

The fixture supplies a viewing account, one distinct partner per visible trade,
and unrelated accounts/trade data. The viewer alternates between the two
participant positions. Visible histories cycle through open, completed and
cancelled states. Each participant's stored offer order is reversed relative to
item construction. Item records and display names are deterministic. Setup and
snapshot queries occur outside the timed/counting window. These are synthetic
histories, not sampled production accounts.

Each workload uses in-process FastAPI TestClient GET requests to `/trades` with
real loopback PostgreSQL. An application ORM Session is created for each request.
Timing covers the TestClient call through receipt of the response; the explicit
JSON equality check follows the timer. SQL compilation/pool warm-up occurs first.
There is no external HTTP server or production network latency in the timings.

## Exact retained quantities

`samples[*].statements` counts SQLAlchemy `before_cursor_execute` callbacks during
that request. It excludes fixture setup, snapshots, driver-level pool pings and
transaction protocol messages. The routine asserts all captured SQL starts with
SELECT. `sql_shapes` contains deduplicated SQL text from the **last measured
request only**, not a complete per-request trace or bound parameters. Its length
can therefore be lower than the executed statement count.

`median_ms` is the ordinary median. `p95_ms` uses nearest-rank selection:
`sorted_times[ceil(10 * 0.95) - 1]`. For ten samples this is the maximum observed
sample, not a well-resolved population tail estimate or confidence bound.
`query_counts` is the sorted set of recorded per-request counts.

`budget` is a recorded acceptance threshold:
`3 + ceil(unique offered item IDs / 500) + ceil(unique participant IDs / 500)`.
The fixed three are session, account and participant-filtered trade reads.
The threshold is common to both variants and is not itself an observation.
For these fixtures, unique item IDs are `2 * trades * items_per_side` and unique
participants are `trades + 1` when trades are nonzero, otherwise zero.

## Response equivalence

Canonicalization sorts only the top-level trade list by trade ID and JSON object
keys. Stored offer and confirmation arrays retain their order. For each warm-up
and measured request, the routine asserts status 200 and complete equality to
the expected canonical fixture response. At workload end it hashes that
**expected** payload using SHA256 over compact sorted-key JSON, and stores the
digest under `response_sha256`.

Thus matching digests establish matching expected payloads. Successful completion
plus the retained routine's assertions supports observed response equivalence;
the packet contains neither the actual response bodies nor a separately captured
per-response digest. Avoid promoting this into an independently replayable body
or comprehensive public-contract audit.

## Authoritative state

Before warm-up and after the measured requests, the routine snapshots every
table in the authoritative ORM metadata using this operation:

```python
{
    name: db.execute(text(
        f'SELECT to_jsonb(t)::text FROM "{name}" t ORDER BY to_jsonb(t)::text'
    )).scalars().all()
    for name in sorted(Base.metadata.tables)
}
```

It records `read_only = after_snapshot == before_snapshot` and asserts that
boolean. The table set comprises players, sessions, ledger, items, operations,
audit, listings, trades, rewards, rate_buckets, game_tickets and loadouts. Schema
metadata, sequence state and concurrent server activity are not this comparison.

**Neither full snapshots nor authoritative-state hashes were written to the
retained result files.** `authoritative_state_hashes` is therefore explicitly
null in each anonymous record. `equivalence.json` preserves the reported
booleans but marks hash equivalence as not evaluable. No state digest has been
reconstructed from booleans, fixture data, result hashes or a new database run.

## Intended limits of a blind verdict

The packet permits arithmetic and internal-consistency review of measured query
counts/timings and recorded equivalence checks. It does not independently prove
source authorization/privacy logic, wallet conservation, receipt fingerprints,
exact retries or expected-price behavior. It contains no peak-memory,
large-database query-plan, concurrent-load or external HTTP measurements.
Give those categories separate evidence statuses rather than extrapolating a
passing performance result into acceptance of unexamined contracts.
