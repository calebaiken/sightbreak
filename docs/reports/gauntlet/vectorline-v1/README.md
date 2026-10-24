# Vectorline (SMG), authored model and hands

Evidence for `claude/weapon-art-vectorline-v1` (stacked on `claude/muzzle-tracers-v1`, PR #39, on `claude/weapon-art-sidearm-v1`, PR #38). The weapon asset contract and rebuild commands are in `docs/art/WEAPON_PRODUCTION.md` and `ASSET_PIPELINE.md`. Cosmetic only: nothing here reads or changes damage, ammo, spread, recoil or the protocol.

| Item | Value |
| --- | --- |
| Piece | The Vectorline: an original compact pistol-calibre SMG (17,152 triangles, budget 22,000; 15,200 in first person) with static authored gloved hands (9,800, budget 10,000), replacing the procedural SMG. The procedural one remains as the fallback (`WeaponModel.use_authored = false`) |
| Bar | A first-person weapon that reads as a believable SMG in sun, backlight and shade, judged by fresh-context critics against what they know of Counter-Strike 2 and Valorant. No reference imagery was available (`docs/roadmap/BARS.md`); no parity claim |
| Source | Generator `tools/art/vectorline.py` (a partial one existed uncommitted in an old worktree and had never been built; it built first time and was then reworked), hands `tools/art/vectorline_hands.py`, integration `weapon_model.gd` (`_build_authored_smg`), tests `weapon_art_test.gd` (the SMG contract, 244 checks in all) and `actor_test.gd` |
| Renders | `sheets/`: BEFORE (procedural SMG) and AFTER pairs in `ready-three-lightings.jpg` and `fire-draw-reload.jpg`, 1280x720 native Godot renders (llvmpipe under Xvfb, gl_compatibility), cropped to the right of the view. `model-*.jpg` are Blender review renders of the generator (flat studio materials, not the baked textures). Labelled, not blind |
| Capture | `game/tests/presentation_gallery_capture.gd --weapons=smg` (add `--procedural` for the old build), `viewmodel_fit_capture.gd --weapon=smg` for placement |
| Tests | `scripts/validate.sh` on the final tree: see the PR; `weapon_art_test` 244 checks, `actor_test` 76, `render_budget_test` 21, `integration_actor_lifecycle_test` 183, `tracer_effects_test` 20 pass |

## What was built, in order

1. The generator built first time (31 objects, 15,168 triangles). Hands were written from the Relay AR's and Kestrel 9's building blocks and posed on the grip and the shroud (a C clamp under it).
2. Bake, magazine ambient occlusion rebaked on its own (23% of the vertices almost fully occluded, 5.1% after), export, textures, integration, placement by `viewmodel_fit_capture.gd`.
3. The first first-person look showed the receiver's flat rear face (the stock is behind the camera) as one black slab. An end plate was added; its first version had a recessed round buffer cap that both critic rounds read as a camera lens, and its first colour blew out to cream in sun. It is now a polymer plate (the magazine's base colour) with four grip ribs and a retaining screw.
4. Placement: the first fit (scale 1.3) covered the middle of the view; the shipped one is scale 1.15, rotated 0.14 rad in yaw, lower right of the view with its bore line near the crosshair.
5. The two paint parts were merged into one `paint_receiver` (one finish for the whole upper, one draw fewer), because the existing `actor_test` budget of six first-person nodes failed for the authored SMG. `actor_test.gd` now holds the authored SMG to eight nodes (the pistol's count; the rifle's nine add its arms) and keeps the original six on the procedural marksman.

## Blind comparison

Three rounds of six unlabelled pairs each (ready in backlit, sun and shade, the instant of a shot, the draw, mid-reload), the authored model against the procedural one, a fresh-context critic each time, key kept outside the reviewed folder (published afterwards in `data/`):

| Round | Authored chosen | Critic's score, authored against procedural (of 60) | What changed after |
| --- | --- | --- | --- |
| 1 | 5 of 6 (lost the muzzle-flash frame) | 31 against 25 | Smaller, lower-right placement; flash scale 0.95 |
| 2 | 6 of 6 | 31 against 19 | Lens-like end cap replaced; a fill floor for the near-black upper |
| 3 | 6 of 6 | 34 against 25 | nothing (last round) |

**A mistake of mine in rounds 1 and 2:** I cropped the frames for the critics and told them the crosshair was at the centre of each image. It was not (it sat at about 27% across and 31% down the crop). Their statements that the gun "covers the crosshair" or "points left of it" in those rounds are void. Round 3 used full 1280x720 frames with the crosshair at the centre; there the critic found that neither gun touches it (by its estimate the nearest part of the authored one is about 115 px away) and that both muzzles sit within about 100 to 130 px of the aim point; I have not measured this independently.

The authored model was chosen in 17 of 18 pairs, which says it beats a placeholder; it does not say it is good. The same critic scored it 34 of 60, about 5.7 out of 10, against the 8.5 bar (gate G5 stays FAILED). Its worst defects in round 3, ranked: near-black gun, gloves and sleeve within a few levels of each other in shade and backlight (the cream magazine and the tan plate are the only light parts and read as stuck-on); arms and hands crude (a constant-width tube sleeve, lumpy mitts; there are no rigged arms for the SMG, so a reload tilts the gun and moves its magazine with no hand taking it); a weak, partly hidden muzzle flash; orange speckle on the right glove under the flash light (the glove's stipple lit by the flash); and a thick sight frame in the horizon band.

## Not shown

No GPU, no motion, no sound, no human. The last two changes (the end plate, the fill floor) were judged in round 3 only on the frames above; the fill floor's effect on separation in shade was not measured separately (`viewmodel_light_probe.gd` has no SMG case). No SMG reload hand animation. The Longwatch marksman remains procedural.
