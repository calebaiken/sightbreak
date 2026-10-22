# Independent ARM Mac preflight and iOS outcome

Accept the bounded no-event Mac readiness result and the unsigned generic-device iOS compile slice for run [39727011693](https://github.com/calebaiken/sightbreak/actions/runs/39727011693), exact source `e7718ee42fd67a65bcb83061c868b34bd9a2c3d2`, single job 119653125533 on macOS 15. The actual job succeeds. Mac input delivery, focus, OS screenshots, ordinary gameplay and iOS runtime remain unverified.

## Actual Mac preflight

On macOS 15.7.9 arm64, all four non-requesting API queries return true:

| API | Actual result |
| --- | --- |
| CGPreflightPostEventAccess | true |
| CGPreflightScreenCaptureAccess | true |
| CGPreflightListenEventAccess | true |
| AXIsProcessTrusted | true |

The result is `READY_FOR_INPUT_ATTEMPT` after 5.497604 seconds within the existing 60-second bound. It records zero posted input events, zero permission requests, and `native_input_verified=false`. Initial and final combined-session Escape, Tab and left-button states are up; the observer explicitly leaves event delivery and keyboard focus unverified. No denial, permission prompt, alternate identity or TCC change is attempted.

The active display is 1024×768 points. At 1.740115 seconds, CoreGraphics observes onscreen layer-zero window 34 owned by the exact exported child PID 6968, with bounds including chrome `[40, 32, 960, 568]` points. The original internal viewport PNG is 960×540, 272,885 bytes, SHA256 `8ff7528f89d2ff49650fd15cbe982f50805b0fcd5dc68dfe9d645343f95f955d`. Its bytes match the native receipt. Direct inspection shows the SIGHTBREAK menu, DEPLOY and Settings controls, ordinary default callsign and zero training progress. This proves internal exported rendering, not an OS screenshot or input delivery.

The real command uses supported `--windowed --resolution 960x540 --position 40,60 --log-file`, then the existing `--smoke --capture` path. Client and redirected engine logs are clean; the client records `SIGHTBREAK_MAIN_READY screen=menu`. Normal exit is 0. Cleanup sends no signals and attests the owned process group is gone. Source and export validation repeat successfully after cleanup.

Both canonical `offline_training.json` and `.tmp` entries are absent before and after. The native user directory already contains 86 files and 32 directories from preceding engine work. Independent comparison of its before/after inventories finds no created, removed or changed files or directories during this particular preflight. The observer preserves native files. This is a warm-directory pre/post observation, not proof of pristine caches, filesystem isolation, a concurrent-write lock or universal launch immutability. Cache contents themselves are not transferred; their native size/hash inventories are retained in the original receipt.

This improves the prior same-scope state from unmeasured ARM API/window readiness to actual positive readiness evidence. It does not improve the native-input acceptance status: no input was posted by design. The next gap is a separately reviewed, bounded real pointer/keyboard attempt with exact PID focus, supported OS capture and actual pixels. Persistent controls still need verified Mac profile isolation.

## Source, suites and startup preservation

Independent reconstruction from 376 tracked Git-object byte records gives game tree `b13548eb130058468b3778d824f17ac1bfd3f724`, shipping content SHA256 `9703e3b19f3feb13243f30ea9b244d411b08a5bb2b48d4c6a2bf88f5d2d71b47` and validation SHA256 `35761ba4155be2baa9a5b9a55fa22fed37bcc63b2eb488bdf830f55e17d542a3`. All clean source/export/manifest records agree. All 303 raw native source-resource hashes match the frozen Git blobs. The Mac executable receipt records 187,121,136 bytes and SHA256 `5fb2abbeaf5a0d68ec5a6d20760c2e06e799da02ae06bd20d89ed477b677fdee`; its separate PCK is SHA256 `56c7516395683c558d78a65ca4cf922fed58dc12afc3184054caf3c4457c1774`. The compiled binary/PCK were not independently downloaded. Later documentation does not relabel these artifacts.

All ten maintained native suites have genuine assertion summaries, clean logs and exit 0, totaling 1,281 checks. Engine-reported per-suite user directories are distinct and fresh, produced-file hashes match where retained, original/copied resources stay unchanged, runner-owned namespaces/private project are removed, and the inner HUD fixture explicitly attests removal and restoration of the caller directory. Synthetic focus/input source suites do not establish exported Mac input.

Default headless menu/demo and graphical menu startup pass. All five graphical diagnostic trials pass without a rendering override: editor minimal 2D/3D, exported minimal 3D, historical frozen game and current candidate. All five original diagnostic PNG hashes and dimensions match; all seven transferred PNGs were directly inspected. The host uses Godot's automatic ANGLE path on an Apple paravirtual device, so physical GPU behavior remains open. Candidate and frozen startup wall times are 4.106263 and 22.281463 seconds in this order; these are functional observations, not a controlled performance comparison or renderer-fix attribution.

The frozen trial's auxiliary two-second process sampler times out and exits −15; its owned group is gone. The actual frozen game itself exits 0 and retains a valid menu capture. This auxiliary failure is preserved rather than erased or misclassified as the game's startup failure. No Intel result is produced by this ARM-only run.

## Actual unsigned iOS compile

The native helper selects process-local Xcode 26.3 build 17C529 with iPhoneOS SDK 26.2 after a real unsigned arm64 link probe forces all five previously missing SDK globals. The probe exits 0. The default Xcode selection is not globally changed. Raw compiler/linker output contains actual arm64 CompileC at line 370, Ld at line 377, and `** BUILD SUCCEEDED **` at line 432. The build exits 0 after 50.010253 seconds; total qualification is 86.440190 seconds within the original 900-second bound. All fifteen owned command receipts have complete cleanup, no timeout, unexpected descendant, cleanup error or surviving process.

The native app inspection attests an unsigned 102,344,664-byte arm64 device-iOS MH_EXECUTE, no signature load command, no signature directory and no embedded profile. Its SHA256 is `a7f7a42a37cc137f4f78e65d9e65f8ae6c79451b509bb21950b9fd14b05b7463`. The separate built PCK SHA256 `0b2e60a7d544af2b6701b3c8f120145abda7d1fad72cf2baf0e12c7196b7ca7b` matches the exact exported-source receipt and 132 integrated resources. Codesign exits with the expected 1 and says the code object is not signed at all. Clean before/after source snapshots agree exactly. This preserves the bounded unsigned compile result on the new source; an unchanged native wrapper hash does not relabel the old PCK as this source.

The app and SDK-probe executable bytes are outside the bounded QA artifacts, so this critic does not independently reparse their Mach-O or PCK bytes. Raw compiler/linker and codesign logs corroborate native helper attestation. Warnings remain for empty camera, microphone and photo-library usage descriptions, `#pragma once`, and skipped AppIntents metadata extraction. Signing, installation, simulator, older OS behavior, runtime, touch, suspend/resume and human/physical-device play remain open.

The first reviewer audit incorrectly required literal SDK-path equality. The actual native receipt first records `iPhoneOS.sdk`, then `iPhoneOS26.2.sdk` under the same developer directory; native resolved-path equality passes. `AUDIT-CORRECTION.md` and the first output preserve that reviewer error. The corrected audit qualifies remote alias resolution as native attestation; no native gate or raw output changes.

## Retained evidence

Official bounded receipts artifact 12403317709 is 674,634 bytes, SHA256 `60d4c831aec80ea19830a363ac808c0de2d59d6c42aeca876d30c075b6a89fbd`. Its inner ZIP is 674,490 bytes, SHA256 `860264ed21f120cbd523a33d04da59d4bb7fee4700fce6fca74a2bbeae611d9b`. All 144 indexed original sizes/hashes and the complete selected file set verify.

Official full QA artifact 12404185338 is 1,313,979 bytes, SHA256 `bdafd4d2f9316c6b2afb1d5a7d1d59446270f6f46a862bf38f7fc9247e924e79`. Its 149 files include seven original PNGs. Every overlapping bounded/full-QA file matches; two frozen-baseline license TXT files are only in the bounded artifact because the full-QA upload includes TXT only at the diagnostic root. Both originals are retained in the bounded ZIP. This is an upload-selection difference, not inferred corruption.

Both artifacts use supported connector/Sediment downloads below 32 MiB and safe ZIP extraction. The 289,791,801-byte development artifact exceeds that transfer cap and is not requested; its official digest remains in metadata. The decoded connector job log is preserved exactly as received, 175,849 UTF-8 bytes, 2,278 LF / zero CRLF, SHA256 `627666470b8e207121b78d89b3e47bf1679eca2bc127fb9c723b35ef2337f814`. It is decoded connector text, not an original GitHub log archive. Raw receipts are actual transferred files, not result JSON reconstructed from stdout.

The review retains exact briefs, declared criteria, source reconstruction, original ZIPs, raw metadata/logs, corrected and first-attempt audits and byte inventories. No implementation edits, native/OCR workload, permission request, input event, external comment, merge, push or publication occurred in this review. No G1, Mac release, human-play, physical performance or full visual-quality gate is closed.
