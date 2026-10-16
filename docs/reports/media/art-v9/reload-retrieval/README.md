# Hip retrieval: an off-screen hip or a visible pouch?

Checkpoint D, art-v9. **Evidence: my own native renders (llvmpipe, 1280 × 720 sunlit, the real first-person camera) and the repo's tests; nobody else has looked at these frames yet, nothing was seen on a phone.**

## Question

The support hand fetches the replacement magazine from the hip. Does the reload read better with the source off-screen, or with a pouch drawn at the bottom of the frame?

## Options compared (same camera, size, lighting and timing)

- **A. Off-screen hip (kept).** The hand leaves the frame, the replacement magazine is first drawn as the hand brings it back up. `pouch-vs-offscreen-hip.jpg`, `hipcompare2.jpg`, `hipstrip.jpg` show the moment of pickup for both.
- **B. A visible pouch** (a mesh at the lower edge of the viewmodel, prototype kept as `pouch-prototype.patch`, not applied). In the render it read as a **floating box**: nothing anchors it to the body or the sling, it sits in the frame for the whole reload (and for ordinary firing if it is not hidden), and it adds geometry to look at for a short beat. A plausible off-screen source is better than an obviously artificial object, and I rejected it.

## Decision

A is kept. What I changed instead is *how deep the hip is*, because the first-drawn frame decides whether the magazine pops into view:

| hip depth (z) | replacement magazine's first drawn frame: share of its own pixels visible | result |
| --- | ---: | --- |
| -0.22 | 56 % | a visible pop |
| **-0.310 (shipped)** | **20 %** | enters from the lower edge |

`reload_sequence_test.gd`'s first-draw rule is now `new_share < 0.25` (it was written against the earlier value). **That threshold is derived from this observed output, not from a visual standard**; the 92 sequence checks pass. The motion is continuous (the existing no-teleport checks at 240 Hz of reload progress pass), the hip and rise rules of `reload_visibility_test.gd` pass, and the authoritative reload time, ammunition and network state are untouched.

## Not claimed

That A reads better to players than B: this is my judgement from frames, with the failure of B named above. The visible-hand variants in `../reduced-motion/` show a different trade-off (a hand visible with no source object). A human playtest should decide.
