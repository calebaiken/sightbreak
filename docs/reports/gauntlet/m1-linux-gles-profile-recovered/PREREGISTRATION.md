# Linux GLES profile capability, recovered candidate

2026-10-23. Builder branch `diagnostic/linux-gles-profile-recovered`, isolated
worktree `/workspace/sightbreak-linux-profile-recovered`, exact base
`917b143ba4e4b0d9644a7a0ddeee1dd64c139682`. Earlier unpublished candidate
`ab4fa6d0` and review `9a3d6488` are unavailable locally. This is a new candidate
requiring a fresh independent source review. No approval is inherited.

## Named benchmark and scope

The inspected reference is the base's `scripts/verify_offline_match.py` ordinary
Linux plant / seed 42 / `--timeout 180` flow and the accepted native attempt at
`8afe0cc6b4c9051d3649a82bbcb4c8de8f947f9c`, retained in
[`m1-linux-frame-sampling/native-review/REVIEW.md`](../m1-linux-frame-sampling/native-review/REVIEW.md).
That attempt reached POST / round 1 / tick 2625 with 0.383333 simulation seconds
left after its original next-buy deadline. Its original gameplay gate remains
FAILED. Readbacks and sampled Mesa CPU support investigating software rendering
cost; they do not identify a costly function or an improvement.

Add one opt-in controller capability, `--linux-gpu-profile`. Admit only native
Linux, scenario plant, default or explicit seed 42 and exactly `--timeout 180`.
Reject combination with `--linux-frame-diagnostics`, so the external CPU sampler
stays off. Put Godot's `--gpu-profile` before the initial command's `--` argument
separator. Preserve the default path, original initial conditions and all
180/60/30/15/12-second bounds, and leave the normal reopened command unchanged.
No game code, timers, renderer selection, geometry, native extent, quality,
affinity, host priority or service settings may change.

This is a capability comparison with the original controller. No blind visual
comparison is applicable. Source correctness needs a separate critic. Runtime
capability needs the exact reviewed source and its fresh source-bound export;
neither the historical export nor this source proposal supplies that evidence.

## One future native attempt

After source/pure checks and fresh independent source acceptance, root may
coordinate exactly one ordinary Linux plant / seed 42 / 180-second attempt with
the profile opt-in and sampler off. This registration does not release an engine,
export, CI or native slot. No four-arm overhead/causal comparison is registered.

Keep original 1280x720 Xvfb, Standard, render scale 1, FPS limit 60, 60 Hz physics,
time scale 1, two Mesa workers, no recorder, ten stock-health actors and the
existing input/capture sequence. Retain all raw client/cleanup outputs,
commands, source/controller/engine/export hashes, native readbacks and the
original deadline success or failure. A failed ordinary flow must retain the
profile bytes already written; it must not acquire a longer gameplay budget.

The runtime capability gate requires at least one intact `GPU PROFILE` block
with a finite nonnegative header value and at least one finite positive named
task row, while the command receipt proves sampler off and only the initial
client profiled. Missing/zero/unsupported output is an unavailable capability,
not a rendering-cost conclusion. Preserve clean owned-process teardown and
explicitly retain whether next buy and restart were reached. A diagnostic
capability pass cannot promote the ordinary plant or release-performance gate.

## Exact upstream meaning

Inspected Godot tag `4.7.2-stable` resolves to
`ed1daf0bf001b61586d9930840f2f1394092c079`, matching the toolchain's
`4.7.2.stable.official.ed1daf0bf`. Exact URLs, lengths and SHA-256 values are in
[`upstream-sources.json`](upstream-sources.json). Fetches were read-only source
inspection; no engine was executed.

- `main/main.cpp:1982` accepts `--gpu-profile`; lines 3571–3572 enable the
  rendering server's print profile. The option is outside `TOOLS_ENABLED`.
- `drivers/gles3/storage/utilities.h:182–201` defines three query buffers.
  `utilities.cpp:329–360` uses desktop-GL `glQueryCounter(GL_TIMESTAMP)` and
  `glGetQueryObjectui64v(GL_QUERY_RESULT)`. Its comment calls the retrieved
  queries frame minus two. CPU timestamp fields also exist, but the printed
  task rows use GPU timestamp differences. The non-desktop-GL branch does not
  populate GPU query results. Native output must establish actual capability.
- `drivers/gles3/rasterizer_gles3.cpp:101–122` begins query retrieval at frame
  begin and rotates buffers at frame end. `RenderingServerDefault::_draw`
  reads the selected buffered results after rendering. Its stdout blocks have
  neither source-frame identifiers nor phase identifiers. The getter's frame
  value is not printed. Treat results as historical; do not assign BUY, LIVE
  or POST from stdout arrival or driver receive times.
- `servers/rendering/rendering_server_default.cpp:136–165` builds relative
  GPU milliseconds from buffered query values, subtracting the first captured
  GPU timestamp. It retains the previous `frame_profile` when no captured
  timestamps are available. The stdout loop does not deduplicate source-frame
  identities, so repeated/retained profiles must not be counted as independent
  unique-frame samples.
- Lines 167–209 accumulate each adjacent GPU timestamp difference under the
  preceding name, except names starting `<` or `>`. Identical names aggregate.
  After strictly more than 1,000,000 host microseconds, each named sum is divided
  by the number of `_draw` calls in that reporting interval. Only averages
  strictly greater than 0.01 ms print. Hash-map iteration supplies no ranked
  order. These are periodic accumulated task averages, not individual frames,
  percentiles or synchronized one-second gameplay phase windows.
- The header's `total` is the final relative GPU timestamp in the latest
  retained profile at that draw. It is not the interval average used for rows.
  Never sum the header with rows, expect printed rows to sum to it, or convert
  the header/row averages into physical FPS. Omitted rows, marker exclusions,
  startup/retained profiles and differing aggregation prevent that inference.

Under llvmpipe, these driver-query elapsed intervals can include software
rendering, submission, scheduling and waiting. They cannot partition process
CPU, identify GDScript/authority cost, measure independent physical-GPU work,
quantify sampler/profiler overhead or establish causality. Query collection and
stdout add unmeasured overhead. This single attempt may locate coarse renderer
task intervals worth a later controlled investigation; it cannot prove a fix
or any performance improvement.

## Source and pure gates before fresh review

1. Invalid platform/scenario/seed/budget combinations and sampler coexistence
   reject before any subprocess or output directory is created.
2. A pure controller interception verifies the exact engine option precedes
   the initial `--`, the sampler is never constructed, and the default command
   is unchanged. A structural comparison against the exact base must account
   for every changed controller statement and preserve the reopened command.
3. Run existing CPU-sampler, role-guidance and capture-fence pure controls,
   Python compile checks and `git diff --check`. Retain commands and outputs.
4. Freeze and push the new exact source. A fresh critic judges the candidate
   against the named original flow and these measurable gates. Runtime remains
   UNVERIFIED until root releases the separately coordinated slot.

The largest remaining deficiency is the lack of actual profiled native output
at the new exact source. The failed Linux next-buy gate and all broader release
gates remain open.
