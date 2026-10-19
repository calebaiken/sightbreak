# Reduced motion: separate controls, three variants, and an evaluation

Checkpoint D of the art-v9 round. **Evidence: my own native renders and tests on Mesa llvmpipe (Xvfb), 1280 × 720 sunlit, 60 Hz. No human has watched these clips, nothing was tried on a phone, and I make no claim about comfort or motion sickness: that needs people.** Presentation only: the reload's duration, the ammunition, the sounds and the authoritative state are identical in every variant.

## What was controlled before, and what is now

Before this checkpoint, reduced motion scaled one thing (the weapon's roll and lift together) and the recoil, so the hand left the frame at the hip and the replacement magazine was drawn with a few hundred pixels of arm (the old `current` row below: smallest magazine 176 px). `Actor.REDUCED_RELOAD_VARIANTS` now holds per-variant profiles with **separate** controls: weapon `roll`, `lift` (translation), `recoil` (muzzle kick presentation) and the support hand's `clip` (`reload` or `reload_calm`, which has a shallower reach to the pouch: 14 cm down against 22, so the hand and forearm stay in the frame at the pickup). Camera shake is not used by the reload at all (nothing to scale). The magazine path follows the hand, and the hand's own motion is the clip.

| variant | roll | lift | recoil | clip | notes |
| --- | ---: | ---: | ---: | --- | --- |
| `current` | 1.0 | 1.0 | 1.0 | `reload` | what reduced motion did before |
| `calm` | 0.4 | 1.3 | 0.6 | `reload_calm` | recommended candidate |
| `still` | 0.0 | 1.8 | 0.4 | `reload_calm` | no roll at all; the weapon is raised instead, so the barrel is high in the frame |

The shipped default is unchanged: `reduced_variant = "current"`. I did not change the global accessibility policy or what the reduced-motion setting does for anyone; `calm` is a recommendation for a human to try.

## Measured (`logs/visibility-*.csv`, `reload_visibility_test.gd`: 15 rules, 51 progress steps)

| | default | reduced `current` | `calm` | `still` |
| --- | ---: | ---: | ---: | ---: |
| all 15 visibility rules | pass | pass | pass | pass |
| least support-hand pixels in any frame | 598 | 598 | 3,829 | 2,063 |
| least replacement-magazine pixels | 2,741 | 176 | 162 | 509 |
| least thumb pixels while holding a magazine | 0 | 0 | 300 | 275 |
| rifle pixels (min to max) | 61,567–73,303 | same | 61,567–73,306 | 61,567–72,662 |

Reading these honestly: the first two rows show the point (the hand stays in view); the magazine's smallest count is a frame at the instant of release, and the rules (not these minima) are what the test enforces. The `still` variant passes all 15 rules **with thin margins**: at lift 1.7 it fails "no replacement magazine drawn with under 3,000 px of its arm in the frame", at 1.9 the crosshair box rule fails. The calm clip's pickup values were fitted by scanning (hip (-0.190, 0.040, -0.110), carry (-0.115, 0.050, -0.050)); no threshold was touched. The thresholds in `reload_visibility_test.gd` are unchanged from art-v8.

## What it looks like (`frames/`, `video/`)

- `frames/variants-ticks-1280.jpg`: ticks 14, 36, 58, 82, 98, 118 for default / current / calm / still (same camera, size, lighting and timing). `frames/sheet-*.jpg`: contact sheets of every variant. `video/variants-2x2-60hz-normal.mp4` and `video/variants-2x2-slow-quarter-speed.mp4`: the four side by side, from the 60 Hz tick captures (153 frames each).
- At the hip (tick 58) the default and `current` rows show the magazine without a visible hand, as before. `calm` and `still` show the gloved hand holding the magazine at the bottom of the frame.

## Trade-off I want to be plain about

In `calm` and `still` the replacement magazine appears **in a visible hand with no visible source** (no pouch or object it came from): the hand reaches below the frame edge and comes back with it. In the default clip the hand is off-screen while it fetches, and the magazine is first drawn about 20 % in frame. Neither shows a pouch (see `../reload-retrieval/README.md`). Which reads better is a judgement I cannot make for players; I recommend `calm` because it keeps the support hand and the magazine continuously visible and cuts roll by 60 %, but I have no evidence it is more comfortable.

## Not claimed

No comfort or accessibility benefit (no human tests); no device testing; the `still` variant's rifle sits high and partly crosses the signage in the sunlit view, which I find odd-looking rather than calm. A human review of all three at normal and slow speed should decide the default.
