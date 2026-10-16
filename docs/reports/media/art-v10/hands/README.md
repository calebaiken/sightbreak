# Hands, round 5 (art-v10): box-modelled cage topology under the same SDF glove

Branch `claude/cs2-fidelity-art-production`, source commit `5e1da3e`. **Evidence: my own native Godot renders and tests on llvmpipe at 1280 × 720; no human has looked at these frames, and nothing was seen on a phone.** An independent same-model review comes at the end of the round (`../review/`).

## The architectural question

Is the SDF generator the limit? Two separate things were bundled in it, and only one is:

- **The shape source** (`tools/art/relay_ar_arms.py`, `sdf.py`): a signed-distance glove built from joint chains. Its volumes are smooth and organised like a hand (three phalanges, condyles, thenar and hypothenar masses, a flared cuff) and it is the high-poly *bake source* for normals, AO, seams and padding. It is procedural, **not hand-sculpted**, and it still gives the characteristic "poured" smoothness: no tendon ridges, no web between the fingers that reads as skin folding, no individual finger character.
- **The game mesh** (what is skinned and rendered): until now a **QuadriFlow remesh of that SDF**, with loops wherever the quad flow landed. That is the part that skinned badly: a finger bent along a diagonal, fingertips were whatever the flow made of them, and creases could not lie on edges.

I replaced the second. `tools/art/hand_cage.py` builds the game glove **the way a character artist blocks one out**: a palm block of ten-vertex rings (cuff to knuckle plane), four finger tubes and a thumb tube extruded from the palm's faces, an edge loop either side of every joint, one subdivision, then each vertex projected onto the glove SDF so the volume matches the bake source. Topology is therefore authored (rings at the joints, a ring of eight at each fingertip), the surface is not. The high-to-low bake, smart UV, heat-map weights onto the unchanged 34-bone rig and the grab solve are the existing pipeline.

What I did **not** do, and why: sculpt. The container has headless Blender and no sculpting session, no tablet input and no licensed scan data. I will not call a cage projected onto a procedural field "hand-sculpted"; it is a better-constructed procedural mesh. A real sculpt-and-retopologise pass, or a licensed hand base mesh, is the remaining route to character in the silhouette and is listed under *next milestone*.

## What changed, measured

| | v9 (`5357329`) | v10 (`5e1da3e`) |
| --- | ---: | ---: |
| arms triangles (both arms, budget 10,000) | 9,268 | **8,520** |
| bones | 34 | 34 (unchanged) |
| contact: left arm in rifle / in magazine, right arm in rifle (mm; bounds 1.0 / 1.0 / 1.5) | 0.0 / 0.9 / 0.8 | 0.0 / 0.0 / 1.0 |
| `test_reload_contact.py` (24 checks), `weapon_art_test` (179), `reload_sequence_test` (92), `reload_visibility_test` (15) | pass | pass, no acceptance threshold changed |

Grab solve: the fingertip margin `GRAB_MARGIN = 0.0013` was added (the first cage build put the left arm 1.09 mm into the magazine; the new loops make the fingertips sit a little proud). The right arm's trigger-finger reach is now penalised for any interpenetration and is deterministic (1.0 mm every build; an earlier build varied 1.4–2.1 mm run to run).

## What the native frames show (`frames/`)

- `gameplay-1280-before-after.jpg`: ready, grasp, insertion and return, v9 above and v10 below, same ticks, same lighting.
- `support-hand-closeup-1280-crop-before-after.jpg`: the support hand at the grasp (#28) and the open return pose (#126), a 1280 × 720 frame cropped and enlarged 1.5×.
- `grip-hand-closeup-1280-crop-before-after.jpg`: the firing hand on the grip at ready and at insertion.

Honest reading of them: the fingers are **more evenly tapered with defined knuckle rings**, the cupped hand around the magazine base has cleaner finger overlaps, and the open return hand has individual fingers with separation rather than a spread fan. The thumb's base reads as a thenar mass. **The improvement is moderate, not transformative.** The gloves are still smooth and rather doll-like; the firing hand still reads as a mitten on the grip at gameplay size; the back of the hand shows no tendon structure; the glove is pale in sun (a lighting matter, below). I do not rate hands at the 8.5 target.

## Known defects

1. Procedural source, no sculpted character (above).
2. Grip hand reads as a mass at 1280 × 720: fingers wrap the grip, but the separation between fingers is under two pixels.
3. Fingertip caps are still read mainly through albedo, not form.
4. Gloves are pale in direct sun (see `../materials/` and `../README.md`).
5. Joint creasing exists only in the baked normal map (nothing is displaced at a bend).

## Reproduce

`tools/art/preview_cage.py` renders the cage next to the SDF glove (Cycles, flat region colours) for shape review in about a minute; `python3 tools/art/arms_build.py <out> --rifle game/assets/weapons/relay_ar/relay_ar.glb` is the full build (about eight minutes with the bake; `--no-bake` is 14 s, for experiments only and never installed). The install steps are in `docs/art/ASSET_PIPELINE.md`.
