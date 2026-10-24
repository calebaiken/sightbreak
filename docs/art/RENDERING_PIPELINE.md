# Rendering pipeline

## Renderer

- **Godot 4.7.2 GL Compatibility** (OpenGL ES 3 / WebGL 2 class), on desktop and mobile (`project.godot`).
- The Forward+ and Mobile renderers are not used. SSR, SSIL, SDFGI and volumetric fog are unavailable, and the art must not depend on them. SSAO, glow and colour adjustment do render in Compatibility (measured on 4.7.2, `GRAPHICS_BACKLOG.md`); they switch the renderer to a post pass, so they are tier features, not defaults.
- Lighting:
  - One `DirectionalLight3D` sun (1.05) with two shadow cascades out to 60 m;
  - colour ambient (`aabfcf`, 0.85: the shadow fill that keeps the defender half readable);
  - Filmic tonemapping;
  - depth fog from 34 m.

## Materials

| Use | Material | Maps |
| --- | --- | --- |
| Authored weapons and hands | `ORMMaterial3D` (`relay_ar_body.tres`, `relay_ar_hands.tres`) | albedo (sRGB), ORM (R occlusion, G roughness, B metallic), tangent normal (OpenGL +Y) |
| Cosmetic paint parts | `CosmeticMaterial` shader (one program for every finish) | Procedural finish plus the authored model's baked occlusion and normal through `detail_orm` and `detail_normal` (`detail` = 1) |
| Procedural weapons and environment boxes | `StandardMaterial3D` with vertex colour, or the three tiling PBR sets in `assets/materials` | Unchanged by this initiative |

Viewmodel meshes do not cast shadows, which avoids self-shadow acne at near-plane scale and saves a pass. They still receive the sun's shadow.

## Quality tiers

Defined in `game/scripts/gameplay/graphics_quality.gd` (one table, tested by `tests/graphics_quality_test.gd`). Evidence and the measured no-op settings are in `GRAPHICS_BACKLOG.md`.

| Tier | Shadows | MSAA | Post pass | SSAO | Texture filtering | Platforms |
| --- | --- | --- | --- | --- | --- | --- |
| 0 LOW | off; environment normal and roughness maps off | off | no | no | trilinear | all |
| 1 MEDIUM | on | 2x | no | no | trilinear | all (the old STANDARD) |
| 2 HIGH | on | 2x | yes | no | 4x anisotropic | desktop |
| 3 ULTRA | on | 4x | yes | yes | 16x anisotropic | desktop |

Phones and tablets are capped at MEDIUM until a physical-device frame-time record exists (`SBGraphicsQuality.MOBILE_MAX`). A 3D render scale of 0.5 to 1.0 (bilinear) applies on every tier.

The authored first-person rifle uses the same maps on every tier.

## Planned within this renderer

- `LightmapGI` bakes for static environment sections (supported in Compatibility).
- Reflection probes for interiors.
- Decals for wear and signage.
- Trim sheets for modular architecture.

Each needs measurement on LOW and STANDARD before it ships.
