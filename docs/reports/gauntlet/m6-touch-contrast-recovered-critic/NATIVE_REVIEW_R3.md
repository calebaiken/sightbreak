# Touch contrast R3 actual-output review, 2026-10-23

Verdict: FAIL the preregistered combined R3 numeric gate. Actual product/method
acceptance is not granted. Source `a52022169241df9ff662039547a375e1c46ac1c5`
and frozen analyzer remain unchanged; its exit 1 is retained. A separate blind
visual verdict cannot override this result.

The candidate resolves 240/304 group rows. Its 32 active-label rows, both sets
of 32 count rows, and both sets of 32 joystick rows pass their declared limits.
Their conservative minima are 4.893:1, 5.655:1 empty / 7.828:1 ready, and
11.604:1 ring / 10.473:1 knob. This is bounded native engineering evidence,
not whole accessibility acceptance. The candidate still has 64 unresolved rows:
32 regular borders, 16 active icons, 8 inactive icons and 8 held borders. Eight
additional held-border rows resolve but fail 3:1, with minimum 1.190:1.
The baseline resolves 216/304 rows and also fails.

## Independent native checks

I verified every hash for the 2,576 native PNGs: 16 shared backgrounds and 1,280
images per source. Both source/manifest identities match the frozen receipt;
the controls bind the same baseline background receipt and the same complete
Godot 4.7.2 official / llvmpipe identity. The 32 scene records per source match
their native receipts and prescribed layout, scale, inset, state and counts.
Geometry dictionaries are equal across sources. Ten selected rows recompute
exactly with the frozen analyzer, including their support, error counts, inferred
color intervals, contrast bounds and coordinates. The original metadata has no
provenance errors. I also viewed the actual arena/smoke backgrounds and selected
uncropped baseline/candidate originals.

The evidence does not support shader-TIME drift, an image substitution, changed
input geometry or a source-identity error as the cause of these selected failures.

## What the failing pixels show

Coordinates below are `(x, y)` in the original native images.

| Original candidate scene / group | Pixel evidence | Interpretation |
| --- | --- | --- |
| `mobile-min-white-idle`, active icon | At `(655,562)`, isolated coverage is 255, but white-minus-black is only `[12,11,12]` rather than approximately 230 codes. Normal is `[200,173,115]`; underlay is `[191,165,107]`; compositing residual is 6.988 codes. | A smoke-icon edge meets the later utility badge. Its pixel lies 9.353 pixels from the 9-pixel badge center, on the rasterized edge. This is real partial glyph occlusion, not ordinary glyph antialiasing. All minimum-scale active-icon rows fail reconstruction at one mobile or two desktop pixels. |
| `desktop-min-white-idle`, inactive icon | At `(773,562)`, isolated coverage is 255 but diagnostic difference is 9 codes rather than approximately 89. Normal/underlay contrast is 1.103:1. | The grenade badge similarly overpaints a glyph portion. Contrast exemption for the depleted icon does not exempt lost coverage. |
| `desktop-max-white-held`, held border | At `(1129,322)`, normal is `[216,185,120]`, suppressed underlay `[201,211,216]`; diagnostic difference is `[243,243,242]`, and reconstruction resolves. The row's lower bound is 1.192:1; observed normal/underlay contrast here is 1.239:1. | The gold held stroke is compared with the silver regular stroke beneath it. This is a genuine failure of the frozen foreground-versus-suppressed-underlay predicate. It does not establish the contrast of the visible final button boundary against its dark surround or the world. |
| `desktop-max-white-held`, regular border | At `(1132,321)`, isolated coverage is 255 but diagnostic difference is `[12,13,12]`, with an 8.741-code residual. At `(796,544)` the badge reduces it to seven codes. | Held gold paint and badges overwrite the earlier silver boundary. The strict intermediate-stroke audit cannot resolve it. |
| `mobile-min-white-held`, held border | At `(695,456)`, normal, underlay, black and white are all `[191,191,191]`, despite isolated coverage 255. | The later RELOAD lettering overwrites the border at this small radius. The original label baseline is +17 pixels, while the button radius is only 19.6. The unchanged label/border geometry creates a real crowded layout. |

The source draw order predicts these cases: regular border, optional held fill
and border, icon, outline/label, then count badge and digits. A utility badge at
`point + (.72r,-.72r)` straddles its own circular button boundary. At minimum
scale its edge also reaches the icon. Labels can extend beyond the small circle.
R3 correctly retains their lost isolated coverage as unresolved; dropping those
pixels now would change the declared method after seeing the result.

The baseline also has resolved contrast failures unrelated to reconstruction.
For example, `desktop-max-white-idle` active labels reconstruct at 2.705:1,
empty count at 2.789:1 and joystick ring at 1.045:1. These selected rows support
a real readability problem in the earlier source. They do not make the new
candidate's unresolved rows pass.

## Smallest next experiment

The largest actionable gap is the distinction between a visible final component
and a hidden earlier paint operation. Before another acquisition, preregister a
small semantic revision that measures the final visible button boundary against
its adjacent dark surround/external background. Explicitly record regular-border
coverage replaced by a held border, badge or label. Keep those occlusion counts
and the R3 failure; do not silently remove their pixels or change 3:1 / 4.5:1.
Every expected label/icon glyph still needs its complete isolated footprint and
an occlusion report. A missing glyph stroke must remain a failure.

The badge-over-icon and small-label collisions require a product draw/layout
correction, rather than a measurement exemption. A small source experiment can
test putting utility badge fill before icons/labels while retaining digits on
top, with all original positions and hit geometry preserved. The small-radius
label fit needs an explicit layout decision and scope amendment if its draw
position or body geometry changes. Do not relabel a hidden glyph as decoration.

First review that revised source and pure controls independently. Then root can
release a bounded matched native experiment. Dark-surround contrast, the final
component boundary, heavy-plate world occlusion and the original live HUD
touch-toggle remain open; this report grants no new engine run.

Evidence: [read-only audit script](audit_native_r3.py),
[all-image hash and selected-pixel recomputation](native-audit-r3.json), and
[ten exact original PNG witnesses](native-selected-r3/RECEIPT.json), 251,098
bytes total. These are unmodified copies, not recrops or reconstructed images.
The complete originals remain at
`/workspace/sightbreak-touch-contrast-native-recovered-r3` while the builder
finishes its member-verified archive handoff. No engine, import, export, OCR or
new native acquisition was run for this review.
