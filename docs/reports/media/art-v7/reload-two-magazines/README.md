# Reload with a second magazine (art-v7)

Native Godot 4.7.2 frames (Xvfb, Mesa llvmpipe, GL Compatibility) and logs from the reload work on `claude/cs2-fidelity-art-production`. **This is not an acceptance and it re-scores nothing**: the weapon-and-arms scores in `docs/art/VISUAL_QA.md` stand until a reviewer who is not me or my subagents re-scores them. Every image is a software-rendered desktop frame, not a phone capture; there is no human review of this work and no listening review of its sound.

Source: the commits of this branch after `68251a0` (the first of them is `d805a90`); the shipped arms GLB is a **full baked build** (`logs/arms-build-full.log`, 3 min 41 s) whose textures are byte-identical to the shipped ones (`textures.py` reproduces them), so only the GLB changed. Its SHA-256 is in `logs/clip_contact.glb.sha256`, and `scripts/test_reload_contact.py` fails if the GLB in `game/assets` is not the one the CSV was made for.

## What the reload now does

1. The support hand leaves the handguard (from the left, in frame), reaches the seated magazine and closes on it.
2. At **UNLATCH (0.24)** the release click plays and the old magazine, which has stayed seated until now, slides out along its well; it clears at 0.32.
3. At **DROP (0.38)** the fingers open and it is let go; it falls (a ballistic fall from the hand's own speed, hidden 0.5 s later, long after it has left the frame).
4. The empty hand goes to the left and a little down, **in frame**. There is no pouch to show, so the **second magazine node** rises out of the closing hand from 0.48 and is held from **ACQUIRE (0.56)**.
5. It is brought up (0.56 to 0.68), lined up, entered (0.74), pushed home and **seated at SEAT (0.80)**, where the seat click plays; the hand stays closed until 0.85 and returns.
6. When the reload ends the two nodes **swap roles**: the replacement is now the magazine in the well, and the next reload extracts that node.

The timing is one list, `game/scripts/gameplay/reload_phases.gd`, which the Blender build reads (by pattern) and the actor uses; a drifted constant fails `weapon_art_test.gd` (negative control N14). Authoritative reload, ammunition and completion (`tick_authority`, `start_reload`) are unchanged.

## What was measured, and what it does and does not show

| Test | Checks | What it shows | What it does not show |
| --- | --- | --- | --- |
| `reload_sequence_test.gd` (headless, in `validate.sh`) | 92 | Two separate nodes; both drawn together; the old one never returns to the well; each magazine slides along its own well (monotonic, on axis within 4 mm, square to the well within 4 degrees at the mouth); the grip is rigid and the base is 80 mm (+-12) from the wrist; clicks fire once each and land within 1 tick (seat) and 2 ticks (release) of the visible part under 60 Hz, 20 Hz and jittered timers (and once each when the timer regresses); reduced motion leaves the gun and hand where they are without it and only removes the tumble; brass bounces on the floor under the port and has none in open air; ammunition, reserve and the timer are identical every tick with or without animation; cancel before / during / after the seat, a round reset, a restart with no idle frame, a weapon swap and back, a remote actor, and the SMG's older click timing and calmed dip | That anything looks like a reload to a person. The in-frame checks use joint origins, not drawn pixels |
| `reload_visibility_test.gd` (native, in `validate.sh` when a display exists) | 8 per run | From a flat-colour identification pass (the part's colour after the depth test): the support hand shows at least 10,000 px in every frame from 0.02 to 0.98 (worst 13,984 at 0.32); whenever the hand is on a magazine the thumb shows at least 100 px (worst 237 at 0.56), at least three of four fingertips show at least 100 px (worst 3 at 0.22, 24 of 24 held frames) and the magazine at least 3,000 px (worst 8,233); the extraction and insertion show the magazine | Contrast: it counts geometry, so **sunlit, backlight and shade give the same numbers** and say nothing about how well the hand reads against the ground in shade. 100 px is 0.01 % of a 1280 x 720 frame; it is a floor against a hidden thumb, not a measure of legibility |
| `scripts/test_reload_contact.py` (on `logs/clip_contact.csv`) | 24 | From Blender, each frame: every digit's tip within 6.5 mm of the held magazine and not more than 2 mm into it (measured: thumb 2.6, index -0.9, middle 1.5, ring 3.5, pinky 2.4 mm; palm 7.5 mm), the thumb 111 degrees round the magazine from the fingers, the left arm 0.0 mm into the rifle and **0.9 mm** into the magazine (limit 1.0), the right arm 1.3 mm into the trigger (the grip solve's aim) | The hand is rigid on the magazine, so every held frame has the same values: the test cannot see a contact that varies. It tests the Blender clip, not the imported one |
| `weapon_art_test.gd` | 166 | The older geometry checks, now on the magazine in the hand and on the shared phases | as above |
| `scripts/reload_negative_controls.py` | 22 controls | Each injected defect is caught by the test meant to catch it, with a summary line saying so (no crash): a single-node replacement, an undrawn replacement, no node swap, a grip 30 mm off, the old magazine returning to the well, reduced motion shrinking the staging, clicks from the authoritative fraction, an early click, a click at the let-go, a double click on a rewind, the wrong sound, brass at the shooter's feet, the animation writing the timer, a drifted phase, the SMG's click and dip regressing, no restart reset, a replacement with no rise, a hand that misses the magazine, the previous grasp that hid the thumb, the previous approach from below the frame, a replacement fetched from below the frame | That the defects listed are the only ones. `logs/negative-controls.log` |

`scripts/validate.sh` ran to completion with these in it (`logs/validate-round-2.log`).

## Defects found on the way, by the new tests and by the independent review

Found by measuring, in the work I had left uncommitted and unbuilt:
- The actor did not parse (`GRAVITY` was already a constant): the previous round's code had never run.
- The replacement node was created from `_viewmodel` before `_viewmodel` was assigned, so it was not created on a first build.
- The old magazine began to move at the grasp, five ticks before the release click (the clip keyed 20 mm of travel into the latch phase).
- A clock correction that went back over the seat clicked it twice.
- The support hand left the picture twice: on the way in (0.06 to 0.10) and on the way out (0.88 to 0.94), because the approach point was 85 mm below the grasp, below the frame; and the empty hand's trip to a pouch below the frame took it off screen for about a quarter of the reload (0.38 to 0.62), with a magazine floating without a hand at 0.56.
- The grasp (palm cupping the base, fingers across at 0 degrees, thumb on the front face) hid the **thumb (0 px) and two fingertips behind the magazine** for the whole hold. The visibility test found it; a search over distal and dorsal directions, knuckle offsets and rolls (80, then 24 builds, filtered by contact, then by pixel counts) produced the shipped grasp.
- Hand pixels fell to 4,476 at 0.32 with the lift at 11 cm; the reload's lift is now 14 cm (`ARMS_RELOAD_OFFSET`), which brings it to 13,984.

Found by the independent read-only review of `d805a90` and answered in the following commit:
- **A1** The contact test depended on an uncommitted CSV: committed here, and bound to the GLB's hash.
- **A2/A3** Removing the reduced-motion scaling and the new click phases applied to every weapon: the procedural weapons keep the 20 % dip and their release-at-start click (tests added).
- **A5/A6** Stale presentation state across a weapon swap and a reload restarted with no idle frame: reset (tests added).
- **B2** Thresholds that could not fail: the hand floor is 10,000 px, and both the old and the replacement magazine must be measured.
- **C1** (opinion, the worst of the review) The replacement popped into an empty hand between two frames. It now rises out of the closing hand over 0.08 of the reload, from fully sunk to held. **I have not had this independently re-reviewed**, and it is still a magazine with no visible source (`sheets/replacement-fetch-frames-62-76.jpg`).
- **A4** (two clicks in one tick share one audio player, so only the seat is heard) is **not fixed**; it needs a client whose first snapshot arrives after the release phase and before the seat.

## Remaining defects. This animation is not finished

1. **The replacement has no visible source**: no pouch, vest or second hand. It rises out of the palm; a critic may still call it a materialisation.
2. **The hand is a glove fist, not a hand.** The thumb and fingertips are present and counted but small (a few hundred pixels each); the review's opinion of the earlier grasp frames, which are this grasp, is that it looks like a carried stick rather than a pinch or a wrap. Hand anatomy is the weakest part of the weapon and was not rebuilt.
3. **No lighting measurement.** The review's opinion is that in backlight and shade the hand, the grip and the magazine are close in value and the empty hand nearly disappears (shade, frames 64 to 72). The earlier value-separation numbers in `VISUAL_QA.md` (gloves 15 to 17 luma in a dark interior, about 6 apart in shade) are unchanged and unmet.
4. **The tan magazine and the tan pistol grip are still alike** in value and colour.
5. **Reduced motion does not scale the rifle's reload staging** (a roll of about 26 degrees and an 11 to 14 cm lift stay) because at a fifth of it the hand fell out of the frame. Whether that is acceptable to a person who asked for reduced motion is a product call.
6. **The clip is sampled every 1/60 of the reload (2.25 ticks)**, so a part can lead its phase by one clip frame (the old magazine is 0.9 mm out a tick before the release click). The contact numbers are at that resolution.
7. **Sound** is two synthesised clicks, synchronised to the animation by measurement, not by listening.
8. **The discard** is a canned fall, slow near the hand; the first-frame and last-frame magazines sit cropped at the bottom edge of the frame.
9. Only the rifle has a rigged reload; the SMG, sidearm and marksman rifle are procedural.
10. **Nothing here is a phone.** Frame cost, thermals, touch feel and legibility on a real screen in daylight are unmeasured.

## Files

| File | Shows |
| --- | --- |
| `clips/reload-<view>.mp4` | The whole reload at 60 Hz, 1280 x 720, every tick (153 frames): sunlit, reduced motion, backlight, shade, and sunlit with the timer arriving at 20 Hz |
| `frames/sunlit-normal/`, `frames/sunlit-reduced/` | Every tick of the two main sequences as 640 x 360 JPEGs (`000.jpg` to `152.jpg`) |
| `sheets/reload-<view>.jpg` | Labelled contact sheets, every 8th tick |
| `sheets/replacement-fetch-frames-62-76.jpg` | The replacement rising out of the hand |
| `sheets/hands-lit-and-identification.jpg` | The lit frame beside the identification frame at three held poses (thumb red, index green, middle blue, ring yellow, pinky magenta, the rest of the hand cyan, the magazine white, the rifle black) |
| `logs/frames-<view>.csv` | Per tick: time, the authoritative timer, the visual progress, which magazine the hand holds, which are drawn, and the click cues with the progress they fired at |
| `logs/visibility-<view>.csv` | Per progress: pixels of each fingertip, the thumb, the rest of the left hand, the right arm and the magazine |
| `logs/clip_contact.csv`, `clip_contact.glb.sha256`, `reload-contact.log` | The Blender contact review, the GLB it was made for, and the test on it |
| `logs/negative-controls.log`, `logs/validate-round-2.log`, `logs/arms-build-full.log` | The 22 injected defects, the full `validate.sh`, the baked build |

To reproduce: `scripts/validate.sh` (with `DISPLAY=:99` under Xvfb for the native test); `scripts/reload_negative_controls.py`; `game/tests/reload_sequence_capture.gd` for the frames; `tools/art/arms_build.py <dir> --rifle game/assets/weapons/relay_ar/relay_ar.glb` for the build, then `python3 tools/art/textures.py <dir> relay_ar_arms <out>` to confirm the textures are unchanged.
