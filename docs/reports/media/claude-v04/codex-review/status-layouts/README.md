# Status line under saved touch layouts

Codex's review of `98ff57c` reported this regression: with a saved layout, the status line alternated every frame between a 346 × 30 px line and a 6 px column. The response is in `docs/audits/CODEX_REVIEW_RESPONSE.md`.

All captures are Godot 4.7.2 on Xvfb with Mesa llvmpipe, from offline matches with touch controls shown. The match simulation is frozen while frames are captured, so no match event replaces the text; the HUD still updates every frame. `sha256.txt` hashes every file.

| File | What it shows |
| --- | --- |
| `before-after.png` | Half-scale sheet. Top row: `98ff57c` at 960 × 720, 130 % text, FRAG and SMOKE saved at 0.459 and 0.541 of the width. Frame 0 is a 346 × 30 line under FRAG and SMOKE; frame 1 is a 6 px column of 23 lines that pushes the bottom HUD off screen. The other four tiles show the fix, from top left to bottom right: the same layout (two lines left of FRAG, identical in frames 0–3); the longest notification there (no clear stretch in the row, so it rises above the controls in three lines); 150 % buttons with a five-button wall across the bottom; 1024 × 768 at 115 % with USE at the centre |
| `frames/98ff57c-*.png` | Full frames from `98ff57c`: buy-prompt frames 0 and 1, and the long notification in its 6 × 2,637 px state |
| `frames/fixed-*.png` | Full frames from the fix: buy-prompt frames 0 and 3 (identical), the long notification, the 150 % wall, 1024 × 768, and the default layout at 130 % |
| `logs/frames-98ff57c.log`, `logs/frames-fixed.log` | For every captured frame: the label's rectangle, its line count, how it was placed (`row`, `risen` or `overlap`), and the health and ammunition rectangles. `logs/status_frames.gd.txt` is the capture script |
| `logs/landscape-test-on-98ff57c-main.log` | Negative control: the new `landscape_ui_test.gd` on `98ff57c`'s `main.gd`, headless, 700 failures of 9,217 checks (stack traces removed) |
| `logs/landscape-headless-fixed.log` | The same test on the fix, headless: 9,217 checks, 0 failures |
| `logs/landscape-native-fixed.log`, `logs/hud-overflow-native-fixed.log` | Native runs on the fix (Xvfb, GL Compatibility). The landscape run uses `--status-quick` (the matrix at 130 % text on 960 × 720 and 1024 × 768); the full matrix renders too slowly in software for a native run. `NO GRAB` lines are X11 pointer-grab errors from a second window on the same display, not test failures |
| `logs/validate-fixed.log` | `validate.sh` on the fix, exit 0 |

## What the frame logs show

| Case | `98ff57c` | Fix |
| --- | --- | --- |
| Saved centre gap, 130 %, buy | Alternates 346 × 30 (1 line) and 6 × 756 (23 lines); health at y = 1,007 on a 720 px screen | 189 × 63, 2 lines, every frame; health at y = 649 |
| Saved centre gap, 130 %, longest notification | Alternates 916 × 63 and 6 × 2,637 (80 lines) | 339 × 96, 3 lines, risen to y = 458, every frame |
| Default layout, 130 %, buy, 960 × 720 | 345 × 30, stable | 341 × 30, stable |
| 150 % buttons, bottom wall, 1280 × 720, longest notification | 312 × 129, 4 lines, over the drawn move-stick ring | 486 × 63, 2 lines, risen above the wall |
| 1024 × 768, 115 %, USE at the centre, defuse | 350 × 26, 1 line, clear (this case passed on `98ff57c` as well) | 184 × 55, 2 lines, left of USE. The single line no longer fits beside the funds label, which the fitter now also keeps clear |
