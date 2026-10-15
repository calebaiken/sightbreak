# Armory increment 3: states, money terms, trade sides, collections

Native Godot 4.7.2 screenshots (Xvfb, Mesa llvmpipe, GL Compatibility) taken by `game/tests/armory_ui_test.gd` at 1280 x 720, plus the layout sweep at 960 x 720 with 130 % text and 1600 x 720. They show real screens built from explicit local fixtures; no real account, server or Credits are involved. They are desktop software-rendered frames, not phone captures.

Backend contracts are unchanged: the same endpoints, payloads, idempotency keys and confirmation flow. Rewards remain committed by the server before any reveal. Nothing here generates a reward, a price or a balance on the client; every number shown is computed from the catalog, inventory, listing or trade the server sent.

## What changed

| Screen | Before | Now |
| --- | --- | --- |
| Header line | `ONLINE • <name> • LEVEL n • <credits>`; with no account loaded it read `ONLINE •   • LEVEL 1 • 0 EARNED CREDITS`, a name and balance nobody had sent | `ONLINE • ACCOUNT NOT LOADED` until the server answers; the name is flattened to one line; balances use thousands separators |
| Inventory | Generic grey squares for cases and keys; blank screen when empty | Case and key glyphs; an empty-state card whose action (BROWSE CASES) opens the cases screen |
| Loading / error | Silent; a failed refresh left whatever was on screen | `State_loading` (no action, never mistaken for empty) and `State_error` (the server's actual failure, "nothing on this screen was changed", TRY AGAIN) |
| Cases | Supplies as text rows | Supply rows with case/key glyphs, exact shortfall (`NEED 50 MORE`), `Holds N finishes` from the catalog, your cases with OPEN, a collection browser (finishes grouped by collection, ordered by rarity, each opening the 3D inspector) |
| Market | Sell form first, listings as text below the first screen | Filters and listing cards first; the sell form follows, in one row |
| Listing card | Name and price | Finish swatch, rarity and wear chips, price in earned Credits, exactly what the seller receives after the fee, `BUY FOR n` / `NEED n MORE`, `YOUR LISTING` with CANCEL, INSPECT |
| Buy / list confirmation | Price only | Price, item, rarity, wear, pattern, what you pay, what the seller receives, the fee, your balance |
| Trades | A line of text per side | `YOU GIVE` and `YOU RECEIVE` columns with each item inspectable, a `YOU RECEIVE NOTHING FOR THIS OFFER` warning on one-sided offers, per-side confirmation chips |

## Files

| File | Shows |
| --- | --- |
| `inventory-selected.png`, `inventory-inspector.png` | Cards with rarity, wear, RESERVED / EQUIPPED chips, case and key glyphs; the selected instance's inspector |
| `inventory-empty.png`, `inventory-loading.png`, `inventory-error.png` | The three states. The error is a real failed connection (a closed local port), not a staged string |
| `cases-collections.png`, `cases-collection-browser.png` | Published odds, supplies with glyphs and contents, the collection browser |
| `market-listings.png`, `market-sell-form.png`, `market-empty.png` | Listing cards with price, fee and receipt; the sell form; the empty market |
| `trades-give-receive.png`, `trades-swap.png` | A gift trade with its warning; a two-sided swap with the editor |
| `layout-<tab>-960x720-130.png`, `layout-<tab>-1600x720-100.png` | Every tab at the tightest and the widest supported size |
| `logs/armory-ui-native.log` | The native run that produced the frames |
| `logs/validate-increment-3.log` | `validate.sh` on the final code |
| `logs/negative-control-armory-ui.log` | The same test against deliberately broken screens |
| `sha256.txt` | Hashes of every file here |

## Tests

`armory_ui_test.gd` is registered in `scripts/validate.sh`. It has 2,292 checks headless (2,312 with the 20 screenshot saves) and covers:
- credits formatting and the fee: the displayed fee equals `price x basis points // 10000` (the rule in `backend/app.py`) for 24,000 price/rate pairs, rounding down, and claims no fee when none is published;
- empty, loading and error cards: each exists, its action does something real, loading is not an empty list, a failed refresh against a closed port records the error and releases the screen, a 401 clears the cached account, inventory and selection;
- inventory chips (rarity, wear, RESERVED, EQUIPPED), selection, and that a reserved finish cannot be equipped;
- supplies: exact shortfall, a disabled BUY while unaffordable, the purchase confirmation's price and balance, OPEN enabled only with a key, the real published probabilities in the confirmation;
- the collection browser: grouping, rarity order from deliberately shuffled input, a finish count per collection, inspecting a finish never adds it to the inventory;
- market: price text, seller receipt and fee, `NEED n MORE`, own listing has CANCEL and no BUY, the buy and list confirmations' exact terms, sort and filter change only the view, listings sit above the sell form;
- trades: YOU GIVE / YOU RECEIVE columns, the gift warning only on a one-sided offer, partner names flattened to one line with the ID prefix, the commit dialog repeating the terms, a swap never called a gift, unsaved edits refused with a reason;
- layout: 4 tabs x 5 sizes (960 x 720 to 1600 x 720) x 4 text scales (85-130 %), no horizontal scroll or overflow, no label wider than its card; plus a hostile partner name (80 Greek capitals, Japanese, 60 W) and a very long item name.

**Negative control.** Against the final code with six defects injected (fee off by one, an unaffordable listing left buyable, the gift warning removed, give and receive swapped, the browser unsorted, the error card hidden), the test fails 21 of 2,252 checks (`logs/negative-control-armory-ui.log`); the file was then restored byte for byte.

## Defects found by looking at the screenshots, which the passing tests had not caught

1. The error state's header showed an empty name and a balance of 0 (see the table). Fixed; now tested.
2. The header and the cases screen formatted the balance differently (`1250` against `1,250`). Fixed; one formatter.
3. The trade columns were outlined in the accent colour on all four sides (a single border colour), so YOU RECEIVE looked focused. Now a top accent bar on a neutral outline.
4. On the market, the sell form pushed every listing below the first screen. Listings first now.
5. A fee shown as `(3.0 %)` wrapped between the number and the sign. Now `(3%)`.
6. The first capture of `inventory-empty` was taken after the action had navigated away. Captured before.

## Not done here, and open

- **Case reveal and post-open inspection** were not changed in this increment; they are covered by the existing `economy_ui_test.gd` and were not re-reviewed on screen.
- **No paid cases, near-miss effects or client-generated rewards exist**, and none were added.
- **Live-server behaviour** (a real purchase, listing or trade) is exercised by the backend and native-economy suites, not by these fixtures. This increment was not run against a live backend.
- **Phone rendering** of these screens is not measured; physical-device performance is UNVERIFIED.
- Item names that do not fit a card are clipped with an ellipsis (`Crimson Archive / Iri...` in a 260 px inventory card). The inspector shows the full name.

## Errata (added in round 2, after independent review)

Review of `2b2731a` found these statements here wrong or incomplete; the fixes and their evidence are in `../increment-4/README.md`.

- **`logs/validate-increment-3.log` is stale.** It was copied before the final run: it records 2,288 armory checks, while this README says 2,292. The 2,292 figure is from the final run; the log in this folder is not.
- **The header claim "no balance until the server answers" was only true of the armory.** The main menu's record card still printed a blank `ONLINE` and `0 EARNED CREDITS` after a failed `/me`. Fixed in round 2 and tested on the real menu.
- **"Text scales from 85 to 130 %" was not true of the armory's labels**, which set their own font sizes. The layout sweep passed because the labels did not grow. Fixed in round 2; the sweep now runs with genuinely larger text.
- **The wide captures (1600 x 720)** are a hypothetical canvas; the shipped build keeps the 16:9 frame with bars. They were not labelled as such.
- **The fixtures were hand-typed**, with integers where the server sends floats; that hid `1840233.0` and `58.0%` on screen. Round 2 builds them from the backend's own serializers.
- The trades captures show a red "unsaved edits" banner that the test provokes on purpose (it toggles an offer item and presses CONFIRM to prove the refusal); it is not a state a player sees on opening the screen.
