# Proposed first market runtime

Status: source/pure controls only. Root authorization is still required before
starting PostgreSQL, API, proxy or native transaction processes. One authorized
private pinned editor import passed on clean `38d78ff` in 5.957 seconds; no other
engine or service has run for this component. Native probe bytes are unchanged
since that check. Current root owns unrelated native work.

One market sequence is planned. Store and case are separate unqualified work.
Use a clean frozen own branch, the existing backend interpreter, pinned Linux
Godot bytes and cached PostgreSQL digest. The runner refuses production source
changes, dirty source, wrong engine/image, shared port 55432, unowned container
or volume identity and a mismatched SQL cluster before fixture writes. It creates
only a new labelled volume/container, a new loopback API listener and two owned
loopback proxy listeners. No pull, deployment, credential file or shared DB.

```sh
cd /workspace/sightbreak-postgres-receipt-recovery
/workspace/sightbreak/.venv/bin/python scripts/test_postgres_receipt_recovery.py \
  --component market \
  --godot /workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64 \
  --out /workspace/sightbreak-postgres-receipt-market-r1
```

The source workload has a 240-second wall bound; cleanup has an independent
60-second allowance even on failure. Specific existing/bounded waits are PG
readiness 30 seconds, migrations 60, API readiness 20, normal native completion
35, held-response observation 10 and proxy hold 15. Native EconomyAPI retains
its unchanged 12-second request timeout. An expired/missing barrier is a failure;
the proxy never invents a successful reply. Each native process runs alone.

The driver pauses at two 60-second read-only observer checkpoints. It prints
the exact ready-marker path while live, enabling root/critic coordination:

```text
<out>/observer/pre_original.ready.json
<out>/observer/post_final_refresh.ready.json
```

Each marker carries non-secret run/phase, exact container ID and label, database
name/role, cluster system ID, frozen source commit, actual phase clocks, selected
read-only SQL file and matching release-marker path. The pre-original marker
follows real registration, trusted fictional setup, listing/equip, verified SQL
ownership and fixture oracle; no native purchase has started. The post-final
marker follows final native response, fresh account/inventory reads, normal exit
and a distinct fresh SQL query. It precedes post-clear restart and cleanup.

The fresh critic independently verifies the container label/ID/database and
executes selected-field SQL through the explicit local Docker socket, for example:

```text
docker --host=unix:///var/run/docker.sock exec <verified-owned-container-id> \
  psql -X -U sb_receipt -d <verified-owned-test-database> -At \
  --set=ON_ERROR_STOP=1 -c <inspected-read-only-SQL>
```

No password or environment dump is needed for the internal read-only observer.
The critic records its own query start, SQL clock, completion, phase and raw SQL
outside the source tree. Only after that inspection succeeds does it create the
matching release file with JSON fields `run`, `phase`, `status: "observed"`.
These are handoff acknowledgments, not substitutes for retained independent SQL.
A missing/late witness fails the bounded attempt and remains retained.

The runner preserves per-phase sanitized native/API logs, raw non-auth market
request bodies, actual backend responses, exact journal captures, unique SQL
files, both event clocks, PID/start identities, resource IDs/bindings, source
before/after and cleanup receipts. Auth bodies/replies/headers, native bootstrap
passwords/tokens and DB secrets never enter argv or retained configuration.
Known plaintext auth values are checked across all persistent client/output
bytes. A log redaction event itself fails privacy qualification.

Before launch, root and critic get the exact clean freeze and hashes plus pure
controls. After the source-only critic permits one attempt and root releases
the lane, send the actual driver PID/session/output path immediately so the
critic can observe live owned process/socket/SQL state. No automatic retry,
postmatch/earned-value claim, rendered consent claim or broad aggregate is part
of this command. Production game/backend/server code remains unchanged.
