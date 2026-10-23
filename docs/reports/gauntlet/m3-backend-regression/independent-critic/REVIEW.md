# Independent backend PostgreSQL regression review

PASS for the declared bounded qualification. At clean source
`48da99428d01d9ea8164457428643aa740b0eacd`, the unchanged backend migrates and
passes every existing test in `backend/tests/test_economy.py`: 44 functions,
61 parametrized cases, zero failures, errors or skips. This fills the optional
backend SQL coverage omitted from aggregate `b09cfe1`; both use backend tree
`67027b4fa17674ef067c84401af76eb1524419ac`.

I inspected the original installed Gauntlet Loop, No AI Slop and its eval, the
mission, preregistered criteria, complete driver, migration, test fixture and
assertions. The benchmark is the repository's existing adversarial suite;
visual blind A/B does not apply. The builder's evidence commit is
`79c52a97c289756452a1a1da453db2754afa0748`, based on
`a3b7070f7739ae854e643f905230ae2b6f1a85cb`. Its entire diff is confined to this
qualification's documentation directory.

The independent [audit](audit.py) reads files, Git objects, safe Docker fields,
`/proc` identity records and listener state. It runs no application, migration,
pytest, SQL or game. Its [raw result](audit.json) retains the complete independently
expanded 61-case list, source receipt, resource observations and artifact hashes.

| Gate | Independent finding |
| --- | --- |
| Complete suite | AST literals expand to exactly 61 unique cases across all 44 functions. Every ID and its order match collection, verbose pytest output, pass summary and JUnit. |
| Migration and bounds | Schema version 4, exit 0 in 0.736 s. Collection exits 0 in 1.086 s. Pytest exits 0 in 6.797 process seconds, within the original 300 s bound. |
| Warning | The original Starlette TestClient/httpx deprecation warning remains. Pytest reports 61 passed, one warning in 6.43 s. |
| Exact source | Before/after receipts are identical and clean. I recomputed all 426 production file hashes, aggregate SHA-256 `8071166f98f588dd4f23131a3a8308becf272d040e5e856d897cf32a3d0d6251`, backend hashes and driver/criteria hashes, and checked the parent/runtime Git trees. |
| Owned database | Reviewed native receipts bind the `_test` database to the unique container, ownership labels, cached pinned image, volume and Docker-assigned `127.0.0.1:32773`. Port 55432 is never selected. |
| Native SQL identity | Before migration, before tests and after tests, internal TCP and mapped loopback queries agree on database, role, postmaster start time, server TCP port 5432 and system identifier `7699384166174421036`. |
| Evidence archive | All 80 manifest entries across three attempts match their files. Every original third-attempt file equals its committed archive byte for byte. |
| Actual cleanup | My own Docker checks find all three exact containers and volumes absent, with no container carrying their run labels. All three recorded postmasters are absent; no recorded child process group remains. Ports 32771, 32772 and 32773 have no listeners and return connection refused. |

The successful run used container
`e130453452120c91d2047eef0ecdcc8e12b6942ff5eca324ee9d4e0389416802`, database
`sb_backend_0876b2c83512_test`, role `sb_regression`, and volume
`sightbreak-backend-regression-0876b2c83512-data`. The image is cached PostgreSQL
17.11, image ID `sha256:327daa8fae7178d61f93142f146b098467b345e10997b9eb79f63bd58e5c8f3c`,
pinned by digest `postgres@sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3`.
I independently confirmed the cached image ID/digest after cleanup. Driver
inspection confirms `--pull=never`, an in-memory generated fake password,
environment-value exclusion/redaction, the owned `DATABASE_URL` override and
removal of inherited `SIGHTBREAK_SERVER_KEY`. Cleanup checks exact IDs and labels
before deletion. No runtime credential values were inspected during this review.

The run finished before my live SQL inspection. My database identity conclusion
rests on the retained native two-route SQL receipts and inspected driver;
my Docker, process and listener cleanup observations are direct. I do not claim
an independent live SQL query or a second execution of the destructive suite.

Both rejected attempts remain rejected. Attempt 1, source `741603c`, used a Unix
socket for its internal witness, so `inet_server_port()` was NULL and the TCP
identity assertion failed. Attempt 2, source `8e1ebbf`, accepted the image's
temporary Unix-socket initialization server as ready; its TCP witness then
received connection refused. Neither attempt reached migration, collection or
tests. The driver-only corrections select TCP for both observation and
readiness. The benchmark, assertions and criteria remain unchanged.

The largest remaining gap is qualification of deployed transport and substantive
earned gameplay. This suite uses in-process FastAPI TestClient and directly
creates fictional balances, inventory and match payloads. It cannot establish
real participation, AFK resistance, remote recovery, production role/security
policy or whole G3/G16 acceptance. The separately accepted stock-account match
keeps its own evidence and limits. No native, render, device or release gate is
promoted by this review.

The audit command used the original ignored output and committed failure archives:

```sh
python -B docs/reports/gauntlet/m3-backend-regression/independent-critic/audit.py \
  --source /workspace/sightbreak-backend-regression-a3b7070 \
  --run /workspace/sightbreak-backend-regression-a3b7070/builds/sightbreak-backend-regression-0876b2c83512 \
  --report /workspace/sightbreak-backend-regression-a3b7070/docs/reports/gauntlet/m3-backend-regression \
  --output docs/reports/gauntlet/m3-backend-regression/independent-critic/audit.json
```
