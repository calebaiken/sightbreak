# Mac CI outcome review

Frozen candidate: `0ca125dfba637868e6e8e9772ff9c40400413e32`.
Run: https://github.com/calebaiken/sightbreak/actions/runs/39719407304.
Reviewer is separate from the builders and runs no local renderer or product modification.

The unchanged shipping startup gate requires the exported default-graphics menu within 120 seconds and a captured menu. Intel and ARM hosts remain separate. Minimal graphics controls and grouped feature ablations diagnose startup; they cannot replace that gate, prove gameplay, or measure physical GPU performance.

Feature traces must parse to frames 1 through 15 in order, use the named case, keep nondecreasing timestamps, exit cleanly and retain a decoded PNG. A completed `frame_post_draw` is Godot's completed viewport-render phase, not display presentation or a measured GPU fence. Old game readiness follows 15 process frames; an absent old marker cannot establish zero completed draws. Ordered cases share cache identity, so durations cannot establish a causal speed improvement. A passing ablation with failing full requires a warm full reference and the implicated case before proposing a shipping correction.

Native source suites require native per-suite user-directory receipts, clean logs, unchanged source and private copied resources, and confirmed cleanup. They do not prove exported or physical-input gameplay. The current maintained list has ten suites, including authority order.

iOS requires clean exact source before and after export/build; native ARM macOS, Xcode, iPhoneOS SDK, Apple clang and template checksum; successful structural export; real CompileC/SwiftCompile and Ld actions plus BUILD SUCCEEDED; unsigned arm64 device-iOS Mach-O and a source-identical PCK; clean bounded-command cleanup. The helper is unchanged from reviewed ac3cfde. Native linker log formatting and strict signature state remain outcome questions. The uploaded evidence excludes the app/DerivedData, so binary reinspection is limited if no separately downloadable payload exists.

The simulator metadata/archive mismatch remains separate from device compilation. Signing, installation, runtime, touch, suspend/resume, physical iPhone/iPad, human play and release acceptance require distinct evidence and stay unverified here. G13 and G14 cannot be closed from these startup/compile slices alone.

`source/source-files.json` binds frozen criteria and implementation snapshots. The iOS implementation review was added after the frozen candidate and is recorded separately under `source/later-review/`, with the checkout identity from which it was read.
