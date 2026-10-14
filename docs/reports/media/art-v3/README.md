# Relay AR arms v3: evidence

Every image is a real render of commit `5100b3e` (rigged arms, viewmodel projection). `sha256.txt` hashes every file in this folder.

- **In-engine captures:** Godot 4.7.2 on Xvfb with Mesa llvmpipe (software), from `game/tests/weapon_art_capture.gd`. They are fixture poses, not played matches, and not phone photographs.
- **Review renders:** Blender 5.2.2 Cycles (CPU, 32 samples, Standard view transform, studio lights), from `tools/art/render_arms.py`. They use the shipped GLBs and the shipped 1024 texture sets, not the high-poly sources.
- **Motion:** `motion/` is a real frame sequence from `game/tests/weapon_motion_capture.gd`, with the trigger held and then a reload. It drives the actor through its own `tick_authority` and `tick_visual` (the calls the match makes) at a fixed 60 Hz simulation step and captures one frame per two steps, with `--fixed-fps 30` so the rest of the scene also advances 1/30 s per frame. That is 30 fps of *simulated* time; llvmpipe renders far slower than real time, so this shows motion design, not smoothness on a device.

| Folder | Contents |
| --- | --- |
| `captures/` | 1280×720: backlit yard ready (01), firing (02), reload at 30 % (03), reload at the support-hand grab (03b); sunlit yard (04); transfer-hall shade (05); sunlit with the Crimson Archive skin (06); the inspection studio with the skin (07) |
| `aspect/` | 01, 03b and 05 at 1600×720 (20:9) and 1024×768 (4:3). The capture sets the root viewport to that size, so these show what a wider or taller canvas would frame. **They are not what ships:** `project.godot` uses `canvas_items` stretch with the default "keep" aspect, so a 20:9 or 4:3 screen shows the 16:9 frame with bars. Whether to switch to "expand" is an open decision for the project owner and Codex. |
| `compare/` | Half-scale before/after sheets: left is `2bba519` (static v2 hands, world projection), right is `5100b3e` |
| `renders/` | Cycles, JPEG quality 92: `eye_54` (the in-game camera at the 54° viewmodel field of view, grey studio), `right_34`, `left_34`, `firing_hand`, `firing_hand_left`, `support_hand`, `support_hand_right`, and two reload frames (`reload_grab` at 14 %, `reload_down` at 45 %) with the magazine on the game's drop curve |
| `motion/` | `5100b3e-sunlit-fire-reload.mp4` (H.264, 1280×720, 115 frames, 3.8 s) and `.gif` (640 px, 15 fps); `5100b3e-sunlit-sheet.png` (16 labelled frames from `tools/art/motion_sheet.py`); `5100b3e-sunlit-frames.csv` (per frame: time, phase, ammunition, reload remaining, clip time, magazine offset, kick) |
| `logs/` | `arms-build.log` (bake, placement and grip-solve report from `tools/art/arms_build.py`), `validate-5100b3e.log` (the first `validate.sh` run, summary) and `validate-5100b3e-rerun-full.log` (the full re-run before publishing: exit 0, 3,144 counted native assertions, the 10-round bot lifecycle match and two ENet clients), `benchmark-5100b3e.log` (software-render relative cost; see `docs/art/PERFORMANCE_REPORT.md`) |

## What these images show that is still wrong

These are my own observations of these frames. The independent review is separate (`docs/art/VISUAL_QA.md`).

- **The reload grab is not legible in first person.** In `03b` the weapon cants and the magazine and the support hand are below the frame, so the player never sees the hand reach the magazine. The motion sequence confirms it: the support hand leaves the handguard at clip time 0.04, is below the frame from about 0.16 to 0.81 (frames 46–90, 1.5 s of the 2.25 s reload), and returns at 0.93. The magazine is never visible during the swap. The Cycles `reload_grab` render shows the hand near the well, not closed on the magazine: the grab solver left the pinky and thumb unresolved (`grab pinky None`, `grab thumb None` in `arms-build.log`).
- **The firing hand is mostly off-screen** at the bottom right, and the right forearm is not visible.
- **The gloves read tan or skin-like** in sun and backlight in-engine, though the albedo is dark. The view floor and rim lift them. The v2 gloves on the left of `compare/01` read darker; on glove value this is a regression.
- **The thumbs are thick and sausage-like** in the close renders.
- **The support forearm is a long, near-uniform olive tube** from the bottom edge. The fold detail is in the normal map only and is barely visible at 1280×720.
- **The rifle is unchanged** from slice 1: about 25k triangles, slab-sided forms, and a UV atlas that still spends area on the stock.
