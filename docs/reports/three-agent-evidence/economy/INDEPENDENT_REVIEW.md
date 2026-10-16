# Economy review — frozen UI and backend

Reviewed UI `7e41de635a92763bd608203faf2c4689255bf727` and backend `11573e587f13dfd832613a0c09dbc615f46d3461`. Application source was read with `git show` and a frozen backend archive was extracted only under this review directory. No repository source edits or GitHub posts were made.

## Actionable consent gap

The native marketplace confirmation states an exact price, but its accepted action sends only `idempotency_key` (`game/scripts/ui/economy_ui.gd:1291`, UI hash above). Backend `market_buy` accepts only `Idempotent` (`backend/app.py:274`), retrieves the listing after idempotency replay (`:277–280`), and charges `listing.price` (`:284–285`) without comparing the price displayed to the buyer.

A controlled authoritative DB price change demonstrates the gap: list and display 400, change that listing's DB price to 900, then send the frozen UI-equivalent purchase payload. The server succeeds, debits 900, credits the seller 873, and keeps a fee of 27. A client preflight fetch would still leave a read/commit race; the comparison belongs inside the existing purchase transaction before any value changes.

This is a confirmation-consistency issue, not a demonstrated seller-controlled repricing exploit. There is no current API endpoint to change an existing listing's price. Supported cancellation and relisting creates a new UUID (`backend/models.py:64`; `backend/app.py:258–259`) and a stale purchase of the cancelled UUID rejects (`backend/app.py:280`). That path passed an explicit probe without any balance, ownership, reservation, ledger, or receipt changes.

## Narrow guard and compatibility recommendation

1. Native confirmation should capture and send the same integer price shown in its sheet as `expected_price`.
2. Use a marketplace-specific request model. When supplied, require a strict positive bounded integer and reject invalid values; do not relax `Strict` extra-field validation generally (`backend/app.py:139`).
3. After exact receipt replay and active-listing validation, compare the supplied expected price with authoritative `Listing.price`. On mismatch return 409, request refresh/reconfirmation, and perform no value, ownership, reservation, receipt, or audit mutation. Always debit the database price; never substitute the client value.
4. For narrow compatibility, a truly omitted `expected_price` may retain the legacy API behavior. This preserves existing native and fixture callers while updated UI requests gain the check. Distinguish omission from invalid supplied values; explicit null need not be accepted as a legacy request.
5. Preserve the original receipt fingerprint for omitted-price requests. Current `replay` hashes `body.model_dump(mode='json')` (`backend/app.py:127–133`). A naive optional field adds `expected_price: null` to that dump and makes receipts written before deployment reject as changed requests. The review probe verifies this hash incompatibility. Narrowly omit the absent price from canonicalization; include a supplied price so key reuse with a changed confirmation price still rejects.
6. Keep replay ahead of current-price/state checks. A committed exact retry must return its original response after the listing is sold or the current price changes. A mismatch rejected before commit should create no receipt, permitting a deliberate fresh confirmation later.

Suggested new Postgres cases: stale expected price above and below the authoritative price, correct price charges server fee and balances exactly once, changed expected price with an already-used receipt conflicts, exact receipt replays despite later price/state change, omitted legacy price succeeds and replays a receipt stored using the old request hash, invalid supplied prices reject, and mismatches leave wallets/item/listing/reservation/ledger/receipt/loadout unchanged. Add a native test through the real marketplace confirmation button to assert the sheet price equals transmitted `expected_price`; frozen native economy coverage currently bypasses that button (`game/tests/native_economy_test.gd:44`).

## Validation and unaffected guarantees

Dedicated disposable PostgreSQL database: `sightbreak_economy_review_20261016_test`, loopback port 55432. No shared development database reset was performed.

- Frozen backend suite: **51 passed**, recorded in `frozen-backend-tests.log`.
- Additional review probes: **8 passed**, recorded in `frozen-consent-probes.log`; source is `test_frozen_consent_probes.py`.
- A legacy purchase receipt replay after sold state and a subsequent DB price change returned the same original response, with one receipt and one purchase/sale ledger pair.
- Two simultaneous requests using the same receipt both returned the same successful result, with one debit and one item transfer.
- Insufficient funds rejected with unchanged buyer/seller balances, item owner/reservation, listing state, ledger count, and receipt count.
- Concurrent two-sided trade confirmation settled once, cleared both reservations, swapped ownership, and preserved both wallets. Existing revision invalidation tests also passed (`backend/tests/test_economy.py:117–131`).

No additional actionable balance or trade defect was found in this focused review. The test environment emitted a pre-existing Starlette/httpx deprecation warning; all assertions passed.
