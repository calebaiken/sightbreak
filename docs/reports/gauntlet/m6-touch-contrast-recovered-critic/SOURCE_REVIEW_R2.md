# Touch contrast R2 source review, 2026-10-23

Verdict: REJECT native release of immutable method
`3c954d33546d70bf59cf6f9b6846f1cb82b6bca3`, receipt `b9923fd`.
The pixel reconstruction corrections pass the independent challenges below.
Three receipt checks still permit an invalid comparison to succeed.

## Remaining blockers

1. The background receipt's `source` and `source_manifest_sha256` are never
   compared with the frozen fixture. Substituting unrelated source identities
   and updating the controls receipt to reference that background receipt still
   produces an error-free pass with all 304 rows.
2. Both receipts need a nonempty renderer, but they can name different renderers.
   A background rendered by `OTHER RENDERER` passes against the controls renderer.
   Bind the shared backgrounds and both sources to the same renderer identity.
3. The CLI success predicate uses the candidate's pass and geometry equality,
   while ignoring baseline receipt errors. With a baseline source-validation
   error, a valid candidate, equal geometry and the correct analyzer freeze, it
   still returns exit 0. Baseline contrast can fail; baseline identity and
   reconstruction errors must block comparative acceptance.

These are narrow validation gaps. The new source fences record the fields needed
to close them. No product redraw change is requested by this review.

## Checks that passed

The fourteen frozen builder controls pass. I replayed the original four witnesses
unchanged, then replayed the pixel attacks while supplying a genuine complete
opaque footprint. The latter avoids a vacuous rejection from the newly mandatory
footprint input. Changed supported underlays, diagnostics changed outside support
and post-glyph occlusion all reject. A completely removed disconnected stroke
also rejects. Valid disconnected white glyphs and a valid 24% opacity foreground
resolve, so the pixel method retains positive controls.

A separate pure metadata fixture exercises the real receipt validator with pixel
decoding and contrast auditing stubbed. Its files are marker bytes, not native
PNGs. The positive control passes all 304 rows. Mutations to the controls source,
renderer presence, scale, scene completeness, isolated-footprint image, frozen
background bytes, and inactive reconstruction status each reject. Only the two
background identity mutations above pass. A separate stub isolates the CLI's
invalid-baseline success predicate.

All seven frozen file hashes match Git `3c954d3`. Both staged projects' original
323-file source trees, fixtures, wrappers, instrumentation receipts and UIDs
match their exact source receipts. The wrappers now cover all 34 baseline and
39 candidate draw sites, including the outline as suppressed backdrop. Original
product bytes remain unchanged from draw candidate `b4d0c1b`; the prior non-draw,
input and geometry findings remain valid.

Evidence is retained in [independent-checks-r2.json](independent-checks-r2.json),
[checks_r2.py](checks_r2.py), [pure-method-r2.log](pure-method-r2.log) and
[staging-source-audit-r2.json](staging-source-audit-r2.json). The independent
runner exits 1 at this freeze because the three remaining invalid witnesses are
accepted. It uses an ignored snapshot copied from exact Git bytes, so later
builder edits cannot change this result.

No engine/import/export/native capture/OCR/service ran. Dark surround against
external backgrounds remains explicitly unresolved for actual native review.
Heavy-plate world occlusion still needs a fresh blind visual critic. The R1
rejection and raw witnesses remain retained.
