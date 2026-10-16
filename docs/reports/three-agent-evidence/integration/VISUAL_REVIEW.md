# Independent native visual review — frozen PR #2 graphics in combined integration

**Decision: rendering compatibility passes this sampled review; visual quality remains about 5.5/10 and does not meet an 8.5/10 quality bar.** The rifle and reload are functional and readable in sunlit conditions. The current framing, hand forms, shade lighting and default reduced-motion behavior still need correction. This is a separate visual assessment of the newly generated native captures, not an inference from implementation tests or an endorsement of earlier self-scores.

## Evidence and scope

Reviewed all four new stage sheets: [sunlit](/workspace/reviews/three-agent-20261016/visual/sunlit.jpg), [shade](/workspace/reviews/three-agent-20261016/visual/shade.jpg), [backlight](/workspace/reviews/three-agent-20261016/visual/backlight.jpg), and [reduced current](/workspace/reviews/three-agent-20261016/visual/reduced.jpg). Inspected ten original 1280×720 PNGs separately, listed with dimensions and SHA-256 in `visual-inspected-images.json`. In particular, sunlit 034/058/074/090/118, shade 074/090, backlight 090, reduced 074/118.

These are Godot 4.7.2 native OpenGL compatibility captures on Mesa llvmpipe from `reload_sequence_capture.gd`, using the real actor, imported rifle/arms and presentation code in the combined source. They use the local-authority fixture, not the exported executable or a phone. `captures.json` records each actual command and exit status. Each run advances 168 simulated 60 Hz ticks; twenty selected ticks were saved as PNGs. Therefore this review establishes stage-to-stage continuity and visible defects at named frames, not the precise onset/duration of an artifact between unsaved ticks or a real-time frame-rate assessment. No audio-quality judgment was made.

The integrated graphics remain the frozen `ed8575454452d8f67c006814a1917fa6cc24fb46` presentation. The independent source comparison in `source-proof.json` already establishes that the actor difference from that graphics head is confined to preserved PR11 movement delegation/constants. No new visual defect here is attributed to a wholesale integration overwrite.

## Concrete remaining issues for PR #2

### 1. Replacement magazine enters the viewport before its supporting hand is visible — P2

Reproduce with the sunlit capture command in `visual/captures.json`. Inspect [sunlit 074](/workspace/reviews/three-agent-20261016/visual/sunlit/074.png): at 1.2333 simulated seconds, reload progress 0.5556, a substantial length of replacement magazine rises from the bottom around the center-left, while the hand gripping its base is entirely below the frame. A wedge of sleeve remains visible at the far lower-left; it does not show the grasp. The magazine consequently reads as unsupported. The same staging appears in [shade 074](/workspace/reviews/three-agent-20261016/visual/shade/074.png) and [reduced 074](/workspace/reviews/three-agent-20261016/visual/reduced/074.png). By saved frame 082 the hand begins to appear, and by [sunlit 090](/workspace/reviews/three-agent-20261016/visual/sunlit/090.png) it visibly supports the magazine.

This is a **framing/staging defect, not evidence that the mesh detached from the bone**. Current `_pose_magazines()` assigns the replacement the same `in_hand = _hand_in_gun() * _grip_offset` transform during ACQUIRE..LETGO. CSV frame 074 reports `held=replacement`. The older Gemini prose alleging an independent `spare_magazine_offset()` curve does not describe this frozen source. Adding BoneAttachment3D alone would not resolve the observed framing.

Correction should bring some readable fingers/base grasp into the picture as the replacement rises, or restage the hand/magazine pickup trajectory so the lift reads as one action. Recheck normal and reduced at the first visible magazine frame and throughout the rise. The existing visibility test counts sleeve/arm pixels toward its no-disembodied-magazine rule during the hip window, and the sequence test allows up to 25% replacement visibility at first draw. Those gates can pass the observed visual defect; a passing attachment or pixel-budget assertion is not quality acceptance.

### 2. Shade suppresses material and hand detail too strongly — P2

Compare [sunlit 090](/workspace/reviews/three-agent-20261016/visual/sunlit/090.png) with [shade 090](/workspace/reviews/three-agent-20261016/visual/shade/090.png). In shade, the receiver, grip and right glove form a dark mass against the lighter yard; subtle panel seams, glove construction and grip detail become difficult to distinguish at normal viewing size. The magazine and silhouette still read, so this is not a claim that the entire weapon disappears. [Shade 074](/workspace/reviews/three-agent-20261016/visual/shade/074.png) exposes the same loss of surface separation during the empty-well pose. Backlight preserves a clear tube highlight and rim, but the broad receiver remains flat/dark in [backlight 090](/workspace/reviews/three-agent-20261016/visual/backlight/090.png).

Correction should preserve distinguishable glove, polymer grip and painted-metal forms in shade while retaining the stable sunlit finish. Recheck matched idle/grasp/insertion/return frames in all three views. Increasing a single global brightness value would require checking the sunlit gloves again.

### 3. Default reduced motion retains the full rigged reload roll and lift — P2

The recorded reduced run uses `--reduced` with **variant current**, confirmed by its `viewport.txt`. Its grasp, hip and return stages retain essentially the same whole-rifle motion and the same unsupported-looking magazine entry as normal; compare reduced and sunlit sheets and frame 074 originals. In current source `REDUCED_RELOAD_VARIANTS.current` sets roll/lift/recoil to 1.0, selects the normal reload clip, and `reduced_variant` defaults to current. Sway/bob/equip motion and the seat kick receive separate reductions, so the toggle does have an effect; the rigged reload roll itself does not become calmer.

Correction needs a deliberate default/accessibility choice, exposed to the user where appropriate, with a measured/reviewed lower-roll clip or staging. The calm/still variants exist in source, but neither was generated in this new four-view set, so this review does not assert their final visibility or quality. This is an observation of motion amplitude and product behavior, not a claim of clinical safety or user comfort testing.

### 4. Hand forms and return pose still look synthetic — P2 quality

At [sunlit 034](/workspace/reviews/three-agent-20261016/visual/sunlit/034.png), the right gripping digits read as a row of rounded tips and the broad back of the glove has little convincing tendon/knuckle structure. At [sunlit 118](/workspace/reviews/three-agent-20261016/visual/sunlit/118.png), the returning left hand presents a wide, flattened palm and evenly fanned rounded fingers rather than a relaxed, progressively curling grasp. The exaggerated thumb/palm silhouette is particularly visible beside the straight magazine. These forms are understandable as a hand, but remain far from convincing tactical-glove anatomy.

Correction should refine phalange/knuckle planes, thumb-to-palm volume, finger spacing and asynchronous curl during release/return. Preserve the current positive hand-to-magazine contact seen at 034 and 090. Bone correctness and a minimum count of visible finger pixels do not measure anatomy.

### 5. Stable sunlit finish still lacks clear painted-metal character — P3 quality

In sunlit 034/074/090, the upper receiver and handguard have a very uniform matte gray response; shallow seams and edges supply most of the differentiation. The black textured grip and tan magazine distinguish the major parts, but the broad receiver does not have much convincing machined painted-metal response. In source the first-person roughness floor is 0.80, which is consistent with the subdued highlights. This review has no new skinned capture and therefore makes no claim that a particular cosmetic skin failed.

Correction should recover restrained surface/edge variation without reintroducing the former bright sky reflection across the body. The sampled sheets do **not** show a broad pale/white receiver flip during the reload; that stability improvement should be retained. The intentionally strong narrow backlight on the buffer tube is distinct from a whole-receiver color flip.

## What this evidence supports

Two distinct magazines are visible across extraction, discard and replacement. The old magazine is away from the well at 058; the replacement is under the well at 090, seated by 110, and the support hand returns by 126/134. The major action is coherent, and the visible 034/090 grasp looks connected. Native views show no obvious missing imported mesh, shader compilation failure, magenta fallback, whole-rifle material flash or broken pose. Reload completion and first muzzle flashes appear in the expected later saved stages. Small visual effects and actual sound quality cannot be rated thoroughly from these stills.

| Category | Independent quality score | Evidence-based assessment |
| --- | ---: | --- |
| Rendering compatibility / finish stability | 7.0/10 | Coherent imports and stable sampled body tint; broad finish remains simplistic |
| Mechanical action and retrieval staging | 5.5/10 | Two-magazine action reads; unsupported-looking replacement entry remains |
| Hand anatomy and posing | 5.0/10 | Connected grasps, but rounded digits and flattened return pose |
| Material separation and lighting | 5.0/10 | Sunlit parts distinguish; shade loses glove/receiver form |
| Framing and default reduced motion | 4.5/10 | Hip grasp leaves the viewport; default retains normal roll/lift |

**Overall visual assessment: approximately 5.5/10, a functional prototype needing further art and staging work.** This is a qualitative reviewer judgment, not a statistical metric. Passing reload, shader, authority and export-resource tests is valuable implementation evidence and does not raise these visible results to 8.5/10. No source edits or GitHub posts were made by this reviewer.
