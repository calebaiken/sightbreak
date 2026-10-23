# R4 source preregistration, 2026-10-23

Status: source/pure work only. No R4 engine, import, UID generation, native render,
OCR or live-HUD acquisition is released. R3 remains FAILED at `a520221`; its
immutable evidence `0f83243` and independent actual verdict `39b5a9d` / `8a5f531`
are retained. A blind preference does not override those failures.

## Source and supported defects

Primary R4 comparison is the actual failed R3 drawing source
`a52022169241df9ff662039547a375e1c46ac1c5`. Its genuine native images and independent
pixel witnesses establish the local bar. The original published `138a1ab` baseline
and all R3 results remain separate historical evidence. No result is relabeled.
WCAG thresholds stay 4.5:1 for active labels/counts and 3:1 for meaningful UI.
CS2 media restrictions, physical devices and whole accessibility remain open.

Independent actual pixels show a utility badge overpainting icon strokes at the
minimum clamp, RELOAD lettering overpainting a small circular border, and held
gold paint replacing the earlier silver stroke. The first two require a drawing
correction; final-visible boundary semantics are registered separately below.

## Candidate drawing changes

Change only drawing in `game/scripts/ui/touch_controls.gd`. Preserve every input
function, target center, radius(), action_at(), hit policy, safe-area policy,
layout persistence/edit behavior, action label word and 12-pixel action font.
No text shrinking or abbreviations. Glyph paths remain unchanged.

Paint utility badge backgrounds and their protected rim before icons/labels;
keep count digits on top. Draw a one-pixel black icon surround using the same original glyph paths
with stroke widths increased by two, then the unchanged foreground paths. The
filled FIRE center expands by one pixel only in the surround pass. Preserve depleted foreground alpha and report its contrast exception;
its complete glyph footprint and count readability remain mandatory.

For non-fire buttons below a 32-pixel nominal radius, move the icon center from
-8 to -13 pixels and the label baseline from +17 to +6. Keep the FIRE stack and
all larger stacks unchanged. This uses the same words/font while separating the
small icon and label foregrounds. A compact plate radius is
`min(1.25*r, max(r,26))`; other plate radii remain r. The 1.25*r cap is the EXISTING
physical hit radius, not a new interaction region. Body fill and held fill follow
the registered plate radius. Compact rim center radius is `paint_r+1`, with a
3.5-pixel dark stroke; larger rim center radius remains r with its 5.25-pixel dark
stroke. Light/held strokes stay 1.25/2 pixels. This clears the full RELOAD glyph
without changing its size; the outer compact dark halo stays within `r+8` across
the full scale clamp. Badge center/radius/digits stay
at their original positions; a dark/light rim protects their final silhouette.

At minimum clamp, ten ordinary plates expand from 19.6 to at most 24.5 pixels,
inside the existing hit region. Their analytical extra fill area is at most
6,789 square pixels, under 1% of 960x720. Maximum mobile/desktop plate sizes do
not expand. Decorative halos can extend beyond the hit region: report their
exact pixel spill and maximum distance. Noninteractive utility badges already
protrude beyond the hit circle; report their rim's additional extent. The critic
must reject misleading target affordances or unacceptable scene occlusion.

The original small-clamp AND maximum mobile cluster are mandatory cases. Source
and pure checks must establish all physical geometry and input text equality,
unchanged font/words/glyph paths, bounded compact body radius, and screen/safe-area
fit. The native fixture must later record per-control paint geometry and actual
footprint-versus-hit-region pixel counts; any action-label foreground outside the
hit region is a reported affordance failure, not silently accepted decoration.

## Full glyph gates

Keep the complete isolated native label/icon/count footprints, exact suppressed
underlays, black/white diagnostics, source/UID/background/image identities and
occlusion checks. Every expected visible glyph stroke remains required. Badge
or label collisions remain failures; do not classify missing glyphs as decoration.
Keep original quantization predicates and 4.5/3 thresholds for these rows.

## Separately registered final-boundary experiment

R3 intermediate regular/held stroke results remain retained and reported with
hidden/replaced coverage. They cannot be reinterpreted as R3 passing. R4's final
boundary experiment measures each complete painted action component after all
of its paint layers. This includes the plate, selected held rim, badge, icon and
label, with all other components left in source order. Capture a whole-component
suppressed underlay, black/white versions preserving primitive alpha, and an
isolated opaque whole-component footprint for each of the eleven actions.

At every pixel on the outer contour of that complete isolated footprint, require
a source-connected inward witness no more than four native pixels away with
actual component diagnostic contribution >=0.8 and conservative observed native
normal/underlay contrast >=3:1. Use all contour pixels, including protruding badge
and halo contours; no averages, percentiles or handpicked arcs. The witness path
must remain inside that action's footprint, so another control cannot supply it.
The four-pixel band covers the registered <=3-pixel decorative halo plus raster
edge; it does not erase glyph coverage gates or permit a hidden glyph.

The new predicate reports its minimum, worst contour coordinate, witness coordinate,
qualified contribution, exact foreground/underlay values and every unresolved
contour. Validate it with pure examples: bright/dark/busy backdrops, disconnected
components, a single failing contour section, distant contrast that must not
rescue an edge, unrelated front paint, and glyph loss that must still fail.
This is a new bounded final-edge engineering measurement, not a WCAG certificate.
The fresh critic must audit its definition, source and falsifiers before native.
Dark surround/external-background inspection and heavy-plate scene occlusion also
remain independent actual-image requirements.

Implementation detail fixed before native: contours use every 8-neighbor boundary
pixel, including holes. Witness contribution requires `min(W-B)>=206`, so the
existing ±2-code subtraction bound still leaves >=0.8 contribution. Glyph gates
import the unchanged R3 oracle. There are 2,816 PNGs per source: original/normal,
the 304 original group rows and 352 whole-action rows, each diagnostic row with
underlay/black/white/isolated-footprint images, plus 128 isolated layer footprints
for label/icon surrounds, badge paint and held fill. These retain exact spatial
intersections with every lost intermediate regular/held-border pixel, including
unattributed pixels; overlapping layers are not presented as exclusive causes.
All 48 intermediate border rows
remain diagnostics; the 608 other rows plus complete glyph/target accounting are
the new candidate gates. This is declared before R4 native, not a reinterpretation
of the R3 failure.

The first pure method attempt is retained. It exposed an overstrong *test*
assertion: at fully opaque `W-B=255`, the three selected-component images contain
no information about the removed U. Pixel algebra alone cannot prove that U.
The exact source-bound suppression wrapper, source/UID fences, unwrapped normal
equality, native background and PNG receipts are therefore essential; no claim
of independent opaque-U reconstruction is made. The corrected falsifier checks
an actual translucent contribution, where an unrelated U must fail the unchanged
compositing predicate. The opaque-underlay limitation is explicitly for the fresh
critic to review, not a dropped native error.

Receipt-control attempt 2 was interrupted with SIGINT before completion because
the metadata-only test was unnecessarily running full-resolution pixel overlap
work. Its log/exit 130 are retained. Attempt 3 stubs that unrelated pixel layer,
as it already stubs decode/contrast for these metadata-only controls; it passes
all 15 controls. A separate small pure overlap control verifies that attributed
and unattributed hidden intermediate pixels remain reported. No native image,
product failure or threshold was changed by this test-harness correction.

## Native acquisition requirements, not yet released

Use a fresh source/UID freeze and the same 32 scene matrix, all exact-source
regressions and original native sizes/scales/states. Both sources and every
shared backdrop must have valid comparable provenance and renderer identity.
Record all actual visual footprint changes alongside unchanged physical geometry.
Keep failed rows and full raw outputs. No new native run occurs until a fresh
independent source/method review and explicit root lane release. No product
integration or shipped-title/accessibility acceptance follows this preregistration.

## Source implementation refinement, still before native

The glyph surround uses one wider-stroke pass, rather than the initially
considered eight shifted passes. This keeps the same glyph paths and default
foreground widths/radii, with a default-zero draw-only width parameter. The R3
native icon footprints have only 0/255 coverage, so their raster endpoints can
be checked against the wider stroke before qualification; no glyph is dropped.
The physical/input methods remain byte-identical. This refinement adds no
native output and grants no acceptance.

The first pure translation check is retained as `r4-source-pure-attempt-1.log`:
desktop-min RELOAD reached 24.240451 pixels from its center, beyond the first
candidate's inner idle rim at 23.875. It failed before native. The registered
compact rim offset above replaces that failed spacing. At minimum radius the
body is inside the 24.5-pixel hit circle, but the light/held rim extends 1.625/2
pixels beyond it and the dark surround extends 2.75 pixels beyond it. This
visual-versus-hit discrepancy is explicit and can be rejected by the critic;
it does not enlarge the actual touch target.
