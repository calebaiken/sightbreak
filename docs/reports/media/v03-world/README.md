# Relay Yard: native before/after evidence

These are direct PNG captures of the running Godot application, with no image editing.

- **Before:** immutable `4f21dc14ef73c3d620f095065ab89a0035ddd1f2` checkout, freshly
  captured for this milestone.
- **After:** 0.3 world geometry/materials and combat presentation; see source hashes in
  `capture.json`. The actor rendering also changed during the milestone.
- **Renderer:** Godot 4.7.2 Compatibility, Mesa llvmpipe under Linux Xvfb, 1280×720.
- **Harness:** `game/tests/environment_probe.gd`, same three camera definitions and
  fixed render settings. No active bots or match simulation in these comparison stills.

| View | Before | After |
| --- | --- | --- |
| Freight approach | [Before](before/approach.png) | [After](after/approach.png) |
| Objective A | [Before](before/site.png) | [After](after/site.png) |
| Yard overview | [Before](before/overview.png) | [After](after/overview.png) |

The approach shows articulated wall bays and route identity, material separation and
new combat presentation. The site shows an engineered crane, loading bays, transit-case
hardware and relay terminal details. The overview shows consistent structural rhythm,
roof equipment and subdivided service surfacing without changing the tested route layout.

The first rendered pass exposed a rooftop unit outside its supporting roof and a
partially occluded old brand sign. Those were fixed. The second pass exposed mirrored
side-wall lettering; inward label orientation is now covered by a regression. No failed
pass is substituted for final evidence.

Run with an available graphical display:

```sh
DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 ./scripts/godot.sh --audio-driver Dummy \
  --script res://tests/environment_probe.gd -- --output=/absolute/output/directory
```

`metrics.json` records scene draw calls/primitives for each actual view. These are
render-work diagnostics, not FPS or phone measurements. Use the separate fixed-work
benchmark for sample timings. Final independent judgments and remaining visual
limitations are in [QA-0.3.md](../../QA-0.3.md).
