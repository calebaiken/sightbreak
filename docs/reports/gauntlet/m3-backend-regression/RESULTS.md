# M3 backend PostgreSQL regression

The unchanged backend passes all 44 existing adversarial test functions,
expanded to 61 cases, on native PostgreSQL 17.11. Migration, source equality and
owned cleanup pass. Independent acceptance is pending; the builder does not
approve this qualification.

The exact clean runtime source is `48da99428d01d9ea8164457428643aa740b0eacd`,
on `codex/m3-backend-regression-a3b7070`, based on root source
`a3b7070f7739ae854e643f905230ae2b6f1a85cb`. Production backend, game, server,
scripts, workflow and installed-skill trees match that parent exactly. The
backend tree is `67027b4fa17674ef067c84401af76eb1524419ac`, also identical to
the backend omitted from the optional SQL lane in aggregate `b09cfe1`.
Only qualification criteria, driver and evidence were added.

## Benchmark and observations

[Criteria](CRITERIA.md) were committed before runtime as `741603c`.
The named, inspected benchmark is the existing `backend/tests/test_economy.py`.
The full collection and test commands run without filters, test edits or skips.
This assertion-based correctness check has no visual blind comparison.

| Observation | Actual output |
| --- | --- |
| Native migration | Exit 0; schema version 4; 0.736 process seconds |
| Collection | 44 test functions / 61 unique cases; exit 0; 1.086 process seconds |
| Existing pytest suite | 61 passed, zero failed/error/skipped; 6.43 pytest seconds / 6.797 process seconds; exit 0 |
| Warning | One preserved Starlette TestClient/httpx deprecation warning |
| Clean source | Before/after snapshots identical, empty Git status at exact `48da994` |
| Content identity | 426 production files; SHA-256 `8071166f98f588dd4f23131a3a8308becf272d040e5e856d897cf32a3d0d6251` |
| Backend and driver identity | Per-file backend and driver/criteria hashes retained and identical before/after |
| Owned cleanup | Container and volume absent, owned postmaster PID identity gone, child groups empty, listener absent, loopback connect refused |

The complete third attempt ran from 07:02:47.600692 to 07:03:03.129692 UTC on
2026-10-22. Native outputs are retained byte-for-byte under [attempt-3](attempt-3/):
[pytest stdout](attempt-3/pytest.log), [JUnit](attempt-3/pytest-junit.xml),
[test inventory](attempt-3/test-inventory.json), [migration](attempt-3/migration.log),
[schema](attempt-3/schema-after-migration.log), [step/process receipts](attempt-3/state.json),
[source before](attempt-3/source-before.json), [source after](attempt-3/source-after.json),
and [cleanup](attempt-3/cleanup.json).

## Disposable database identity

The driver used the cached pinned image with `--pull=never`; it performed no
installation. Image ID is
`sha256:327daa8fae7178d61f93142f146b098467b345e10997b9eb79f63bd58e5c8f3c`,
with digest `postgres@sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3`.

| Field | Owned value |
| --- | --- |
| Container | `sightbreak-backend-regression-0876b2c83512` |
| Exact container ID | `e130453452120c91d2047eef0ecdcc8e12b6942ff5eca324ee9d4e0389416802` |
| Qualification label | `io.sightbreak.qualification=sightbreak-backend-regression-0876b2c83512` |
| Owner label | `io.sightbreak.owner=backend_regression_builder` |
| Host listener | Docker-assigned `127.0.0.1:32773`, container TCP 5432 |
| Database / role | `sb_backend_0876b2c83512_test` / `sb_regression` |
| PostgreSQL system identifier | `7699384166174421036` |
| Native server | PostgreSQL 17.11, Debian 17.11-1.pgdg13+2, x86_64 |
| Volume | `sightbreak-backend-regression-0876b2c83512-data`, same ownership labels |
| Postmaster | PID 117578, start tick 2840963; absent after deletion |

Native TCP queries inside the owned container and through its loopback mapping
agree on database, role, system identifier, server port and start time. These
checks ran before migration, immediately before the TRUNCATE-bearing test suite,
and after the suite. The generated fake password stayed in memory and the
disposable runtime; evidence excludes environment values. Child environments
overrode `DATABASE_URL`, set `SIGHTBREAK_SERVER_ID=local-relay`, and removed the
inherited `SIGHTBREAK_SERVER_KEY`. Tests supplied their own fictional keys.
The driver verified exact resource IDs and labels before removing only its own
container and volume. Shared port 55432 and the shared development database were
never selected.

## Preserved rejected preflights

The first two attempts failed before migration, collection or tests. Each had a
fresh database/container/volume, preserved native outputs, unchanged-source
snapshots and successful owned cleanup. Neither is a backend test failure.

1. Source `741603c`, [attempt 1](attempt-1-identity-rejected/): the in-container
   witness used a Unix socket. PostgreSQL returns NULL for its TCP port on that
   connection, so the driver's port assertion rejected it. `a41401f` changes
   that witness to TCP and retains host-query evidence before assertions.
2. Source `8e1ebbf`, [attempt 2](attempt-2-startup-rejected/): Unix-socket
   readiness accepted the image's temporary initialization server while its
   TCP listener was closed. The native TCP witness reported connection refused.
   `48da994` makes readiness use TCP too. The third attempt then passes unchanged
   benchmark criteria. Both original rejections remain committed.

## Limits and next action

Fixtures deliberately mint fictional balances/items and submit fictional match
bodies. This is backend regression evidence; it proves no real earned gameplay.
The separately accepted stock-account match retains its own PASS and limitations.
The in-process FastAPI TestClient suite does not qualify deployed API hosting,
remote clients, competitive policy, meaningful participation or AFK resistance.
Whole G3/G16, security review, deployment and release acceptance remain open.

The largest remaining gap for this deliverable is independent inspection of
the actual source-bound evidence. The fresh critic must record its own verdict;
root owns canonical mission/progress/NEXT updates and integration.
