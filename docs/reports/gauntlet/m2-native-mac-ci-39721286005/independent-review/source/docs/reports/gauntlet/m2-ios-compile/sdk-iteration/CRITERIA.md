# SDK correction criteria

Declared before implementation on 2026-10-22, after actual ARM Mac run
39719407304 at exact source `0ca125dfba637868e6e8e9772ff9c40400413e32` failed.
The retained receipt binds that failure to its clean source and pinned engine.
Xcode 16.4/iPhoneOS 18.5 compiled the wrapper and failed the actual arm64 link
with exit 65; its SDK lacks five globals required by the pinned Godot archive.
This is separate from the upstream simulator archive metadata limitation.

The exact runner image `macos-15-arm64/20260907.0337` documents installed
Xcode 26.0.1, 26.1.1, 26.2 and 26.3 alongside default 16.4. Apple WebKit SDKDB
records the five missing globals as introduced in iOS 26. Runtime inventory
and a real device link probe must establish which installed SDK can supply them.

Acceptance for this correction:

1. Preserve the failed source receipt, raw compiler/linker log and runner image
   identity. Do not promote this failure to a successful compile.
2. Enumerate installed Xcodes and probe candidate SDKs within the unchanged
   900-second total budget. Use process-local `DEVELOPER_DIR`; never change
   global Xcode selection, install Xcode, rebuild or replace pinned Godot, or
   read signing keys.
3. A tiny unsigned arm64 device-iOS link must strongly reference all five
   missing symbols against QuartzCore and Metal in the selected SDK. Retain
   each attempted command, exit, SDK identity and failure log. If none links,
   stop before the game export/build with an explicit failed preflight receipt.
4. Record the selected actual Xcode, compiler and iPhoneOS SDK identity and use
   the same process environment for all subsequent export/verify/build commands.
5. Recognize the real native `Ld ... normal (in target ...)` action format.
   Still require compiler action, exit zero, build success and independently
   inspected final app Mach-O arm64/device-iOS metadata and absence of signing.
6. Linux fixtures must reject missing-symbol probes and failed native logs,
   verify environment isolation/fallback/no-compatible failure, and preserve
   existing timeout, source PCK, binary and signing controls. These fixtures do
   not establish the final game compile; a new native attempt remains required.

No workflow edit, signing change, timeout increase or simulator workaround is
part of this iteration. A separate critic must review this correction before
the next native attempt.
