# Frozen blind native-image verdict

**Decision: a reproducible pickup-pose improvement is visible, but there is no across-the-board visual or animation acceptance.** In the coherent contact sheets, Sequence 01 favors **B**; Sequence 02 is **uncertain overall** because cleaner poses compete with a conspicuous adjacent-frame entry step; Sequence 03 favors **B for pickup**, with an **A advantage in shaded return/ready material readability**. These letters are local to each sequence, not source identities.

This verdict is final before unblinding. No private mapping was opened, and no ownership, chronology, branch, implementation, test-result, or performance inference is part of the judgment. `freeze.json` and `SHA256SUMS.txt` seal this report and its machine-readable companions.

## Scope and independence

- Packet: `C:\Users\blith\AppData\Local\Temp\opencode\sol-visual-20261019-b83f76-evidence\blind`.
- Visually inspected with the image-reading tool: **all 78 individual lossless native originals** for the **39 pairs**, **all six chronological contact sheets**, and **four official Valve reference images**: **88 unique images**. Critical pickup frames and several sheets/references were reinspected.
- Pair images are 1280×720 originals. The contact sheets are chronological evidence at reduced presentation scale, not substitutes for native detail. The combined pair PNGs, JPEG equivalents, and strip JPEGs were not used as additional visual observations. Hashing a file does not mean that its image was visually inspected.
- Packet-declared conditions: fixed 60 Hz simulation, three capture conditions, common camera/weapon within a matched pair, and ticks `0, 58, 66, 67, 74, 78, 82, 98, 110, 118, 126, 134, 146`. Those are capture metadata, **not measured runtime performance**.
- Sheet A/B is coherent **within one sequence only**. Every still pair has its **own independently randomized** A/B order. No pair-to-sheet or cross-sequence source mapping is supplied or inferred in the judgments.
- No project source was edited or executed. No engine, Git, GitHub, source-history, private-directory, or mapping operation was performed. All deliverables are in this new external sibling directory; the raw packet remains untouched.

### Disclosure about the rubric lookup

The first rubric search in the allowed `docs/reports/QA-0.3.md` was too broad and its search preview incidentally returned historical assessment prose and scores. Those were not used or repeated as scoring evidence. Subsequent direct reading was restricted to the rubric at lines 9–21. **Source-identity blindness is preserved, but this review cannot honestly be described as completely prior-assessment-naïve.** This disclosure should remain attached if the verdict is reused.

The requested root `SPECIFICATION.md` did not exist. The allowed specification was located at `docs/SPECIFICATION.md`; only the relevant acceptance requirements were searched/read, including lines 554–566. Its evidence rule is applied here: untested criteria remain **UNVERIFIED**, not passed.

## Coherent neutral-sequence verdicts

| Sequence / condition | Overall | Pickup sheet | Return/ready sheet | Confidence and reasons |
| --- | --- | --- | --- | --- |
| 01 — sunlit, normal | **B** | **B** | **Tie** | High confidence in the pose difference, moderate in the overall judgment. At 74/78/82, A's large high-left diagonal sleeve dominates the lower-left view; at 78 its blunt/capped upper contour reads as an implausibly exposed arm segment. B keeps the support arm near the lower boundary while the magazine remains legible. At 66→67, the sheet does not show the equally obvious large visibility step found in Sequence 02. At 98–146, the principal hand/magazine/weapon poses are materially alike; small cuff/shading changes do not establish a return-motion win. |
| 02 — sunlit, reduced motion / calm | **Uncertain** | **A for pose/framing; B for the 66→67 entry continuity** | **Tie** | A has less intrusive arm presentation at 74/78/82. However, on coherent sheet A, an essentially empty/low hand at 66 is followed at 67 by most of an upright magazine already visible, with comparatively little hand displacement: a conspicuous one-tick visibility/entry step. B avoids that particular early large reveal but retains the bulky later arm sweep. At 60 Hz, 66→67 is one 16.7 ms sample interval. This is evidence of a sampled discontinuity/pop risk, not a playback, comfort, or complete animation-quality test. The competing defects prevent an unqualified sequence winner. |
| 03 — shade, normal | **B, qualified** | **B** | **A for material/detail readability; pose tie** | Moderate confidence. B reduces the same excessive arm silhouette at 74/78/82 and gives a cleaner view. At 98/110/118/126/134/146, A retains more olive fabric value, folds, and cuff/palm separation; B's darker sleeve loses information into a flatter mass. B's pickup improvement is the larger visible geometry/framing difference, but it is not a clean material/readability win. Both retain a very dark receiver/magazine in shade. |

**Do not add the randomized pair votes to infer these sequence identities.** The table above is judged directly from the coherent sheets. Native-pair judgments below keep their own local letters.

## Biggest reproducible gap and remaining defects

### D01 — oversized/high-entry support arm: the strongest comparative gap

The most repeatable difference is not extra surface detail; it is **how much of the left-side view is occupied by a thick, nearly straight sleeve during magazine pickup**. The poorer pose raises a broad diagonal forearm with an abrupt/blunt upper contour, whereas the better pose enters from near the lower boundary. The contrast is particularly clear at:

- Sequence 01, pair 5, tick **78**: **A over B**.
- Sequence 02, pair 4, tick **74**, and pair 5, tick **78**: **B over A**.
- Sequence 03, pair 4, tick **74**, and pair 5, tick **78**: **B over A**.

The magazine remains readable in the favored frames. This is a directly visible silhouette, anatomy-presentation, and obstruction benefit. It does **not** prove that the elbow is anatomically solved off-camera or that an entire reload is smoother. In several frames the grasp itself is cropped below the image; a hidden grasp is **unverified**, not automatically correct or broken.

### D02 — calm entry discontinuity at 66→67

Coherent Sequence 02 sheet A shows a much larger magazine visibility change between adjacent ticks than its hand-position change explains visually. This prevents calling its cleaner later poses a complete continuity improvement. Native Sequence 02 pair 2 and pair 3 were inspected independently for the hand/object detail; their A/B letters are **not** transferred to the sheet.

The appropriate follow-up evidence would be a genuinely chronological native-resolution run around 62–80 plus real-time playback. No such additional capture was executed for this review. The existing adjacent images are sufficient to flag the visibility step, not to invent interpolation, sound, controller feel, or a specific implementation cause.

### D03 — shaded sleeve readability tradeoff

In Sequence 03 return/ready, coherent A preserves more readable fabric and wrist separation than B. Darkening the foreground may be plausible in shade, but **darker is not automatically more physically correct**, and lost fold/palm/cuff information is a visible readability cost. No shader, light-source, or material implementation is inferred. The black receiver/vertical magazine remain comparatively flat in both.

### D04 — grasp, anatomy, and first-person integration remain simplified

- At 98/110, the support hand contacts the magazine base in the supplied images; a gross consistently floating magazine is **not demonstrated** there.
- At 118/126, an opening/releasing hand is not by itself a failed grip. Likewise, the free magazine at 58 can be the released old magazine and is not automatically an attachment defect.
- Palm/finger pads remain slab-like, the support contact is often a small base cradle rather than a richly articulated wrap, sleeves are broadly tubular, and wrist/cuff seams can look abrupt. These are presentation limits, not claims about hidden rigging.
- At 134/146, both sunlit sheets show similar support-hand/fore-end relationships and comparable final framing. This supports endpoint similarity, **not** a claim of jitter-free settling at every intervening frame.
- Character body anatomy, faces, third-person stance, feet/contact with the ground, and equipment animation are **UNVERIFIED** because no SIGHTBREAK character is presented for that purpose.

### D05 — shared environment and material ceiling

The yard is coherent and readable: structural rooflines, freight/relay lettering, containers, restrained lane markings, and graphite/crimson/muted-gold accents establish an original industrial setting. However, the sunlit view is dominated by broad plain wall/ground planes and hard shadow blocks; the receiver is an unusually uniform dark mass and surface response does not consistently explain edge shape. The shaded view gives more architectural depth, but not consistently convincing foreground form separation. These observations concern the captured views only, not unseen map areas.

## All 39 native-pair judgments

Each row was judged from **both individual 1280×720 PNG originals**. `A` or `B` means relative visual preference at that instant, not a source or animation verdict. `Tie` means no material preference under this evidence, not pixel equality. Confidence is confidence in the stated relative preference, not in whole-game quality. Machine-readable records are in `pair-judgments.json`.

### Sequence 01 — sunlit / normal

| Pair | Tick | Verdict | Confidence | Visible evidence / limits |
| --- | ---: | --- | --- | --- |
| 0 | 0 | Tie | Medium | Comparable ready silhouette, glove/fore-end overlap, and aim clearance. Minor cuff shading does not justify a winner. Shared dark, broad receiver and simplified fingers. |
| 1 | 58 | A | Medium | A leaves the support arm largely below the boundary; B exposes a broad left forearm and open palm. A obstructs less. The falling magazine need not be grasped at this release instant. |
| 2 | 66 | A | Low | A has a smaller left-bottom arm wedge than B. Grasp is mostly below-frame in both; no attachment or temporal conclusion is available. |
| 3 | 67 | B | Medium | B's lower entry is less intrusive than A's large diagonal sleeve. The new-magazine tip remains a low-boundary detail; fingers/contact are partly cropped. |
| 4 | 74 | A | Medium | A reduces the large high-left tubular sleeve visible in B while retaining the magazine. A's lower grasp is cropped, so it is not a verified grip win. |
| 5 | 78 | A | High | A has a low, relatively horizontal entry and visible contact near the magazine base. B has the conspicuous long high-left sleeve with blunt/capped upper contour. Strong framing/anatomy-presentation gap. |
| 6 | 82 | B | Medium | B keeps the support arm lower/smaller. A still occupies more of the left view with the sleeve. Magazine/base-hand relation is readable in both. |
| 7 | 98 | Tie | Medium | Both cradle the magazine base with similar fingers and weapon pose. Slight wrist/cuff tonal changes do not establish a better grasp. |
| 8 | 110 | Tie | Medium | Comparable seated/inserting-magazine presentation and palm support. Both have simplified flat finger pads and limited contact depth. |
| 9 | 118 | Tie | Medium | Comparable opening palm beneath the magazine. This release-looking pose is not evidence of lost attachment. Small seam/shading differences are not decisive. |
| 10 | 126 | Tie | Medium | Comparable open-hand return pose and weapon placement; neither still establishes settling, easing, or timing. |
| 11 | 134 | Tie | Medium | Similar fore-end support and return framing. Sleeve/cuff surface differences are minor in sunlight. |
| 12 | 146 | Tie | Medium | Similar ready endpoints and central-view clearance. No sampled-endpoint advantage large enough to call. |

### Sequence 02 — sunlit / reduced motion, calm

| Pair | Tick | Verdict | Confidence | Visible evidence / limits |
| --- | ---: | --- | --- | --- |
| 0 | 0 | Tie | Medium | Comparable ready silhouette and hand/weapon relationship; minor cuff rendering difference only. |
| 1 | 58 | Tie | Medium | Both keep most arm coverage near the bottom; one hand is more splayed, the other more curled. At magazine release neither makes an unambiguous quality gain. |
| 2 | 66 | B | Medium | B has a flatter/lower arm entry and visible curled fingertips; A forms a more intrusive angular sleeve wedge. No new-magazine grasp is proved by this instant. |
| 3 | 67 | A | Medium | A presents a clear upright magazine and compact lower support entry; B still exposes a large sleeve wedge with the hand/object mostly low. This static preference is not a continuity pass: see coherent sequence 66→67 caveat. |
| 4 | 74 | B | High | B keeps the sleeve at the lower boundary and the upright magazine readable; A exposes a large raised left diagonal sleeve. The different magazine heights alone are not a timing winner. |
| 5 | 78 | B | High | B substantially reduces the long straight sleeve across the lower-left view while retaining the magazine/base-hand relation. A remains bulky and tubular. |
| 6 | 82 | B | Medium | B's support entry is smaller and lower than A's broad bottom-crossing sleeve. Both show magazine-base contact. |
| 7 | 98 | Tie | Medium | Similar base cradle, finger-pad simplification, receiver placement, and material separation. |
| 8 | 110 | Tie | Medium | Comparable insertion/support pose; no decisive hand/magazine alignment difference. |
| 9 | 118 | Tie | Medium | Similar opening palm and magazine position. No gross floating-object defect demonstrated. |
| 10 | 126 | Tie | Medium | Similar open-hand return and gun framing; timing/easing unavailable from the still. |
| 11 | 134 | Tie | Medium | Similar support-hand/fore-end relationship and sleeve presentation. |
| 12 | 146 | Tie | Medium | Comparable ready endpoint. This does not certify a reduced-motion setting or human comfort. |

### Sequence 03 — shade / normal

| Pair | Tick | Verdict | Confidence | Visible evidence / limits |
| --- | ---: | --- | --- | --- |
| 0 | 0 | B | Low | B retains more olive fabric/fold and wrist detail. A is a darker, flatter sleeve mass. Both share a very dark weapon; darker is not automatically incorrect lighting. |
| 1 | 58 | A | Medium | A leaves the left view clearer; B exposes the broad sleeve and open palm. The released magazine is not expected to remain grasped. |
| 2 | 66 | B | Medium | B reduces the large left-bottom sleeve wedge. Hand/object detail is largely cropped in both; attachment remains unverified. |
| 3 | 67 | B | Medium | B has less diagonal sleeve intrusion and preserves the low object-entry area; grip remains partly below-frame. |
| 4 | 74 | B | High | B has the less intrusive lower sleeve entry; A exposes the large high-left tube. Both have difficult dark-weapon separation in shade. |
| 5 | 78 | B | High | B avoids A's large straight/blunt upper-left arm segment while keeping the magazine legible. Strong silhouette improvement despite darker sleeve detail. |
| 6 | 82 | B | Medium | B has lower/smaller support-arm coverage. A's brighter but broader sleeve is more intrusive. Both show a base-hand relation, not fully articulated fingers. |
| 7 | 98 | B | Medium | B more clearly separates olive fabric, folds, cuff, and palm. A loses these into a dark mass. Pose/contact is effectively tied. |
| 8 | 110 | B | Medium | B preserves more wrist/fabric information at comparable insertion pose. A is flatter/darker. This is a material-readability preference, not proof of physically correct lighting. |
| 9 | 118 | B | Low | B gives a slightly clearer palm/cuff/fabric read. Pose and open-hand release are similar; the tonal advantage is modest. |
| 10 | 126 | A | Medium | A has clearer olive sleeve/fold and wrist/palm separation in the open-hand return pose. B is more uniformly dark. |
| 11 | 134 | B | Low | B preserves somewhat more fabric/wrist detail under the fore-end; pose is otherwise comparable. |
| 12 | 146 | A | Low | A's sleeve/fold detail is more legible at a similar ready endpoint. The shared near-black receiver still lacks strong shape separation. |

## Scoped visual scores against the seven-category rubric

Anchors from the allowed rubric: **5** recognizable development blockout; **7** coherent playable alpha with visible simplifications; **8.5** consistently polished and convincing with only minor defects; **10** exceptional execution. Categories are equally weighted **when all are actually evaluated**. An aggregate is not computed here because effects and large parts of the other categories are uncaptured. Scores below describe only visible subscopes, with approximately **±0.5 point reviewer uncertainty**, not measured precision or whole-game grades.

| Equal-weight category | Actual captured-scope score / 10 | Evidence and limits |
| --- | --- | --- |
| Geometry and composition | **6.5**, pooled captured yard views | Coherent industrial architecture, container/cover masses, route lettering, lane hierarchy. Broad plain planes dominate the sunlit view; shade has more depth. Other locations, playable composition, and map-wide landmark quality **UNVERIFIED**. |
| Materials and surfaces | **6.5**, pooled captured gun/gloves/sleeves/yard | Cloth weave/folds, glove panels, tan magazine, and dark metal are distinguishable in sun. Receiver response is broad/flat, fingers are slab-like, and shaded detail is uneven. No shader/PBR implementation conclusion. Unseen assets **UNVERIFIED**. |
| Lighting and atmosphere | **6.5** for sunlit view; shaded viewmodel detail **A 6.5 / B 6.0 in Sequence 03 sheet labels only** | Clear directional shadow division and scene depth, but hard broad shadows/flat planes and dark foreground forms limit convincing grounding. A/B here is local sheet identity, never pair identity. Dynamic stability, character grounding, and other lighting conditions **UNVERIFIED**. |
| Models and animation presentation | **Sequence 01 A 6.5 / B 7.0; Sequence 02 A 6.5 / B 6.5; Sequence 03 A 6.5 / B 7.0**, local sheet labels | Pose/anatomy/occlusion and sampled continuity only. Compact pickup improves presentation, but tubular sleeves, simple finger contacts, calm 66→67 step, and shaded information loss remain more than minor defects. Complete animation, real-time smoothness, other weapons, and third-person characters **UNVERIFIED**. |
| Combat and cosmetic effects | **UNVERIFIED — no score** | No SIGHTBREAK firing, impact, smoke, casing sequence, hit feedback, case reveal, or cosmetic inspection evidence here. A magazine or distant scene object is not a substitute. |
| Identity and consistency | **7.5**, captured palette/architecture/weapon only | Graphite, crimson container accents, muted-gold lane/industrial accents, and restrained wayfinding fit SIGHTBREAK Arcade. No parchment or Valve imitation is proposed. Menus, HUD, cosmetics, and game-wide consistency **UNVERIFIED**. |
| Competitive readability | **7.5**, static scene/viewmodel obstruction only | Routes and major silhouettes are readable; the compact pickup reduces left-side obstruction. Dark weapon detail and bulky alternative arm remain limitations. No opponent/team test, HUD, crosshair usability, phone display, touch reach, or effects-load validation: those areas **UNVERIFIED**. |

**No whole-game score, seven-category mean, release pass, performance pass, or 8.5-per-category acceptance is claimed.** The evaluated scopes do not demonstrate 8.5-level polish; unverified scopes cannot count as passes. Relative wins are not evidence that the winner reaches the absolute bar.

## Official Valve image anchors — actual images, not animation claims

The four JPGs and their provenance manifest were read at:
`C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3-evidence\cs2-references-20261019`.

- **`first-person-rifle.jpg`**: the actual image shows a foreground rifle/hand with readable curved and ribbed weapon forms, glove texture/paneling, and definite hand-to-fore-end overlap against a brighter architectural scene. It anchors shape separation and first-person contact readability, not reload timing.
- **`nuke-bombsite-a.jpg`**: large industrial tanks, gantry, signs, floor tracks/plates, and structural services have a strong hierarchy. Differing surfaces and controlled window/key light explain the space without relying only on extra small props. It anchors material/composition/grounding clarity, not a required layout or rendering feature set.
- **`operators.jpg`**: the promotional team image gives clearly layered equipment, cloth folds, recognizable proportions, and distinct hand/weapon silhouettes. SIGHTBREAK third-person character quality cannot be scored from its absent character evidence by borrowing this reference.
- **`smoke.jpg`**: the actual still separates a cloud from the environment and visible combatants, with a soft irregular boundary and depth/occlusion cues. No corresponding SIGHTBREAK smoke is captured here, so its effects category remains unverified.

These are Valve-published bytes per the supplied manifest, not generated illustrations; their recorded retrieval date is **not** an individual capture date. Input hashes are recorded in the audit outputs and checked against the manifest. **Reference stills cannot judge CS2 animation**, smoke dynamics, player comfort, or gameplay responsiveness. SIGHTBREAK need not copy Valve's art, asset density, palette, or technology to meet its own clarity/polish bar.

## Limits and useful next evidence

1. Thirteen timestamps across 153 declared simulation ticks are sparse. Except for 66→67, intervals contain unsampled frames; jitter, acceleration, trajectory, grip switching, frame pacing, and perceived smoothness cannot be reconstructed from them.
2. A fixed 60 Hz capture setup is not proof of sustained 60 fps or mobile performance. No performance evidence was inspected or scored.
3. Reduced-motion intent is stated by capture metadata. Pose differences and the adjacent step can be discussed, but the setting's wiring, accessibility compliance, nausea reduction, sway/recoil behavior, and subjective comfort remain **UNVERIFIED**.
4. Low framing can conceal a bad grasp as well as improve clutter. A useful verification would keep the wrist/fingers/magazine visible around entry, without introducing the high-left arm tube.
5. The next evidence should specifically resolve Sequence 02's 66→67 entry, preserve shaded wrist/fabric separation without lifting the entire weapon unrealistically, and show complete native real-time reload playback plus broader combat/character/effects/HUD evidence. These are evidence requests, not claims that such work exists.
6. No claims about historical or newer owners, source implementation, automated correctness, performance gains, or upstream quality are adopted. The incidental historical rubric-preview exposure is disclosed above; no mapping was accessed before or after freezing.

## Artifact key

- `pair-judgments.json`: all 39 independent native-pair decisions, ticks, confidence, visible defects/limits, and exact image paths.
- `sequence-judgments.json`: three coherent neutral-sequence decisions and six sheet decisions; no source mapping.
- `scoped-scores.json`: seven-category scope/score/verification records; no aggregate.
- `inspected-images.json`: the 88 unique visually inspected images, exact byte sizes, dimensions, and SHA-256 hashes.
- `integrity-check.json`: read-only verification of the blinded packet manifest, packet snapshot hashes, and four reference hashes. Hash-only files are not represented as visually inspected.
- `freeze.json`: final freeze time, independence disclosure, and output hashes.
- `SHA256SUMS.txt`: SHA-256 hashes of every other output artifact, including the freeze record.

**Stop condition: verdict frozen while still source-identity blind. Do not open the private mapping as part of this review.**
