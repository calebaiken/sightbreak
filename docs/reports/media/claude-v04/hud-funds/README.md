# Funds label (`7756e35`)

At the project owner's request, match funds are one gold "800 · FUNDS" label directly above the health readout and bar. They are no longer repeated in the utility row or the buy-phase prompt. These are native Godot 4.7.2 captures (Xvfb/llvmpipe, not a phone) from `game/tests/hud_overflow_test.gd --capture-dir`, with two 24-character names in the feed.

- `before-1280x720.png`: `77e0433`. Funds end the utility row ("FUNDS 800") and lead the buy prompt ("MATCH FUNDS 800 / TAP BUY TO EQUIP").
- `after-1280x720.png`, `after-960x720.png`: `7756e35`.
- `compare-1280x720.png`: the two side by side at half scale.

The label takes no layout height, so the status line and the bottom row keep their positions. `landscape_ui_test.gd` checks that it clears every touch control at every tested size.
