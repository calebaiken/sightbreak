# Source findings and bounded diagnostic handoff

Source candidate is `7101350e5d0a2f6e4afb9a913b5b1bcf2107857a`, over exact
`c32415148db1f110bbc7eadfca3793d4693429ff`. Preregistration is
`e939c30f6bc348b7e9b2521ccc2d8ef53ecf527b`. This is a diagnostic source candidate,
not a shutdown fix or native acceptance. Builder cannot approve it.

## Actual failure benchmark

Official Windows run 40080238905, job 120832097220, attempt 1, completed FAILURE.
Original files remain in the actual critic's directory, byte-bound by
ACTUAL_FAILURE_BENCHMARK.json. Initial client 9080 and reopened 7968 both exit 0.
Controller reports 111.14099999999996s and cleanup_errors []. Source lines 1021–1022 raises
`Reopened export failed clean shutdown` because reopened.log includes the
ObjectDB leak warning. That log contains 691 bytes, SHA-256
`be8dcaa93523c43561087bf9e99070211f63d5331690633d4579ed7be1e3c166`.
It reports three instances and no classes, IDs, reference counts or retaining
owners. Original OpenGL3.3-to-ANGLE warning is independently retained. Earlier
living/settings/focus markers were reached; no marker-only acceptance is claimed.
Independent full actual reconstruction belongs to
`/root/windows_collector_actual_critic_20261024` and remains separate.

## Supported shutdown and lifetime facts

A separate read-only source scan started at exact c324. Initial controller close
follows LEAVE/menu (verify_offline_export.py845–850); reopened close follows the
living focus test (1011–1022). Both use WinUI.request_close,
PostMessageW(WM_CLOSE), in verify_integration_export.py582–584. main.gd1236–1253
handles focus notifications; no close-specific teardown exists. Explicit quits
at 1367–1378 concern smoke/demo; 1857–1860 is server-only LEAVE. Ordinary LEAVE
removes and queues the match for deletion at 1861–1865. The scene ownership at
close differs, but that fact identifies neither leaked instance nor retaining
owner. A direct operating-system close is an ordinary supported user action.

Actors own shot/hurt/reload nodes as children (actor.gd 233–245) and stop them on
tree exit (566–572); reload voices are children (reload_audio.gd35–45), with
stop_all at 78–80. Static resource caches exist in actor 195–196, reload_audio 24,
weapon_model 93/96/508/544, utility 16–18, viewmodel_shading 194–199 and design_tokens 52.
A static cache is not evidence of a leak. No audio cause follows from the count.

Main awaits are account tickets 631 and smoke/demo captures 1367/1375. Match awaits
are admission 969/989 and ranked results 1386. None establishes a pending await in
the ordinary reopened offline flow. offline_diagnostics.gd closes file handles at
199–206 and211–217; signal closures capture observer/game at 258–261; finish 312–313
deactivates observation. These are inspection facts, not causal proof.

## What native verbose output can establish

Pinned engine source was read at ed1daf0bf, matching the official engine identity.
[ObjectDB cleanup2532–2567](https://github.com/godotengine/godot/blob/ed1daf0bf/core/object/object.cpp#L2532-L2567)
prints each leaked native class and instance ID, Node path where applicable, and
RefCounted reference count when verbose stdout is enabled. Its Resource-path
assignment2553–2554 is overwritten by the independent RefCounted branch2556–2557;
ObjectDB output therefore cannot be promised to expose Resource paths.
[ResourceCache814–823](https://github.com/godotengine/godot/blob/ed1daf0bf/core/io/resource.cpp#L814-L823)
separately lists cached remaining Resource paths/classes.
[Main1224–1226](https://github.com/godotengine/godot/blob/ed1daf0bf/main/main.cpp#L1224-L1226)
enables verbose stdout for --verbose;
[help560–561](https://github.com/godotengine/godot/blob/ed1daf0bf/main/main.cpp#L560-L561)
places engine arguments before --. These diagnostics supply no allocation stack
or ownership chain. They can narrow the next investigation, not prove a cause.

## Candidate and verification

Only reopened receives engine --verbose, before --, when the new controller option
--reopened-verbose is present. Initial client, OCR and display commands retain
their original arguments. Default-false workflow input verbose_reopened_shutdown
adds that controller switch only on the existing Windows living/settings/restart
step. All other workflow lines erase to exact c324. A single pure-test invocation
is added to validate.sh. No game runtime/resource source changes.

Own pure output retains 182 methods: 179 passes and the same three existing
Windows-only skips. This is the original 178-method source selection plus four
new direct-AST controls; 17 groups and shell syntax pass. The run records
preregistration HEAD because source was then uncommitted; those source bytes were
committed unchanged as 7101350e. source-erasure.json binds all current materialized
source bytes and every Git identity to that frozen candidate. New tests execute
the actual parser and command AST without importing/running the native controller.
Windows/Linux argument contexts, original quit-after negative control, omitted
and enabled verbosity, argument separator placement, input defaults and all three
workflow host contexts are checked. Nine in-memory bad variants are rejected
without harness errors; original logs and mutation results remain in this folder.

Source erasure verifies all 507 original non-doc paths/modes/blobs. 504 are unchanged;
three original files recover byte-exactly after removing only preregistered opt-in
edits. The only new non-doc path is the four-method test. Full 508-path union is
retained. Strict native_log.py and all Godot files are byte-exact; schedules,
whole 300s, close 20s, existing cleanup, ownership, privacy, protocol 6, physics,
controls and earned economy remain unchanged.

No Godot, native client/helper, export, CI, replay or retry ran for this task.
The full staged whitespace check exits2 on seven original mutation-failure log
lines emitted by unittest. Those raw bytes remain unchanged; raw-whitespace-check.json
retains the exact output. A separate source/doc check excludes only raw .log paths.
The source scan's suggested shared flag would have affected both clients; the
implemented reopened-only argument is narrower and matches preregistration.
Three setup/package omissions are retained: .gitignore initially omitted the raw
.log files from evidence commit14f2a4f8; the following checkpoint explicitly
force-adds only this task's own original logs. Other setup errors were the guessed native-validation.yml search exit2; an
unmatched optional filesystem glob made a read-only listing exit2 and prevented
that command's following reads. Correct paths were read in separate calls. Initial
instruction reads before CPU4 pinning were read-only and disclosed in prereg.

## Remaining gap and next action

Largest gap is actual reopened verbose output under the unchanged flow. Leak
identity and cause remain UNKNOWN. Native verbosity may change startup/shutdown
I/O timing, so its result cannot establish uninstrumented performance or gameplay
acceptance. The same whole 300s, phase and close 20s budgets apply; no allowance or
truncation converts failure to pass. No object-retaining instrumentation is added.

Fresh source critic must inspect exact 7101350e in its own initialized sparse and
one-commit views, repeat pure/negative controls and source erasure, and report its
own verdict. Root must separately preregister and admit any future native/CI run.
If released, invoke the existing Windows living/settings/restart producer with
--reopened-verbose, or select the workflow input on the frozen qualifier. Preserve
all original schedules and strict gates, complete raw output/commands/actions and
source identity. Do not rerun or dispatch from this builder handoff. No Mac
file-handling review is attempted; its automated block remains binding.
