# Touch contrast source review, 2026-10-23

Verdict: REJECT native release of fixture `090892d041565af0a20fcd682357f135afd7fc97`.
The independent pure witnesses show that its oracle can accept incorrect
backgrounds, occluded glyphs and an unbound scene matrix. The draw candidate
`b4d0c1b` has no observed source-scope violation. This verdict covers the method;
no native pixels, visual winner, device result or accessibility pass exist here.

Reviewed baseline `138a1ab810a29e3c504f5811a0051a08e1ad52b9`, preregistration
`61151b5`, original gauntlet / No AI Slop instructions and evaluation, frozen
generator, analyzer, eight pure controls, capture fixture and production touch
source. Historical Oct 22 notes supply no qualifying evidence for this source.
The Luanti reference is contextual mobile-control evidence only. CS2 parity
remains blocked.

## Blocking findings

1. `audit_pixels` never checks whether the suppressed underlay agrees with its
   black/white captures on support. Replacing only that underlay at the 54 glyph
   pixels promotes a white-on-gray result from 1.544:1 to an accepted 18.724:1,
   with zero fit residual. Require quantization-bounded compositing consistency
   and an auditable exact source path for foreground-free underlays.
2. Source opacity cannot distinguish antialiasing from later occlusion. A white
   glyph followed by a 90% black layer has 1.191:1 actual full-glyph contrast;
   the oracle reconstructs 14.969:1, marks all 53 surviving support pixels as low
   coverage, and resolves the group. Fully occluded strokes disappear from the
   support entirely. Retain a pre-occlusion footprint, distinguish layer
   attenuation from raster coverage, or leave those pixels unresolved. Grouped
   labels also need proof that each expected glyph/control survives.
3. The outside-support check compares only normal and underlay. Mutating both
   black and white to RGB 180 at an uncovered pixel leaves their difference zero
   and still resolves. Require all diagnostic passes to agree outside support.
4. Scene count is the sole matrix identity check. Thirty-two invented 20×12
   scenes pass with empty geometry and a nonexistent background path. All 64
   inactive rows are unresolved, yet the aggregate passes because their entire
   rows are exempted. Require exact scene IDs, dimensions, scale/insets/state,
   exact source/fixture identity, native metadata and matching frozen background
   hashes. Inactive contrast exemptions must retain reconstruction requirements.

The analyzer also has no dark-surround versus external-background output, despite
the preregistered protected-edge inspection. Include that evidence and identify
overlap/boundary ambiguities before claiming the protected-edge gate complete.

## Source findings and retained evidence

The actual staged baseline and candidate each contain 323 original game files,
9,924,140 and 9,924,649 bytes respectively. Every staged game byte matches the
declared Git source and manifest. Both fixtures match; the 29 wrapped call sites
and generated wrapper match the frozen generator. The only product path changed
is `game/scripts/ui/touch_controls.gd`. The full source outside `_draw` is
identical; input actions, touch hit tests, positions, radii, labels, font sizes,
safe-area logic and glyph helper remain unchanged. Existing draw geometry is
retained, including the equivalent extracted knob expression. Added outline and
dark-border drawing increases visible coverage as intended.

The fixture freezes real arena/smoke pixels once and replays them with nearest
filtering. This addresses shader `TIME` drift in principle. At this freeze no
receipt binds those backgrounds to the normal/diagnostic images or verifies the
same backgrounds across sources. The smoke fixture uses the production utility,
visual-only mode and remaining lifetime 10 seconds; it is not a smoke-quality or
gameplay test.

The existing eight pure controls pass. The independent
[counterexample runner](counterexamples.py) exits 1 at the reviewed freeze:
all four invalid witnesses are accepted. Exact output is retained in
[counterexamples-090892d.json](counterexamples-090892d.json); independent staging
checks are in [staging-source-audit-090892d.json](staging-source-audit-090892d.json).

```sh
python scripts/test_touch_contrast_method.py
python /workspace/reviews/touch-contrast-recovered/docs/reports/gauntlet/m6-touch-contrast-recovered-critic/counterexamples.py --scripts /workspace/sightbreak-touch-contrast-recovered/scripts --out /tmp/touch-review.json
```

No engine, import, export, native capture, OCR or service was run. The builder
received all counterexamples and acknowledged the missing validator. Require a
dated preregistration amendment, a new exact method freeze and independent replay
before root releases its shared render lane. Actual native reconstruction and a
fresh blind visual critic must then assess readability and the heavy-plate/world
occlusion risk. The source reviewer cannot approve that visual work.
