# Pre-edit protocol adjudication: REVISE

Target `12c076128eff25a1dfee63e6bc7441f500ac8607`. Existing independent critic
thread reused; the critic authored neither this proposal nor a future
implementation. Registration89934ea5 precedes review. All17 complete original
Git/blob/byte/SHA identities and all10 original Kernel method hashes verify.
Original e468/8cc/85c source and findings remain unchanged.

The retained descriptor/debt architecture and narrow protection shape are
supported. Three interface/construction details need an additive exact amendment
before implementation: interpreter-level retry promises, status normalization,
and the known old zombie-positive fixture. This is static source adjudication,
not a new observer, model score, source-candidate acceptance or Linux release.

## Supported lifetime and accounting contract

Records identified by a local serial and retained descriptor can preserve an
exited lifetime despite PID/start-tick or fd-number reuse. Parent and child
retained checks around numeric reads/opening prevent an exited parent from
authorizing a replacement's descendants. Root designation must remain a record
role from its known Popen binding, never a PID comparison.

ACTIVE, EXITED_PENDING/UNRESOLVED and terminal REAPED/root-delegated accounting
must remain distinct. Exited records stay outside numeric live views but inside
accounting. EMPTY, NO_CHILD, disappearance, fd-close and an empty supervisor list
cannot erase debt. A successful consuming fd wait can certify a known non-root
adopted zombie; an unknown supervisor child cannot gain ownership from PPID alone.
No numeric wait fallback is supported. An exited state cannot revive on a later
empty poll, and terminal records cannot be waited again.

The conservative completeness cost is acceptable as an explicit failed/incomplete
result: a parent-reaped or not-yet-adopted lifetime may lack a certificate even
when no active process remains. The protocol must not represent that as clean
completion. Raising INCOMPLETE when the active view becomes empty with debt fits
the existing success gates. It can also abort cleanup before adoption later
becomes observable; report that conservative failure without claiming all owed
status was collected or extending the deadline. Known active orphan adoption and
subsequent descriptor reaping remain supported. A finite reconciliation pass has
no adoption-wait loop; a growing outer BFS/system call is still not preemptible.

Root Popen exclusively owns its poll/wait/status. Root fd readiness delegates
accounting; it does not supply exit0. Descendant waits exclude the root by record
role, including when another lifetime later reuses the old root number. Signals
target only proved ACTIVE descriptors; ESRCH never authorizes numeric reopen.

The exact pinned v6.6 fork.c2075–2090 emits IN|RDNORM for
thread_group_exited; its exit.c1898–1910 treats a completely gone task as exited
too. With only IN requested, the pinned select filter returns IN for both an
ordinary zombie and a Popen-reaped root. This pidfd_poll has no !pid_has_task/HUP
branch; other pid_has_task uses in that file concern fdinfo/preparation. An
unconditional HUP filter preserves a provided bit, not generates one. A different
kernel variant emitting IN|HUP would be rejected by this exact-mask contract and
could reject an ordinary reaped root. Such a variant needs separate source
qualification before widening masks. HUP alone never supplies a reap certificate;
terminal descendants remain terminal and root status remains Popen-owned.

## Required exact Python mapping amendment

The interpreter reports3.12.14. Independently fetched public CPython tagv3.12.14
source is pinned completely by hash in PYTHON_SOURCE_MAPPING.json. It establishes
reference semantics; it does not attest the deployed build, compiled headers,
kernel interfaces or availability. No wait/poll API was called.

`posixmodule.c:9423–9430` retries waitid after EINTR when PyErr_CheckSignals does
not raise. `selectmodule.c:673–701` likewise handles interrupted poll internally,
checks signals and recomputes its timeout. For timeout0, expiration after an
interruption can produce an empty result. The wrapper cannot promise that every
interruption surfaces as EINTR or that one Python call is one kernel invocation.
An empty poll does not certify an interruption-free interval or revive an exited
record.

Amend the promise to exactly one **Python** poll/waitid call per applicable
record/reconciliation, with no wrapper retry, sleep or alternate wait. Explicitly
acknowledge CPython's internal handling and unknown return latency. Retain the
existing absolute deadline checks after return: normal completion at whole60 is
rejected by its strict comparison; cleanup's existing final comparison permits
equality at its5s deadline but rejects later success. These are observed-success
checks, not hard preemption/kill bounds. If a single-syscall/no-retry guarantee is
required, these Python APIs and the proposed scope cannot provide it; this
adjudication authorizes no ctypes/ABI expansion.

The source maps zero si_pid to **None** (`posixmodule.c:9432`), otherwise returns
integer siginfo fields, and maps OS failure through the normal exception path.
P_PIDFD and option/CLD constants are build-conditional exports. Availability
checks and unsupported/error outcomes remain mandatory; version metadata alone
does not satisfy them.

Freeze these normalization rules and receipt labels explicitly:

| Input observation | Accounting meaning |
| --- | --- |
| Python None | EMPTY debt; no exit status and no successful reap certificate. |
| ECHILD/ChildProcessError carrying ECHILD | NO_CHILD debt; no distinction between external reap and lack of current child eligibility. |
| CLD_EXITED with a positive matching original pid and status0–255 | REAPED, preserving raw si_code/si_status; normalized returncode equals si_status, including valid exit0. |
| CLD_KILLED or CLD_DUMPED with a valid positive signal number | REAPED, preserving which CLD kind occurred; normalized returncode is negative signal. Keep core-dump distinction. |
| Unknown/stopped/continued code, zero/mismatched pid, boolean/malformed status, unavailable API or another exception | Retained failing/unresolved observation, including potentially consumed status; no undo, numeric lookup or retry. |

Validate pid against the descriptor's original record, not the current numeric
table. Validate fd as an actual nonnegative integer (fd0 is legal; bool is not).
Use the supported signal domain rather than accepting arbitrary integers.
Preserve raw fields separately from any normalized returncode. si_status is
**not** waitpid's encoded status: passing it to waitstatus_to_exitcode, or silently
reusing the old encoded `status` label, would change meaning. Clarify that the
proposal's “nonzero eligible exit” means nonzero pid, never exclusion of exit0.
Preserve all five available siginfo fields; require the source-shaped SIGCHLD
signo and typed uid as well. A malformed consumed response remains debt.

## Required old construction amendment

The protected old method
`SupervisorControls.test_tree_does_not_signal_unrelated_process_and_reaps_owned_zombie`
at8cc lines277–281 creates101 already Z/PPID50 before its first observe, then
expects101 removed. It supplies no prior active ownership proof. The new protocol
correctly cannot reap that unseen direct-supervisor zombie.

Before implementation, separately freeze a minimal named construction amendment:
prove101 as an active descendant under the known root, retain its distinct fd,
then stage genuine reparenting/exit before reaping. Preserve original complete
method bytes/output and all unrelated/unowned/reap/close assertions. If explicit
root binding is needed, name that call as part of this exact construction. Do not
change the expected unrelated protection or invent a hidden lifetime ID in the
identity API. A matching unproved-zombie negative must remain incomplete. This
review does not authorize an unseen patch or generic old-test normalization.

## Exact protection scope and remaining implementation gate

The proposed exception is structurally narrow enough: only two unique additive
undecorated LinuxKernel methods `(self,fd)`, named pidfd_alive and reap_pidfd, and
exact separate unaliased select/errno imports. All10 old Kernel methods, their
order/bytes and both original protection JSON files stay exact. Remove only the
additions' exact physical spans before the already adjudicated OwnedTree/FakeKernel
restoration. Reject duplicate/decorated/async/out-of-class/wrong-signature methods,
combined or widened imports, outside helper/comment/decorator mutations and
whitespace trimming. Freeze separators before the future guard executes.
Reconstruct the whole original module/test bytes under the original hashes;
whole-Kernel erasure or changed expected hashes are unsupported.

This supports the scope shape, not unseen method bodies or guard implementation.
OwnedTree/FakeKernel changes still require exact future review. No cleanup,
monitor, acquisition/finally, source-binding, codec/math, canonical output, timing
test, old assertion or root API edit is covered. Pre-pipe observer behavior remains
forbidden. The finite model must use real-shaped API observations backed by
distinct held lifetime objects and include adoption/debt, same-tick alias, root
exclusion, malformed/consumed status, fd reuse and late Python returns. Its exact
registry/count must be frozen before candidate execution; none ran in this review.

Winner: the retained descriptor/debt design over stale numeric ownership, with
actual CPython mappings governing the API promise. Largest remaining gap is the
amended interface/receipt/construction contract and its unimplemented proof under
the full existing callers. The source candidate needs a separate different
independent implementation reviewer. Missing child-list capability, inherited
composition blockers and the consumed failed acquisition remain; no native/API,
proc, poll, wait, pidfd, helper, signal, SDK/CI, capability, study or Linux retry
occurred or is authorized here. Receipt09b evidence is untouched.
