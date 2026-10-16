# art-v10: viewmodel lighting environment, cage-topology hands, magazine continuity, forearm bounce, calm path

Branch `claude/cs2-fidelity-art-production` (PR #2). Starts from `ed85754` (the last externally verified graphics commit). Code and assets: `5357329` (materials), `5e1da3e` (hands, hip path, continuity test), `1f11697` (forearm bounce, calm path, new controls); evidence commits follow. **Everything below is my own native Godot rendering and tests on Mesa llvmpipe, plus one read-only review by an agent of my own model family (`review/review.md`, verbatim): not human acceptance, not a phone, nobody listened to the audio.** Nothing was merged into `main`; no Codex or Gemini branch was touched.

## Scores, without inflation

The same-model review scored what the stills support (weapon and hands only; motion at speed, a phone and audio not judged): **materials 5.5, viewmodel lighting 5.5, hands 6.0, reload presentation 5.5** (the previous same-family review gave 5.0 on all four). **The 8.5 gate is not met.** Codex's last scoped rubric (6.1/10) and Gemini's (5.25/10) stand against it as well; this round did not earn a higher number than they gave.

## Technical root causes

1. **Rifle pale/olive/matte in v9.** v9 hid the sky-horizon reflection swing by flooring the metal's roughness at 0.80. The engine has one `ROUGHNESS` for both the sun's highlight and the sky's radiance, so the floor also turned the sun's lobe into a wide bright haze (the receiver's 69.7 median luma at the ready was sun 35, reflection 12, ambient 18, fill 9). The fix removes the sky from the metal instead of roughening it (`materials/README.md`).
2. **Hands.** The shape source (a procedural SDF) is a smooth, plausible hand; what skinned badly was the QuadriFlow remesh of it, whose loops fell wherever the quad flow landed. Replaced by a box-modelled cage with loops at every joint (`hands/README.md`). The SDF remains the bake source and the surface: this is not hand-sculpted.
3. **Replacement magazine pop.** The hand holds the magazine by its base, so the magazine's top enters the frame before the hand does; raising the hip made it worse (`continuity/README.md`).
4. **Forearm wedge.** The viewmodel's ambient is flat and the fill darkens down-facing surfaces (0.55 factor), so a forearm turned away from the sun had nothing lighting its underside.

## What changed

- **Materials/lighting (Checkpoint A, `5357329`).** First-person shaders declare `render_mode ambient_light_disabled` and take a fixed studio environment (edge-free gradient, key panel, thin cool strip; Fresnel, baked metalness/roughness, detail normal, baked AO); the sun is the engine's with the baked roughness (floor 0.30, was 0.80); the handguard is a polymer material; the arms reflect almost nothing. Applies to the default finish and every cosmetic.
- **Hands (Checkpoint B).** `tools/art/hand_cage.py`; arms 9,268 → 8,520 triangles; 34 bones unchanged; contact 0.0/0.0/1.0 mm (bounds 1.0/1.0/1.5); grab margin and a deterministic trigger-finger reach.
- **Continuity (Checkpoint C).** Replacement tilted 55° at the hip and the elbow swung out so hand and magazine enter together; hip 34 cm; new independent test `reload_continuity_test.gd` (6 checks; default, `calm`, `still` in `validate.sh`).
- **Readability and calm (Checkpoint D).** `viewmodel_bounce` on the arms (support forearm's underside at the hip: sleeve median luma 33.9 → 42.2 in shade, 48.0 → 61.9 in sun; a pose check in the light-separation test); `calm` clip rebuilt (28 cm pickup, same tilt and elbow). Shipping reduced-motion default unchanged (`current`).
- **Not changed:** reload duration, ammunition and authority, phases, `match.gd`, the protocol, hit volumes, audio, muzzle flash (investigated: seen down the bore any axisymmetric flash reads as a disc, and the star-shaped alternatives were rejected in earlier rounds; a directional flash needs a screen-space or per-shot asymmetric shape, not triangles).

## Comparisons (native, 1280 × 720, same ticks and lighting)

| What | File |
| --- | --- |
| Rifle: 57f6464, v9, v10, sun/shade/backlight | `materials/frames/before-after-*.jpg`, `receiver-zoom-sunlit.jpg`, `v10-stills-backlit-shade-skin-inspection.jpg` |
| Stills of the reload, v9-era (`5357329`) vs final, sun/backlight/shade | `materials/frames/stills-*-before-after.jpg` (the rifle is identical in them: it did not change after `5357329`; the baseline for the rifle is v9, above) |
| Hip forearm before/after | `materials/frames/hip-forearm-before-after.jpg` |
| Hands before/after, support and grip | `hands/frames/` |
| Replacement entering the frame | `continuity/frames/hip-entry-before-after.jpg` |
| Full reload + first shots, 9 configurations (sun, backlight, shade, dark interior, 20:9 and 4:3 *simulations*, reduced current/calm/still), MP4 at 60 fps and quarter speed, contact sheets, per-tick CSVs | `sequences/` |

## Tests (final head, `validate-v10d.log`: `scripts/validate.sh` exit 0)

Weapon-art 180, reload sequence 92, reload audio 29, real-time audio captures 9 and 6, contact 24, visibility 15 (default view), continuity 6 (default, `calm`, `still`), finish stability (sun, shade, skin), light separation 21 (adds the hip pose), actor 73, weapon integrity 28, match 75, networking suite. **No existing acceptance threshold was loosened; one was tightened back:** v9's disclosed relaxation of the first-draw rule in `reload_sequence_test.gd` (`< 25 %`) was restored to the original `< 5 %` (`f4a763a`) and holds with the new hip path. Disclosed empirical thresholds: the continuity test's 1,500 px / 3,500 px / 800 px / 150 px / 6-tick bounds (set after seeing the baseline; the first draft was stricter and was loosened to the 0.1 s perception scale), the hip-sleeve bounds in the light test (midway between with and without the bounce), and the calm pickup depth (chosen from a scan).

## Negative controls

New this round, all caught: N25–N31 (materials: sky radiance back, a hard gradient edge, handguard given the receiver finish, no metal floor, the arms reflecting the whole studio), N32–N34 (v9 hip pose, v9's 31 cm hip, a far pouch), N35 (no forearm bounce), N36 (the v9 calm path). Logs: `../art-v9/negative-controls-*.txt`, `continuity/logs/negative-controls-continuity.txt`, `materials/logs/negative-controls-bounce-calm.txt`, and the full run in `negative-controls-full.txt`: 40 controls, 39 caught and one invalid (N31's text had gone stale); after repairing it and adding the grab pose to the quick light test, N28, N29, N31 and N35 were re-run and are caught (the baseline passes with the new test set).

## Performance (`perf/`, llvmpipe, relative only)

| | `5357329` | `1f11697` |
| --- | ---: | ---: |
| triangles in the viewmodel nodes | 37,598 | 36,850 (arms 9,268 → 8,520) |
| draw calls, ready / mid-reload / flash | 31 / 34 / 34 | 31 / 34 / 34 |
| texture memory | 5,592,824 B | 5,592,824 B |
| `Actor.tick_visual` in a reload, median / p95 (µs) | 15 / 84 | 15 / 32 and 14 / 39 (two runs) |
| frame time, ready (ms) | 166 | 170 and 163 (the two runs of the same build differ by more than the builds do) |

The shader adds one `clamp`, a multiply and an add per fragment on the arms. No claim about a phone's GPU, battery or heat.

## Known defects (the most important first)

1. **The sunlit rifle is still warm grey-olive, with weak specular on its large faces: dark painted graphite, not convincing metal.** In sun the shipped handguard is brighter than the receiver (67.6 vs 54.6 at the ready; level in shade, 29.7 vs 28.4), though the same-model reviewer still read them as close by eye (an earlier version of this line, and of the PR comment, said 54.6 vs 56.6: that came from a probe that did not measure the shipped handguard, see `materials/README.md`). Stable, better than v9, not 8.5.
2. **Hands are better built and still not good.** The grip hand's fingers read as stacked rounded pads; the glove is smooth and doll-like; no tendon structure; the source is procedural, no sculpt.
3. **Shade, backlight and the dark interior are crushed** (receiver, grip and sleeves within 30–40 of 255; suppressor end pure black); the gloves and sleeves are brighter than the rifle and the ground there (a separate-light "ghost" look), and the two hands do not match in value.
4. **`calm`'s hand and magazine are below the frame for about 8–11 ticks** at the hip while the forearm tube stays in view; the default clip has the same stretch by design. No depth passes the continuity test and keeps the hand in view (`reduced-motion/README.md`).
5. **The support forearm at the hip is a foreshortened olive tube** filling the lower left for about 10 ticks.
6. **Muzzle flash and smoke unchanged**: a disc and a soft puff.
7. Not judged by anyone: motion at speed, a phone, 20:9/4:3 shipping behaviour (they are simulations), audio.

## Codex integration notes

Files that need cross-system validation (presentation only; none touches networking, authority or `match.gd`): `game/scripts/gameplay/viewmodel_shading.gd` (new uniforms `viewmodel_env`, `viewmodel_sheen`, `viewmodel_metal_scale`, `viewmodel_reflect`, `viewmodel_ambient`, `viewmodel_bounce`; `render_mode ambient_light_disabled` on first-person shaders; the `ViewmodelShading.surface()/enable()/flash()` contracts are unchanged), `game/scripts/ui/cosmetic_material.gd` (first-person finish carries the same render mode and STUDIO; a duplicated polymer material for the handguard), `game/scripts/gameplay/weapon_model.gd` (arms constants), the arms GLB and its three textures, `clip_contact*.csv` and `.glb.sha256`. `actor.gd` and `reload_phases.gd` were not changed this round. Hazard: a map with a different ambient colour must set `viewmodel_ambient`; nothing does yet. Gemini's `48eb058` was fetched and not merged.

## Next milestone (suggested)

1. A sculpted or licensed-base glove (grip hand first) with the same rig and the bake pipeline here.
2. A real metal read in sun: a rougher but brighter graded finish with anisotropic-looking edge wear painted into the albedo/ORM bake (not shader tricks), and value separation between receiver and handguard.
3. A first-person value pass for shade/dark: gloves below the rifle's value, matched hands, an edge light on the metal.
4. An authored "draw from the hand" for the replacement in `calm`, so the hand never leaves the frame.
5. A directional flash and smoke, with a human reduced-motion review and a phone measurement.
