# Development status

## Combined preview update — 2026-10-14

The isolated combined branch includes PR1=98ff57c, PR2=64ec598 and Codex PR3–8=89c0e9. See [integration report](reports/COMBINED_INTEGRATION_REPORT.md) for exact source/build identities and evidence. Full maintained47-group matrix passes; new custom-HUD adversarial tests and full-capacity close-loss reconnect fail. Unicode feed clipping is fixed; older references below are historical. Default rig works, static fallback projection is defective, and the independent weapon/arms visual slice scores5.5/10 (not the historical whole-game8.1 rubric). Device performance, physical touch, Xcode and production Internet security remain unverified. Next priority: owner corrections for HUD/fallback, a separate bounded reconnect fix with hostile account/capacity tests, then refreshed combined verification. Prediction stays opt-in, live rewind disabled, earned-only economy unchanged.

## Historical record (superseded where noted above)

Updated 2026-10-13 by Claude (cloud session). Read this first when resuming work.

## Branches and pull requests

| Branch | Head | State |
| --- | --- | --- |
| `main` | `e67f2c8` | 0.3.0-dev baseline |
| `claude/independent-audit-visual-v04` (PR #1 → `main`) | `227d6c8` | Codex's three blockers, the second review's findings and Codex's follow-up (CJK fallback rows, `8803029`) are fixed; owner-requested funds label (`7756e35`). **Unmerged; waiting for Codex review.** Not a release candidate. |
| `claude/cs2-fidelity-art-production` (stacked on PR #1) | this branch | First vertical slice of the graphics initiative. Merge only after PR #1, as its own reviewed PR. |
| `codex/competitive-network-systems` (Codex) | `acfa704` | Network privacy (protocol 3), stacked on PR #1's earlier head `cf9a630`. A local trial merge onto `77e0433` was clean. |

Ownership (from Codex's `docs/engineering/PARALLEL_WORK.md`):
- **Codex:** networking, server lifecycle, backend, measurement and build tooling.
- **Claude:** meshes, materials, shaders, visual UI, animation and art production.
- **Shared:** `match.gd` changes must be small integration commits.

## Done on the art branch

- **Asset pipeline:** `tools/art/` with headless Blender (bpy 5.2.2): generators, bake, export, texture packing and review renders. See `docs/art/ASSET_PIPELINE.md`.
- **Relay AR rifle:** original, real scale, 30,326 triangles (25,194 in first person, which omits the buttstock), 1024² baked PBR set.
- **First-person hands (v2, being replaced):** static gloved hands and sleeves, 9,800 triangles, fitted with `tools/art/viewmodel_fit.py`. First-person tilts turn about a model-declared pivot. The `2bba519` review scored the whole viewmodel about 4.5/10 (`docs/art/VISUAL_QA.md`).
- **Arms v3 (in progress):** `tools/art/sdf.py` (signed-distance modelling and surface nets), `relay_ar_arms.py` (anatomy, glove, sleeve) and `arms_build.py` (retopology, bones, weights, contact-solved grip, reload clip). Not yet exported or integrated.
- **Integration:**
  - the authored rifle in first person and inspection, with the weapon contract unchanged (`docs/art/WEAPON_PRODUCTION.md`);
  - casings leave from the authored ejection port;
  - cosmetic finishes keep the baked occlusion and normals, and with no skin the rifle shows its baked surface;
  - the procedural rifle remains the fallback.
- **Tests:**
  - `weapon_art_test.gd` (48 checks) runs in `validate.sh`;
  - `weapon_art_capture.gd` takes the in-engine captures;
  - `weapon_render_benchmark.gd` measures relative cost.
- **Docs:** `docs/art/` (gap analysis with reference-access limits, direction, pipeline, budgets, weapon, character, environment, animation, rendering, visual QA, performance).

## Not done (in priority order)

Latest visual review (`2bba519`, same model family; see `docs/art/VISUAL_QA.md`): about 4.5/10 against a CS2-class bar of about 9. The rifle is at coherent alpha; hands, sleeves, motion, composition and lighting are at blockout level.

1. Arms v3: rigged anatomical gloves and real-length sleeves, skeletal reload and trigger, a viewmodel projection (about 50° vertical) with anti-clip, a viewmodel light, and value separation between glove, sleeve and receiver.
2. **Decision needed (owner and Codex):** the project ships `canvas_items` stretch with the default "keep" aspect, so 20:9 and 4:3 screens get bars. The 20:9/4:3 art captures, and the landscape UI tests' wide sizes, show an "expand" setup instead.
3. The rifle's LOW-tier hook and a UV repack (no stock in the first-person atlas) (mip bias or LOD), and weapon lighting checked on real GPUs.
4. Skins built on the UVs with wear masks instead of model-space bands.
5. The sidearm, SMG and marksman rifle through the same pipeline.
6. One environment section at final quality (`docs/art/ENVIRONMENT_PRODUCTION.md`).
7. An authored operator (`docs/art/CHARACTER_PRODUCTION.md`).
8. Desktop-showcase and flagship tier definitions.

## Unverified

Physical Android/iOS frame time, thermals and touch feel, for every change on both branches. Every timing in this repository comes from Mesa llvmpipe software rendering and is relative only.

## Resume commands

```sh
git fetch origin && git worktree list
SIGHTBREAK_TOOLS_DIR=<tools> ./scripts/validate.sh
SIGHTBREAK_TOOLS_DIR=<tools> ./scripts/godot.sh --headless --script res://tests/weapon_art_test.gd
DISPLAY=:99 ./scripts/godot.sh --audio-driver Dummy --resolution 1280x720 --script res://tests/weapon_art_capture.gd -- --capture-dir=<out> [--procedural]
```
