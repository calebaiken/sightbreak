# Finite pure plan for a later registered implementation

No model or test executed in this task. Before future execution freeze generated
input schedules, expected states, API-shaped observations and hashes independently
of candidate results. The builder cannot approve the result. CPU4 pure only;
production poll/wait/pidfd/proc/signal/Popen entrypoints must be fail-on-use guards.
No capability/native retry follows from a model pass.

The kernel oracle uses distinct lifetime objects. A numeric table maps pid to its
current object; fds map to the originally opened object through exit, reap and
numeric reuse. identity(pid) exposes only real API-shaped fields, never the
oracle's lifetime ID. pidfd_alive observes the object's thread-group exit state;
reap_pidfd checks that object's current child eligibility/waitable status and
consumes only that object's status. Root's fake Popen owns a separate wait log;
any attempted descriptor wait on its root record fails the test. New identities
may intentionally share pid/start_ticks with an old object. fd integers may be
reused only after close, with old record serials remaining distinct.

Bound the generated state space to supervisor plus at most six lifetime objects,
five state events per record and two API-query cuts per event. Use only legal
oracle operations from fork-under-owned-parent, exit-thread-group, adopt-to-self,
reap-by-current-parent, reap-by-supervisor-fd and reuse-number. Generate every cut
before/after each held check, numeric read, children read, fd open, child reread,
queue visit and live view. Seal the exact resulting finite registry/count before
candidate execution; do not infer expectations or reduce domains from its output.
No production process-count or runtime-performance bound is claimed by this
finite model bound.

The explicit required seeds and paired counterparts are:

| Family | Expected proof |
| --- | --- |
| Original two same-tick parent-reuse schedules and stale live case from85c | No foreign adoption or successful signal; old descriptors never retarget. Preserve original assertions/results; any new fake-API adapter is additive/registered. |
| Changed-tick replacement versus same-tick replacement | Both reject old-lifetime ancestry, without relying on different ticks. |
| Replacement before/inside enumeration, before/inside open/reread and queued revisit | Parent/child retained checks prevent stale ownership at every cut. |
| Stable three-generation tree | Original held descriptors/ancestry survive, no always-reject workaround. |
| Known child reparented to supervisor while active | Same child fd survives adoption; a later waitable zombie is consumed/logged by fd. |
| Unseen direct supervisor child or unproved zombie | No ownership from PPID/group alone; unresolved and no signal/reap. |
| Ready adopted zombie versus ready already-reaped lifetime | Both poll EXITED; only successful fd wait certifies the former. NO_CHILD for the latter stays unresolved. |
| Ready non-child before adoption, then successful adoption/wait | Pending debt is retained; no empty success before proof. Conservative zero-active INCOMPLETE is permitted and reported. |
| Parent reaps a descendant before observation can obtain a certificate | NO_CHILD does not certify external reap; final result remains INCOMPLETE. This is an explicit completeness cost. |
| Old terminal fd plus new owned same-key lifetime | Separate serial/descriptor, original terminal certificate retained; no overwrite. |
| Root exits/zombifies/reaps with Popen status0/nonzero/signal | Root descriptor never waited by tree; outer Popen wait/status proof remains authoritative. |
| Zombie leader with active sibling threads | pidfd is still ACTIVE; no premature whole-group exit/reap claim. |
| EMPTY and NO_CHILD despite exit readiness | Neither produces REAPED or accounting closure. |
| Missing interface, malformed status/fd/mask, error, late return | Explicit unresolved/failure; no numeric fallback or success. |

For poll wrapper unit controls use fake select.poll/register/poll only. Cover
empty, exact(fd,POLLIN), duplicate/foreign fd, RDNORM-only, IN|unexpected bits,
ERR/HUP/NVAL and raised errors. Enforce only POLLIN registration and timeout0.
A ready record never becomes active on a later empty response.

For wait wrapper unit controls use a fake os.waitid only. Assert exact
P_PIDFD/retained_fd/WEXITED|WNOHANG and absence of WNOWAIT/P_ALL/P_PID/waitpid.
Cover valid exited/killed/dumped status, EMPTY, ECHILD, unavailable/error and
malformed/zero pid/status records. The tree validates diagnostic pid against the
original record, never current numeric lookup. A malformed consumed result stays
failed; no retry invents an undo. Root-record exclusion uses role/reference even
if another descriptor later has the root's old numeric PID.

Protection controls must remove exactly the two unique method/import additions
and reconstruct full old bytes under original JSON hashes. Mutate every old
kernel method, import alias/set, adjacent comment/decorator/helper and outside
source byte independently; all must remain visible and fail the old baseline.
Reject missing/duplicate/decorated/async/out-of-class methods. Freeze any exact
method separators before testing; do not trim whitespace to recover a donor.
Old31 method/assertion bodies and all historical failures remain recoverable;
only already adjudicated class scopes/model APIs may change. Any old constructor
conflict needs separate precise adjudication, not a false positive expectation.

Deadline models retain WHOLE60/CLEANUP5 and absolute clocks from the existing
source. Exercise returns just before, exactly at and after relevant boundaries,
including a syscall-shaped fake that advances time past deadline before returning.
No new call may sleep/retry or reset cleanup's deadline. Late completion cannot
produce passed=True. Source calls are not physically preemptible; model success
is not a hard wall-time guarantee or a host availability/performance measurement.

Reproduce original maintained/literal/adapter results separately, with no original
failed run reclassified as success. Only after a different critic qualifies the
exact implementation, full source composition and both initialized views could
a scoped source verdict be considered. None is supplied by this proposal.
