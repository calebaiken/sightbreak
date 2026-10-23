# Independent c088 ARM actual-output verdict

Verdict: **FAIL** for ordinary gameplay and the complete native regression gate
in [run 39912086121](https://github.com/calebaiken/sightbreak/actions/runs/39912086121),
job `120277159133`, exact `c08889b8c1118c89e83c151079df4dc224076760`.
This is the original sole ARM macOS-15 attempt on
`codex/v1-qualify-mac-c08889b`, created 2026-10-23T06:32:13Z. Its actual three
failed steps are native regressions, verbose leak diagnosis and ordinary play.
Preregistration `5dd3e66` preceded fetching this run's output. Source approvals
`12ecda91`/`45a6e5d` remain separate decisions.

The candidate wins the narrow startup-observation and failure-path-close
comparison against actual `b2e0293` run `39906639650`: it records the changing
window, reaches a real focused home screen and closes ordinarily without signals.
Both ordinary gameplay attempts fail before any CGEvent. There is no ordinary
gameplay winner or blind visual-quality comparison. The earlier first attempt's
four test-owned alias-path errors and both previous failures remain unchanged.

## Ordinary failure and original pixels

The new flow fails after **28.365824 seconds**. The first owned window is PID 3247 /
window 55, bounds `[0,25,1024,684]`. Exact subsequent rows record that same window
at `[0,25,1004,664]`. Six rejected startup captures show the Godot splash. The
seventh capture shows the home screen; one focus request is observed within
0.227 seconds, then a fresh focused home screenshot passes the existing home
identity check. Geometry is pinned once at 27.208147 seconds, inside the original
60-second menu budget. All eight original capture attempts and their hashes are
retained. The final accepted images are **1004x664 pixels at scale 1**, despite
the unchanged requested 1280x720 launch.

Both accepted native Vision receipts identify exactly one
`DEPLOY • OFFLINE 5V5` row with **confidence 0.5**. The unchanged target gate
requires exact `DEPLOY · OFFLINE 5V5` and confidence >= 0.8. The controller rejects
the caption before moving or clicking. The original focused image visibly
contains the Deploy button; visual inspection does not upgrade Vision's reported
confidence. The failure does not establish a missed input, bad hitbox or gameplay
response, because **zero CGEvents are posted** and no stock-offline trace exists.
The pin itself proves no actual input behavior. Deploy, initial stock state,
living fire, reload, HUD, FIELD MENU and LEAVE MATCH remain wholly unreached.

Exact original witnesses are in [witnesses/01-focused-menu.png](witnesses/01-focused-menu.png),
[its native receipt](witnesses/01-focused-menu.json),
[the accepted startup menu](witnesses/00-startup-menu-7.png) and
[its receipt](witnesses/00-startup-menu-7.json). The focused PNG SHA-256 is
`6fd1f2c99a5764acc64edca3f4667e22b877177691f9d585b47567cea520bfbf`;
receipt `8c876f1eb35f63f26cc7874bce9824643b3278a6cd87db7757c9260f35ff7de2`.
No crop, image conversion, local OCR or recapture was used for this review.

Final controls are neutral, no release errors exist, the public failure-path
termination request is accepted and the client exits 0. All ten recorded
compiler/helper/client groups are gone with no fallback signals. This passes
failure-path teardown only; the planned post-gameplay ordinary-close sequence
never runs. In the prior `b2e0293` attempt the later context was unrecorded and
failure close needed SIGTERM; those deficiencies are improved in this attempt.

## Strict native source regressions fail

Only seven suites execute, reporting **1,584 assertions**. The first six suites
are clean. `input_mode` reports 462 checks/zero assertion failures and exits 0,
but its original log reports two ObjectDB instances leaked at exit. The unchanged
strict scan rejects that output, and the remaining eight suites do not execute.
Therefore the expected **15 suites/9,434 checks gate fails**. Prior successful
counts cannot be transferred to this attempt.

The separate bounded verbose repeat reproduces the strict failure in 11.851798s.
Its original output names `AudioStreamPlaybackWAV` and `AudioStreamWAV`, each with
reference count 1, plus orphan StringName `Master`. These are actual diagnostic
types; their precise retaining owner or product cause is not established here.
All five diagnostic process groups report normal exit and removal without signals.
Both native-test projects preserve the exact 323-file game inventory and copied
resources, remove temporary projects and their own userdata namespaces, and have
no finalization errors. This isolation evidence does not erase resource leaks.

## Separate passing scopes and cleanup limits

| Actual completed output | Independent bounded finding |
| --- | --- |
| Fresh export/default startup | Exact clean source; original headless and graphical startup exits 0. Recorded package inspection reports 134 resources. Original menu pixels inspected. Final 187,121,136-byte Mac executable remains independently unparsed. |
| Source controls | All four ordinary source commands pass 34 tests, including 11 startup groups. These use mocked processes/screenshots/authority and cannot certify actual gameplay. |
| Read-only preflight | Ready in 3.870970s on arm64, current input/capture permissions true, no posted input or permission requests, ordinary exit 0 and owned group gone without signals. |
| Existing Settings/Escape menu | Passes in 32.568175s at PID 2995/window 43. Original home/settings/home images, exact Settings point `[307.9310337342623,478.13818193180816]`, actual pointer acknowledgement and five posted events/down-up acknowledgements agree. Neutral controls, exit 0 and all six groups gone without signals; source/profile entries preserved. |
| Private ordinary userdata | Actual engine-created private `user://` log exists before input under real `/Users/runner/Library/Application Support/`. Original seven-file app payload descriptors agree with manifest; staged files/modes match except exact two-setting sibling override. Original payload/source and entire default-userdata before/after inventories match. No fabricated private gameplay profile exists. |
| Default-renderer diagnostics | Five startup controls pass with exact original captures and no surviving owned groups. Minimal 3D controls show cubes; frozen/current captures show menus. These hosted ANGLE/Apple Paravirtual graphics controls establish no physical performance or gameplay qualification. |
| Unsigned iOS compiler/linker | Xcode 26.3/SDK 26.2 device build succeeds: 81.752134s total, 44.701606s actual Xcode build. Same-source PCK hashes/134 resources and recorded unsigned arm64 descriptors agree; 15 command receipts meet original bounds and report no group survivors/cleanup errors. Large final 102,344,664-byte binary was not transferred or reparsed. |

The iOS cleanup claim must remain limited. The original final job log explicitly
records GitHub post-job cleanup terminating **ibtoold PIDs 5323 and 5317**, despite
the command receipts reporting no survivors. Those daemon descendants are outside
what the retained command receipts establish. Complete descendant cleanup is
unqualified; neither command-group receipts nor the final workflow status can
replace that missing proof. iOS installation, simulator, runtime and physical
acceptance remain unqualified.

## Provenance and reproducibility

Both original downloaded outer ZIPs match GitHub's published digests:

| Artifact | ID | Bytes | SHA-256 |
| --- | --- | --- | --- |
| QA/original PNGs |12483606939|3,303,784|`6452eac95a8f55fd84d1bcba9e62a50763fda7d419b7c453d25d009aa0f8dfb7`|
| Raw receipts |12483084532|1,267,376|`960e1b6877c8c8c9d1b99672d94cd8eb5a3f34597dab21c7d6fe5efc8e24e5a8`|

GitHub's supported connector retrieved the decoded original job log and artifacts;
Sediment downloaded the two bounded files. No denied redirected log host was
bypassed. The larger 364,390,835-byte development bundle was not transferred.

[audit_native.py](audit_native.py) audits original retained files read-only and
records its result in [audit.json](audit.json). All 165 indexed receipts verify,
163 overlapping QA files are byte-identical, and all 182 QA files have independent
hashes. All 19 original PNGs are visually covered: 14 unique hashes, with exact
duplicates linked in [images.json](images.json). Both original and verbose
`input_mode.log` fail the unchanged strict scan; the other 104 retained logs pass.
The expanded auditor's initial filename-key error is retained separately and
corrected without modifying raw evidence.

Exact Git-object recomputation binds game tree
`55691684d31d44f1680141954bbe530443de9d1f`, content
`bcb872f6998ed8504c852dee354ab0acf5b6f19e58e40717267a1927e6d68a50` and validation
`e7b3c825c3cca650d902873739308b7c2136cb5b2389c34ccfd97dbaee7b159c`.
Recorded Mac executable hash is
`c781b2681a1069297103aafe5d441b36c61745ff8111a82bc2ae5b91a5143d9d`.

The largest remaining gap is an actual stock Deploy/living sidearm/reload/leave
journey: the native target-recognition precondition still prevents its first
event. A reliable source-reviewed recognition method must retain confidence,
identity, unique-window/input-pin guards and original budgets. The independently
reproduced input-mode resource leak is a separate blocker to the complete native
gate. No new source approval, native attempt or broad release gate is granted
by this actual-output verdict.
