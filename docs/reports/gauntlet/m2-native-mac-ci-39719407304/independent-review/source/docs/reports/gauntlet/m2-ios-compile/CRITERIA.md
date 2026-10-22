# iOS device compile qualification

Declared before implementation on 2026-10-22. Starting source:
`3968f47293fea5d52172b18d9cb1e0cf453f98d1`.

The comparison is the existing unsigned-project structural gate in
`scripts/verify_builds.py`, which cannot establish a compiler or linker result.
This increment must retain that gate and obtain the missing native result on
the existing authorized public-repository ARM macOS runner.

Acceptance requires all of these:

1. A clean exact commit, game tree, content hash and validation hash remain
   unchanged throughout export, inspection and compile.
2. The runner records native ARM macOS, selected Xcode, iPhoneOS SDK, compiler,
   and the cached Godot 4.7.2 template archive's pinned checksum.
3. A fresh `SIGHTBREAK_BUILDS_DIR` passes `scripts/export.py ios` and
   `scripts/verify_builds.py --targets ios`. Existing unsigned sentinel removal
   and checkout signing settings remain unchanged.
4. Real `xcodebuild` runs the exported project for generic iOS device, Debug,
   with `CODE_SIGNING_ALLOWED=NO`. Its compiler and linker actions execute,
   the command exits zero, and it reports build success.
5. The resulting app has the expected identity/version, source-identical game
   PCK and integrated resources. Its executable is unsigned arm64 Mach-O for
   device iOS, with no code signature, signing directory or embedded profile.
6. Every command has a bounded timeout within one total deadline. Owned process
   groups are reaped or their cleanup failure fails qualification. Failure
   receipts and raw command logs remain available without a success claim.
7. The desktop workflow still runs the existing tests and diagnostics. iOS
   compilation runs on ARM `macos-15` after those steps even when another
   qualification fails. Only logs and JSON receipts enter the bounded QA pack;
   exported/compiled native libraries stay outside it.

Linux fixture tests must exercise timeout/descendant cleanup and binary/platform
and PCK rejection. They cannot satisfy the native build gate. A separate critic
must inspect the implementation and actual Mac evidence before verification.

This is device compile qualification only. The cached upstream simulator
framework advertises arm64+x86_64 while its debug archive inspected on Linux
contains x86_64 only. That remains a separate simulator limitation; it does not
establish a device compile failure. Signing, installation, execution, touch,
suspend/resume and physical iPhone/iPad qualification remain unverified.
