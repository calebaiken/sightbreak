# Relay AR slice: evidence

Every image is a real render. The in-engine captures are Godot 4.7.2 on Xvfb with Mesa llvmpipe (software) at 1280×720, from `game/tests/weapon_art_capture.gd`. These are fixture poses, not played matches, and not phone photographs. The review renders are Blender 5.2.2 Cycles (CPU) from `tools/art/render_views.py`, using the procedural materials the textures were baked from. `sha256.txt` hashes every file.

| Folder | Contents |
| --- | --- |
| `captures/before-procedural/` | The 0.4 procedural rifle and box hands, the same seven fixtures |
| `captures/after-authored/` | The Relay AR and baked hands at the final head (`b376e61`): backlit yard ready, firing, reload; sunlit yard; transfer-hall shade; sunlit with the Crimson Archive skin; inspection studio with the skin |
| `reviewed-v4/` | The three authored frames as the visual reviewer saw them, before the follow-up fixes: casing origin, default baked finish, inspection centring (`docs/art/VISUAL_QA.md`) |
| `compare/` | Half-scale before/after sheets for all seven fixtures, plus a full-resolution sunlit detail crop |
| `renders/` | Cycles, JPEG quality 92: the seven required views (left and right ¾, side profile, top perspective, receiver close-up, grip and magazine close-up, surface-materials close-up), `eye` (the in-game first-person camera in a grey studio), and both hands |
| `logs/` | `weapon_render_benchmark-498311e.log` and `-b376e61.log` (software-render relative cost; see `docs/art/PERFORMANCE_REPORT.md`), `validate-art-head.log` (the full `validate.sh` on `b376e61`), and both capture runs |

The Cycles grip and magazine close-up was re-rendered once: the first camera direction sat below the studio floor and produced a black frame.
