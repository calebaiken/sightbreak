# R4B R2 independent source and method verdict

**ACCEPT the method-only correction for source readiness.** The rejected
baseline ownership receipt path now rejects contradictory evidence while
retaining a genuinely failing baseline as comparable. This verdict releases no
native lane and grants no rendered, physical, accessibility or shipped-quality
acceptance.

Reviewed exact method freeze `b001fc5087960729535f63c896b40d6dc25bd272`,
handoff `548e3569fe9228740c5bb82cae4331bdd60128ae`, preregistration `1cad5ca`.
Freeze receipt SHA-256 is
`f9d292d7cb04fc129eee7df84fdc1c0591ae14600497bcf63aac0243cd7f2563`.
Analyzer SHA-256 is
`c47bb2fd7a3b8eab83765fd75ee76885815fc5ae467ffac6b99859e72be05141`.
The earlier independent rejection `ce3510e3776c8fec42ef1de648b14a453c221724`
remains valid for its rejected freeze `2ea23f9`. R3 FAIL and R4 NO GO remain
unchanged.

## Receipt correction

`audit_ownership` now constructs the independently replayed wrong-owner map
from every supported component pixel. It validates native sample coordinates,
winning identities and support/wrong/unclaimed counts, then compares the
complete native mapping with replay. Missing, extra and differing winners are
retained separately. Duplicate coordinates invalidate the receipt even when
they repeat the same winner. Witness array order has no effect.

Contradictions now enter `errors`, so the existing `audit_source` provenance
gate and final comparison reject them for either source. The product gate
separately requires zero actual wrong-owner pixels. An agreeing native/replay
record with wrong-owner or unclaimed pixels therefore keeps valid provenance,
fails product quality and remains usable as a baseline.

I executed the two original critic falsifier blocks unchanged, byte-bound to
commit `ce3510e`, against the rejected and corrected methods. The old method
still falsely accepts the zero-wrong-owner baseline receipt. The new method
rejects it, reports its missing native witness, and reports the forged `pause`
winner where replay selects JUMP. The original rejection, expressions and
historical findings are retained rather than relabeled as passing this freeze.

The reviewer-built synthetic sample map includes correctly owned, wrong-owner
and unclaimed pixels at the one-code support threshold. Twenty-eight mutation
types reject under both `r3` and `r4b`: false zero, missing/extra coordinates,
same/different duplicate witnesses, forged/swapped identities, incorrect
unclaimed classifications, invalid identities, unsupported/out-of-bounds or
noninteger coordinates, malformed samples/lists/records and invalid counts.
Equal totals and matching coordinate sets do not conceal wrong winners.

All 56 mutation cases pass through the complete 32-scene `audit_source`
provenance wiring and final CLI in both baseline and candidate roles. Exact tie
controls distinguish R3 dictionary-order ownership from R4B stable action-ID
ownership. Genuine agreeing product failures retain valid provenance for both
variants; they compare successfully only in the baseline role. The 54 supplied
pure controls also pass in 11.807 seconds.

The full comparison controls use explicitly synthetic sample arrays and the
inspected marker-metadata helper. PNG decoding, source geometry,
contrast/affordance and source-audit ownership injection are isolated stubs;
the ownership validator itself runs on the explicit sample maps before
injection. These controls establish reconciliation and propagation, not native
pixels or actual engine execution. Eight independent review groups and their
complete mutation/CLI results are retained in `checks.json`.

## Exact scope and remaining gap

All 22 frozen files match the exact method commit. Both new prepared projects
match their original game bytes, regenerated diagnostics and fixture bytes:
323 original game paths, 327 verified source/UID paths each, 138 unique UIDs
each and no `.godot`. Baseline manifest SHA-256 remains
`8769df11adb16daefd652d6694b2917cf4ecd95db59e77bccfb99cc5a651788f`;
candidate is
`a423eb35530201a0b6090a146a8211c802ea80c99c328d5879d391e28ea03780`.

Across `game` and `scripts`, the only changes since the rejected R4B source are
`audit_ownership` and the added pure test file. Removing that function from both
analyzer ASTs leaves identical programs. The complete game tree hash is
unchanged. Product geometry, native regression and capture fixture, ownership
sampling, source/UID/background fences, 4.5:1 and 3:1 limits, complete glyph/AA/
occlusion predicates and final-band semantics are unchanged.

The prior 32-case / 2,482-interval geometry certificate remains source support
under its original limits. This review does not add geometry or native evidence.
The three retained final-band falsifiers remain applicable: opaque P/B/W cannot
identify U, an inward contrasting band can approve an invisible outer contour,
and component minimum alpha cannot certify every interior primitive's survival.
Custom collisions are not repaired or qualified. Native Vector2/raster rounding,
font support, dynamic joystick origin/states, editing, reach and scene occlusion
remain unqualified.

The biggest remaining gap is actual frozen native output. It must establish
that the per-pixel native ownership map agrees with replay, that complete glyph
and component gates pass, and that original/wrapped images and all source/
background/image receipts hold. Preserve any native/replay mismatch as failure.
Root must separately release that lane. Fresh actual-pixel and blind actual-image
critics, live HUD and physical evaluations remain required afterward.

Read and applied the existing AGENTS/CLAUDE instructions and the already-read
gauntlet-loop, sightbreak-gauntlet and no-ai-slop/eval skills. No engine, import,
UID regeneration, OCR, native render, engine compile, CI, services or nested
agents ran. Only this review directory changed.

Source/pure reproduction:

```sh
PYTHONPATH=scripts python3 -m unittest -v test_touch_geometry_r4b test_touch_method_r4b test_touch_receipts_r4b_r2
python3 docs/reports/gauntlet/m6-touch-contrast-recovered/fresh-source-critic-r4b-r2/checks.py
```
