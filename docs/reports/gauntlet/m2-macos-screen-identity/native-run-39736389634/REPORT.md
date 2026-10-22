# Independent native ARM screen identity outcome

ACCEPT the new bounded menu result, `PASS_MENU_NAVIGATION_ONLY`, at exact
source `20464da`. Fresh OS pixels, exact screen roles, foreground observations,
five event attempts, native button/Escape acknowledgments and ordinary cleanup
all agree. This improves on b09cfe1's manually observed navigation and failed
automatic home observation. The prior b09 run remains FAILED; its stored JSON
fixtures do not qualify this new run.

The whole ARM job remains **FAILED**. The first strict source suite, actor,
reports 73 assertions/0 failures and exit 0, then six leaked ObjectDB instances.
The other 11 suites are unreached. The input-mode-only verbose diagnostic correctly
skips; no native verbose repeat or leaked-object type is available.

The largest remaining gap is obtaining actual type/allocation evidence for this
strict actor leak and resolving it without changing the clean-log requirement.
No cause is inferred from its count or from the prior input-mode warning.

## Actual job scopes

[Run 39736389634](https://github.com/calebaiken/sightbreak/actions/runs/39736389634)
has one job 119682963783, native macos-15, overall failure.

| Actual component | Result and limit |
| --- | --- |
| Exact-source export and ordinary preflight | PASS; preflight alone posts no events |
| Owned background capture | PASS_CAPTURE_ONLY_NO_FOCUS_OR_INPUT; Godot splash pixels |
| Exact foreground and menu pointer/Escape journey | PASS_MENU_NAVIGATION_ONLY on this hosted ARM session |
| Strict native source suites | FAILED at actor; 73/0 assertions, exit 0, six ObjectDB leaks |
| Failure-only input-mode verbose repeat | SKIPPED_DIFFERENT_OR_UNPROVEN_FAILURE; no repeat |
| Five default graphical diagnostics | PASS startup/capture only |
| iOS generic-device Debug compile/link | PASS unsigned; installation/runtime/simulator unverified |

## Source, export and helper identity

Exact source is `20464dae1de36eb28f5db04fb6f51f5ff6b6e2ad`. Independent
Git-object reconstruction gives game tree
`fb6be859e05812d8707be1ef5c6f747d2588c1e9`, content SHA256
`f148106d4ed189f2a5d49e798f55bf0fb30f612126ec203037377f88d332855e`,
validation SHA256
`be4914a8b0376e5985c16815742d813690bcfce6a734023d1607e8163dd927b4`.
Fresh export, manifest, startup, preflight, menu, diagnostic and iOS identities
match. Their source snapshots are clean and final checks are unchanged.

Fourteen relevant Mac/helper/guard/control/workflow files match reviewed `a866c73`
byte-for-byte. The game tree is also unchanged. Post-review code differences
concern offline capture fences, fixtures and validation registration. The new
actual native receipts bind `20464da`; no earlier build is relabeled.

The source-bound desktop executable descriptor is
`c5906f40853d10145656d04675609c233957cb3786f1ec442b795b4fee280396`
in both preflight and menu results. The 290,719,451-byte development artifact is
over 32 MiB and was not requested. Full executable/PCK bytes remain untransferred.

Swift compilation exits 0 with its original empty log. Helper source SHA256
`af6576bbda2deac290a418cdbf0fef8894376372e934d617ee2bc1bdecb524b9`
matches Git. The native helper executable descriptor is
`a98bf9f5672aa2d5de5b8b2f0217a71b7858547dd835c1d9575e002655011296`;
that binary is omitted from QA and cannot be independently rehashed here.
All four native capture commands use that compiled helper path.

## Current window, capture and focus

Fresh preflight records PID 10253/window 35 and normal exit 0. All four controller
permission queries are true. Its internal 960×540 capture matches its receipt.
Its identity is separate from the actual menu client.

The menu driver retains client PID 10678, controller PID 10445 and owned visible
layer-zero window 42 before capture/activation. Pinned full-window geometry is
`[40,32,960,568]` points. All four helper receipts have their own capture/post
permission true, zero events and zero requests. CoreGraphics bounds, SCWindow
frame and filter content rect match; scale 1 yields original 960×568 window PNGs.
The titlebar is present, with no guessed offset. This proves the observed 1× host
geometry, with no actual Retina-scale or physical-device qualification.

The pre-activation PNG shows the Godot splash and is correctly capture-only.
It does not supply a home-screen or focus outcome.

One public activation request, options 3, returns true. Raw foreground 344
persists before the recorded public main-run-loop turn. A requested 0.05 s turn
takes 0.193286 s, return code 3; its raw after foreground is 10678. The focus
sample elapsed time is 0.259037 s, followed by fresh guards and a focus-observed
state with the exact target. This meets the unchanged five-second bound.
The observation change does not explain the earlier PID 3996 failure.

## Fresh screen roles and input

I inspected all four original OS-window PNGs directly. Both
[01 home](full-qa/macos-menu-input/01-menu-0.png) and
[03 returned home](full-qa/macos-menu-input/03-returned-menu.png) contain exactly
one qualifying SIGHTBREAK, OPERATOR RECORD and SETTINGS observation. Every
required role has confidence 1, a positive finite normalized in-bounds box and
a distinct exact normalized label. Neither home receipt has FIELD SETTINGS.
The title-bar SIGHTBREAK (DEBUG) is shared and does not count as home identity.

The small masthead is merged to `S/B TACTICAL OPERATIONS` at confidence 0.5 in
these new originals. It remains below the unchanged 0.8 threshold and does not
supply any required role. The current high-confidence hero/control roles are
the actual source of acceptance.

[02 FIELD SETTINGS](full-qa/macos-menu-input/02-field-settings.png) has one exact
FIELD SETTINGS observation, confidence 1, valid box, and no qualifying home
role. The original PNG visibly shows the settings page. The new role audit
uses these fresh native receipts, not the historical b09 fixtures.

The independently computed Settings point is
`[307.93103373474474,478.1381819349307]`; actual OS pointer observation is
`[307.9310302734375,478.13818359375]`. Five ordered attempts are pointer move,
button down/up and Escape down/up. Four combined-session observations acknowledge
button down/up and Escape down/up with foreground PID 10678. Foreground capture
checks confirm home → FIELD SETTINGS → home.

This is actual narrow synthetic OS menu delivery and visible navigation. It
does not qualify movement, aim, firing, a complete match or physical input.

## Menu profiles and cleanup

The menu journey completes in 31.416814 s, requests public ordinary termination,
and exits 0. Compiler, four helper groups and client group are all gone; no
signals are sent. Initial/final controls are neutral and no driver-held control
remains. Post attempts stay 5 after cleanup.

Both canonical profile entries remain absent/unchanged. The native directory's
before/after inventories match exactly for preflight and menu: 86 files and
32 directories. Native files are preserved. These warm-directory snapshots do
not prove absence of transient writes, concurrent-input safety or hard-kill safety.

## Original strict actor failure

The first maintained suite runs this command:

```text
/Users/runner/work/sightbreak/tools/godot-4.7.2/Godot.app/Contents/MacOS/Godot --path /var/folders/nj/vtw8zd2j31d1gdrtntc5y4600000gn/T/sightbreak-native-tests-bh4c1rkz/project --headless --script res://tests/actor_test.gd
```

[actor.log](full-qa/regressions/actor.log) is original native output:

```text
ACTOR TESTS: 73 checks, 0 failures
WARNING: 6 ObjectDB instances were leaked at exit (run with --verbose for details).
   at: cleanup (core/object/object.cpp:2536)
```

The process exits 0 after 2.172785 s; `clean_log=false`. Isolation reports
`actor failed; raw output retained`. The command is not verbose. No leaked
instance class, allocation stack, ownership or cause is retained. The warning
must not be attributed to the menu observer, prior input_mode leak or any
particular product class without new actual evidence.

Import and native bootstrap/before/after path probes succeed. All 307 source
resource hashes match exact Git objects; both actor producer receipts and all
three retained produced-file hashes match. Source/copied resources remain
unchanged, the temporary project and validated unique user namespace are
removed, and finalization failures are empty. These receipts do not make the
strict log clean.

The 11 unreached suites are match, authority_order, state_privacy,
movement_prediction, peer_lifecycle, input_mode, menu_focus, offline_diagnostics,
hud_objective_hint, activity_provenance and bot_squad_symmetry. No previous
suite totals or passes are substituted.

## Actual diagnostic skip and mocked controls

The actual [diagnostic.json](full-qa/input-mode-verbose/diagnostic.json) binds
source `20464da` and reports:

```text
status: SKIPPED_DIFFERENT_OR_UNPROVEN_FAILURE
skip_reason: Original failure evidence is absent: input_mode.log
passed: false
strict_gate_repaired: false
```

It finishes in 0.228575 s. Recorded hashes of the actual results/isolation files
match originals; the absent input_mode.log hash is null. Original evidence and
source remain unchanged. The diagnostic directory contains only this receipt:
no repeat project, process receipt, verbose log or native type evidence is
available. This is the selector's correct refusal for an actor-stage failure.

The job log also contains `DIAGNOSTIC_CLEAN_REPEAT` lines from pure controls,
with `source_commit:"invented"` and temporary control paths. Those mocked
lines are not native diagnostic outcomes. Exit 0 on the separate diagnostic
step reflects its honest skip and does not repair the failed strict step.

No diagnostic bootstrap is attempted here. Its documented possibility of
preserving an unvalidated namespace after a bootstrap failure is not exercised;
this run supplies no successful diagnostic-namespace cleanup claim.

## Other native outputs and evidence retention

All five graphical diagnostics pass with matching original PNG hashes and no
owned survivors. All 11 PNGs were directly inspected: four OS-window captures and
seven internal startup/diagnostic frames. The host uses automatic ANGLE on an
Apple paravirtual device; no physical GPU performance is established.

Separate iOS receipts and raw logs support unsigned generic-device Debug
compile/link: Xcode 26.3/SDK 26.2, one CompileC, four SwiftCompile, one Ld,
BUILD SUCCEEDED and no CodeSign action. All 15 command cleanup receipts have no
survivors. Codesign exits 1 with unsigned status. Source-before/after snapshots
match. App/export PCK descriptors agree at 10,520,108 bytes, 132 resources, SHA256
`2bdc2f9117dda65ef710beb52e60c081ff1196d6e7e0dbebe48d1b01ac7ac499`.
Full binary bytes are untransferred. Empty camera/photo/microphone usage-description
warnings remain; installation, runtime and simulator are unverified.

Supported GitHub connector → file_uri.file_id → download_file transfers preserve
both official originals under [archives](archives). No signed URL was fetched.

| Artifact | Bytes | Official SHA256 |
| --- | ---: | --- |
| Full QA 12407123499 | 2,199,686 | 20762f4c386a639a3b9194b33b8f72bf7311146eaa59fa9405288ffadc7c0d64 |
| Receipts 12407443036 | 619,303 | f7def658583d0b63a49a6bdd38fce87692886d9bb7aff02548202d97eecbdf4d |

Safe extraction checks paths, duplicates, links and expansion. All 80 indexed
receipts match sizes/hashes; 89 full-QA files include 11 PNGs. All 78 shared receipts
match byte-for-byte; two receipt-only files are frozen licenses. Original
workflow metadata and decoded connector text are retained; the latter is not
an original GitHub log ZIP.

[Source reconstruction](source-reconstruction.json), [screen roles](screen-roles-recomputed.json),
[focus/event audit](focus-recomputed.json), [strict first failure](strict-first-failure.json),
[actual diagnostic selection](diagnostic-selection-recomputed.json),
[index/suite audit](recomputed.json) and [native output audit](native-output-crosscheck.json)
preserve reproducible checks. All local scripts read files/Git objects only;
no engine, OCR, compiler, native API or implementation workload ran locally.
The menu increment is accepted within its stated scope; full ARM/platform and
release-candidate acceptance remain open.
