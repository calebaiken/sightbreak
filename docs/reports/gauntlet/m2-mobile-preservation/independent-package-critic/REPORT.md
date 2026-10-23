# Independent mobile package review

The Android debug APK and unsigned iOS project satisfy the frozen source's defined
artifact inspection criteria. One supplemental check fails: the pinned iOS template
declares an ARM64 simulator slice that its static library does not contain. This
review qualifies export construction and inspection at `6a0d8d5`; it does not close G14.

Reviewed on 2026-10-22 by the fresh `mobile_package_critic` agent. The builder supplied
the artifacts; the critic independently read their contents and recomputed hashes.
No build, signing, installation, cache/key/config change or child agent was used.

## Source and benchmark

- Frozen checkout: `/workspace/sightbreak-v1-mobile6a`, clean before and after review.
- Commit: `6a0d8d5d85b4fb37943903886982f51b4ed230b0`.
- Game tree: `13079ab8a3de9b18252a652ed57157e0776cf394`.
- Game content SHA-256: `954b0a73cff89483a9270434da7902b2d128f1b9a99c30290dfe03862c038873`.
- Validation SHA-256: `9155b9c6a68fbeb459c4d0654b49ec4b250d1e11bea667747dfc4056e1ea2f03`.
- Artifact tree: `builds/mobile-preservation` in that checkout.
- Raw review: `/workspace/reviews/mobile-package-critic`.
- Documentation base: `3968f47293fea5d52172b18d9cb1e0cf453f98d1`.

The inspected benchmark is the frozen `scripts/build_manifest.py` source/payload
contract, `game/export_presets.cfg`, and Android/iOS branches of
`scripts/verify_builds.py`, under the mission's pinned Godot 4.7.2 and G14 requirement.
The critic also checked native object architecture, pinned template identity,
ZIP alignment, PCK data integrity and cross-platform compiled scripts. A visual
score and blind presentation comparison do not apply to these correctness checks.

## Results

`inspection-results.json` records 49 checks: 48 pass and one supplemental check
fails. The independent runner exits 1 to keep that finding visible.
`defined_benchmark_passed` is true; `passed` is false. The builder's retained
`verify_builds.py --targets android ios` receipt separately reports success.

| Area | Independent observation |
| --- | --- |
| Source binding | Recomputed both canonical digests and Git identities; both source receipts match the frozen clean source. |
| Payload inventory | All 54 manifest payload files match their SHA-256, byte count, filesystem mode, delivery mode and exact file set. No symlinks or private signing material found. |
| Toolchain | Editor ZIP and template TPZ match `toolchain.py`'s SHA-512 pins; installed editor and cached Android/iOS templates match those archives. Editor reports `4.7.2.stable.official.ed1daf0bf`. |
| Android identity | `com.sightbreak.game`, version `0.3.3-dev`, build 6, min SDK 24, target SDK 36; landscape activity, exported launcher and network permissions present. |
| Android signing | `apksigner verify` passes v2/v3 with the `CN=Android Debug, O=Android, C=US` certificate. This is a debug artifact. v1/v3.1/v4/SourceStamp report false; none is claimed. |
| Android native payload | Exactly ARM64-v8a and x86_64. Both Godot and C++ libraries have the expected 64-bit ELF machine values and match the pinned debug template. |
| Android container | 234 ZIP entries; CRCs, unique names and 16 KiB page alignment check pass. 134 asset entries include required compiled modules and imported model/texture payloads; no test harnesses or credentials found. |
| iOS resources | PCK format 4 declares Godot 4.7.2; all 132 resource entries pass bounds and MD5 checks and have unique paths. Required compiled modules and imported payloads are present; no test harnesses found. |
| Shared scripts | All 38 `.gdc` files match byte for byte between Android and iOS. Platform project/scene serialization differs; byte identity is not claimed for the whole export. |
| iOS metadata | Bundle ID, 0.3.3/build 6, iOS 15 minimum, phone/tablet family, landscape declarations and local-network explanation match the contract. |
| iOS unsigned state | Team and provisioning fields are empty; no sentinel, certificate/private key, profile, built app, IPA or code-signature directory is bundled. Generic `Apple Development` and `Apple Distribution` selector strings remain in the template project. They are not actual signing identities. |
| iOS device engine | Debug archive matches the pinned template and contains 2,357 ARM64 Mach-O objects plus its symbol table. |
| Logs | No retained import/export/inspection engine or Python error lines. iOS retains warnings about `application/boot_splash/fullsize`, the macOS-only IPA step, and export completed with warnings. They remain recorded in `builder-log-review.json`. |

Principal artifact hashes:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Android debug APK | 67,478,013 | `101ca9466cc89731c3d5c488f8635511105c2d6833ab7b5569feb3319ac85d58` |
| iOS `project.pbxproj` | 15,914 | `e498a79552f3cf85be7050697b99befeaf253ca79fcb9b941d42db5549afed18` |
| iOS game PCK | 10,518,172 | `e006ce4ffee64d8cd5c3386e8a1116231409504b6e25034a984218434280dc98` |

## Open finding

The exported `sightbreak.xcframework/Info.plist` and pinned debug template declare
the simulator library as `ios-arm64_x86_64-simulator`, with `arm64` and `x86_64`.
Every one of its 2,292 Mach-O object members is x86_64; no ARM64 object is present.
The archive's SHA-256 is
`9ee798cee5dc9164490b50ed74a191dd784faa8651e27f10c247c92a6a2d120e`.
It byte-matches `libgodot.ios.debug.xcframework/ios-arm64_x86_64-simulator/libgodot.a`
inside the pinned `ios.zip`. This is an upstream template metadata/payload mismatch,
rather than evidence of local payload tampering.

Do not claim ARM64 simulator support from this export. An actual Xcode simulator
build is needed to determine the observed failure and the proper correction. The
ARM64 device archive is present; this finding alone does not prove a device build
failure. Leave the frozen artifacts intact and investigate in a separate attempt.

The first supplemental parser assumed the simulator file was a fat archive. It is
a BSD `ar` archive. The critic retained that failed attempt under
`parser-assumption-round0/`, corrected the parser to inspect every member's Mach-O
CPU type, and reran. The retained final evidence establishes the mismatch without
the initial format assumption.

## Reopen and limitations

The exact brief is in `brief.txt`; executable review logic is in `inspect.py`;
native command arrays, working directory, exit code and log names are in
`commands.json`. To repeat without writing into the frozen checkout, copy
`inspect.py` to a new empty review directory and run it with Python 3 while the
original local source/artifacts/tools remain available. Expected current exit is 1
for the supplemental simulator finding. No setup, export or signing command runs.
The final runner also imports the frozen `validate_record`, `no_test_harnesses`
and `integrated_resources` checks with bytecode writes disabled; all pass in
`frozen-benchmark-readback.log` without replacing the builder's verification logs.

Physical Android installation, startup, actual play, touch ergonomics, GPU timing,
suspend/resume and LAN permission behavior remain UNVERIFIED. macOS/Xcode iOS
compilation, signing, installation, startup, play and device behavior remain
UNVERIFIED. No emulator/device or compiler was available. No distribution ZIP,
archive reproducibility or later-source compatibility is claimed.

The largest remaining qualification gap is actual Xcode compilation and mobile
device execution. G14 stays IN PROGRESS with those external checks blocked.
