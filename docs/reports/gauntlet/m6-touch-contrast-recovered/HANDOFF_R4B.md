# R4B source, ownership and method handoff

SOURCE/PURE ONLY. Fresh independent review is required. No R4B engine, import,
native render, UID regeneration, OCR, live HUD, export or recording ran. This
handoff does not release the runtime lane or grant product acceptance.

Exact source/method freeze: `2ea23f947aec6085449bced53c9b061618a67029`, branch
`codex/m6-touch-contrast-recovered`. [Preregistration](R4B_PREREGISTRATION.md)
started at `0352edd`; failed-layout refinements are separate `e3487c5` and
`d813955`. [SOURCE_FREEZE-r4b.json](SOURCE_FREEZE-r4b.json) SHA-256 is
`375b2a867d9fc2991eb9cf5a3caa7e0ef04a77c3fd9311194620425b09e8af68`.
Analyzer SHA-256 is
`486f0da12fa692dbfc97649c2dfc50753002148223c12f84c3982a73af98c988`.

R3 remains FAILED at `a520221`, with immutable evidence `0f83243`. R4 freeze
`16335ab` remains NO GO under independent source verdict
`6eb990f30fe005b46a763a014ba5e9d7cbbe09db`. The exact review, 56-pixel synthetic
occlusion counterexample, wrong-action/menu-spill witnesses and method limits
are copied unchanged under [retained-r4-source-critic](retained-r4-source-critic/REVIEW.md).
Nothing is relabeled as new native evidence.

## Registered interaction correction

R4B explicitly amends input/layout preservation. Geometry uses requested HUD
scale capped by safe width/640 and height/480, with the existing .7 lower bound.
The saved setting is unchanged. An ordinary action has a minimum 31px hit radius;
larger targets and FIRE/movement retain proportional radii. The center clamp
uses the complete hit radius plus 1px. Selection compares distance divided by
the actual hit radius; exact ties use stable action identity, independently of
dictionary order. The raw normalized saved coordinate format and values remain.

On a safe rectangle below 1100px wide or 650px tall, untouched defaults respond
as FRAG x=.58, USE y=.61, JUMP y=.72 and SWAP y=.91. SMOKE stays at its original
x=.69. The initial .70 and .68 hypotheses and their actual source-derived
failures remain retained. Customized normalized values remain customized.
Utility badge offset is bounded by .66r and `(hit_radius-12.625)/sqrt(2)` so its
complete protected rim also has a target/raster allowance. Digits, font size,
words, foreground glyph paths and all input-event/persistence methods are
unchanged. Joystick drawing follows the same derived scale as its physical
geometry. Mouse/keyboard/controller mode selection and event paths are unchanged.

At 960×720 with 32px side insets, requested scale 1.5 now resolves to 1.4; at .7,
ordinary targets grow from49px to62px diameter. These are declared interaction
changes. The source proof does not establish physical reach or accessibility.
Later actual images and physical play must assess the lower SWAP position,
raised USE position, responsive size cap and any scene/aim occlusion.

## Pure checks and their limits

[Combined log](r4b-pure-freeze.log): 47 controls, exit 0. This includes the original
11 full-glyph controls, unchanged final-band falsifiers, complete native-owner
record and independent replay tests, receipt negatives, event/persistence/glyph
source equality, stable neighbor-order/tie selection, corrected inherited
counterexamples and deliberately invalid custom-layout rejection by the proof.
Metadata marker tests explicitly stub pixels/source geometry and are not native.

[Continuous geometry certificate](r4b-continuous-certificate.json): 32 declared
viewport/inset cases, requested scale .7–1.5, 2,482 interval bounds. The geometry
translator executes the actual restricted product geometry functions, preserving
Vector2 value-copy semantics. It does not run Godot. A continuous weighted-distance
minimum over conservative plate/rim, glyph/surround and badge envelopes proves
the declared source ownership/clearance bounds; it also samples the translated
actual `action_at` loop. Critical branch scales and interval-variation bounds
must be audited independently. The .75px raster envelope allowance and old native
font-mask bounds still need actual new native verification.

Cases are 960×540,960×720,1280×720,1280×800,1920×720,1920×1080,860×480 and
720×1280, each with zero, 32px side, 80/24/80/56 and 100/40/20/30 insets. Full
target safety includes movement's larger target. Arbitrary tiny safe rectangles
are not qualified. Deliberately colliding/coincident custom layouts fail this
proof; the product does not automatically repair user-created collisions. No
claim is made that every arbitrary saved custom layout is valid or reachable.

The full source proof and non-rendered circle envelopes do not establish native
pixels, complete primitive interior nonocclusion, final dark-surround contrast,
human reach, whole accessibility or shipped-title parity. Builder PASS fields
are pure check results only; the independent critic decides whether the source
and method are adequate for bounded acquisition.

## Frozen projects and native ownership hook

Both projects are at `/workspace/sightbreak-touch-contrast-fixture-recovered-r4b`.
Each has 323 exact tracked game files plus original diagnostic/fixture source and
UID bytes, 327 verified paths, unique UIDs and no `.godot`. The two changed game
files are touch_controls.gd and its unexecuted touch_test.gd regression harness.

| Source | Commit | SOURCE.json SHA-256 |
| --- | --- | --- |
| baseline | a52022169241df9ff662039547a375e1c46ac1c5 | 8769df11adb16daefd652d6694b2917cf4ecd95db59e77bccfb99cc5a651788f |
| candidate | 2ea23f947aec6085449bced53c9b061618a67029 | cb3bd854be3b546cf94ffaaaecde3864975fadbcf552a5d222fcd6825ca270f2 |

The new fixture retains the original 32 native scenes and 2,816 PNGs/source plus
sixteen fresh shared backgrounds. For every isolated whole-action footprint,
it calls actual source `action_at` at every supported native pixel center and
records all wrong/unclaimed coordinates and winners. Its cache is limited to an
unchanged layout/scale/positions tuple. Pixel counts must match the saved PNG.
The analyzer independently replays normalized-hit selection across the complete
native footprint; decoration, badge/count and formerly hidden pixels have no
ownership exception. Source/matrix/background/renderer/image fences remain.

The analyzer validates each source's actual geometry functions and declared
policy. Equality with the rejected layout is a historical diagnostic, not a new
requirement. Font metrics still match. A valid failing R3 baseline is comparable;
an invalid baseline provenance/geometry/ownership receipt blocks comparison.
The existing unexecuted touch regression now calls the real product methods
across all 96 size/inset/endpoint-midpoint cases, complete plate/badge envelope
samples, safe full targets, reversed neighbor order and exact coincident ties.

The 4.5:1 active text/count and 3:1 UI limits, all complete glyph/AA/occlusion
predicates and R4 final-band predicate are unchanged. All 48 intermediate-border
diagnostic rows and layer-overlap accounting stay retained. The band predicate
only establishes connected contrast within four pixels; it does not establish
the outermost dark surround's contrast, opaque-U identity or all interior paint
opacity. Exact suppressed-source execution/receipts and separate full-glyph and
actual-image reviews remain essential.

## Reproduction and blocked next steps

Pure checks, safe before runtime release:

```sh
PYTHONPATH=scripts python3 -m unittest -v test_touch_geometry_r4b test_touch_method_r4b
python3 scripts/test_touch_geometry_r4b.py --certificate /tmp/r4b-independent-certificate.json
```

The report staging helper writes deterministic report receipts. Inspect its body
before choosing to rerun it; an independent reviewer should prefer a read-only
audit that writes into its own review directory. Do not execute a helper from a
different checkout merely because an exact-freeze checkout lacks handoff files.

Only after a new independent source/method/geometry verdict and separate root
lane release, use a NEW immutable native root
`/workspace/sightbreak-touch-contrast-native-recovered-r4b`. Use the R4 handoff's
source-fence, pinned 4.7.2, explicit unused Xvfb, taskset 0–3, private per-producer
XDG state, original viewport/background/state matrix and cleanup requirements.
Freeze all twenty method/source hashes and all 327 paths before/after every
producer. Import/version failures are retained without repair in that attempt.
Actual engine, archive/binary/renderer/CPU selectors, commands, exits and cleanup
must be recorded freshly. No historical native number is inherited.

Run exact-source touch/input-mode regressions for both sources; candidate adds
the real-function ownership regression. Then run the frozen analyzer once:

```sh
python3 scripts/analyze_touch_contrast_r4b.py --baseline /workspace/sightbreak-touch-contrast-native-recovered-r4b/baseline --candidate /workspace/sightbreak-touch-contrast-native-recovered-r4b/candidate --backgrounds /workspace/sightbreak-touch-contrast-native-recovered-r4b/backgrounds --freeze docs/reports/gauntlet/m6-touch-contrast-recovered/SOURCE_FREEZE-r4b.json --out /workspace/sightbreak-touch-contrast-native-recovered-r4b/recomputed.json
```

Keep every failed attempt, source receipt, actual ownership witness and original
PNG in a hashed bounded archive. The per-pixel actual ownership hook adds work;
record its actual duration without inventing an estimate or hiding a timeout.
Root assigns a fresh actual-pixel critic and separate blind actual-image judge
after archive freeze. No live HUD capture, unrelated native workload or product
integration is released. Physical reach, custom-layout conflicts, CS2-host
restrictions and full accessibility remain open; no protected art is added.
