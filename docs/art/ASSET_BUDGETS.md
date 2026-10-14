# Asset budgets

The budgets are design limits. They are not measurements of device performance. Physical-device frame time, thermals and battery are **unverified** for every tier. The cloud build host renders on Mesa llvmpipe (CPU), whose timings show relative cost only (see `PERFORMANCE_REPORT.md`).

## Tiers

| Tier | Target | Status |
| --- | --- | --- |
| Desktop showcase | Desktop GPUs; can raise texture size and shadow quality | Not defined in game settings yet |
| Flagship mobile | Recent high-end phones | Maps to STANDARD today |
| Standard mobile | Mid-range phones | STANDARD with render scale 0.75–1.0 |
| Low mobile | Older or thermally limited phones | LOW: no shadows, no environment normal/roughness maps, render scale down to 0.5 |

The game exposes two quality settings (LOW and STANDARD) plus a render-scale slider. The first-person weapon does not yet change with the tier.

## First-person weapon (per equipped weapon)

| Item | Budget | Relay AR |
| --- | --- | --- |
| Triangles, weapon | ≤ 32,000 | 30,326 (25,194 in first person, which omits the stock) |
| Triangles, hands and sleeves | ≤ 10,000 | Rigged arms (default): 7,828, both arms, 34 bones, one skinned mesh. v3 was 10,672 and over budget; the contract test allowed 12,000 and now allows 10,000. Static v2 hands (fallback): 9,800 |
| Animation | 1 clip per weapon | `reload`, 1 s, sampled at 30 fps, seeked by reload progress |
| Draw nodes in the viewmodel | ≤ 6 (asserted) | 6 |
| Texture sets | 1 atlas per GLB | 2 in first person (rifle, arms); the v2 hands' set loads only when they are used as the fallback |
| Texture size shipped | ≤ 1024² per map | 1024² albedo, ORM and normal for each |
| Texture memory (VRAM-compressed, with mips) | ≤ 8 MB per weapon including hands | 5.59 MB (rifle 2.80 MB plus arms 2.80 MB), measured from the imported S3TC/BPTC and ETC2 `.ctex` files |
| Shadow casting | Off for the viewmodel | Off |
| Materials | 1 `ORMMaterial3D` + 1 shared cosmetic shader | As budgeted |

The 2048² bake sources stay outside `game/` and are rebuilt by the pipeline. Only the 1024² maps ship.

## Planned budgets (not yet produced)

| Asset class | Triangles | Textures | Notes |
| --- | --- | --- | --- |
| Other first-person weapons | ≤ 24,000 (sidearm ≤ 14,000) | 1024² set | Same contract as the rifle |
| Third-person weapon | ≤ 4,000 | Shares the first-person atlas at a lower mip | Needs an LOD export |
| Operator | ≤ 18,000 LOD0, ≤ 6,000 LOD1, ≤ 2,000 LOD2 | 1024² body + 512² gear | Team colour from material parameters, not textures |
| Environment hero prop | ≤ 6,000 | Trim sheet 1024² shared | Batching-friendly; static |
