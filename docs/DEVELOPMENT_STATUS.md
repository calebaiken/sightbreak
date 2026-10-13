# Development status

Updated 2026-10-13 by Claude (cloud session). Read this first when resuming work.

## Branches and pull requests

| Branch | Head | State |
| --- | --- | --- |
| `main` | `e67f2c8` | 0.3.0-dev baseline |
| `claude/independent-audit-visual-v04` (PR #1 → `main`) | `77e0433` | Codex's three blockers and the second review's findings are fixed. **Unmerged; waiting for Codex review.** Not a release candidate. |
| `claude/cs2-fidelity-art-production` (stacked on PR #1) | this branch | First vertical slice of the graphics initiative. Merge only after PR #1, as its own reviewed PR. |
| `codex/competitive-network-systems` (Codex) | `acfa704` | Network privacy (protocol 3), stacked on PR #1's earlier head `cf9a630`. A local trial merge onto `77e0433` was clean. |

Ownership (from Codex's `docs/engineering/PARALLEL_WORK.md`):
- **Codex:** networking, server lifecycle, backend, measurement and build tooling.
- **Claude:** meshes, materials, shaders, visual UI, animation and art production.
- **Shared:** `match.gd` changes must be small integration commits.

## Done on the art branch

- **Asset pipeline:** `tools/art/` with headless Blender (bpy 5.2.2): generators, bake, export, texture packing and review renders. See `docs/art/ASSET_PIPELINE.md`.
- **Relay AR rifle:** original, real scale, 30,326 triangles, 1024² baked PBR set.
- **First-person hands:** gloved hands and sleeves, 9,684 triangles; the viewmodel is fitted (about 6° of roll) with `tools/art/viewmodel_fit.py`.
- **Integration:**
  - the authored rifle in first person and inspection, with the weapon contract unchanged (`docs/art/WEAPON_PRODUCTION.md`);
  - casings leave from the authored ejection port;
  - cosmetic finishes keep the baked occlusion and normals, and with no skin the rifle shows its baked surface;
  - the procedural rifle remains the fallback.
- **Tests:**
  - `weapon_art_test.gd` (43 checks) runs in `validate.sh`;
  - `weapon_art_capture.gd` takes the in-engine captures;
  - `weapon_render_benchmark.gd` measures relative cost.
- **Docs:** `docs/art/` (gap analysis with reference-access limits, direction, pipeline, budgets, weapon, character, environment, animation, rendering, visual QA, performance).

## Not done (in priority order)

Visual review of this slice (same model family; see `docs/art/VISUAL_QA.md`): first-person presentation about 4.8 → 5.4 on the project's rubric. Whole-game effect is about +0.1, still below 7, and far below the 8.5 target.

1. Hands: rigged gloves with real finger anatomy; sleeve folds and gear; less viewmodel roll; support hand at mid-handguard.
2. The rifle's LOW-tier hook (mip bias or LOD), and weapon lighting checked on real GPUs.
3. Skins built on the UVs with wear masks instead of model-space bands.
4. Reload and inspect animation with an articulated hand rig.
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
