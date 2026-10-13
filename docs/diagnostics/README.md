# Sky retirement reproduction (Godot 4.7.2)

QA-012 was narrowed to sky lifetime during scene transitions. This diagnostic constructs only two small Godot scenes, each with a procedural sky, a camera and a directional light. It does not load SIGHTBREAK assets, UI, gameplay, screenshots or test render probes.

Run with the installed official Godot binary on a graphical display:

```sh
DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 ./scripts/godot.sh --audio-driver Dummy --script ../docs/diagnostics/godot_sky_retirement.gd
DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 ./scripts/godot.sh --audio-driver Dummy --script ../docs/diagnostics/godot_sky_retirement.gd -- --wait-before-free
```

On the observed Linux Xvfb/Mesa llvmpipe configuration:

- Immediate retirement before the first rendered frame produces two texture teardown errors, each 349,524 tracked bytes. Godot itself exits zero, so inspect the log.
- Waiting for `RenderingServer.frame_post_draw` before retiring the first scene exits without the texture errors.

This is an **expected-failure engine diagnostic**, intentionally excluded from the passing release regression command. Keep both variants together. It is not a physical-device memory test.

## Source evidence

In the [official 4.7.2 GLES3 renderer](https://github.com/godotengine/godot/blob/4.7.2-stable/drivers/gles3/rasterizer_scene_gles3.cpp), `_invalidate_sky` places skies on `dirty_sky_list`; `_update_dirty_skys` allocates a radiance/raw-radiance texture pair. `_init_radiance_texture` records an RGBA8 mip chain size: 349,524 bytes for the default 256 pixel size. `free(RID)` frees a sky without unlinking it from that dirty list. The observed lifetime sensitivity and allocation pair are consistent with this engine cleanup defect. This is stronger evidence than attribution by texture size alone; other GPU drivers have not been tested.

## Project mitigation and regression

Relay Yard now preloads one immutable `assets/environments/relay_sky.tres` resource shared by menu and match scenes. It avoids creating and immediately retiring redundant sky resources and keeps the same lighting. There is no forced garbage-collection loop, dropped error output, renderer switch or Godot source patch.

`DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 ./scripts/test_render.sh` checks the actual demo and five rendered menu/match cycles, verifies old scene weak references are released, checks warmed texture allocation counts plateau, and rejects logged renderer errors even when Godot exits zero. This validates the project mitigation on the measured configuration; it does not fix the upstream renderer or establish indefinite memory stability.
