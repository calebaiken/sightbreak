# Source-only production market recovery design

No runtime has run for this component. The intended implementation adds test
orchestration and a native probe; production game/backend/server source stays
unchanged. Existing author attribution remains in the imported B-21 history.

Reuse the accepted transaction restart harness's before/after source receipts,
private XDG state, raw request/journal snapshots, native error guards and observed
process-kill sequence. Replace its fake SQLite authority with the unchanged
production PostgreSQL/API. Reuse the real native economy test's ordinary API
flow and trusted fixture helpers, while replacing its shared dev database and
credential-bearing fixture file with owned runtime resources and memory-only
authentication bootstrap. Do not run either existing script against shared
`sightbreak-postgres` as the new proof.

The planned market runner is `scripts/test_postgres_receipt_recovery.py` with
an explicit `--component market`. Native probe
`game/tests/postgres_receipt_probe.gd` loads a non-secret fixture configuration,
reads synthetic username/password only from its private environment, and calls
the real EconomyUI `_authenticate`, `_perform` and `_retry_pending` methods.
No auth token/password enters a configuration file or process argv. Fresh native
processes obtain new actual backend sessions. Expected total auth calls are nine
(three registrations and six native logins), below the unchanged per-minute
limit 15. Preserve that limit; failure is evidence, not grounds to disable it.

The transparent HTTP proxy forwards only to the fixed owned loopback API. It
records raw mutation method/path/body and the original backend response, but
redacts authentication bodies/headers/responses. Actual authentication responses
are parsed in memory to collect token values for the final leak scan. GETs and
ordinary responses are forwarded unchanged. A one-shot barrier for the original
market response and another for its first recovery response hold after the
production API has returned 200 and SQL has been retained. The driver proves
the native process is still alive, kills it, captures the journal and then closes
the held client socket without transmitting response headers. Barriers fail on
timeout; no fabricated backend status enters the product path. Revoke each killed
process's old session with actual `/auth/logout` and verify actual 401 before the
next fresh login. These token values remain only in the driver's/proxy's memory.

Use one new owned labelled PostgreSQL volume/container, a fixed digest with
`--pull=never`, and an OS-assigned loopback host port. Use the explicit managed
Docker socket and clear endpoint/context/TLS selectors per the installed runtime
skill. Preserve Docker config/proxy/registry identity; no daemon restart or network
change is needed. Establish external/internal SQL system identifier, postmaster,
database and role before schema/fixture writes, following the independently
qualified backend regression driver's ownership pattern. Use production
`backend/migrate.py`, production `/auth/register`, existing `credit`/`mint` helpers
only for labelled fictional seed, then real `/loadout` and `/market/list`.

SQL observations select full business records, excluding password hashes, session
tokens/hashes and rate-bucket internals. Retain wallet/XP, ledger including seeds,
all fixture items and listing, original operations, audit, loadouts, rewards and
game tickets. Authentication legitimately adds sessions/rate counters between
phases; it must not change business value. Compare the complete business state
after initial settlement, both rejected client controls, first replay, final
replay and post-clear restart. Keep repeated equal observations as separate
timestamped files. Do not infer a post-replay witness from a pre-replay query.

The wrong-origin native process signs in anew through a second owned proxy URL
to the same production backend. Its account ID matches, its base URL differs,
and its saved journal keeps the original URL. The expected failure is the real
client's origin guard, with no keyed POST at either proxy. This does not prove
remote origin security or cross-host token binding. The wrong-account native
process signs in as the distinct outsider and exercises the same real guard.

The independent critic gets the exact source freeze and non-secret container/DB
identity before native mutation, then uses an owned read-only SQL session while
the container is live. A final separate query starts after replay. Preserve the
runtime until the agreed read-only witness completes within a declared bounded
checkpoint; do not discard a failed/late witness or accept metadata alone.

Before launch, pure tests should poison each observation: duplicate ledger rows,
wrong seller proceeds/fee, changed item metadata or owner, duplicate operation,
changed request hash/price/body/path, missing loadout removal, missing/old SQL
witness, wrong account/origin POST, credential persistence, wrong image/source,
and incomplete cleanup. These tests challenge the oracle only. Native/HTTP/SQL
results stay UNVERIFIED until actually executed and independently reviewed.

Planned command, after implementation, fresh source freeze, critic review and
root lane release:

```sh
cd /workspace/sightbreak-postgres-receipt-recovery
/workspace/sightbreak/.venv/bin/python scripts/test_postgres_receipt_recovery.py \
  --component market \
  --godot /workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64 \
  --out /workspace/sightbreak-postgres-receipt-market-r1
```

The runner and native probe now exist as source. Before any launch, provide
the exact frozen SHA/hashes, pure results, resource/timeout plan and critic
witness commands to root and the fresh critic. The implemented driver checks
fixture state before dispatch and binds the API to an inherited owned loopback
socket, avoiding a reserve/close/rebind gap. Cleanup gets its own bounded window
after the work deadline, and authentication construction/read/close failures
withhold raw credential-bearing exception contents.
Root controls the local native lane; further engine use requires coordination.
