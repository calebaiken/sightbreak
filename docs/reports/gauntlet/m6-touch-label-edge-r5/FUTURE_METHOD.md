# Native label support proposal for independent review

The current R4B R3 comparison remains FAIL. This proposal has no native output
and is not wired into any current product, fixture or analyzer.

## Observed mismatch

In all sixteen candidate mobile scenes, JUMP contributes three low-coverage
left-edge pixels that the frozen nominal font rectangle excludes. For the
mobile-min white idle case, their coordinates are `(830,524)`, `(830,525)` and
`(830,526)`, with native footprint codes 6, 44 and 4. The native label origin is
`x=831.860046386719`, so pixel centers at `830.5` fall left of `origin.x-1`.
They remain inside `component_jump` and the physical JUMP hit circle; the native
ownership receipts and independent replay agree on JUMP. Baseline shows the
same left overhang. The support exists in the image. The nominal rectangle
does not describe all of it.

The exact retained scene/image inputs and original failure rows are listed in
[retained-inputs.json](retained-inputs.json). Replaying the unchanged method
must still produce all sixteen assignment failures and seven unresolved gated
rows. Per-control label footprints do not exist in that old acquisition.

## Pinned native API evidence

[pinned-font-api.json](pinned-font-api.json) records exact URLs, SHA-256, byte
counts and method documentation retrieved from the official Godot repository at
the actual engine hash `ed1daf0bf001b61586d9930840f2f1394092c079`.

`Font.get_string_size` returns a size that accounts for kerning, advance and
subpixel positioning. A size alone does not supply a left ink-bearing origin.
`Font.get_char_size` explicitly warns that its returned font height has no
relation to glyph height and that summing characters does not measure a string.
Neither observation authorizes arbitrary padding around the old rectangle.

`TextServer.shaped_text_get_glyphs` supplies glyphs in visual order.
`font_get_glyph_offset` returns an offset from the baseline and
`font_get_glyph_size` returns glyph size for the actual font RID, size/outline
pair and glyph. These APIs could explain the observed overhang with actual
shaped glyph records. Before treating their rectangles as ink bounds, a new
native fixture must establish that it uses the same font RIDs, shaping,
fallbacks, glyph indices, font size, outline size, glyph offsets/advances,
subpixel cache choice, viewport oversampling and draw origin as the product.
The current capture contains no such per-glyph receipt. No metric result or
complete glyph rectangle is claimed here.

## Direct support evidence

The proposed new acquisition adds exactly eleven images to each scene, named
`action_label_<action>-footprint.png`. Selection follows the current actual
source action and foreground label group; it cannot select label outlines,
icons, badge paint or a whole component. A reviewable fixture patch would
preserve the existing selection for every old pass and add this branch only:

```gdscript
if probe_group.begins_with("action_label_"):
    selected = probe_group == "action_label_" + probe_action and group in ["active_label", "inactive_label"]
```

This is a proposed selector fragment, not implemented instrumentation. The
fixture must additionally record exact source draw-call identity, action,
original foreground alpha, draw origin and image hash. It must keep all old
images and prove that wrapped normal is identical to the actual product.
The same original glyph call must render each new white-on-black footprint;
no independently recreated text, font change, rectangle raster, crop, flood
fill, one-pixel omission or mask reconstruction is allowed.

The dormant [prototype.py](prototype.py) checks byte-identical coverage and
exactly-once assignment of every original grouped label pixel to the new
per-action native footprints. It separately requires nonempty complete action
evidence, neutral RGB8 images of the exact native size, membership in the
correct complete component and original physical hit circle, and independent
normalized-distance ownership with the existing lexical tie rule. The original
native ownership receipt reconciliation remains required in the future full
analyzer. These source checks alone do not authenticate native images.

The future matrix keeps the original 32 scenes per source, sources, backgrounds,
counts, held/idle cases and original 2,816 PNGs per source. Adding 352 action
label footprint PNGs makes 3,168 PNGs per source. All original one-code support,
4.5:1 text/count contrast, 3:1 icon/boundary contrast, contour witness radius,
coverage, reconstruction, source/UID/background and geometry requirements stay
in place. The old nominal-rectangle rows remain available as historical
diagnostics; a fresh method registration must explicitly identify the new
label-attribution evidence and acceptance predicate before any acquisition.

The controls reject dropped one-code pixels, changed coverage with unchanged
support, duplicate labels, inactive/active relabeling, extra support, foreign
components, physical spill, neighbor ownership, missing actions, nonneutral
images and malformed shapes. A synthetic negative-bearing one-code pixel can
pass only when every required source/component/group/ownership check agrees.
The proposal refuses to evaluate the old capture without the missing new native
action-label evidence. Synthetic cases are not images from the product.

## Separate quantization investigation

The seven original unresolved rows each have one W−B difference with RGB
channel spread 2. They continue to fail the frozen `spread > 1` predicate.
All original contrast limits and other reconstruction checks remain unchanged.
[quantization-investigation.json](quantization-investigation.json) records the
seven exact native pixel inputs and a separate necessary-condition calculation.

If a final observed 8-bit code represents an ideal value within closed
`±0.5`, an ideal neutral contribution `D` must satisfy, for every channel `c`:

```text
D in [W_c - B_c - 1, W_c - B_c + 1] intersect [0,255]
```

The common interval is the intersection of those three intervals. A spread of
2 leaves only one closed endpoint; all seven observed cases have that form.
For `[28,29,30]`, the interval is exactly `[29,29]`. This calculation deliberately
allows both tie endpoints and is only a conservative necessary condition under
the stated final-quantization model. It does not prove a feasible native blend,
common opacity, underlay relation, source RGB, intermediate framebuffer rounding,
tie behavior, absence of nonlinear effects or acceptable contrast. Even W=B
passes this necessary condition while providing no measurable ink at all.
Spread 3 and genuinely negative contribution controls reject. No output from
this function enters the old analyzer or any proposed acceptance verdict.

A defensible new neutrality predicate needs an explicit pinned-renderer error
model, actual underlay reconstruction and meaningful incompatible-color and
nonlinear negative controls. That work is open. The interval calculation alone
does not justify changing the frozen one-code threshold or rerunning capture.

Fresh independent method/source acceptance and a separate root release are
required before implementing a production fixture/analyzer revision or acquiring
new native evidence. Product draw quality, glyph metric accuracy, native method
validity, visual preference, physical accessibility and release gates remain
unqualified by this report.
