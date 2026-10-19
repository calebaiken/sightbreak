# Rifle materials: a viewmodel lighting environment instead of a roughness floor (Checkpoint A, art-v10)

Branch `claude/cs2-fidelity-art-production`, from `ed85754`. **Evidence: my own native renders and tests on Mesa llvmpipe (GL Compatibility); a same-model review comes at the end of this round; nobody has looked at these on a phone and no human has judged them.**

## Where the v9 fix went wrong

v9 stopped the rifle changing colour in the reload by flooring the first-person metal's roughness at 0.80 and adding a fill floor of 0.26. Three reviews then saw a paler, olive, matte rifle, with the receiver and handguard at the same value (70 and 70 median luma at the ready in sun, against 54.5 at `57f6464`). I took the component breakdown of the v9 receiver at the ready, in sun, by switching terms off (`reload_discolour_probe.gd`): the whole 69.7 was **sun 35** (switching the sun off leaves 34.4), sky reflection 12, ambient 18 (together with the reflection), fill about 9. So the pale olive was not only the reflection: a roughness of 0.80 turns the *sun's* specular lobe into a wide, bright haze over every panel (the same single `ROUGHNESS` drives the sun's lobe and the sky's radiance in the engine), and the warm sun colour on a near-neutral surface is the olive.

## Root cause, restated

The engine reflects the procedural sky, which has a bright horizon band and dark ground, and one roughness controls both the sun's highlight and that reflection. Raising roughness hid the band but flattened the sun's response as well. The fix has to take the *sky radiance* away from the metal, not roughen the metal.

## What changed

- First-person materials (`ViewmodelShading.SURFACE`, the first-person cosmetic finish, so the default and every skin) declare `render_mode ambient_light_disabled`: the engine's sky radiance and ambient light are not applied to them.
- `ViewmodelShading.STUDIO` substitutes the viewmodel's own environment: the arena's flat ambient colour for the diffuse part (so the diffuse look matches the engine's), and a reflection of a small studio (a soft sky-to-ground gradient with no edge, a broad key panel up and to the left, a thin cool strip behind on the right), through Schlick Fresnel with the baked metalness and roughness, the **detail normal** (so bevels and panel lines catch the lobes) and the baked ambient occlusion. A weapon that rolls and lifts moves across a gradient and two soft lobes; it does not slide across a horizon.
- The sun is the engine's again, with the baked roughness (floor 0.30, was 0.80), so highlights are tight and the receiver is a dark graphite.
- The handguard is a polymer part: its own material with a rougher floor (0.62) and 30 % of the baked metalness, so the receiver and handguard differ (machined metal against polymer) instead of being one flat value.
- The arms use the same shader with the studio's reflection turned nearly off (`ARMS_REFLECT` 0.05, sheen 0): fabric must not shine. The fill floor for the metal fell from 0.26 to 0.12 because the studio now supplies the base.
- Inspection and third person keep the engine's own lighting and are unchanged (asserted).

## Measured (sunlit/shade, reload ticks 0, 40, 100, 124, 134 and the 16-tick set; logs in `logs/`)

| | 57f6464 | v9 | v10 |
| --- | ---: | ---: | ---: |
| receiver at the ready, sun / shade (median luma) | 54.5 / 29 | 69.7 / 34.4 | 54.6 / 28.4 |
| receiver, highest over lowest through the reload, sun / shade / skin | 1.52 / 1.75 / 1.68 | 1.18 / 1.14 / 1.18 | 1.20 / 1.14 / 1.20 |
| receiver hue shift, (r - b) / luma from the first tick, sun | 0.094 | 0.034 | 0.015 |
| receiver / handguard in the dark interior at the ready | | 27.6 / 30.2 | 28.6 / 31.2 |
| gloves / sleeves in sun, grab pose | | 0.76 | 0.77 |
| grip / receiver in sun, ready | | 0.56 to 0.76 | 0.63 |

The 1.25 stability bound, the 0.06 hue bound, the 0.85 / 0.78 / 22 separation bounds and the 15 visibility rules are **unchanged** from v9 (they were derived from measured data in earlier rounds; none was touched). v10 sits near the 1.25 bound in sun (1.20) because the sun alone swings the receiver by 1.27 from the ready to the rolled pose (25 to 32 luma with the studio off): that is the legitimate illumination change as the weapon turns toward the sun, and it is not removed.

## What it looks like (`frames/`)

`before-after-*.jpg` (57f6464, v9, v10; ticks 0, 36, 98, 118, 124, 136; sun, shade, backlight), `receiver-zoom-sunlit.jpg` (cropped, the three builds at the ready and in the roll), `v10-stills-backlit-shade-skin-inspection.jpg` (backlit ready, firing, the hall in shade, a Crimson Archive skin in the first person, the inspection view). In sun the receiver reads as dark graphite with soft highlights along bevels and slots, the same colour through the roll; the olive cast is gone (hue shift 0.015); the handguard is softer; a skin reads as a skin.

## Trade-offs and what is still wrong

- **The studio is fixed.** The viewmodel no longer reflects the world: a red wall next to the weapon will not tint the metal. The diffuse ambient is the arena's constant colour (as before: the arena's ambient is a flat colour). If another map uses a different ambient, `viewmodel_ambient` has to follow it (it is a uniform; nothing sets it yet). That is the price of a stable metal, and I judged it the right one for a competitive weapon.
- The highlights are subtle at gameplay size; the metal reads as *graphite*, not polished steel. A brighter key lobe makes the gloves look like latex (tried, rejected: sheen 15).
- **Correction (found after the first write-up, from an independent review of `5357329`):** this section first said the receiver and handguard were level in sun (54.6 and 56.6). Those handguard numbers came from `reload_discolour_probe.gd`, which assigned the receiver's finish to both paint parts and so measured a handguard that does not ship. Measured on the shipped nodes (`viewmodel_light_probe.gd`, ready pose): **sun receiver 54.6, handguard 67.6; shade 28.4 and 29.7**. So the polymer handguard is about 13 luma brighter than the receiver in sun and the two are level only in shade. The probe now starts every case from the shipped materials (the finish-stability bounds still pass: receiver ratio 1.20, handguard 1.18).
- The glove-to-sleeve ratio in sun is 0.77 against a 0.78 bound (v9: 0.76): the arms' reflection had to be turned down to 0.05 to hold it.
- The flash light, the muzzle smoke and the procedural-fallback shaders were not touched.
- Nothing about a phone's GPU: the STUDIO adds three `pow`, two `normalize`, one `smoothstep` and a TBN reconstruction per fragment on first-person surfaces; I have not measured it on a device.
