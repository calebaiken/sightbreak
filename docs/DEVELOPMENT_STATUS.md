# Development status

Updated 2026-10-14 by Claude (cloud session). Read this first when resuming work.

## Branches and pull requests

| Branch | Head | State |
| --- | --- | --- |
| `main` | `e67f2c8` | 0.3.0-dev baseline |
| `claude/independent-audit-visual-v04` (PR #1 → `main`) | `148760e` | <ul><li>Codex's blockers are fixed.</li><li>The Unicode kill-feed fix was accepted at `227d6c8`.</li><li>The status-line regression Codex found at `98ff57c` is fixed in `148760e` (`docs/audits/CODEX_REVIEW_RESPONSE.md`).</li><li>**Unmerged; waiting for Codex's re-review.** Not a release candidate.</li></ul> |
| `claude/cs2-fidelity-art-production` (PR #2, stacked on PR #1) | this branch, `b507205` and later | <ul><li>Graphics slice: Relay AR, rigged arms, viewmodel projection.</li><li>Codex's four corrections from its review of `64ec598` are addressed.</li><li>Codex's visual score of 5.5/10 stands against the 8.5 gate.</li><li>Merge only after PR #1, as its own reviewed PR.</li></ul> |
| `claude/native-ui-production-v1` (no PR yet) | based on PR #1 `148760e` | <ul><li>The UI and UX overhaul (`docs/ui/VISUAL_GAP_REVIEW.md` on that branch).</li><li>Independent of the art branch.</li></ul> |
| Codex branches and PRs #3–#9 | see GitHub | Networking, backend, economy integrity and integration. Integration preview PR #9 (`integration/sightbreak-network-art-preview`). Claude does not push to them |

**Ownership** (Codex's `docs/engineering/PARALLEL_WORK.md`):
- **Codex:** networking, server lifecycle, backend, measurement and build tooling.
- **Claude:** meshes, materials, shaders, visual UI, animation and art production.
- **Shared files:** changes to `match.gd` and actor presentation must be small. When this branch meets Codex's movement PR, keep both the `ViewmodelShading` preload and the `SBMovementStep` aliases and delegation in `actor.gd`.

## Done on this branch

- **Asset pipeline:** `tools/art/`, with headless Blender (bpy 5.2.2): generators, signed-distance modelling, bake, export, texture packing, review renders and motion sheets. See `docs/art/ASSET_PIPELINE.md`.
- **Relay AR rifle:** original and real scale. 30,326 triangles (25,194 in first person), with a 1024² baked PBR set.
- **Rigged arms:**
  - 7,828 triangles and 34 bones, with a contact-solved grip and a 1 s reload clip.
  - Glove and sleeve are separated in value.
  - A presentation-only reload clock keeps poses smooth at the 20 Hz snapshot rate.
  - The reload is staged so the hand and the whole magazine are in frame at the grab and the seat.
- **Viewmodel projection:** 54° with depth compression, applied to every first-person mesh of the authored rifle build, including both fallback hand variants.
- **Tests:** `weapon_art_test.gd` (109 checks) runs in `validate.sh`. `paint_visibility_test.gd` (pixels) and `weapon_motion_capture.gd` (frame sequences) need a native display.
- **Evidence:** `docs/reports/media/art-v1`, `art-v3`, `art-v4`.

## Not done (in priority order)

The review record is in `docs/art/VISUAL_QA.md`. Codex scored the slice 5.5/10; the gate is 8.5.

1. **Composition:** the bore's vanishing point is about 125 px left of the crosshair (the rifle reads as held sideways), and the action leaves the frame at 4:3.
2. **Hands and sleeves:**
   - the grip hand reads as a mitten;
   - support fingertips crest the rail;
   - the sleeves are near-uniform tubes;
   - the static v2 fallback hands are still the v2 asset.
3. **Lighting:** shade contrast between receiver and arms; over-bright backlit rims.
4. **Animation:** draw and inspect clips; a second magazine; reduced motion reviewed.
5. **Effects:** muzzle flash and casings.
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
