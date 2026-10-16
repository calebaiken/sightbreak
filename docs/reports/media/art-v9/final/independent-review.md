# SIGHTBREAK first-person rifle / hands, final review (art-v9, cd0e40a vs base 57f6464)

Reviewer: a read-only Claude agent, the same model family as the author. This is NOT human acceptance and NOT independent in the sense of a different model or a person. Judged from the per-tick PNGs (1280x720, 60 Hz), the 2560x1440 closeups and the reduced-motion sequences, looked at BEFORE the author's write-up. I also took pixel medians from the PNGs in memory (no files written, nothing in the repos touched, no validate/Blender/Godot run). Stills cannot score motion; I compared consecutive frames only as frame-difference counts. Paths below are relative to `/tmp/claude-0/-home-user-sightbreak/879e0955-4175-58a7-99d2-52975641cc63/scratchpad/` (called S).

## 1. Findings, ranked by severity

1. **The rifle is warmer, paler and more khaki than base at rest, and the metal parts lost their separation.** (S/fin/{base,new}-sunlit/000, 134-182; S/fin/big-{base,new}/000.)
   - In sun at tick 0 the new receiver reads olive/khaki. Base reads graphite.
   - My patch medians (receiver at the ready pose, sunlit): base (57,60,56), new (73,73,67), about +28% value. This matches the author's own table (ready receiver 55 to 70).
   - In shade and backlight the rifle is near black in both builds (new receiver about (32,36,39) vs base about (26,31,35)), so the receiver, mag and glove still separate poorly there. See finding 5.
   - The receiver and handguard now have the same luma (author's own table: 70/70 in sun ready, 82/82 grab). In the frames the whole upper is one flat matte olive-grey with no metal/polymer distinction.
   - The author admits the highlight response was traded away and not rebuilt.
2. **The "pale rifle in reload" fix works as stability, at the price of a permanently drab olive cast.** (a) answer:
   - Base: the receiver is cool blue-grey in ticks 36-98 (patch (78,85,87)) and shifts warm/olive by tick 118-124 ((83,85,82)). Idle is dark neutral (57,60,56). So base changes colour twice, and the beige appears in the transition, as the author says.
   - New: the same patch is (84,84,81) at 36-98, (81,83,79) at 118, (81,80,74) at 124. It never shifts hue in the reload, which is a real improvement. At 134-182 the receiver patch is flat at (73,73,67) with no jump at the first shot. My visual impression of a dark pop at tick 136 was NOT confirmed by pixel sampling; ignore it.
   - Across all three lightings the new rifle does not change colour between ticks 100-134. But the steady colour is olive/khaki. Whether that reads as "beige" is a judgement; to me, at 1280x720 in sun, it does read as drab khaki rather than gunmetal. The test only measures median luma (ratio <= 1.25) and cannot see hue or beige.
3. **Replacement-magazine pop at the hip is larger than base** (S/fin/new-sunlit/066-068 vs base 066-068).
   - At tick 67 the replacement mag appears at the bottom edge with about 60 px of it in view, and no hand is visible. Base shows about 20 px.
   - Frame-difference count in the lower-left region at tick 67: new 3092 vs base 701 (changed pixels, threshold 25). The jump is ~4x larger.
   - The author relaxed the first-draw rule from `new_share < 0.05` to `< 0.25` to accommodate this (see section 4). That is a visible regression in pop size relative to base, justified in prose by the hand now reaching the lower edge.
   - From 67 to about 76 the mag rises on its own with no hand visible, then the hand appears at 78. The arm at the left edge (S/fin/new-sunlit/066-074) is a near-black wedge, not connected to the mag. The off-screen hip is plausible as a concept, but it reads as a floating tan block for roughly 10 ticks. Base has the same issue, only smaller.
4. **Gloves are better constructed but still modest at 1280x720, and the two hands do not match in value in sun.** (S/fin/big-{base,new}/014, 036, 098, 118.)
   - New: darker glove, a camo back panel, a pale cuff stripe, seams at the knuckle line, fingertip and finger segmentation. The left (support) hand grasp reads: fingers wrap the mag base, the thumb is visible at 098/106/118. This is a real improvement over base, whose left glove is a smooth pale-grey mitten with no panel.
   - The right (grip) wrist and hand back is still a large pale beige-grey mass in sun (S/fin/big-new/036 and 098, around x 1600-1800, y 700-950 of the 2000-px display; also 1280x720 tick 036 around (1050-1230, 440-600)). It carries a diagonal strap/stripe now, but its value is much lighter than the left glove. In sun it still reads close to bare skin or a pale glove, which the author concedes in hands/README.
   - Fingers on the grip hand are mostly hidden behind the grip. They read as 3 round blobs, not joints.
   - The open palm-up return pose (ticks 118-130) shows long thin fingers spread flat. The author says so too.
5. **Shade/backlight material separation is not meaningfully solved.** (S/fin/new-shade/070, new-backlight/098.)
   - Receiver, grip, sleeve and glove are all dark blue-black. The mag reads grey and is the only clear object.
   - New gloves are darker than base's pale blue-grey ones, so glove vs sleeve contrast is about the same.
   - The author measured glove/sleeve 0.82 before and after in shade.
6. **Left forearm at the hip is a black wedge** at ticks 64-74 in all three builds (base and new): the underside of the sleeve is far darker than the lit sleeve elsewhere. A lighting inconsistency, not a new defect.
7. **Reduced motion: only the opt-in variants keep the hand visible; the shipped default does not.** The default is still `reduced_variant = "current"`.
   - `current` (S/seq/current/058): the fingertips are at the bottom edge and the mag floats in the middle, identical to default. Hand continuity is the same as the base behaviour.
   - `calm` and `still` (S/seq/calm and still, ticks 30-118) keep a gloved hand continuously on the mag. The pickup reads as a hand lifting a mag from the lower edge. There is no visible source object, as the author notes.
   - `calm`: rifle rolled a little, the barrel is high in the right half, and the "RELAY 02" signage is partly covered (calm/058). Readable.
   - `still`: the barrel exits the top-right corner. The rifle looks awkwardly propped (still/036, 107), and the "RELAY" text is covered. At tick 70 the hand is largely cropped by the bottom edge. It is visible and plausible but odd-looking. The author calls it odd too.
   - I found no pop in calm/still around ticks 63-72 (frame-difference counts no spike; calm/still 067 look continuous).
   - 107 (seat) spikes in default (about 38k px), as expected for the seat kick.
8. **Muzzle flash and smoke are unchanged from base, and still a flat, round blob.** (S/fin/{base,new}-sunlit/136-160, S/seq/fire-sheet.jpg.)
   - Tick 136 shows a white disc with a yellow halo and a dark core. By 138 it is a small grey puff. By 160 a faint grey smudge.
   - It reads at gameplay size and has no directional character (no petals/tongue visible at this size). Smoke is minimal, the puff is faint and vanishes quickly.
   - Frames are identical between base and new apart from the rifle tint (the author says VFX were not touched).
9. **Rifle texture/wear.** New shows mottled wear on the receiver (S/fin/new-sunlit/124-135 at 1280x720). Base is cleaner/smoother. This is probably the author's palette or wear change; it looks like dirt/grain at 1280 and is fine at scale. Not verifiable from stills on a phone.

## 2. Before/after verdict per area

- **Rifle colour (a):** Reload stability: better. Base shows a cool blue-grey hold followed by a warm transition to idle. New holds one colour from tick 36 to 134 in sun, shade and backlight. But new is paler and khaki at idle (+28% value in sun). A beige cast is steady rather than transitional. Gain on stability, loss on the metal read. The test measures luma only.
- **Hands (b):**
  - Better: darker, a panelled back, a cuff stripe, defined knuckles and fingertips, a readable thumb and finger wrap on the mag, and a visible stitched cuff.
  - Honest: modest at 1280x720. The grip hand is still a pale mass in sun, and the right wrist reads skin-like. The base gloves are clearly worse (pale mitten, bare-skin look).
- **Lighting/material separation (c):** Sun: gloves a bit darker than sleeves (0.73), grip darker than receiver (author's measure), but the receiver, handguard and mag are all flat olive. Shade/backlight: unchanged, near-black on near-black. Verdict: mixed. Better in sun for glove/grip; worse for receiver vs handguard; unchanged elsewhere.
- **Hip retrieval (d):** Same concept as base. The pop at 67 is larger (60 px vs 20 px visible); the mag floats unheld for about 10 ticks. Extraction (36), carry, insertion (98-106) and seat (107) read OK, and the hand grasp on the mag base is clearer than base. Return/ready (118-134) is fine.
- **Reduced motion:** Default reduced setting unchanged. `calm` is the best of the three: a continuous hand and mag, a modest roll. `still` is awkward. Neither was adopted.
- **Flash/smoke (e):** Unchanged. Small bloom, faint smoke.

## 3. Score table

No preserved earlier scores were changed. Mine are only for what the captures show, are weapon/hands scope, are stills-only (no motion), and are NOT comparable to a different reviewer's numbers.

| Category | Preserved earlier score (source) | My score from these captures | Note |
| --- | ---: | ---: | --- |
| Geometry / composition | Codex 6.0 | not scored | no composition change shown |
| Materials and surfaces | Codex 5.5 | 5.0 | matte olive receiver = handguard; gloves slightly better |
| Lighting (viewmodel only) | Codex 5.0 | 5.0 | shade/backlight still near-black on near-black |
| Models and animation presentation (hands/reload) | Codex 5.5 | 5.0 | hands better, a bigger mag pop, a pale grip hand; stills cannot score motion |
| Combat/cosmetic effects | Codex 4.5 | not scored | flash/smoke unchanged, stills only |
| Identity and consistency | Codex 5.5 | not scored | |
| Competitive readability | Codex 6.5 | not scored | outside these captures |

Other preserved scores in VISUAL_QA.md that I did not change: the b507205 review (about 4.5 overall; hand/glove anatomy 3.5, sleeves 4.0, reload legibility 3.5, materials/value separation 4.5, rifle 5.0, effects 4.0), and a v8 review whose per-category scores lie between 5.5 and 6.5 (individual numbers not recorded). Nothing in this round was added to docs/art/VISUAL_QA.md (no diff).

## 4. Changed thresholds and rules (base-wt vs art-wt; test files compared)

Tests that differ: `reload_sequence_test.gd`, `viewmodel_light_probe.gd`, `weapon_art_test.gd`; new `reload_discolour_probe.gd`. `reload_visibility_test.gd` and all other game tests are byte-identical. Scripts: `validate.sh`, `reload_negative_controls.py`, `test_reload_contact.py` differ.

1. **Relaxed: `reload_sequence_test.gd` first-draw rule `new_share < 0.05` becomes `< 0.25`.** This is moving a goalpost that matters. Base measured at <5% and it shows (about 20 px in frame). The new clip puts 20% (about 60 px at my 1280x720 view) in frame at the first draw, and the bound was loosened to fit. The justification (the hand now reaches the lower edge, with its visibility checked by the visibility test) is plausible. But the net effect is a bigger visible pop, and the author's own negative-controls note says defects in the 25-90% band now pass. The change is disclosed. I judge it a justified-in-prose but real regression against base.
2. **New (not a relaxation): `reload_discolour_probe.gd --assert` bound 1.25** on max/min median luma through the reload. Derived from measured data (before 1.42-1.75, after about 1.18). Reasonable as a regression guard, but luma only, with no hue or beige check. It passes the olive cast.
3. **New: `viewmodel_light_probe.gd --assert`:** grip/receiver <= 0.85 in all lightings; gloves/sleeves <= 0.78 in sun; receiver and handguard >= 22 in the dark interior. Author says the bounds were set from this round's measurements (after values 0.56-0.76; 0.73-0.76; 25/28), so they pin the shipped state. They are not visual standards. The grip/receiver ratio is partly driven by the receiver getting brighter. No gloves/sleeves bound exists for shade or the dark, where separation is not improved.
4. **`weapon_art_test.gd` +checks:** variant existence and ordering, `METAL_ROUGHNESS >= 0.7`, `METAL_FLOOR > FLOOR`, arms specular < 0.5. These are additive and pin the shipped values.
5. **Negative controls:** N18's injected defect was rewritten (hip -0.60/carry -0.40, to match the new hip path keys), and N23 depends on the 25% bound. 33/35 caught in the first run plus a re-run of N18/N23 (disclosed). The harness now restores every edited file. Fine.
6. **Source constants changed (values, not tests):** GRIP_DARKEN 0.30 to 0.24, ARMS_LIFT 0.35 to 0.50, ARMS_RIM 0.40 to 0.25, new ARMS_FLOOR 0.14, ARMS_SPECULAR 0.25, METAL_ROUGHNESS 0.80, METAL_FLOOR 0.26. The reduced-motion `still` lift 1.6 to 1.8 (and roll to 0.0, recoil 0.4).
7. **Contact bound:** the author says the 1.5 mm bound was not touched. The csv path in `test_reload_contact.py` was repointed to the v9 log; I did not re-run the contact CSV.

## 5. What remains unconvincing

- The rifle is olive/khaki at rest and in the reload. No test would catch a "beige" look.
- The receiver and handguard are now level, so the metal has no separation or highlight.
- The gloves still read pale-ish and skin-like on the grip hand in sun.
- Shade and backlight separation is unchanged and near-black on near-black.
- The hip pop is bigger than base, and the mag is unheld for about 10 ticks.
- The glove improvement is described by the author as "modest"; I agree, and I'd call it a clear but small step.
- `current`, the shipped reduced default, keeps the weak hip visibility; the better variants are not adopted.

## 6. Not assessed

Motion feel and smoothness (stills only; I only counted frame differences). The comfort or accessibility value of the reduced-motion variants. Listening (audio). Any phone hardware, tonemapping or renderer (this is llvmpipe, GL Compatibility). Hue-sensitive claims beyond my own eye and a few patch medians. I did not re-run any test, and I cannot say whether the 1280x720 stills match what a phone shows. I did not look at the 20:9 and 4:3 captures or the perf logs.
