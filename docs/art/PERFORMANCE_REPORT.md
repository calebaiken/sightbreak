# Performance report: Relay AR slice

**Read this first.** Every number here was measured on a 4 vCPU cloud container that renders with Mesa llvmpipe (software, on the CPU) under Xvfb. llvmpipe's cost is dominated by rasterisation and vertex work on the CPU, so it exaggerates triangle cost compared with a phone GPU. These are **relative costs between variants on one host**. They are not frame rates, and they are not evidence about any phone. Physical Android/iOS frame time, thermals and battery are **unverified**.

## Viewmodel cost (`game/tests/weapon_render_benchmark.gd`)

The test uses one fixed yard view at 1280×720 and alternates three variants over 3 rounds. Each round runs 8 warm-up frames and 40 measured frames, and the median frame time per round is recorded. Raw output is in `docs/reports/media/art-v1/logs/weapon_render_benchmark-<head>.log`.

| Variant | Draw calls | Primitives | Median, `498311e` | Median, `b376e61` (final) |
| --- | ---: | ---: | ---: | ---: |
| No weapon | 23 | 37,452 | 120.8 ms | 118.4 ms |
| Procedural rifle with box hands (0.4) | 28 | 40,476 | 128.3 ms | 129.4 ms |
| Relay AR with baked hands | 30 | 76,326 | 160.0 ms | 169.5 ms |

What this shows:
- The authored viewmodel adds **2 draw calls** and about **36k primitives** compared with the procedural one. That matches the budgets: 30.3k triangles for the rifle and 8.3k for the hands.
- On llvmpipe it costs **+32 ms** per frame over the procedural rifle at `498311e`, and **+40 ms** at the final head.
  - The final head's default finish also samples the baked albedo, which is probably most of that difference on a CPU rasteriser.
  - Round-to-round spread is several milliseconds.
  - The view is simple, so the viewmodel's share is large.
- **Texture memory:** six 1024² maps, VRAM compressed with mipmaps, take 5.59 MB in S3TC/BPTC and the same in ETC2. This is measured from the imported `.ctex` files.

## Risk and mitigation

Thirty-nine thousand first-person triangles is within what current mid-range mobile GPUs draw comfortably, but that is **an expectation, not a measurement**. Until a device run exists:

1. On the LOW tier, render the viewmodel from a reduced LOD. The importer already generates LODs, and `lod_bias` or an explicit decimated export can select one. Measure LOW and STANDARD separately.
2. Keep viewmodel shadow casting off (already the case).
3. Re-measure with this harness after every weapon added to the pipeline.
4. Before any release decision, run the same fixed view on a physical low-end and mid-range Android device and one iPhone. Record frame time, GPU time and thermals over 10 minutes.

## Regression status (art branch head)

`scripts/validate.sh` passes on `b376e61`, with 1,958 native assertions. That includes `weapon_art_test.gd` (43), the bot match and two ENet clients. The log is in `docs/reports/media/art-v1/logs/validate-art-head.log`. No gameplay value, hit volume, network protocol or economy behaviour is changed by this slice.
