# Status text against touch controls at larger text sizes

Codex's recheck of `227d6c8` reported this defect; the response is in `docs/audits/CODEX_REVIEW_RESPONSE.md`. The native captures are Godot 4.7.2 on Xvfb with Mesa llvmpipe, offline matches with touch controls shown. `sha256.txt` hashes every file.

| File | What it shows |
| --- | --- |
| `960x720-130-buy-before-after.png` | The bottom of the HUD at 130 % text, buy phase. Top: `227d6c8`, where the prompt runs under FRAG and SMOKE. Bottom: the fix, where it ends left of FRAG |
| `1280x720-130-notification-before-after.png` | The same at 1280 × 720 with a real round-end notification |
| `960x720-130-buy-227d6c8.png`, `960x720-130-buy-fixed.png` | The full frames |
| `logs/probe-227d6c8.log`, `logs/probe-fixed.log` | Text block against FRAG and SMOKE at 130, 115 and 100 %, four sizes, buy and objective prompts: 15 overlaps before, 0 after (`logs/status_touch_probe.gd.txt` is the probe) |
| `logs/landscape-test-on-227d6c8-main.log` | Negative control: the new landscape checks on `227d6c8`'s `main.gd`, 34 failures |
| `logs/validate-fixed.log` | `validate.sh` on the fix, exit 0 |
