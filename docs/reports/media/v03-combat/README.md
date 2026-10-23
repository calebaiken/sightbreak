# Native combat presentation evidence — 0.3.0-dev

All PNGs are unmodified captures from the running Godot application. Geometry,
materials, articulated operators, viewmodels, smoke and effects are rendered 3D
content. These are deliberately staged review fixtures, not screenshots of a
naturally played match or evidence of human-tested animation quality.

## Reproduce

Final captures use source commit `538f52f9a9dfb5dac38209b7541bde145fc01976`,
Godot 4.7.2 Compatibility/OpenGL, Mesa llvmpipe software rendering, Xvfb display
`:99`, Dummy audio and a 1280 × 720 viewport:

```sh
DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 ./scripts/godot.sh \
  --audio-driver Dummy --script res://tests/combat_presentation_capture.gd \
  -- --capture-dir=/absolute/path/to/captures
```

The fixed first-person camera starts at actor position `(0, 0.05, -19)`, yaw
`PI - 0.08`, camera pitch `-0.025`, FOV 82. The operator camera is at
`(0, 1.45, -14)`, looks at `(0, 1.05, -18)`, FOV 55. The same poses and
renderer settings were used for iteration 1. Arena detail changed during the
iteration, so the background is not a controlled environment comparison.
For the immutable 0.2.0 baseline comparison, see [world evidence](../v03-world/README.md).

`render.log` records the successful final process exit in the accompanying
manifest. Its only warning is unavailable V-Sync switching on Xvfb. There are
no logged script errors, renderer resource leak messages or shutdown errors.
`sha256.txt` records exact hashes for all retained PNGs and the renderer log.

## Screenshot-driven changes

| Subject | Initial 0.3 iteration | Final 0.3 capture | Change |
| --- | --- | --- | --- |
| Rifle | [Initial](iteration-1/02-rifle-ready.png) | [Final](final/02-rifle-ready.png) | Narrower graphite receiver, machined bevels, indexed geometry, differentiated attachments, glove and cuff detail. |
| Operators | [Initial](iteration-1/06-operator-silhouettes.png) | [Final](final/06-operator-silhouettes.png) | Pastel bodies and white goggles replaced by graphite cloth, muted team accents, dark goggles, smaller boots, raised support grip and beveled gear. |
| Smoke | [Initial](iteration-1/07-smoke.png) | [Final](final/07-smoke.png) | Bright opaque lobes replaced by a textured closed core with bounded soft billboard edges; UV seams removed. |

Iteration 1 was captured during development of 0.3, before independent visual
critique. It is not an immutable 0.2 baseline. That early operator fixture also
left the unused first-person gun visible behind the models; the final fixture
hides it before switching cameras.

Additional final evidence:

- [Sidearm](final/01-sidearm-ready.png)
- [Rifle firing](final/03-rifle-fire.png)
- [Reload extraction](final/04-rifle-reload.png)
- [Magazine reseated](final/05-rifle-reseated.png)
- [Pooled impact effect](final/05b-bullet-impact.png), held at a fixed point to the left of the viewmodel for inspection.

## Scope and limitations

Weapons share the same procedural model between gameplay and inspection.
Static metal and cloth attachments batch by material; operators batch clothing
and equipment per articulated joint. Effects reuse fixed pools of 24 casings,
40 sparks and 12 dust instances. Their cosmetic RNG cannot affect shot spread.

Smoke uses one opaque core and six translucent quads in High or three in Low.
All clouds share one original 64 × 64 RGBA texture, about 22 KiB with mipmaps.
There are no smoke lights. Core shading samples that texture three times per
fragment; each edge quad samples it once. Alpha overdraw still needs device
measurement. The server's smoke visibility radius and damage rules are unchanged.

These changes improve presentation, but operators remain visibly stylized and
procedural, the default rifle has strong highlight bands, impact dust remains
simple, and the opaque smoke core still has a rounded mass. This evidence does
not establish an 8.5 visual score, physical-device frame rate, thermal behavior,
battery consumption, human-rated gunplay or release readiness. Independent
scoring and remaining defects are in [QA-0.3](../../QA-0.3.md).
