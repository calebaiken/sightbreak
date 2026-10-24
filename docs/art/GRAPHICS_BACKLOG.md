# Graphics backlog and evidence log

Durable record for the graphics work stream. It says what the renderer can and cannot do, what shipped, what was measured and rejected, and what comes next. Each statement names its evidence. Captures come from the software rasteriser (llvmpipe under Xvfb); there is no GPU in the build container, so frame times here are relative and never device frame rates.

## What the installed engine does in Compatibility (Godot 4.7.2, measured)

Each row is a pixel experiment on the real Relay Yard (`game/tests/graphics_tiers_capture.gd`, 1280x720, same view, one setting changed).

| Setting | Result | Consequence |
| --- | --- | --- |
| `tonemap_mode` Filmic to Linear | 99% of pixels change by more than 6 levels | Tonemapping works in the single-pass path |
| Any post effect on (`adjustment_enabled` at identity values) | Switches the renderer to a post pass. Sunlit surfaces compress (clipped pixels in view 11: 2.69% to 0.00%), floors and walls move by about +5 levels | The post pass is a look change, not a free toggle. It is the real content of the HIGH tier |
| SSAO on top of the post pass | Against the post pass alone, two parameter sets (radius 0.5 and 1.4, light affect 0 and 0) darken 0.2% to 0.7% of pixels by more than 6 levels; mean change -0.06 to -0.24 levels. Four further sets (radius 0.35 to 2.5, intensity 0.8 to 2.5) were compared with the single-pass image and show the same few-percent darkening on top of the post-pass shift | Works, but the yard already has authored contact skirts (`_build_contact_occlusion`). Kept on ULTRA only, conservative |
| `DirectionalLight3D.shadow_blur` 8 vs 1 | 0.000 mean difference | No effect in Compatibility. Not offered |
| Soft-shadow filter quality | Hard vs low 0.26 to 0.30 mean level; ultra vs low 0.49 to 0.76; medium vs low exactly 0.00 | Barely visible and not monotonic in cost. Not offered |
| Directional shadow atlas 4096 vs the project default | 0.000 | The default is already 4096, so there is nothing to raise. 512 changes the picture (mean 1.7 to 2.3 levels), so the atlas setting is live |
| MSAA 2x vs off | Edge error against a 2x supersampled reference: 10.5, 10.7, 9.9 to 5.4, 6.8, 6.3 (views 5, 8, 11) | Real and large |
| MSAA 4x and 8x vs 2x on this host | Identical pixels | llvmpipe does not distinguish them. The ULTRA 4x setting is unverified here; it is a standard GPU feature |

SSAO, the post pass and ambient occlusion are therefore **available** in this renderer. `VISUAL_GAP_ANALYSIS.md` and `RENDERING_PIPELINE.md` said they were not. Both are corrected.

## Quality tiers (`game/scripts/gameplay/graphics_quality.gd`)

| Tier | Shadows | MSAA | Post pass | SSAO | Texture filtering | Where |
| --- | --- | --- | --- | --- | --- | --- |
| 0 LOW | off | off | no | no | trilinear | all platforms |
| 1 MEDIUM | on | 2x | no | no | trilinear | all platforms; the pipeline phones already ran |
| 2 HIGH | on | 2x | yes | no | 4x anisotropic | desktop |
| 3 ULTRA | on | 4x | yes | yes | 16x anisotropic | desktop |

Phones and tablets are capped at MEDIUM until a physical-device frame-time record exists. A profile saved on a desktop keeps its choice and runs the capped tier on a phone.

## Shadow fill (all tiers), measured

The independent critic and a pixel survey agreed that the original ambient (0.41, sun 1.18) left the defender half near black: 19% to 32% of pixels in views 3, 8, 9 were below luminance 40. Variants, all at MEDIUM:

| Variant | Ambient / sun | Views 3, 8, 9: pixels below luminance 40 | Shaded floor p5 luminance (view 9) |
| --- | --- | --- | --- |
| A (before) | 0.41 / 1.18 | 19.4%, 31.3%, 32.3% | 37 |
| B | 0.65 / 1.10 | 1.1%, 2.5%, 0.1% | 45 |
| **C (shipped)** | 0.85 / 1.05 | 0.0%, 0.1%, 0.0% | 52 |
| D | 1.05 / 1.00 | 0.0%, 0.0%, 0.0% | 57, with 1.35% clipped pixels in view 8 |

Across all twelve review views (`m6-final`, mean of per-view fractions):

| Render | Pixels below luminance 40 | Clipped pixels (any channel 250 or more) | Mean luminance |
| --- | --- | --- | --- |
| Before (old MEDIUM) | 14.8% | 0.53% | 99.5 |
| LOW | 0.2% | 0.00% | 106.2 (no shadows) |
| MEDIUM | 0.3% | 0.62% | 111.4 |
| HIGH | 1.3% | 0.10% | 112.3 |
| ULTRA | 1.3% | 0.10% | 112.2 |

HIGH keeps sunlit surfaces from clipping (0.62% to 0.10%) and holds its shadows a little deeper than MEDIUM (1.3% against 0.3% below 40), still far above the old 14.8%. ULTRA's tonal statistics match HIGH's to within 0.1: the ambient occlusion is a small local effect.

C keeps shadows readable as shapes (lit to shaded floor stays near 5:1 in linear light) and does not add clipping. **Operator check.** `game/tests/operator_readability_capture.gd` stands operators of both teams on open floor in the sun and in the shade at 8 to 32 m, renders each frame with and without them, and takes the difference as the silhouette. Weber contrast in linear light, operator against the ring around it (`graphics-tiers-m6/data/operator-contrast-*.json`, same placements both runs):

| Operator | Before (ambient 0.41, sun 1.18) | After (0.85, 1.05) |
| --- | --- | --- |
| Shade, 16.5 m | background 0.041, operator 0.016, Weber -0.62 | 0.064, 0.025, -0.60 |
| Shade, 20.5 m | 0.084, 0.021, -0.75 | 0.105, 0.032, -0.70 |
| Sun, 8.5 to 32.5 m (six operators) | Weber -0.66 to -0.94 | -0.69 to -0.94 |

The fill leaves the contrast ratio of an operator in the shade within 0.05 Weber of before (background-to-operator ratio 2.6 and 3.9 before, 2.5 and 3.3 after) while the absolute luminance difference rises by about 16%: it lifts the dark end without flattening the figure. Operators are darker than the floor in every case, so a shaded floor that was nearly black was where they would have merged. Only two shaded placements exist in the open floor in view of this camera; this is a spot check on a standing fixture, not a visibility study.

## Blind comparison (fresh-context critic, labels removed, key kept outside the review directory)

Set 1, twelve views, the old MEDIUM look against the new MEDIUM (shadow fill): the critic chose the new side in 11 of 12 pairs (high confidence in 2 dark scenes, medium in 5, low in 4). The one loss is view 11, where the critic found blown crate tops; they clip 2.8% of pixels there, as they did before (2.69%), so this is an old defect that stays, not a new one. Regressions it flagged on the new side: highlights 10 to 25 levels hotter, a cooler greyer shade, and a lit-to-shade range about 22% lower (p95/p5 3.4 against 4.5), so the scenes are less moody. Washed-out look, banding, halos and shadow-edge change were not seen.

Set 2, six views, new MEDIUM against HIGH: HIGH won 3 (views 5, 10, 11), 3 ties, MEDIUM won none. The difference is highlight handling only; shadows differ by 5 levels or less, and no pair changes whether a figure can be seen.

Limits: a model from the same family judged stills from a software rasteriser, so it says nothing about motion, shimmer, a real display, or figures in shadow (no player model was in the scene). The pair order was randomised with a seed; the key is `scripts/ab_pair.py`'s output, outside the reviewed directory.

Also tried and rejected: `tonemap_white` 1.5, 2.0 and 3.0 with matching exposure left the clipped fraction unchanged (2.8% in view 11) on MEDIUM, so the single-pass tonemapper has no usable highlight knob. The post pass (HIGH) is the only measured fix.

## Relative cost (software rasteriser, relative only)

Median frame time over 40 frames at each of 12 views, same host and load, llvmpipe at 1280x720: LOW 114 ms, MEDIUM 464 ms, HIGH 450 ms, ULTRA 503 ms (median of the 12 view medians; per-view files `m6-final/tier*-timings.json`). The ordering says MEDIUM, HIGH and ULTRA cost about the same on a CPU rasteriser and LOW is four times cheaper (shadows off). It says nothing about GPU frame time: the post pass and SSAO are bandwidth work that a CPU rasteriser prices differently from a phone or a desktop GPU. A device frame-time record is still owed before any tier is raised on a phone.

## Open defects, ranked (independent critic, 12 stills at MEDIUM before this work)

Scores before: lighting 4, grounding 4, materials 3, edges 5, depth 2, colour structure 4, finish 3. The critic's pixel claims were spot-checked; its "no contact darkening" claim is partly wrong (skirts exist, but fall invisible on the shaded side).

1. Far wall reads as a flat pale slab at the horizon, brighter than the sky (views 8-12). Needs a fogged skyline behind the attacker-end wall.
2. Shadow fill. **Addressed in M6.**
3. Texture moiré: concentric rings on the floor (view 5), radial hatching on the crate top (view 11). Anisotropic filtering added at HIGH and ULTRA; the tiling source texture itself needs rework for MEDIUM and LOW.
4. Contact darkening is one-sided; only sunlit sides show it.
5. Value collapse: black marker box (views 8, 10) matches the shaded floor (the fill lifts it apart; confirmed by the blind critic on pairs 7 and 9). Sunlit crate tops clip on LOW and MEDIUM (2.8% of view 11); the post pass fixes it on HIGH and ULTRA. For MEDIUM the fix is a darker crate-top albedo.
6. Sun disc is a hard-edged sticker with no glow.
7. Flat painted decals (the KEEP CLEAR slab) have hard edges and no wear.
8. Signage turns to noise at range.
9. Crane hook block appears to float in view 9: its two cables are 3.5 cm wide and vanish at 26 m.
10. Unmotivated pale floor strips and a hairline seam.

## Next, in order

1. Operator-in-shadow readability capture, then tune fill if a dark-clad silhouette loses contrast.
2. Skyline behind the attacker-end wall (defect 1) and a soft sun glow (6).
3. Crane cable and hoist fix (9), floor texture rework against moiré (3), decal wear (7).
4. Surface-aware bullet-hole decals (Compatibility supports 8 decals per surface, 64 per view) and impact effects.
5. Weapon art for the Kestrel 9, Vectorline and Longwatch (separate gauntlet).
6. LightmapGI bake for one environment section: baking needs a RenderingDevice, so it must run on a machine with a GPU.
7. Device frame-time baselines (Windows, macOS, Linux, Android, iOS) before any tier is raised on a phone.
