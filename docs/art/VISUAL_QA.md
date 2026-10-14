# Visual QA

## Procedure for every visual change

1. **Cycles review renders** from the generator.
   - `render_views.py` with all seven views (left and right ¾, side profile, top, receiver, grip and magazine, materials), plus `eye`, which reproduces the in-game camera.
   - Fix every visible defect before baking.
2. **In-engine captures** with `game/tests/weapon_art_capture.gd`:
   - backlit yard: ready, firing, reload;
   - sunlit yard;
   - hall shade;
   - sunlit with a skin;
   - the inspection studio with a skin.
   - Repeat with `--procedural` for the before set.
   - All on Xvfb/llvmpipe at 1280×720.
3. **Contract test:** `weapon_art_test.gd` must pass, along with the rest of `validate.sh`.
4. **Review:** score against the project's seven-part rubric (`docs/reports/QA-0.3.md`; anchors 5 = blockout, 7 = coherent alpha, 8.5 = consistently polished, 10 = exceptional) and against `VISUAL_GAP_ANALYSIS.md`.
   - Only categories the change touches are re-scored.
   - Stills cannot score motion.
   - A reviewer from the same model family as the author is recorded as such and does not count as independent acceptance.

## Relay AR slice (2026-10-13)

Evidence: [`docs/reports/media/art-v1/`](../reports/media/art-v1/README.md).

**Reviewer:** a separate Claude agent. It is the same model family as the author, so this is **not independent acceptance**. It had stills only (no motion), llvmpipe captures (no device shading or compression artefacts), and no CS2 reference images; its CS2 comparisons come from general knowledge.

**Images reviewed:** the captures in `captures/before-procedural/`, the authored set before the follow-up commits (kept in `reviewed-v4/`), and the Cycles renders.

Scores cover the first-person weapon, hands and inspection only, not the whole game:

| Category | Before | After | Reviewer's reason (abridged) |
| --- | ---: | ---: | --- |
| 2 Materials and surfaces | 4.0 | 5.5 | Baked occlusion and normals give panel lines, bevel highlights and a readable sight glass. But the default graphite finish discarded the baked albedo, so the receiver read as matte plastic without wear. |
| 4 Models and animation presentation | 4.5 | 5.5 | It is now a recognisable carbine with a rail, slots, brake and optic. The hands read like mannequin parts, and reload is still a whole-rig tilt. |
| 5 Combat and cosmetic effects (incl. inspection) | 4.5 | 5.0 | Inspection shows a real-looking rifle. Effects are unchanged, and the skin is a flat two-tone band that blows out. |
| 6 Identity and consistency | 5.0 | 5.0 | A generic AR silhouette. It is now more detailed than the box-built environment, and the hands are less detailed than the rifle. |
| 7 Competitive readability | 6.0 | 6.0 | Less of the central 40 % is covered (5.6 % against 6.4 %); in exchange, the forearm covers more of the lower centre. |

- **Categories not re-scored:** 1 (geometry) and 3 (lighting), because the environment and scene lighting did not change.
- **Mean of the five categories:** about 4.8 → 5.4.
- **Whole-game effect:** about +0.1, at most +0.2, from the independent 6.6 baseline. That is still below the 7 "playable alpha" anchor and far below 8.5. The reviewer put a CS2-like first-person weapon at about 9 on this rubric.

**Defects, ranked by the reviewer:**
1. Hand anatomy: tube fingers and a claw-like support grip.
2. A pipe-like sleeve with no folds; it is the largest and least detailed thing on screen.
3. The flat default graphite finish.
4. CAD-like surfaces and a faceted grip.
5. A heavy roll; the support hand sits at the handguard tip.
6. Inspection framing: the muzzle at the frame edge.
7. The two-tone skin band and blow-out.
8. Weapon and background merge in shade.
9. Detail mismatch with the box-built environment.
10. Unchanged effects (star flash, box casing, tilt reload) now stand out.

**Fixed after the review (not re-scored):**
- the casing origin (`039ade9`): casings no longer appear beside the gun;
- defect 3 (`b376e61`): without a skin, the rifle shows its baked anodised surface with wear;
- defect 6 (`b376e61`): the inspection placement is re-centred.

The final captures are in `captures/after-authored/`. Every other defect stays open and is listed in `docs/DEVELOPMENT_STATUS.md`. The next steps, in the reviewer's order, are:
1. Rigged glove hands with real anatomy.
2. Sleeve shape and gear, with a reduced roll and the support hand moved to mid-handguard.
3. Layered default materials and UV-based skins with wear masks.
4. Weapon lighting checked on real GPUs.
5. Authored reload, equip and inspect animation.


## Hands v2 re-review (2026-10-13)

**Reviewer:** another Claude agent, so again **not independent acceptance**. It had stills only, llvmpipe captures and no CS2 reference. It reviewed commit `ecd290b` (the evidence is kept in `reviewed-hands-v2/`). Scores cover the first-person weapon, hands and inspection only.

| Category | Previous | New | Reviewer's reason (abridged) |
| --- | ---: | ---: | --- |
| 1 Geometry/composition | not scored | 5.5 | The whole rifle, optic and both hands are framed, but the pose is broadside and the rear is cropped. |
| 2 Materials | 5.5 | 5.5 | Baked wear exists, but the receiver sat at 19–27/255 at 1:1 and the sleeve and gloves are smooth. Gains and losses cancel. |
| 4 Models/animation | 5.5 | 6.0 | The hands now read as hands. Held back by a reload frame with a huge slab, a visible sleeve end and a rigid forearm. |
| 5 Effects/cosmetic/inspection | 5.0 | 5.2 | Inspection centring is fixed. The flash and skin band are unchanged, and the reload magazine looks worse. |
| 6 Identity | 5.0 | 5.0 | The gold strap echoes the yard. The rifle now clashes more with the cuboid containers. |
| 7 Readability | 6.0 | 6.0 | Strong silhouette; weak in shade (receiver 13/255 against a floor of 38). |

- **Mean of categories 2, 4, 5, 6 and 7:** 5.4 → 5.5 (27.7/5).
- **Whole-game effect:** about +0.03. The game stays at about 6.6–6.7, and nothing here moves it toward 7.
- **CS2 comparison** (general knowledge only): the reviewer put a CS2-like first-person weapon at about 9.

**Verdicts on my claims:**

| Claim | Reviewer's verdict |
| --- | --- |
| Default finish shows the baked surface | Partly true: present, but crushed to near-black at 1:1 |
| Inspection centring | True |
| Casing origin | Unverifiable in the frames (a sliver at the right edge) |
| Hand anatomy | Partly true: segmented fingers and a thenar mass, but "lumpy putty gloves", a thumb poking into an M-LOK slot and three knuckle balls floating over the rail |
| Sleeve taper, darker fabric, strap | True, but folds and the strap are invisible in-engine (the strap is a 1–2 px line) |
| Roll reduced, fitted placement | Mostly true: the diagonal fell from about 32° to about 17°. The firing hand is half visible, there is no right forearm, and the stock and buffer tube are cropped |
| **"Holds at 16:9, 20:9 and 4:3"** | **False. My aspect captures were 1280×720 and 1024×576. I resized them for the comparison without checking their real size, so those layouts were never shown. The claim has been withdrawn and the captures redone (below).** |

**Regressions the reviewer found, and their status:**
- **Reload frame (03):** a flat tan slab about 190 px wide jammed against the right edge. It was the buttstock: the actor tilts the weapon node about its origin, which sat about 0.45 m from the stock. **Fixed.**
  - The model now declares a pivot, so tilts turn about its middle.
  - The stock is its own mesh and first person leaves it out.
  - `weapon_art_test.gd` pins both. A negative control showed the earlier stock-visibility test failing at full roll, which is what led to the omission.
- **Sleeve end visible (01):** hidden, not fixed. The forearms were lengthened to about 0.65 m, 2.4 times a real forearm; the next review rejected this (below).
- **Thumb in an M-LOK slot and floating fingertips:** **fixed.** The thumb is thicker and runs below the slot row, and the fingers stop at the side of the handguard.
- **Receiver too dark, "black plastic":** **fixed in sun only.** It reads about 58–60/255 in sun with panel lines and edge wear, but 24–28/255 backlit and in shade (next review).
- **Cycles `eye` view not matching the game:** **fixed.** Two bugs of mine: it used the old placement, and Blender's YXZ Euler order, which is Godot's ZXY.
- **Not fixed:**
  - skin band blow-out;
  - the unchanged star flash, box casing and tilt-only reload;
  - the detail mismatch with the box-built environment;
  - the rifle still reads as "held out for display" rather than aimed;
  - the right forearm is out of frame;
  - the hand and sleeve surfaces are still smooth.

The reviewer's top next steps, in its order: lift the receiver and add rim/specular (done in part); re-pose with more foreshortening and both forearms visible; author reload, draw and inspect; replace the flash with a multi-plane flash, light, smoke and a real casing; and redo the aspect captures (redone at real sizes, but see the next review: they show an "expand" stretch the project does not use).

## Review of `2bba519` (2026-10-13)

**Reviewer:** a fresh Claude agent, read-only, given the evidence and the code but not my conclusions. It is the same model family, so this is **not independent acceptance**. It had stills only and no CS2 reference images.

**Verdict:** about **4.5/10** against a CS2-class bar of about 9. The rifle is at coherent-alpha level; hands, sleeves, motion, composition and lighting are at blockout level. Passing tests do not change that.

| Area | Score | Main defects |
| --- | ---: | --- |
| Hand anatomy | 4.5 | Fingers are chains of ellipsoids: lumpy, four near-equal visible segments instead of three phalanges in about 5:3:2, identical lengths across fingers, a 30 mm featureless thumb, no back-of-hand plane, a 52 mm wrist inside a 75 mm cuff. No glove construction. |
| Sleeves | 3.5 | Forearms 2.4× human length; uniform cones with no elbow; folds and strap invisible in-engine; the right forearm never on screen. |
| Rifle | 5.5 | Sound real-world dimensions, but slab-sided forms and a box magazine well; the optic has no reticle and an opaque lens. The finish is grainy grey in sun and crushed in shade. Skins drop the baked wear and clash (glossy red over a matte body). |
| Positioning and motion | 3.5 | The world camera's 82° vertical field of view (about 114° horizontal) also draws the viewmodel; CS-style viewmodels use about 47–54°. A 15.5° yaw puts the barrel's vanishing point 115 px left of the crosshair. No skeletal animation: reload is a rigid tilt and a magazine slide, fire is a kick, equip is a drop. Wall clipping is likely (inferred from code). |
| 20:9 and 4:3 captures | 5 | At 20:9 the left 60 % is empty; at 4:3 the firing hand is cut to fingertips. **These captures do not show shipped behaviour:** `project.godot` uses `canvas_items` stretch with the default "keep" aspect and nothing overrides it, so a 20:9 or 4:3 screen shows the 16:9 frame with bars. I verified this. |
| Lighting and visibility | 4 | Receiver 28/255 backlit, 58 in sun, 24 in shade against a 37 floor. Flat ambient, no viewmodel fill or rim, and near-black albedos on glove, sleeve and receiver with no value separation. |
| Rendering cost | 5 | +35,230 primitives (48 % of the frame) and +60 ms on llvmpipe (relative only). The rifle atlas uses 54.7 % of its area, 9.5 % of it on the stock, which first person never shows. Sleeves take about 70 % of the hands atlas. The handguard alone is 7,976 triangles, mostly rail-slot booleans. Suggested budget: 15–18k triangles for the first-person rifle plus about 5k for the arms. |

**Its top changes, by impact per effort:**
1. A viewmodel light rig and value separation between glove, sleeve and receiver.
2. Render inspection at full resolution. It reports `stretch_shrink` resolving to 2 at 1280×720 (not yet verified by me).
3. A separate viewmodel projection (about 50° vertical) with anti-clip depth, then a pose with the barrel near-parallel to the view.
4. Real-length forearms with elbows.
5. Re-sculpted hands with glove construction in the normal map.
6. A UV repack without the stock and with texel priority for the gloves.
7. Rigged arms with reload, fire and draw clips.
8. A material and skin pass.

**Response:** the hands, sleeves and motion are being rebuilt rather than patched (arms v3: signed-distance anatomy with three phalanges per finger, a glove with a knuckle guard, padded phalanges, seams, cuff and strap, a jacket sleeve of real length, a skeleton with automatic weights, fingers closed on the rifle by contact, and a skeletal reload driven by the existing reload timer). The stretch-aspect question is a product decision, "keep" (every player sees the same field of view) or "expand" (fill the screen), and it is left to the project owner and Codex.


## Review of arms v3, `5100b3e` (2026-10-14)

**Reviewer:** a fresh Claude agent, read-only, given the evidence (`docs/reports/media/art-v3/`) and the code. It formed its findings before reading my self-assessment. It is the same model family as the author, so this is **not independent acceptance**. It had stills, llvmpipe captures and Cycles renders only: no motion (the motion sequence was captured after the review started), no device and no CS2 reference images.

**Verdict:** **4.5/10** overall against a CS2-class bar of about 9. That is the same as the review of `2bba519`: the rig, the separate projection and the depth handling are structural progress, offset by an unreadable reload, lighter skin-like gloves, a still misaimed bore and a blocking shader regression.

| Area | Score | Main defects (abridged) |
| --- | ---: | --- |
| Hand and glove anatomy | 5.0 | Proportions are sound on paper, but fingers are parallel sausages without joint creases, the grab hand is a mitten with a bulbous thumb, the index tip reads as a ball in the trigger guard, the knuckle-guard bake edge is jagged, and the palm crumples at the index base. Seams, guard and cuff are invisible at 1280×720. |
| Sleeves and forearms | 4.0 | A straight, thin olive tube. The fold normals read as regular helical stripes and the hem as evenly spaced rings. No elbow or upper arm. The right forearm is never visible. The support hand sits about 0.84 m from the eye, beyond human reach, so the arm looks locked. |
| Magazine grab | 2.5 | In 03 (44 % through the reload) neither the hand nor the magazine is on screen, and in 03b only a glove top shows at the bottom edge. The magazine is below the frame even at rest. The grab solve left the thumb and pinky unresolved and the ring finger hyper-extended. The same magazine is pulled 23 cm and pushed back. |
| Clipping | 6.0 | No gross penetration at rest. Support fingertips crest the top rail. The trigger pad floats 11.6 mm off the trigger. The thumb tip butts the hand stop. |
| Projection and composition | 4.0 | The 54° projection removes the edge stretch and the depth handling is correct. But the bore's vanishing point is about 124 px left of the crosshair (no better than v2's 115 px), the 1.7× magnification crops the magazine and firing hand, and the buffer tube's cut end shows during reload. |
| Materials | 4.0 | Glove and sleeve albedos have nearly the same value. The v3 glove is about 2.6× brighter (linear) than v2's, which is the main reason it reads as skin. The firing glove merges with the magazine in sun. In shade the receiver is 19–27/255; the 0.08 × albedo floor is negligible. |
| Rifle | 5.0 | Unchanged from slice 1 (5.5 on its own), crushed in backlight and shade, −0.5 for the broken inspection. |
| Rendering cost | 5.5 | No regression against the static v2 hands (166.9 against 168.5 ms on llvmpipe, relative only). The arms are 10,672 triangles, twice the suggested 5k. The off-screen right arm and 40 cm sleeves are still skinned and drawn. |

**My verification of its factual claims:**

| Claim | Verified how | Result |
| --- | --- | --- |
| **Blocking:** inspection loses the receiver and handguard; procedural first-person weapons are likely hit too | The frame itself, then a native pixel test (`paint_visibility_test.gd`) on `5100b3e` | **True, and wider than stated.** The paint parts changed 0 pixels in inspection (skin and default) and on the procedural sidearm. The case reveal uses the same finish. **Fixed in `9ebe724`** (separate first-person shader variant; five new contract checks with a negative control; pixel test 59,824 / 56,548 / 11,716 px) |
| Vanishing point about 124 px left | Bore direction through the viewmodel projection in engine | True: (515, 374), 125 px left |
| Support hand about 0.84 m from the eye | `L_hand` bone distance in engine | True: 0.88 m to the wrist bone |
| Magazine and support hand off-screen during the reload | Motion sequence (`art-v3/motion/`) | True: the hand is below the frame for clip times 0.16–0.81, and the magazine is never visible |
| Glove about 2.6× brighter than v2, about the same value as the sleeve | Mean of the shipped albedo textures | True in direction: by hue, glove sRGB ≈ 68 against ≈ 50 for v2, and glove 0.052 against sleeve 0.055 linear. The cause is in `arms_build.py`: the convexity wear blends fingers and knuckles up to 55 % toward a light tan, `(0.21, 0.18, 0.13)` linear |
| Capture 03 is at 44 %, not 30 % | `weapon_art_capture.gd` sets 1.25 s left of 2.25 s | True; my README was wrong and is corrected |

**Order of work in response:**
1. The shader regression (done).
2. Placement re-fit: the vanishing point near the crosshair, reach about 0.6 m, magazine well and firing knuckles in frame, buffer-tube end off-screen.
3. Reload staging that keeps the hand and magazine on screen at the grab and the insertion.
4. An arms rebuild:
   - value separation: charcoal glove, distinct sleeve, subtle wear;
   - slimmer thumbs and finger creases;
   - the knuckle-guard bake edge;
   - fingertips off the rail;
   - the trigger pad;
   - the grab thumb and pinky;
   - irregular sleeve folds;
   - fewer off-screen triangles.
5. New captures, motion sequences and a fresh review.

The scores above stay as the reviewer gave them until a new review re-scores the changed work.

## Codex integration review of `64ec598`, and the work after it (2026-10-14)

**Reviewer:** Codex, a different model family, reviewing an isolated integration build that combined PR #1, this branch and Codex's PRs 3–8. Evidence is in Codex's integration preview (PR #9, `docs/reports/integration-evidence/art-independent/`). It is an AI review, not human acceptance.

**Verdict:** about **5.5/10** for the weapon and arms, against the 8.5 gate.

| Area | Score |
| --- | ---: |
| Geometry | 6.0 |
| Materials | 5.5 |
| Lighting | 5.0 |
| Animation | 5.5 |
| Effects and cosmetics | 4.5 |
| Identity | 5.5 |
| Readability | 6.5 |

**Main weaknesses it named:**
- the ready and bore composition: the vanishing point is 124 px left and the rifle "reads as displayed sideways";
- mitten-like gloves and regular sleeve rings;
- shade contrast between receiver and arm, and over-bright backlit edges;
- action cropped at 4:3 and leaving frame mid-swap;
- a flat star muzzle flash, box casings and a simple cosmetic stripe.

**Corrections it requested, and what was done:**

| Finding | Status | Evidence |
| --- | --- | --- |
| Static fallback hands drawn with the world projection, detached from the rifle; the procedural gloves likewise | Fixed in `3934110`; contract assertions and native captures added | `docs/reports/media/art-v4/fallback-projection/` |
| Online reload poses stepped at the 20 Hz snapshot rate (40 changes in 120 ticks) | Fixed: presentation clock, at least 115 changes in 119 ticks in a 20 Hz simulation | `art-v4/README.md` |
| Arms packed scene not retained | Fixed | same |
| Magazine framing margin of 2.8 px at 15 % | Fixed: an 11 cm lift; every vertex at least 1 % inside the frame at the grab and the seat | same |

**Also since `64ec598`:** the arms rebuild (`144dc33`, `0087956`).
- **Value separation:** glove 0.024 against sleeve about 0.08 linear.
- **Anatomy:** slimmer thumbs, joint condyles and creases, and a lower knuckle guard.
- **Grip:** a resolved grab hand and a trigger pad 4.4 mm from the trigger.
- **Budget:** 7,828 triangles.

**Still open (my observations, `art-v4/README.md`):**
- the grip hand still reads as a mitten;
- support fingertips crest the rail;
- the sleeves are a near-uniform tube;
- the bore vanishing point is unchanged;
- shade contrast;
- no draw or inspect clips;
- the reload reseats the same magazine;
- reduced motion is not reviewed.

None of the five weaknesses behind the 5.5 is resolved by these fixes except glove value. The score stays at Codex's 5.5 until a new review re-scores the work.

## Review of `b507205` (2026-10-14)

**Reviewer:** a fresh Claude agent, read-only, given the `art-v4` evidence. It scored from the images and from frames it pulled out of the MP4s before reading any self-assessment. It is the same model family as the author, so this is **not independent acceptance**.

**Verdict:** about **4.5/10**, below Codex's 5.5 for `64ec598`. The reviewer weights reload legibility and hands more heavily.

| Area | Score |
| --- | ---: |
| Hand and glove anatomy | 3.5 |
| Sleeves and forearms | 4.0 |
| Magazine grab and reload legibility | 3.5 |
| Clipping and contact | 5.0 |
| Projection and composition | 5.5 |
| Materials and value separation | 4.5 |
| Rifle model | 5.0 |
| Effects | 4.0 |

**Top defects, in its order:**
1. **Reload legibility:**
   - at the grab and the seat the support forearm covers most of the magazine;
   - in backlight the pulled magazine renders near black;
   - the bright tan pistol grip is the most prominent object and reads as "the magazine".
2. **Hands:** the grip hand is a mitten without thumb or knuckle read, and the support fingers fuse into a paddle on top of the rail.
3. **Bore direction:** the rifle aims low-left and reads as held across the body.
4. **Materials:**
   - a saturated chartreuse sleeve in sun (sRGB 143, 150, 102);
   - glove and receiver almost equal in shade;
   - tan furniture in the same warm band as the sunlit gloves.
5. **Effects:** a flat star muzzle flash and box casings.

**Also seen:** the support hand opens in mid-air before the seat completes, with no push.

**Against art-v3:**
- **Better:** glove value is fixed (sunlit glove saturation 0.09 against 0.17), and the hand and magazine stay in frame at the grab.
- **Mild regressions:** the sleeve is brighter and more saturated in sun, and its fold relief no longer reads.

**On my claims:**
- **Confirmed:**
  - every magazine vertex is in frame at the grab and the seat;
  - the gloves no longer read as skin;
  - the fallback hands are attached.
- **Overstated:** "in frame" is not "legible". The magazine is mostly covered, and in backlight black. Slimmer thumbs, condyles, creases and the lower guard are not visible at 1280 × 720.
- **Wrong:** I described the static v2 fallback's sleeves as tan. They are slate grey with a tan cuff stripe, now corrected in both READMEs.
- **Not acknowledged before:** the black magazine, the forearm covering it, the early hand opening and the sleeve saturation. All four are recorded here.

**My verification of the black magazine (superseded by the correction below; this diagnosis was wrong):**
- **Measured, not a texture fault:**
  - the magazine region of backlit frame 60 has a median of sRGB (3, 3, 2), with 27 % pure black;
  - its albedo, sampled at its UVs, is a normal tan-grey (0.10, 0.09, 0.06 linear);
  - its baked AO is ordinary (mean 0.59).
- **Cause:** the shadowed side gets only the flat ambient (energy 0.41) and the 0.08 × albedo emission floor. Both are about 0.01 linear, which the yard's Filmic tonemap toe crushes to black.
- **Conclusion (wrong):** this is not a broken shading path. The viewmodel needs a real fill term; the current floor is too weak (the review of `5100b3e` said the same).

**Next on this branch, in order:**
1. A view-space fill for the viewmodel: shaped, AO-aware, in the existing shader, so no extra light pass.
2. A less saturated sleeve and darker furniture.
3. Reload staging with the support forearm below the magazine, and a push at the seat.
4. Grip-hand finger separation and a visible thumb.
5. Bore direction.

The scores above stand until a new review re-scores the work.

## Correction: the black magazine was a texture defect (2026-10-14)

My entry above sampled the magazine's **albedo** and its **mean AO** over the whole mesh, concluded the texture was fine, and blamed the lighting. That measurement was too coarse. Rendering the shader's inputs over the *pulled* magazine's own visible pixels showed an albedo median of 109 (a normal tan) but a **baked occlusion median of 0**. The occlusion had been baked with the magazine seated in the magwell, so the faces that were inside the well were fully occluded and went black as soon as reload pulled the magazine out, in every lighting condition.

- **Fix:** the magazine's occlusion was re-baked on its own and patched into `relay_ar_orm.png` (red channel, magazine islands only; the other textures and the GLB are byte-identical). Tools: `tools/art/rebake_part_ao.py`, `tools/art/patch_part_ao.py`.
- **Result** (`docs/reports/media/art-v5/lighting/`): backlit mid-reload median luma **4 → 59**, shade 2 → 56, dark interior 2 → 33. No other part changed by more than 3 luma, and the inspection render differs by 1 pixel of 921,600. `weapon_art_test` now guards the occlusion (111 checks).
- **The fill I was asked to investigate was built, swept and removed.** It bought 1–3 luma in the darkest scene and broke sunlit values above a gain of 0.4.
- **Still open:** gloves in a nearly dark interior measure a median of 15–16, and the pulled magazine is now the brightest part in sun (warm tan beside a grey receiver).

The review's scores above are unchanged: this fixes one of its defects (reload legibility's black magazine), not the occlusion of the magazine by the support forearm, the hand shapes, the bore direction or the sleeve material.
