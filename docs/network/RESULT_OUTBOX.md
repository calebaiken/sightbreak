# Authoritative result recovery

`serve-account-match.sh` starts a local worker before admitting account matches. Set `SIGHTBREAK_RESULT_SPOOL`, `SIGHTBREAK_RESULT_DB` and `SIGHTBREAK_RESULT_LOG` to persistent, server-only paths when operating a development server. Defaults are under `.local/server-results`. The worker has no listening socket. `SIGHTBREAK_SERVER_KEY` remains environment-only. Do not copy this directory into client builds.

Godot allowlists result fields, flushes a bounded JSON record and atomically renames a unique handoff file. Sequential identity collisions are rejected; concurrent files cannot overwrite each other. SQLite serializes and verifies the canonical payload fingerprint for each match identity. A conflicting concurrent handoff is quarantined, never silently substituted. The backend remains the sole reward authority. `queued_for_delivery` means persisted for delivery, not settled or credited.

The Python worker commits an immutable payload to SQLite with FULL synchronous/WAL before deleting its handoff. It retries the exact bytes, with 2–60 second backoff. Exact backend idempotent replays can now acknowledge an already committed result after the normal freshness window; new stale identities still fail. Lost responses cannot create additional rewards. The launcher refuses startup without a ready worker and shuts down/reaps its game child if the worker later dies. Restarting the same paths resumes delivery.

## Bounds and failure policy

- 16KiB per record; 512 handoff files; 2,048 SQLite records. Full queues retain source files and require operator recovery. No successful settlement is claimed on capacity failure.
- Pending delivery has a one-day local retry horizon. Committed/dead receipts expire after seven days; malformed partial files are quarantined and expire after one day. Delivery metadata rotates at 1MiB with three backups.
- The existing backend **15-minute freshness limit** still rejects a newly delivered old result. Long outages can therefore leave legitimate results unpaid. Changing that earning policy requires separate product/security approval. The worker never rewrites timestamps or identities to bypass it.
- Completed Godot handoffs were tested against process SIGKILL. Before SQLite import, Godot flush/rename is **not a power-loss guarantee**. Storage hardware durability, disk failure, backup/restore and filesystem exhaustion remain unverified.
- One worker lock per database prevents concurrent delivery. Operators must use one database/spool pair per dedicated server and preserve it across restarts. Do not share a spool across independent worker databases.
- Inactive/disconnected participant eligibility and all economy rates/odds are unchanged. Existing all-roster eligibility can penalize active teammates; this remains an explicit product decision.

## Reproduction evidence

Environment: Linux x86_64, Godot4.7.2, Python3.12, PostgreSQL17 local Docker. Run `python3 -m unittest discover -s server/tests -v`, the Godot `result_outbox_test.gd`, and `.venv/bin/python scripts/test_result_outbox.py`. The integration harness creates/drops a randomly named isolated test database and uses ports8183/8184. It kills actual Godot after staging, interrupts database access, kills/restarts the worker, withholds a real backend acknowledgment after commit, then replays the source file. Final assertions require ten reward records, ten ledger grants, exact payload identity and unchanged wallets. It never disables the shared PostgreSQL service or touches development accounts.

Final local results: Godot9/9; worker/import/supervisor10/10; PostgreSQL51/51; crash/outage/lost-ack integration passed (`outbox-26059b51`). Full stack regression status is recorded separately in `CODEX_NETWORK_QA.md`.
