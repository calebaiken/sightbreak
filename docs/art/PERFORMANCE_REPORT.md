# Performance report: Relay AR slice

**Read this first.** Every number here was measured on a 4 vCPU cloud container that renders with Mesa llvmpipe (software, on the CPU) under Xvfb. llvmpipe's cost is dominated by rasterisation and vertex work on the CPU, so it exaggerates triangle cost compared with a phone GPU. These are **relative costs between variants on one host**. They are not frame rates, and they are not evidence about any phone. Physical Android/iOS frame time, thermals and battery are **unverified**.

## Viewmodel cost (`game/tests/weapon_render_benchmark.gd`)

The test uses one fixed yard view at 1280×720 and alternates three variants over 3 rounds. Each round runs 8 warm-up frames and 40 measured frames, and the median frame time per round is recorded. Raw output is in `docs/reports/media/art-v1/logs/weapon_render_benchmark-<head>.log`.

| Variant | Draw calls | Primitives | `498311e` | `b376e61` | `ecd290b` (hands v2) |
| --- | ---: | ---: | ---: | ---: | ---: |
| No weapon | 23 | 37,452 | 120.8 ms | 118.4 ms | 112.9 ms |
| Procedural rifle with box hands (0.4) | 28 | 40,476 | 128.3 ms | 129.4 ms | 126.3 ms |
| Relay AR with baked hands | 30 | 76,326 (77,698 at `ecd290b`) | 160.0 ms | 169.5 ms | 174.2 ms |

Each cell is the median of 3 round medians. Round-to-round spread is a few milliseconds, and the "no weapon" row also moves between runs, so compare within a column.

What this shows:
- The authored viewmodel adds **2 draw calls** and about **37k primitives** compared with the procedural one. That matches the budgets: 30.3k triangles for the rifle and 9.7k for the hands, which grew with the second hands pass.
- On llvmpipe it costs **+32 ms** per frame over the procedural rifle at `498311e`, **+40 ms** at `b376e61` and **+48 ms** at `ecd290b`.
  - The default finish then sampled the baked albedo, and the hands grew by about 1.4k triangles.
  - The view is simple, so the viewmodel's share is large.
- **Texture memory:** six 1024² maps, VRAM compressed with mipmaps, take 5.59 MB in S3TC/BPTC and the same in ETC2. This is measured from the imported `.ctex` files.

## Risk and mitigation

About forty thousand first-person triangles is within what current mid-range mobile GPUs draw comfortably, but that is **an expectation, not a measurement**. Until a device run exists:

1. On the LOW tier, render the viewmodel from a reduced LOD. The importer already generates LODs, and `lod_bias` or an explicit decimated export can select one. Measure LOW and STANDARD separately.
2. Keep viewmodel shadow casting off (already the case).
3. Re-measure with this harness after every weapon added to the pipeline.
4. Before any release decision, run the same fixed view on a physical low-end and mid-range Android device and one iPhone. Record frame time, GPU time and thermals over 10 minutes.

## Regression status (art branch head)

`scripts/validate.sh` passes on `ecd290b`, with 1,958 native assertions. That includes `weapon_art_test.gd` (43), the bot match and two ENet clients. The log is in `docs/reports/media/art-v1/logs/validate-art-head.log`. No gameplay value, hit volume, network protocol or economy behaviour is changed by this slice.
