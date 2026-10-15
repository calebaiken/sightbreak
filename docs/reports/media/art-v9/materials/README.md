# Materials and lighting, round 4 (art-v9): gloves, grip, painted metal

Branch `claude/cs2-fidelity-art-production`, from `46626c7`. **Evidence: my own native renders and probe numbers (llvmpipe, GL Compatibility); an independent same-family review comes at the end of the round; nobody has looked at these on a phone.** "Dark interior" is the shade view with the sun at 8 % and the ambient light at 30 % (a simulation: the sky is still bright in the frame).

## What was wrong, as measured

1. **The gloves read as bare skin in sun** because the dark albedo was not most of what the eye saw: a glove's median luma in sun was 89 to 91 where its albedo, the sun and the ambient light account for about 59. The rest was additive: dielectric specular (the engine's default 0.5 puts a pale sheen on a rough, dark surface), sky reflection, rim and fill. The arms-wide probe attributes 9 luma to the sky reflection, 4 to the fill, 2 to the rim; the sun, specular included, is about 64 of the 104. Zone colour contrast on the glove (Checkpoint B) was invisible under it.
2. **The roughness floor of Checkpoint A took the sheen off the painted metal**, which was most of the receiver's and handguard's value in the dark: handguard 44 → 18 and receiver 26 → 17 at the ready pose in the dark interior, 63 → 33 in backlight. The rifle was dissolving into the dark. I caused this and found it with the probe.
3. **The grip was level with the receiver in shade** (24.9 against 26.2 at the ready pose): its luma was almost all specular and ambient, not its albedo (darkening the albedo to 0.3 changed it by 1.6 luma).

## What changed

| | before | after |
| --- | --- | --- |
| arms: dielectric specular (`viewmodel_specular`, new) | engine default 0.5 | 0.25 |
| arms: rim | 0.40 | 0.25 |
| arms: fill strength (`viewmodel_floor`) and albedo lift | 0.10 and 0.35 | 0.14 and 0.50 |
| painted metal: fill strength (`ViewmodelShading.METAL_FLOOR`, new) | 0.10 | 0.26 (replaces the removed sheen with a constant) |
| pistol grip albedo factor over its baked graphite | 0.30 | 0.24 |

Chosen from three sweeps (`logs/` in the scratch of this round is summarised here): specular 0.25 alone darkened the gloves in shade (34 → 26) so the fill came up with it (a floor of 0.14 holds the gloves at 32 in shade and gives 24 in the dark interior, from 20); the painted metal's floor was tried at 0.18, 0.26 and, with a lift of 0.5, a higher one, and 0.26 returns the dark-interior rifle to about its old value without lifting the sun lighting by more than 6 luma.

## Median luma of each part's own visible pixels (0 to 255; `logs/light-probe-v9.txt`; before is `art-v8/reload-hip-retrieval/logs/light-probe-after.txt`)

| lighting, pose | state | magazine | receiver | handguard | furniture | grip | gloves | sleeves | gloves / sleeves | grip / receiver |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| sun, ready | before (57f6464) | 118 | 55 | 74 | 66 | 54 | 91 | 113 | 0.81 | 1.00 |
| sun, ready | after | 118 | 70 | 70 | 65 | 53 | 77 | 105 | 0.73 | 0.75 |
| sun, grab | before (57f6464) | 135 | 81 | 104 | 52 | 51 | 89 | 112 | 0.79 | 0.63 |
| sun, grab | after | 135 | 82 | 82 | 52 | 49 | 79 | 104 | 0.76 | 0.60 |
| backlight, ready | before (57f6464) | 53 | 33 | 63 | 42 | 26 | 35 | 41 | 0.87 | 0.78 |
| backlight, ready | after | 53 | 35 | 39 | 42 | 25 | 33 | 41 | 0.81 | 0.71 |
| backlight, grab | before (57f6464) | 57 | 55 | 83 | 30 | 27 | 37 | 42 | 0.90 | 0.49 |
| backlight, grab | after | 57 | 39 | 42 | 30 | 26 | 34 | 41 | 0.81 | 0.67 |
| shade, ready | before (57f6464) | 46 | 26 | 46 | 33 | 25 | 34 | 40 | 0.84 | 0.94 |
| shade, ready | after | 46 | 33 | 35 | 33 | 24 | 32 | 40 | 0.81 | 0.73 |
| shade, grab | before (57f6464) | 53 | 45 | 67 | 32 | 28 | 33 | 40 | 0.82 | 0.62 |
| shade, grab | after | 53 | 38 | 40 | 32 | 27 | 32 | 40 | 0.82 | 0.71 |
| dark interior, ready | before (57f6464) | 26 | 26 | 44 | 28 | 14 | 20 | 23 | 0.89 | 0.54 |
| dark interior, ready | after | 26 | 25 | 28 | 28 | 14 | 24 | 28 | 0.88 | 0.56 |
| dark interior, grab | before (57f6464) | 32 | 45 | 69 | 22 | 15 | 20 | 23 | 0.89 | 0.34 |
| dark interior, grab | after | 32 | 30 | 32 | 22 | 15 | 24 | 27 | 0.88 | 0.52 |

## What this shows, and what it does not

- **Gloves in sun** are 12 to 14 luma darker (91 → 77 at ready), which is the "skin" reading reduced; in shade and the dark interior they are no darker (34 → 32) or a little lighter (20 → 24). Look at `frames/lightings-grab-before-after.jpg` and `-ready-`: in sun the cupped support hand reads as a graphite glove with a stitched cuff, where before the pale sheen flattened it. In shade and the dark the arms are still a low-contrast mass, outlined by the rim; that is not solved.
- **Glove-to-sleeve value separation did not improve in shade or the dark** (0.82 and 0.88 before and after). It improved in sun (0.81 → 0.73) and backlight (0.87 → 0.81). In the dark they separate by hue, if at all.
- **Grip against receiver** is now at most 0.75 in every lighting at the ready pose (it was 1.00 in sun and 0.94 in shade), and 0.52 to 0.71 at the grab. Part of that is the receiver being lit better in the dark, not the grip getting darker; the grip itself moved by 1 luma at most (54 → 53 in sun), because its luma was never mostly albedo. **The grip is still defined by value only.** I tried no hue or rim separation for it in the shipped build.
- **The receiver and handguard lost their highlight response.** At the grab pose the handguard is 104 → 82 in sun, 83 → 42 in backlight, 67 → 40 in shade: the rifle's metal is a matte graphite with a constant fill, steadier through the reload (Checkpoint A) and flatter. The brief asked for a better receiver highlight response; **I traded it for stability and did not get it.** A designed highlight (an edge or a fixed studio reflection) is the next step and I did not build one.
- The probe measures median luma; it cannot see hue or form, and the frames are what I judged those by.

## Tests and controls

- `viewmodel_light_probe.gd --assert` (in `scripts/validate.sh`): the grip is at most 0.85 of the receiver in every lighting and pose measured; the gloves are at most 0.78 of the sleeves in sun; the receiver and handguard are at least 22 in the dark interior. **All three bounds were set from this round's measurements** (before: grip/receiver 1.00 and 0.94 at the ready pose; gloves/sleeves 0.79 to 0.81 in sun; receiver/handguard 17 and 18 in the dark before the fill), so they guard a measured state and are not a visual standard.
- `weapon_art_test.gd` (+2 checks, 171 in all): the painted metal's fill floor is set and above the rest of the viewmodel's; the arms carry a specular below the engine's default and their own fill.
- Negative controls N28 (grip not darkened), N29 (no metal fill floor), N30 (arms back to the engine's specular): 3 of 3 caught, each by the light test (N29 and N30 also by the weapon-art test) (`logs/negative-controls.txt`; run without the baseline, which `validate.sh` covers).
