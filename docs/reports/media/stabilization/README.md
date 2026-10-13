# Stabilization native captures

These unedited PNG files are actual native Godot 4.7.2 viewport captures on Linux Xvfb/Mesa llvmpipe, not concept art. Their original paths and hashes are in `captures.json`.

- `menu.png`, `settings-tablet.png`: main menu/settings at the recorded desktop logical landscape sizes.
- `mobile-hud-wide.png`, `mobile-hud-tablet.png`: running offline match with touch controls forced visible; 1600×720 and 960×720. The maintained `landscape_ui_test.gd` creates the real main scene and uses native input/UI code. These show synthetic viewport layout, not a physical phone screenshot.
- `item-inspector-fixture.png`, `case-result-fixture.png`: actual native economy widgets with explicitly fictional QA inventory fixtures. They do not demonstrate an earned player balance or a random live reward. Real HTTP/PostgreSQL economy transactions are independently checked and recorded in `../../QA.md`.

Reproduce landscape captures on a graphical display with:

```sh
DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 ./scripts/godot.sh --audio-driver Dummy --script res://tests/landscape_ui_test.gd -- --capture-dir=/absolute/path
```

The final landscape run passed 66 assertions plus nine successful screenshot writes (75 total), with no logged script or texture cleanup errors. Device touch feel, FPS and visual-release acceptance remain separate gates. Environment before/after fixed-camera captures are in `../environment/`.
