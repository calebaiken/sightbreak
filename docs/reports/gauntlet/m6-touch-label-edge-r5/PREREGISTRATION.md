# R5 label measurement investigation

This is a source-only method proposal. The product remains byte-identical to
`108d1cdc6cf471daa7390298c234bb1c087ae865`; the existing R4B analyzer, fixture,
instrumentation, geometry, thresholds and source selection remain unchanged.
No engine, native capture, import, export, CI or retry is authorized here.
Root narrowed this work from a draw repair to measurement validity after the
fresh critic established the actual failure witnesses.

The inspected comparison is the original R4B R3 candidate under
`/workspace/sightbreak-touch-contrast-native-recovered-r4b-r3`. Preserve its FAIL.
Seven gated rows each contain one W−B pixel with channel spread 2, while measured
contrast exceeds the original threshold. Sixteen mobile scenes each contain
three JUMP label pixels inside the correct component and hit circle but outside
the nominal font rectangle. Baseline contains the same left overhang. These
facts do not establish missing glyphs, wrong ownership or poor visible contrast.

## Proposed future label measurement

Keep every original grouped label footprint pixel. Add one isolated native
foreground-label footprint per source action, selected by both the actual
`probe_action` and its original active/inactive label group. Retain all eleven
actions, original white footprint semantics, original glyph draw call and its
position, and all low-coverage pixels at the existing one-code support rule.
The new images must come from a separately frozen, independently accepted
fixture and a separately released new acquisition. Never synthesize them from
the old component masks or represent an old capture as containing them.

The proposed pure validator will require the following independently of any
nominal text rectangle:

- Every original grouped label pixel is assigned to exactly one native action
  label footprint with byte-identical RGB coverage. Missing, duplicate, extra
  and intensity-changed pixels fail.
- Every action footprint is present, nonempty, neutral RGB and the exact native
  image size. Each action belongs to its original active/inactive group.
- Every action label pixel also appears in that action's complete native
  component footprint and lies inside its original physical hit circle.
- Existing native ownership reconciliation, complete-foreground contrast,
  final-boundary measurement, image/source/UID/background fences and all other
  regression gates stay required. This prototype cannot close those gates.

This changes the proposed attribution evidence, not the 4.5:1/3:1 contrast
limits, one-code support, source geometry, physical ownership or player paint.
The existing analyzer will not import or call the proposal. No current verdict
will change. A fresh independent method critic must decide whether the new
evidence is sufficient before root considers integrating it.

## Native font metrics

Investigate the pinned Godot source at engine commit
`ed1daf0bf001b61586d9930840f2f1394092c079`. `TextServer` provides shaped glyphs,
per-glyph baseline offsets and glyph sizes; these are candidates for truthful
ink metadata. An unobserved metric rectangle is not a native receipt. Do not
assume a character advance, ascent/descent or arbitrary padding encloses every
subpixel-rendered ink pixel. Per-action native footprints provide the direct
support check; native glyph metrics may explain those pixels in a future run.

## Falsifiers and retained inputs

Before implementing the proposal, commit this registration. Copy bounded exact
old PNG and scene bytes into this report with SHA-256 and original paths. Keep
all seven unresolved gated inputs and all sixteen mobile grouped/component
label inputs. Re-run the unchanged old pixel and affordance functions against
those bytes and require their original failures to remain. Retain a compact
verbatim extract of the original result rows and metadata.

Synthetic proposal controls must reject a missing one-code pixel, a pixel
outside its source component, a pixel outside its unchanged physical hit circle,
wrong active/inactive attribution, coincident source label support, missing
action evidence, nonneutral input and malformed dimensions. A positive synthetic
case must retain a negative-bearing one-code overhang without adding nominal
rectangle padding. Source checks must prove no product or old method mutation.

CPU4 pure checks only, each command capped at 60 seconds. Record command, exit,
duration and exact source hashes. Native label support, native glyph metric
accuracy, quantization causation, visual preference, physical reach and whole
accessibility remain unqualified. The seven spread-2 cases require their own
measurement investigation; no opacity change or tolerance relaxation is part
of this proposal. The builder cannot accept its own method.
