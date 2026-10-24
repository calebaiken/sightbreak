# Independent ancestry source review: REJECT

Frozen source8cc38cdcd7dfff37056782149e513c08037e4e77, handoff
9807106cb79033cd00b69c1411c3808488c372bb. Prerega6b652e5 preceded source/tests/
handoff inspection; concrete model/replay registrationdf9572e9 and control binding
ed81596c/0a5fc805 preceded all execution. Existing critic thread reuse is explicit.
Root supplied the same-start-tick question before registration; that lead is
disclosed. Reviewer is independent of this implementation. No actual process,
pidfd, signal, /proc/API/helper/native/CI experiment occurred.

No observer wins the registered ownership bar. This source improves the two old
different-parent/different-birth examples by rejecting them, but two independently
specified same-tick schedules import and fake-signal an unrelated child's newly
opened descriptor. A third method finds the replacement parent falsely reported
live through the old exited descriptor. Thus source acceptance fails despite62
maintained methods passing. Largest gap is proving the queued/live process is the
same lifetime as its retained ownership evidence.

## Supported model and concrete failures

Public Linuxv6.6 is a supported reference model, not the unprobed actual kernel.
The retained source establishes separate facts: free_pid removes a number from
the namespace IDR before final reference release (pid.c155); a pidfd holds its
own struct pid reference (fork.c2147) and polls whole-thread-group exit
(fork.c2075); proc starttime converts nanoseconds through nsec_to_clock_t
(array.c577–578), which performs integer division (time.c733–745). PID allocation
uses independent IDR allocation, including explicitly selected IDs, not a rule
that a number can have only one lifetime per exposed clock tick. A retained old
pidfd therefore need not describe the current numeric PID/start_ticks projection.
These facts support the possible model; they do not measure likelihood, actual
host settings, process rates or a race in550. No namespace/PID setting was changed.
One public pidfd.c URL404 is preserved; this tag's implementation is in fork.c.

The independent kernel model uses distinct lifetime objects. Numeric lookup emits
only the actual API-shaped fields; fake descriptors retain their original object
across reuse and reject sends once it has exited. This avoids the old simplified
fake-fd-equals-PID shortcut. The two invalid traces share this sequence:

1. Supervisor50 and root100 remain valid; owned parent200/birth1000 is verified
   under root100 and descriptor4002 binds its old lifetime.
2. Parent200 exits/reaps; unrelated process999 creates a new child atPID200
   within the same exposed tick1000. That replacement creates child300/PPID200.
3. Reuse occurs either before queued-parent lookup or inside children(200).
   New200 has PPID999/group999/session999. Its old held descriptor remains exited.
4. parent_alive compares only PID/start_ticks, so the new parent's projection
   passes. Child300's PPID200 also passes. Descriptor4003 binds the foreign child.
5. observe returns without error and signal_all issues a successful fake signal
   to4003/foreign-child. Send to4002 correctly raises ProcessLookupError; it does
   not retarget to the replacement. The unsafe action is the newly imported child.

Both schedules reproduce in both source views. Each records two failure events,
for adoption and signal. The separate live() case replaces200 after prior proof
and finds it returned as live solely because numeric PID/birth matches the old
key. Total:9 independent methods,6 pass/3 failed methods/5 assertion failure
events,0 errors/skips in each view. Complete lifetime/descriptor/event/input/
signal records and raw failures are retained; no failure was repaired or rerun.

The non-collision counterpart changes only replacement birth to1001: it rejects
safely with no foreign adoption. Stable three-generation ownership and genuine
owned-orphan reparenting preserve original descriptors and pass. Stale foreign
PPID and child reparent during opening reject and close unproved handles. These
positives/nearby negatives distinguish the target lifetime issue from unrelated
invalid freshness/context or an always-rejecting model.

## Source findings and necessary correction

Queued parent validation at OwnedTree.observe checks its current numeric identity
against the queued pair, but not whether its held lifetime has exited or its
changed PPID still has a proved permitted ancestry. live() repeats the same
numeric-key assumption. The earlier child PPID checks around opening are useful,
but a child PPID that refers to a replacement parent number cannot prove descent
from the original parent lifetime. Root/group/session gates remain enforced for
the root; descendant groups cannot be assumed identical to that root.

A correction must establish valid lifetime/ancestry evidence around enumeration
and child binding, and prevent stale held descriptors from certifying current
numeric live entries. Supported pidfd exit readiness and explicit permitted parent
edge/reparenting checks are relevant tools. Unknown proof must reject. Do not
remove genuine orphan support, weaken root/session/executable/affinity checks,
perform observer API work before pipe retention, or treat coarse start_ticks as
a unique lifetime identifier. The exact implementation and any new kernel API/
protection-scope change require separate preregistration/frozen review. No fix
is implemented or preapproved by this verdict.

## Preserved improvements, guards and execution accounting

All62 maintained methods pass in both own and exact-depth views:57 math/codec/
ancestry/protection plus5 strict-log,0 failures/errors/skips. These are pure fake
tests with real Popen/signals/pidfd calls/native-library effects forbidden inside
test bodies. Pure elapsed times are not physical/native performance evidence.

Literal replay selected only the two unchanged f323 ancestry methods, not its
other four inherited binding/actual/cleanup checks. Literal result is2 methods/
2 errors/0 failures per view: the new safe RuntimeErrors are not caught by that
old rig. Raw output/source are preserved. The separately preregistered adapter
catches only the two exact intended rejection messages and verifies no target
outside adoption/signal before the original assertions continue. Adapted result
is2 pass/0 errors/skips in each view. Literal errors were not relabeled as passes.
The new lifetime-aware falsifiers are separate and do not use that adapter.

The original protection JSON/hashes are byte-exact. Independent complete-module
reconstruction replaces only OwnedTree with exact329 and matches the entire old
acquisition module; replacing only FakeKernel matches the entire old test module.
All31 original test method/assertion bodies persist. The adapted codec protection
method is intentionally changed and is not claimed AST-identical. Its unique AST
class spans preserve outside code/comments/decorators and reject bad boundaries;
the maintained five scope controls pass. Baseline segments independently match329,
not just mutually supplied hashes. Builder's initial57/one guard failure remains
retained; the later old-test assertion was originally unreached.

Constructor tracing and source ordering prove no OwnedTree API call before
immediate stream_factory retention. Original parser/kernel/canonical588 inputs/
schema2 transport, native log policy, LinuxKernel/Streams/cleanup/monitor/finally,
deadlines/CPU domains and all remaining acquisition bytes are unchanged.

Full non-doc union525:3 changed/2 new/520 protected path/mode/blob identities.
All362 physical own/depth paths and all525 physical builder paths match before
and after tests;163 sparse omissions remain exact object identities. Exact-depth
HEAD8cc has one reachable commit, HEAD^ fails128, full index11643 and clean status.
Views share /workspace/sightbreak/.git objects; no self-contained/full clone claim.
Prior admission/actual/process/codec/protection manifests remain unchanged.

Inherited physical-source-binding defects and absent child-list interface remain
whole-producer blockers. This new rejection is independent of them. Codec's
component-only acceptance and prior guard-scope permission do not transfer to
ancestry. Actual550 remains FAILED and no new/retried acquisition or qualification
is authorized. Separate study evidence review still waits its own final freeze.

Packaging preserves the full-report whitespace exit2: four trailing-space lines
are original unittest subtest-failure output in the two independent original.stderr
files. They remain byte-exact. Source whitespace exits0; the report check excluding
only those two named raw outputs exits0. No source/authored-content waiver or
failure-output trimming is used. The exact failing and scoped commands are retained.
