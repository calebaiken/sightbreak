# Visual and UI gap review (2026-10-14)

A review of what the game shows today, from native captures. It sets the order of work for the UI branch (`claude/native-ui-production-v1`) and the art branch (PR #2). It is my own review (the same model family as the author), so **it is not acceptance**. Codex's independent findings are cited where they agree.

## Method

- **Shell and match screens:** native Godot 4.7.2 captures on Xvfb with Mesa llvmpipe, at 1280 × 720 and 960 × 720, from PR #1's head with the status-line fix. The capture script is `gap-review/captures/ui_tour.gd.txt`. Every screen in the main shell was captured:
  - menu, local network, settings and operator record;
  - the combat HUD in the buy and live phases;
  - requisition, scoreboard, field menu and touch editor.
- **Armory:** `game/tests/economy_ui_test.gd` with `ECONOMY_CAPTURE_DIR`. It renders inventory, cases, market, trades, profile, the inspector and the case reveal from a fictional render fixture; no backend runs.
- **First-person weapon:** PR #2's evidence (`docs/reports/media/art-v4/`).
- **Out of scope:** phones. Every frame is software-rendered.

Half-scale contact sheets are in `gap-review/`:

| Sheet | Screens |
| --- | --- |
| `sheet-shell.png` | Menu, local network, settings and operator record at 1280 × 720 |
| `sheet-match.png` | HUD in the buy and live phases, requisition, scoreboard, field menu and touch editor at 1280 × 720 |
| `sheet-960.png` | Menu, requisition, settings and scoreboard at 960 × 720 |
| `sheet-economy.png` | Inventory, cases, market, trades, profile and the inspector |
| `sheet-cases.png` | The case reveal from carousel to result, the inspector with a fictional Legendary finish, and the reference knife |

## What works

- **Consistent tokens:** one palette (obsidian, graphite, crimson, muted gold, steel) and one type scale across shell, HUD and armory (`design_tokens.gd`).
- **Honest copy:** the economy states separate match funds, offline training credits and earned online Credits. Case odds are published before opening. The reveal says the reward is committed before it plays, and skipping does not change it.
- **HUD:** it holds its layout across sizes, text scales and saved touch layouts (PR #1 tests).
- **Trades:** "YOU GIVE" and "YOU RECEIVE" are listed per side.

## Prioritised backlog

P0 blocks a credible visual milestone, P1 is high impact, P2 is polish. "Branch" says where the work belongs.

| # | Priority | Area | Gap seen in the captures | Branch |
| --- | --- | --- | --- | --- |
| 1 | P0 | First-person weapon | <ul><li>The bore's vanishing point is about 125 px left of the crosshair, so the rifle reads as held across the body.</li><li>The grip hand reads as a mitten and the sleeves as a uniform tube.</li><li>Shade contrast is weak.</li></ul> Codex scored the slice 5.5/10 (A6) | PR #2 |
| 2 | P0 | Requisition (buy) | <ul><li>Affordable, unaffordable and equipped cards look alike: text is low-contrast steel on a near-transparent card, and disabled cards only dim.</li><li>No weapon silhouettes.</li><li>The price is mixed into a sentence ("1100 · NEED 300 MORE").</li><li>The HUD shows faintly through the scrim behind the cards.</li></ul> | UI |
| 3 | P0 | Armory inventory | <ul><li>Item cards are three lines of text: no thumbnail, rarity colour, wear bar or equipped state.</li><li>The inspector opens as a popup over the list, not beside it.</li><li>Tabs are plain buttons, with REFRESH styled like a tab.</li></ul> | UI |
| 4 | P0 | Status text | <ul><li>The gold status text has no shadow or outline, so it is hard to read where it crosses the light sidearm.</li><li>At 130 % text, the ammunition label's box reaches 1.8 px into SWAP's bounding square at 1280 × 720.</li></ul> | UI |
| 5 | P1 | Cases | <ul><li>The odds are one line of text, not a table with rarity colours.</li><li>The case is a text button ("OPEN / Obsidian case") with no case art until the reveal.</li><li>The reveal reads well, but the popup covers half the armory with the profile visible behind it.</li></ul> | UI |
| 6 | P1 | Market and trades | <ul><li>Form-first layout: listings are text rows with no thumbnail, and the fee appears only as a sentence.</li><li>Trades show the right content but no item visuals, and the counterparty shows as "Unknown player" when the name is not known.</li></ul> | UI (no backend change) |
| 7 | P1 | Main menu | <ul><li>A generic wordmark (the engine's bundled font, emboldened).</li><li>The economy entries are a row of micro-type buttons.</li><li>There is no summary of level, XP and Credits from data that exists: the offline training record, plus the online account when signed in.</li><li>The background is the untextured block yard seen from above.</li></ul> | UI; the yard is item 9 |
| 8 | P1 | Operator record and profile | <ul><li>Plain text lines.</li><li>An empty state with no call to action.</li><li>Only statistics that exist may be shown (matches, wins, eliminations, deaths from the offline record; XP, level and Credits from the account). No invented career statistics.</li></ul> | UI |
| 9 | P1 | Relay Yard | Block geometry with flat materials. Signage is text only. No trims, decals, wear or modular detail. This is the menu background as well | Environment slice (Phase 6) |
| 10 | P1 | Effects | The muzzle flash is a flat star and casings are boxes (Codex A6) | PR #2 |
| 11 | P2 | Scoreboard | <ul><li>Readable, but plain: no row banding.</li><li>The local player's row is gold only.</li><li>The column header is detached from the values.</li></ul> | UI |
| 12 | P2 | Settings | <ul><li>Raw sensitivity values (0.0028).</li><li>One long list, where sections such as controls, display, audio and accessibility could be grouped or tabbed.</li></ul> | UI |
| 13 | P2 | Field menu and touch editor | Functional; the touch editor's instructions are drawn over the 3D scene with no backing | UI |

## Rules the UI work keeps

- **Funds:** match funds, offline training credits and earned online Credits stay separate on screen and in code.
- **Cases:**
  - The server commits the reward; the client presents it.
  - Odds stay visible before opening.
  - No near-miss reel, no reel that implies a different outcome, and no slowdown on rare items.
- **Market and trades:** each side shows exactly what it gives and receives. No backend transaction change.
- **No invented data:** no persistent statistics or progression the backend does not store.
- **Buttons:** every one works; no placeholder actions.
- **Field of view:** the competitive aspect and field of view stay ("keep" stretch) unless the owner approves a change (Codex's `MOBILE_ASPECT_REVIEW.md`).
- **Platforms:** touch targets stay at least 48 px, safe areas are respected, and text scales from 85 to 130 %.
