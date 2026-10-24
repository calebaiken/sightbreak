# Fixed blind packet selection

Selection is recorded during candidate capture, before root or the blind judge
inspects new image pixels or numeric outcomes. The judge's evaluation criteria
and shipped-reference observations were already committed before capture.

Use all 32 fixed case directories from each producer: four layout/scale modes,
four shared backgrounds, idle and held. Select exactly each case's `normal.png`.
Require the two case sets and image dimensions to match. Preserve all other
original images for numeric, diagnostic and interaction review; they do not
replace normal screenshots in this visual comparison.

Copy original image bytes into a separate packet, with neutral scene numbers
and randomized A/B labels independently per pair. Root generated a seed without
viewing pixels and retains it separately. The judge receives scene dimensions,
layout, scale, background and state, without source IDs, source filenames,
prior judgments or the mapping. Keep source hashes and mapping in a separate
record until the judge commits its observations. Do not crop, resize, enhance,
generate, recolor or otherwise edit the screenshots. Inspect for visible source
identity before calling the packet blind; if labels reveal identity, disclose
the limitation instead of claiming blinding.

The judge must inspect actual matched originals and identify A/B/tie, observable
reasons and largest remaining deficiency, with invalid comparisons called out.
Preference cannot override numeric contrast, native ownership, source integrity,
regressions or cleanup. Static fixture images do not qualify live/custom HUD,
physical touch reach, navigation, input latency or CS2 presentation parity.
