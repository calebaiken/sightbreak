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
| `sdf.py` | Signed-distance modelling with NumPy only: rounded and capped cones, ellipsoids, rounded boxes, tori, smooth union and difference, bounded composition, material regions, and naive surface-nets meshing |
| `relay_ar_arms.py` | Arms v3 anatomy. One right arm in a relaxed rest pose from landmarks: carpal block, arched metacarpals, thenar and hypothenar masses, three phalanges per finger with condyles and palmar creases, and the thumb. The glove adds a 1 mm dilation, knuckle guard, padded phalanges, seams, cuff and strap. A real-length jacket sleeve has a hem, a seam and irregular folds. It also defines the bone positions |
| `arms_build.py` | Builds the rigged arms from `relay_ar_arms.py`: <ul><li>meshes the high-poly bake source and a QuadriFlow game mesh (after a voxel remesh and decimation);</li><li>builds a 34-bone skeleton with bone-heat weights and mirrors the left arm;</li><li>places both arms on the rifle and closes the fingers on its surface by contact (BVH), with a multi-start reach for the trigger finger;</li><li>bakes 2048² passes from high to low;</li><li>applies the hold as the bind pose, solves the magazine grab and keys the 1 s `reload` clip;</li><li>exports a skinned GLB.</li></ul> The log reports every finger's solved angles and any digit it could not close (`None`) |
| `rebake_part_ao.py`, `patch_part_ao.py` | Fix the baked occlusion of a part that moves in game. `bake.py` bakes occlusion with every part in place, so a part baked while seated (the magazine, which reload pulls out of the magwell) comes out with its hidden faces fully occluded and black once it moves. `rebake_part_ao.py` re-bakes one object from the retained unwrapped `.blend` with everything else hidden, onto a black and a white canvas (the part's UV islands are the texels where they agree); `patch_part_ao.py` merges it into the full occlusion bake on those texels only. Check the provenance first: `textures.py` on the unpatched bake must reproduce the shipped textures exactly |
| `render_arms.py` | Cycles review renders of the shipped rifle and arms GLBs with the shipped 1024² textures: ¾ views, both hands from both sides, the in-game eye at the viewmodel field of view, and two reload frames |
| `motion_sheet.py` | Labelled contact sheet from a `game/tests/weapon_motion_capture.gd` frame sequence (frame, simulated time, phase, ammunition, clip time) |
| `viewmodel_fit.py` | Fits the first-person placement constants in `weapon_model.gd`: it projects rifle landmarks through the viewmodel projection (`--fov`, 54° by default) and searches for the pitch, yaw and offset that best match screen targets. `--layout v4` adds vanishing-point, reach, magazine-well and buffer-tube terms; it was evaluated and not adopted (see `VISUAL_QA.md`) |
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

The rigged arms replace the v2 hands as the default; the v2 hands above remain the fallback.

```sh
$B $T/arms_build.py $OUT/arms --size 2048 --samples 48                        # mesh, rig, grip solve, bake, clip, GLB
cp $OUT/arms/relay_ar_arms.glb game/assets/weapons/relay_ar/
python3 $T/textures.py $OUT/arms relay_ar_arms game/assets/weapons/relay_ar
$B $T/render_arms.py <dir> --samples 32                                        # review renders of what ships
```

`build_rig(..., preview=True)` in `arms_build.py` stops before baking, which takes about a minute. Use it to iterate on the hold and the grab, and read the per-finger report after every build.

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
  - `hands` is a separate GLB (v2, the static fallback);
  - `relay_ar_arms.glb` holds one skinned mesh `arms`, a skeleton with `R_*` and `L_*` bones, and the `reload` clip;
  - `muzzle` and `ejection` are marker empties;
  - `grip_hand` and `support_hand` are hand anchors.
- **Materials:**
  - One atlas and one `ORMMaterial3D` per GLB.
  - In first person the rifle and arms draw with `SBViewmodelShading.surface()` (the 54° viewmodel projection). The cosmetic finish has a separate first-person shader variant: a shader that writes `POSITION` must never be shared with inspection or third person (see `VISUAL_QA.md`, review of `5100b3e`).
  - Paint parts carry `detail_orm` and `detail_normal` metadata so `CosmeticMaterial.apply` keeps baked occlusion and normals under any finish.
- **Import:** textures use Godot's VRAM compression (ETC2/ASTC on mobile, S3TC/BPTC on desktop, both already enabled in `project.godot`) with mipmaps; the normal map is imported as a normal map.
- **Determinism:**
  - Geometry is fully determined by the generator.
  - Smart-UV packing is deterministic for identical geometry, so a geometry change needs a re-bake before export.
  - `export.py` refuses nothing, so check `weapon_art_test.gd` afterwards.
