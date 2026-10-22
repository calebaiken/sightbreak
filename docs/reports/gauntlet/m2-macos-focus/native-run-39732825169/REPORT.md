# Independent native ARM focus and menu outcome

The revised observer produces a clear bounded improvement over run 39729489971:
this run records its exact window, its helper's own capture permission, full
window pixels, exact foreground focus, delivered pointer/Escape states and
visible menu → FIELD SETTINGS → menu navigation. The prior run remains FAILED
with zero events and no helper invocation. This sequence does not establish
why that earlier run failed.

Preserve the new run's declared menu result as **FAILED**. Its final automatic
screen check rejects a low-confidence header in a visibly returned menu:

> Original OS screenshot did not confirm menu screen

The single largest remaining gap for this menu gate is reliable high-confidence
final-menu observation under the unchanged 0.8 threshold. A separate native
source-suite leak also blocks whole-host qualification. No blind image pair is
available because the earlier attempt has no OS-window capture.

## Exact source and native identity

[Run 39732825169](https://github.com/calebaiken/sightbreak/actions/runs/39732825169)
contains exactly one macos-15 job 119671543697, concluded failure. Source is
`b09cfe1b661ec153f2bd57d45e695cc70e9717b0`. Independently reconstructed
game tree is `fb6be859e05812d8707be1ef5c6f747d2588c1e9`, shipping-content
SHA256 `f148106d4ed189f2a5d49e798f55bf0fb30f612126ec203037377f88d332855e`
and validation SHA256
`8b5b1d9c202f237afa1e38d5186f56459f729b4e43cac49bc4dc56fadea4c845`.
Fresh export, preflight, menu and iOS snapshots agree and are clean. Final
source/export checks remain unchanged by native receipts.

Seven recorded implementation/control/helper/workflow blobs and three imported
guard files match reviewed 1260217. A separate static reviewer inspected the
intervening product/HUD guidance changes and found unchanged ordinary Settings,
Escape and profile-save boundaries. The new source requires its own receipts;
no older export is substituted.

Desktop executable SHA256
`507210b5d0785b0e885b25a182295b62d641771f31735058844e2efe6c508cd3`
matches both current preflight and menu export descriptors. The development
artifact is 290,739,700 bytes and was not requested under the 32 MiB transfer cap.
Executable/PCK descriptors remain native attestations; their binary bytes were
not independently transferred or rehashed.

Fresh preflight independently records PID 3634/window 35, bounds
`[40,32,960,568]` points, all four permissions true and an internal 960×540 PNG.
Its normal exit, profiles and owned cleanup pass. This identity is separate
from the actual menu client.

## Capture-only evidence

The actual client is PID 4062, controller PID 3656, owned visible layer-zero
window 45. `client_window_selected` retains bounds `[40,32,960,568]` before
capture or activation.

Swift compilation succeeds with the original empty compiler log and exit 0.
Source SHA256
`af6576bbda2deac290a418cdbf0fef8894376372e934d617ee2bc1bdecb524b9`
matches Git. The native executable descriptor is
`a98bf9f5672aa2d5de5b8b2f0217a71b7858547dd835c1d9575e002655011296`.
The binary is excluded from QA, so its hash is not independently recomputed.
All four actual capture commands invoke that same compiled helper path.

All four helper receipts query their own screen/post permissions true, report
zero events and zero requests, and bind PID 4062/window 45. CoreGraphics frame,
SCWindow frame and filter content rect are all `[40,32,960,568]` points.
Scale 1 produces original 960×568 PNG files, including the visible 28-point chrome.
This establishes this host's mapping, with no guessed titlebar offset or
Retina-scale qualification.

The pre-activation [background PNG](full-qa/macos-menu-input/00-background-window.png)
shows the inactive Godot splash. `PASS_CAPTURE_ONLY_NO_FOCUS_OR_INPUT` is the
correct bounded label: it establishes capture and geometry, with no accepted
menu or focus outcome. Later foreground screenshots supply the menu evidence.

## Actual focus sequence

The raw pre-background and pre-request snapshots identify foreground 344,
controller 3656 and target 4062; `foreground_is_controller=false`. Target active
changes from false to true while the raw foreground value remains 344. Target
active state is therefore not used as focus proof.

There is one public activation request, options 3, returned true. Its raw return
snapshot still reports foreground 344. The first recorded public call processes
the controller main run loop: requested 0.05 s, actual 0.198636 s, return code 3. The raw before value
is 344; raw after is 4062. The sample's focus elapsed time is 0.261159 s, within the
unchanged five-second limit. Fresh target/diagnostic confirmation follows;
`focus_observed` occurs about 0.290 s after the before-request trace.

This records an observation change across the public run-loop turn on this
host. It does not distinguish the internal timing of activation from an observer
refresh, and cannot retrospectively explain the older run's foreground 3721.

## Input, original pixels and failed recognition

The [initial foreground menu](full-qa/macos-menu-input/01-menu-0.png) has
TACTICAL OPERATIONS and one exact SETTINGS target, both Vision confidence 1.
Independent conversion of the original normalized SETTINGS box gives global
point `[307.9310337342623,478.13818193180816]`; the actual OS pointer is
`[307.9310302734375,478.13818359375]`.

Five ordered post attempts occur: pointer move, button down/up, Escape down/up.
Four combined-session observations acknowledge button down/up and
Escape down/up. Each observation has foreground 4062. Source-bound exact-target
and neutral guards remain present; no input retry occurs.

The ordinary click produces [FIELD SETTINGS](full-qa/macos-menu-input/02-field-settings.png),
with the title at Vision confidence 1. After Escape, the
[original returned-menu PNG](full-qa/macos-menu-input/03-returned-menu.png) visibly
shows the main menu, SETTINGS and TACTICAL OPERATIONS, with no FIELD SETTINGS.
Its SHA256 is
`c17ca318ef148c0e444136048f8f914bade3770366c29acb6d619cb71427adeb`.

The [original Vision receipt](full-qa/macos-menu-input/03-returned-menu.json)
merges the header into `S/B TACTICAL OPERATIONS` at confidence 0.5. The source
drops that entry under its 0.8 minimum. Exact SETTINGS remains confidence 1.
Thus the final menu condition fails despite the visible return. The helper
itself exits 0 and reports successful capture/OCR. The failed PNG/JSON/log remain
retained even though the driver throws before adding this final capture to its
accepted `captures` list.

Observed synthetic OS delivery and visual navigation are independently supported
by these originals. The declared full menu gate remains FAILED; this review
does not lower confidence or replace its result with a manual pass.

## Cleanup and native state

At 29.709 s the driver completes failure cleanup. Button and Escape are up, the
owned-held set is empty, and the post-attempt count remains 5 after release.
The public ordinary quit request succeeds; client 4062 exits 0. Compiler, all
four capture helpers and client groups are gone, with no termination signals.

Both canonical profile entries remain absent/unchanged. Preflight and menu
before/after inventories are identical: 86 files, 32 directories. Native files
are preserved. These are warm-cache snapshots, with no claim about transient
writes, hard-kill safety or concurrent physical input.

## Separate native source-suite failure

The declared suite list contains 12 suites, but this run executes only the first
seven. Actor 73, match 75, authority 178, privacy 55, movement 725, lifecycle 16 and
input 462 sum to 1,584 assertions with zero assertion failures. All seven process
exits are 0. The [original input-mode log](full-qa/regressions/input_mode.log) then reports:

> WARNING: 2 ObjectDB instances were leaked at exit (run with `--verbose` for details).

The strict clean-log gate correctly rejects that suite. Isolation status is
false with `input_mode failed; raw output retained`. No verbose instance
types are available; type, ownership and cause are unproven. Menu focus,
offline diagnostics, HUD objective hint, activity provenance and bot squad
symmetry are unreached. The prior 12-suite pass cannot qualify this source/run.

All 307 isolation resource hashes match exact Git objects; 14 standalone native
producer receipts and 21 produced-file hashes match. Source/copied resource
inventories are unchanged, the unique namespace and temporary project are
removed, and finalization has no cleanup failure. No HUD fixture output exists
because that suite was never reached.

The review reader initially assumed the HUD log existed and raised
FileNotFoundError. Its exact failed reader and output are retained as
`audit_receipts-attempt-1.py`/`audit-attempt-1.log`. The corrected reader
reports the partial suite list and leak without changing native evidence.

## Other native outputs and transfer

All five default graphical diagnostic trials pass with matching original PNG
hashes and no owned survivors. All 11 transferred PNGs were directly inspected:
four ScreenCaptureKit window PNGs and seven internal startup/diagnostic frames.
The native host uses automatic ANGLE on an Apple paravirtual device. These
outputs do not establish physical GPU behavior, performance or human play.

iOS independently passes unsigned generic-device Debug compile/link:
Xcode 26.3/SDK 26.2, one CompileC, four SwiftCompile, one Ld, BUILD SUCCEEDED and
no CodeSign action. All 15 command cleanup receipts are complete. Codesign exits 1
with `code object is not signed at all`. Source-before/after snapshots match.
The app's PCK descriptor matches exported 10,520,108 bytes, SHA256
`cec5485ede048a38eb4b7e01c26719806daa9dff2bdc5b319a5a2977adfd3411`,
132 resources. Binary descriptors are not independently rehashed. Empty camera,
photo and microphone usage-description warnings remain in raw logs. Device
installation/runtime and simulator remain unverified.

Supported GitHub connector → file_uri.file_id → download_file transfers retain
both official originals under [archives](archives), without signed-URL access:

| Artifact | Bytes | Official SHA256 |
| --- | ---: | --- |
| Full QA 12406027661 | 2,220,069 | eeb8614db1e0dc00b4dbe5e86608a9fddfd13e44ee1bae14dd3339c0cfc265cd |
| Receipts 12406212225 | 728,454 | 5e4b675de6d75a997a99a4aff9dd321a16b6aa5bd2cfbc4318484daf64b5b1c1 |

Safe extraction checks paths, duplicates, links and expansion size. All 127 indexed
receipts match size/hash; 136 full-QA files include 11 PNGs. All 125 shared receipt
files agree byte-for-byte. Two receipt-only files are frozen license texts.
The connector's decoded log is preserved as
[job-119671543697.log](job-119671543697.log), with its full response and workflow
metadata. It is decoded text, not an original GitHub log ZIP.

[Source reconstruction](source-reconstruction.json),
[focus sequence](focus-recomputed.json), [original pixel/box review](original-pixel-and-box-review.json),
[suite/index recomputation](recomputed.json) and
[native-output cross-check](native-output-crosscheck.json) preserve the review.
All replay scripts read files/Git objects only. No implementation, native API,
engine, compiler or OCR workload ran locally. Movement, aim, firing, matches,
physical-device behavior and whole-platform qualification remain open.
