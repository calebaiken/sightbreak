# Relay Yard surface review

The surface pass uses three original, reproducible 128×128 grayscale PNG tiles for asphalt, concrete and painted container panels. Run `python3 scripts/generate_surfaces.py` to regenerate the exact assets. Texture import enables mipmaps; world projection maintains scale across differently sized geometry. Roughness separates painted metal from paving. Slightly stronger ambient/key light retains the original warm/cool palette. No geometry, collision, route or weapon balance changes are included.

The existing static batches remain intact. Texture sampling adds GPU work even when geometry and draw counts are unchanged; physical mobile cost has not been measured. There is no runtime procedural noise, normal map, added light or postprocessing pass.

## Evidence

`game/tests/environment_probe.gd` renders three fixed native camera views of the actual arena and rifle. This is a deterministic visual fixture, without simulated opponents or match HUD. Captures use Godot 4.7.2 Compatibility on Linux Xvfb/Mesa llvmpipe at 1280×720. These are not device screenshots or device FPS measurements.

```sh
DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 ./scripts/godot.sh --audio-driver Dummy \
  --script res://tests/environment_probe.gd -- \
  --output=/workspace/sightbreak/builds/qa/environment-after
```

| View | Before draw calls | After draw calls | Before primitives | After primitives |
| --- | ---: | ---: | ---: | ---: |
| Approach | 248 | 248 | 23,522 | 23,522 |
| Site A | 178 | 178 | 16,650 | 16,650 |
| Overview | 244 | 244 | 25,098 | 25,098 |

Captured images are in `media/environment/`, named `*-before.png` and `*-after.png`. Both probes exited cleanly without Godot errors. The existing shared sky remains preloaded and unchanged.

The actor/arena regression suite passes 51 checks, including the 25 unchanged navigation obstacles, roughness-aware material caching and small world-scaled surface textures. Existing character silhouettes and many structural shapes remain simple procedural art; this surface pass does not establish the requested 8.5/10 visual quality gate.
