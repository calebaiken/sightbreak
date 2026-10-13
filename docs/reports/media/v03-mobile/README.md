# 0.3 mobile landscape evidence

These are unedited viewport captures from the running native Godot application on Linux, using Xvfb and Mesa llvmpipe. Touch controls are forced visible. They demonstrate native layout and rendered content; they are not photographs or measurements of a physical phone.

The maintained `game/tests/landscape_ui_test.gd` opens the actual menu, settings, match HUD, requisition, roster, and touch editor at 960×720, 1280×720, 1600×720, and 1560×720. The last size has the same aspect ratio as a 2340×1080 phone display. It checks reticle centering, centered scores, touch-target bounds, instructions, and panel overflow. Synthetic safe-area and multitouch checks are separately maintained in `game/tests/touch_test.gd`.

Reproduce on a graphical display:

```sh
DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 \
SIGHTBREAK_STATE_DIR="$PWD/.local/v03-mobile-capture" \
./scripts/godot.sh --audio-driver Dummy \
  --script res://tests/landscape_ui_test.gd -- \
  --capture-dir="$PWD/builds/qa/v03-mobile"
```

Compared with the [0.2 mobile HUD captures](../stabilization/README.md), the HUD now uses transparent edge fades, keeps the score and aiming reticle centered, adds original vector action glyphs with readable labels, and exposes reload/critical-health states. Confirmation ticks are driven by resolved damage. The four-aspect evidence does not establish device reachability, touch latency, thermal behavior, battery use, or GPU performance; those remain physical-device checks.

The native capture run passed **156 assertions** (144 layout checks plus 12 successful screenshot writes), exited successfully, and logged no script errors or texture/resource cleanup errors. The software driver emitted its known unsupported VSync warning. The unmodified log and SHA256 manifest are included here. Four combat ratios, the 1280 menu and tablet settings are retained; the remaining native screenshots are in `builds/qa/v03-mobile`.

A separate regression verifies that maximum-size (1.5×) default touch controls do not overlap visually at 960×720. Existing saved custom layouts remain user-controlled.
