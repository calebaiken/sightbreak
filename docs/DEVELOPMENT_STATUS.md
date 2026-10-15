# Development status

Updated 2026-10-15 (art-v9 round) by Claude (cloud session). Read this first when resuming work.

## Branches and pull requests

| Branch | Head | State |
| --- | --- | --- |
| `main` | `e67f2c8` | 0.3.0-dev baseline |
| `claude/independent-audit-visual-v04` (PR #1 → `main`) | `148760e` | <ul><li>Codex's blockers are fixed.</li><li>The Unicode kill-feed fix was accepted at `227d6c8`.</li><li>The status-line regression Codex found at `98ff57c` is fixed in `148760e` (`docs/audits/CODEX_REVIEW_RESPONSE.md`).</li><li>**Unmerged; waiting for Codex's re-review.** Not a release candidate.</li></ul> |
| `claude/cs2-fidelity-art-production` (PR #2, stacked on PR #1) | this branch, `b507205` and later | <ul><li>Graphics slice: Relay AR, rigged arms, viewmodel projection.</li><li>Codex's four corrections from its review of `64ec598` are addressed.</li><li>Codex's visual score of 5.5/10 stands against the 8.5 gate.</li><li>Merge only after PR #1, as its own reviewed PR.</li></ul> |
| `claude/native-ui-production-v1` (no PR yet) | `2b2731a`, based on PR #1 `148760e` | <ul><li>The UI and UX overhaul (`docs/ui/VISUAL_GAP_REVIEW.md` on that branch): a measured, adaptive main menu and an armory with empty, loading and error states, exact market and trade terms, and a collection browser.</li><li>Independent of the art branch.</li></ul> |
| Codex branches and PRs #3–#9 | see GitHub | Networking, backend, economy integrity and integration. Integration preview PR #9 (`integration/sightbreak-network-art-preview`). Claude does not push to them |

**Ownership** (Codex's `docs/engineering/PARALLEL_WORK.md`):
- **Codex:** networking, server lifecycle, backend, measurement and build tooling.
- **Claude:** meshes, materials, shaders, visual UI, animation and art production.
- **Shared files:** changes to `match.gd` and actor presentation must be small. When this branch meets Codex's movement PR, keep both the `ViewmodelShading` preload and the `SBMovementStep` aliases and delegation in `actor.gd`.

## Done on this branch

- **Asset pipeline:** `tools/art/`, with headless Blender (bpy 5.2.2): generators, signed-distance modelling, bake, export, texture packing, review renders and motion sheets. See `docs/art/ASSET_PIPELINE.md`.
- **Relay AR rifle:** original and real scale. 30,326 triangles (25,194 in first person), with a 1024² baked PBR set.
- **Rigged arms:**
  - 9,204 triangles and 34 bones, with a contact-solved grip and a 1 s, 60 fps reload clip.
  - The reload uses **two magazine nodes**: the support hand takes the old one out along its well at the release click (0.24), lets it go (it falls), fetches the second (it rises out of the closing hand, held from 0.56), brings it up, lines it up, enters it and seats it at 0.80 with the seat click, holds to 0.85 and returns; the nodes swap roles when it ends. Phases are one list (`reload_phases.gd`) that the Blender build and the actor share. Measured, with what each measurement does not show, in `docs/reports/media/art-v7/reload-two-magazines/`: the left arm is 0.0 mm into the rifle and 0.9 mm into the magazine, the right arm 1.3 mm into the trigger; the support hand is at least 13,984 px in every frame and the thumb at least 237 px and three fingertips at least 100 px whenever it holds a magazine (a floor against hiding them, not a legibility measure). **The animation is not finished**: the replacement has no visible source, the hand is still a glove fist, nothing measures how it reads in shade, the tan magazine and grip are alike, and nothing has been seen on a phone or by a person (the README lists ten).
  - The sleeve is a muted olive-drab (median luma 110 in sun, was 146) with a finer hem; gloves are 25 % lighter.
  - A presentation-only reload clock keeps poses smooth at the 20 Hz snapshot rate.
- **Reload round 3** (`docs/reports/media/art-v8/`): the replacement magazine is taken from a hip pouch below the frame (not drawn; the hand is out of the picture for 19 % of the reload); spline-smooth, weighted handling; six reload sounds on four voices with a capture test and a cancel test; a graphite pistol grip with finger grooves; a rebuilt muzzle flash with a first-person light and smoke; three reduced-motion variants of the rifle's roll and lift, **compared and not chosen (the default stays the 26° roll)**. 167 + 92 + 29 + 24 checks, three audio captures, a four-view pixel test, 29 injected defects, nine 60 Hz sequences. **A same-family review scored it 5.5 to 6.5 per category against the 8.5 gate; no human has seen it, nobody has heard the sounds, nothing has run on a phone.** The README in `reload-hip-retrieval/` lists what is unresolved: the hands are still sausage-like, the hip trip has no visible pouch, glove and sleeve share a value in shade and the dark.
- **Art-v9 round** (`docs/reports/media/art-v9/`, `docs/art/VISUAL_QA.md`): the rifle's pale reload frames are root-caused to the sky reflection on the baked metal and corrected with a roughness floor and a metal fill floor (stability test, sun/shade/skin, with controls); the gloves have seams, tips, a taller guard, a pad and knit grain (contact 0.8 mm, 9,268 triangles); the grip, gloves and metal are separated by value in sun (a light-separation test); the replacement is still fetched off-screen (a drawn pouch was rejected) with the hip at 31 cm; reduced motion has separate roll, lift, recoil and hand-clip controls with `current`, `calm` and `still` variants (`Actor.REDUCED_RELOAD_VARIANTS`; the default is unchanged) and a second `reload_calm` clip. 175 weapon-art checks, 92 sequence, 24 contact, 15 visibility rules in four variants, 35 negative controls, a same-model read-only review. **The 8.5 gate is not met**; the reviewer scored materials, lighting and hands/reload at 5.0 (scope: weapon and hands, stills).
- **Bore:** the rifle's vanishing point is 38 px left and 21 px above the crosshair (3.5°, was 124 px left, 10.0°) and the bore line passes through the crosshair.
- **Effects:** a layered additive muzzle flash (213 triangles; it differs shot to shot and lasts 40 ms) and a lathed brass casing that tumbles, bounces and settles. Presentation only.
- **Viewmodel projection:** 54° with depth compression, applied to every first-person mesh of the authored rifle build, including both fallback hand variants.
- **Tests:** `weapon_art_test.gd` (167 checks) runs in `validate.sh`; `reload_legibility_probe.gd` and `viewmodel_light_probe.gd` (native display) measure the reload and the per-part luma. `paint_visibility_test.gd` (pixels) and `weapon_motion_capture.gd` (frame sequences) need a native display.
- **Evidence:** `docs/reports/media/art-v1`, `art-v3`, `art-v4`, `art-v5/lighting`, `art-v6/reload-hands-effects`.

## Not done (in priority order)

The review record is in `docs/art/VISUAL_QA.md`. Codex scored the slice 5.5/10; the gate is 8.5.

1. **Composition:** the bore is 3.5° off the crosshair (was 10°), not zero; at 4:3 the canvas shows more than ships (the project keeps 16:9).
2. **Hands and sleeves:**
   - the hands are SDF-built and modest at gameplay size (art-v9); a sculpted, hand-authored glove is the next step and needs a modelling session outside this container;
   - the grip hand still reads pale and skin-like in sun, the grip hand's fingers read as blobs, the open return pose shows thin flat fingers;
   - glove-to-sleeve and grip-to-receiver separation in shade, backlight and the dark did not improve (near-black on near-black);
   - the near-black underside of the support forearm at the hip;
   - the static v2 fallback hands are still the v2 asset.
3. **Lighting and finish:** the painted metal lost its sheen to the roughness floor (receiver and handguard are level in value and read drab olive-grey at rest); a fixed viewmodel environment would restore a highlight without the sky-band swing; shade contrast between receiver and arms; over-bright backlit rims.
4. **Animation:** draw and inspect clips; the hip pop (20 % of the replacement is in the frame when first drawn, was under 5 %; the first-draw bound is now 25 %); reduced motion: `calm` is the recommended candidate but unadopted, to be reviewed by someone who uses the setting (no policy, no comfort claim); a listening review of the reload sounds.
5. **Effects:** a bolt or charging-handle animation, a listening review of the reload sounds (synthesized, never heard by a person).
6. **The rifle:** a LOW-tier LOD and a UV repack.
7. **Next weapons:** sidearm, SMG and marksman rifle through the same pipeline.
8. **Environment:** one Relay Yard section at final quality.
9. **Characters:** an authored operator.

**Stretch aspect:** stays "keep" until the owner approves a competitive field-of-view policy (Codex's `MOBILE_ASPECT_REVIEW.md` on PR #9).

## Unverified

Physical Android and iOS frame time, thermals and touch feel, for every change on every branch. Every timing in this repository comes from Mesa llvmpipe software rendering and is relative only.

## Resume commands

```sh
git fetch origin && git worktree list
SIGHTBREAK_TOOLS_DIR=<tools> ./scripts/validate.sh
SIGHTBREAK_TOOLS_DIR=<tools> ./scripts/godot.sh --headless --script res://tests/weapon_art_test.gd
DISPLAY=:99 ./scripts/godot.sh --audio-driver Dummy --resolution 1280x720 --script res://tests/weapon_art_capture.gd -- --capture-dir=<out> [--procedural | --static-hands | --procedural-hands]
DISPLAY=:99 ./scripts/godot.sh --audio-driver Dummy --resolution 1280x720 --fixed-fps 30 --script res://tests/weapon_motion_capture.gd -- --capture-dir=<out> --view=sunlit
```
