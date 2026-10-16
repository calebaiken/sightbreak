# Reduced motion: `calm` refined (art-v10)

Native Godot on llvmpipe, 1280 × 720, `reload_continuity_test.gd`, `reload_visibility_test.gd`, `reload_sequence_test.gd`. **The shipping setting is unchanged: `reduced_variant` defaults to `current`** (the normal reload with the existing reduced-motion scaling of roll, lift and recoil). I am not adopting `calm` or `still` by default; that is the owner's policy decision and nobody who uses reduced motion has looked at either (no comfort claim).

## What the new continuity test found about `calm` and `still`

The v9 `calm` clip kept the support hand on screen by picking the replacement up only 11 cm below the well, in view. That left the hand on screen, and it also meant the replacement magazine **appeared whole in an open hand**: 8,640 px (58 % of it) in its first visible tick for `calm`, 9,542 px for `still` (limit for a magazine that arrives through the edge: 1,500 px). v9's own notes call this "the price of keeping the hand on screen"; `reload_continuity_test.gd` (new this round) turns it into a measurable defect: a magazine that materialises is as abrupt as one that floats. `calm`'s other properties were fine (hand in view with it: 9,097 px; no unsupported ticks).

## The refined `calm` path (`tools/art/arms_build.py`, `_PATH_CALM`)

| | v9 `calm` | v10 `calm` | default clip |
| --- | ---: | ---: | ---: |
| replacement pickup below the well | 11 cm | **28 cm** | 34 cm |
| turn about the forearm at the hip | 10° | 10° | 22° |
| magazine tilt at the hip | −14° | 55° (as the default) | 55° |
| elbow swing | (−0.12, 0, 0.10) | (−0.35, 0, 0.30) (as the default) | same |
| first visible tick, replacement px (`calm` / `still`) | 8,640 / 9,542 | **481 / 417** | 8 |
| hand px at that tick (`calm` / `still`) | 9,097 / 4,437 | see `logs/` | 32,541 |
| unsupported ticks | 0 | 0 | 0 |

How it was found: a scan of the pickup depth with `ARMS_CALM_JSON` against both reduced variants (`logs/calm-scan.txt`): 20 cm → first draw 2,670 px (calm) and 3,984 px (still), both over 1,500; **24 cm → calm's hand has 99 px of contact at one tick (under 150)**; **26 cm → `still` has 104**; **28 cm → every continuity and visibility rule passes for both**. So 28 cm is the shallowest depth that passes everything, which makes `calm` travel 6 cm less than the default and **turn 12° less about the forearm** rather than being an order of magnitude calmer. The roll, lift, recoil and hand-clip scaling that make `calm` calm are the existing ones; I did not change them.

Timing, ammunition and phases are the existing ones (`reload_sequence_test`: 92 checks, unchanged; the reduced variants share the same phase constants). Visibility: 15 of 15 rules for `current`, `calm` and `still`. Continuity: 6 of 6 for the default, `current`, `calm` and `still`. The two reduced variants are now in `scripts/validate.sh` and N36 (the v9 path) is a negative control that fails the calm continuity test.

## What the same-model stills review added (`../review/review.md`)

Looking at the frames rather than the test, the reviewer found that v10 `calm` **loses the hand and the magazine below the frame for about 8 to 11 ticks (0.13 to 0.18 s, ticks 62 to 72) while the support forearm stays in the picture as a plain olive tube**, and judged it visibly worse than v9 `calm` there (v9 kept the hand cupping the magazine at the bottom edge). That is true and it is the price of the fix: the continuity test passes because the forearm is in the frame (the support arm's pixels, forearm included, never fall under 8,600 in `calm`), but the *hand* is not. The default clip has the same stretch by design (the off-screen hip); v9 `calm` had been the one variant that avoided it, at the cost of the replacement appearing whole in the hand. **There is no depth that gives both**: at 20 cm the hand stays in view and the first draw is 2,670 px (18 % of the magazine), which the unrelaxed continuity bound (1,500 px) rejects. I chose the bound over the hand. If the owner prefers a hand that never leaves the frame for the reduced-motion variants, the right route is not a shallower pickup but a short authored "draw from the hand" for the replacement (no pouch), which is not built.

`still` is the closest to continuous: its support arm's lowest count in ticks 50 to 100 is 881 px (6 ticks under 3,000 px, ticks 65 to 70), against 8,621 for `calm` and 7,371 for the default (that is the forearm; the reviewer's reading of the stills is that `still` keeps a palm under the magazine after tick 74 and is the most continuous of the three, while the v9 review had found it awkward-looking; both are same-model readings of stills).

## Proposed policy (not applied)

If the owner wants a comfort-first default: make `calm` the default when the OS or in-game reduced-motion preference is on (`current` is unchanged for everybody else), keep `still` as a manual option, and keep the Settings strings for the three. What I can and cannot say: `calm` keeps every action readable and keeps the hand and magazine in view with it; it moves the hand 6 cm less and turns it 12° less than the default, (the existing scaling of roll, lift and recoil applies on top); I have no evidence it is more comfortable for anyone. A short play session with an actual reduced-motion user is the only test that decides it.

## Trade-offs

- `calm` still dips the hand 28 cm; if the discomfort comes from vertical hand travel, `calm` is only mildly different from the default. A true low-travel variant would need a pouch in view, which is rejected (a floating box).
- The pickup depth was chosen after seeing the scan; the 1,500 px and 150 px bounds belong to the continuity test and were themselves set after seeing the baseline's numbers (disclosed in `../continuity/README.md`), so passing them is a regression guard, not an independent standard.
