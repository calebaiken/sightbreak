# Relay AR arms v3: evidence

Every image is a real render of commit `5100b3e` (rigged arms, viewmodel projection). `sha256.txt` hashes every file in this folder.

- **In-engine captures:** Godot 4.7.2 on Xvfb with Mesa llvmpipe (software), from `game/tests/weapon_art_capture.gd`. They are fixture poses, not played matches, and not phone photographs.
- **Review renders:** Blender 5.2.2 Cycles (CPU, 32 samples, Standard view transform, studio lights), from `tools/art/render_arms.py`. They use the shipped GLBs and the shipped 1024 texture sets, not the high-poly sources.
- **Motion:** `motion/` is a real frame sequence from `game/tests/weapon_motion_capture.gd`, with the trigger held and then a reload. It drives the actor through its own `tick_authority` and `tick_visual` (the calls the match makes) at a fixed 60 Hz simulation step and captures one frame per two steps, with `--fixed-fps 30` so the rest of the scene also advances 1/30 s per frame. That is 30 fps of *simulated* time; llvmpipe renders far slower than real time, so this shows motion design, not smoothness on a device.

| Folder | Contents |
| --- | --- |
| `captures/` | 1280×720: backlit yard ready (01), firing (02), reload at 44 % (03), reload at the support-hand grab (03b); sunlit yard (04); transfer-hall shade (05); sunlit with the Crimson Archive skin (06); the inspection studio with the skin (07) |
| `aspect/` | 01, 03b and 05 at 1600×720 (20:9) and 1024×768 (4:3). The capture sets the root viewport to that size, so these show what a wider or taller canvas would frame. **They are not what ships:** `project.godot` uses `canvas_items` stretch with the default "keep" aspect, so a 20:9 or 4:3 screen shows the 16:9 frame with bars. Whether to switch to "expand" is an open decision for the project owner and Codex. |
| `compare/` | Half-scale before/after sheets: left is `2bba519` (static v2 hands, world projection), right is `5100b3e` |
| `renders/` | Cycles, JPEG quality 92: `eye_54` (the in-game camera at the 54° viewmodel field of view, grey studio), `right_34`, `left_34`, `firing_hand`, `firing_hand_left`, `support_hand`, `support_hand_right`, and two reload frames (`reload_grab` at 14 %, `reload_down` at 45 %) with the magazine on the game's drop curve |
| `motion/` | `5100b3e-sunlit-fire-reload.mp4` (H.264, 1280×720, 115 frames, 3.8 s) and `.gif` (640 px, 15 fps); `5100b3e-sunlit-sheet.png` (16 labelled frames from `tools/art/motion_sheet.py`); `5100b3e-sunlit-frames.csv` (per frame: time, phase, ammunition, reload remaining, clip time, magazine offset, kick) |
| `logs/` | `arms-build.log` (bake, placement and grip-solve report from `tools/art/arms_build.py`), `validate-5100b3e.log` (the first `validate.sh` run, summary) and `validate-5100b3e-rerun-full.log` (the full re-run before publishing: exit 0, 3,144 counted native assertions, the 10-round bot lifecycle match and two ENet clients), `benchmark-5100b3e.log` (software-render relative cost; see `docs/art/PERFORMANCE_REPORT.md`) |

## Blocking regression in `5100b3e`, found by the review and fixed

**`captures/07-inspection-skin.png` shows a rifle without its receiver and handguard.** I published that frame without noticing. The v3 review caught it.

- **Cause:** `5100b3e` put the viewmodel projection snippet into the shared cosmetic shader. That snippet wrote `POSITION` only when `viewmodel_fov > 0`. A shader that writes `POSITION` anywhere makes Godot skip its own vertex transform and start from `vec4(1.0)`, so with the field of view at 0 every vertex of a painted part collapsed to one point.
- **Where it hit:**
  - the inspection studio (inventory and marketplace previews);
  - the case reveal's reward;
  - the painted parts of the procedural sidearm, SMG and marksman rifle in first person.
- **Fix:** the world and inspection finish is again the exact pre-v3 shader, and only a separate first-person variant carries the projection. The projection snippet also falls back to the camera's own projection if the field of view is ever unset.
- **Evidence (`fix-position/`):**
  - `07-inspection-skin-5100b3e.png` against `07-inspection-skin-fixed.png`.
  - `paint-visibility-*.log`: `game/tests/paint_visibility_test.gd`, a native-display pixel test, renders each case, hides the paint parts, renders again and counts the changed pixels.

    | Case | `5100b3e` | Fixed |
    | --- | ---: | ---: |
    | Inspection with the skin | **0** | 59,824 |
    | Inspection with the default finish | **0** | 56,548 |
    | Procedural first-person sidearm | **0** | 11,716 |
    | Authored first-person rifle | 39,736 | 39,736 |

  - `validate-fixed.log`: `validate.sh` on the fix, exit 0. `weapon_art_test` is now 69 checks; its 5 new checks fail on the bug (negative control: 4 failures naming `paint_receiver`, `paint_handguard` and the sidearm's paint mesh).
- **Not regenerated:** the other captures in this folder show `5100b3e`. Its first-person frames used the viewmodel variant, which the fix does not change; the pixel test measures the same 39,736 pixels for the first-person rifle before and after.

## Reload staging after the review (`staged-reload/`)

**What changed:** with the rigged arms the rifle now goes into a held reload pose before the support hand reaches the magazine. It lifts 9 cm, moves 5 cm toward the centre, tips the muzzle up 0.05 rad and rolls 0.45 rad clockwise. It holds that pose until the magazine is seated, then returns (`actor.gd`, `ARMS_RELOAD_OFFSET` and `ARMS_RELOAD_ROTATION`). The pose was chosen by projecting the magazine and the support wrist through the viewmodel projection across the reload. The fallback weapons keep their previous reload motion exactly.

**What the evidence shows:**

| Moment in the reload | `5100b3e` | Now |
| --- | --- | --- |
| 14 % (the grab) | Wrist at y = 1.01, magazine bottom at 1.19: below the frame | Wrist at 0.80 and the whole magazine in frame (bottom at 0.96) |
| Mid-swap | Hand and magazine out of frame | Hand and magazine out of frame (unchanged) |
| 84 % (the seat) | Below the frame | Both back in frame |

- `sunlit-*` and `backlit-*` are motion sequences from `weapon_motion_capture.gd`: MP4, labelled sheet and per-frame CSV, plus a GIF for the sunlit view.
- `03-*` and `03b-*` are the new reload stills.
- `weapon_art_test.gd` (69 → 73) pins the staging: the wrist and the magazine bottom are inside a 16:9 frame at 14 % and 84 %, and the buffer tube's end face stays out of frame. With the old pose restored, the two framing checks fail (wrist y = 1.01 and 0.97, magazine bottom 1.19 and 1.15).
- `validate-staged.log`: `validate.sh`, exit 0.

**Still wrong in these frames:**
- At the grab the support hand is an open palm in front of the magazine, not closed on it. The grab solve's thumb and pinky are unresolved; this is part of the arms rebuild.
- The buffer tube's dark rear section runs off the right edge during the reload; only its end face is kept out of frame.
- In backlight the magazine is near-black at the bottom left of the frame.

## Placement evaluation (`placement-eval/`)

The review measured the bore's vanishing point 125 px left of the crosshair and the support hand 0.88 m from the eye. I fitted alternatives with `viewmodel_fit.py --layout v4`, which weights the vanishing point and caps the reach, and rendered them in engine:
- `v3-vs-reach-0.62.png`: shipped v3 against a 0.62 m reach cap. The rifle fills the right half and the optic blocks the view.
- `v3-A-B-weapon-crops.png`:
  - v3;
  - candidate A, vanishing point 102 px left: nearly identical to v3;
  - candidate B, vanishing point 9 px from the crosshair: the rifle points into the screen, the handguard foreshortens and the support hand sits at the muzzle.

**Decision:** keep the v3 placement and record the vanishing point as a known trade-off. Uniformly scaling the viewmodel and its distance gives the same image, so the reach in metres is not visible by itself. The "locked arm" look comes from the forearm's angle in frame, which the arms rebuild addresses through the elbow direction. This is my judgement, not a reviewer's acceptance.

## What these images show that is still wrong

These are my own observations of these frames. The independent review is separate (`docs/art/VISUAL_QA.md`).

- **The reload grab is not legible in first person.** In `03b` the weapon cants and the magazine and the support hand are below the frame, so the player never sees the hand reach the magazine. The motion sequence confirms it: the support hand leaves the handguard at clip time 0.04, is below the frame from about 0.16 to 0.81 (frames 46–90, 1.5 s of the 2.25 s reload), and returns at 0.93. The magazine is never visible during the swap. The Cycles `reload_grab` render shows the hand near the well, not closed on the magazine: the grab solver left the pinky and thumb unresolved (`grab pinky None`, `grab thumb None` in `arms-build.log`).
- **The firing hand is mostly off-screen** at the bottom right, and the right forearm is not visible.
- **The gloves read tan or skin-like** in sun and backlight in-engine, though the albedo is dark. The view floor and rim lift them. The v2 gloves on the left of `compare/01` read darker; on glove value this is a regression.
- **The thumbs are thick and sausage-like** in the close renders.
- **The support forearm is a long, near-uniform olive tube** from the bottom edge. The fold detail is in the normal map only and is barely visible at 1280×720.
- **The rifle is unchanged** from slice 1: about 25k triangles, slab-sided forms, and a UV atlas that still spends area on the stock.
