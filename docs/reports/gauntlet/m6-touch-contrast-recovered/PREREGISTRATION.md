# M6 touch contrast reconstruction, 2026-10-23

Status: PREREGISTERED; no native run or acceptance result.

## Source and bar

Baseline is exact published integration `138a1ab810a29e3c504f5811a0051a08e1ad52b9`.
Own sparse checkout `/workspace/sightbreak-touch-contrast-recovered`, branch
`codex/m6-touch-contrast-recovered`. The Oct 22 unpublished implementation and raw
captures were not found. Historical notes supply hypotheses only; their scores,
acceptance and images do not qualify this reconstruction.

Fetchable bar B3 is this actual baseline rendered by the same frozen fixture.
B4 is WCAG 2.2: active text 4.5:1, meaningful active UI components 3:1, measured
from native pixels. B1 shipped CS2 media remains blocked by the documented host
policy. This work can prove bounded engineering improvement only. No protected
assets or third-party media are introduced.

## Product boundary and hypotheses

Only `game/scripts/ui/touch_controls.gd` may change in the product. Changes stay
inside `_draw`: strengthen button plates and protected borders, draw black text
outlines at width 3, make depleted count text readable, protect joystick ring and
knob with dark underlays. Preserve every input function, action, position, radius,
label, glyph path, hit test, safe-area policy and font size. Depleted action labels
and icons retain the existing inactive exception and visual distinction; their
measurements are reported separately. The 0 count remains useful information.

## Frozen native fixture

Before engine use, commit the same minimal fixture generator, capture script,
analysis script and source receipt; have a separate critic audit the method.
Prepare two minimal projects from exact Git bytes. Retain exact tracked game code/assets and UIDs (about 10 MiB), including
typed transitive dependencies of the original utility smoke implementation,
then add the same fixture sources/UIDs. Record every path/hash and source commit. Instrumented
versions are test-only: mechanically wrap draw calls and record original line,
classification and emitted bytes. A normal pass must execute the same source
calls with original arguments. No candidate-specific shader, font or backdrop.

Matrix per source: 4 layouts × 4 backgrounds × 2 states = 32 normal captures.
Layouts are 960×720 scale .7 and 1.5 with simulated left/right 32-pixel insets,
and 1280×720 scale .7 and 1.5 without insets. These cover mobile/tablet and desktop
clamp boundaries; physical phones and GPUs remain unverified. Backgrounds are
opaque white, sRGB .5 gray, fixed-camera actual Relay Yard, and the same rendered
yard with actual utility smoke. First capture native backgrounds once per layout,
freeze them as PNGs, and replay those exact pixels for every diagnostic and both
sources. Shader TIME therefore cannot drift between a foreground and underlay.
Record camera, smoke age, native renderer/version, source and PNG hashes.

States are idle and simultaneous held actions/movement (fire, reload, interact,
and joystick vector (.65,.45)); grenade count 0 and smoke count 1 in both.
Capture all normal images at native size. Do not crop away overlaps or failures.

## Pixel oracle

For each scene, capture foreground groups separately: action text, icons, counts,
action borders, joystick ring and joystick knob. For each group render an exact
foreground-free underlay plus black and white diagnostic foreground versions;
all other calls/arguments remain byte-identical. Black/white diagnostics preserve the original primitive alpha. Their difference
recovers effective raster coverage at every pixel, including disconnected
letters and thin strokes, with only the 8-bit quantization floor (difference >= 1
code value). Opaque diagnostic overrides would hide original translucency.
No high-luminance threshold, flood fill, inferred text rectangle or chosen glyph
subset may stand in for complete coverage. Keep original and diagnostic PNGs.

Fit each original pixel to its exact underlay and diagnostic coverage. Report
reconstructed full-coverage foreground contrast over every covered pixel,
conservative quantization bounds, observed high-coverage contrast, full glyph
pixel counts, residual error and coverage failures. Low-coverage antialiasing
pixels are reported separately; they cannot be required to reach 4.5:1 because
coverage tends to zero. Any ill-conditioned pixel remains unresolved and blocks
an unqualified full-glyph claim. Audit foreground-free underlays against source,
and verify diagnostic passes change no pixel outside their coverage support.
No source-color calculation alone closes the native contrast gate.

Active labels/counts must each reach 4.5:1; active icon/ring/knob protection must
reach 3:1. For protected edges, inspect the complete light foreground footprint
against the exact retained dark underlay and the dark surround against its
external background; name any local boundary ambiguity. No averages or percentiles
may hide a failing control. Report depleted exceptions and editor text separately.

## Acceptance and stopping rules

Require: exact non-draw source equality; geometry arguments preserved; paired
native layout metadata equality; existing touch/input-mode suites; complete raw
matrix; strict pixel gate or explicitly unresolved scope; fresh blind critic
choosing candidate with no correctness/accessibility regression. Root assigns a
fresh critic. The builder cannot accept its own work. Keep every failed attempt
and counterexample, and change criteria only in a dated amendment before rerun.
After focused native proof, run the original live HUD touch-toggle capture and
appropriate broader validation on the integrated source when the root releases
the single shared CPU/render lane. No engine/import/export/record/OCR/native
execution is permitted before that release. Source/pure checks may proceed.

No full accessibility/presentation gate, device performance, shipped-title parity,
real touch ergonomics or entire player journey is claimed by this fixture.

## Source-method clarification, before native execution

The frozen fixture splits foregrounds into ten same-color groups: active and
inactive labels/icons, empty and ready counts, regular and held action borders,
joystick ring and knob. The complete support mask is `max(white-black) >= 1`.
Every supported pixel participates in the affine identity `P = B + C*(W-B)`,
where P is the normal native output and B/W are native diagnostic captures.
Recover shared RGB C by least squares and intersect conservative per-pixel
quantization intervals; reject residuals above two code values, nonneutral
coverage, an empty color interval or changed pixels outside support.

Only the minimum primitive alpha is taken from the recorded draw calls. Native
RGB and the exact suppressed-foreground underlay determine contrast at every
support pixel, including low-alpha edges. Applying the minimum primitive opacity
to inferred native RGB is conservative for overlapping same-color strokes.
Strong-coverage observed contrast is reported separately. Inactive label/icon
rows are exceptions; unresolved diagnostic reconstruction is never a pass.
Border portions overlapped by another component may produce a strict failure;
retain that result for the independent critic instead of dropping those pixels.

Pure method controls must catch a single bright underlay under a disconnected,
low-coverage glyph pixel, changed backgrounds, nonconstant colors and the false
assumption that a .24-opacity foreground is opaque. Source controls prove the
entire file outside `_draw` and every original non-color draw argument remain
unchanged (the knob variable is normalized to its unchanged position expression).
The minimal source projects are ~10 MiB each; diagnostics are bounded at 32 scenes
per source, 64 ordinary and wrapped-normal PNGs plus 912 diagnostic PNGs each.
Raw output and any native failure stay outside the source checkout until archived
with path/hash/size receipts; no raw files are deleted to conceal failed rounds.

## R2 amendment, before any native run

The fresh critic retained four pure false-pass witnesses against first freeze
`090892d`: changed supported underlay, changed diagnostics outside support,
post-glyph occlusion mistaken for antialiasing, and fabricated tiny scene rows
with unresolved inactive groups. R1 is rejected for native qualification. Its
source projects, receipts and original pure results remain retained.

R2 adds an isolated opaque native footprint for each named group, using the
same primitives and geometry. Every other draw color, including text outlines,
becomes transparent for that pass, and the frozen background is modulated black.
Retain these PNGs. Their complete >=1-code footprint supplies the audit mask;
effective B/W coverage must remain at least minimum source alpha × isolated
coverage, allowing two code values for quantization. Missing or attenuated
strokes fail. At every footprint pixel require B≈U×(1-(W-B)/255), within two code
values. Source layers after a tested foreground may fail this check; that result
stays unresolved instead of being described as harmless antialiasing. Diagnostic
P/B/W changes outside the complete isolated footprint also fail.

Require the exact 32 scene IDs, native dimensions, scale, inset, held state,
counts, movement, actions and all 12 named component geometries. Native capture
receipts bind every image hash, the complete shared 16-image background set and
its native receipt, pinned engine/renderer identity, and the exact prepared
source manifest. The fixture checks all original sources, fixture sources and
UID hashes before and after capture. The analyzer requires the frozen source
receipt and rejects changed/missing image or source/background identities.
Inactive contrast exceptions remain, but every inactive reconstruction must
resolve. R2 retains 1,280 PNGs per source (64 ordinary/wrapped normals and 1,216
underlay/black/white/isolated-footprint diagnostics), plus 16 shared backgrounds.

The dark surround versus external background still requires an independent
review of the native output. The analyzer names that scope UNRESOLVED; a numeric
light-foreground-versus-retained-underlay pass cannot close that boundary scope.
The fresh critic must review R2 source/method before the root releases native
execution. No engine, import, export, OCR or render has run in either round.

## R3 amendment, before any native run

The R2 independent reviewer rejected three remaining receipt gates: unrelated
background source/manifest, different background renderer, and CLI success with
an invalid baseline source receipt. The exact independent reproducer and its
R2 rejection output are retained under `retained-r2-critic/`; they remain pure
metadata/pixel controls and are not native image evidence.

R3 binds the one shared background capture to the frozen baseline fixture's
source and manifest hash, for both baseline and candidate audits. Controls must
match the background's complete native engine dictionary and renderer string.
Existing pinned-version, source/UID, image, background, exact matrix and geometry
checks remain. CLI comparison succeeds only when both baseline and candidate
provenance errors are empty, candidate numeric gates pass, geometry matches and
the analyzer matches its freeze. A baseline's legitimate contrast failure does
not block comparison when its provenance remains valid. No product drawing,
native fixture generator or capture script changes for R3.

The unchanged independent R2 reproducer now reports `independent_checks_pass=true`;
all sixteen builder controls pass, including invalid-baseline rejection and a
valid low-contrast baseline positive control. R3 source/method still requires
independent re-review and root render-lane release. Native calls remain zero;
dark-surround/external-background inspection and blind visual judgment are open.
