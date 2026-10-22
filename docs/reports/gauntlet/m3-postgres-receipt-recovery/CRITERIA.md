# M3: production PostgreSQL market receipt recovery

Registered before implementation or runtime on 2026-10-22. Own branch is
`codex/m3-postgres-receipt-recovery`, sparse worktree
`/workspace/sightbreak-postgres-receipt-recovery`, base
`89393f3d1e059a3da35533e0bd84e98a098c691c`. Production game tree is
`1f3616afdfaaed0fb7c9ffbd0aa8e4947f7d2a48`; backend tree is
`67027b4fa17674ef067c84401af76eb1524419ac`.

## Retrieved benchmark and measured gap

The named bar is SIGHTBREAK's actual production `backend/app.py` market_buy,
replay, credit, authenticated and loadout transfer logic at this base, its four
production migrations, and `scripts/test_native_economy.py` /
`game/tests/native_economy_test.gd`. These files were read before registration.
The existing native test runs real EconomyUI/API over HTTP into PostgreSQL and
checks purchase, seller proceeds, ownership and direct receipt replay. It does
not interrupt an unanswered native purchase and recover its original journal
through fresh authentication and repeated process restart.

The accepted B-21 runtime is the other inspected reference: actual native
EconomyUI/API/journal recover 12/12 local SQLite-fixture crash cases versus 0/12
on the old client; independent review `73685c7`. That proves the client fixture
boundary. It does not establish production PostgreSQL settlement. No new
production defect is presumed, no backend repair is proposed, and a source/pure
pass cannot close this gap.

The new harness must reuse production backend routes and native EconomyUI/API
with real HTTP. Its proxy may withhold or drop an actual backend response; it
must never invent a successful transaction, item, balance or authentication.
The client calls actual `/auth/login` in each fresh process. Calling UI methods
from a native test does not establish rendered player consent or navigation.

## Independently testable components

| Component | Original request | Production SQL invariant | Order |
| --- | --- | --- | --- |
| Market | `/market/{listing}/buy`, exact UUID key and integer expected_price 400 | One original operation; buyer debit 400; seller credit 388; fee 12; one sold listing and item transfer; seller loadout removed | First implementation and runtime qualification |
| Store | `/store/buy`, exact UUID key and definition_id key | One original operation, one 150-credit debit and one minted key | Separate later component; not qualified by market |
| Case | `/cases/open`, exact UUID key and original case/key instance IDs | One original operation, both inputs consumed once, one original random finish/roll/table response, no wallet debit | Separate later component; not qualified by market |

These rates come from the unchanged production config. Preserve random case
generation; never patch the RNG to make the test deterministic.

## Market fixture and exact gates

Create three disjoint synthetic accounts through production `/auth/register`:
seller, buyer and outsider. Observe all start with zero XP/credits/items. Only
inside this owned test database, trusted fixture setup uses existing production
credit/mint helpers to seed seller 100, buyer 1,000 and one seller rifle skin.
Use the explicit ledger reason `fictional_test_fixture`; outsider stays zero.
Equip the skin and list it for 400 through real API routes. This is synthetic
fixture value, never a claim of earned rewards, and never a product balance grant.

Retain these separate phases without deduplicating equal SQL snapshots:

1. Actual SQL after fixture/listing/equip and before the original native request.
2. Original native process authenticates and dispatches the keyed request through
   the transparent proxy. The production API returns its actual 200. A fresh
   read-only SQL query must see the committed operation, full business effects
   and exact response before the proxy drops any response and before client kill.
3. Kill the still-live original native process before it receives any response
   headers; retain PID/start identity, kill acknowledgment and journal bytes.
4. Fresh native wrong-account and second-owned-origin attempts must retain the
   journal and issue zero keyed mutation requests. Separate production API replay
   with outsider authentication must not return the buyer's receipt or item.
   Before/after business SQL stays unchanged. The second proxy origin forwards
   to the same owned backend, isolating the client origin check from account ID.
5. A fresh correctly authenticated native retry reuses the exact endpoint, method,
   raw request body, parsed payload, UUID key and expected price. Withhold its
   actual production 200 again, retain unchanged SQL, kill this second process,
   and prove the saved journal is byte-identical to the first capture.
6. A third correctly authenticated native process recovers the original response,
   clears the journal and refreshes ownership/balance from actual API reads.
   Retain a distinct SQL query requested after final replay. A second post-clear
   restart has no receipt and sends no purchase. Business SQL remains unchanged.
7. A changed expected price with the original key must receive production 409
   without changing business SQL. No altered or fresh request may replace an
   unresolved receipt. Any failure remains a failure; no deadline extension or
   retry campaign is implied by this registration.

Every successful SQL state must show buyer 600 / seller 488 / outsider 0, unchanged
XP, exactly one buyer -400 `market_purchase` row and seller +388 `market_sale`
row beyond the explicit fixture seed rows, one sold listing for the original
item, unique buyer ownership, no new item, removed seller loadout, one market
settlement audit, no match rewards and no game tickets. Sum of the two purchase
ledger amounts is -12. The service has no separate fee-account ledger; do not
invent one. Original operation ID and request hash must join to the exact native
request and stored response. Every successful native result must equal that
original stored response, including the item identity and fee.

Each SQL witness has a unique phase/query ID, requested/completed monotonic and
wall clocks, actual PostgreSQL clock, cluster/database identity and complete
selected rows. The final query must start after replay; an earlier identical
sample is insufficient. Independent read-only live SQL observation is arranged
before runtime and after final replay. Keep clean fixed source until its
source-after receipt.

## Runtime ownership, privacy and acceptance

Only after root releases the lane: pinned Godot 4.7.2, an owned PostgreSQL 17
container and labelled volume using the already pinned cached digest from
`backend/dev-db.sh`, one production API and two transparent proxies. All published
ports bind 127.0.0.1; random PostgreSQL port must differ from shared 55432. Refuse
arbitrary DATABASE_URL, API URL, container or volume selection. Verify cluster
identity over external TCP and internal container SQL before migrations/fixture
writes. Apply all four unchanged production migrations. No shared dev database,
image pull, production service, paid action or live credential is used.

No bearer token or plaintext account password may appear in the journal, app
state, probe configuration, retained request headers, logs or evidence. Native
bootstrap credentials and proxy-observed session tokens stay in process memory;
scan all owned persistent client/output bytes against those values. Backend
password/session hashes are the unchanged production authentication storage.
The ephemeral fixture database password stays in runtime configuration and is
redacted from retained commands/outputs; removing its owned container/volume is
part of cleanup. Do not read saved credentials or dump process environments.

Record exact source/engine/image hashes, native/process/socket identities,
raw method/path/body only for non-auth transaction requests, original response,
SQL and journal bytes, failures, private user namespaces and resource cleanup.
Delete only exact owned IDs after label/volume checks. Reap process groups,
close proxy/API/DB ports, remove the owned container/volume, and record source
unchanged afterward. A fresh critic must inspect actual native and SQL outputs.
The builder cannot approve its own work.

Root currently owns the engine/aggregate lane. This registration authorizes
source/pure work only. No runtime service, native/OCR/CI action starts before
root's release and source/criteria review. Whole G3/G7/G16, rendered consent,
postmatch UX, other routes, remote hosts and host-power-loss durability remain
open. Protocol 6, prediction opt-in, live rewind off, state privacy, earned-only
authority and offline/online boundaries remain unchanged.
