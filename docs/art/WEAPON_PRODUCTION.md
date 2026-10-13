# Weapon production

The standard every first-person weapon follows, using the Relay AR as the worked example. Gameplay values (damage, recoil, fire cadence, magazine size, spread, hit registration) live in `game/scripts/gameplay/weapons.gd` and the authoritative actor code. A weapon model never reads or changes them.

## Relay AR (rifle), v1

- **What it is:** an original 5.56-class carbine designed for SIGHTBREAK. It is AR-pattern in layout but not a copy of any real or game model. Its distinguishing features are:
  - a skeletonised stock with a cheek riser and sling slot;
  - a raked polymer grip;
  - an angular reflex sight;
  - a three-port brake;
  - a slotted rounded-hexagon handguard with a hand stop.
- **Scale:** 0.95 m overall, a 36 mm upper receiver and a 14.5-inch-class barrel. It is real scale; the viewmodel places it rather than inflating it.
- **Parts (38):**
  - upper receiver with ejection port, open dust cover, deflector and flutes;
  - lower receiver with magwell, flared lip, trigger guard and controls;
  - pistol grip;
  - buffer tube, castle nut, stock, lever and butt pad;
  - barrel, gas block and muzzle brake;
  - handguard, two Picatinny rails, QD cup, cap screws and hand stop;
  - optic body, lens, knob and clamp;
  - magazine with cartridge.
- **Materials:**
  - dark anodised aluminium (receivers, handguard and rails; these are the cosmetic paint surfaces);
  - parkerised steel;
  - earth-tone polymer furniture (stock, grip, magazine, hand stop) for two-tone readability;
  - rubber and brass.

| Game mesh | Triangles | Draw | Role |
| --- | ---: | --- | --- |
| `paint_receiver` | 4,508 | 1 | upper, lower and upper rail; takes the cosmetic finish |
| `paint_handguard` | 7,976 | 1 | handguard and its rail; takes the cosmetic finish |
| `body` | 11,082 | 1 | every non-paint, non-stock part |
| `stock` | 5,132 | 1 (inspection only) | the buttstock, which is behind the camera in first person and is left out there |
| `magazine` + `magazine_rounds` | 1,392 + 236 | 2 | animated by reload |
| **Rifle total** | **30,326** (**25,194** in first person) | **5** (**4** in first person, plus the cartridge) | budget 32,000 |
| `hands` (separate GLB) | 9,800 | 1 | budget 10,000 |

The first-person node therefore holds six draw nodes: body, two paint parts, magazine, hands and muzzle flash. The magazine's cartridge is one more draw. The procedural rifle used five draws plus the magazine detail.

## Gameplay contract (unchanged)

| Contract | How the authored rifle meets it | Verified by |
| --- | --- | --- |
| Barrel along −Z, bore at +Y 0.025 | Generator space with glTF conversion | `weapon_art_test.gd` |
| Muzzle flash origin | `muzzle` empty | `weapon_art_test.gd` |
| Casing origin | `ejection` empty, reported to the actor | `weapon_art_test.gd` |
| Magazine moves on reload and reseats | `magazine` pivot at its seated top; the actor's existing extraction offsets | `actor_test.gd`, `weapon_art_test.gd` |
| Two paint parts take one finish | `paint_receiver` and `paint_handguard` | `actor_test.gd`, `render_budget_test.gd` |
| Finishes are presentation only | `CosmeticMaterial.apply` binds the material and baked detail; no stat is read | `actor_test.gd` (cosmetic seed affects the paint material only) |
| Inspection uses the same geometry without hands | `build(..., hands = false)` skips the hands GLB and keeps the stock | `actor_test.gd`, `weapon_art_test.gd` |
| Tilts turn the rifle about its middle | The model reports a `pivot` (the balance point between the hands). The actor adds it to the node's rest position and the model is offset by the same amount, so the rest pose is unchanged | `weapon_art_test.gd` |
| First person never shows the buttstock | The stock is its own mesh and first person omits it | `weapon_art_test.gd` |
| Shared geometry across equips | The packed scene is cached by id, hands and placement | `render_budget_test.gd` |
| Procedural fallback | `SBWeaponModel.use_authored = false` or missing asset | `weapon_art_test.gd` |

Recoil kick, sway, bob, equip and reload tilt still move the whole weapon node with the same formulas and amplitudes. The actor changes are presentation only: `apply_cosmetic` delegates to `CosmeticMaterial.apply`, casings leave from the authored `ejection` marker, and the node's rest position is a named constant plus the model's optional pivot. Procedural weapons have no pivot and keep the previous rest position and casing offset. No gameplay value is read or changed.

## Viewmodel placement

`weapon_model.gd` places the rifle inside the camera-attached node, which rests 0.235 m right, 0.235 m down and 0.42 m ahead of the eye:
- **Rotation:** YXZ Euler (−0.05, 0.27, −0.10) rad, so about 6° of roll and 15° of yaw. The barrel converges toward the crosshair and the left receiver face and handguard read.
- **Offset:** (0.087, 0.082, 0.149) m in the weapon node's space.
- **Result at 1280×720:**
  - the muzzle sits near the crosshair;
  - the support hand is at mid-handguard;
  - the reflex sight is right of centre;
  - the pistol-grip hand is at the lower right;
  - the stock ends behind the camera.
- **Derivation:** `tools/art/viewmodel_fit.py` projects rifle landmarks through the game camera (82° vertical field of view) and fits the pitch, yaw and offset to screen targets. Rerun it when the rifle's proportions change.
- **Aspect ratios** (captures in `docs/reports/media/art-v1/captures/aspect-ratios/`, at their real sizes):
  - 16:9 (1280×720) is the fitted layout.
  - At 20:9 (1600×720) the whole rifle stays in frame.
  - At 4:3 (1024×768) the horizontal view is narrower: the optic is partly cut and the firing hand is off-screen, though the muzzle, handguard and support hand still read.
  - **Open question for the project's display settings:** `project.godot` sets `canvas_items` stretch with no explicit `stretch/aspect`, and Godot's default (`keep`) letterboxes screens wider than 16:9. The landscape UI tests set `root.size` directly, so they do not show what a real 20:9 device gets. I have not verified how the Android and iOS exports handle this.

The placement is presentation only. Shots trace from the camera, as before.

## Adding the next weapon

1. Write `tools/art/<weapon>.py` with `build()`, `GROUPS` and `ANCHORS` on the same axes and contract, with real dimensions.
2. Iterate with `render_views.py` (all seven views plus `eye`) until no defect shows; record the renders.
3. Bake and export it, pack its textures, and write a `.tres`; then pose hands with a hands generator.
4. Add the id to `SBWeaponModel` the same way `_build_authored_rifle` does, and extend `weapon_art_test.gd`.
5. Capture it with `game/tests/weapon_art_capture.gd`, then review it against `docs/art/VISUAL_QA.md`.
