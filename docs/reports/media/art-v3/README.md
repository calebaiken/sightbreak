# Relay AR arms v3: evidence

Every image is a real render of commit `5100b3e` (rigged arms, viewmodel projection). `sha256.txt` hashes every file in this folder.

- **In-engine captures:** Godot 4.7.2 on Xvfb with Mesa llvmpipe (software), from `game/tests/weapon_art_capture.gd`. They are fixture poses, not played matches, and not phone photographs.
- **Review renders:** Blender 5.2.2 Cycles (CPU, 32 samples, Standard view transform, studio lights), from `tools/art/render_arms.py`. They use the shipped GLBs and the shipped 1024 texture sets, not the high-poly sources.
- **Still images only.** Moving evidence (frame sequences of reload and fire) is a separate, later item; stills cannot show motion quality.

| Folder | Contents |
| --- | --- |
| `captures/` | 1280×720: backlit yard ready (01), firing (02), reload at 30 % (03), reload at the support-hand grab (03b); sunlit yard (04); transfer-hall shade (05); sunlit with the Crimson Archive skin (06); the inspection studio with the skin (07) |
| `aspect/` | 01, 03b and 05 at 1600×720 (20:9) and 1024×768 (4:3). The capture sets the root viewport to that size, so these show what a wider or taller canvas would frame. **They are not what ships:** `project.godot` uses `canvas_items` stretch with the default "keep" aspect, so a 20:9 or 4:3 screen shows the 16:9 frame with bars. Whether to switch to "expand" is an open decision for the project owner and Codex. |
| `compare/` | Half-scale before/after sheets: left is `2bba519` (static v2 hands, world projection), right is `5100b3e` |
| `renders/` | Cycles, JPEG quality 92: `eye_54` (the in-game camera at the 54° viewmodel field of view, grey studio), `right_34`, `left_34`, `firing_hand`, `firing_hand_left`, `support_hand`, `support_hand_right`, and two reload frames (`reload_grab` at 14 %, `reload_down` at 45 %) with the magazine on the game's drop curve |
| `logs/` | `arms-build.log` (bake, placement and grip-solve report from `tools/art/arms_build.py`), `validate-5100b3e.log` (the first `validate.sh` run, summary) and `validate-5100b3e-rerun-full.log` (the full re-run before publishing: exit 0, 3,144 counted native assertions, the 10-round bot lifecycle match and two ENet clients), `benchmark-5100b3e.log` (software-render relative cost; see `docs/art/PERFORMANCE_REPORT.md`) |

## What these images show that is still wrong

These are my own observations of these frames. The independent review is separate (`docs/art/VISUAL_QA.md`).

- **The reload grab is not legible in first person.** In `03b` the weapon cants and the magazine and the support hand are below the frame, so the player never sees the hand reach the magazine. The Cycles `reload_grab` render shows the hand near the well, not closed on the magazine: the grab solver left the pinky and thumb unresolved (`grab pinky None`, `grab thumb None` in `arms-build.log`).
- **The firing hand is mostly off-screen** at the bottom right, and the right forearm is not visible.
- **The gloves read tan or skin-like** in sun and backlight in-engine, though the albedo is dark. The view floor and rim lift them. The v2 gloves on the left of `compare/01` read darker; on glove value this is a regression.
- **The thumbs are thick and sausage-like** in the close renders.
- **The support forearm is a long, near-uniform olive tube** from the bottom edge. The fold detail is in the normal map only and is barely visible at 1280×720.
- **The rifle is unchanged** from slice 1: about 25k triangles, slab-sided forms, and a UV atlas that still spends area on the stock.
