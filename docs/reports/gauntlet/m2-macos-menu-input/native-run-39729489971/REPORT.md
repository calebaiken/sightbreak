# Independent native ARM Mac menu outcome

REJECT native menu-navigation acceptance for
[run 39729489971](https://github.com/calebaiken/sightbreak/actions/runs/39729489971),
the single `native (macos-15, macos)` job 119661018459. The actual result is
`FAILED`, after 25.950 s. Its exact failure is:

> Public NSRunningApplication activation did not produce exact foreground PID

The new run is better diagnostic evidence than the accepted
[e7718ee bounded readiness](../../m2-macos-input/native-run-39727011693/REPORT.md):
it establishes the first native Swift compilation and a concrete foreground
failure. Proven input capability remains at the prior zero-event readiness
boundary. There is no menu-navigation win or comparable blind image pair.

The largest remaining gap is obtaining and observing the exact exported
foreground PID through a supported activation path. Capture-helper permission,
full-window pixel geometry and delivered Settings/Escape navigation remain
unreached. Preserve the focus guard and this failed native attempt.

## Source and export

Exact source is `3b97a0043fc415c2408ed774f38710ac022cfd72`. Independent hashing
of immutable Git bytes reconstructs game tree
`e877ba16bdc7f63994930a77f32e484e8f12d890`, content SHA256
`db3c976711ef8d91b75604fdfe05309599445cfc5bdf59e5f6fbdf669a859fc5`
and validation SHA256
`9886d8d90e3499936798c6169f0c2664912033f6dd590fdb0a26ccf47f9becba`.
Manifest, startup, preflight, menu and diagnostic receipts agree. All source
snapshots are clean and final source/export checks pass by native receipts.

The eight reviewed driver/helper/guard/workflow files match source `800d36c`
byte-for-byte and match its recorded hashes. Product `main.gd` and
`input_mode_test.gd` changed through the intervening HUD integration. A separate
static reviewer found unchanged ordinary Settings/Escape/save boundaries; this
run correctly used its own export/preflight. Earlier rejected aa309a1 boundary
probes and intermediate fixes remain in [independent-review](../independent-review/REVIEW.md).

The desktop executable descriptor is SHA256
`f74664e481b1f71e681dd5404f12cc98c135697335897ee2a01974b3ba4114b4`
in both preflight and menu results and their matching export descriptors. The
289,930,176-byte development artifact exceeds the32 MiB transfer bound and was
not requested. These native binary/PCK descriptors were not independently
rehashed from transferred executable bytes.

## Native attempt and refusal

Fresh preflight passes on macOS 15.7.9 arm64, Godot 4.7.2. All four queried
permissions are true. It records PID 3571/window 35, full-window bounds
`[40,32,960,568]` points, and an internal 960×540 viewport PNG with matching
SHA256. Normal exit 0, absent profiles and cleanup agree. This is a separate
smoke launch, with zero events and no OS screenshot/focus qualification.

The actual menu driver again reports all four controller permissions true.
It compiles the Swift source with `xcrun swiftc -parse-as-library
-swift-version 5 -target arm64-apple-macos14.0` and the declared public
frameworks. The original compiler log is empty; the compiler child exits0.
The recorded source hash
`af6576bbda2deac290a418cdbf0fef8894376372e934d617ee2bc1bdecb524b9`
matches the exact Git object. The native helper executable descriptor is
`a98bf9f5672aa2d5de5b8b2f0217a71b7858547dd835c1d9575e002655011296`.
The helper binary is omitted from both QA archives, so that executable hash
remains a native receipt rather than an independently rehashed file.

The ordinary exported client launches as PID 3996. The required foreground PID
is not observed during the adapter's five-second activation poll. Final native
diagnostics show foreground 3721 and target 3996, pointer `[10,10]`, button up,
Escape up and no driver-held controls. The failed activation request's return
value and selected window ID/bounds were not retained. The separate preflight
PID 3571/window 35 must not be relabeled as this client's window.

The sole action is the compiler command. Post attempts are 0 before and after
cleanup; captures are empty. No helper invocation, helper permission receipt,
ScreenCaptureKit geometry, original OS-window PNG, Vision box, pointer move,
button state transition or Escape state transition exists. Its own capture
permission is unobserved, with no evidence of denial. The observed failure is
foreground activation, not a compiler or permission failure.

Original [results](full-qa/macos-menu-input/results.json),
[actions](full-qa/macos-menu-input/actions.json),
[compiler log](full-qa/macos-menu-input/compile-capture-helper.log),
[client log](full-qa/macos-menu-input/client.log) and
[engine log](full-qa/macos-menu-input/engine.log) retain the attempt.

## Profiles and owned cleanup

The public ordinary termination request is accepted and PID 3996 exits0 within
its separate failure-close budget. Compiler PID 3728 and client PID 3996 are both
gone, with no SIGTERM/SIGKILL sent. Final owned release is empty, native button
and Escape states are up, and release errors are empty.

Both canonical profile entries remain absent/unchanged. Independent comparison
finds identical before/after native inventories,86 files and32 directories, for
both preflight and menu attempt. The before/after inventory has no created, removed or changed native entries. This
is a warm-directory observation; native cache bytes were not transferred and
concurrent input/write or hard-kill safety remains outside the evidence.

## Other native outputs

Exact frozen-source suite order is derived from its `SUITES` AST. Raw
summaries give actor 73, match 75, authority 178, privacy 55, movement 725,
lifecycle 16, input 462, focus 30, diagnostics 60, HUD 33, provenance 32 and
bot 2722:12 suites,4,461 assertions,0 failures. All exits/logs pass. An independent
reviewer checks all 307 isolation resource hashes against source Git objects,
24 before/after native producer receipts and41 retained produced-file hashes.
Source/copied resources are unchanged; owned namespace and temporary project
are removed. The separate HUD fixture reports owned/removed/caller restored.

Headless menu/demo and graphical menu startup pass. All five diagnostic trials
pass; their original PNG hashes match. All seven transferred PNGs were directly
inspected and have valid dimensions. They are internal rendered captures from
other startup/diagnostic paths, with no FIELD SETTINGS transition or helper
geometry. The host uses automatic ANGLE on an Apple paravirtual device; these
images do not establish physical GPU behavior or performance.

The separate iOS output supports unsigned generic-device Debug compile/link.
Independent raw review confirms Xcode 26.3/iPhoneOS 26.2, one CompileC, four
SwiftCompile, one Ld, BUILD SUCCEEDED, no CodeSign action, and 15 command cleanup
receipts without survivors. Codesign exits 1 with unsigned status. Source/PCK
descriptors agree with the exported project; executable/PCK bytes were not
transferred. Camera/photo/microphone usage-description warnings are retained.
Installation, runtime and simulator remain unverified.

## Evidence transfer and replay

Official full-QA artifact 12404428943 is 1,410,807 bytes, SHA256
`39fd1bcccf0e8dc3c98eee0a2cfb5c29f4aa280ceee6e4bf964865fed015fe90`.
Official receipt artifact 12404428936 is 1,628,280 bytes, SHA256
`9ae3ff896e0dd162b9ac6b4f42649324d91631f7d582f395c4d069308bdbea6b`.
Supported connector/Sediment transfer preserves both originals under
[archives](archives). Safe extraction rejects unsafe paths, links, duplicates
and excessive expansion. All 165 indexed receipts match their original sizes
and hashes. Full-QA has 170 files; all 163 shared receipt files match exactly.
Seven full-only files are PNGs; two receipt-only files are frozen license texts.

[Final workflow metadata](final-jobs.json), [artifact metadata](final-artifacts.json),
[decoded original connector log](job-119661018459.log), [source reconstruction](source-reconstruction.json),
[recomputation](recomputed.json) and [full-QA cross-check](full-QA-crosscheck.json)
are permanent evidence. The job log is decoded connector text, not an original
GitHub log ZIP. A running-job log 404 and an initial signed-URL transfer 403 are
retained as retrieval failures; the supported workspace transfer then succeeds.
No denied host was retried through an alternate network path.

Replay performs only file/Git-object reads:

```sh
python docs/reports/gauntlet/m2-macos-menu-input/native-run-39729489971/recompute_source.py /workspace/sightbreak-mac-menu-native-review --output /tmp/mac-menu-source.json
python docs/reports/gauntlet/m2-macos-menu-input/native-run-39729489971/audit_receipts.py docs/reports/gauntlet/m2-macos-menu-input/native-run-39729489971/receipts --checkout /workspace/sightbreak-mac-menu-native-review --source /tmp/mac-menu-source.json --output /tmp/mac-menu-audit.json
```

This critic ran no implementation, engine, OCR, compiler or native API and made
no implementation change. Menu input, aim, firing, complete matches, human play
and physical-device qualification remain open.
