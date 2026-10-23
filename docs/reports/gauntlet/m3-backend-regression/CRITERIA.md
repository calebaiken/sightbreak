# M3 backend PostgreSQL regression criteria

Preregistered 2026-10-22 before runtime. Parent source is exactly
`a3b7070f7739ae854e643f905230ae2b6f1a85cb`, production backend tree
`67027b4fa17674ef067c84401af76eb1524419ac`. Only this qualification's report,
criteria and evidence driver may change. The run starts from a clean committed
worktree; its exact HEAD and content hashes are retained before and after.

The named, inspected benchmark is the unchanged repository
`backend/tests/test_economy.py`: all 44 test functions, expanded by pytest to
61 cases. This is a correctness comparison against the existing assertions;
blind visual A/B is inapplicable. No new product code, rewritten test, filter,
skip, xfail or weakened assertion may produce a pass.

Acceptance requires all of these observations:

1. A new owned disposable PostgreSQL container and volume, unique labels and
   database name ending `_test`, cached pinned image
   `postgres:17@sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3`,
   `--pull=never`, and a Docker-assigned random loopback-only host port other
   than 55432. No shared container/database or saved credentials are used.
2. The ephemeral fake password exists only in process memory and the disposable
   container runtime configuration until deletion. Evidence excludes environment
   values and redacts the generated password if a child unexpectedly prints it.
   Child environments override `DATABASE_URL`, set `SIGHTBREAK_SERVER_ID=local-relay`,
   and remove inherited `SIGHTBREAK_SERVER_KEY`. The suite sets its own fictional
   keys. No application server, Godot, rendered capture or OCR is needed.
3. Native PostgreSQL identity is queried independently through the loopback
   connection and inside the owned container before any fixture can TRUNCATE.
   Database, role, system identifier and server port must agree with the owned
   container. Repeat identity checks immediately before the unfiltered test run.
4. `backend/migrate.py` completes successfully within 60 seconds. Collection
   completes within 60 seconds. The unchanged suite completes within 300 seconds,
   with all 61 collected cases passing and zero failure, skip, error or xfail.
   Preserve full stdout/stderr, collected node IDs, JUnit, exit codes, durations,
   process IDs, native SQL identity/version, image ID/digest, labels and port.
5. Source HEAD, Git status, production tree IDs, per-file backend SHA-256 hashes,
   aggregate production content SHA-256 and driver/criteria SHA-256 are identical
   before and after runtime. Output is written under ignored `builds/` during
   execution, then copied into this report after the source-after snapshot.
6. Preserve every failure. Remove only resources whose exact ID/name and labels
   match this run. Verify container, owned volume, postmaster PID identity,
   child process groups and listener are gone. A fresh independent critic must
   inspect actual outputs before the root records this qualification as accepted.

These adversarial tests mint fictional fixture balances/items and submit fictional
match bodies through trusted test code. They do not establish real earned gameplay.
The separately accepted stock-account match keeps its own evidence and status.
This run fills the optional backend SQL gap beside the `b09cfe1` aggregate; it
cannot close whole G3/G16, security review, deployment, competitive policy,
remote impairment, AFK resistance or product release gates.
