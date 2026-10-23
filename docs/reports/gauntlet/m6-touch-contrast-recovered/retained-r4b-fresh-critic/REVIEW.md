# R4B fresh independent source and method review

**REJECT source/method readiness.** The new baseline ownership receipt fence does
not reject a contradiction between the recorded native result and independent
replay. Correct that fence and freeze the changed method before another source
review. The amended default geometry has no blocking defect in this review's
declared cases.

Reviewed source/method `2ea23f947aec6085449bced53c9b061618a67029`, handoff
`a4f942af1213f2d4a18a790adea624bcbcd3b7b5`, baseline
`a52022169241df9ff662039547a375e1c46ac1c5`. Freeze receipt SHA-256 is
`375b2a867d9fc2991eb9cf5a3caa7e0ef04a77c3fd9311194620425b09e8af68`.
This review ran source reads and pure Python checks only. No Godot, import, UID
regeneration, native capture, OCR, engine compile, export, CI or nested agent ran.
No native lane is released. R3 remains FAILED and R4 remains NO GO.

## Blocking receipt contradiction

In `scripts/analyze_touch_contrast_r4b.py:246`, `audit_ownership` independently
calculates each component pixel's winning action. Its receipt validation only
checks support count, witness count, unclaimed count, unique supported
coordinates and a recorded winner different from the component's action. It
never checks that the native witness set and winning identities equal replay.

The retained synthetic counterexample starts with the supplied ownership
fixture. FIRE's single support pixel moves to `(100,50)`, where the unchanged
geometry gives JUMP the winning target. The native receipt falsely claims zero
wrong-owner pixels and supplies no witness. The analyzer returns:

```json
{
  "errors": [],
  "actual_native_wrong_owner_pixels": 0,
  "independent_normalized_hit_replay_wrong_pixels": 1,
  "native_record_well_formed": true,
  "pass": false
}
```

The candidate's failure gate correctly rejects that row. The baseline takes a
different path: `audit_source` defines `provenance_valid` from `errors` and row
counts at line 401, while `comparison_passes` at line 410 permits a failing
baseline. With the other independent fences satisfied, that contradictory
baseline receipt is therefore accepted for comparison. A second retained case
supplies a wrong-owner witness with the correct count and coordinate but invents
`pause` as the winning identity; it also receives no receipt error.

These arrays are synthetic, not native evidence. They demonstrate the missing
validation path without claiming that an actual capture has produced it.

The preregistration requires every wrong/unclaimed native coordinate and winner
to be recorded, and the handoff explicitly says an invalid baseline ownership
receipt blocks comparison. Reconcile the complete native wrong-owner mapping
against replay and make a contradiction a provenance error. Keep an agreeing,
genuinely failing R3 baseline comparable. Add negatives for false zero counts,
omitted/extra witnesses, wrong recorded winners and unclaimed classification
through the baseline comparison path. No contrast or footprint threshold needs
to change.

## Geometry and source findings

The source translator copies `Vector2` assignments before changing responsive
coordinates, preserving GDScript's value semantics and raw saved values. Its
restricted expressions match the inspected product functions. The tested
normalized default values are below one, so the approximation used for default
equality does not introduce a relative-tolerance difference in these cases.
The translator remains Python arithmetic rather than actual native execution.

The responsive defaults, 31px ordinary minimum target, effective safe-viewport
scale cap and full-target center clamp are explicitly registered interaction
changes. At mobile-max `(960,720)` with 32px side insets, requested 1.5 resolves
to 1.4. FRAG and SMOKE centers are `(551.68,576)` and `(650.24,576)`, nominal
radius 39.2 and hit radius 49. The old overlapping FRAG-painted witness no
longer belongs to the FRAG affordance. MENU center `(878,50.4)` leaves 1px at
the safe right edge and 1.4px at the top of its complete target.

I audited the quadratic weighted-distance minimum over a disk. The neighbor
distance squared minus the owner's distance squared has a scalar quadratic
term, so minimizing along the negative linear direction and clamping the
stationary radius covers convex and concave cases. The interval error terms
conservatively subtract changes in centers, envelope radius and target radius.
The critical scales cover the inspected scale cap, minimum target, compact
plate, badge-offset and center-clamp branch transitions. Size-dependent default
selection stays fixed within each declared viewport/inset case.

The original certificate reproduces exactly: 32 cases, 2,482 positive interval
bounds over requested scale .7–1.5. Its smallest reported lower bounds are
0.00622136 normalized squared ownership margin, 0.000520833px containment and
2.6px paint clearance. The tiny containment bound is conservative interval
slack; it must not be presented as a measured native margin. The independent
1,998 endpoint/branch-interior evaluations have minimum sampled margins of
.25px inside the owning hit circle, 2.6px paint clearance and 0.0573316
normalized squared ownership. Two hundred random disk-bound checks and the
retained negative cases are in `checks.json`.

The certificate uses floating point calculations, endpoint `nextafter`
adjustments and a midpoint linearity check. Its real coverage rests on the
audited branch formulas, not midpoint agreement alone. It is source review
support, not a formally rounded interval proof of the native implementation.
The .75px raster allowance and old font-mask bounds still require actual new
native verification. Arbitrary tiny safe rectangles remain unqualified.

Customized coordinates keep their values. Colliding/coincident saved layouts
still fail the proof; the product does not repair or qualify them. Exact ties
use action identity independently of dictionary order. Dynamic joystick origin,
all movement states, physical reach and editing-layout usability remain outside
this fixed default-layout proof.

## Preserved measurement and provenance

All twenty frozen files match the exact source. Both staged projects have 323
original game files and 327 verified source/UID paths, regenerated diagnostic
bytes match, UIDs are unique and `.godot` is absent. The handoff changes no frozen
game or script byte. The sixteen historical glyph-mask input hashes still match
the retained R3 originals and scene receipts.

The future native fixture calls actual `action_at` at every isolated whole-action
support pixel center. Its winner cache is confined to unchanged geometry within
one layout. The analyzer replays all component pixels, including rims, badges,
counts and formerly hidden pixels. No decoration exception can produce a
candidate ownership pass. The blocker above concerns whether contradictory
baseline receipts invalidate comparison.

The 47 supplied controls pass. Complete foreground support, AA/quantization,
occlusion predicates, 4.5:1 active text/count and 3:1 UI thresholds are unchanged.
The 48 intermediate-border diagnostic rows stay retained separately from the
608 gated rows. Event/persistence functions, the raw default/persistence format
and the glyph helper match the rejected R4 source as declared.

I reran the three strongest final-band falsifiers against this analyzer: opaque
diagnostics can pass with an unrelated suppressed underlay; an invisible outer
contour can pass using an inward contrasting band; 60% interior replacement can
pass the component-wide minimum-alpha check. These remain explicit method
limits. Exact suppression/provenance, separate full-glyph gates and actual-image
inspection remain necessary. This review grants no complete primitive interior
nonocclusion, outermost dark-surround contrast, scene-occlusion, physical-device,
whole-accessibility or shipped-title quality acceptance.

Reproduction is source/pure only:

```sh
PYTHONPATH=scripts python3 -m unittest -v test_touch_geometry_r4b test_touch_method_r4b
python3 scripts/test_touch_geometry_r4b.py --certificate docs/reports/gauntlet/m6-touch-contrast-recovered/fresh-source-critic-r4b/reproduced-certificate.json
python3 docs/reports/gauntlet/m6-touch-contrast-recovered/fresh-source-critic-r4b/checks.py
```

The biggest immediate gap is a trustworthy baseline ownership receipt. After a
corrected method receives fresh source review, root must separately release any
runtime lane. Actual pixel review, a fresh blind actual-image judge, live HUD and
physical reach evaluations remain required.
