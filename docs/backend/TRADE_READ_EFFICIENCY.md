# Participant-private trade-read batching

## Scope and acceptance

`GET /trades` selects the authenticated participant's trades, then hydrates their
offered items and participant display names in batches of at most 500 IDs.
`trade_json` accepts request-local lookup maps; write routes continue using its
existing direct lookups. Name maps are reduced to the two participants of each
individual trade before serialization.

The response schema, agreed offer-array order, all trade states, current item
metadata (including transferred/consumed historical items), authentication and
participant visibility remain the contract. Top-level trade order remains
unspecified. There is no cross-request cache. The PostgreSQL economy advisory
lock, wallet mutations, receipt hashes/replay ordering, PR15 expected-price
validation and game/client interfaces retain their existing behavior.

This slice addresses database round trips. The endpoint still returns an
unpaginated history, and response size/memory remain proportional to that history.
Pagination/index selection and a measured replacement of global write
serialization require separate scope.

### Reproducible workload

- `backend/tests/test_trade_reads.py`: 13 real-PostgreSQL cases. Exact payloads,
  both participant positions, unrelated trades/name privacy, open/completed/
  cancelled states, reordered/repeated historical offers, changed current names
  and item metadata, consumed keys, all-table read-only checks, authentication
  expiry/revocation/inactive accounts and query budgets.
- `scripts/benchmark_trade_reads.py`: the same deterministic fixture and harness
  against any clean backend checkout. Two warm-up requests plus ten measured
  requests per workload, each with a fresh request/ORM session. Seven workloads:
  `(trades, items per side) = (0,0), (1,0), (1,2), (10,1), (40,1), (40,20), (501,0)`.
- The acceptance budget is `3 + ceil(unique offered item IDs / 500) +
  ceil(unique participant IDs / 500)`. The three fixed queries are session,
  account and participant-filtered trades. Empty ID sets cause no hydration
  query. SQLAlchemy `before_cursor_execute` counts application SQL, excluding
  fixture setup, pool-driver ping and transaction protocol messages.
- Canonical response hashes sort only top-level trade rows and JSON object keys;
  offer/confirmation arrays retain their original order. Every response must
  match the fixture, and all authoritative tables must remain byte-identical
  before/after each workload. Raw per-request timings and SQL shapes are saved.
  Timings are in-process TestClient plus loopback PostgreSQL, not a load test.
- Enhanced retention saves every distinct received raw/canonical response body,
  hashes every warm-up/timed response, and saves full canonical before/after rows
  for all 12 authoritative tables with per-table/aggregate hashes. The original
  first-round records contained expected-fixture hashes and state-equality
  booleans only. `scripts/verify_trade_read_artifacts.py <output>` independently
  recomputes the enhanced artifacts using only the standard library.
- `--runtime-reference <commit>` requires the shipping backend, excluding
  `backend/tests`, to match that revision, while recording the complete backend
  tree plus the distinct test/fixture and frozen harness hashes. For
  this evidence-only follow-up use `701ce2c` for the old source and `4a8e9ea` for
  the batching source. The fixture and two-warm-up/ten-sample workloads are fixed.

The [retained-artifact follow-up](../reports/BACKEND_TRADE_READ_RETENTION_R2.md)
records the exact enhanced harness freeze, executed commands, all actual bodies
and full table rows, offline falsifiers, qualified timings and a separately
mapped second-round neutral packet.

The current harness also records the actually imported fixture module's
`__file__`, resolved path and byte SHA256 before/after measurement, rejecting a
mismatch with the harness-root fixture. Earlier records hashed only the
harness-root file; later import replays must be identified as post-hoc evidence.

The query-budget test now checks every executed statement's bound-parameter
count directly against 500 as well as the round-trip budget. Targeted assurance
controls are reproducible with `scripts/check_trade_read_assurance.py --out
<new-directory>` using `SIGHTBREAK_TEST_ADMIN_URL`. They execute only the
1,600-item/502-participant boundary cases, then an isolated 500-to-5000 mutation,
fixture provenance controls and explicitly post-hoc frozen import replays.
The runtime in the working checkout is not mutated.

The original `backend/tests/test_economy.py` has 44 functions / **61 parametrized
cases**. Run it on the frozen baseline in the same interpreter/database version,
then run all **74** backend cases on the candidate. The old implementation is
also a negative control for the new query budgets; report those failures as
expected efficiency failures, not baseline economy failures.

## Windows setup (no Docker, psql installation or Windows service required)

Run PowerShell from a checkout of this branch. Use a new writable directory under
`$env:LOCALAPPDATA/Temp/opencode`, separate from source/evidence. Repository
`backend/dev-db.sh` pins PostgreSQL major 17, and `backend/pyproject.toml` permits
Python 3.12+. Existing broad matrix scripts have Linux-specific process/path
assumptions; the commands below and the slice's benchmark are native Windows.

### Python dependencies

The retained V2 suite ran Python 3.12. This machine's system Python 3.14.6 crashes
in a minimal FastAPI TestClient program, before Sightbreak logic; retain that
failure separately. Use uv-managed Python 3.12 for both sides of the comparison.

```powershell
$root = (Get-Location).Path
$tools = Join-Path $env:LOCALAPPDATA 'Temp/opencode/sightbreak-backend-trade-env'
$env:UV_CACHE_DIR = "$tools/uv-cache"
$env:UV_PYTHON_INSTALL_DIR = "$tools/python"
$env:UV_PROJECT_ENVIRONMENT = "$tools/venv312"
uv sync --project backend --frozen --python 3.12
$python = "$tools/venv312/Scripts/python.exe"
$env:PYTHONDONTWRITEBYTECODE = '1'
```

### Portable PostgreSQL

The measured Windows binary is EDB **17.11-5**, PostgreSQL reports **17.11**.
Download provenance: <https://www.enterprisedb.com/download-postgresql-binaries>,
17.11 Windows x86-64 link `fileid=1260616`, redirected to the URL below. Archive
SHA256 is `80379b2c04d51c30225532e0ae04509899141e9957ed096fe749d7fd9df8f82f`.

```powershell
$zip = "$tools/postgresql-17.11-5-windows-x64-binaries.zip"
Invoke-WebRequest 'https://get.enterprisedb.com/postgresql/postgresql-17.11-5-windows-x64-binaries.zip' -OutFile $zip
if ((Get-FileHash $zip -Algorithm SHA256).Hash.ToLower() -ne '80379b2c04d51c30225532e0ae04509899141e9957ed096fe749d7fd9df8f82f') { throw 'Archive hash mismatch' }
& $python -c 'import sys,zipfile; z=zipfile.ZipFile(sys.argv[1]); [z.extract(n,sys.argv[2]) for n in z.namelist() if n.startswith(("pgsql/bin/","pgsql/lib/","pgsql/share/"))]' $zip $tools
$bin = "$tools/pgsql/bin"
$data = "$tools/data"
'sightbreak_local_only' | Set-Content "$tools/local-password.txt" -Encoding ascii
& "$bin/initdb.exe" -D $data -U sightbreak --pwfile "$tools/local-password.txt" --auth=scram-sha-256 --encoding=UTF8 --locale=C
& "$bin/pg_ctl.exe" -D $data -l "$tools/postgres.log" -o '-h 127.0.0.1 -p 55439 -c max_connections=30 -c shared_buffers=32MB' -t 20 -w start *> "$tools/postgres-start.log"
```

Initialize only a new data directory; preserve an existing one. Port 55439 must
be unused. This uses the repository's public fictional-development credentials
on loopback. `pg_ctl` output must go to a file: capturing inherited subprocess
pipes on this host left a startup wrapper waiting after the server was ready.
No Windows service registration is needed. To stop this exact instance after
its users finish: `& "$bin/pg_ctl.exe" -D $data -m fast -w stop`.

### Tests and matched measurement

Create a dedicated `*_test` database through installed psycopg. The autouse test
fixture refuses other names and truncates its test tables on every case.

```powershell
$env:SIGHTBREAK_TEST_ADMIN_URL = 'postgresql://sightbreak:sightbreak_local_only@127.0.0.1:55439/postgres'
& $python -c 'import os,psycopg; c=psycopg.connect(os.environ["SIGHTBREAK_TEST_ADMIN_URL"],autocommit=True); c.execute("CREATE DATABASE sightbreak_trade_manual_test"); c.close()'
$env:DATABASE_URL = 'postgresql+psycopg://sightbreak:sightbreak_local_only@127.0.0.1:55439/sightbreak_trade_manual_test'
$env:PYTHONPATH = "$root/backend;$root/backend/tests"
$env:SIGHTBREAK_SERVER_ID = 'local-relay'
& $python backend/migrate.py
& $python -B -m pytest -p no:cacheprovider backend/tests -q
& $python -c 'import os,psycopg; c=psycopg.connect(os.environ["SIGHTBREAK_TEST_ADMIN_URL"],autocommit=True); c.execute("DROP DATABASE sightbreak_trade_manual_test WITH (FORCE)"); c.close()'

# Use an existing clean 701ce2c checkout as baseline. Each output directory must
# be new; the harness creates/drops only its own unique database automatically.
$baseline = 'C:/path/to/frozen-701ce2c-checkout'
& $python -B scripts/benchmark_trade_reads.py --source $baseline --out "$tools/evidence/baseline" --samples 10
& $python -B scripts/benchmark_trade_reads.py --source $root --out "$tools/evidence/candidate" --samples 10
```

For the baseline's original 61 cases, use a new disposable database and set
`PYTHONPATH` to that checkout's `backend` and `backend/tests`, then run its
`backend/tests/test_economy.py` with `--import-mode=importlib`. To apply the new
query-budget negative control to old code, retain that baseline `PYTHONPATH` and
run this branch's absolute `test_trade_reads.py` path with `--import-mode=importlib`.

Freeze/commit the candidate before measurement; the benchmark refuses a dirty
backend and verifies file hashes/identity at completion. Retain Python version,
package versions, PostgreSQL version, exact source and harness/fixture hashes,
all failures and raw logs. Query-count improvements are the deterministic gate;
host-dependent latency is supporting evidence.
