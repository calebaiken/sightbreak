# UI increment 1: requisition, status text, armory cards and odds

Native Godot 4.7.2 captures on Xvfb with Mesa llvmpipe. The `before-*` files are from `148760e`; the others are from this commit. The armory screens come from `economy_ui_test.gd`'s fictional render fixture; no backend runs. `sha256.txt` hashes every file.

| Change | Before | After |
| --- | --- | --- |
| **Requisition** | `before-1280x720-100-requisition.png`: affordable, unaffordable and equipped cards look alike; low-contrast text; price inside a sentence | `1280x720-100-requisition.png`, `960x720-130-requisition.png`. Each card shows:<ul><li>a flat side-profile glyph per weapon class (original shapes, drawn, no assets);</li><li>name and role;</li><li>damage, rate and magazine meters, relative to the best weapon in the match's own table;</li><li>the price;</li><li>a state chip: gold EQUIPPED or OWNED, crimson BUY, the exact shortfall, or PREPARATION ONLY.</li></ul> Match funds only; earned Credits never appear here |
| **Status text** | No shadow; hard to read over the light sidearm (gap review item 4) | `*-hud-notice.png`: `SBDesign.legible()` adds a soft dark outline and a shadow. Neither changes the label's size, so the PR #1 layout tests are unaffected |
| **Armory item cards** | `before-armory-inventory.png`: three lines of text | `armory-inventory.png`. Each card shows:<ul><li>a swatch from the item's collection palette (`CosmeticMaterial.PALETTES`);</li><li>name and collection;</li><li>rarity, EQUIPPED and RESERVED chips;</li><li>for finishes, the instance's wear as a value and a meter;</li><li>a gold border when selected.</li></ul> Nothing is shown that the instance does not carry |
| **Case odds** | `before-armory-cases.png`: one line of text | `armory-cases.png`: a table with each rarity in its colour and a bar **linearly** proportional to its probability, so rare outcomes look exactly as rare as they are |

**Tests:** `ux_contract_test.gd` (32 → 36) checks each requisition card's state chip and tooltip against the real availability. It also checks that every card holds its content and is at least a 48 px touch target. `validate.sh` exit 0 (`validate.log`).

**Still open from the gap review:** the main menu summary, market and trade visuals, the scoreboard, settings grouping, the 130 % SWAP and ammunition box contact, and the operator record.
