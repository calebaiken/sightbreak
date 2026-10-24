# Independent c838 ARM actual-output verdict

**FAIL** for ordinary gameplay and the overall attempt in
[run 39920948579](https://github.com/calebaiken/sightbreak/actions/runs/39920948579),
sole ARM job `120305758766`, exact source
`c838907cf4978e53c57423e08c23277c34f4496d` on immutable
`codex/v1-qualify-mac-c838907`. The only failed workflow step is the ordinary
Deploy/living-sidearm/leave journey. The separate 15 native suites pass in this
sample; the previous audio leak remains unresolved.

Criteria commit `0abfd19ca3f9190b5c14409acd8001a62c968de5` was committed and
pushed at 07:52:43 UTC before dispatch at 07:54:40 UTC. Attempt 1 ran on
`macos-15-arm64`; the job completed at 08:03:01 UTC. Source approval
`2a3bcdfa5347ae16edb76d4f40c1a6976d7d42c8` remains a different decision.

## Fixed 2× analysis does not improve Deploy recognition

The actual ordinary flow fails after **34.506823 seconds**, before any CGEvent.
PID `3989` owns window `56`: the first recorded bounds are `[0,25,1024,684]`,
then the same window is observed at `[0,25,1004,664]`. Five rejected startup
captures show the Godot splash, followed by an accepted real menu. One focus
request is observed in 0.225354 seconds; the fresh focused menu is pinned at
32.633042 seconds within the original window/menu budgets.

The original [native PNG](witnesses/01-focused-menu.png) is **1004×664** at
scale 1. Its [derived PNG](witnesses/01-focused-menu-deploy-2x.png) is
**2008×1328**. Both are upright, contain the complete same window/menu, and
retain the matching title bar and content orientation. The actual
[Vision receipt](witnesses/01-focused-menu.json) records one fixed full-window
2× CoreGraphics-high analysis, accurate en-US recognition, no custom words or
language correction, and matching native owner/window/bounds. Independent
hash/dimension binding succeeds, as does reciprocal normalized-box containment.

| Actual focused observation | Caption | Confidence |
| --- | --- | --- |
| Original native pixels | `DEPLOY • OFFLINE 5V5` | **0.5** |
| Fixed 2× whole-window pixels | `DEPLOY • OFFLINE 5V5` | **0.5** |

Each image has exactly one corresponding complete caption. Bullet separator
normalization succeeds, but derived confidence fails the unchanged **>=0.8**
gate. The pure frozen selector reproduces the original rejection on the actual
remote receipt. The native center would be `[194.7413809981,338.5521172837]` if
the precondition passed; no target is accepted, moved to or clicked here.

The focused native SHA-256 is
`eeacddfa545fc0fabe1b065d52b289bbea42e8f75bbde02d8ffa7ed4df326921`;
derived SHA-256 is
`ec8b434a4906f64513512c23554b95b07d2daabecd88514179c406f3928c5e73`.
Raw rows remain unchanged. Only the focused-menu command requests analysis;
no second scale, crop, recapture, hint or deadline extension appears.

Actual c08889b run `39912086121` also reports the same unique raw caption at
.5 and fails before input. **Neither attempt wins Deploy or ordinary gameplay**:
the candidate adds bound upright analysis but leaves the target confidence and
outcome unchanged. This is an identified actual regression comparison, not a
blind visual-quality judgment. The new sample wins only completed native-suite
coverage, 15 versus 7; it does not establish why the previous leak occurred.

## Unreached gameplay and clean failure-path close

Zero ordinary CGEvents are posted, and no stock-offline trace is produced.
Deploy, stock initial state, first LIVE, living sidearm fire, reload, HUD,
FIELD MENU, LEAVE MATCH and post-journey ordinary close are **UNQUALIFIED**.
The target failure provides no evidence about a native missed click or hitbox.

Failure-path release leaves mouse, Escape and reload neutral with no release
errors. Public ordinary termination is accepted; the client exits 0 and all
nine recorded compiler/client/capture groups are gone without fallback signals.
This passes failure-path teardown only. No post-gameplay close happened.

The seven-file original app inventory matches the exact export manifest;
staged files/modes match except the exact two-setting sibling userdata override.
Actual Godot created the private engine log before input under
`/Users/runner/Library/Application Support/SIGHTBREAK-mac-ordinary-…`.
Its retained bytes match the final native inventory. Payload/source and the
entire default-userdata inventories remain unchanged, with no training profile
written. Original launch arguments retain requested 1280×720, Dummy audio,
stock offline validation and the default renderer selection. The actual engine
log identifies hosted ANGLE/Apple Paravirtual Compatibility graphics, not a
physical GPU or performance qualification.

## Separate completed scopes

| Scope | Independent bounded finding |
| --- | --- |
| Export/startup | Clean exact source; native headless smoke/demo and graphical menu exit 0 with strict-clean logs. Recorded package inspection finds 134 resources. The 187,121,136-byte executable is described by hash, not independently transferred/reparsed. |
| Source controls | Five ordinary commands pass 47 synthetic/mocked methods, including all 13 derived controls. They prove no actual input or OCR improvement. |
| Strict native suites | All 15 original suites execute and report **9,434 checks**, exit 0 within original caps. All 145 retained logs pass the unchanged strict scan. Per-suite native identities, 323-file source/copy inventories and owned temporary/userdata removal agree. |
| Audio diagnostic | Skipped by the original condition because the strict suites passed. The c088 original/verbose playback-WAV/stream-WAV/Master leak failures remain retained; this cleaner sample supplies no owner/cause or audio fix. |
| Read-only preflight | Ready on arm64 in **4.412420s**, current input/capture permissions true, zero events/permission requests, ordinary exit 0 and group gone without signals. |
| Settings/Escape menu | Passes in **31.566818s**, PID 3753/window 45, bounds `[40,32,960,568]`. Original home/settings/home PNGs and five native posted events with down/up acknowledgements agree. Settings target `[307.9310337347,478.1381819349]` matches observed pointer. Native profile entries preserved; six groups exit ordinarily without signals. |
| Default-renderer diagnosis | All five minimal/editor/export/frozen/current startup controls pass with original PNGs and no recorded owned-group survivors. This proves no gameplay, Intel or physical rendering gate. |
| Unsigned iOS compile | Xcode 26.3 / device SDK 26.2 compile and link succeed: **108.968931s** total, **69.107538s** actual build. Fifteen commands satisfy original bounds; same-source export/app PCK hashes and 134 resources agree. Recorded arm64 executable is unsigned. No installation/runtime/physical result follows. |

The final original job log explicitly records runner cleanup terminating
**ibtoold PIDs 7092 and 7084**. iOS command receipts report no surviving owned
groups, but those receipts do not cover these later daemons. Complete descendant
cleanup is therefore **UNQUALIFIED**. The 102,344,664-byte iOS executable was
not independently transferred or reparsed.

## Original evidence and reproducibility

Supported GitHub connectors retrieved decoded job logs and two original artifact
ZIPs; Sediment downloaded both within the 32 MiB cap. Their bytes match the
published GitHub digests:

| Original artifact | ID | Bytes | SHA-256 |
| --- | --- | --- | --- |
| QA/PNG ZIP |12487532640|4,349,573|`b9e43c18585005a95e1e61041d54eb2e5742f39533fe96b4bcfb627c1a77a398`|
| Raw-receipt outer ZIP |12487298475|3,528,976|`be25e205d27114bc810c622bb7c20f8843a50d291858b237dd07af7fb1671a95`|

The 365,457,427-byte development bundle was not downloaded. No denied redirected
host was bypassed. [audit_actual.py](audit_actual.py) independently verifies
**1,210 integrity predicates**, all 217 indexed receipts, 215 exact overlapping
QA members, 234 QA files and all 439 exact Git input objects. The two receipt-only
members are original frozen-baseline license/copyright text. All **19 PNGs / 15
unique hashes** are covered by direct original inspection and exact duplicate
binding in [images.json](images.json); witness copies preserve original bytes.
The auditor's initial JSON-count parsing failure remains in
[audit-first-failure.txt](audit-first-failure.txt), corrected without changing
native output. No native/OCR/Swift workload ran locally.

To replay the read-only audit, extract the retained QA outer ZIP into a fresh
`qa/`, the receipt outer ZIP into `receipts-outer/`, and its `qa-receipts.zip`
into `receipts/`, all under one fresh directory. Then run:

```sh
python3 docs/reports/gauntlet/m2-mac-derived-ocr/native-c838-independent/audit_actual.py \
  --raw-directory /path/to/fresh-directory
```

Exact source recomputation yields game tree
`55691684d31d44f1680141954bbe530443de9d1f`, shipping content
`bcb872f6998ed8504c852dee354ab0acf5b6f19e58e40717267a1927e6d68a50`,
validation `f4cc2b35db79cc811ba5b1ed7d4c150fb8593ae26b5a0bc1f02e78c963ffa650`.
Recorded Mac executable SHA-256 is
`b8851735c5298dbee61e09d171677f0044b3408df1286f02c623174e19aad572`.
The original earlier Mac failures and their source/actual reviews stay intact.

The largest remaining gap is actual stock Deploy and the living sidearm/reload/
leave journey: recognition still prevents its first event. Any next component
needs fresh source and trial review with the original confidence, ownership,
input and budget requirements preserved. No retry, source integration or broad
Mac/Intel/physical/human/full-match/release acceptance is granted here.
