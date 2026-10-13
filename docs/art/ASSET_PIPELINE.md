# Asset pipeline

Every authored mesh and texture is produced by code in `tools/art/` from numeric parameters, so any change is a reviewable diff and any asset can be rebuilt. Nothing is downloaded or purchased; see `tools/art/REFERENCES.md`.

## Tools

| Tool | Version | Use |
| --- | --- | --- |
| Blender as a Python module (`bpy`, PyPI) | 5.2.2 (Python 3.13) | Modelling, UVs, Cycles CPU baking, glTF export; headless, no GUI or GPU |
| Pillow + NumPy (system Python) | 12.3 / 2.5 | Packing bake passes into game textures |
| Godot | 4.7.2 official | Import, integration tests, native captures |

Set up with `python3.13 -m venv <tools>/bpy-venv && <tools>/bpy-venv/bin/pip install bpy==5.2.2`. Draco and meshopt compression libraries are absent from the wheel; the pipeline does not use them.

## Stages

```
generator.py ──► render_views.py   (Cycles review renders; nothing written to the game)
      │
      └──────► bake.py ──► <name>.blend + raw 2048² passes
                               │
                               ├──► export.py   ──► <name>.glb    (game mesh groups and markers)
                               └──► textures.py ──► <name>_{albedo,orm,normal}.png (1024²)
                                                         │
                     game/assets/weapons/<asset>/ ◄──────┘  + <name>.tres material
```

| Script | Does |
| --- | --- |
| `hardsurface.py` | The modelling toolkit: filleted 2D profiles; two-view silhouette modelling (side profile ∩ plan profile); lathe; EXACT booleans that keep the target's material; bevel, harden-normals and weighted-normal finishing |
| `relay_ar.py` | The Relay AR rifle generator. It declares the mesh `GROUPS` and hand `ANCHORS` that `export.py` reads |
| `relay_ar_hands.py` | Gloved hands and sleeves posed on the rifle: flattened ellipsoid phalanges through explicit joints (knuckles come from the overlaps), palm, heel and thenar masses, tapered oval sleeves with folds and a seam, flared cuffs and wrist straps. Hands are fused by a voxel remesh, smoothed and decimated |
| `viewmodel_fit.py` | Fits the first-person placement constants in `weapon_model.gd`: it projects rifle landmarks through the game camera and searches for the pitch, yaw and offset that best match screen targets |
| `render_views.py` | Cycles views that frame themselves from object bounds: left and right ¾, side profile, top, receiver, grip and magazine, materials, both hands. `eye` reproduces the in-game first-person camera (82° vertical field of view) from the placement in `weapon_model.gd` |
| `bake.py` | Smart-UV atlas, then object-space procedural surfaces (tone, grain, directional scratches, edge chipping, grime, stipple). It bakes albedo, roughness, tangent normal (OpenGL +Y), 3.5 cm contact AO and metallic, and saves the unwrapped `.blend` |
| `export.py` | Joins parts into one mesh per draw group, splits the magazine's cartridge into a child, adds marker and anchor empties, and exports the GLB. UVs and normals are left exactly as baked |
| `textures.py` | Lanczos resize to 1024², packs ORM (R occlusion, G roughness, B metallic) and renormalises the normal map |

## Rebuilding the Relay AR

```sh
B=<tools>/bpy-venv/bin/python; T=tools/art; OUT=<scratch>
$B $T/bake.py $T/relay_ar.py $OUT/rifle --size 2048 --samples 48               # ~15 min on 4 vCPU
$B $T/export.py $T/relay_ar.py $OUT/rifle game/assets/weapons/relay_ar/relay_ar.glb
python3 $T/textures.py $OUT/rifle relay_ar game/assets/weapons/relay_ar
$B $T/bake.py $T/relay_ar_hands.py $OUT/hands --size 1024 --samples 32
$B $T/export.py $T/relay_ar_hands.py $OUT/hands game/assets/weapons/relay_ar/relay_ar_hands.glb
python3 $T/textures.py $OUT/hands relay_ar_hands game/assets/weapons/relay_ar
./scripts/godot.sh --headless --editor --quit                                  # import
./scripts/godot.sh --headless --script res://tests/weapon_art_test.gd          # contract
```

Review renders: `$B $T/render_views.py $T/relay_ar.py <dir> [view ...] --samples 48`. For the rifle with hands, use a two-line module that calls `relay_ar.build()` then `relay_ar_hands.build(reset=False)`.

## Conventions

- **Space:**
  - Metres, Blender Z up, barrel along +Y. glTF export converts this to Godot's −Z barrel, +Y up.
  - The receiver rear is at the origin and the bore at 0.025 m, matching the procedural rifle.
- **Naming contract** (read by `SBWeaponModel`):
  - `paint_*` take the cosmetic finish (two groups: receiver and handguard);
  - `stock` is the buttstock, a separate mesh that first person leaves out;
  - `magazine` has its pivot at the seated top, with the `magazine_rounds` child;
  - `body` is everything else;
  - `hands` is a separate GLB;
  - `muzzle` and `ejection` are marker empties;
  - `grip_hand` and `support_hand` are hand anchors.
- **Materials:**
  - One atlas and one `ORMMaterial3D` per GLB.
  - Paint parts carry `detail_orm` and `detail_normal` metadata so `CosmeticMaterial.apply` keeps baked occlusion and normals under any finish.
- **Import:** textures use Godot's VRAM compression (ETC2/ASTC on mobile, S3TC/BPTC on desktop, both already enabled in `project.godot`) with mipmaps; the normal map is imported as a normal map.
- **Determinism:**
  - Geometry is fully determined by the generator.
  - Smart-UV packing is deterministic for identical geometry, so a geometry change needs a re-bake before export.
  - `export.py` refuses nothing, so check `weapon_art_test.gd` afterwards.
