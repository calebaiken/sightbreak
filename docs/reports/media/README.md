# Native captures

These PNGs are actual Godot 4.7.2 desktop viewport captures, rendered through Mesa llvmpipe under Xvfb at 1280×720. They are not concept art or web mockups.

- `native-menu.png`: running main menu over the original Relay Yard.
- `native-combat.png`: offline native match during live simulation, with real HUD, bots, geometry and procedural weapon.

The associated `../render-metrics.json` records an uncontrolled CPU software-render diagnostic, including concurrent cloud workloads. It is not a physical mobile benchmark, a 60 FPS result or an acceptance score. See `../QA.md` for the rendered teardown investigation and all remaining limitations.

Economy UI development captures additionally exist in ignored `.local/screenshots/economy/`; those are explicitly labelled fictional QA fixtures and are not evidence of naturally earned player inventory. Actual native/HTTP transaction checks are reported separately.
