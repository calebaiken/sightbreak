# Independent iOS compile implementation review

Scoped approval: candidate `ac3cfdefa9e6115d7a125903061724b1578e42c6` is suitable
for an actual ARM macOS CI attempt. No blocking implementation defect was found.
This is implementation readiness only. No Xcode command, Apple compiler or linker,
signing operation, installation or mobile execution ran in this review.

The fresh `mobile_package_critic` agent reviewed the declared criteria, helper,
controls, unchanged exporter/toolchain/structural verifier, QA packer and actual
workflow on 2026-10-22. No child agents or implementation edits were used.
The exact task and follow-ups are retained in `brief.txt`.

## Source and method

The requested `6b78185` candidate received two narrow builder follow-ups during
review: bounded source snapshots at `571e8c7`, then SIGTERM handling at `ac3cfde`.
The builder confirmed the latter frozen. All final controls ran on an independent,
clean detached checkout at `/workspace/reviews/ios-compile-critic/source571e8c7`.
The directory name records its initial snapshot; its actual reviewed HEAD is
`ac3cfde`. `source-files.json` binds all inspected implementation files to their
SHA-256 hashes, and `actual-source-snapshot.json` retains the real clean-source
snapshot emitted by the candidate CLI.

The benchmark is the seven explicit conditions in
`docs/reports/gauntlet/m2-ios-compile/CRITERIA.md` at that commit, plus the existing
source/payload, unsigned export and resource-inspection contracts. Linux controls
can assess rejection, process ownership and evidence handling. They cannot satisfy
the native compiler result required by criteria 2–5. No visual score applies.
The app-validator fixtures reuse the preserved PCK and source receipt from the
earlier frozen `6a0d8d5` mobile export. Their app headers are synthetic; this is
test data, not an export or compile of the new candidate.

## Observed checks

All 40 candidate/existing tests pass independently: ten iOS helper controls,
24 source-manifest controls and six QA receipt-package controls. All 26 additional
critic controls pass. `commands.json`, logs and executable critic control sources
retain the commands and results.

| Area | Evidence and conclusion |
| --- | --- |
| Source binding | Real clean CLI snapshot succeeds. Disposable Git fixtures reject untracked source dirt and changed validation scripts; validation changes alter the hash. Helper takes clean snapshots before export and after compile, compares source identities, and rechecks the exported payload after build. |
| Native identity and pins | Implementation requires actual Darwin/ARM64, records selected Xcode/developer path/iPhoneOS SDK/Apple clang, verifies cached template archive SHA-512, then runs the pinned setup/export tools. Actual Linux invocation exits 1 with FAILED receipt and no Apple/export commands. These branches still need native observation. |
| Device discrimination | Independent app fixtures carry the actual preserved 132-resource PCK. ARM64 device header passes; ARM64 simulator and x86_64 headers fail. Simulator plist identity and incorrect bundle/version/build/executable fields fail. |
| Signing state | Zero-size `LC_CODE_SIGNATURE`, nested `_CodeSignature`, embedded profile and symlinked executable are rejected. Generic `Apple Development`/`Apple Distribution` project selector strings are not actual signing identities. The compile command disables signing and does not permit provisioning updates; actual `codesign -d` failure is required for success. |
| PCK provenance | Same-size one-byte mutations in built and exported PCKs fail. Duplicate manifest PCK provenance fails. Existing controls additionally cover missing, duplicate and symlinked app PCKs. |
| Owned process cleanup | Real timed-out leader plus TERM-resistant child, and zero-exit leader with child output closed, leave no live fixture child and no delayed marker. Injected `killpg` denial retains timeout/cleanup failure. Existing controls also reject failed cleanup diagnostics and preserve nonzero command exits. |
| Cancellation | A real subprocess invoking the candidate CLI receives SIGTERM during a fixture source command. Its owned child stops; the CLI exits 1, retains the raw partial log, and writes `compile_completed=false`, `status=FAILED`. Apple host values and the source command were explicitly synthetic for this control. |
| Workflow | YAML parses. Exactly seven workflow lines were added; existing tests, diagnostics and packaging remain. iOS controls and qualification follow diagnostics on `macos-15`, use `always()` after successful desktop export, and do not depend on another qualification passing. Compile step has a 17-minute timeout; helper command budget is 900 seconds. |
| QA bounds | Real packer fixture retains logs/JSON and excludes native files injected in the receipt tree plus sibling DerivedData payloads. Actual iOS export and DerivedData paths are outside `desktop-playability`; helper copies only four receipt/log files. Existing 30 MiB bound tests pass. |

The first independent control harness stopped when an expected manifest rejection
raised `SystemExit`, which its exception list omitted. That is a review-harness
error. The critic retained the partial attempt in `control-harness-round0/`, added
the expected exception type, and reran all independent controls successfully in
`independent-r1/`. No candidate change was needed.

## Remaining evidence limits

One observed, non-blocking cancellation gap remains: a SIGTERM-interrupted command
does not return its local cleanup record to `run()`. In the exercised case,
`compile.json` has `commands=[]` although `source-before.log` exists. The overall
receipt is FAILED and the critic independently confirmed that the child stopped;
this gap cannot create a false PASS. Persisting the command/cleanup record through
the interrupted path would make cancellation evidence easier to audit.

Two assumptions require actual native output before acceptance:

- Compiler/linker detection requires a linker log line matching `^Ld .* normal arm64`.
  A valid Xcode build whose log omits `arm64` on that line would fail qualification.
  No available native log establishes whether this candidate's Xcode does so.
- The verifier rejects any `LC_CODE_SIGNATURE`, even an empty/ad-hoc one, and
  requires `codesign` to say the app is unsigned. This matches the declared strict
  unsigned criterion. The signature state produced by this actual iPhoneOS linker
  with `CODE_SIGNING_ALLOWED=NO` has not been observed here.

Keep these checks intact until the Mac run supplies evidence. If it fails, retain
the first raw compiler/linker logs and inspect the actual Mach-O load commands
before deciding whether the failure is product, tooling or verifier behavior.

The upstream simulator mismatch stays open and separate: its framework metadata
advertises ARM64+x86_64, while the previously inspected pinned simulator archive
contains x86_64 objects only. Device ARM64 archive presence does not establish an
actual compiler/linker success.

The next evidence required is a source-bound ARM macOS run of the registered
workflow, then independent review of `compile.json`, `xcodebuild-device.log`,
exported source/inspection receipts and the actual output inspection. Xcode
compilation, simulator support, signing, installation, runtime, touch,
suspend/resume and physical iPhone/iPad qualification remain UNVERIFIED. G14 stays
IN PROGRESS.
