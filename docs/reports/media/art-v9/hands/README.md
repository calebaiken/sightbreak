# Hands, round 4 (art-v9): glove construction, finger form, and what did not change

Branch `claude/cs2-fidelity-art-production`, from `0c5623e` (the rifle finish fix). **Evidence: my own native renders and tests on llvmpipe; nobody else has looked at these frames yet (an independent review comes at the end of this round), and nothing was seen on a phone.** This checkpoint changes the arms' *source geometry and textures*; how the gloves are lit (why they can read as bare skin in sun) is Checkpoint C's.

## What I found first (frames at 2560 × 1440 and 1280 × 720, `frames/`)

- The glove's zones were within a few luma of each other (`fabric` 0.025, `palm` 0.036, `cuff` 0.023, `strap` 0.020 linear), so nothing about its construction read: a smooth tube with fingers. The seams (0.55 mm grooves) and the knuckle guard's edge were below a pixel at 1280 × 720.
- The grip hand's back and wrist read as **bare skin**: a pale beige-grey mass in sun (`frames/closeups-before-after-2560.jpg`, middle). The albedo is dark graphite; the pale is lighting (below), so no palette change alone fixes it.
- The support hand under the handguard at rest is a pale glove with no visible knuckle guard or panels (`frames/idle-hand-before-after-2560.jpg`).
- The shapes themselves (finger chains, thumb, thenar and hypothenar, wrist) are anatomically organised already (`frames/glove-preview-before.jpg`, a Cycles review render of the source SDF); the mesh that ships is a 1,800-quad retopology of it, and the guard and padding exist only in the normal map.

## What changed (`tools/art/relay_ar_arms.py`, `arms_build.py`)

1. **Construction you can read at 1280 × 720.** New regions in the glove SDF and the palette: `tip` (suede fingertip and thumb-tip caps), `seam` (raised piping, 1.15 mm radius, down both sides of every finger and thumb segment, across the back of the hand behind the guard, round the cuff's top edge), `pad` (a darker rubberised pad on the palm heel). The palm, tips and seams have their own values (palm and tips lighter than the knit back, the guard near black at 0.009, the thread a cool light grey); the guard is taller (3.2 mm against 2.4 mm, domes 4.2 against 3.0, finger-pad plates 2.4 against 1.6). `frames/glove-preview-construction.jpg` shows the zones.
2. **Finger form.** Shafts leaner (0.90 of the joint radius, was 0.94) and the joint condyles fuller (1.10 × 0.66 × 0.88, was 1.02 × 0.62 × 0.80), so knuckles read in a silhouette.
3. **A knit you can see.** The back of the hand and the cuff get a 4.6 mm knit-rib cell in the baked normal (three to four texels of the 1024 atlas; the old grain was 0.7 mm and vanished at gameplay size), the palm and tips a finer suede grain.
4. **Game mesh.** Glove 2,100 quads (was 1,800); the sleeve 28 × 16 (was 32 × 20; its folds are in the normal map): 9,268 triangles for both arms (was 9,180; budget 10,000).

## What went wrong on the way (kept so the next person does not repeat it)

- The first build painted **stray palm-coloured patches on the back of the hand and the wrist**: the palm filler is a volume inside the hand, and where the back is thin its surface was as near the skin as the fabric's, so the nearest-surface region rule gave those faces to `palm` (the same artefact was in the old build as cream blotches on the side of the hand). Palm and pad now take only faces whose normal points to the palm side.
- **The tip caps pushed the trigger fingertip 2.5 mm into the trigger** (the contact test's bound for the right arm is 1.5 mm; before this round 1.47). I bisected it by switching features off in no-bake builds (14 s each): the caps were proud of the finger's flattened section by about 1 mm on the pad side. Cut to the finger's real section, the build measures **0.0 mm left arm in the rifle, 0.9 mm in the magazine, 0.8 mm right arm in the rifle** (before: 0.0, 0.9, 1.47). No threshold was touched.
- The first fingertip caps were a warm neutral grey, which in the sun read as bare fingertips (cut-finger gloves). They are cool now.

## Measured

| | before (`0c5623e`) | after |
| --- | ---: | ---: |
| arms triangles (budget 10,000) | 9,180 | 9,268 |
| contact: left arm in rifle / in magazine, right arm in rifle (mm) | 0.0 / 0.9 / 1.47 | 0.0 / 0.9 / 0.8 |
| support hand least pixels outside the hip and the rise (`reload_visibility_test`) | 13,797 | 13,773 |
| thumb tip, least pixels while holding a magazine | 247 | 337 |
| the other visibility rules (15 in all), the 24 contact checks, 169 weapon-art checks, 92 sequence checks | pass | pass, thresholds unchanged |

## What did not improve, plainly

At gameplay size (`frames/gameplay-1280-before-after.jpg`) the change is **modest**: a visible stitched line at the cuff, defined fingertip caps, a dark guard shape on the back of the support hand at rest, a slightly fuller knuckle line. The grasp still reads as a cupped hand around the magazine's base, the open return pose still shows long thin fingers spread flat, and **the gloves still read pale and skin-like where the sun hits them**: by my estimate (a glove's median luma in sun is 89 where its albedo, the sun and the ambient light account for about 59) the additive terms (specular, sky reflection, rim, fill) are around a third of its brightness and wash the zone contrast out; the arms-wide probe attributes 9 luma to the sky reflection, 4 to the fill and 2 to the rim, and the rest is the sun, including its specular. That is lighting, not geometry, and it is the next checkpoint. The finger geometry is not new: I did not replace the SDF with a sculpted mesh, and I do not claim the hands are anatomically convincing. A sculpt-and-retopology route is not available in this container (headless Blender, no sculpting session); the realistic next step is hand-authored finger geometry outside it.

`tools/art/preview_glove.py` renders the source glove (Cycles, flat region colours) from four views in about a minute for shape review.
