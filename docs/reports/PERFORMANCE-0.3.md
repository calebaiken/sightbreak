# Rendering measurements — 0.3.0-dev

## Scope and reproduction

These are **Linux Xvfb / Mesa llvmpipe software-rendering diagnostics**, not physical GPU or mobile FPS measurements. No Android/iPhone was attached. Thermal behavior, battery use, sustained phone performance and shader compilation on device remain unverified.

```sh
DISPLAY=:99 ./scripts/profile_render.sh "$PWD/builds/qa/v03/profile-after" standard
DISPLAY=:99 ./scripts/profile_render.sh "$PWD/builds/qa/v03/profile-low" low
```

`game/tests/render_benchmark.gd` constructs Relay Yard, a local rifle and four fixed operators at 1280×720. Each of three processes captures the same four camera poses, warms eight frames and measures 24 frames per pose. Only visual animation advances at 1/60; bots and match simulation are excluded. These fixed-work views also exclude active smoke and ten-player combat; a separate smoke stress probe measures the cloud in a ten-operator fixture. Both versions use the first two allowed CPU cores, two Mesa workers, identical cameras and sample counts, VSync off, and no frame cap. Other native capture jobs are serialized. Shared host scheduling and short sample windows still affect frame times. The 0.2 baseline is an immutable `git archive` of `4f21dc14ef73c3d620f095065ab89a0035ddd1f2`, imported separately with the identical benchmark added; it does not share current gameplay files.

Standard uses 2× MSAA and sun shadows; low disables MSAA, sun shadows and optional world normal/roughness lookups. Low retains surface resources, so it does not promise lower allocated texture memory. Godot's primitive counter is reported as primitives, not asserted to be a precise triangle count across every primitive topology. Draw calls include shadow/render passes. Texture bytes are global tracked allocations, not a physical GPU working-set measurement. Scene construction excludes engine startup/import; first-present time includes cold renderer work and cannot isolate shader compilation.

## Fixed-work before/after results

| View | 0.2 median ms | 0.3 median ms | Draws before → after | Primitives before → after |
| --- | ---: | ---: | ---: | ---: |
| approach | 463.606 | 561.950 | 353 → 444 | 24,782 → 136,954 |
| site | 431.488 | 494.209 | 178 → 239 | 16,650 → 63,966 |
| overview | 337.987 | 472.588 | 332 → 451 | 26,154 → 120,622 |
| operators | 452.032 | 532.717 | 296 → 383 | 23,068 → 113,648 |

These numbers are medians of three run medians, not FPS targets. **The added art costs more rendering work overall**: standard-preset frame medians rose approximately 15–40% in these views, with more submitted geometry and draw calls. This is a measured quality/cost tradeoff, not an overall rendering speedup. The separate occluded-armory optimization is a speedup with unchanged visible output.

Tracked texture allocation rose from **50,568,122 to 55,942,068 bytes**. Median construction increased from about **89.5 to 291.5 ms** (three observations per version). Actor construction/model batching and new architecture contribute; this measurement does not isolate them individually.

Shared-host variance matters: the baseline p95 samples span roughly 505–798 ms; the final operator view has a 1,349 ms p95 outlier in its third run. Cold first-present costs are retained in the per-run records; they include renderer startup and cannot be called shader compilation time. Short samples cannot establish long-session stutter behavior.

[Raw summaries, per-run counters and logs](evidence-v03/render-profile/) retain every measured run, including outliers. Comparable static native pictures are in the [world gallery](media/v03-world/README.md); the profile fixture additionally includes four operators.

## Low preset measurements

Same current source, camera poses, two CPU cores and three runs; this is a comparison with Standard, not a second historical baseline.

| View | Low median ms | Draw calls | Primitives |
| --- | ---: | ---: | ---: |
| approach | 88.181 | 170 | 40,070 |
| site | 81.068 | 90 | 19,866 |
| overview | 87.158 | 185 | 37,602 |
| operators | 82.728 | 156 | 36,820 |

Low tracked texture allocation is **41,196,468 bytes**. Optional maps remain loaded; the lower framebuffer/MSAA requirements and disabled shadows/lookups reduce work. Physical-device quality/performance selection still needs measurement.

## Measured optimization ledger

- **Hide fully occluded menu world behind the opaque armory:** a maintained native visible→hidden→visible experiment produced identical UI screenshot hashes in all three phases. Median draw calls fell **358→33**, primitives **74,346→4,292**, and software frame samples **267.880→21.875 ms** (restored visible **261.336 ms**). Kept the change; returning to menu restores the world, and hidden camera orbit work stops. This is a measured removal of invisible work, not a phone speed claim. See [retained menu-occlusion evidence](evidence-v03/menu-occlusion/README.md).
- **Share/batch operator and weapon geometry:** material batches preserve rigid animation joints and reduce per-part draw overhead. The final fixed-work comparison above records overall scene cost; extra map detail can offset these savings. No claim that every added detail is an optimization.
- **Demand-render cosmetic studios:** bounded 1024×512 maximum and one requested update per interaction; animated reveal requests updates only during its transition. Three unshadowed studio lights and no individual 3D viewport per inventory card. Lifecycle tests separately establish short resource plateaus; device battery savings remain unmeasured.
- **Keep one world sun and shared sky:** no extra world dynamic lights, SSAO, reflection probes or expensive postprocessing were added. Compatibility rendering does not support the requested SSAO path; direct light and geometry establish shape instead.

## Smoke stress diagnostic

A separate fixed camera, ten stationary operators and one fully grown cloud use Standard world/shadow/MSAA settings. Only the cloud budget changes: six versus three alpha quads plus the opaque core. Eight warm-up and 24 sampled frames per condition, two CPU cores/two Mesa workers; one sequence only. The shared 64² texture is preallocated in every condition.

```sh
DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=2 taskset -c 0,1 \
  ./scripts/godot.sh --audio-driver Dummy --script res://tests/smoke_render_probe.gd \
  -- --output="$PWD/builds/qa/v03/smoke-cost"
```

| Condition | Draw calls | Primitives | Median ms | p95 ms |
| --- | ---: | ---: | ---: | ---: |
| clear | 540 | 196,160 | 981.226 | 2251.155 |
| standard_cloud | 547 | 196,796 | 915.178 | 1354.447 |
| low_cloud | 544 | 196,790 | 974.178 | 1976.645 |

The measured cloud overhead is **seven draws / 636 primitives** on Standard and **four draws / 630 primitives** on Low. Tracked textures remain **55,963,912 bytes** throughout; the cached cloud texture adds 21,844 bytes relative to the equivalent render target without it. **Frame-time variance is too high to conclude a smoke speedup or a Low-versus-Standard timing advantage.** Occlusion also changes visible scene work. The counters establish bounded submission cost; this single run does not isolate fill rate, prove the cloud is cheap on phones, or cover simultaneous smoke grenades. The startup log retains a shader-cache recompile warning; no script/render error occurred.

[Raw samples and unedited captures](evidence-v03/smoke-cost/metrics.json) preserve the complete result and zero failed checks. The opaque central volume remains visibly spherical, an explicitly open art defect. Physical-device overdraw profiling and multiple-cloud stress remain required.

## Device budgets still to establish

Capture CPU/GPU frame timing distributions, draw/triangle/texture residency, first load and repeated shader warm-up, memory, touch-to-response, and a full sustained match on representative low/mid/high Android devices. Record OS, chipset, build SHA, preset, temperature, battery change and reproducible camera/match workload. Verify low-preset readability before lowering quality further. Instancing is already used for repeated architecture and effect pools; distance LOD and geometry streaming remain future work contingent on real device profiles.
