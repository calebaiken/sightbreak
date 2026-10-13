# Independent Phase F review — durable match results

Reviewer: separate Codex reviewer agent, read-only tracked source. This is automated same-model review, not an external security audit or human acceptance.

## Scope and recommendation

**Accept this scoped development change after the aggregate regression matrix passes its applicable gates.** No remaining Phase F blocking defect was found after the fixes below. This is not production approval or an 8.5/10 claim.

Reviewed implementation: `e954158`, follow-up restart fix `30ebfce`, and final durable-result branch `99773c30f6224c84928713cc137f792f417bafd3`. The same corrections were propagated to the later stack. Read-only review covered Godot staging, bridge/match status, SQLite worker, launcher, backend idempotency order, maintained tests, and operator documentation. No art or tracked source was edited by this reviewer.

Environment: Linux x86_64 6.18.44, Python 3.12.14, official Godot 4.7.2 (`ed1daf0bf`), local PostgreSQL 17. Godot was headless. No physical-device, power-loss or storage-hardware claims.

## Confirmed functionality

- Godot allows only explicit result and participant fields and writes bounded, unique final handoffs. `queued_for_delivery` does not claim settlement or grant currency.
- SQLite FULL/WAL commits the canonical immutable payload before source removal. Exact duplicate imports preserve one result row; changed payloads with the same identity are quarantined.
- Delivery retries exact payload bytes. Backend idempotency remains the reward authority. Moving only the staleness check after exact persisted replay allows late acknowledgment without permitting new stale results.
- Worker HTTP requires verified HTTPS or exact loopback HTTP, follows no redirects, bounds responses and timeouts, and keeps its credential in the environment. The worker has no listener.
- A failed worker prevents launcher startup or stops and reaps the game child. Restart preserves queued results. Delivery logs and retained records have bounds.

## Defects found and fixed during review

| Finding | Reproduction and final result |
|---|---|
| Import scan raced producer rename | Actual `.tmp` rename between directory inspection and stat raised `FileNotFoundError`. Final guarded scan completes; next scan imports one result. |
| Conflicting concurrent stages overwrote the same final path | Two actual Godot threads accepted different bodies for the same UUID in 30/50 original trials. Unique final destinations now retain both files; SQLite arbitrates identity. |
| Worker failure left game running / unreaped | Launcher initially only checked startup. Supervision now stops the game and waits for it, leaving no live child or zombie. |
| Restart read stale readiness marker | Existing startup log allowed the asynchronous truncation to race readiness checks; observed immediate false timeout. Synchronous truncation fixes the restart. |
| Partial-file quarantine raced producer completion | A producer paused beyond 10 seconds completed after partial JSON was read; quarantine rename raised uncaught `FileNotFoundError`. Final code tolerates completion, preserves the valid final file and imports it on the next scan. |

These were reliability defects, not demonstrated unauthorized currency creation. The completed final files survived the import races. No finding was dismissed solely because normal tests passed.

## Independently executed evidence

- Python worker/import/supervision: **11 tests passed**, `phasef-final-fixed-unit.log`.
- Godot staging: **9 checks passed**, `phasef-final-godot.log`.
- Actual Godot producer SIGKILL, actual isolated PostgreSQL connection outage, worker SIGKILL, real backend commit followed by withheld HTTP acknowledgment, restart, and duplicate source replay: **passed**. Ten reward rows, ten ledger grants, unchanged wallets after replay, and unchanged canonical payload/fingerprint. `phasef-final-crash-integration.log`; detailed logs `phasef/outbox-6b079b4a`. The maintained harness was copied with only review output location and ports changed to 3183/3184; its isolated database was dropped afterward. This run tested the committed initial F implementation; final follow-ups only add filesystem race handling/readiness ordering.
- Final concurrent stage probe: 50 UUIDs, two different bodies per UUID. Four second calls rejected sequentially; 46 raced successfully. **All 96 successful handoffs remained**, SQLite imported exactly 50 identity rows and quarantined 46 conflicts. This is queued, not committed, semantics. `phasef-final-stage-race.log`, `phasef/concurrency-final.json`.
- Final independent quarantine race: completes with zero imports during the rename, then imports one valid final file. `phasef-final-quarantine.log`.
- Final restart/supervision probe: launcher exits after worker death and game `/proc` entry is absent, proving reap. `phasef-final-launcher-fixed.log`. The earlier failed restart remains recorded in `phasef-final-launcher.log`.

External probe source and frozen implementation copies are in this review directory. Maintained regressions cover the discovered races; no failing tests were removed.

## Remaining limits and risks

- Completed Godot flush/rename handoffs survived process termination. Power failure before SQLite import, filesystem exhaustion, corrupt media, backup/restore and disaster recovery remain **UNVERIFIED**.
- New results older than the backend's existing 15-minute freshness window are still rejected. A long outage can leave legitimate participants unpaid. This is explicitly documented and needs a product/security policy decision; timestamps must not be rewritten.
- Capacity failure is surfaced; unlimited durability is not promised. Operators must preserve server-local storage, monitor dead results/full queues, and use one database/spool pair per server.
- Concurrent conflicting handoffs cannot both settle. Their `queued` response is not proof which payload wins arbitration; normal authoritative producer code should never generate conflicting identities.
- Input eligibility, bot farming/AFK policy, currency amounts, case odds, marketplace and trading logic were not redesigned. Full aggregate regression evidence is separate from this focused review.
- No blanket security, performance or backend quality score is supported by these tests alone.
