# Marketplace confirmation price guard

Development correction based on integration PR11 `11573e587f13dfd832613a0c09dbc615f46d3461`.

The native confirmation quotes a listing price, but legacy buyers send only a receipt ID. A controlled database reprice from 400 to 900 caused that legacy request to debit 900. Current seller APIs cannot edit an existing listing's price: cancel/relist creates a new UUID. This is a consent-consistency guard, not evidence of a seller-controlled repricing exploit.

`POST /market/{listing_id}/buy` accepts optional `expected_price`, a strict integer in 1–10,000,000. Under the existing serialized economy transaction, exact receipt replay happens first, then the server compares the supplied price with the active listing. Mismatch returns 409 before writes. Successful settlement still uses the authoritative listing price. Legacy omitted/null prices retain the previous receipt fingerprint; other routes' fingerprints do not change. Clients should supply the displayed confirmation price and retain the entire request on an unknown-outcome retry.

Independent read-only review found no blocker in comparison ordering, authorization, atomicity or canonicalization. 61 isolated PostgreSQL tests pass, including strict input, both mismatch directions, unchanged ownership/reservation/wallet/ledger/receipt state, concurrent identical guarded purchase, exact replay after sale/reprice, changed-price receipt rejection, and a pre-guard receipt fingerprint. Existing economy tests and negative controls remain present. No real-money functionality or public service deployment is introduced.
