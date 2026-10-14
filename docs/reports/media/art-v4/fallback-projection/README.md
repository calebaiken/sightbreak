# Fallback hands and the viewmodel projection

Codex's integration review of `64ec598` found that with `SBWeaponModel.use_rigged_arms = false` the static hands kept the world camera's projection (82° vertical) while the authored rifle used the 54° viewmodel projection, so the hands drew detached from the rifle. The procedural gloves had the same problem.

**Fix:** every mesh of a first-person build with the authored rifle now draws with the viewmodel projection.
- **Static hands:** `SBViewmodelShading.surface()` with the hands' own texture set. That set is the same three maps the `relay_ar_hands.tres` material binds, and that material sets no other parameter.
- **Procedural gloves and sleeves:** they are merged into one vertex-coloured mesh, which now uses `SBViewmodelShading.vertex_colour()`. Its sRGB-to-linear conversion matches `StandardMaterial3D`'s `vertex_color_is_srgb`.
- **Procedural weapons** (sidearm, SMG, marksman rifle, procedural rifle) keep the camera's projection for both the weapon and its gloves: each build has one projection. Moving those weapons to the viewmodel projection would need their placement refitted; that is not done here.
- **Switch:** `SBWeaponModel.use_hand_assets = false` puts the procedural gloves on the authored rifle, as if both hand assets were missing. Captures and tests use it; gameplay never reads it.

All captures are Godot 4.7.2 on Xvfb with Mesa llvmpipe, from `game/tests/weapon_art_capture.gd` (fixture poses at 1280 × 720). `sha256.txt` hashes every file.

| File | What it shows |
| --- | --- |
| `fallback-sheet.jpg` | 04 (sunlit) and 01 (backlit) for each variant. Rows: <ol><li>the static hands at `0087956`: the support hand floats above the rail and the grip hand is offset from the grip;</li><li>the static hands with the fix: both hands sit on the rifle;</li><li>the procedural gloves with the fix;</li><li>the rigged arms (the default), unchanged;</li><li>the procedural rifle with its gloves, both with the camera's projection, unchanged.</li></ol> |
| `captures/static-hands-0087956-*.png`, `captures/static-hands-*.png` | Full frames, before and after, at the ready pose (04) and at the reload grab (03b) |
| `captures/procedural-hands-*`, `captures/rigged-*`, `captures/procedural-rifle-*` | The other variants at the ready pose |
| `logs/weapon-art-fixed.log` | `weapon_art_test.gd`, 96 checks, 0 failures |
| `logs/weapon-art-negative-control.log` | Negative control: the same test with only the two material changes reverted. Two failures: the static `hands` mesh, and the merged procedural glove mesh, each drawn with the camera's projection |
| `logs/validate-projection.log` | `validate.sh` on the fix, exit 0 |
| `logs/capture-*.log` | The capture runs: 8 frames each, no errors |

**New checks in `weapon_art_test.gd` (74 → 96).** Seven first-person builds:
- the authored rifle with the rigged arms, the static hands, and the procedural gloves;
- the procedural rifle, sidearm, SMG and marksman rifle.

For each build the test checks three things: it reports the right projection; every mesh draws with that one projection; and its hands are drawn. The inspection build must also draw everything with the camera's projection.

**Not addressed here.** This fix does not raise the v2 static hands to the rigged arms' standard. Their blocky fingers and slate-grey sleeves with a tan cuff stripe are as reviewed in `VISUAL_QA.md`.
