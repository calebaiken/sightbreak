# Mobile aspect and world FOV review

Fresh source: `60cf125bb2c05606e71a4a68482d31ec26dc69bb`, including foundation 98ff57c. Earlier d084/85edf results are preserved separately. Native Godot4.7.2 Compatibility/OpenGL on Xvfb/Mesa llvmpipe. This fixture changes the running window only; committed `project.godot` keeps the existing policy. Physical safe areas, touch comfort and gyro are UNVERIFIED.

| Policy | Physical window | Logical viewport | Origin / scale | Horizontal world FOV | Crosshair/touch/HUD bounds |
| --- | --- | --- | --- | ---: | --- |
| keep | 1280×720 | 1280×720 | [0.0, 0.0] / [1.0, 1.0] | 114.19° | PASS |
| keep | 1440×720 | 1280×720 | [80.0, 0.0] / [1.0, 1.0] | 114.19° | PASS |
| keep | 1560×720 | 1280×720 | [140.0, 0.0] / [1.0, 1.0] | 114.19° | PASS |
| keep | 1600×720 | 1280×720 | [160.0, 0.0] / [1.0, 1.0] | 114.19° | PASS |
| keep | 960×720 | 1280×720 | [0.0, 90.0] / [0.75, 0.75] | 114.19° | PASS |
| expand | 1280×720 | 1280×720 | [0.0, 0.0] / [1.0, 1.0] | 114.19° | PASS |
| expand | 1440×720 | 1440×720 | [0.0, 0.0] / [1.0, 1.0] | 120.19° | PASS |
| expand | 1560×720 | 1560×720 | [0.0, 0.0] / [1.0, 1.0] | 124.07° | PASS |
| expand | 1600×720 | 1600×720 | [0.0, 0.0] / [1.0, 1.0] | 125.26° | PASS |
| expand | 960×720 | 1280×960 | [0.0, 0.0] / [0.75, 0.75] | 98.43° | PASS |

All ten configurations passed: crosshair remains centered; synthetic touch circles and radar/ammo/health/funds bounds stay inside the logical viewport. This does not test every glyph collision: the independently reproduced130% custom narrow-gap status oscillation fails and can hide the bottom HUD. Default-layout bounds do not certify every saved layout.

World vertical FOV stays82° in both policies; the first-person weapon uses a separate54° projection. Keep maintains the same114.19° horizontal world FOV at all five sizes, introducing side bars80/140/160 px at 18:9/19.5:9/20:9 and 90 px top/bottom bars at 960×720. The root viewport PNG under keep excludes those bars (960×540 at the4:3 physical window); physical window, capture dimensions, transform and origin are logged separately. Filled art-review20:9/4:3 captures therefore do not imply the shipping window is full bleed.

**Recommendation: retain keep until an explicit competitive FOV policy is approved.** Expand fills modern displays but fixed vertical FOV grants wider displays more horizontal visibility:120.19°,124.07°,125.26° at 18:9,19.5:9,20:9, versus98.43° at 4:3. Fixing horizontal FOV would move the visibility difference to the vertical axis. A product decision must define equal visibility, allowed peripheral advantage or constrained competitive viewports, then retest aiming sensitivity, all UI scales and real notch/touch behavior. Do not silently apply expand as a cosmetic layout fix.

Reproduce: `DISPLAY=:99 scripts/godot.sh --audio-driver Dummy --script res://tests/integration_aspect_probe.gd -- --output=<directory>`. Raw metrics and ten native PNGs are packaged with the integration evidence.
