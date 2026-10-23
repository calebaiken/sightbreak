# R4B ownership and safe-target preregistration

Source/pure only. R4 source freeze `16335ab` is NO GO under independent verdict
`6eb990f30fe005b46a763a014ba5e9d7cbbe09db`; R3 remains FAILED. Retain the exact
review counterexamples and historical fixtures unchanged. No engine, native
render/import, UID regeneration, OCR or live HUD is authorized for R4B.

This explicitly amends R4's input/layout preservation. The inherited max-mobile
FRAG/SMOKE paint overlap selects SMOKE at FRAG-painted (610.5,575.5), and the
max MENU full target escapes the safe area. Correct layout, physical target
clamping and actual nearest-action ownership before another native experiment.
Keep all action names/availability, font 12, original glyph paths, input events,
mouse/keyboard/controller mode policy and saved normalized coordinate format.

The candidate will use the following source policy. These are hypotheses for a
fresh critic, not validated geometry or physical reach claims:

- Derive touch geometry scale from the requested HUD scale, bounded by safe
  rectangle width/640 and height/480, with the existing .7 lower scale bound.
  Preserve the requested setting itself. Font size stays 12. The cap avoids
  allowing large plates to collide merely because the viewport becomes short.
- Give ordinary action targets a minimum 31px radius (62px diameter), retain
  larger 1.25-times-nominal targets, and keep FIRE/movement proportional targets.
  Compare normalized distance using the resulting hit radius and require <=1.
  Make exact ties deterministic by action ID, independently of dictionary order.
- Clamp centers using the complete hit radius plus one pixel, rather than
  nominal radius+8. Preserve the original normalized default/persistence values.
  When the safe width is below 1100px or height below 650px, defaults respond as
  FRAG x=.58, SMOKE x=.70, JUMP y=.72 and SWAP y=.91. Apply that response only to
  positions still equal to their default; explicitly customized values remain
  customized. Non-touch desktop input behavior is unchanged.
- Keep complete glyphs and the R4 compact plate/glyph stack. Utility badge
  offset per axis is capped by both .66 times nominal radius and
  `(hit_radius-12.625)/sqrt(2)`. The 12.625 allowance is its 11.625px outer dark
  rim plus a 1px raster margin. Digits/font/badge radius/rim widths stay intact.

Test the actual nearest-normalized winning action across every source-derived
paint affordance and each retained original glyph pixel, not merely membership
in its own hit circle. For circular body/rim/badge envelopes include a 0.75px
raster margin and conservative full glyph/outline bounds. Keep wrong-owner,
unclaimed, neighbor-order/tie, pairwise paint-clearance and full-target safe-area
failures. Do not remove paint, glyphs, hidden pixels or counts from those gates.

Pure cases include every original fixture layout and capture-script viewport
(960x540,960x720,1280x720,1280x800,1920x720,1920x1080), plus 860x480 and portrait
720x1280, the full .7–1.5 scale range including transition values, original/native
safe insets, asymmetric notches and the existing 80/24/80/56 regression inset.
Report dimensions that cannot physically contain the minimum glyph/target layout
as unresolved; do not claim arbitrary tiny rectangles work. Include valid custom
edge positions and deliberately colliding/coincident custom layouts as negative
ownership controls. A user-created invalid layout is not evidence of a valid
default layout; neither is silently accepted by the proof.

The new harness must bind its geometry model mechanically to the exact product
functions and emit full case receipts, winning action witnesses and separations.
Add unexecuted Godot tests that directly call the real functions later. The
fresh native fixture must record actual target radii, resolved normalized points,
effective scale and per-control paint geometry. Its analyzer must validate the
new declared geometry separately for each source; equality with the rejected
layout is no longer an acceptance requirement. Native visible affordance pixels
must select their source action under the actual winning-action policy.

Keep original complete foreground footprints, 4.5:1 active text/count and 3:1 UI
thresholds, quantization and occlusion checks unchanged. Keep R4's final-band
metric narrowly described: it proves a contrasting connected band within four
pixels, not outermost-surround contrast, opaque-underlay identity or complete
interior nonocclusion. Component minimum alpha remains a limited check; retain
all separate glyph gates and actual-image review. No overlap threshold is relaxed.

Commit the preregistration first, then source/harness changes and a separate
exact source/UID freeze. A new independent critic must review before root can
release any runtime. Later native evidence and a fresh blind judge must assess
readability, full affordance truthfulness, scene occlusion and usable mobile
reach; source arithmetic cannot approve those qualities or shipped-game parity.
