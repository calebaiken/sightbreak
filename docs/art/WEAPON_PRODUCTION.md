# Weapon production

The standard every first-person weapon follows, using the Relay AR as the worked example. Gameplay values (damage, recoil, fire cadence, magazine size, spread, hit registration) live in `game/scripts/gameplay/weapons.gd` and the authoritative actor code. A weapon model never reads or changes them.

## Relay AR (rifle), v1

- **What it is:** an original 5.56-class carbine designed for SIGHTBREAK. It is AR-pattern in layout but not a copy of any real or game model. Its distinguishing features are:
  - a skeletonised stock with a cheek riser and sling slot;
  - a raked graphite pistol grip (v8: palm swell, a flared base, three finger grooves and a recessed stippled panel on each side);
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
  - furniture in two polymers for readability: graphite (`grip_polymer`: stock, pistol grip, hand stop) and earth-tone (`polymer`: the magazine). The v7 grip and magazine were the same tan, and a glove on the grip measured the same median luma as the grip (89 and 91 in sun); in the game the grip is also darkened to 0.3 of its baked albedo (`GRIP_DARKEN` in `weapon_model.gd`) and given no fill floor, which makes it the darkest thing in the hand (51 in sun against the gloves' 89);
  - rubber and brass.

| Game mesh | Triangles | Draw | Role |
| --- | ---: | --- | --- |
| `paint_receiver` | 4,508 | 1 | upper, lower and upper rail; takes the cosmetic finish |
| `paint_handguard` | 7,976 | 1 | handguard and its rail; takes the cosmetic finish |
| `body` | 10,094 | 1 | every non-paint, non-stock, non-grip part |
| `grip` | 1,976 | 1 | the pistol grip (its own mesh since v8, so it can be measured and tinted apart) |
| `stock` | 5,040 | 1 (inspection only) | the buttstock, which is behind the camera in first person and is left out there |
| `magazine` + `magazine_rounds` | 1,392 + 236 | 2 | animated by reload |
| **Rifle total** | **31,222** (**26,182** in first person) | **6** (**5** in first person, plus the cartridge) | budget 32,000 |
| `hands` (separate GLB, v2 static fallback) | 9,800 | 1 | budget 10,000 |
| `arms` (`relay_ar_arms.glb`, rigged, default) | see `ASSET_BUDGETS.md` | 1 | budget 10,000 |

The first-person node therefore holds seven draw nodes since v8: body, grip, two paint parts, magazine, hands (or rigged arms) and muzzle flash (`weapon_art_test.gd` allows seven). During a reload the spare magazine and, after a shot, the muzzle smoke are two more (nine nodes counted by `reload_perf_probe.gd`; draw calls 31 ready, 34 mid-reload on the host's renderer, against 30 and 33 at `fceefa1`). The magazine's cartridge is one more draw. The procedural rifle used five draws plus the magazine detail.

## Kestrel 9 (sidearm), v1

- **What it is:** an original compact 9 mm service pistol built for SIGHTBREAK, not a copy of any real or game model. Distinguishing features: a faceted hex-section slide with two sight teeth and a hooked front end (the "beak"), a 17 degree raked grip that matches the Relay AR's, six stadium serration slots per flank, an ejection port with a visible extractor, an open square trigger guard with a three-slot accessory rail, and a squared tan magazine foot.
- **Scale:** 0.1955 m overall, 0.1435 m high with the magazine, bore on the same 0.025 m axis as the rifle. Placed in first person at scale 1.05 (a real-scale pistol reads small at a viewmodel field of view built for a 0.95 m rifle).
- **Parts (19 objects):** slide with sight pockets, striker plate, rear sight, front sight with a brass bead (4.4 mm, the aiming dot), barrel and collar, chamber block, extractor, guide rod, frame and grip, trigger, slide stop, magazine release and boss, three pins, and the magazine with its top round.
- **Mesh groups:** `paint_slide` (takes the cosmetic finish), `grip`, `magazine` + `magazine_rounds`, `body`.
- **Triangles:** 6,954 for the pistol (budget 14,000): `paint_slide` 1,266, `grip` 1,336, `magazine` 962 + 164, `body` 3,226. The hands (`kestrel_9_hands`, static) are 9,800 (budget 10,000).
- **Draws in first person:** body, slide, grip, magazine (+ round), hands, muzzle flash: within the seven the weapon art test allows.
- **Textures:** albedo, ORM and normal at 1024 for the pistol and for the hands (`game/assets/weapons/kestrel_9/`).
- **Hands:** `tools/art/kestrel_9_hands.py` reuses the Relay AR hands' building blocks. The firing hand lies on the right face of the grip with its index finger along the frame to the trigger and its thumb forward on the left; the support hand lies on the left face with its fingers over the firing hand's and its thumb along the dust cover; forearms run back and down out of frame. There are no rigged arms for the pistol: a reload tilts the pistol and moves its magazine.
- **Lessons recorded here:** the front bead was first built at the model origin (z 0) because `lathe` takes its centre from the caller; the magazine baked 81% almost fully occluded (it seats inside the grip) and drew black, fixed with `rebake_part_ao.py` and `patch_part_ao.py` (0.8% after); the shared flash mesh is sized for a rifle and covered the pistol's sights, so the model reports `flash_scale` 0.62; the rifle's grip darkening (0.24) drew the pistol's frame as a black column, so it uses 0.55 with a fill floor.
- **Measured and judged:** see `docs/reports/gauntlet/kestrel-9-v1/`. Two blind rounds against the procedural sidearm: six pairs to none each time, 29.5 then 35 of 60 against about 24. Open defects the critic ranked: the pistol and arms cover the middle of the view; the slide is one near-black material with thin sight nubs; the hands are lumpy and no reload motion reaches the magazine.

## Vectorline (SMG), v1

- **What it is:** an original compact pistol-calibre submachine gun built for SIGHTBREAK, not a copy of any real or game model. Distinguishing features: a squat slab-sided receiver with a stepped bench top and one ladder-rail spine, an open square sight window on an inverted-U foot (no lens: a real hole with two reticle ticks), a wide shroud with four vertical slots a side that steps down to a square muzzle block, a dead-vertical tan 30-round magazine ahead of the trigger guard, a 12 degree raked graphite grip, a closed picture-frame stock with a cheek riser (behind the camera in first person), and an earth-tone end plate (four grip ribs, a retaining screw, corner screws) on the receiver's rear face.
- **Scale:** 0.425 m from the receiver's rear face to the muzzle (0.565 m with the stock), bore on the same 0.025 m axis as the rifle. Placed in first person at scale 1.3.
- **Mesh groups:** `paint_receiver` (receiver, cover, rails and shroud: one finish covers the whole upper, and one draw fewer keeps the first-person weapon at six nodes), `grip`, `magazine` + `magazine_rounds`, `stock` (inspection only), `body`.
- **Triangles:** 17,152 (budget 22,000): `paint_receiver` 7,116, `body` 6,324, `stock` 1,952, `grip` 880, `magazine` 688 + 192. 15,200 in first person. The hands (`vectorline_hands`, static) are 9,800 (budget 10,000).
- **Draws in first person:** body, paint, grip, magazine (+ round), hands, muzzle flash: six.
- **Textures:** albedo, ORM and normal at 1024 for the weapon and for the hands (`game/assets/weapons/vectorline/`).
- **Hands:** `tools/art/vectorline_hands.py` reuses the Relay AR hands' building blocks. The firing hand lies on the right face of the grip with its index finger along the receiver's right flank to the trigger and its thumb forward on the left; the support hand holds the shroud from below in a C clamp, behind the chin that stops it; forearms run back and down out of frame. There are no rigged arms for the SMG: a reload tilts it and moves its magazine.
- **Lessons recorded here:** the magazine baked 23% almost fully occluded (it seats in a well) and was rebaked on its own (5.1% after, `rebake_part_ao.py` and `patch_part_ao.py`); the first-person view looks at the receiver's flat rear face once the stock is left out, which read as one black slab, so the generator got a bevelled end plate in an earth-tone polymer; its first version had a recessed round buffer cap that both critic rounds read as a camera lens, so it became four grip ribs and a retaining screw; a first, lighter plate colour blew out to cream in sun and was darkened twice; the bake table in `bake.py` and the material table in `hardsurface.py` both need a row for a new material (the bake failed with a `KeyError` before it had one).
- **Measured and judged:** see `docs/reports/gauntlet/vectorline-v1/`.

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
| Rigged arms present the reload, never drive it | The actor seeks the `reload` clip from a presentation clock that follows `reload_remaining` and never writes it; `use_rigged_arms = false` falls back to the static hands | `weapon_art_test.gd` (including a 20 Hz snapshot simulation) |
| One projection per first-person build | The authored rifle and whichever hands it has (rigged arms, static hands, procedural gloves) draw with the viewmodel projection; procedural weapons and their gloves with the camera's | `weapon_art_test.gd` |
| Inspection, case reveal and procedural weapons keep the engine's vertex transform | The world cosmetic shader never writes `POSITION`; only the first-person variant does, with the viewmodel projection set | `weapon_art_test.gd`; `paint_visibility_test.gd` (native display) |

Recoil kick, sway, bob, equip and reload tilt still move the whole weapon node with the same formulas and amplitudes. The actor changes are presentation only: `apply_cosmetic` delegates to `CosmeticMaterial.apply`, casings leave from the authored `ejection` marker, and the node's rest position is a named constant plus the model's optional pivot. Procedural weapons have no pivot and keep the previous rest position and casing offset. No gameplay value is read or changed.

## Viewmodel placement and projection

- **Projection:** first-person surfaces draw with their own 54° vertical projection (`SBViewmodelShading`, about 68° horizontal at 4:3), not the world camera's 82°. This removes the edge stretch. The projection scales the camera's own matrix, so the aspect ratio and the Y flip into viewport textures are kept.
- **Depth:** depth is compressed toward the near plane (clip space is reversed-Z), so the weapon never clips into a wall the player stands against.
- **Lighting:** an emission floor and a view rim are added. The v3 review measured the floor (0.08 × albedo) as negligible, so shade readability is still open.
- **Inspection and third person** use the engine's own transform. The cosmetic finish keeps a separate first-person shader variant; see the `5100b3e` review in `VISUAL_QA.md` for why a shared one broke inspection.
- **Placement:** `weapon_model.gd` places the rifle inside the camera-attached node, which rests 0.235 m right, 0.235 m down and 0.42 m ahead of the eye.
  - **Rotation:** YXZ Euler (−0.020, 0.174, −0.04) rad: about 10° of yaw and 2.3° of roll.
  - **Offset:** (0.065, 0.074, −0.005) m in the weapon node's space.
  - **Derivation:** `tools/art/viewmodel_fit.py` fits these through the 54° projection.
  - **Measured at 1280×720:**
    - the bore's vanishing point is 125 px left of the crosshair;
    - the support wrist bone is 0.88 m from the eye.
  - **A vanishing point at the crosshair** was evaluated (`--layout v4`, `docs/reports/media/art-v3/placement-eval/`) and not adopted. It forces the real-scale rifle almost parallel to the view, the handguard foreshortens and the support hand sits at the muzzle.
- **Reload staging with the rigged arms:**
  - **Pose:** the rifle moves into a held pose (`actor.gd` `ARMS_RELOAD_OFFSET` and `ARMS_RELOAD_ROTATION`) so the support hand and the whole magazine are in frame when the hand takes the magazine and when it seats it. The lift is 11 cm: at 9 cm the magazine's lowest vertex was 3.8 px inside a 720 px frame at the grab and 2.8 px outside it a moment later (Codex's review of `64ec598`). At 11 cm every vertex stays at least 1 % of the frame inside it from 12 to 15 % and from 82 to 88 % of the reload.
  - **Crosshair:** at its height the muzzle is at about (0.58, 0.48) of the frame, right of the crosshair.
  - **Tests:** `weapon_art_test.gd` pins the framing and the clear crosshair.
- **Aspect ratios:** `project.godot` uses `canvas_items` stretch with the default "keep" aspect, so 20:9 and 4:3 screens show the 16:9 frame with bars. Captures at other sizes show what a wider or taller canvas would frame, not what ships. The choice between "keep" and "expand" is open for the project owner and Codex.

The placement and staging are presentation only. Shots trace from the camera, and reload duration and ammunition come from the authoritative actor.

## Adding the next weapon

1. Write `tools/art/<weapon>.py` with `build()`, `GROUPS` and `ANCHORS` on the same axes and contract, with real dimensions.
2. Iterate with `render_views.py` (all seven views plus `eye`) until no defect shows; record the renders.
3. Bake and export it, pack its textures, and write a `.tres`; then pose hands with a hands generator.
4. Add the id to `SBWeaponModel` the same way `_build_authored_rifle` does, and extend `weapon_art_test.gd`.
5. Capture it with `game/tests/weapon_art_capture.gd`, then review it against `docs/art/VISUAL_QA.md`.
