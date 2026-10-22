# iOS device compile candidate

Status: IN PROGRESS. The first native Xcode compilation failed against the
default iPhoneOS 18.5 SDK. The [SDK correction](sdk-iteration/README.md) retains
that exact-source failure and needs a new ARM Mac attempt. The build gate
remains unverified. [Declared criteria](CRITERIA.md).

`qualify_ios_compile.py` exports a fresh unsigned project using the template
archive already cached by native setup, checks that archive's pinned SHA512,
runs the existing structural verifier, and invokes generic-device Debug
`xcodebuild` with `CODE_SIGNING_ALLOWED=NO`. The original exporter and signing
sentinel removal are unchanged. The helper requires actual compiler/linker
actions and inspects the resulting unsigned arm64 device executable, app
metadata and exact source PCK. No archive, IPA, signing or publishing step runs.

The registered desktop workflow adds this after the existing Mac regressions
and diagnostics on `macos-15` only. Exported native payload and DerivedData live
in separate ignored build directories. `desktop-playability/ios-compile` holds
only receipts and raw logs, including failed attempts; the existing bounded QA
packer includes those files without compiled libraries.

Linux controls pass: ten new process/binary/provenance fixtures, 24 existing
build-manifest controls and six existing QA-package controls. Raw outputs are
in [controls](controls). They verify the helper's failure handling and fixtures;
they do not establish an Apple SDK build. No game, actor, match, export preset,
signing identity, provisioning profile or credential configuration changed.

The largest gap is the missing actual Mac compile result. The separate upstream
simulator debug archive mismatch remains open, as do installation and physical
iPhone/iPad qualification.

Next command, after independent implementation review and integration on a clean
source, is the already registered workflow:

```sh
gh workflow run desktop-alpha.yml --repo calebaiken/sightbreak --ref codex/v1-mission-playability
```

Review `ios-compile/compile.json`, `xcodebuild-device.log`, the copied exported
source record and project inspection receipts from the ARM Mac QA artifact.
An implementation review or Linux green controls cannot close this gate.
