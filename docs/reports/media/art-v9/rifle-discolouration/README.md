# The rifle that turned pale in the reload: root cause and correction

Branch `claude/cs2-fidelity-art-production`, from `57f6464`. Checkpoint A of the art-v9 round. **Evidence: my own native renders and measurements on Mesa llvmpipe under Xvfb. No human has looked at the before and after frames except through these images, and nothing here was seen on a phone.**

## The defect, as measured

A review of art-v8 saw the Relay AR "pale or beige around reload frames 120 to 134". Reproduced at `57f6464` (`logs/probe-before-sunlit.csv`, the median colour of the receiver's own pixels, found by hiding the part and counting what changes):

| reload tick | receiver (sun) | handguard (sun) | furniture (sun) | receiver colour (r g b) |
| --- | ---: | ---: | ---: | --- |
| 0 (ready) | 54 | 74 | 65 | 53 55 54 |
| 40 to 118 (rolled 27.7°, lifted) | 80 | 103 | 52 | 74 82 83 |
| 124 (rolling back) | 81 | 96 | 57 | 77 82 79 |
| 130 | 62 | 80 | 64 | 60 63 61 |
| 134 (ready again) | 55 | 74 | 65 | 53 56 54 |

So it is not frames 120 to 134 in particular: the receiver is 48 % brighter and bluer for the whole reload hold and returns to graphite as the roll comes back (the beige the review saw is the transition, where the colour passes through (77, 82, 79)). Ready and tick 134 are identical, so nothing is left changed after the reload.

## Root cause

**View-dependent reflection of the procedural sky on the painted metal.** Not a material, texture, UV, shader-parameter or cosmetic-assignment change.

Evidence, in the order I gathered it (`game/tests/reload_discolour_probe.gd`; every CSV is in `logs/`):

1. **The materials do not change.** The probe records every painted part's material resource id and the shader parameters that could change (fill floor, rim, lift, `patterned`, `wear`, `detail`) at every tick: one distinct audit string across all ticks and conditions.
2. **The animation is not needed.** With the animation frozen (idle pose, no reload state, no arms clip) and only the gun node's roll swept from 0 to 25.8° (the reload's own `ARMS_RELOAD_ROTATION`), the receiver goes 54.5 → 77 (`logs/sweep-before-sunlit.csv`). Lifting the gun 14 cm alone, with no roll, does the same: 54.5 → 74.0.
3. **It is the reflection term.** Disabling the Environment's reflected light source: in shade the receiver is a constant 13.5 at every roll angle and lift (against 29 → 51 with it), so in shade the whole swing is the sky reflection. In sun it removes 21 of the 28.6 luma of swing (54.5 → 83.1 becomes 38.6 → 46.4); the rest is diffuse sun and ambient.
4. **It is not the fill, the rim or the muzzle light.** Switching off the viewmodel's fill and rim moves the receiver by 2 luma at every pose. The flash light is off in these frames.
5. **It is the shape of the sky, not its brightness.** `relay_sky.tres` has a bright horizon band (0.76, 0.80, 0.78) with the ground below it falling to (0.20, 0.24, 0.27) within a few degrees (default ground curve 0.02). At rest the receiver's reflection vector lies a little under the horizon and mirrors the dark ground; the roll, the lift (which changes the view vector at 0.5 m) and the pitch (1.7° to 5.7°) slide it across the edge to the bright band. A flat-colour sky removes most of the swing (receiver 76 to 77 across the roll sweep); lightening only the ground half of the sky makes the *ready* pose brighter (54 → 78), which says the ready look is the dark ground in the reflection.
6. **The roughness of the lobe decides how much of the band it sees.** The baked roughness is 0.45 or more already; raising it makes the lobe average the sky over the band. Lowering `METALLIC` does not help (the swing stays 29 luma): the diffuse term varies too.
7. **The symptom is general, not tied to the reload.** It occurs in the sun and in shade; with the unskinned finish, with a cosmetic skin applied (receiver 53.6 → 89.8 over the sweep), and in the procedural fallback rifle (43 → 70). It occurs with the lift or the roll alone. I did not disable viewmodel lighting wholesale; the fill and rim terms, which are the viewmodel lighting I wrote, are shown above to contribute 2 luma. The furniture moves the other way (65 → 52, darker).

## The correction

`ViewmodelShading.METAL_ROUGHNESS = 0.80`, a new `viewmodel_roughness` uniform that the first-person fragment code applies as `ROUGHNESS = max(ROUGHNESS, viewmodel_roughness)`, set by `CosmeticMaterial.finish()` for the first-person finish only (the receiver and handguard, skinned or not). Inspection, third person and the procedural weapons use the engine's own shader and are unchanged. The furniture, grip, arms and magazine are untouched.

I tried and rejected, with numbers (`logs/experiments-*.csv`, `logs/studio-*.csv`, `logs/ground-*.csv`, `logs/floors-*.csv`):

| option | receiver ratio, sun | receiver ratio, shade | cost |
| --- | ---: | ---: | --- |
| none (57f6464) | 1.52 | 1.75 | |
| lower metallic | 1.46 | 1.70 | no effect |
| roughness floor 0.65 | 1.29 | 1.36 | |
| roughness floor 0.70 | 1.26 | 1.31 | |
| **roughness floor 0.80 (shipped)** | **1.18** | **1.13** | ready receiver 54.5 → 63.5 in sun; handguard in shade 50.7 → 28.2 |
| lighter sky ground | 1.18 to 1.24 | 1.45 to 1.48 | ready look changes by +24 to +39 luma; shade not fixed; changes the world's sky |
| a fixed viewmodel environment (engine ambient and radiance off, my own gradient) | 1.24 | 1.28 | ready look drops to 37; fitting the replacement for ambient and reflection is a larger change than the defect |
| flat sky | 1.18 | 1.30 | changes the world |

(The ratio is the highest median luma over the lowest across the roll sweep, lift and both; the handguard's ratios are in the CSVs.)

**What the correction costs, honestly:** the finish is a more matte graphite in first person (a floor of 0.80 removes the sheen the baked roughness gave) and the handguard in shade is darker (50.7 → 28.2 median luma at rest), closer to the receiver and the grip in value. Priority Two of this round (material separation) has to deal with that; it was not hidden by brightening anything here. The skinned finishes' first-person gloss (baked 0.29) is also lost to the same floor; their inspection view is unchanged.

## After

`logs/after-*.csv` (reload ticks and sweeps; sun, shade, skinned). Highest over lowest median luma of the painted metal through the reload: receiver 1.18 (sun), 1.13 (shade), 1.17 (skin); handguard 1.22, 1.20, 1.15 to 1.19. Before: 1.52 and 1.42 (sun), 1.75 and 1.48 (shade), 1.68 and 1.48 (skin). The frames: `sheets/rifle-crops-sunlit.jpg`, `sheets/rifle-crops-shade.jpg` (before on top, after below, ticks 0, 100, 124, 134, cropped to the rifle at the capture's own pixels), `sheets/before-after-*.jpg` (the whole frame). In the sunlit crops the rolled receiver at tick 100 is a blue-grey in the before row and a neutral graphite in the after row, close to the ready tick.

**This does not make the swing zero** (a ratio of 1.18 is 18 %); the rest is diffuse sun and ambient on a surface that turns toward the sky, which is lighting, not a defect.

## Tests and controls

- `reload_discolour_probe.gd --assert` is a native test: the receiver and handguard's median luma through the reload ticks (and, in the probe's sweep mode, through a frozen-animation roll and lift sweep) stay within 1.25 of their lowest. **The 1.25 bound is derived from the measured data** (before 1.42 to 1.75, after at most 1.22), not from a visual standard. It runs in `scripts/validate.sh` for sun, shade and a skin.
- `weapon_art_test.gd` checks that the first-person finish carries the floor (at least 0.7) and that only the first-person cosmetic shader applies it.
- Negative controls (`scripts/reload_negative_controls.py --only N25,N26,N27`, `logs/negative-controls.txt`): the floor reverted to 0, the finish no longer given the floor, the shader ignoring it: 3 of 3 caught, each by both tests, with the baseline passing first.
- **A defect in the control harness, found by this work:** the harness restored only the three files earlier controls edited, so the new controls (which edit `viewmodel_shading.gd` and `cosmetic_material.gd`) left their edits in the tree, which made the next `validate.sh` fail and made the second and third controls run on top of the first. The harness now restores every file any control edits, and the three controls were re-run on a clean tree (the log is that run). The full suite's earlier 29 controls were not affected: none of them edits these files.
- `scripts/validate.sh` passed on the corrected tree (169 weapon-art checks, 92 sequence, 29 audio, 9 + 6 audio captures, 24 contact, 15 visibility, and the three finish-stability runs).

## Not claimed, and not done

- Nothing about a phone's GPU: the sky reflection of other renderers (Forward+, Mobile) and a device's tonemapping were not tested; the project ships the GL Compatibility renderer and this is measured on llvmpipe with it.
- The ready-pose look changed slightly (above); I judged it from the crops, and no one else has.
- The furniture's own pose-dependence (it gets darker, ratio 1.45 in sun) is not corrected: a roughness floor on it helps in sun (1.22) and makes it worse in shade (1.49), so I left it.
- The negative controls cover this fix only; the full control suite (29 earlier controls) was not re-run for this checkpoint.
