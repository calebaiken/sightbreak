# Independent Intel macOS outcome

Run [39719407304](https://github.com/calebaiken/sightbreak/actions/runs/39719407304), job `119629141604`, exact source `0ca125dfba637868e6e8e9772ff9c40400413e32`. The unchanged exported default startup gate fails at 120 seconds. Explicit OpenGL also fails. Every grouped feature case times out. No shipping graphics correction is supported by these results; G13 remains FAILED.

The native host records macOS 15.7.9, x86_64, model Macmini6,2, four CPUs, runner image `20260824.0482.1`. Logs identify OpenGL 4.1 APPLE-21.1.1 on Apple Software Renderer. The display profiler did not produce usable JSON, so physical GPU capabilities are unverified. These are hosted software-render observations, not physical-GPU performance or gameplay qualification.

## Startup controls

The original graphical verifier retains `macos-graphical-menu` TIMEOUT in `verification/results.json`; `raw/intel-job.log:406` identifies its unchanged 120-second command. The subsequent explicit OpenGL command also raises a 120-second timeout at line 451. No shipping menu capture is present. Headless menu/demo startup exits zero; this does not satisfy graphical startup.

The later diagnostic verifies the original frozen comparison artifact and all three Universal 2 binaries, preserves source identity, and reports:

| Native trial | Result | Total seconds |
| --- | --- | ---: |
| Editor minimal 2D, default | Captured, exit 0 | 2.894 |
| Editor minimal 3D, default | Captured, exit 0 | 30.874 |
| Exported minimal 3D, default | Captured, exit 0 | 8.689 |
| Frozen game, default | 120-second timeout, no capture | 120.335 |
| Candidate game, default | 120-second timeout, no capture | 120.461 |
| Exported minimal 3D, explicit OpenGL | Captured, exit 0 | 23.697 |
| Candidate game, explicit OpenGL | 120-second timeout, no capture | 120.609 |

All diagnostic trials have clean native logs and no surviving owned process group. Four actual minimal-control PNGs fully decode; the 2D label and exported 3D lit cube were opened and inspected. The QA archive also contains copied source textures, which are not native captures. The frozen comparison is original source `0fb74800cffb96077069144028d113e308ef1744`, outer ZIP SHA-256 `45e7bd2cc36514333651c484a6950260e31afa81b7efc2bcb4fe7771b1a036eb`.

Candidate default reaches `ready_enter`, settings, menu construction and `first_process` at 6,928 ms before timing out. Its old ready marker follows fifteen process frames; absent readiness cannot establish zero completed draws. The actual stack samples independently show active rendering work.

## Feature outcomes

All five cases reach their construction marker but log no `frame_post_draw` completion and retain no PNG. Independent parsing of raw logs exactly matches their empty `draw_trace` arrays and `trace_complete=false`. This means no instrumented completed viewport-render phase was observed; it does not mean no rendering work occurred or establish GPU presentation.

| Case | Changed items | Outcome | Total seconds |
| --- | ---: | --- | ---: |
| full | 0 | 120-second timeout | 120.507 |
| shadows-off | 1 | 120-second timeout | 120.510 |
| surface-detail-off | 1 | 120-second timeout | 120.505 |
| sky-off | 1 | 120-second timeout | 120.839 |
| materials-untextured | 21 | 120-second timeout | 120.408 |

Each case has a clean native log and no surviving owned group. `COMPLETE diagnostic cases only` means collection completed; every `passed` field is false. The fixture's 126 copied shipping resource hashes and wrapper hash match independently retained frozen source. Diagnostic preparation and Universal 2 export pass; source and shipping receipt remain unchanged.

The 90-second full-case sample shows `glDrawElementsInstanced_IMM_GL3Exec` → `gldRenderFillTriangles` → `gldMergeScanlines2x2` → `gldLLVMFPTransform2x2` → `glvmInterpretFPTransformFour`/`Inner` (`render-features/full-90s.sample.txt:46` onward). Shadows-off, sky-off and materials-untextured samples also show software draw/fragment work. Surface-detail-off at 90 seconds instead samples `gldLoadPipelineProgram` → `glpPPShaderLinearizeEx`/`StreamMgrEx` → `BuildInterferenceSets` and BitSet helpers (`surface-detail-off-90s.sample.txt:46` onward). The retained samples locate software raster/fragment execution and shader preparation in different cases; they do not identify one responsible material, primitive, instruction or pass.

These grouped switches did not produce a case within the startup budget. They cannot rank feature costs, prove a relative speed change or rule out interactions. Their fixed order shares cache identity. No passing variant exists to compare against a warm full reference. If a future variant passes while full fails, require a warm full repeat and implicated-case repeat before proposing a shipping change. A useful next diagnostic would isolate the responsible draw/material/geometry path while preserving the shipping gate; this review approves no implementation change.

## Source suites and evidence integrity

Ten actual Intel native suites pass 1,281 reported checks, with native fresh per-suite identities and zero reported failures. All 297 source resource hashes equal the frozen checkout. The outer isolated namespace and private project report removal with unchanged copied resources. The HUD test's extra `SIGHTBREAK_QA/hud-objective-hint-*` directory is outside that cleanup receipt, as detailed in `ARM_REPORT.md`; complete cleanup of all test-created paths is not established. Source-suite and startup results do not establish exported Mac gameplay.

Intel receipt artifact `12401532210` is 5,387,014 bytes, SHA-256 `8f9d844a1f37e89b447f07e9febf5215600cbaa2b89f7dfe3884b1dfbc815a13`. Independent audit verifies all 164 indexed raw files (5,307,040 bytes) without mismatch. QA artifact `12401691735` is 7,123,068 bytes, SHA-256 `9222e4391cf5f83ae5e57c0a83be894d75a1b9c53c4f04563960b31dfaaa8a3f`. Original ZIPs, complete logs/samples, source references and audits are retained. The 378,469,610-byte development artifact exceeds the 32 MiB transfer cap and was not requested; native binary hashes/architecture checks are receipt evidence, not independently reopened binaries.

The largest unresolved deficiency is the absence of a completed game menu capture and an identified responsible render path on Intel. No player input, match, physical GPU, human, signing/notarization or release acceptance is claimed.
