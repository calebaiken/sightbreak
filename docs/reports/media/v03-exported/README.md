# Exported Linux native game capture

[Actual exported demo screenshot](linux-demo.png) and [unaltered process output](linux-demo.txt). This was captured from `builds/linux/sightbreak.x86_64`, not the editor or a web reconstruction. The process exited 0 with `SIGHTBREAK_DEMO_CAPTURED`, no script/renderer/leak errors and the expected Xvfb unsupported-VSync warning. The integration owner inspected the resulting yard, weapon and native HUD.

The scene is the built-in offline demo during its opening buy phase, not a human-played complete match. It uses Godot 4.7.2 Compatibility/Mesa llvmpipe under Linux Xvfb at 1280×720. No phone or hardware GPU performance is implied. `capture.json` binds the executable, shipped source and exact image hashes.

```sh
DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 ./builds/linux/sightbreak.x86_64 \
  --audio-driver Dummy -- --demo --capture=/absolute/output/linux-demo.png
```
