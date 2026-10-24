# R4 independent source and method verdict

**NO GO: correct product geometry before native acquisition.** This review is
bounded to source and pure counterexamples. It grants no visual, native contrast,
accessibility, physical interaction or shipped-title acceptance.

Reviewed drawing/method freeze `16335abfaf2068b2b2ea54c7e100a1505f62b5c1`,
handoff `bb1fc88850a3e41376b1717b163bc479aab378a6`, baseline
`a52022169241df9ff662039547a375e1c46ac1c5`. The handoff freeze SHA-256 is
`aa32b3a08f2682ddbbd5c5ecc811af216bf1aa42b7dd210166235806eab14906`.
All fifteen frozen files match. No engine, import, UID generation, OCR, compile,
export, CI, service, native render or product edit ran in this review.

## Blocking source geometry

At mobile-max, the exact fixture safe rectangle produces FRAG center
(569.6, 576) and SMOKE center (650.24, 576). Both bodies have radius 42 px.
Their center distance is 80.64 px, body overlap is 3.36 px, and the two 5.25 px
dark rims overlap by 8.61 px. SMOKE occurs later in `DEFAULT_POSITIONS` and is
painted after the complete FRAG component.

This cannot pass the registered complete-component footprint gate. Sixteen
native pixel centers lie at least one pixel inside both nominal body circles.
Even a fully opaque earlier FRAG contribution is attenuated to at most
`255 * (1 - .86) = 35.7` codes by the later SMOKE body. FRAG's smallest source
primitive alpha is .35, so its full opaque footprint requires at least
`255 * .35 - 2 = 87.25` codes. Later rim paint only reduces its contribution
further. These are broad interior points, not one-code AA endpoints.

The retained source-derived body-only synthetic model passes without SMOKE,
then fails the unchanged `audit_boundary` with 56 missing-footprint pixels and
56 compositing errors after SMOKE is added. Its contour witness contrast remains
13.084:1 with zero unqualified contours: this isolates why the full-footprint
predicate must remain mandatory even when a nearby witness passes. The 56 is a
synthetic model result, not a native pixel count.

The next source component must separate the two complete utility paint
footprints while keeping glyphs and font intact. The old physical targets also
need assessment; source identity is not evidence that they are correct. With equal
5.25 px rims at these centers, each rim center radius must be at most 37.695 px
before a raster margin, a reduction of at least 4.305 px from 42. A draw-only
utility plate/rim cap can do this; do not shrink or omit the glyphs. Alternatively
the centers need at least 8.61 px additional separation before a raster margin.
Changing a default center changes physical layout and requires a new explicit
geometry registration. Neither arithmetic option is a validated patch. Check
all scales and neighboring badges/controls, add a pairwise paint-clearance
counterexample, and produce a new freeze before acquisition. Drawing both
controls' rims on top would still leave the earlier complete footprint occluded.

There is a related input ownership problem in the unchanged geometry. At native
point (610.5, 575.5), the FRAG body exists and the point is inside FRAG's hit
circle, but `action_at` selects SMOKE because its normalized center distance is
smaller (.94627 versus .97388). The hit circles overlap by 24.36 px. Merely
checking each glyph or painted point against its own hit circle does not establish
which action receives input there. A new layout component should test actual
winning-action ownership across each visible affordance, including neighboring
controls. Separating complete existing hit circles would need 24.36 px additional
center spacing before a raster margin; disjoint hit circles are not an old
registered requirement, and nearest-action selection can be valid when its
painted affordances are clear. A drawing cap alone is not approval of that policy.

The maximum mobile MENU hit circle also exceeds the safe rectangle: center
(878, 50.4), hit radius 52.5, safe right edge 928, giving 2.5 px right spill and
2.1 px top spill. The unchanged `radius+8` clamp is smaller than `1.25*radius`
at this scale. This is a source-level inherited defect, not a newly observed
physical-device failure. It prevents any claim that preserving geometry proves
the full hit region stays inside the safe area.

Do not lower the footprint threshold, trim FRAG's isolated footprint, mask the
overlap, relabel FRAG paint as decoration, or accept only the contour witness.
Those changes would hide the known product loss.

## Measurement findings and limits

The instrumentation classifies every source draw call, keeps its non-color
arguments, selects whole actions in original paint order, and renders an isolated
opaque footprint independently of later controls. Normal-image equality checks
the wrapper against the original product. Complete label/icon/count and joystick
gates import the unchanged R3 pixel oracle, including inactive glyph resolution;
the inactive contrast exception does not excuse missing glyph pixels. Native
affordance accounting assigns every foreground support pixel exactly once and
rejects action-label/icon spill outside the existing hit circle. Decorative and
noninteractive count spill are reported, not qualified as truthful affordance.

The new experiment changes acceptance semantics. Forty-eight original
regular/held-border rows remain reported diagnostics but do not block R4's new
608 gated rows. That is preregistered and explicit; it does not make R3 pass or
prove its original border gate. It is reasonable to compare a final held rim to
its underlay rather than demand survival of hidden silver paint, provided no
foreground or cross-control loss is excused. Keep that distinction in any result.

Three independent synthetic counterexamples establish the exact limits:

- With `W-B=255`, changing U only inside the component to unrelated RGB 32 still
  resolves and passes. P/B/W cannot identify opaque U. Exact suppressed-source
  execution and source/background/image receipts must establish that identity.
- A two-pixel outer contour identical to U passes when a contrasting connected
  interior witness is within four pixels. The metric establishes a contrasting
  band near each contour; it does not establish contrast of the outermost dark
  surround against the world.
- With minimum component alpha .35, a 60% black replacement over an interior
  white area on black U can pass the component gate while its external contour
  remains unchanged. A single minimum alpha does not establish every primitive's
  expected interior opacity. Separate full-glyph gates remain essential, and
  the result must not be called complete-action nonocclusion.

These limitations are retained in `checks.py` and `checks.json`. The method is
usable as its declared bounded engineering test after the known source blocker
is corrected. A stronger claim about all action paint would require a per-pixel
expected-opacity reference or an independently verified equivalent, not the
component-wide minimum alpha. It cannot replace actual-image review of dark
surrounds, scene occlusion and visual-versus-hit-region truthfulness.

## Provenance and pure verification

An independent read-only audit verifies both prepared manifests, every original
game byte against its exact commit, fixture bytes, regenerated wrapper bytes,
original UID bytes, all 327 prepared paths per source, unique UIDs and absence of
`.godot`. The only game file changed between sources is the touch drawing file.
The sixteen retained R3 glyph-mask input hashes match the actual originals and
their scene receipts. Input and physical geometry before `_draw` are identical.

The native recipe correctly binds fresh shared backgrounds to failed R3 source
a520221, keeps the older 138a1 baseline separate, and requires baseline provenance
even when its contrast gate fails. Receipt controls reject source, matrix,
renderer, image, background and metadata substitutions. Metadata marker tests
explicitly stub pixel processing and do not count as native evidence. Later
acquisition must retain the actual pinned binary/archive identity, command logs,
before/after 327-path fences, renderer identity and original/wrapped equality;
a JSON claim alone does not establish execution.

The existing 46 controls pass, and fourteen independent source/pure checks pass.
Passing the independent checks means the expected negative cases were observed,
including the product blocker; it is not a product PASS. Reproduction and exact
exits are retained in `verification.json`, `builder-controls.log` and
`independent-checks.log`.

One review setup error is retained in `setup-attempts.json`. The exact-freeze
checkout lacks the handoff-only staging helper. After that command failed, the
helper was executed from the builder checkout before inspecting its body. It
rewrites deterministic report copies there; those outputs remain byte-identical
and the builder checkout is clean. The reviewer-owned subsequent audit is
read-only and writes evidence only in this review directory. No product or
prepared-project bytes changed.

Read and applied the installed AGENTS/CLAUDE instructions, original gauntlet-loop,
no-ai-slop plus eval, and sightbreak-gauntlet skills. No skill was installed and
no nested agent was used. Actual R4 captures and a fresh blind actual-image judge
remain required after a corrected source freeze and a separate root lane release.
