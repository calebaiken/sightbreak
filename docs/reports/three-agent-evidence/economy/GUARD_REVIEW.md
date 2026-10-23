# Concrete marketplace guard review

Reviewed the uncommitted `backend/app.py` and `backend/tests/test_economy.py` patch in `/workspace/sightbreak-market-guard` based on `11573e587f13dfd832613a0c09dbc615f46d3461`. No source edits were made.

**Accepted: no security or compatibility blocker found.**

- `backend/app.py:158–159`: marketplace-specific optional price remains inside the existing strict model. A supplied non-null price is a strict integer bounded to the same 1–10,000,000 range used for listing creation. Booleans, strings, floats, nonpositive values, and oversized values reject rather than coerce.
- `backend/app.py:129–133`: receipt canonicalization is changed only for `MarketBuy` with a null/omitted price. Removing that newly introduced default field reproduces the exact old legacy payload hash. All other request model canonicalization is retained. A supplied integer remains part of the fingerprint, preventing changes to an already-committed confirmation under the same receipt.
- `backend/app.py:282–288`: existing transaction serialization is retained; exact replay runs before current listing/state/price checks. The expected price check runs before seller/item mutation or debit and raises 409 on either higher or lower price mismatch.
- `backend/app.py:292–297`: actual fee and debits still use authoritative `Listing.price`. The client cannot set the charged amount.
- Explicit `null` intentionally aliases legacy omission, as tested in `backend/tests/test_economy.py:153–162`. This is a reasonable documented compatibility behavior: omission is already supported and both paths preserve authoritative pricing. It does not let a changed request replay a receipt originally committed with a supplied integer.
- The mismatch cases inspect both wallets, item ownership/reservation, listing state, ledger count, and receipt count. They also prove that a rejected mismatch does not consume the receipt. Concurrent identical guarded receipt execution, post-sale/post-reprice replay, changed-payload conflict, and synthetic pre-guard receipt replay are tested.

Independent verification on dedicated `sightbreak_economy_review_20261016_test`: **15 marketplace tests passed**, 46 unrelated tests deselected. Log: `guard-market-tests.log`. The only warning was the existing Starlette/httpx deprecation warning.

Integration condition: send the captured displayed price from the native marketplace confirmation. The backend patch is suitable to integrate; the UI wiring and the primary agent's full-suite checks remain separate verification.
