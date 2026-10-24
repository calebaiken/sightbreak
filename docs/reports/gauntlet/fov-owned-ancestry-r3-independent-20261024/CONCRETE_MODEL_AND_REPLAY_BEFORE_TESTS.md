# Concrete process models and legacy adapter, before any test

Source8cc/handoff980 is physically/object-bound;525 union/3changed2new/520protected.
Own and exact one-commit view materialize362/omit163 pinned paths; builder525
physical modes/blobs/bytes also independently match. Exact depth index11643,
count1, HEAD^ fails128, clean. No candidate pure/model method has run yet.

Pinned public Linuxv6.6 is a supported reference model, not an identification of
the unprobed actual kernel/configuration. kernel/pid.c removes a terminated PID
from the namespace IDR at155 before delayed put_pid; fork.c2147 retains struct pid
for each pidfd; fork.c2075 poll reports whole-group exit. array.c577–578 serializes
start_boottime through nsec_to_clock_t; time.c733–745 performs integer division.
PID allocation atpid.c215/236 does not couple number allocation to that clock
quantum. Thus the exposed birth counter is many-to-one and held pidfd lifetime
can differ from a reused numeric PID. Source permits explicit PID selection as
well as cyclic allocation; no settings/capabilities were inspected or changed.
This establishes an interface-permitted model, not its likelihood or an actual
race at550. The failed fs/pidfd.c URL lookup404 is retained; pinned implementation
was found in kernel/fork.c. Public source reads involved no kernel interface call.

Independent kernel fixture will represent each lifetime as a distinct object.
Numeric identity returns only real API-shaped pid/state/ppid/pgrp/session/start_ticks.
Fake pidfds reference lifetime objects permanently; an exited object's handle
raises ProcessLookupError on fake send and reports exited through a separate
model readiness view. A numeric PID reuse never retargets that old descriptor.
No implementation-specific readiness method is supplied to force a particular
fix; this tests the currently exposed observer behavior.

Stable positive: supervisor50/birth1, root100/birth900, owned parent200/birth1000,
owned child300/birth1000, unrelated999. All genuine edges remain stable. Positive
orphan: already verified parent200 survives root100 exit and reparents to50 with
same descriptor; its genuine child remains owned. These must preserve only owned
lifetimes and never signal50/999.

Blocking falsifiers, differing only in injection point: after parent200 is proved
and its old lifetime descriptor held, that lifetime exits/reaps. Unrelated999
creates a new lifetime atPID200 within the same exposed start tick1000, PPID999,
and a child300/PPID200 in the same tick. Trigger (a) before queued-parent lookup,
(b) inside children(200) enumeration. Parent/childgroup=session999 can differ
from old group's100. Old pidfd remains exited. Require no new300 adoption and
no fake signal to its unrelated lifetime, whether observer returns or rejects.
Run the identical during-enumeration trace with new birth1001 as a non-collision
negative: safe RuntimeError rejection/no outside adoption remains required.

Also verify live() does not report a replacement foreign lifetime through an old
exited descriptor; stale foreign child-list PPID and child reparent during open
must reject/close unproved handles. Independently reconstruct complete baseline
process/test bytes from exact329 donors and verify constructor/pipe ordering.
Every result retains full logical events, lifetime→fd mapping and fake signals.
Expect nine independent methods; failure/subtest events are counted separately.

Literal legacy replay selects ONLY these two unchanged f323 methods:
test_stale_children_pid_with_unrelated_parent_is_never_owned_or_signaled and
test_queued_owned_parent_reuse_cannot_import_unrelated_descendants. Preserve their
source verbatim and literal output/errors. The other four legacy methods are
out-of-scope inherited binding/previous actual/unchanged cleanup checks; no second
physical-binding experiment or actual-input replay occurs. Literal RuntimeErrors
may mean safe rejection, not an unsafe import.

Separately adapted replay wraps ONLY observe(), catches ONLY exact known
RuntimeError messages child ancestry differs from observed owned parent or queued
owned parent birth identity changed, and then verifies no target unrelated birth
was adopted or signaled before allowing original assertions to continue. A stale
child rejection must exclude200; a queued-reuse rejection must exclude300. Any
other exception or failed postcondition stays a test failure/error. Preserve
literal vs adapted outputs separately and do not relabel literal errors as passes.

Run maintained62 plus independent9 and literal/adapted2 in each source view onCPU4.
Inside every suite, forbid real Popen/os.kill/pidfd_open/pidfd_send_signal/ctypes
effects. Fake kernel calls are the only process observations/signals. No engine,
helper, /proc/interface trial, namespace/PID manipulation or native retry.
