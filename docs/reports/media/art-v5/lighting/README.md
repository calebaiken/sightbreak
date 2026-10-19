# The black pulled magazine: diagnosis, fix and measurements

Every number here is measured from real rendered frames (Godot 4.7.2, Xvfb, Mesa llvmpipe, 1280 × 720, the arena's own lighting) by `game/tests/viewmodel_light_probe.gd`. They are software-rendered desktop frames, not phone captures. `sha256.txt` hashes every file.

## What was wrong

The independent review of `b507205` reported the pulled magazine near black in backlight (median RGB about 3, 3, 2). The working hypothesis was weak shadow-side lighting: the engine's flat ambient plus a 0.08 × albedo emission floor, crushed by the Filmic tonemapper. **That hypothesis was wrong as the dominant cause.**

`frames/diagnosis-pulled-magazine-*.png` render the pulled magazine's actual shader inputs. Over the magazine's visible pixels:

| Input | Median |
| --- | ---: |
| Albedo | 109 (a normal tan) |
| **Baked ambient occlusion** | **0** (p90 36) |

The occlusion was baked (`tools/art/bake.py`) with the magazine **seated inside the magwell**. The faces that were inside the well came out fully occluded, so they are black the moment reload pulls the magazine out, in every lighting condition. No amount of ambient light can lift an occlusion of 0. Measured at the magazine's own UVs, 23.4 % of its vertices had occlusion below 0.1.

## The fix

The occlusion of a part that moves should be its own. Two new tools in `tools/art/`:
- `rebake_part_ao.py` re-bakes one object's occlusion from the retained unwrapped `.blend` with everything else hidden from the render. It bakes onto a black and onto a white canvas; the part's UV islands are exactly the texels where the two agree, even where the occlusion itself is 0.
- `patch_part_ao.py` merges the result into the full occlusion bake on those texels only.

**Provenance check.** Regenerating the textures from the unpatched raw bake with `textures.py` reproduces the shipped `relay_ar_albedo.png`, `relay_ar_orm.png` and `relay_ar_normal.png` **byte for byte** (maximum difference 0). The patched set differs from the shipped one **only in the red (occlusion) channel of `relay_ar_orm.png`**, in 41,235 texels of the magazine's islands. The albedo and normal maps and the GLB are unchanged.

| Over the magazine | Before | After |
| --- | ---: | ---: |
| Mean occlusion (island texels) | 0.412 | 0.662 |
| Texels below 0.1 | 49.8 % | 25.4 % (real recesses between ribs) |
| Mean occlusion (vertices, shipped 1024² texture) | 0.583 | 0.762 |
| Vertices below 0.1 | 23.4 % | 5.9 % |

`weapon_art_test.gd` (109 → 111 checks) now asserts at most 10 % of the magazine's vertices below 0.1 and a mean of at least 0.70. With the previous ORM restored it fails both (23.7 % and 0.585).

## Measured result

Median luma (0–255, sRGB-encoded) of each part's visible pixels, by hiding the part and counting the pixels that change. The "dark interior" scenario is the shade view with the sun scaled to 8 % and the ambient to 30 %. **Only the magazine changed** (cells that moved by 3 or more luma, before → after):

| Scenario | Pose | Magazine |
| --- | --- | ---: |
| Sun | grab | 66 → 83 |
| Sun | mid reload | 88 → 143 |
| **Backlight** | **mid reload** | **4 → 59** |
| **Shade** | grab | 0 → 41 |
| **Shade** | mid reload | 2 → 56 |
| Dark interior | grab | 2 → 21 |
| Dark interior | mid reload | 2 → 33 |

- **Isolation:** no other part (receiver, handguard, furniture, gloves, sleeves) changed by more than 3 luma in any of the 16 scenario and pose cases. The full tables are in `logs/light-before-7ce8981.log` and `logs/light-after.log`.
- **The magazine is never below 20 anywhere** (it was 0–4 in six cases).
- **Inspection lighting is unchanged:** the inspection render of the rifle with a skin differs by 1 pixel of 921,600 (largest difference 7 of 765) before and after.
- `backlit-before-after.png` shows the real frames: the pulled magazine as a black slab in frames 52–84 before, readable after.
- **Not self-lit:** the lighting model is untouched, so the weapon still gets darker with the scene: in the dark interior every part is at or below its shade value in the same pose (the handguard barely responds, 52 against 52 to 53, as at baseline; its value comes mostly from the sun-facing side it shows).

## The fill that was investigated and rejected

The brief asked for a shaped, view-space fill. I implemented one (hemisphere term by world normal, scaled by baked occlusion, albedo, metallic and roughness, driven by the scene's ambient energy with an eye-adaptation floor) and swept its gain against the pre-registered criteria (`logs/light-fill-gain-*.log`, `logs/light-ao-only-fill-off.log`):

| Gain | Gloves, dark interior | Sunlit values within 8 % of baseline |
| --- | ---: | --- |
| 0 (AO fix only) | 16 | pass |
| 0.25 | 17 | pass |
| 0.4 | 18 | pass |
| 0.6 | 19 | **fail** (sleeves 145 → 160) |
| 2.2 (first attempt, measured before the AO fix) | 34 | **fail badly** (sleeves 145 → 235: the unnaturally self-lit look the brief warns against) |

It buys 1–3 luma in the darkest scene and costs sunlit fidelity, a shader term, a material registry and a per-frame hook. **I removed it.** The measured defect was the baked occlusion, and the lighting model stays as it was.

## Corrections to my own criteria

- "Every part's dark-interior median ≤ 0.5 × its sunlit median" was **ill-posed**: it fails on the *baseline* handguard (0.57), because the sun and dark scenarios stand at different headings. The meaningful comparison holds the camera fixed (dark against shade), which is unchanged by this fix.
- "Every visible part's median ≥ 20" was met by everything except one case below.

## Still open

- **Gloves in the dark-interior scenario: median 15–16** (below the 20 I set). It is their faithful response to a nearly dark scene (albedo 0.024 linear), and lighting can't fix it without lifting sunlit values. The lever is the glove's value, which belongs with the hand rework.
- **In sun the pulled magazine is now the brightest part** (143), warm tan beside the grey receiver. The review's note that tan furniture shares the gloves' warm band stands; the magazine's colour is a material decision still to make.
- Receiver against glove value in shade is unchanged (24–35 against 30): the review's value-separation point is not addressed by this fix.
- Frames were captured on a software renderer; GPU tonemapping on phones is UNVERIFIED.
