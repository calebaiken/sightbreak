# Before/after evidence — `claude/independent-audit-visual-v04`

Unedited viewport captures from the running Godot 4.7.2 application, rendered by **the same maintained scripts** against an immutable `git archive` of `e67f2c8` (before) and the branch (after), one after the other in a single session. Host: 4 vCPU Linux cloud container, Xvfb, Mesa llvmpipe 25.2.8 (software rendering), runs pinned to two CPU cores. These show rendered content and layout. They are **not** photographs of a phone and say nothing about device frame rate, thermals or touch feel.

`compare/` holds half-scale side-by-side sheets of every pair. The only edit is the label strip added above each sheet. `before/` and `after/` hold full-resolution originals for the pairs listed below. `sha256.txt` hashes every file.

| Pair | Script | What to look for |
| --- | --- | --- |
| `smoke-mid`, `smoke-close`, `smoke-inside` | `tests/smoke_visual_capture.gd` (the script was copied into the archive so both sides use it) | A smooth sphere becomes a lobed cloud with a soft rim and edge puffs. The inside view stays an even fog. The far "TRANSFER STATION" header is no longer cut by a column. |
| `combat-07-smoke` | `tests/combat_presentation_capture.gd` | The same fixture cloud behind two operators. |
| `combat-02-rifle-ready`, `combat-06-operator-silhouettes` | same | **Unchanged on purpose.** Operator and weapon art was not reworked, and these pairs show that. |
| `hud-1560x720`, `hud-960x720` | `tests/landscape_ui_test.gd --capture-dir` | Radar (self, teammates, sites; never opponents), squad pips, "YOU · ATTACK", utility counts on the HUD and the FRAG/SMOKE buttons, health bar, TEAM/BUY below the radar, unclipped "FREIGHT" and "TRANSFER" signage. |
| `menu-1280x720`, `settings-1280x720` | same | Shared tokens, primary/ghost buttons, sectioned settings with 3D render scale and interface text size. |
| `armory-trades`, `armory-market`, `armory-inventory` | `tests/economy_ui_test.gd` with `ECONOMY_CAPTURE_DIR` | Selected tab state, "WITH <partner>", "YOU GIVE" / "<partner> GIVES". Data are the suite's fictional fixtures (the fixture trade has no partner name, so it shows "Unknown player"). |

The "after" captures were taken with the game code of `82ce83f`, which is unchanged through `f8ca47f`. The later reviewer fixes (review §7, `9c04d59`) change the smoke shader's inside test, the client fade, trade name quoting and saved-layout migration. None of these alters the views captured here, except that a trade partner's name now appears in quotes. The one-way-smoke fix is verified by the `SMOKE_LOBE_VIEW` line of `smoke_visual_capture.gd`: 0 marker pixels (control 59,339).

Both sides passed their capture runs: landscape 156/156 assertions each, economy UI pass each, 8 combat frames each, no script errors.

## Measured with the captures

| Metric | Before | After |
| --- | --- | --- |
| Changed pixels inside a hidden operator's projected bounds (behind the cloud) | 0 of 1,817 | 0 of 1,817 |
| Inside-cloud luminance mean / standard deviation | 0.578 / 0.0523 | 0.556 / 0.0515 |

Low-preset concealment was checked the same way on the branch (`smoke_visual_capture.gd --quality=low`): 0 of 1,817 pixels leaked.

**Smoke rendering cost.** The smoke cost probe (`tests/smoke_render_probe.gd`) measures one mature cloud against the same frame without smoke. It ran three times per side, alternating sides:

| Median added frame time over the clear frame | Run 1 | Run 2 | Run 3 | Median |
| --- | ---: | ---: | ---: | ---: |
| Before, Standard cloud | +8.0 ms | +108.3 ms | −18.2 ms | +8.0 ms |
| Before, Low cloud | +0.6 ms | +9.1 ms | −24.6 ms | +0.6 ms |
| After, Standard cloud | +22.0 ms | +73.5 ms | +21.8 ms | +22.0 ms |
| After, Low cloud | +37.6 ms | +52.7 ms | +33.8 ms | +37.6 ms |

The ranges overlap and this shared host is noisy, but every branch run added time while the baseline did not consistently. The new cloud probably costs more, on the order of 5–9 % of a llvmpipe frame here (clear frames: about 410 ms after, 510–560 ms before, because the rest of the scene got cheaper). Low does not reduce it: both presets share the same core and differ only in edge quads. An opaque, depth-writing Low core variant was tried and measured +17 to +77 ms (Standard +9 to +59 ms in the same runs), so it was not kept. That variant also looked worse, and `discard` in an opaque pass can defeat hidden-surface removal on tile-based mobile GPUs. **Measure smoke on a device before deciding whether to simplify the core shader.** Raw results: `benchmarks/smoke-cost-*.json`.

## Benchmarks

`benchmarks/{standard,low}-{before,after}.json` are the three-run summaries from `scripts/profile_render.sh` (fixed cameras, 24 frames per view per run). Draw-call and primitive counts are exact. Frame times are llvmpipe CPU rasterization. The review report summarizes them in [CLAUDE_REVIEW_0.4 §2](../../../audits/CLAUDE_REVIEW_0.4.md).

## Reproduce

```sh
# before: git archive e67f2c8 | tar -x -C <archive>; copy game/tests/smoke_visual_capture.gd into it
export DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=2
godot --path <project>/game --audio-driver Dummy --script res://tests/landscape_ui_test.gd -- --capture-dir=<out>/mobile
ECONOMY_CAPTURE_DIR=<out>/economy godot --path <project>/game --audio-driver Dummy --script res://tests/economy_ui_test.gd
godot --path <project>/game --audio-driver Dummy --script res://tests/combat_presentation_capture.gd -- --capture-dir=<out>/combat
godot --path <project>/game --audio-driver Dummy --script res://tests/smoke_visual_capture.gd -- --capture-dir=<out>/smoke
godot --path <project>/game --audio-driver Dummy --script res://tests/smoke_render_probe.gd -- --output=<out>/smoke-cost
./scripts/profile_render.sh <out> standard|low      # SIGHTBREAK_PROFILE_PROJECT=<archive>/game for the baseline
```
