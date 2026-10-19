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

### The machined metal (art-v11, sun-metal track)

The Relay AR's metal (receiver, rails, barrel, suppressor: where the baked metalness is high; the polymer handguard, the tan magazine, the grip and the arms are not) takes a finish of its own in first person (`ViewmodelShading.metal()`, called for the rifle body in `weapon_model.gd` and for the first-person cosmetic finish, so the default and every skin). Four parts, each a uniform that defaults to "off" so nothing else changes:

- **Rebuilt detail normal** (`viewmodel_normal_fix`). The baked normal maps are imported RG-only (`compress/normal_map=1`; the engine's own normal mapping rebuilds z from x and y), so the studio, which read the blue channel itself, got z = -1: an inside-out detail normal, bevels leaning the wrong way, n.v of 0 on every face. The rifle now rebuilds z. Schlick's term deliberately stays at grazing incidence (what shipped): evaluated at the real n.v the receiver's median luma swung 1.25 to 1.31 through the reload, against the unchanged 1.25 bound. The arms keep the old normal (their ground-bounce term reads `-n.y` and their hip-sleeve bounds were measured with it; it lights up-facing rather than down-facing surfaces, reported, not changed).
- **Reflectance and kept diffuse** (`viewmodel_f0` 0.15, `viewmodel_diffuse` 0.45). Baked albedo 0.03 linear and metalness 0.44 gave an engine f0 of 0.036 (a black glossy dielectric), and the warm sun's diffuse on it was most of the olive. `REFLECTANCE` remaps ALBEDO and METALLIC (what the engine's sun reads) so the diffuse is 45 % of what it was and the reflectance 0.15, ramped by the baked metalness so polymer and the magazine are untouched.
- **Cool gradient** (`viewmodel_metal_reflect` 0.45 against 0.30): the studio's constant gradient replaces the diffuse the metal gave up. The key and strip lobes keep their default strength (a lobe gain of 8 put 234 of 255 on the suppressor in a dark interior).
- **Weapon-fixed finish grain** (`viewmodel_variation` 0.30): a slow swell along the barrel and a fine brushed grain along it, in object space, on the metal's reflection only, zero on average, faded by `fwidth` where a pixel spans more than a third of its period. A flat face under a distant environment has one reflection direction over its whole area, so no environment can put structure on it without making the whole face swing with the pose; a surface-fixed variation can. It is a shader stand-in for authored wear and brushing in the bake, which is the next step (`docs/reports/media/art-v11/sunmetal/README.md`).

Every constant is empirical (comments in `viewmodel_shading.gd`); `scripts/test_sun_metal.py` pins the measured bounds, `reload_negative_controls.py` N37 to N43 inject each failure mode.

