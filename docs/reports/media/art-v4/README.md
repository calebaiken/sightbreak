# Relay AR arms rebuild and the `64ec598` review fixes: evidence

This folder covers the work after Codex's integration review of `64ec598`.

| Commit | Change |
| --- | --- |
| `144dc33` | Arms generator rebuild |
| `0087956` | The rebuilt arms asset |
| `3934110` | Fallback hands drawn with the viewmodel projection; see `fallback-projection/README.md` |
| `7ce8981` | Reload presentation clock, framing margin and scene retention |

`sha256.txt` hashes every file.

- **In-engine captures:** Godot 4.7.2 on Xvfb with Mesa llvmpipe (software rendering), from `game/tests/weapon_art_capture.gd` and `game/tests/weapon_motion_capture.gd`. They are fixture poses and a scripted fire-then-reload sequence, not played matches, and not phone photographs.
- **Motion:** 30 fps of simulated time. llvmpipe renders far slower than real time, so the sequences show motion design, not smoothness on a device.

## The arms rebuild (`144dc33`, `0087956`)

| Item | v3 (`64ec598`) | Rebuild | Source |
| --- | --- | --- | --- |
| Triangles (both arms) | 10,672 | 7,828 (budget 10,000; the test now enforces it again) | `logs/arms-build.log` |
| Bones | 34 | 34 | same |
| Glove and sleeve albedo (generator palette, linear) | Glove about 0.052, sleeve about 0.055 (measured from the v3 texture) | Glove fabric 0.024, sleeve (0.082, 0.092, 0.052) | `tools/art/arms_build.py` `PALETTE` |
| Trigger pad to trigger face | 11.6 mm (review of `5100b3e`) | 4.4 mm, no point inside the trigger | `logs/arms-build.log` |
| Magazine grab | Thumb and pinky unresolved (`None`) | The solver resolves all five digits (no `None`). The pinky's first two joints stay nearly straight (−2°, −1°); per-joint angles are in the log | same |
| Covered texels with baked AO below 0.1 (raw 2048² bake) | 0.5 % | 0.6 % | measured on the raw bakes |

**AO bake correction.** The rebuild bakes glove and sleeve separately. That bake first left 14 % of covered texels with AO below 0.1, because the other arm's low-poly copy stayed visible to the bake and occluded it. Hiding the other copies during the bake brought it back to 0.6 %. **This fixes a defect introduced during the rebuild. It is not an improvement over v3**, and `144dc33`'s commit message should be read that way.

## Codex's other findings on `64ec598` (`7ce8981`)

- **Online reload poses stepped at 20 Hz.**
  - **Before:** the pose read the replicated timer, so the clip changed on 39 of 119 visual ticks (Codex measured 40 of 120).
  - **Fix:** a presentation clock in `actor.gd` (`_reload_clock`). It advances every visual tick and stays within 0.1 s below the authoritative timer. It snaps to a new reload or to an upward correction, and returns to the hold at once on cancel. It never writes `reload_remaining`, ammunition or any gameplay state.
  - **Test:** `weapon_art_test.gd` simulates 20 Hz snapshots: the pose changes on at least 115 of 119 ticks, never goes backwards, and keeps within the slack.
- **The arms scene was not retained.** `ResourceLoader.has_cached` was false after a build, so every equip loaded the GLB again. `SBWeaponModel` now keeps the packed scene, and the test checks the cache.
- **Narrow framing margin at the grab.**
  - **Before:** with the 9 cm reload lift, the magazine's lowest vertex was 3.8 px inside a 720 px frame at 14 % of the reload, and 36 of 1,497 vertices were up to 2.8 px below it at 15 %.
  - **Fix:** the lift is now 11 cm. The magazine's lowest vertex is then 29 px inside at 14 % and 23 px inside at 15 %, and every vertex is in frame from 12 % to 16 % and from 80 % to 90 %.
  - **Unchanged:** the buffer tube's end face stays off the right edge, and the muzzle stays right of the crosshair at about (0.58, 0.48) of the frame.
  - **Test:** `weapon_art_test.gd` checks every magazine vertex, with a 1 % margin, at 12–15 % and 82–88 %.
- **Negative control** (`logs/weapon-art-negative-control-clock-framing-cache.log`): the three changes reverted together give exactly four failures: 14 % and 15 % framing, 39 pose changes in 119 ticks, and the scene not cached.
- **Results:** `weapon_art_test.gd` 109 checks, 0 failures (`logs/weapon-art-clock-framing.log`). `validate.sh` exits 0 (`logs/validate-clock-framing.log`; actor 73/0).

## Files

| Folder | Contents |
| --- | --- |
| `captures/` | 1280 × 720, at `7ce8981`: backlit ready (01), the reload grab at 15 % (03b), sunlit ready (04), transfer-hall shade (05). `04-support-hand-zoom.png` is a nearest-neighbour enlargement of the support hand from 04 (rebuilt arms, 9 cm lift, which does not affect the ready pose) |
| `motion/` | <ul><li>`sunlit-fire-reload.mp4`, `backlit-fire-reload.mp4` (H.264, 1280 × 720, 116 frames) and `sunlit-fire-reload.gif` (640 px, 15 fps);</li><li>`*-sheet.png`: 16 labelled frames over the whole sequence;</li><li>`sunlit-grab-seat-sheet.png`: the grab (clip 0.01–0.19) and the seat (0.87–0.99);</li><li>`*-frames.csv`: per frame, the time, phase, ammunition, reload remaining, clip time, magazine offset and kick.</li></ul> |
| `fallback-projection/` | The fallback-hands fix (`3934110`), with its own README |
| `logs/` | `arms-build.log`, `validate-arms-rebuild.log` (`0087956`), `validate-clock-framing.log`, `weapon-art-clock-framing.log`, and the negative control |

## What these frames still show wrong

These are my own observations of these frames, not a review.
- **The grip hand reads as a mitten:** a smooth grey-beige shape whose fingers wrap the grip's front strap without visible knuckles. The support hand is closer but still lacks joint definition at 1280 × 720.
- **Support fingertips crest the top rail** (`captures/04-support-hand-zoom.png`).
- **The sleeves are a near-uniform olive tube.** The irregular folds are in the normal map and barely show at this size.
- **The bore's vanishing point is still about 125 px left of the crosshair.** The rifle reads as held across the body, which is the "displayed sideways" read in Codex's art report.
- **Shade contrast:** in the hall, receiver and gloves are close in value. In backlight the rim brightens silhouettes strongly.
- **Animation gaps:** no draw or inspect clip, and the same magazine is pulled and reseated. Reduced-motion variants have not been visually reviewed.
- **The static v2 hands** (the fallback) are attached now, but are still the blocky v2 asset: slate-grey sleeves with a tan cuff stripe (an earlier version of this line said "tan sleeves"; the review below corrected it).

Codex's independent art rubric on `64ec598` was about **5.5/10** against the 8.5 gate. No new score is claimed here; the next review re-scores this work.
