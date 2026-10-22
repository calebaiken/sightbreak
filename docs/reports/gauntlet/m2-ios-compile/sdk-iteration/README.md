# Device SDK correction

Status: IN PROGRESS. The first actual unsigned game compile failed. The SDK
selection correction has Linux fixture coverage and still needs independent
review followed by a new actual ARM Mac attempt.

[Run 39719407304](https://github.com/calebaiken/sightbreak/actions/runs/39719407304)
at clean source `0ca125dfba637868e6e8e9772ff9c40400413e32` reached the compiler
and linker. Its default Xcode 16.4/iPhoneOS 18.5 SDK could not resolve four
`CADynamicRange*` globals and `MTLTensorDomain` from the pinned Godot archive.
`xcodebuild` exited 65 after 36.095 seconds; the full qualification attempt
lasted 61.983 seconds. [Original receipt and raw output](failure-0ca125d) retain
that failure and exact source identity.

The run's [image header](runner-image-header.txt) identifies
`macos-15-arm64/20260907.0337`. Its exact [software manifest](runner-software.md)
lists installed Xcode 26.3 with iPhoneOS 26.2, plus 26.2, 26.1.1 and 26.0.1.
The retrieved manifest's blob and URL are in [source metadata](runner-software-source.json).

Apple WebKit's SDK database marks the missing globals as introduced in iOS 26:
[QuartzCore](https://github.com/WebKit/WebKit/blob/efcd462e778e604404747a985b6023a314edb241/WebKitLibraries/SDKDBs/iphoneos/QuartzCore.partial.sdkdb#L115)
and [Metal](https://github.com/WebKit/WebKit/blob/efcd462e778e604404747a985b6023a314edb241/WebKitLibraries/SDKDBs/iphoneos/Metal.partial.sdkdb#L1899).
The exact excerpts and blob identities are [retained](apple-sdk-symbol-evidence.json).

The correction inventories actual installed Xcodes, tries newer versions first,
and uses each candidate only through child-process `DEVELOPER_DIR`. A tiny
device executable must link all five strong symbols with QuartzCore and Metal.
Apple's linker `-u` requires resolution; `-no_adhoc_codesign` keeps the probe
unsigned. Its command, source, SDK path, exit and arm64 device Mach-O inspection
are retained. No compatible candidate stops preflight before game export.
The selected Xcode/SDK/compiler identities are then recorded and used for the
unchanged game export and unsigned build. The original 900-second shared budget
and checksum-pinned engine remain unchanged.

The original native linker action was `Ld ... normal (in target ...)`, so the
action parser now accepts that observed form. A compiler action, build-success
marker, exit zero and independent final-app architecture/platform/signing checks
remain mandatory. The retained failed log is a negative fixture; it cannot pass.

Fourteen Linux controls pass, including SDK fallback/environment isolation,
no-compatible failure, wrong-platform probe rejection and the native-log
regression. Existing process cleanup, signing, Mach-O and PCK controls also pass.
These fixtures do not establish actual SDK availability or game link success.
The separate simulator mismatch, final app signature state and physical-device
runtime qualification remain open.
