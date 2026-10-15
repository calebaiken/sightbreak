# Main menu, hardened (increment 2)

Native Godot 4.7.2 captures on Xvfb with Mesa llvmpipe (software rendering, not phone captures), at the real tested dimensions (each PNG's size matches its name). The profile in the captures is a fixture with real stored fields (level 3, 1,340 XP, 2,750 training credits, 9 matches, 5 wins, 61 eliminations, 44 deaths). `sha256.txt` hashes every file.

## What changed since the checkpoint (`5c0f791`)

The checkpoint fitted the menu into 886 × 630 px of an 888 × 648 px region at 960 × 720 and 130 % text: 2 px of slack. It passed its tests, but any wider glyph would have broken it. The cause was the **"SIGHTBREAK" wordmark**: 88 px display type (68 px × the accessibility scale) measured 546 px and alone set the left column's width.

| Before | Now |
| --- | --- |
| The wordmark scaled with the text-size setting | The wordmark is a headline, not body text: fixed at 68 px and fitted to its column by `SBDesign.fit_font_size()`, measured with the real face |
| Columns always side by side | The columns are measured in the real theme and fonts, then placed side by side only if they fit with 32 px (`MENU_SAFETY`) of slack, and **stacked** otherwise |
| A fixed minimum column width | Natural widths measured at runtime; each entry keeps its natural width as a floor and can truncate only beyond that |
| Content taller than the screen left it | A vertical scroller (never horizontal); a **compact variant** (no tagline, tighter spacing) when the full variant is taller than the room |
| Names could widen the layout | User-supplied names truncate with an ellipsis and never widen anything |
| Slack: 2 px | Slack: 150 px at 960 × 720 and 130 %, and more at larger sizes (`logs/layout-table.txt`) |

## Training record (only what is stored)

Level, XP **to the next level** from the profile's own rule (`Profile.xp_for_level`, the inverse of `level_for_xp`, so there is one definition of the curve), a progress bar, training credits, matches, wins, eliminations and deaths from the offline profile. The online identity and earned Credits appear **only while signed in, on their own lines**; training credits and earned Credits are never combined or shown together as one number.

## Evidence

| File | What it shows |
| --- | --- |
| `menu-<size>-100.png`, `menu-<size>-130.png` | 960 × 720, 1024 × 768, 1280 × 720, 1560 × 720 and 1600 × 720 at 100 % and 130 % text (the dimension is in each name) |
| `menu-1280x720-85-account.png` | 85 % text, signed in |
| `menu-960x720-130-account-cjk-cjkname.png` | Signed in, a 32-character CJK profile name and online name, at 130 % text, with Noto Sans CJK as the fallback face. Names truncate with an ellipsis; the policy line stays whole |
| `menu-960x720-130-pseudo.png` | A pseudo-translation (every menu string about 60 % longer) at 130 %: the layout stacks, goes compact and scrolls. The repeated fragments (such as "DEPLOY · O") are the stand-in strings' truncated copies, not clipped text |
| `sheet-key-states.png` | A half-scale sheet of the four above |
| `logs/ux-contract-default-fonts.log`, `logs/ux-contract-noto-cjk.log` | `ux_contract_test.gd`, 2,227 checks, 0 failures, with the host's default fonts and with Noto Sans CJK as the fallback face (a taller face than the default, which broke PR #1's kill feed earlier) |
| `logs/layout-table.txt` | The layout chosen for each of 200 cases: side by side or stacked, compact or not, whether it scrolls, and the slack |
| `logs/negctl-*.log` | Negative controls, below |
| `logs/validate-fixed.log` | `validate.sh`, exit 0 |
| `logs/menu_capture.gd.txt`, `logs/native-capture.log` | The capture script and its output |

## What the tests cover (`ux_contract_test.gd`, 36 → 2,227 checks)

For **5 sizes** (960 × 720, 1024 × 768, 1280 × 720, 1560 × 720, 1600 × 720) × **4 text scales** (85, 100, 115, 130 %) × **2 account states** (none, signed in) × **4 names** (short, 32 ASCII characters, 32 CJK characters, accents with combining marks) plus a **pseudo-translation** each:
- no control leaves the screen, and there is no horizontal scrolling;
- the columns do not overlap, and side-by-side columns keep 32 px of slack;
- **no text is truncated or collapsed** unless it is a user-supplied name (the check measures the text against its box with the real face);
- all eight actions exist, are at least 48 px, and can be scrolled into view;
- the card's XP-to-next-level comes from the profile's own rule, and the online identity shows only while signed in.

Separately: the level curve round-trips for levels 1–11; and **every menu action opens its intended screen** (LAN → connect, Operator Record → progress, Settings → settings, Inventory, Cases, Market and Trades → the armory on that tab, Deploy → an offline match, and leaving it returns to the menu).

## Negative controls

| Control | Result |
| --- | --- |
| Never stack or compact (`negctl-never-stack.log`) | 6 failures: side-by-side slack below 32 px, and controls off the screen, in the pseudo-translation cases |
| No scrolling (`negctl-no-scrolling.log`) | 4 failures: content leaves the screen in the cases that need the scroller |
| The two defects found in the first native captures, restored (`negctl-truncation-and-collapse.log`) | 160 failures. **The first draft of the test passed while "OPERATOR RECORD" was truncated and the "DEVELOPMENT BUILD" label had collapsed to 1 px.** Its checks were about rectangles, not about text fitting in them; the text-fits check was added after the screenshots exposed both |

## Honest limits

- The adaptive paths are rare in practice: 4 of 200 cases (the pseudo-translation at 130 % on 960 × 720 and 1024 × 768) stack, go compact and scroll; every real-string case is side by side with at least 150 px of slack. There is no translation system yet; `menu_labels` is the string table a translation would replace, and the pseudo-translation is a stand-in, not a real language.
- Screens beyond the menu (settings, connect, record) still use their earlier layouts.
- All captures are software-rendered desktop frames. Physical phone layout, safe-area cutouts and touch feel are UNVERIFIED.
