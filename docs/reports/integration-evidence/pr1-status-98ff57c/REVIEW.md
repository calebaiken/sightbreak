# Independent review: PR1 status fitting at `98ff57c`

Candidate: `98ff57c4a9ec6735db68c4e65ad36f6fe5a26ca6`.
Before: `227d6c8245a75522b8144c8004de2a86d61b833b`.
Read-only detached checkout: `/workspace/sightbreak-pr1-status-review`.

**Recommendation: REQUEST CHANGES on `98ff57c`.** The default-layout status overlap is corrected, but valid saved custom layouts can now make the status text and critical bottom HUD oscillate off-screen. The earlier development-acceptance recommendation applies to `227d6c8`, not this new regression. No production source or PR branches were edited; no GitHub comments were posted by this reviewer.

This is independent execution and source inspection by a separate same-model reviewer agent. It is not human acceptance or an external audit. No mobile-device or GPU performance claim is made.

## Blocking: narrow custom center gap creates an unstable layout and hides critical HUD

Location: `game/scripts/main.gd:1099`–1109, especially unconditional preference for the center-containing interval and unbounded wrapping into that interval. The position calculation reads a row whose own height is changed by wrapping, creating a feedback loop.

Minimal reproduction through the real saved-layout restore path:

- Logical/native viewport 960x720, UI text 130%, touch buttons 100%.
- Preserve every default control except saved `hud_positions` entries:
  - `grenade: [0.459375,0.82]`
  - `smoke: [0.540625,0.82]`
- Start an offline match in the buy phase. Both positions are legal editor/restore values.

The two 28px utility radii plus 8px clearance leave a 6px interval centered on 480px. The fitter chooses this interval despite broad free areas on either side. Real Label wrapping produces 23 lines in a 6x756px rectangle starting at (477,221). Health, funds and ammunition leave the viewport. On the next frame, the changed row height puts buttons outside the tested vertical band; the fitter restores a 346x30px line at (307,589). It then chooses the 6px gap again. Consecutive frames continue alternating.

The longest current notification similarly reaches a 6x2637px Label with 80 lines. When its normal 5s notification lifetime expires during the native sequence, the shorter objective prompt still oscillates; later filenames retain the original scenario name, while frame geometry shows that changed prompt.

### Native visual proof

All screenshots below are actual 960x720 PNGs, with no compositing or retouching:

- Before `227d6c8`: `before-captures/narrow_center-960-buy-00.png` and `-01.png` stay stable. Text overlaps utility buttons, but the full bottom HUD remains visible.
- After `98ff57c`: `saved-captures/narrow_center-960-buy-00.png` shows its ordinary frame.
- The next consecutive frame, `saved-captures/narrow_center-960-buy-01.png`, shows the status as a vertical column and health/funds/ammo absent.
- Eight consecutive buy frames alternate ordinary/broken. `saved-narrow-native.log` records each frame's Label rectangle and visibility checks. The ordinary and broken screenshots were directly visually inspected.

Thus this is a newly introduced regression, not just the earlier status/button overlap.

### Required correction and coverage

Choose a usable interval based on the actual wrapped text bounds; do not prefer an arbitrarily narrow center gap over a viable side interval. Keep fallback placement/layout height bounded and stable when no interval can fit. Preserve the default-layout clearance improvement. Add regression coverage using these two saved positions, longest notification and maximum button size; assert actual Label bounds, bottom HUD bounds and convergence across consecutive frames. Two endpoint samples can miss a two-frame oscillation.

## Nonblocking/pre-existing limitation: no free interval

At 960x720 with 150% buttons, place the 11 drawn targets evenly across the status band. Their expanded target spans cover the entire row. `free` becomes empty, `best` stays ZERO, and `span` remains the full row. Buy text then intersects five targets; the long notification intersects all 11. This persists from the old layout rather than creating the new offscreen regression, but the broad claim that custom layouts are covered is not established. A bounded explicit fallback or documented limit is needed.

## Confirmed improvements

- Maintained `landscape_ui_test.gd`:325 checks, 0 failures at exact98ff57c.
- Independent default cases 960/1280 at 100% buttons and 1600 at 150% buttons, all at 130% text: buy and long notification clear every drawn button, remain on-screen and converge, headless and native.
- A custom centered FIRE button correctly moves/wraps status into the side interval.
- Disabling touch restores zero horizontal status margins in all six tested scenarios.
- Changes are confined to presentation/tests/docs. No actor, weapon, protocol or backend code differs from the previously tested227d6c8 foundation. This review does not claim those suites were reexecuted on 98; the parent combined matrix handles the current integration.

## Results

| Execution | Checks | Failures | Meaning |
|---|---:|---:|---|
| Maintained landscape 98 |325|0|Defaults pass |
| Independent six-case edge matrix 98 headless |54|7|Narrow gap 5; full band 2 |
| Same six cases 98 native |54|7|Same failures reproduced |
| Minimal saved-two-position 98 headless |9|5|New offscreen/oscillation regression |
| Minimal saved-two-position 98 native |9|5|Eight consecutive native frames confirm flicker |
| Six-case negative control 227 headless |48|12|All failures are old text/button overlaps; every case stable with bottom HUD visible |
| Minimal 227 native before |4|1|Old text/button overlap only; stable bottom HUD |

The new maintained `text_block` helper uses `Font.get_multiline_string_size` without matching the Label's smart wrap mode. In the 6px case it estimates a 180px text block while the real Label reports 23 lines/756px. Its on-screen test also omits the bottom edge. Independent tests therefore inspect real Label bounds and frame-by-frame geometry as well as the helper's glyph estimate. This explains why a helper-only check cannot establish bounded custom layouts.

Twenty-eight native captures are retained: 10 general-case stills, 16 consecutive minimal-case frames, 2 matching before frames. All PNG dimensions are recorded in the manifest. Native audio uses Dummy; software OpenGL uses Xvfb:99 / Mesa llvmpipe. Only the expected test-assertion errors occur in the failing probes; no claimed device evidence or performance measurement is involved.

## Reproduce

Use `SIGHTBREAK_STATE_DIR=<isolated state>` with the checkout's `scripts/godot.sh`.

1. `--headless --editor --import --quit`.
2. `--headless --script res://tests/landscape_ui_test.gd`.
3. `--headless --script <review dir>/status_saved_narrow_probe.gd` (expected failure on 98).
4. Native: `DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 scripts/godot.sh --audio-driver Dummy --script <review dir>/status_saved_narrow_capture.gd -- --capture-dir=<output dir>`.

The broader `status_edge_probe.gd` covers defaults, max button size, centered FIRE, narrow center gap, no available span and disabled-touch reset. For exact old comparison run the same fixture from 227; `status_saved_before_capture.gd` limits old native capture to the buy case. Raw logs preserve every assertion and measured rectangle. All commands had finite 90–300s timeouts and all processes exited. Evidence manifest/checksums cover sources, logs and images, excluding generated runtime state.
