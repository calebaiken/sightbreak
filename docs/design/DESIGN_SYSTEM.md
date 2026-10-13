# SIGHTBREAK visual design system

Source of truth: [`game/scripts/ui/design_tokens.gd`](../../game/scripts/ui/design_tokens.gd) (`SBDesign`). Screens must take color, type, spacing, motion and component states from it rather than defining local values. This document explains the intent; the script is authoritative.

## Identity

A restrained tactical shooter, not a mobile storefront. Obsidian and graphite surfaces carry brushed-steel text; muted metallic gold marks emphasis and selection; dark crimson is reserved for the primary action and for danger. Geometry is precise: 3 px radii, hairline borders, wide-tracked semibold headings. Decoration never competes with the play space.

| Token | Value | Use |
| --- | --- | --- |
| `OBSIDIAN` | `#0a0d12` | App background, inset fields |
| `GRAPHITE` / `GRAPHITE_RAISED` / `GRAPHITE_HOVER` | `#141920` / `#1b222b` / `#232c37` | Panels, buttons, hover |
| `LINE` / `LINE_STRONG` | `#2c3540` / `#46525f` | Borders, dividers |
| `STEEL` / `STEEL_BRIGHT` / `TEXT` | `#8e99a6` / `#c3ccd6` / `#e9ecf0` | Secondary text, meters, primary text |
| `GOLD` / `GOLD_DIM` | `#c8ab6e` / `#8c7647` | Headings, selection, focus, positive emphasis |
| `CRIMSON` / `CRIMSON_BRIGHT` | `#a32539` / `#d64a5f` | Primary action, critical health, urgent timers, errors |
| `ATTACK` / `DEFEND` | `#c98a52` / `#58a8b8` | Squad identity; matches operator shoulder accents in the world |

Rarity colors stay in `CosmeticMaterial.RARITIES` (one source for inspection, cards and reveal lighting).

**Color is never the only signal.** Squads are also labelled ("YOU · ATTACK"), alive state uses filled vs outlined pips, lethal and headshot hit markers differ in luminance as well as hue, depleted utility shows "0" and dims, and disabled buttons change text and contrast.

## Typography

Godot's bundled font only (no external font files or licenses). Headings use `heading_font()`: the same face with emboldening and +1 px tracking.

| Token | Size | Use |
| --- | ---: | --- |
| `TYPE_DISPLAY` | 68 | Title, match outcome |
| `TYPE_H1` | 32 | Screen titles, score |
| `TYPE_H2` | 24 | Section totals, funds |
| `TYPE_H3` | 19 | Card titles |
| `TYPE_BODY` | 16 | Body copy, settings |
| `TYPE_SMALL` | 14 | Help text, feed names |
| `TYPE_MICRO` | 12 | Kickers, squad marker, touch glyph labels |

Settings → Accessibility → Interface text size scales body copy and `main.gd` labels by 90/100/115/130 %. Layout tests run at 100 %.

## Spacing, targets and motion

- Spacing scale: 4 · 8 · 12 · 18 · 28 px (`SPACE_XS`…`SPACE_XL`).
- Every tappable control is at least `TOUCH_MIN` = 48 px tall (enforced by `ux_contract_test.gd` on the menu, settings, connect and record screens).
- Motion: 0.12 / 0.2 / 0.35 s. `motion(seconds, reduced)` returns 0 when Reduced Motion is on. No looping UI animation; the only pulse is the planted/dropped device marker on the radar.

## Components

| Component | States | Notes |
| --- | --- | --- |
| Button — `primary` | normal, hover, pressed, focus, disabled | Crimson fill with a 3 px lower edge. One per screen (DEPLOY, RESUME, JOIN GUEST LAN MATCH, SAVE TOUCH LAYOUT, RETURN). |
| Button — `secondary` | same | Default theme button. |
| Button — `ghost` | same | Transparent fill: BACK, LEAVE, REFRESH, BACK TO FIELD. |
| Tab | normal, selected | Selected = raised surface, gold underline and gold text (`tab_selected_style`). The armory always shows which section is open. |
| Panel / card / inset / overlay | — | `panel(variant)`. Overlays use `SCRIM` behind an overlay panel. |
| Section header | — | Gold micro-heading + full-width hairline (`main.gd` `section()`). |
| Meter | — | `ProgressBar` with obsidian track; gold fill (objective), steel fill turning crimson at ≤ 25 health. |

## Combat HUD layout (landscape)

```
┌ radar ┐            ■■■■■  07 : 05  ■■■■■             device state   [II]
│ (N-up)│          ROUND 08 · LIVE · 01:12              kill feed (≤4)
└───────┘               YOU · ATTACK
 [TEAM] [BUY]                                    (touch actions, right thumb)
                    status / objective prompt
                       ▬▬▬ objective bar ▬▬▬
 100 · HEALTH                                            RIFLE   27 / 90
 ▬▬▬▬▬▬ health bar                         FRAG ×1   SMOKE ×1   FUNDS 3400
```

- Score stays at the optical center; equal-width squad pips flank it (attack fills toward the score from the left, defense from the right).
- The radar shows geometry, sites, self and living teammates only. **It never shows opponents**, even though clients receive their positions (audit M-4); `ux_contract_test.gd` enforces this.
- The kill feed uses plain `Label`s (display names are user supplied, never rich text), keeps four rows and fades after 5 s. Rows involving the local player get a gold outline.
- The reticle gap follows the actual authoritative spread cone (`SBActor.current_spread`), so it opens while moving or airborne.
- Default touch positions keep TEAM/BUY below the radar. Saved custom layouts are never rewritten.

## Transactions

Confirmation dialogs state the exact terms at the moment of commitment:

- **Trades:** partner display name and ID prefix, revision, *you give* and *you receive* with name, rarity, wear and pattern, and an explicit gift warning when you receive nothing.
- **Market purchases:** price, exact instance (rarity, collection, wear, pattern) and the seller fee note.
- **Case openings:** the published probabilities, the case consumed and "results are final". The reveal shows only the server-committed item; skipping changes nothing.

No countdown pressure, scarcity badges, or emphasis on rare outcomes appears in any purchase or opening flow. All currency remains earned in play.

## Visual consistency checklist

Use for every new or changed screen. Each item is checkable in a native capture or a test.

- [ ] Colors come from `SBDesign`; no new hex values in screen code.
- [ ] One primary (crimson) action per screen; destructive or exit actions are ghost buttons.
- [ ] Every control ≥ 48 px tall; touch targets clear safe areas at 960×720, 1280×720, 1560×720 and 1600×720 (`landscape_ui_test.gd`).
- [ ] Headings use `heading_font()`; body copy respects the interface text size setting.
- [ ] Color is paired with text, shape or luminance for every state.
- [ ] Selection is visible (tabs, toggles, focused controls).
- [ ] Disabled states explain why (e.g., "NEED 900 MORE", "PREPARATION ONLY").
- [ ] User-supplied strings render in plain `Label`s, truncated, never as rich text.
- [ ] No HUD element covers the reticle region or the central 40 % of the play view.
- [ ] Opponent information appears only when the player could see it in the world.
- [ ] Transactions state exact items, price and finality before confirmation; no manipulative urgency.
- [ ] Reduced Motion removes or shortens every non-essential animation.
- [ ] Before/after native captures are taken with identical cameras and recorded with provenance.
