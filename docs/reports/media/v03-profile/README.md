# Fixed-work profile captures

Unedited actual Godot 4.7.2 Compatibility images at 1280×720 on Xvfb/Mesa llvmpipe. Same camera poses and five-actor fixture as `game/tests/render_benchmark.gd`; one local actor and four displayed operators. These are synthetic rendering fixtures, not played match screenshots.

| View | 0.2 Standard | 0.3 Standard | 0.3 Low |
| --- | --- | --- | --- |
| Approach | [Before](before-approach.png) | [After](standard-approach.png) | [Low](low-approach.png) |
| Operators | [Before](before-operators.png) | [After](standard-operators.png) | [Low](low-operators.png) |

Before is immutable starting commit `4f21dc14ef73c3d620f095065ab89a0035ddd1f2`; after uses final world/actor/model sources included in game tree `ab35c845326fe859c86f3d0b4e37038e82e18c44`. Standard has 2×MSAA/sun shadows; Low disables them and optional surface maps. Actor placement and 1/60 visual ticks match, but the animation implementation changed. Image SHA256 values are in `captures.json`.

[Measurements and limitations](../../PERFORMANCE-0.3.md). Low retains silhouettes, world labels and route markers but loses grounding shadows and edge smoothness. Physical-device readability is unverified.
