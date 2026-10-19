# SIGHTBREAK art-v10 visual review (Relay AR rifle, gloved arms, reload)

Reviewer: same model family as the author. This is NOT human acceptance. I judged only the real 1280x720 stills (BEFORE 5357329 in scratchpad/capB, AFTER 1f11697 in scratchpad/capA2), looked first and measured second. No repo file was edited. Working crops are in scratchpad/review10/w/.

## Headline

1. The rifle and the replacement magazine are pixel-identical BEFORE vs AFTER. I diffed every lighting at ticks 0, 28, 66, 110, 134 and 140. Changed pixels are only the arms, gloves and sleeves, plus sub-pixel dither noise in the world. Example: capB/sunlit/110.png vs capA2/sunlit/110.png. The diff image (w/diff_sunlit_110.png) is black over the whole rifle and magazine and white over both forearms and both hands. Median RGB of a receiver patch (860,360)-(940,420) is identical in all four lightings (sunlit 67,68,65; shade 31,36,39; backlight 32,36,39; dark-interior 31,35,39), and the rifle patch luminance is the same before and after. The "fixed studio environment" change therefore had no visible effect on the weapon in these stills. Either it is not applied to the rifle material, or it is a no-op there. Item A of the brief is unchanged from the previous version.
2. The visible gains are all on the arms and hands: smoother glove topology, more even sleeve lighting, a calmer hip entry in the normal clip. They are real but modest.
3. The reduced-motion 'calm' clip has a new weakness around ticks 64-72. The hand and magazine leave the bottom of the frame, and a flat olive sleeve tube fills the lower left.

## Findings, ranked by severity

### S1. Rifle still reads as warm grey / olive-khaki painted plastic in sun; no material improvement
- Evidence: capA2/sunlit/134.png and w/open_124b.png. Receiver, handguard and rail sit around RGB 67,68,65, slightly warm grey-green with very low specular.
- The suppressor is a flat grey cylinder with a brown cap, with no metallic gradient. See w/grip_110.png (suppressor at upper right).
- Metal highlights exist only as thin edge glints on the ejection cover and rail (w/open_124b.png) and as the chrome streak on the suppressor in backlight (w/backlight_110.png). Those are identical to BEFORE.
- Receiver, handguard and grip are distinguishable by form (handguard slots, rail, textured grip, tan magazine). They are not distinguishable by material: the receiver and handguard are nearly one value and hue.
- In shade, backlight and dark-interior the rifle collapses to the same near-black blue-grey (luminance about 33 in all three; patch (880,330)-(960,400) at tick 110). The suppressor end is pure black in shade and backlight (w/shade_028.png, w/backlight_028.png, crushed). The pistol-grip well and magazine housing are also near-black.
- Colour shift through the reload (ticks 0, 40, 100, 124, 134): none that I can measure. The hip-pose receiver median is constant across ticks 28, 40, 100 and 110. Tick 0 and 134 are different poses and were judged by eye; they look consistent. This is good for continuity but it also shows the rifle is not reacting to light.
- The tan magazine is the only warm, saturated object on the rifle (sunlit). It is what makes the weapon look khaki. In shade it drops to charcoal grey (w/hip_A.png, shade column, tick 76), so the sun-to-shade value mapping is not credible.

### S2. Calm clip: hand and magazine leave the frame around ticks 64-72
- Evidence: w/reduced-calm_56-96.png, top row, ticks 56, 62, 68.
  - Tick 62 shows only the mag top and the finger tips.
  - Tick 68 shows no hand and no magazine, only the sleeve edge.
  - Tick 72 shows the sleeve tube and a clipped magazine corner.
- The hand returns visibly at tick 80 (mag in an open palm). The magazine-pixel proxy I used (tan mask, y>300) dips to 2253 px at tick 70 in AFTER calm against 5175 in BEFORE calm. Visibly it is worse than BEFORE calm (w/calm_56-96.png), where the hand cups the magazine and stays at the bottom edge through ticks 62-76.
- Cause: the pickup is 28 cm below the well instead of 11 cm. The grasp is now partly off-screen.
- The mag enters the frame together with the hand from about tick 76 on, which is the intended fix. It works, but only after a dead stretch of about 8 ticks where the magazine is neither seen nor held. Reads as "pop out then pop in".

### S3. Support forearm at the hip is a featureless foreshortened olive tube
- Evidence: capA2/sunlit/72.png, w/hip_A.png, w/A_sun_56-88.png (ticks 68-76), w/reduced-current_56-96.png (ticks 62-80), where the tube spans the lower-left third of the frame.
- It is no longer a near-black wedge. Ground-bounce makes the underside a readable olive in sunlit and backlight, and a dark olive gradient in shade and dark-interior (hip_A.png columns 2 and 4).
- It still reads as a log or cone: a smooth cylinder with a "tread" camo-and-wrinkle texture and no cuff, glove or hand in frame, 600+ px long, for about 10 ticks (62-76).
- BEFORE had the same issue to a lesser degree because the hand was visible earlier (capB/sunlit ticks 60-70, hand visible with the magazine). I would call this a mild regression in screen composition, with better lighting.
- At tick 58 the open hand reads well (palm up, four long fingers and a thumb). That frame is the best new pose (w/A_sun_56-88.png, top-left cell).

### S4. Magazine floats at ticks 58-64 in the normal (non-reduced) clip, but with a hand in AFTER
- Normal sunlit AFTER: tick 58 shows an open hand right next to the dropped magazine, tick 60-64 the magazine at the bottom edge with fingers. See w/A_sun_56-88.png.
- BEFORE: the magazine tumbles with no hand in frame (w/B_sun_56-88.png ticks 56-64). AFTER is better here; the pickup is no longer unsupported.
- From tick 72 the hand sits at the bottom of the magazine in both versions. Insertion ticks 82-98 are fine in both (w/A_sun_76-98.png). The magazine is visibly cupped from below and aligned to the well. No pop-in after tick 76. Seated at tick 110 is clean.
- Remaining gap: tick 66-70 in every variant (normal, calm, still, current) has the magazine essentially at or below the bottom edge (proxy about 1-2k px, vs 6-10k in the rest of the clip).

### S5. Grip-hand fingers are still stacked spheres
- Evidence: w/open_124b.png and w/grip_110.png (left side of the pistol grip, three or four round finger pads). Same in BEFORE and AFTER.
- Wrap around the pistol grip is plausible in silhouette but the finger segments are blobs with no knuckle ridges. Sausage fingers remain on this hand.
- The support hand is clearly improved: see S-hands below.

### S6. Value inconsistency between hands and gear in low light
- In shade and dark-interior the gloves and sleeves are far brighter than the surrounding ground and the rifle. Support glove luminance is about 38 in shade and dark-interior, against 18 for the dark-interior ground and about 33 for the rifle. The grip glove is darker (about 23 in the same patches).
- The two hands do not match in value (support brighter than grip). The arms read as lit by a separate source (w/dark_A.png, ticks 28, 110). It is not a glowing rim, but it is a pale-grey ghost look.
- No over-bright rims on the sleeves. The cuff band stripe is the brightest part of the sleeve in every lighting.

### S7. Muzzle flash and smoke (ticks 136-146): acceptable, unspectacular
- Evidence: w/flash_zoom_A.png (rows sunlit, shade, backlight, dark-interior; ticks 137, 139, 142, 145).
- Tick 137 is a white-yellow disc with a hot core and a ring. Ticks 139 and 142 are a soft grey-white puff. Tick 145 repeats the disc.
- The flash lights the handguard slot edges and the support glove orange. This is the best-looking lighting in the set and reads well in all four lightings.
- The flash is a flat billboard disc with no spikes or directional shape, and the smoke is a single soft blob. It is passable at 1280x720, not premium.
- Unchanged from BEFORE (same frames in the contact sheets).

### S8. Other
- Sleeve camo and weave texture is crisp at the hip but shows a faint tile pattern at the stretched forearm (w/A_sun_56-88.png ticks 72-76).
- The rifle's pose at tick 0 and 134 (low in the lower right with the support arm extended) is fine. Nothing clips visibly.
- No visible clipping of the glove into the magazine or grip at ticks 28, 98, 104, 110. The support hand's fingers rest on the magazine face (w/open_124b.png). That is a contact, not a penetration.

## What improved

- Hands: glove mesh is smoother and the fingers are longer and more distinct. See w/open_124b.png (support hand; the AFTER fingers have separate segments and a visible knuckle line). The open return hand at ticks 118-126 is clearly better: a flat palm with thin fingers and a thumb, no blob (w/supp_28.png area, w/A_sun_104-124.png). The wrist cuff crease line (black line on the grip-hand sleeve at tick 110) is gone (w/grip_110.png).
- Arm lighting: forearm and sleeve undersides are lifted by ground-bounce. In sunlit and backlight they read as olive cloth instead of near-black. In shade they stay dark but readable (w/shade_028.png right panel vs left).
- Reload entry: in the normal clip the support arm and hand now arrive with the magazine (tick 58 hand next to the magazine; ticks 76-90 hand holds it from below).
- Reduced-still variant: hand and magazine stay mostly in frame. Ticks 76-96 show a clear palm-held magazine carried up to the well (w/reduced-still_56-96.png). Return to the firing grip is clear.

## What regressed or did not move

- Regressed: calm ticks 62-72 (S2); lower-left screen share of the tube-like forearm (S3).
- Did not move: rifle and magazine materials (S1), highlights, colour (identical pixels); grip-hand finger blobs (S5); muzzle flash (S7).

## Variants

- reduced-calm: readable except ticks 62-72 (S2). Open hand and magazine clearly visible at ticks 80-98. Return to the firing grip at ticks 118-134 is clear.
- reduced-still: best of the three for continuity; rifle sits steady and the hand always has a palm under the magazine after tick 74.
- reduced-current: forearm tube dominates ticks 62-80 (w/reduced-current_56-96.png); hand first appears under the magazine at tick 80. Worst of the reduced set.

## Scores (0-10, scoped to the weapon and hands in these stills only; the gate is 8.5; the previous same-family review gave 5.0 on all four)

| Aspect | Score | Why |
|---|---|---|
| Materials | 5.0 | Rifle pixel-identical to previous. Grey-olive, low specular, no graphite-metal read; crushed black in shade and backlight. No credit for the claimed environment change. |
| Viewmodel lighting | 5.5 | Arms are better lit (ground bounce, no black wedge), but the support hand is brighter than the grip hand in low light and the rifle ignores the lighting. |
| Hands | 6.0 | Cleaner topology and a good open return hand; support-hand grasp improved. Grip-hand fingers still spherical blobs. |
| Reload presentation | 5.5 | Pickup is now supported in the normal clip; calm clip loses the hand and magazine for about 8 ticks; forearm tube dominates the lower left. |

None of the four reaches the 8.5 gate.

## What I could not judge

- Motion at speed (60 Hz playback, easing, jitter, hitching, frame pacing); I saw 4-tick stills only. The ticks 64-72 dead stretch could be less or more noticeable in motion.
- A real phone screen (size, brightness, glare, touch HUD overlap, 20:9 and 4:3 captures were not reviewed).
- Audio.
- Whether the environment-lighting change is applied to the rifle at all in the build. I can only say the output pixels did not change.
- Whether a human tester would accept this; I am the same model family as the author.

## Materials re-judgement vs v9 (added after coordinator correction)

Correction accepted: BEFORE (5357329) already had the studio-lighting change, so my "pixel-identical rifle, therefore no-op" inference in S1 and the headline was wrong as a verdict on the change. Identical rifle pixels between BEFORE and AFTER only show the rifle is unchanged this round. The right baseline is v9 (ed85754). I compared 57f6464, v9 and v10 in art-v10/materials/frames/ (before-after-sunlit/shade/backlight.jpg, receiver-zoom-sunlit.jpg, v10-stills-backlit-shade-skin-inspection.jpg), by eye. I did not re-measure v9 myself.

- Graphite vs v9 in sun: yes, somewhat. v9 is visibly paler, matte and olive-brown. v10 is darker (README luma 54.6 against 69.7; this matches what I see in receiver-zoom-sunlit.jpg), with tighter edge glints on the rail and cover. It reads as dark painted graphite or parkerised metal. It does not read as metal with a convincing specular response: still warm grey-olive in sun, subtle highlights, flat large faces.
- Receiver vs handguard separation: only marginally better. In sun the two are still close in value (README itself says 54.6 vs 56.6). The difference is mostly softer highlights on the polymer handguard. I would not call this resolved.
- Reload colour swing: absent or small to my eye across the reload ticks in the v10 strips (sun, shade, backlight). The 57f6464 strip shows the blue-slate to bright-band swing, and v9 and v10 are both stable. Against v9 this is neutral, not an improvement. In shade and backlight v10 is again near-black, so little can be seen.
- Backlight and the inspection skin (v10-stills...): the firing frame has good edge highlights and warm flash fill; the ready frame is a near-black silhouette with a bright suppressor streak.

Revised scores (stills only; gate 8.5): Materials 5.5 (was 5.0: credit vs v9 for darker graphite and tighter glints, but receiver/handguard and metal specular still weak). Viewmodel lighting 5.5 (unchanged: stable across the reload, but shade and dark are crushed and the arms are brighter than the weapon). Hands 6.0 and reload presentation 5.5 stand as above.
