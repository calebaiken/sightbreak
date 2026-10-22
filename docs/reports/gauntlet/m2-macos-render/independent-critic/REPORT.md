# Independent Intel macOS render diagnostic review

Verdict: choose candidate `8042d76` + `2390ab8` over baseline `6a0d8d5` for diagnostic usefulness. Approved for diagnostic integration and one manual Intel CI investigation. No blocking correctness finding was found in this bounded review. This does not approve a Mac fix, G13, gameplay, physical GPU performance, visual quality, or CS2 parity.

The candidate can distinguish first completed renderer frame from progress through the next fourteen frames and can screen named feature groups while preserving one camera and the actual menu. The baseline's absent marker after fifteen process callbacks cannot answer either question. This is a source and evidence-method comparison; a blind visual ranking would not answer the diagnostic question.

The largest remaining deficiency is the absence of actual Intel Mac feature-case results. Native feature attribution remains UNVERIFIED. Linux timing is not Mac evidence.

## Findings and limits for the next run

1. The feature cases are grouped ablations. `surface-detail-off` removes normal mapping and roughness textures; `materials-untextured` also removes albedo textures from the registered surface materials; `sky-off` changes the background and disables sky reflections. The comparison can narrow a feature group, but cannot identify one texture, shader instruction or render pass. If a group wins, split it before selecting a shipping correction. The source and report already limit claims appropriately; this does not block the first screening run.
2. Case order is fixed and cases share the diagnostic user/cache identity. Shader/driver cache effects and initialization costs can affect raw durations and even a tight timeout comparison. If a variant captures while full times out, repeat a warm full reference and the implicated case before claiming the variant explains the difference. The script explicitly labels ordered caches as outside performance acceptance. No relative speed claim is approved from the retained Linux results.
3. `RenderingServer.frame_post_draw` establishes Godot's completed viewport-render phase. It is not a measured GPU fence, display presentation timestamp, or input-to-photon measurement. On the old Intel software renderer, the sampled synchronous fragment-raster work makes this a useful progress marker; retain that terminology boundary.
4. The new report status says collection is complete even when individual cases fail. Read each trial's `passed`, `trace_complete`, `timed_out`, capture and cleanup fields. The unchanged shipping verifier remains a separate failing step, so diagnostic collection cannot turn the shipping gate green.

## Source and resource preservation

Reviewed clean checkout: `/workspace/sightbreak-macos-render`, branch `codex/v1-macos-render`, exact HEAD `2390ab82f08ed766742bbbdf37bb08e46f204a46`.

Baseline and candidate game tree both equal `13079ab8a3de9b18252a652ed57157e0776cf394`; content SHA-256 remains `954b0a73cff89483a9270434da7902b2d128f1b9a99c30290dfe03862c038873`. No game, `diagnose_macos_startup.py`, `verify_builds.py` or `toolchain.py` change appears in the candidate diff.

A fresh reviewer-created fixture contained all 126 expected tracked, non-test game files. Every copied source hash matched, and every non-overridden destination matched. Only the declared project identity/main scene and export preset were replaced; the wrapper and wrapper scene were added. Source identity was exactly unchanged before/after fixture preparation. The separate custom user directory avoids reading shipping player state. The output path guard excludes the game tree and current shipping Mac payload. Before/after receipt validation binds the shipping artifact to unchanged source and payload.

The retained final Linux fixture's local file hashes all match. Its exact binary SHA-256 is `9b3e910f3e54fa4900e66fb6c8538aeccf7c6719b454107a85986b068915bca9`. Its 136 packed resources include the diagnostic wrapper, compiled shipping modules and imported weapon assets/textures, and exclude test harnesses. The final wrapper SHA-256 is `7ffcc1451ae46226b8efe76cf8924e697d7c8268b434af827bfd4bba339670f3`, matching current source and fixture receipts.

`main._process(0.0)` sets the same initial process camera position in every case and then disables only main's process callback. The world geometry, menu UI and renderer remain active. Arena material batching retains both original and derived materials in `_surface_materials`, so the material cases reach the rendered batch materials. The non-full saved cases report nonzero changes: 1 directional light, 1 detail provider, 1 environment, and 21 surface materials respectively.

## Actual evidence inspected

The original supplied ZIP and committed retained copy both hash to `c3179d25d87cce7030bc3d9c9700990094d799eb8610df221e38a8e321b5b8a5`. It binds to source `6a0d8d5d85b4fb37943903886982f51b4ed230b0` and the same game tree/content above. The original candidate default/OpenGL receipts show 120-second timeouts with no capture and no surviving owned process group. Original 15/90-second samples show `glDrawElementsInstanced_IMM_GL3Exec` → `gldRenderFillTriangles` → software fragment execution. They prove active rendering work at sampled times, without identifying the material/pass or how many frames completed.

Final exported Linux captures were opened and inspected at 1280×720. Menu layout, camera view and geometry agree across all five; the shadows and sky changes visibly affect the intended rendering. All five PNGs fully decode. Their logs independently parse to exactly frames 1–15, with matching case names and nondecreasing timestamps; parsed values equal the retained JSON. Logs pass the shared native error/leak gate.

| Case | Changed | Frame 1 ms | Frame 15 ms | Draw calls | Primitives |
| --- | ---: | ---: | ---: | ---: | ---: |
| full | 0 | 1330 | 4062 | 135 | 43330 |
| shadows-off | 1 | 1011 | 3010 | 125 | 23878 |
| surface-detail-off | 1 | 1148 | 3819 | 135 | 43330 |
| sky-off | 1 | 1101 | 3517 | 135 | 43330 |
| materials-untextured | 21 | 1061 | 3621 | 135 | 43330 |

These are retained Linux correctness observations only. The shadow case's lower submitted primitive count is expected because shadow passes are disabled; visible world geometry is retained. No renderer or Godot process was launched by this critic, so the concurrent offline run was not disturbed.

The candidate unit suite passed 4/4 tests. Independently exercised nine real subprocess controls through the shared native runner: clean success, dirty log, missing marker, exit 7, SIGTERM-ignoring timeout requiring SIGKILL, missing capture, invalid PNG header, timeout cleanup of a real parent/child process tree, and external SIGTERM interruption with a retained exit-143 receipt. All had the expected acceptance/rejection result and zero surviving owned group. The timeout test uses a shortened test-only in-memory budget; source budgets stay 120 seconds.

## Workflow

`macos-render-diagnostic.yml` is manual only, public-repository guarded, uses `macos-15-intel`, grants only `contents: read`, and pins checkout/setup-python/upload-artifact to 40-character commits. It installs the checksum-pinned 4.7.2 toolchain, tests the diagnostic controls, exports clean exact shipping source, and runs the existing shipping graphical verifier unchanged. An `always()` condition permits diagnosis after a failed shipping qualification only when export succeeded.

Each diagnostic import/export is bounded at 120 seconds, and each native feature case uses the inherited 120-second trial runner with owned process-group cleanup and samples at 15/90 seconds if still alive. The Universal 2 architecture check, full-case inclusion, logs, per-case JSON, fixture hashes, payload descriptors, failed trial retention and final source/receipt check are present.

The always-run packaging step gathers shipping receipts/logs, verifier results/captures and diagnostic JSON/logs/samples/captures. Its manifest binds each included file to bytes/hash, run ID and source commit; the ZIP preserves originals and fails above the upload-size limit. The final artifact step runs on every outcome. Fixture project/app binaries are represented by hashes rather than included in the small QA ZIP; source and pinned toolchain are required to reproduce them. A diagnostic may fail on a new machine; the workflow's actual run and downloadable evidence remain unverified until dispatch completes.

## Review record

Exact parent brief: `brief.txt`. Re-runnable commands: `commands.sh`; independent audit sources: `audit_evidence.py`, `audit_fixture.py`, `process_controls.py`. Raw receipts/logs are under `raw/`; the extracted original Linux controls are under `linux-controls/`. `SHA256SUMS` binds this review.

One reviewer audit initially assumed pack paths had a `res://` prefix. Actual embedded pack paths are relative and use remaps; the assertion was corrected in the review script. That was a reviewer assumption error, not a candidate failure. No implementation file was edited.

Read the native Mac per-case progress and capture results before planning a product correction. Preserve G13 as FAILED until the unchanged shipping game passes its existing gate and platform qualification.
