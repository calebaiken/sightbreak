# Touch contrast R3 source review, 2026-10-23

Verdict: APPROVE SOURCE/METHOD FOR BOUNDED NATIVE EVIDENCE ACQUISITION at
`a52022169241df9ff662039547a375e1c46ac1c5`, frozen receipt `f527e01`.
Root can release the preregistered fixture on its shared lane. This approves
source and method only. No contrast result, visual winner, external-surround
gate, live HUD result or release-candidate acceptance is established.

The R3 analyzer SHA-256 independently matches
`2501fc714ca07d77aa883689d3003f06ae40db6210eba08f1002f33a1afda4ab`.
I reviewed the narrow R2-to-R3 diff, the amended preregistration, exact prepared
projects and frozen sources. R1 and R2 failures remain retained in this report
branch and the builder's branch.

The sixteen builder controls pass from a private snapshot copied from exact Git
bytes. The unchanged independent R2 reproducer also passes. Its original pixel
attacks receive valid isolated footprints, so rejection does not depend on a
missing-input error. Changed underlays, changed diagnostic pixels, later glyph
occlusion and a fully lost disconnected stroke reject. Valid disconnected
glyphs and a 24% opacity foreground resolve. The source still audits the entire
isolated footprint, including disconnected components and pixels where the
normal black/white difference has vanished, with the declared quantization
tolerance. No luminance threshold or chosen subset replaces that support.

The metadata positive control passes all 304 rows. Wrong source, missing
renderer, altered scale, missing scene, changed footprint image, changed frozen
background, and unresolved inactive reconstruction reject. R3 also rejects the
previously accepted unrelated background source/manifest and differing
background renderer. The CLI rejects invalid baseline provenance. Additional
independent predicate controls verify that a valid low-contrast baseline remains
comparable, while candidate failure, either source's provenance errors, geometry
mismatch or analyzer-freeze mismatch block success.

Every one of the original 323 files in each staged project matches its declared
Git source and receipt. Fixture sources, the 34 baseline / 39 candidate wrapped
draw sites, generated source and UIDs match. All seven frozen hashes verify.
The product, generator, native capture script and UIDs are byte-identical to
R2. The product remains the reviewed draw-only `b4d0c1b` candidate; input,
geometry, labels, font sizes, action logic and safe-area behavior retain their
earlier source findings.

Native qualification must retain the shared baseline-rendered backgrounds,
complete normal/original/diagnostic/footprint images, source fences and failed
rows. Active labels/counts require 4.5:1; active icons, borders and joystick
components require 3:1. Inactive contrast exemptions retain reconstruction
requirements. A false baseline numeric subtotal does not itself prove a measured
contrast failure: the actual-output reviewer must inspect any unresolved rows
and preserve that scope. No missing, ill-conditioned or overlapping component may
gain an unqualified contrast claim from the CLI's comparison result.

Dark surround against external background remains explicitly unresolved in the
analyzer. Actual rendered overlaps, heavy plates and world occlusion require
independent native inspection and a fresh blind judge. Existing touch/input-mode
suites, original live touch-toggle capture and appropriate broader validation
remain subsequent gates. Historical Oct 22 output and contextual Luanti media
qualify none of these new results; CS2 comparison remains blocked.

Evidence: [unchanged independent replay](independent-checks-r3.json),
[sixteen-test log](pure-method-r3.log),
[comparison controls](comparison-controls-r3.json), and
[staging/source audit](staging-source-audit-r3.json).
No engine, import, export, native render, OCR or service was run in this review.
