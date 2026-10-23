# ARM macOS and iOS outcome

Frozen source `0ca125dfba637868e6e8e9772ff9c40400413e32`, Actions job `119629141595`, run `39719407304`.

ARM exported default-graphics startup and ten native source suites pass. The new generic-device iOS build fails at the real linker. G13 platform/gameplay and G14 mobile preservation remain open.

## Actual iOS failure

`arm-receipts/evidence/ios-compile/compile.json` records Darwin arm64, macOS 15.7.9, Xcode 16.4 (16F6), iPhoneOS SDK 18.5, Apple clang 17.0.0, and checksum-pinned Godot 4.7.2. Export and structural inspection exit zero. Source/export/project receipts match the independently recomputed frozen identity. `xcodebuild` runs Debug with `-sdk iphoneos -destination generic/platform=iOS CODE_SIGNING_ALLOWED=NO`; its device command exits 65 after 36.095 seconds, without timeout or surviving owned process group.

`xcodebuild-device.log:240` contains a real arm64 CompileC action. The linker action starts at line 247; its command uses `-target arm64-apple-ios15.0`. Lines 258–270 report undefined `_CADynamicRangeAutomatic`, `_CADynamicRangeConstrainedHigh`, `_CADynamicRangeHigh`, `_CADynamicRangeStandard`, and `_MTLTensorDomain`, referenced by `libgodot.a[1146](metal_cpp.ios.template_debug.arm64.o)`. Line 273 reports `** BUILD FAILED **`. Other linker warnings include absent Swift DarwinFoundation autolink libraries/frameworks and a disallowed direct SwiftUICore link. The evidence locates the immediate failure in native linkage of the pinned Godot device library against this selected SDK/toolchain; no simulator-architecture inference is needed.

The actual Ld summary is `Ld .../sightbreak normal (in target ...)`, without `arm64`. The reviewed regex `^Ld .* normal arm64` would also reject an otherwise successful build with this format. This parser issue did not cause the present failure: the helper first rejects the real exit 65. A correction should bind the summary to its actual device/architecture linker command and retain independent binary platform checks. No built-app inspection, signature check, source-after command, installation or runtime gate was reached.

The job's exact Included Software link, https://github.com/actions/runner-images/blob/macos-15-arm64/20260907.0337/images/macos/macos-15-arm64-Readme.md, was read through the GitHub connector. It lists default Xcode 16.4 and installed Xcode 26.3 (17C529) at `/Applications/Xcode_26.3.app` with iPhoneOS 26.2, plus Xcode 26.2/26.1.1/26.0.1. The retained image inventory supports trying a compatible installed SDK/toolchain while preserving Godot 4.7.2. This inventory is not a successful build result.

The later desktop package manifest again records clean frozen source, so the failed build did not change its attested source identity. The helper's full successful post-build source/app checks remain unexercised. The app and DerivedData were intentionally excluded from uploaded QA; no output Mach-O was reopened in this review. The 289,501,975-byte development artifact exceeds the 32 MiB transfer limit and was not requested.

## ARM desktop evidence

The host is a 3-CPU ARM64 VirtualMac2,1. Logs identify ANGLE over Metal on an Apple Paravirtual device. The original graphical verifier exits zero and retains `verification/macos-menu.png`. The later minimal editor 2D/3D, exported minimal 3D, frozen-game and candidate-game trials all exit zero within the unchanged 120-second budget, with clean logs, readiness/capture markers and no surviving owned process group. Candidate default completes in 2.629 seconds in the ordered diagnostic. This duration is an observation only; shared caches and ordered launches do not prove a speed improvement.

All six retained PNGs decode completely with Pillow. The original and candidate menu images were opened and show the SIGHTBREAK menu and world; the minimal 3D image shows its lit cube. The menu captures are 1004×564 on this hosted window. No physical-GPU performance, player input or gameplay was exercised by these startup cases.

Ten source suites report 1,281 checks and zero failures: actor 73, match 75, authority order 178, state privacy 55, movement prediction 725, peer lifecycle 16, input mode 36, menu focus 30, offline diagnostics 60, HUD objective hint 33. The 297-entry source resource inventory matches the frozen checkout byte for byte. Native macOS producer receipts show distinct fresh per-suite user directories, no prior profile/diagnostic state, and matching before/after identities. The runner reports source/copied resources unchanged, outer user namespace removed and temporary project removed, with no finalization failures.

There is a bounded cleanup limitation: `hud_objective_hint_test.gd` creates a second native directory `SIGHTBREAK_QA/hud-objective-hint-2472-215773` and ownership marker, then exits without removal. The outer runner tracks only its `SIGHTBREAK-native-tests-*` namespace, so its cleanup receipt does not establish removal of this extra HUD fixture. Save isolation works; complete cleanup of every created native directory is not established.

## Retrieval and checks

Connector artifact `12400936508` is 591,186 bytes, SHA-256 `a3e26e62226a0431d3f51bf1669c2bc1a5fdc195d3d061676d14cf6135ba6e04`; its inner receipts ZIP is 591,042 bytes, SHA-256 `9c7a6b11ccf2f121ba5c63e03eadc4cd80a40310edb43c3f927a4fe257767faf`. Independent audit verifies all 136 indexed raw files (526,749 bytes) with no mismatch. Connector QA artifact `12400692213` is 1,024,158 bytes, SHA-256 `497c4adca952196632651503ab99eabcc36a77898725e6e16e2ed74854c91852`; it supplies the PNGs. Raw artifacts, extraction, job logs, source snapshots and audit receipts are retained here.

The first log request returned BlobNotFound while packaging was still active. A later completed-job connector request succeeded. No denied download route was bypassed. A local extraction command had a syntax typo before execution; the corrected command verifies the archive digests before extraction. Neither issue changes the native results.
