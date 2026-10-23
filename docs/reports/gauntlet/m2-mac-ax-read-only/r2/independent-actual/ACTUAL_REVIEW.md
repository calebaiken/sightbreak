# Independent actual ARM AX diagnostic decision: FAILED

Exact source: `d6cb78aa4b0bc5a8265d9b82a0d379b4ee386e53`. Frozen ref: `qualifier/m2-mac-ax-r2-read-only-d6cb78aa`. [Run 39939989024](https://github.com/calebaiken/sightbreak/actions/runs/39939989024), attempt 1, job `120368768573` (`macos_ax_read_only`). The normal `native` job `120368769996` was skipped. The actual run satisfies the admitted diagnostic-only route and fails its semantic-exposure gate.

The preregistered measurable bar wins: the observer did not finish a valid bounded tree or establish one exact Deploy button with native frame agreement. The largest deficiency is the reader's requirement for an AXTitle value on every observed AXButton. The first such button in this run returned `-25212`, so the diagnostic stopped before it could answer whether the exported menu exposes the required Deploy semantics. This is an explicit failure, with no numeric score or blinded visual comparison. The historical ordinary journey is a different method and remains failed.

## Actual failure and inference boundary

The original [AX receipt](native-39939989024/qa/ax-read-only/ax-observation.json) is 2,083 bytes, SHA-256 `f795b8f263668b7e4e6960969fd9f23dc57fbbf97c7b88e541999f75919c8be8`. Observer PID 4182 is trusted. Request/nonce/clock/PID/window binding passes the unchanged pure validator. Its single partial snapshot observes three nodes at maximum depth one:

| Node | Parent | Role | Retained title |
| --- | --- | --- | --- |
| 0 | none | AXWindow | `SIGHTBREAK (DEBUG)` |
| 1 | 0 | AXGroup | Title reads excluded for this role |
| 2 | 0 | AXButton | Read failed; no value retained |

The exact failure is `Required AX attribute unavailable: AXTitle code=-25212`. The controller correctly retains `query_prerequisites=true`, `bounded_traversal_complete=false`, `unique_semantic_candidate=false`, `native_pixel_frame_agreement=false` and overall `status=FAILED`; its original [result](native-39939989024/qa/ax-read-only/results.json) returns exit 1. Replaying the original collection validator on these bytes rejects with `AX traversal did not complete`.

The receipt cannot identify node 2 as a window control, Deploy button or another particular control; it contains no subrole or frame for that node. It also cannot establish that Deploy semantics are absent. Traversal stopped at this missing value before it completed the menu tree. A correction must preserve this distinction and the actual failure. It requires its own source review; this report authorizes no retry, alternate attribute search, relaxed title matching or input action.

## Passing bounded observations

The hosted image is `macos-15-arm64` / macOS 15.7.9, build 24G830. The engine reports `4.7.2.stable.official.ed1daf0bf`. The pinned editor/template setup, exact clean export and all twelve source-control commands pass; the original job log records 118 top-level pure tests, with mocked negative-control RuntimeErrors retained as expected output. No normal native suite, ordinary input journey, iOS build or unrelated diagnostic ran in this lane.

The original first window is PID 3740/window 24 at `[0,25,1024,684]`. It resizes during startup before pinning. Native menu capture then succeeds on the sixth startup capture; the first five failed splash captures remain attached. The single focus request succeeds, foreground PID remains 3740, and the focused menu pins once at `[0,25,1004,664]`. ScreenCaptureKit frame, filter content rectangle, native PNG dimensions and AX window frame agree at 1004 by 664, scale 1, on the reported 1024 by 768 display. Owned rows before/after the observer and its last guarded rows preserve that PID/window/frame. This qualifies the observed window relation only; no semantic button frame was produced.

I opened all four distinct original images: startup 1, startup 2, startup 6 and focused menu. Startup 2 through 5 are byte-identical by SHA-256, so all seven retained frames are covered. The first two distinct images show the Godot splash; startup 6 and focused show the stock SIGHTBREAK menu and visible Deploy caption. Every PNG header dimension and every retained-file hash agrees with its original receipt.

The [focused original PNG](native-39939989024/qa/ax-read-only/01-focused-menu.png) is SHA-256 `9abb4debf0e04f4688dbe1357977ade41eda46d8f9ffd892dbd2f19e3078a051`; its [original Vision JSON](native-39939989024/qa/ax-read-only/01-focused-menu.json) is `7e61598d473cb391d576419aafc53c0c04a93694beeb775df470b49b3657f082`. The sole complete Deploy OCR row is `DEPLOY • OFFLINE 5V5`, confidence **0.5**. Running the unchanged ordinary selector on this original receipt rejects under its **0.8** gate. There is no derived 2x analysis in this diagnostic and no replacement of the raw PNG/OCR evidence. Historical native/fixed-2x failure from run `39920948579` remains unchanged.

Actual controller and observer trust/capture preflights are true. Their records contain zero permission requests and zero event posts, one focus request and no gameplay target acceptance. All 75 recorded AX calls belong to the admitted six-call API allowlist. Exact source fingerprints match the five bound observer/controller/contract/AppKit/capture files, whose privacy and API allowlists remain the independently reviewed source. The retained partial nodes contain no value/text/help/account fields. These source and receipt observations support the diagnostic's read-only scope; they are not a system-wide OS audit trace.

## Budgets and cleanup

The entire controller finishes in **51.579790666 seconds** under the original 300-second limit. No deadline is renewed. Conservative receipt-derived bounds, rather than invented exact stage timings, are:

| Boundary | Observed bound or duration | Original cap |
| --- | ---: | ---: |
| Capture-helper compile, bounded above by first window poll | 18.350415 s | 60 s |
| First owned window, measured from whole-flow start | 28.450390 s | 30 s |
| Remaining menu/observer/close work after first owned window | 23.129400 s | 60 s menu |
| Focus-before-request to focus-observed | 0.328303 s | 5 s |
| Longest retained capture | 3.863421 s | 25 s |
| Observer child receipt interval | 0.5379955 s | 5 s |
| Parent interval around observer | 0.869616625 s | 5 s |
| Close/finalization, bounded above by time after AX command start | 2.797465 s | 20 s close |

The observer retains one snapshot, three cumulative nodes and depth one, within 3 / 256 / 16 and 512 KiB caps. Its incomplete snapshot has no finishing timestamp, which is retained as incomplete evidence. The raw receipt reports no per-call elapsed samples. Source rejects returns at or beyond 0.25 seconds, but this run does not independently measure each call or prove native-call interruption.

Public ordinary termination returns true; the client exits **0**. All ten owned process groups are gone with **no fallback signals**. The observer itself exits 1 for the retained AX failure. There are no finalization failures. Original compile/capture/client/engine/export/import logs pass the unchanged strict native error/leak checker. The engine's warning that the virtual machine switches to ANGLE is preserved. The renderer is Apple Paravirtual through ANGLE; this is no physical GPU, FPS, audible-output or input-response qualification. The GitHub runner's final orphan-cleanup line lists no orphan process in this job.

Default userdata before/after is identical: an existing directory with an empty `objectdb_snapshots` directory and no files. Private menu data is honestly inventoried: 82 final files, comprising the engine log and shader caches; no `offline_training.json` or `.tmp` is present. No private profile/account values were parsed or retained, no stock match trace exists, and no Deploy, reward or earned-progression action occurred.

## Source and artifact provenance

Preregistration `6cfc5d8d` and final source admission `a4d8cb46` were pushed before root's release `493f7ed2` and the single dispatch. The run's original metadata confirms workflow_dispatch, exact full SHA, admitted frozen ref and attempt 1. Both executed source and artifact manifest report clean source, game tree `55691684d31d44f1680141954bbe530443de9d1f`, content digest `bcb872f6998ed8504c852dee354ab0acf5b6f19e58e40717267a1927e6d68a50` and validation digest `7b62d3ce7e6b0b57fc150d930f923e8d044db1b0393adc7aedf90822a70c39ea`. I compared the Git game-tree identity, all five bound source hashes, manifest/result equality and staged-inventory correspondence. The full content/validation digests are retained native-controller attestations, not a new reconstruction from every source asset in this sparse checkout.

The original/staged inventories agree with all manifest app entries; the sole extra staged file is the declared private-user-directory `Contents/MacOS/override.cfg`, whose content hash agrees. Receipts report unchanged executable `62476482ca555c1b0b55e41df39724c87950f88263481e393894a7d4cf181d25` (187,121,136 bytes), PCK `1d19884fd7f506d1a7d37f808c9c19833aee547d21776af5fd1a0133d40ebb0a` (10,528,904 bytes), capture-helper `d17e32c94939f0f52ecade4ecafa5a8e58e81ecfcc007e0e158f52a518d7893b` and Python interpreter `d4f152f2a753c94e0e7935c8ebbe6b2609979e1df7898422b577d0076383d08b`. None of those binary/PCK/helper/interpreter payloads was transferred or reparsed by this critic. Native staging/source/payload finalization passes in the retained controller evidence; independent byte equality is scoped to transferred evidence and bound local source.

Both original GitHub artifacts were obtained through the connected download tool and then downloaded using its returned file reference, without denied-host routing or cap changes:

| Original artifact | Bytes | Verified SHA-256 |
| --- | ---: | --- |
| QA `12495925886` | 956,961 | `09486d7f72e8ca3290ff4a8d395447668f7a7f11bc762c5c635494f6f2208273` |
| Receipts `12496010720` | 197,410 | `80a090f498a4533aee7a94a99a13949445e97a29a082f7e30c751e1970493a4f` |

Both transfers are below 32 MiB and match GitHub's original metadata digests. Original ZIPs, all 32 full-QA members, the nested receipt ZIP, original job log, run/job/artifact metadata and index are preserved. The nested 197,266-byte `qa-receipts.zip` matches producer hash `5664122e01146398bc8ce2ca405e431e7712bcb8f4eb7c6c3a5f948c15e00f09`. Every one of its 25 raw receipt members matches its recorded size/hash and the same full-QA member exactly. See [download verification](native-39939989024/download-verification.json), [receipt cross-check](native-39939989024/receipt-crosscheck.json), [independent recomputation](native-39939989024/independent-recomputation.json) and [evidence hashes](native-39939989024/sha256.txt).

## Remaining limits and retained failure

Actual native ARM reading of the window title and basic geometry succeeded far enough to produce this failure. Non-ASCII/non-BMP native string behavior, exact CF +1 release counts, individual per-call timing, complete exported AX menu semantics and button clipping remain unobserved. A clean process exit does not substitute for per-reference ownership instrumentation. CF ownership and complete-string boundary guarantees retain their separate source/pure evidence.

The source rejection `12ec93dd`, R2 source acceptance `114f2224`, all earlier ARM failures, native/fixed OCR confidence 0.5 and every failed splash remain intact. This report changes no gameplay or release gate. Intel macOS, ordinary Deploy/fire/reload/leave, earned progression, human/physical input and broad accessibility stay unqualified.

A review-only persistence attempt hit `Argument list too long (os error 7)` before process creation when saving metadata and the full connector log in one command. It is retained in [the setup-error receipt](native-39939989024/retained-review-setup-error.txt). Saving metadata separately and the unchanged log in bounded chunks resolved that local setup issue; no engine/native command or native retry ran. All shell review commands and children were pinned to CPU 4. This critic dispatched nothing and changed only this report directory.

The first staged whitespace check reports original timestamped empty log records and final blank lines in client/engine logs. Its unchanged output is retained in [raw-evidence-whitespace-check.log](native-39939989024/raw-evidence-whitespace-check.log). The report-local `.gitattributes` disables whitespace checks only for the retained original log files; their bytes and hashes remain unchanged. Authored reports and JSON still pass whitespace checks.
