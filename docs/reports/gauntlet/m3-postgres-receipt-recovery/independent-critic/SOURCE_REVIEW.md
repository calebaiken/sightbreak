# Independent production market boundary review

Status: SOURCE REVIEW IN PROGRESS. No new PostgreSQL/API/native result is accepted.

The inspected root is `05277154c6b8c92b80fd7c25e8365de9efdc4fae`. Its game
tree is `1f3616afdfaaed0fb7c9ffbd0aa8e4947f7d2a48`, backend tree
`67027b4fa17674ef067c84401af76eb1524419ac`, and server tree
`667e900f73c12d75f6824d4befcadeae4223050e`. Game and backend match accepted
receipt checkpoint `89393f3`; the game also matches native candidate `79e076e`.
The critic uses an owned sparse worktree and has launched no engine, service,
renderer, OCR process or CI job. Root owns the runtime lane.

The original Gauntlet, project Gauntlet, No AI Slop and its eval, mission,
acceptance matrix, contributor instructions and accepted B-21 reports were read.
B-21 established native SQLite fixture recovery, candidate 12/12 versus baseline
0/12. It supplies no production PostgreSQL or player-pixel evidence.

## Inspected contract

`backend/app.py` authenticates actual login passwords with Argon2 and issues a
new in-memory bearer token. Production writes execute inside a PostgreSQL
transaction under the service advisory lock. `replay` scopes receipts to the
authenticated actor, route and UUID, and compares the canonical payload hash.
`market_buy` checks replay before listing availability or the live price guard.
Thus an exact committed receipt can be replayed after the listing is sold.

For this preregistered fictional fixture, a 400-credit purchase from initial
buyer 1000 / seller 100 / outsider 0 must produce buyer 600 / seller 488 /
outsider 0. Configuration sets 300 basis points, so the fee is 12. The exact
business operation ID is `<buyer>:buy:<listing>:<idempotency UUID>`. The two sale
ledger rows use the listing ID as reference, with `market_purchase` -400 / final
balance 600 and `market_sale` +388 / final balance 488. The transfer clears the
item reservation, makes the buyer the owner, marks the listing sold to that
buyer, deletes the seller's equipped loadout, and appends one `market_settled`
audit event with fee 12. Fixture funding rows are distinct from these sale rows.
All four migrations, including append-only audit/ledger triggers and the active
listing index, belong to the production contract.

`EconomyUI._authenticate` uses actual `/auth/login` through `EconomyAPI`, clears
its password field and refreshes `/me`, `/inventory`, `/catalog` and `/loadout`.
`_perform` durably stages the exact keyed intent before dispatch. `_retry_pending`
requires the saved account and server before any API call and then sends the
saved path, payload, message and method. `_send_transaction` clears only a valid
confirmation and refreshes authoritative state. It does not grant inventory or
credits from the saved local record. The journal permits six transaction fields,
has an 8 KiB bound and retains failed recovery. Credentials have no journal field.

## Prelaunch requirements sent to the builder

- Freeze the preregistration and actual driver/probe source before runtime.
  Record clean before/after identities, the pinned Godot executable and cached
  owned PostgreSQL 17 image/version. Refuse destructive setup on other databases.
- Retain the exact original and every replay POST path, method, raw body bytes,
  parsed UUID and expected price 400. Match the canonical operation hash and
  stored business response to those values and the original journal bytes.
- Preserve actual upstream 200 received by the transparent owned proxy, a SQL
  observation of committed business state, original native alive status, and
  acknowledged SIGKILL before forwarding that response. Repeat the held-200
  recovery boundary with a second native process; retain all failures.
- Actual wrong-account and second-owned-origin login controls must preserve
  identical journal bytes and dispatch no market POST. Retain control request
  counts and actual SQL state; never infer refusal from a UI message alone.
- Recover with fresh actual login, observe the exact saved response, server-read
  balances/inventory/loadout and disk clear, then restart again and establish no
  mutation replay. Retain a separately requested SQL query after final replay and
  refresh. Independent live SQL must query only whitelisted business fields.
- Preserve failure streams without raw login bodies, login replies, bearer
  headers, token hashes, password hashes or credential-bearing process arguments.
  Audit allowed evidence and journal/state files without printing credentials.
- Verify every owned API/proxy/native process, listener and PostgreSQL container
  is gone after success or failure. No fictional fixture may be described as
  earned value, remote-host evidence, rendered consent, whole G3 or whole G16.

No blind or presentation verdict is possible for this source-only review. The
largest open boundary is the actual production lost-response run and its raw SQL
witnesses. Player input, rendered consent and usability remain separate gates.

## Preregistration review

Builder commit `8e9de18` records `CRITERIA.md` and `DESIGN.md` before
implementation. The critic also read the builder's subsequent visible draft
edits that incorporate the requirements above. The proposed market component is
suitable for implementation and further source review. This is not permission
to start runtime while root owns the lane, or acceptance of a future run.

The proposed independent observation uses the explicit local Docker socket and
`docker exec` into the exact labelled owned container, with PostgreSQL's local
socket and a known fixture role/database. It avoids a persisted password or DSN.
The builder will supply nonsecret ownership/identity handoffs before the original
native mutation and after the final response plus authoritative refresh. The
critic will retain its own selected-field query results and clock observations.

## Corrected frozen harness review

Source/pure verdict: ACCEPT `882931dd7024c2b200a72b2a52017dd98b95ee6a` for
one bounded market attempt after root releases the runtime lane. Actual
PostgreSQL/API/native recovery remains UNVERIFIED. This review started no
engine, Docker command, service, socket, HTTP request or SQL session.

The rejected `f5bea86141c66e4753d2ef3d2e49f122ad9398bc` remains recorded in
`independent-f5bea861-falsifiers.json`. Its two original independent falsifiers
show matching poisoned stored/HTTP item metadata passing the oracle and a
forwarded wrong-route purchase missing from evidence. Additional mocked tests
also exposed missing new-process/listener/query deadline checks, unrecorded
failed/PUT mutations and missing initial postmaster binding. These are harness
failures; they are not production product defects or failed native campaigns.

The corrected clean freeze passes the preserved two falsifiers and nine new
independent guard groups in `source_guards_v2.py`. The critic also reran all nine
maintained oracle groups and seventeen maintained guard groups. Exact outputs,
component SHA-256 values and clean before/after receipts are retained in
`independent-882931dd-falsifiers.json`. The new startup probe drives `execute`
through mocked setup: valid owned metadata reaches the migration boundary;
wrong volume label, mount name, destination or write mode stops before it.
Every external entrypoint is mocked and the migration itself is never executed.

The corrected recorder retains attempts before validation/forwarding, including
wrong routes, refused responses, upstream errors, PUT, PATCH and DELETE.
Wrong-account/origin and post-clear gates count all non-auth mutation attempts.
The SQL oracle now joins the full returned item to selected SQL metadata,
including wear, seed, variant, definition, eligibility and acquisition timestamp.
The initial cluster/postmaster/role are bound to subsequent SQL snapshots.
New processes, listeners, requests and queries check the work deadline; cleanup
has a separate bounded allowance. Authentication construction, request, read and
close failures suppress credential-bearing details. The deterministic journal
listener is bound to each killed native PID/inode and included in closure checks.

Runner SHA-256 is
`1cc2a4167534a4fd27938b8993f4265f4f365faeb0534cdd0d7c83e337bc621b`;
oracle SHA-256 is
`6052d8923a33918ba9a21d26a7ca3ebd4b8b6113fe8adba88f1eea4980604019`.
The only game differences from accepted `89393f3` are the new native test and
its UID; production game, backend and server files remain equal.

## Independent live witness plan

At both `pre_original` and `post_final_refresh`, inspect the exact ready marker,
verify the frozen source, run identity and full CID, then query only that owned
container. Inspect selected Docker fields for run/owner labels, image identity,
loopback mapping and exact named writable data volume; separately verify its
volume labels. Never inspect Docker `.Config.Env`, process environments or
credential files. Preserve Docker config/proxy identity and clear only endpoint,
context and TLS selectors for the explicit managed local socket.

Use the frozen `BUSINESS_SQL` with `psql -X -At --set=ON_ERROR_STOP=1` under
`PGOPTIONS=-c default_transaction_read_only=on -c statement_timeout=5000`, role
`sb_receipt`, exact owned test database and the verified CID. Internal local
socket authentication needs no password/DSN in argv or evidence. Retain the
selected SQL text/hash, raw selected result, independently requested/completed
monotonic and wall clocks, actual SQL clock, phase/query ID, source, cluster and
postmaster. Check pre-original fixture state independently. The post-final
query must begin after the final response and fresh native account/inventory
refresh, and independently recompute the one settlement against the first
witness and actual original response. Do not reuse a prior query.

Only after each retained witness passes should the critic write its matching
release JSON (`run`, `phase`, `status: observed`). Both checkpoints remain under
the runner's existing 60-second/240-second bounds. After completion inspect all
raw native/proxy/API/journal/SQL/source/cleanup outputs and retain failures.
Fictional owned fixture value, local process kills and native method calls do
not qualify earned progression, remote hosts, host power loss or rendered player
consent. Those acceptance boundaries stay open.
