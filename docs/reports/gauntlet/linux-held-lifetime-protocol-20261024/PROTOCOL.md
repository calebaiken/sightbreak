# Descriptor lifetime protocol for separate pre-edit adjudication

This is a proposed source contract, not implemented, approved or runnable. Source
8cc38cdcd7dfff37056782149e513c08037e4e77 remains rejected by85cba435, and the
e4685e48 adjudication remains binding. No Linux process/proc/poll/wait/pidfd/API,
native, capability, helper, CI, engine or new test ran. R5 source stayed frozen.

Recommend retaining every proved descriptor through an explicit exit/accounting
state machine, with a second descriptor-bound nonblocking reap primitive. Numeric
PID/start_ticks never identifies a lifetime by itself. An exited lifetime that
cannot be proved reaped remains unresolved; it cannot disappear from the success
proof merely because live() no longer reports it. The conservative cost is that
some genuinely clean, parent-reaped descendants remain INCOMPLETE without an
observable reap certificate. This protocol does not label ECHILD as success.

## Evidence boundary

SOURCE_IDENTITIES.json pins the original implementation, tests/protection data,
four root proposals at88a9443f, original two independent verdicts and retained
Linuxv6.6 sources, including exact Git blobs/full-file SHA-256. No full report,
receipt or kernel corpus was copied into this small docs checkout.

The pinned reference supports these distinct facts:

- fork.c2075–2088 polls the held struct pid for whole-thread-group exit;
  fork.c2147 retains that struct pid independently of numeric namespace reuse.
- exit.c1890–1910 includes zombie/dead/completely gone lifetimes in exit readiness.
  Readiness is neither a reap certificate nor a currently visible PID certificate.
- select.c855–880 returns requested event bits plus ERR/HUP. Request only POLLIN;
  ordinary exit is exact POLLIN for that retained fd. Reject other descriptors,
  masks, errors and unknown results instead of treating them as alive.
- exit.c1682–1704 binds P_PIDFD through pidfd_get_pid; numeric P_PID uses
  find_get_pid. The descriptor choice prevents waiting on a replacement PID.
- exit.c1099–1128 and1198–1228 distinguish WNOWAIT from consuming exit status.
  WEXITED without WNOWAIT claims a zombie atomically and releases it when eligible.
- exit.c1380–1465,1600–1640 can return ECHILD for no eligible child, or no status
  under WNOHANG even though an eligible child exists. Neither proves prior reap.
- exit.c615–723 describes reparenting to a surviving parent thread, nearest
  subreaper ancestor or namespace init. Genuine known orphan adoption is allowed;
  parent-group/session coincidence does not establish that provenance.

These are a pinned reference model, not host-kernel/Python availability or an
actual race measurement. No external CPython waitid implementation was fetched
or executed. Before implementation, the wrapper's exact os.waitid result/None/
exception mapping must also be source-pinned for the intended Python release;
this is an explicit remaining interface prerequisite, not a host support claim.

## Lifetime records and admissible ancestry

Keep a private record for each successful held-descriptor binding. Its primary
identity is a new local serial plus the retained fd association, not a PID/birth
pair or the integer fd alone. Preserve diagnostic pid/start_ticks and an index
from that projection to records, permitting collisions. For existing outside
receipt compatibility seen may use (pid,start_ticks,serial) keys, preserving
key[0], while internal ownership always uses the record reference. Root is an
explicit role on its original record, never inferred anew by pid equality.

A fresh candidate becomes proved only while its parent lifetime and newly opened
child lifetime remain active around identity lookup, children enumeration,
opening and reread. Validate the permitted parent edge and unchanged child
projection; do not use a ready/exited parent to certify the current numeric
parent. Recheck held parent before/after enumeration and child binding. Reject
unproved candidate fds and close only those unproved handles. An already exited
new fd cannot certify that its current numeric projection is the same lifetime;
keep that discovery unresolved, with no signal/reap/adoption permission.

For a known live child, a permitted parent is its still-active proved parent
record or the same executing supervisor after genuine reparenting. The child's
own held fd must remain active around the numeric reread; original ownership is
retained through the change. An unseen direct supervisor child is not an owned
orphan solely because PPID equals supervisor. Root is admitted only by the known
Popen bind path. If prior ancestry was never observed, keep discovery unresolved.
The supervisor actor cannot die/reuse its PID while continuing this Python
execution; its original identity checks remain. No global process scan is added.

After an old record exits, a same-PID/same-start-tick numeric row does not restore
it. A new independently proved owned lifetime receives another serial/fd record;
a foreign replacement is rejected. Old exited/unresolved records remain present.
An fd remains open until final close; a reused integer fd after an unproved close
cannot resurrect an older record. A source-matching start tick is diagnostic only.

## Exit and accounting states

| State | Evidence and permitted next action |
| --- | --- |
| UNPROVED | Candidate only; never parent, signal or reap authority. |
| ACTIVE | Exact held-fd empty readiness result; eligible for guarded ancestry/numeric reads and fd signals. A zombie leader with live sibling threads can still be ACTIVE. |
| EXITED_PENDING | Exact held-fd POLLIN; no further numeric liveness/ancestry/signal permission. Retain and try descriptor-bound accounting. |
| EXITED_UNRESOLVED | Descriptor-ready plus NO_CHILD/EMPTY/unknown ownership; retained debt, not a reap certificate. It may later become waitable through genuine adoption. |
| REAPED_BY_SUPERVISOR | Successful consuming descriptor-bound exit result for this non-root record; exact status logged. Terminal accounting. |
| ROOT_EXITED_DELEGATED | Root fd ready; only Popen.poll/wait owns its status. Excluded from descendant reap, with separate existing outer root-wait gate. |
| CLOSED | Final resource release after success or failed cleanup; never converts unknown accounting into success. |

EXITED is absorbing: a later empty poll cannot revive ACTIVE. API failure leaves
an explicit unresolved/failing record. A dead PID disappearing from numeric lookup
or being reused never supplies a terminal transition. An exit status consumed by
another parent is not distinguishable here from a not-yet-adopted child through
ECHILD alone; both stay unresolved unless this protocol obtains a consuming
certificate. This sacrifices completeness rather than claiming an absent debt.

reap_descendants() iterates all held non-root EXITED records, not live(). For each
it makes at most one nonblocking descriptor wait per reconciliation pass. It
never calls existing numeric reap(pid), waitpid(-1), waitid(P_ALL), P_PID or a
fallback numeric wait. A successful wait consumes the known descriptor's child
status and logs it once. Repeated visits to a terminal record do not wait again.
Adoption is operationally established by the descriptor wait succeeding as an
eligible child, not by trusting an unrelated numeric Z/PPID projection.

Before returning a live() view, reconcile pending exit records once. Return only
proved ACTIVE records, never an exited/replacement numeric row. Pending debts may
coexist with active owned records, so existing monitor/cleanup loops can continue.
Crucially, **live() must not return an empty success-compatible list while any
non-root record or discovery remains unresolved**. It raises a precise INCOMPLETE
failure in that case. This fits the existing outside empty-list success gates
without fabricating live zombie entries that numeric affinity checks might read.
Reconciliation happens even if ordinary liveness filtering removed every zombie.
A newly adopted waitable zombie is reaped before this empty-view decision.

That is intentionally conservative. NO_CHILD followed by an empty supervisor
list still does not prove a previously held descendant was reaped. If adoption
cannot be proved before the zero-active boundary, fail/inconclusive; do not spin,
drop a record, extend a deadline or certify an external reap. A known orphan
adopted while active, then exited and successfully waited by fd, remains a normal
supported success trace. Unsupported ptrace/clone/wait-owner interferences stay
unresolved; no __WALL or WCONTINUED scope widening is proposed.

## Exact new Kernel contracts requested, not authorized

Retain all ten original LinuxKernel methods, their signatures/order/physical bytes,
including numeric reap(self,pid), unchanged. Do not instantiate/experiment here.
Request exactly two additive undecorated synchronous methods, both (self,fd):

1. pidfd_alive: create a fresh poll object, register only that fd with POLLIN,
   poll with timeout0 once. Return True only for an empty result; False only for
   exactly [(fd,POLLIN)]. Missing poll/constants, foreign/duplicate fd records,
   POLLERR/HUP/NVAL, other masks, malformed results and exceptions raise a precise
   unavailable/error result. Do not return a permissive boolean on uncertainty.
2. reap_pidfd: validate waitid/P_PIDFD/WEXITED/WNOHANG availability, call exactly
   os.waitid(os.P_PIDFD,fd,os.WEXITED|os.WNOHANG), with NO WNOWAIT, once. Return
   a tagged result: REAPED with original siginfo pid/code/status for a nonzero
   eligible exit; EMPTY for the documented no-status result; NO_CHILD only for
   ECHILD. Unexpected/invalid result, unsupported exit code kind,
   EINTR/EAGAIN/EBADF/EINVAL/ENOSYS or other errors remain explicit
   unavailable/error, never REAPED. No internal retry, sleep or alternate wait.

The wrapper must preserve CLD_EXITED/CLD_KILLED/CLD_DUMPED distinction; a stopped or
continued result cannot close exit accounting. EMPTY is not zero exit status.
NO_CHILD is not 'already reaped'. Reap record identity is the supplied fd's held
lifetime, not a new lookup by returned si_pid. Validation of expected pid occurs
against the original record by OwnedTree, with no numeric lookup. A malformed
returned status may already have consumed kernel wait state; retain that raw
result as unresolved/failing rather than pretending to undo it or retrying by
PID. Before invoking the wrapper,
OwnedTree must exclude its designated root record by role/reference, not by
comparing numeric PID: a later descendant may legally reuse an old root number.

Request only exact additional unaliased lines `import select` and `import errno`.
Existing os/signal imports serve waitid/status constants. Do not edit old kernel
availability/preflight methods or invent success if those new facilities are
unavailable. Missing facilities mean no accepted correction/native admission.
This proposal is not permission to test or calibrate them. The intended Python
source mapping noted above must be pinned before a final method body can freeze.

## Root ownership, signals and success proof

Popen alone owns root poll/wait/status. No descriptor wait may target that root
record, and no generic wait may accidentally collect it. Root fd readiness only
means ROOT_EXITED_DELEGATED; it does not invent returncode0 or satisfy the existing
Popen.wait==poll-status assertion. Failed bind still preserves Popen safety cleanup.
Initial tree construction remains API-free and immediate stdout/stderr retention
still precedes bind_root/any new observer API. Root parent/session/executable/
affinity checks, strict log/input/receipt rules and consumed failed550 stay intact.

signal_all acts only through a currently proved ACTIVE record's retained fd.
A subsequent ESRCH means that lifetime exited; no numeric reopen/retry can retarget
the signal. Exited/pending/reaped records are never ancestry parents or signal
candidates. Numeric reads used as evidence require held-lifetime checks around
those reads. This design does not claim atomic /proc snapshots or certify the
unchanged outer affinity/executable readback as a new physical observation.
Those inherited composition gates remain separately reviewable/blocking.

For a cleanup pass to report success, the original outer conditions still all
hold: bound original root, Popen exit/status wait proof, no ACTIVE owned record,
no unresolved held/discovery debt, no supervisor child left unaccounted, complete
required pipe draining and no observer/drain failure. Closing descriptors is not
part of that proof. A known reaped descendant remains in the receipt history.
No owed-child claim may be derived solely from readiness, numeric absence, an
empty child list, ECHILD or fd close.

Keep WHOLE_SECONDS60 and CLEANUP_SECONDS5, existing absolute deadlines/CPU/stream
caps and one admitted native-invocation policy. New calls are nonblocking, one
attempt per finite reconciliation snapshot, with no inner drain/sleep/retry loop.
Existing whole-flow/cleanup clock checks must reject any success observed late;
no new relative timeout may extend those deadlines. Syscalls/proc reads and an
existing growing BFS cannot be preempted by Python: this is an observed-success
deadline contract, not a guaranteed wall-time kill bound. If per-call/preemptive
or inner-BFS deadline guarantees are required, existing interfaces do not prove
them; separately register exact caller/budget changes before implementation.
No such outside-source edit is requested or hidden in this two-method scope.

## Exact protection boundary for future adjudication

The previously proposed one-method exception is insufficient. Request only:

- OwnedTree and FakeKernel remain their already adjudicated editable classes.
  New model classes stay nested in FakeKernel or in new test files; no broad
  helper/import/protected-kernel donor replacement is allowed.
- Two unique methods LinuxKernel.pidfd_alive and LinuxKernel.reap_pidfd plus the
  two exact unaliased imports above. Reject missing/duplicate/decorated/async/
  malformed/out-of-class additions and wrong signatures or combined imports.
- Add only their exact physical-method/import erasure in the existing protection
  reconstruction stage before the already allowed OwnedTree/FakeKernel donor
  restorations. Freeze exact separator/import deltas; preserve all adjacent
  comments/decorators/blank bytes. No rstrip, whole-class erasure, changed donor
  or LinuxKernel normalization that can hide old-method edits.
- Reconstruct the complete original protected module/test bytes, not just slices
  omitting imports. Keep scripts/fixtures/fov_binary_protected_segments.json and
  fov_owned_ancestry_baseline_segments.json byte-exact, including original old-test
  erasure SHA44154d83d97c32ef688587f1f96190b6c880d306606792d85ad38fdce11b5978.
  Source kernel methods/hashes are listed in SOURCE_IDENTITIES.json.

No cleanup/monitor/acquire/finally, native program, math/codec, canonical receipt,
old assertion or root API method edit is authorized by this proposal. The separate
physical-binder timing-constructor adjudication at e468 is not broadened here.
FakeKernel must gain API-shaped fake readiness/wait results bound to distinct
lifetime objects; fd==PID or hidden lifetime IDs returned by identity are invalid
models. Any old constructor compatibility conflict must retain original output
and receive a precise separate amendment, not weakened assertion expectations.

## Remaining gate

A DIFFERENT critic must adjudicate the protocol, conservative completeness cost,
Python interface mapping, exact two-method/two-import scope and success gate
composition before any code. The finite plan is in PURE_MODEL_PLAN.md. No model
or production test was executed by this design task. Existing child-list absence,
rejected ownership source, source-binding/native-input issues and consumed actual
attempt remain blockers. Nothing here releases a process, capability probe, retry,
new native acquisition or study.
