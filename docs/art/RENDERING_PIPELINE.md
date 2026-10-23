# Rendering pipeline

## Renderer

- **Godot 4.7.2 GL Compatibility** (OpenGL ES 3 / WebGL 2 class), on desktop and mobile (`project.godot`).
- The Forward+ and Mobile renderers are not used. SSR, SSAO, SSIL, SDFGI and volumetric fog are therefore unavailable, and the art must not depend on them.
- Lighting:
  - One `DirectionalLight3D` sun with two shadow cascades out to 60 m;
  - colour ambient (`aabfcf`, 0.41);
  - Filmic tonemapping;
  - depth fog from 34 m.

## Materials

| Use | Material | Maps |
| --- | --- | --- |
| Authored weapons and hands | `ORMMaterial3D` (`relay_ar_body.tres`, `relay_ar_hands.tres`) | albedo (sRGB), ORM (R occlusion, G roughness, B metallic), tangent normal (OpenGL +Y) |
| Cosmetic paint parts | `CosmeticMaterial` shader (one program for every finish) | Procedural finish plus the authored model's baked occlusion and normal through `detail_orm` and `detail_normal` (`detail` = 1) |
| Procedural weapons and environment boxes | `StandardMaterial3D` with vertex colour, or the three tiling PBR sets in `assets/materials` | Unchanged by this initiative |

Viewmodel meshes do not cast shadows, which avoids self-shadow acne at near-plane scale and saves a pass. They still receive the sun's shadow.

## Quality tiers today

| Setting | Effect |
| --- | --- |
| LOW | No sun shadows; environment normal and roughness maps off |
| STANDARD | Shadows and environment detail maps on |
| 3D render scale 0.5–1.0 | Bilinear 3D scaling |

The authored first-person rifle uses the same maps on both tiers. A tier hook (smaller mip bias or LOD on LOW) is listed as next work in `VISUAL_GAP_ANALYSIS.md`.

## Planned within this renderer

- `LightmapGI` bakes for static environment sections (supported in Compatibility).
- Reflection probes for interiors.
- Decals for wear and signage.
- Trim sheets for modular architecture.

Each needs measurement on LOW and STANDARD before it ships.
