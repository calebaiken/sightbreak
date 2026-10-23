# Opaque account screen: unnecessary background rendering

A controlled native probe opened the actual offline inventory screen at 1280×720, froze its underlying menu camera, and rendered visible yard → hidden yard → visible yard. Each phase had four settling frames and twelve sampled frames. All three unedited screenshots have the **same SHA256**, so hiding the yard leaves the opaque account UI unchanged.

| Measured quantity | Visible before | Hidden | Visible after |
| --- | ---: | ---: | ---: |
| Median draw calls | 358 | 33 | 358 |
| Median primitives | 74,346 | 4,292 | 74,346 |
| Median frame time, ms | 267.880 | 21.875 | 261.336 |

These are Godot 4.7.2 Compatibility measurements on Linux Xvfb/Mesa llvmpipe. They demonstrate avoidable rendering work in this environment. They are **not mobile FPS, thermal or battery measurements**. The small timing sample is diagnostic; the render-counter change and identical screen output support the optimization.

The retained implementation hides the cached `menu_world` on `open_economy`, restores it on `show_menu`, and skips the hidden menu camera orbit. It does not unload map resources, modify account transactions, or hide gameplay. Main-scene regressions verify both transitions; the native economy UI suite passes.

Reproduce:

```sh
DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 \
SIGHTBREAK_STATE_DIR="$PWD/.local/v03-occlusion-probe" \
./scripts/godot.sh --audio-driver Dummy \
  --script res://tests/menu_occlusion_probe.gd -- \
  --output="$PWD/builds/qa/v03-menu-occlusion"
sha256sum builds/qa/v03-menu-occlusion/*.png
```

The probe explicitly forces both visibility states so it remains reproducible after the optimization. Its final step hides the yard and checks that returning to the menu restores visibility. The original measurement predates that added restoration check; the state transitions are independently covered by `main_test.gd`.
