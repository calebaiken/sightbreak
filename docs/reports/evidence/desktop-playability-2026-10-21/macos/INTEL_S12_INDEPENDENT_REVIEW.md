# Final S12 Intel macOS evidence and native stacks

[Run39673232413](https://github.com/calebaiken/sightbreak/actions/runs/39673232413), job119476277947, exact source `e3c1194a9c7bb2ff8a5e3b81ab122513dce4a32c`, game tree `45b6c6ea9d3244700e324e90d6df4778ee28d18e`. Whole Intel job: FAILURE. The native default verifier, retained explicit-OpenGL verifier and controlled comparison each exit1. This reviewer ran no engine/application; all findings inspect retained actual native evidence.

QA artifact12382096873 is437214bytes and matches upload SHA256 `a3469c6bda682ab1dcd530200df799e4a864b882bf9d5b581a7bed703b11fc0a`. Fresh safe extraction: `intel-s12-qa-extracted/`. Source/runtime/tool receipts agree exactly with S12 and remain unchanged. Official engine4.7.2 ed1daf0bf runs on macOS15.7.9 x86_64 image20260824.0482.1. Logs select Apple Software Renderer / OpenGL4.1 APPLE-21.1.1; detailed profiler GPU metadata remains UNVERIFIED because JSON was unavailable.

| Actual graphical case | Native result | Capture |
| --- | --- | --- |
| Editor minimal2D | Exit0 |1280×720 label|
| Editor minimal3D | Exit0 |1280×720 lit box|
| Export minimal3D | Exit0 |1280×720 lit box|
| Original frozen game0fb7480 | TIMEOUT120s; native exit absent |None|
| Candidate S12 game | TIMEOUT120s; native exit absent |None|
| Explicit-OpenGL minimal3D | Exit0 |1280×720 lit box|
| Explicit-OpenGL candidate | TIMEOUT120s; native exit absent |None|

All four original PNGs match their receipt hashes/dimensions and were visually inspected without alteration. 2D SHA256 `b2717a5743e1e4513a4be34df8a8e23e3f46fd3c90f3c0d1251ca17878f3a96b`; all three 3D PNGs SHA256 `abab76c84c40c859c9264c2bc7b109250b9c994fc229e40e7300aac6e7dd43d8`. Failed game trials have no PNG and never reach the15th-frame readiness/capture marker. Candidate default first_process is10920ms; explicit OpenGL first_process1692ms. Neither timing establishes comparative performance because caches/order differ.

Every failed comparison game trial remains runnable around96.6–100% CPU at sampled checkpoints, exits-15 only after bounded controller SIGTERM, and leaves no owned process group. Clean application logs do not convert that cleanup into a native pass.

Six native two-second samples were inspected. Counts are main-thread stack samples at each checkpoint, not continuous profiling or all-process CPU percentages:

- Candidate default15s: all1379/1379 main-thread samples traverse `glDrawElements_GL3Exec -> gldLoadPipelineProgram -> glpPPShaderLinearizeStreamMgrEx -> BuildInterferenceSets` in Apple's software GL libraries.
- Candidate default90s:751/751 traverse software drawing;749 pass through `gldMergeScanlines2x2`,745 through `gldLLVMFPTransform2x2`, and737 take the dominant `glvmInterpretFPTransformFour` branch.
- Original frozen15s:832/832 traverse pipeline-program/shader linearization and interference-set work. At90s all1346 are again in software draw/shader-program paths, split across752/594 draw branches.
- Explicit-OpenGL candidate15s:1322/1322 traverse pipeline-program/shader linearization. At90s1316/1316 traverse software drawing, with1308 in the dominant fragment-transform branch and1291 in its dominant fragment interpreter branch.

Minimal, frozen and candidate lipo receipts each exit0 with `x86_64 arm64`; native strict codesign checks each exit0. All eight maintained source suites exit0/clean. Those structural/signature/source results remain separate from failed graphical execution. The original frozen archive/payload verification succeeds; no baseline re-signing or byte replacement occurred.

Final evidence reproduces the same minimal-versus-game distinction found in r2. Expensive work is localized to Apple software shader-program processing/fragment execution during game drawing. It does not isolate the responsible material/shader/draw call, establish an engine/application defect, prove a blanket unsupported-host condition, or qualify a physical Intel Mac. Stripped official frames above the driver are insufficient for that attribution. Main-thread outer AppKit frames are not proof of an idle input/focus deadlock.

The next authorized step is bounded feature isolation in a separate source-hashed menu-arena diagnostic project, followed by actual physical Intel GPU qualification. Production renderer/material changes are not justified solely by this hotspot. Keep120s budgets, the original failed default game gate and historical macOS14 ANGLE exception separate. No runtime/renderer/signing/gate was changed during this review.
