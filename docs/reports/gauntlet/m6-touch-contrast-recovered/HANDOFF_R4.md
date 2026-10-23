# R4 source and method handoff

Status: SOURCE/PURE ONLY, review pending. No R4 engine, import, generated UID,
native render, OCR, live HUD, export or recording ran. Root currently owns the
native lane for other work. A fresh independent source/method verdict and a
separate explicit root release are required before R4 acquisition. The builder
does not grant acceptance.

Exact source/method freeze: `16335abfaf2068b2b2ea54c7e100a1505f62b5c1` on
`codex/m6-touch-contrast-recovered`. Initial preregistration `d583359`; product
savepoint `4153d91`; [final preregistration](R4_PREREGISTRATION.md).
[SOURCE_FREEZE-r4.json](SOURCE_FREEZE-r4.json) SHA-256:
`aa32b3a08f2682ddbbd5c5ecc811af216bf1aa42b7dd210166235806eab14906`.
Analyzer SHA-256:
`ebb98982433348a146c4ae724770ffe5e7d93db56c4c3d249991d37c4fd54095`.

The primary comparison is a fresh rendering of the actual failed R3 product
source `a52022169241df9ff662039547a375e1c46ac1c5`, compared with R4 source above.
R3 remains FAILED, with its full immutable archive/evidence at `0f83243` and
independent actual verdict `39b5a9d` / `8a5f531`. Its original published
`138a1ab` baseline and measured numbers remain separate. A blind R3 preference
does not qualify any R4 result. No native number is inherited.

## Product changes and explicit risks

All source before `_draw` is byte-identical to R3: physical radius, centers,
hit selection, input, safe-area policy and layout persistence/edit behavior are
unchanged. Label words, font 12 and original foreground glyph paths/widths are
preserved. Badge background/rims precede glyphs, count digits stay on top, and
the same glyph paths receive one wider black surround pass. Compact non-FIRE
icons/labels move from -8/+17 to -13/+6 pixels. Compact body radius is capped at
the existing physical hit radius; its decorative rim spacing is separately
registered. The maximum-clamp body sizes and stack positions stay unchanged.

The small ordinary body is inside the existing 24.5px hit circle, while its light
rim, held rim and dark halo extend 1.625/2/2.75px beyond that circle. Utility
badges are noninteractive decoration that already protruded; their new protected
rim adds footprint. These differences must be inspected for truthful affordance.
Analytical minimum-clamp extra body fill is at most 6,789px², below 1% of 960×720;
this is source arithmetic, not an actual scene-occlusion verdict.

The maximum mobile cluster is a required risk case. Its unchanged grenade/smoke
centers are nominally 80.64px apart, whereas both original bodies have radius
42px: nominal body overlap is 3.36px, dark-halo overlap 8.61px. The new full
component accounting may retain real cross-control occlusion failures there.
No pixel is excluded to avoid this result. Minimum clamp, maximum mobile cluster,
held controls and white/gray/arena/smoke remain mandatory actual comparisons.

## Pure and source checks

[Combined retained log](r4-pure-freeze.log): 46 controls, exit 0. They cover all
11 unchanged R3 full-glyph pixel controls; source/input and foreground-path
identity; original native-mask translation; bright/dark/busy final contours;
one failing contour section; disconnected/distant witness rejection; later
occlusion; one-code AA; quantization; source/background/renderer/matrix/PNG
receipts; unresolved inactive/component rows; hidden-stroke accounting; and
complete glyph/unchanged-hit-region accounting. Metadata controls explicitly
stub decoding/pixels with marker bytes and are not native evidence.

All failed attempts remain: initial compact RELOAD rim collision, an overstrong
opaque-underlay test assertion, an interrupted metadata-only run (SIGINT/130),
and the staging helper's initial wrong Python import root. Their corrections are
recorded before native. At opaque D=255, P/B/W alone cannot establish U; exact
source-bound suppression and native source/background/image receipts are
essential. The fresh critic must assess that limitation explicitly.

Prepared projects are source-only:

| Name | Exact source | SOURCE.json SHA-256 |
| --- | --- | --- |
| baseline | a52022169241df9ff662039547a375e1c46ac1c5 | 6c0e396142c5cf13a33500f6e3cb6ffd062781cd5b1fc81e94dcbb1d9fa02e03 |
| candidate | 16335abfaf2068b2b2ea54c7e100a1505f62b5c1 | ff86d326823a713e7a2c995b5ed165400aeae8971f0cda1fbf51f365f8fc6f07 |

Both are at `/workspace/sightbreak-touch-contrast-fixture-recovered-r4/`.
[Pure staging audit](r4-staging-audit.json) verifies all 323 original tracked game
paths plus exact diagnostic/fixture source and original UID bytes: 327 paths per
project, no UID duplicates and no `.godot`. Only the product touch drawing file
differs between the two game trees. The fifteen frozen source/method files match
the exact freeze commit. No automatic engine import or UID regeneration is used.

Pure replay, safe before native release:

```sh
PYTHONPATH=scripts python3 -m unittest -v test_touch_contrast_r4 test_touch_contrast_r4_method test_touch_contrast_r4_receipts
python3 docs/reports/gauntlet/m6-touch-contrast-recovered/audit_r4_staging.py
```

## New final-boundary experiment

The original R3 analyzer stays unchanged and is imported for all complete label,
icon, count and joystick diagnostics. All 304 original group rows remain, with
their original 4.5/3 limits and every glyph footprint/occlusion predicate. The 48
regular/held intermediate-border rows retain their failures, coverage and exact
spatial intersections with isolated glyph/surround/badge/held-fill footprints;
unattributed loss is retained. Their role is explicitly a retained diagnostic in
this NEW experiment, not R3 acceptance or a retroactive pixel exclusion.

Each of eleven complete action components gains native suppressed U, black B,
white W and isolated opaque footprint F. All eight-neighbor contours, including
holes, need an inward Bresenham path within F to a witness at most four native
pixels away. The witness requires `min(W-B)>=206`, leaving contribution >=0.8
after the original two-code quantization allowance, and conservative observed
P/U contrast >=3. Every contour failure, best-witness minimum, exact values and
unresolved/occluded footprint remains reported. This is a bounded final-edge
engineering predicate, not an accessibility certificate.

Expected acquisition is 2,816 PNGs/source plus sixteen new shared backgrounds:
original and wrapped normals, 304×4 original group diagnostics, 352×4 whole-action
diagnostics, and 128 layer-only isolated footprints. Candidate numerical gating
uses 608 rows plus complete glyph/target accounting. Both sources must have
valid comparable provenance; a valid low-contrast baseline may fail its product
gate, but invalid baseline source/matrix/background/renderer identity blocks
comparison. Font metrics and all physical geometry must match across sources.
Actual dark surrounds against the world, heavy plates, visual-versus-hit-region
truthfulness and scene occlusion still require independent actual-image review.

## Acquisition recipe, blocked and unexecuted

Only after fresh independent review and root release, start a NEW immutable raw
directory `/workspace/sightbreak-touch-contrast-native-recovered-r4`. Record
release, UTC start/end, actual pinned 4.7.2 binary/archive identity, engine version,
renderer/logs, CPU/cgroup selectors, every command/exit/source fence and cleanup.
Use an explicit verified-unused Xvfb display (proposed `:132`, never assume free),
`taskset -c 0,1,2,3`, LP_NUM_THREADS=2 / OMP_NUM_THREADS=2 and separate private XDG
state for each producer. Use the R3 controller's bounded source-fence, timeout,
process ownership and cleanup pattern, adapted and retained as a NEW controller.
Recheck every frozen file and all 327 paths before and after each producer.

Required producers, in order, with original native sizes and the fixture's
32 scenes (960×720 inset32 / 1280×720 inset0; .7/1.5 scale; idle/held):

1. Exact engine version, then import both isolated projects once. Retain any
   parse/import failure; do not repair source in that run.
2. Baseline fixture `--mode=backgrounds`; freeze all sixteen resulting PNGs and
   its native receipt before controls. Both controls producers use those exact
   files with the same engine/renderer. Fresh backgrounds bind R3 source a520,
   not the earlier 138a1 source.
3. Baseline then candidate fixture `--mode=controls`, using X11, GL compatibility,
   Dummy audio, 1280×720 outer window and max-fps60; fixture controls its original
   pixel viewports. Require original/wrapped normal equality.
4. Both exact sources' `touch_test.gd` and `input_mode_test.gd` regressions,
   private state, pinned engine and source fences. Simulated input-mode coverage
   must not be presented as physical mobile interaction.
5. Run the frozen analyzer below once; preserve nonzero exit and every failed
   row. No product/method editing or threshold adjustment mid-run.

```sh
python3 scripts/analyze_touch_contrast_r4.py --baseline /workspace/sightbreak-touch-contrast-native-recovered-r4/baseline --candidate /workspace/sightbreak-touch-contrast-native-recovered-r4/candidate --backgrounds /workspace/sightbreak-touch-contrast-native-recovered-r4/backgrounds --freeze docs/reports/gauntlet/m6-touch-contrast-recovered/SOURCE_FREEZE-r4.json --out /workspace/sightbreak-touch-contrast-native-recovered-r4/recomputed.json
```

Keep all actual originals, diagnostic PNGs, logs, receipts and failed attempts in
a hashed bounded archive with source identity and cleanup. Root assigns a fresh
read-only actual-pixel critic and separate fork-none blind visual judge after
archive freeze, keeping the random mapping outside the judge's packet. Builder
output and an analyzer exit are evidence inputs, never acceptance. No live HUD
export/capture or unrelated native/OCR work is released here.

Official contextual Luanti references and shipped CS2 host restrictions remain
explicit. No third-party art is added. Shipped-title parity, physical ergonomics,
complete accessibility and the live HUD toggle remain unqualified.
