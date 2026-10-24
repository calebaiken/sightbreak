# M10: operator muzzle flash, tracers and per-weapon flash size

Evidence for the shot presentation changes on `claude/muzzle-tracers-v1` (stacked on `claude/weapon-art-sidearm-v1`, PR #38). Cosmetic only: nothing here reads or changes damage, ammo, spread or the networking protocol.

| Item | Value |
| --- | --- |
| Pieces | (1) Operators' muzzle flash is the first-person flash's lathed mesh and additive material at 3.0 times its size (growing to 5.7 times at 40 m), replacing a 0.085 x 0.085 x 0.16 m prism (a flat yellow triangle seen from the front). (2) `SBTracerEffects`: one multimesh, one draw call, 16 slots; one operator shot in three leaves a comet-shaped streak, 7 m long at 190 m/s, from the muzzle to where the trace ended (never drawn for the local player's own shots, and not drawn when seen end-on). (3) The procedural SMG's and marksman's first-person flash scaled up (1.25 and 1.9) because their muzzles sit further down the view. |
| Bar | A flash and a bullet path that read on an operator who is shooting, at the ranges the yard offers (8 to 40 m), judged by fresh-context critics against what they know of Counter-Strike 2 and Valorant. No reference imagery was available (`docs/roadmap/BARS.md`); no parity claim |
| Source | Branch `claude/muzzle-tracers-v1` on `claude/weapon-art-sidearm-v1` (3b2afd3b) |
| Renders | `sheets/`: BEFORE (3b2afd3b) and AFTER pairs, 1280x720 native Godot renders (llvmpipe under Xvfb, gl_compatibility), cropped. Labelled, not blind. The 40 ms flash and the 190 m/s streak are stepped by hand at 240 Hz, so a frame shows what a player's frame at that age shows, not what the software rasteriser's 0.3 s frames would |
| Capture | `game/tests/muzzle_presentation_capture.gd` (the same script runs on a build without tracers) |
| Tests | `game/tests/tracer_effects_test.gd` (20 checks headless, 22 rendered; registered in `scripts/validate.sh` both ways), `render_budget_test`, `actor_test`, `weapon_art_test` (209) and `integration_actor_lifecycle_test` pass, and the full `scripts/validate.sh` on the final tree: exit 0 with `DISPLAY=:99` (skipped by the script: catalog drift check, three Windows-only tests). Captured logs in `data/` |

## What was measured

Flash area on screen in the first person, as bright warm pixels the shot adds (rifle, SMG, marksman; backlit and sunlit). Before: rifle 1,946 and 921, SMG 1,147 and 846, marksman 528 and 475. The marksman's flash was a quarter of the rifle's. After scaling the SMG and the marksman: SMG 1,424 and 1,100, marksman 1,345 and 1,845 (rifle 1,898 and 1,169).

## Blind comparison

Round 1 (12 unlabelled pairs, the old build against the new, key kept outside the reviewed folder): the critic chose the new look in all 8 pairs where either side showed anything, and 4 pairs were blank on both sides (frames 70 ms after the shot, where neither build shows a flash and the streaks had left the view; that was my choice of frames, not a finding). The critic's defects, checked before acting on them:

- A "laser or wire through both operators". True of the frames, and my fixture's fault: it aimed each operator's tracer across the other (the left operator at a point to the right). The fixture now shoots outward and ends each streak at the first surface by a physics ray.
- "Vertical beams on the floor" in the shots fired at the camera. Geometry, not a bug: a streak running toward a camera that is above it projects downward. I accepted it at first; round 2 below changed my mind.
- "The flash is small and the wrong shape" (about 8 px at 8 m). Agreed: the world flash scale went from 2.0 to 3.0.

Round 2 (16 unlabelled pairs, near and far crops, the old build against the new one with the larger flash and the fixed fixture): the new look won all 16 (high confidence on 12). The bar is low: the old build shows no flash at all from the front, only a small yellow triangle that never changes. What the critic found wrong with the new look is the useful part, and each point was checked against the geometry before acting on it:

- Pale vertical "beams" and a "keyhole stalk" under the flash in the shots fired at the camera. Geometry: a streak running toward a camera that is above it projects downward and ends in a pillar. Fixed in the shader: a streak fades as the angle between it and the line of sight closes (end-on streaks are not drawn), and fades out within 8 m of the camera.
- "Floating amber dashes" at 35 ms. A travelling streak 3.6 m long really is detached from the muzzle after 19 ms. The streak is now 7 m long and a comet (nothing at its tail end, a bright head), so it stays visibly joined to the muzzle for the 8 m shots.
- "No light on the hands or vest": left as is. Operators carry no light (ten of them firing would be ten dynamic lights); the first-person flash keeps its own.
- "At 22 m and 40 m nothing legible". The operator's flash now grows with the distance from the viewer, 1.0 up to 10 m and then 3% per metre, at most 1.9 times (`WORLD_FLASH_GROWTH`).

Round 3 (16 pairs, the previous revision against the tuned one, judged blind): the tuned look won 12 of 16. It won all 8 shots fired at the camera (the pillars and the stalk are gone, high confidence) and the two 35 ms diagonal shots in each set; it lost the two 15 ms diagonal shots in each set, where its new tail faded to nothing at the tail end and left the bright head 45 px clear of the muzzle ("a floating dash 15 ms after firing", a regression I introduced). The tail is now left below zero while a streak is still lengthening, which lights it down to the muzzle. That last change was inspected on the 15 ms frames (it now joins the flash on both sides in both lightings) and **not re-judged blind**. The critic's remaining notes, not acted on: the flash is one flat sprite for every shot, the operators' flash casts no light, and scene tags on the container faces look like laser dots on the streak's path in some frames (they are scene geometry, present in the clean frames too).

In order: round 1 new look chosen 8 of 8 decided (4 blank frames), round 2 16 of 16, round 3 tuned over previous 12 of 16 (the 4 losses fixed afterwards, not re-judged).

The keys (`data/blind-keys/`) are published after the fact for audit; they were never inside a reviewed folder.

## Not shown

No GPU, no motion, no sound, no human. Tracers are not drawn for the local player's own shots: a streak that leaves the muzzle toward the crosshair is seen end-on (measured on an earlier revision: 27 pixels differ across three ages in a 1280x720 frame), so it would be a smear and nothing more. Tracers exist only where a shot is traced (the authority or an offline match); a client that is sent only a flash does not get one, so nothing new about a hidden shooter is revealed. Whether the tracer cadence (one in three) and speed (190 m/s) feel right in motion is unjudged. The tracer costs one draw call; nothing here was measured on a GPU or a phone, and the new world flash has no tier gate (the graphics tiers are on PR #35 and were not in this branch's base).
