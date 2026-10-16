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

## First-person lighting: the viewmodel environment (art-v10)

First-person surfaces (`ViewmodelShading.SURFACE` and the first-person cosmetic finish, so the default and every skin) declare `render_mode ambient_light_disabled`. The engine's sky radiance and ambient light are not applied to them; `ViewmodelShading.STUDIO` supplies a fixed environment instead: the arena's flat ambient colour (`viewmodel_ambient`, (0.165, 0.214, 0.254)) for the diffuse part, a ground-bounce term for surfaces that face down (`viewmodel_bounce`, arms only), and a reflection of a small studio (an edge-free sky-to-ground gradient, a key panel up and to the left, a thin cool strip behind on the right) through Schlick Fresnel with the baked metalness and roughness, the detail normal and the baked occlusion. The sun remains the engine's directional light with the baked roughness.

Why: the engine's sky has a bright horizon band, and one `ROUGHNESS` controls both the sun's highlight and the sky's reflection; a weapon that rolls and lifts slides the band across the metal and its colour swings. The previous remedy (a roughness floor of 0.8) removed the swing and flattened the sun's response with it (`docs/reports/media/art-v10/materials/README.md`). Consequences: the viewmodel no longer reflects the world (a red wall does not tint the metal); a map with another ambient colour must set `viewmodel_ambient` (nothing does yet); the ambient and reflection terms are the same constants in a dark interior (the only world-dependent terms are the engine's own lights: the sun and any omni light), which keeps the weapon readable without touching the world camera's lighting or any enemy's visibility. Inspection and third-person models keep the engine's own lighting (asserted in `weapon_art_test.gd`).
