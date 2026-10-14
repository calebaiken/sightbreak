# The reload, the support hand, the bore and the effects

Frames are Godot 4.7.2 on Xvfb with Mesa llvmpipe (GL Compatibility), 1280 × 720 unless a file says otherwise, from `game/tests/weapon_motion_capture.gd` (a fixed 60 Hz simulation step, one frame per two steps) and `game/tests/reload_legibility_probe.gd`. They are software-rendered desktop frames, not phone captures, and the motion sequences show the animation's design, not smoothness on a device. `sha256.txt` hashes every file.

**This is not an independent review and scores nothing.** Every number below is something the probe or a test measured; the judgement of how it looks is still owed by a reviewer who is not me or my subagents.

## What the previous review found, and what it measured at `233df74`

The review of `b507205` said the support forearm covered the magazine at the grasp and the seat, the hand opened before the magazine was seated, and the bore pointed sideways. I had no numbers for any of them, so I wrote a probe first (`reload_legibility_probe.gd`). It renders the reload and, at each progress, hides the arms and then the magazine to count pixels. Its baseline on `233df74`:

| Over the reload | At `233df74` |
| --- | --- |
| Magazine on screen, mid-swap (0.30 to 0.70) | as little as **11 %** of its silhouette (it left the bottom of the frame) |
| Magazine covered by the arms at the grasp (0.14 to 0.20) | up to **87 %** |
| Magazine covered at the seat (0.76 to 0.84) | up to **91 %**; 996 pixels of it visible at the seat |
| Covered pixels, by who covers them | the **sleeve**, not the glove: 55 to 90 % sleeve and 0 to 16 % glove (measured with the v4 grasp on the new carry path, because the attribution was added to the probe after the baseline run) |
| Bore at the ready pose | the bore line passes **56 px below** the crosshair; its vanishing point is 124 px left (10.0°); the muzzle is 119 px right and 97 px below |

I recorded the acceptance targets before changing anything: magazine at least 90 % on screen throughout; at most 35 % covered at the grasp and the seat; at least 4,000 px visible from the grasp on; the arms no larger on screen than they were (a guard I added after the first attempt below); bore line within 15 px of the crosshair.

## What changed

| | |
| --- | --- |
| **The reload** | A mechanical sequence: the hand leaves the handguard and comes up to the seated magazine **from below** (it no longer crosses the magazine on a straight line), cups its base, closes, slides the magazine out along its own well (axis from the model's geometry, not a straight drop), lifts it out to the rifle's left and shows it, brings it back, lines it up, enters, pushes it to its stop at **0.80**, stays closed on it until **0.85**, and only then opens and returns. The magazine is posed from the hand bone while the hand holds it (`Actor._pose_magazine`), so the two cannot drift apart. It is the same magazine mesh: there is no second magazine, so "bring the replacement" is the same magazine shown and re-seated. |
| **The grasp** | The v4 grasp put the palm on the magazine's left face; from the camera's side of the rifle the forearm then lay along the line of sight. The hand now cups the base from below, fingers up the right face, so the forearm hangs below and behind. |
| **Bore** | The rifle is turned 6.9° outward and 2.9° up about its balance point (`relay_ar_rotation` and `relay_ar_offset`, computed so the rest pose of the hands barely moves). |
| **Palette** | The jacket's median luma in sun fell from 146 to 110, and it is a muted olive-drab instead of chartreuse. The gloves are 25 % lighter in linear terms. The rifle's unpainted parts (furniture, magazine, metal) are drawn at 60 % saturation and 0.84 gain by the first-person shader; nothing was re-baked and inspection is unchanged. |
| **Sleeve mesh** | 32 segments by 20 rings (was 20 by 16): the hem no longer shows a sawtooth. The arms are 9,204 triangles (budget 10,000). |
| **Fingers** | The cupped hand's fingers are fanned a little (`GRAB_FAN`) so they do not fuse into one mass from the side. |
| **Muzzle flash** | One layered additive mesh of 213 triangles (hot teardrop core, soft bell, five streaks, four side flares, a glow disc), fading to nothing at every outer edge. Each shot has its own turn, length and width, and the flash shrinks over its 40 ms. The star is gone. |
| **Casings** | A lathed brass case (rim, groove, tapered body, shoulder, neck, an open mouth that is dark inside) instead of a six-sided prism. It tumbles about its own axis, bounces off the floor (it lies still after at most four contacts), settles and fades. |
| **Import setting** | `relay_ar_arms.glb.import` resampled the clip to 30 fps. Seat and let-go keys on the 60 fps grid were interpolated between frames, so the hand drifted 3 to 4 mm while it should have held. Now 60. |

## Results against the targets

Magazine on screen, covered by the arms, and visible pixels, sunlit, from `logs/reload-legibility-*.log` (every 0.02 of the reload):

| | `233df74` | now |
| --- | ---: | ---: |
| Magazine on screen, whole reload (0.10 to 0.90) | ≥ 0.11 | **≥ 0.94** |
| Covered at the grasp (0.14 to 0.20) | ≤ 0.87 | **≤ 0.01** |
| Covered at the seat (0.76 to 0.84) | ≤ 0.91 | **≤ 0.01** |
| Visible magazine pixels, grasp to let-go | ≥ 996 | **≥ 9,248** |
| Arm area on screen | ≤ 94.6k px | ≤ 90.6k px |
| Bore line against the crosshair | 56 px below | **1 px above** |
| Bore vanishing point | 124 px left, 10.0° | 38 px left, 21 px above, 3.5° |

Backlight, shade and the two other canvases give the same readings (`logs/reload-legibility-after-*.log`). The 1600 × 720 and 1024 × 768 frames are what a wider or taller canvas would frame; **they are not shipped behaviour**: `project.godot` keeps the 16:9 frame with bars (`docs/art/WEAPON_PRODUCTION.md`).

**Contact** (`logs/clip_contact.csv`, from `arms_build.py`'s `review_clip`, at each of the clip's 61 frames): the deepest vertex of either arm inside the rifle or the moving magazine is **0.0 mm** for the left arm. The right arm's trigger finger rests 1.3 mm into the trigger, which the grip solve aims for and which is unchanged. (My first measurement of the clip with the old grasp read 4.5 mm into the rifle and 3.2 mm into the magazine; the shipped `233df74` clip had no contact review at all.)

**Median luma per part** (`logs/light-before.log` and `light-after.log`; sRGB-encoded 0 to 255, by hiding each part and counting the pixels that change):

| Scenario, pose | Magazine | Receiver | Handguard | Furniture | Gloves | Sleeves |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Sun, ready | 120 → 117 | 53 → 53 | 72 → 72 | 72 → 70 | 85 → 89 | **146 → 110** |
| Sun, mid reload | 146 → 143 | 78 → 78 | 93 → 93 | 81 → 80 | 82 → 86 | **145 → 110** |
| Shade, ready | 46 → 45 | 25 → 25 | 45 → 45 | 34 → 34 | 30 → 32 | 50 → 38 |
| Dark interior, ready | 26 → 25 | 24 → 24 | 42 → 42 | 27 → 27 | 16 → 17 | 26 → 20 |

Two outcomes cut against the change and are recorded as they are. **The sleeve is now darker in shade, so its separation from the glove shrank** from about 20 luma to about 6 in shade and backlight (50 against 30 became 38 against 32); the two still differ in hue, but the value gap is weak there. **Gloves in a nearly dark interior are 15 to 17, still under the 20 I set** in the lighting report; lifting the albedo moved them 0 to 2.

## Tests

`weapon_art_test.gd` went from 111 to **164 checks** (in `validate.sh`; the whole suite passes, `logs/validate-art.log`). New: the phase boundaries; the magazine seated and still while the hand reaches; on its well's axis within 4 mm while it slides; cleared by 32 %; carried out to the left; lined up and not yet in at 69 %; entering at 75 %; seated within 0.5 mm at 80 %; hand and magazine unmoving, **fingers closed (under 1°) from the seat to the let-go**; fingers open after it; fingers never loosening between the grasp and the seat; no teleports (hand under 4.5 m/s, magazine under 1.5 m/s, over 540 steps); the seat sound neither before nor after the seat; the flash mesh (triangle range, fades to nothing wherever wider than 5 cm, reach, hot core, additive shader, shared by procedural weapons); per-shot variation and the 40 ms envelope; the casing mesh (size, dark mouth); and the casing's floor bounces, settling, and that a resting casing stays put.

**Negative controls** (`logs/negative-controls.log`): five defects injected one at a time, each restored byte for byte, each failing the suite: the magazine released from the hand halfway (3 failures), the grip offset measured at the wrong moment (17), a flash lobe ending on an opaque edge (1), casings that never settle (2), and a clip that lets go of the magazine at 0.77 before the seat at 0.80 (7).

## Defects in my own work, found by measuring or looking

1. **I gamed my own metric first.** Pitching the rifle nose-down scored "covered 13 %" by swinging a flat-ended sleeve stump across the left half of the screen (arm area 95k to 176k px). The sheet showed it. I rejected it and added the arm-area guard; the probe prints that column so a score cannot be read alone.
2. **The importer's 30 fps resample blurred the seat** (above). Found because the test said the magazine was 3.9 mm off at the seat while the clip said it was exact.
3. **A resting casing re-bounced every frame** (gravity pushed it into the floor, bounce count 6, then 23 in the control). Fixed with an explicit resting state.
4. **The first flash burned to a white ball** (overlapping additive layers summed past 1), then showed an octagonal gem outline (the widest ring still had alpha). Each lobe's widest ring is now fully transparent.
5. **A test gave a false failure from random throws**; the effects RNG is seeded in the test.

## Not done, and open

- **Grip hand:** still reads as a mitten and the support fingers still crest the rail at the handguard hold; only the cupped grasp's fingers were changed. The thumb is not visible in the cupped grasp.
- **Glove detail** (panels, seams, knuckles, creases): unchanged from v4; at this size the existing detail is not what limits the read.
- **The pistol grip** is still a flat tan block (the rifle model is unchanged); only its colour is calmer.
- **Gloves in the dark interior** (15 to 17 against 20) and the **weak sleeve-to-glove value gap in shade** (above).
- **Bore:** moved from 10.0° to 3.5° off, not to the crosshair. The earlier "v4" layout that put it nearer was rejected for foreshortening the handguard; this is a smaller step, and I judged it on the frames in `bore-before-after.jpg`, which is my judgement.
- **Casings** are cosmetic particles: there is no bolt or charging-handle animation, and the flash is a mesh, not a light.
- **Draw and inspect animations**, a second magazine mesh, reload sound design and reduced-motion review are not done.
- **Phone performance is UNVERIFIED.** The flash adds a draw only for 40 ms and the casing pool is one draw of at most 24 instances, but nothing here was measured on a device.
- **Independent review** of these frames has not happened.

## Files

| File | Shows |
| --- | --- |
| `reload-before-233df74.jpg` | The reload as it was: the arms cover the magazine at the grasp and the seat and it leaves the frame mid-swap |
| `reload-after.jpg` | The new reload, twelve points from the reach to the return |
| `reload-backlight-shade.jpg` | The grasp, the carry and the seat in backlight and shade |
| `reload-other-canvases.jpg` | The same at 1600 × 720 and 1024 × 768 (hypothetical canvases, not shipped behaviour) |
| `support-hand-closeups.png` | The cupped hand at the seat and carrying the magazine, 2× |
| `bore-before-after.jpg` | The ready pose before and after, crosshair marked |
| `firing-burst.jpg`, `muzzle-flash-closeups.png` | A burst: the flash differs shot to shot; brass cases tumble out of the port |
| `logs/` | Probe sweeps before and after, per-part luma, the contact review, the full arms build, the negative controls, `validate.sh` |

Reproduce: `docs/art/ASSET_PIPELINE.md`, "The reload review loop".
