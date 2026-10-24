# Process-observation source verdict: REJECT

Frozen source `b6f25804cddc3e48faeec613a2daa7f392fb1990`, handoff
`b770ccc10701bf7fd48921fdad3ecc0045d5cd2a`, is better than550 for missing API,
direct root identity and Popen cleanup, but loses the full process-ownership bar.
Two independent timing-race models adopt and signal unrelated fake processes.
Its inherited source-binding helper also accepts three hidden physical/mode
changes while Git reports clean. No engine, new /proc probe, real signal or native
retry occurs in this review.

The largest remaining process gap is ancestry proof between a children snapshot
and later identity/pidfd acquisition, including birth of a queued parent before
recursion. Direct Popen-root binding does not establish every descendant's owner.
Source admission/actual invocation remains blocked; current environment capability
and the original18 input-bit mismatches remain separate known blockers.

Existing critic thread reuse is explicit. Reviewer is independent of root builder.
Actual R1 rejection6e6d7159 was sealed first. Prereg9dcac915 preceded b6 source
inspection/tests, and additional concrete controls6711ac15 preceded execution.
No actual evidence, earlier32 admission files, canonical docs or other worktrees
were changed. Codec329 is frozen separately and not reviewed here.

## Two ownership failures

Both models use only the frozen fake kernel/process adapters. signal_all calls
the fake send method, which changes dictionaries; there is no real pidfd/signal.
Each follows a valid direct root bind. Results are identical in own and initialized
one-commit views, in own/depth INDEPENDENT.json and exact failed stderr.

1. `test_stale_children_pid_with_unrelated_parent_is_never_owned_or_signaled`:
   a children snapshot lists PID200. Before identity is read, that number belongs
   to a stable unrelated process with PPID999. observe() accepts its new birth,
   opens its fake pidfd, records it and fake-signals200. Birth stability around
   open does not prove it still belongs to the enumerated parent. This models
   child exit/reap/PID reuse between separate kernel observations.
2. `test_queued_owned_parent_reuse_cannot_import_unrelated_descendants`: root100
   first owns child200/birth456. Before recursion, native root may reap that child
   and PID200 is reused by unrelated parent999/birth457. observe() enumerates the
   queued numeric PID without revalidating its owned birth, then adopts and
   fake-signals unrelated child300. Checking only child PPID against numeric200
   would not fix the reused-parent case; parent lifetime must still be owned.

Inherited observe() checks birth around pidfd acquisition but neither the
candidate's PPID against the enumerated parent nor the queued parent's current
birth before following children. The source can therefore expand ownership across
these races. A correction must reject/defer unknown ancestry and avoid signaling
unproven objects, while allowing legitimate subreaper adoption through a currently
verified owned parent/supervisor. These are source-only timing models, not observed
incidents in actual R1 and not tests against any real unrelated process.

## Physical source binding

Registered real local Git controls run only in a new own initialized exact view,
not producer/runtime or another author's index. A clean source_binding passes.
Each benign change sets assume-unchanged, leaves Git status empty/diff exit0,
then calls only source_binding; changed code/GDScript is never executed.

| Change | Frozen guard result |
| --- | --- |
| Append a harmless comment to reference.gd | Accepted; returned actual component hash changes but is never compared with the expected Git blob. |
| Toggle project.godot executable bits | Accepted; byte hash and returned binding remain equal to baseline; modes are not in binding. |
| Append a harmless comment to imported scripts/native_log.py | Accepted; returned binding remains baseline because dependency is outside the six component files. |

All bytes, executable modes and assume-unchanged flags are restored in finally,
then verified exact and source-clean. Git stores executable mode, not umask read/
write permission bits; the recorded mode control changes the executable flag.
No altered source is loaded/executed and no acquisition is called.

The helper currently records six actual hashes and checks Git metadata; that is
not self-contained physical equality with expected frozen objects. A source-
bound producer must compare physical bytes/Git modes and actual imported custom
dependencies with trusted expected identities, or explicitly require a separate
external physical-admission proof and avoid claiming the helper does that work.
The original actual550 runtime was independently physically verified at519 paths
before/after. These tests make no old-run tamper allegation and do not alter its
existing process/input-failure verdict.

## Verified improvements and test accounting

All36 maintained methods pass in both views:31 math/supervisor/interface plus5
unchanged strict-log methods. Missing API for an existing parent/task fails;
legitimate disappeared paths remain separate. Prelaunch observer failure creates
no native attempt. Direct root checks parent/birth/pidfd before unchanged session/
executable/affinity gates, intended PID is retained, and normal cleanup waits a
known terminal Popen status. Bound root remains known even when discovery is empty.
Forced cleanup still prevents acquisition success. Original actual raw still
fails the unchanged exact input-scalar roundtrip gate.

Independent suite has6 methods. Own view:3 pass,2 fail,1 planned real-Git skip.
Exact depth view:3 pass and3 distinct methods fail, with5 failure events from two
ancestry methods plus three physical-source subcases in one method. Errors=0.
Never subtract subtest event count from method count. The duplicate ancestry
failures in both views are repetitions of the same two findings, not four cases.

The observer-error positive correctly rejects/reaps the fake known Popen and
retains EOF bytes; its fallback wait status is not persisted in the current
receipt. This is an additional diagnostic limitation, not a passing acquisition.

Independent replay of the builder's9 new tests against exact old550 acquisition
bytes reproduces6 failure events/5 error events across7 distinct failing methods,
2 passed methods. Missing new bind_root API errors and already-failing malformed
PID conversion cases are not all unsafe old false passes. The old source and
original result/negative passed-count adjudication are preserved; no negative
passed-method arithmetic is used.

Full519 non-document union has exactly two changes (acquire wrapper and tests),
517 protected identities. Native kernel,588 cases, parser, game, protocol/privacy/
economy and canonical fixtures remain byte-exact.356 physical files match modes/
blobs in each sparse view;163 exact omitted objects remain available. Exact source
view has populated11582-path index, count1, no HEAD^ and shared alternate
/workspace/sightbreak/.git/objects. Storage is not self-contained; no full clone.
All physical controls restore source and index flags; no Godot source cache appears.

## Scope and next action

Preserve b6 rejection and all actual R1 source/runtime/raw. Source-only correction
must establish descendant parent/lifetime continuity and make source-binding
scope truthful. Register new exact target before tests. Existing environment lacks
the required children interface and must remain prelaunch-blocked; independent
binary input transport is not approved by this review. No new native/helper/API
trial, C/FOV/study review, platform run or CI is authorized.
