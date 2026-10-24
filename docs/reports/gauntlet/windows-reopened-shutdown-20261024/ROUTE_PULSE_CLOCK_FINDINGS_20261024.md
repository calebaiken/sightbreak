# Route-pulse clock failure: read-only findings

Official diagnostic run 40083894472 / job 120842796227 ended before reopened
launch. The retained failure is `Native route pulse sleep returned before its
requested boundary`, elapsed 102.2349999999999 seconds, initial_exit/reopened_exit
null and cleanup_errors[]. This is INCONCLUSIVE for reopened shutdown. No leak
identity or production lifetime conclusion follows from this attempt.

The original bounded raw directory is
/workspace/reviews/windows-reopened-verbose-actual-20261024/.local/windows40083894472/full/offline-input.
The existing actual critic owns its independent reconstruction. This report
reads those original bytes without changing them. No new tests, timing experiments,
code edits, native process, export, CI or retry were executed for this inspection.
All source/raw inspection commands used CPU4. A guessed native_route_pulse.py path
search failed with exit2; key_pulse is actually in verify_integration_export.py.

## Exact retained anchors and limits

results.json pointer /settings_cover_route/native_pulses/1 records D input:

- Pulse requested_seconds 0.12567175974707734, floathex 0x1.0160321127de0p-3.
- Stored hold_until 768.093671759747, floathex 0x1.800bfd6fac561p+9.
- Down API before/after 767.968, floathex 0x1.7ffbe76c8b439p+9.
- Release API before/after and finished 768.093, floathex 0x1.800be76c8b439p+9.
- Original route absolute_deadline 796.718, floathex 0x1.8e5be76c8b439p+9.
- D release_complete is true, with no release errors and neutral final OS bitmap.

The down-to-release API bracket difference is exactly 0.125 seconds in the
retained binary floats. Stored boundary minus release is exactly
0.0006717597470924374647438526154 seconds. One ULP at this boundary is
1.1368683772161603e-13 seconds; the gap is 5,908,861,224 ULPs. Rounded addition
of the requested pulse duration at the down anchor differs by about 1.51e-14
seconds, so floating-point cancellation alone cannot account for the gap.

Zero-based actions 152/153 bracket the controller callback at elapsed
101.2349999999999/101.42199999999991 seconds and Unix milliseconds
1792836429550/1792836429740. Action 162 records failure at elapsed 102.0 seconds.
Those include controller tracing and other work and do not isolate sleep entry
or return. route-pulse-actual-timing.json retains the full failed pulse, selected
actions, exact floathex/decimal representations and original byte hashes.

The literal sleep argument is not recorded. requested_seconds describes the
pulse's original requested budget. Source computes a smaller residual wait after
OS checks/input calls. The exact clock samples used to construct the hold
boundary, calculate wait and make the immediate post-sleep comparison were not
retained. The first release timestamp comes after the failing comparison. These
anchors prove a failed boundary observation, not physical short sleep.

## Exact controller and runtime source

verify_integration_export.py439 defaults to clock=time.monotonic and
sleep=time.sleep. Offline caller verify_offline_export.py747–758 supplies no clock
or sleep override. key_pulse501 stores H=min(clock()+seconds,deadline),527 computes
wait=H-clock(),530 calls sleep(wait), and531–532 rejects a fresh clock sample below
H. This predicate uses the absolute boundary directly, so an after-start subtraction
rounding slightly short is not its failure mechanism. Attempted keys are released
through finally535–547 even after that rejection.

Official results controller argv identifies
C:\hostedtoolcache\windows\Python\3.12.10\x64\python.exe. Complete official
job.log line 209 states `Successfully set up CPython (3.12.10)`;
route-pulse-python-identity.json binds the 1,228,778-byte job log and that line.
No actual get_clock_info implementation/resolution readback was retained.

Upstream [CPython v3.12.10 pytime.c1053–1092](https://github.com/python/cpython/blob/v3.12.10/Python/pytime.c#L1053-L1092)
implements Windows monotonic using GetTickCount64, an integer millisecond count,
then converts to nanoseconds/float seconds. Its clock-info resolution is obtained
from GetSystemTimeAdjustment's timeIncrement. The actual runner's numeric clock
resolution was not measured, and integer-millisecond storage does not establish
a one-millisecond update cadence.

Upstream [timemodule.c2278–2347](https://github.com/python/cpython/blob/v3.12.10/Modules/timemodule.c#L2278-L2347)
rounds the relative sleep timeout upward into 100ns units, sets a waitable timer,
and waits for its timer signal. It does not use the same GetTickCount64 value as
an absolute timer target. Thus a normal waitable-timer return need not coincide
with a coarse monotonic tick crossing the fractional stored boundary. This is a
source-supported clock-resolution explanation to test, not proof of actual
physical sleep duration in this run.

Fetched pytime.c is 33,421 bytes, SHA256
033751b3c90dd12cd40b86af11388a0a201bc44deca0e96b52b4a13da8be82c9.
Fetched timemodule.c is 66,285 bytes, SHA256
81ce33b3f784a9abae1663576424faabb9c584d84f36daa4c27d0e16195c76b0.
The accompanying cpython-31210-*-source.json files retain exact URLs, full-source
hashes and line-numbered bounded excerpts.

## Proposed pure correctness cases, not yet executed

1. Preserve the old exception/release result with the exact retained boundary
   and edge-anchor values. Do not describe it as a physical timing reconstruction.
2. Vary independent fine sleeper time and coarse clock tick phase/cadence. A
   valid sleeper can return before the next coarse tick; compare that with a
   genuinely early sleeper return.
3. At nonzero and large epochs, compare samples exactly at H and one float below
   or above. Keep absolute comparisons separate from rounded elapsed subtraction.
4. Charge state/dispatch costs against the fixed original H. Every further wait
   must request only the current positive residual, never a restarted duration.
5. Exercise exact/just-before/after original absolute deadlines, including a hold
   boundary clipped by that deadline. Late completion must reject after releasing.
6. Repeated early wakes, clock stall/backward/nonfinite values and sleep/read
   exceptions must not accept early release or leave attempted controls down.
7. Existing invalid request, ownership/focus/physical input, controller-finally,
   late release, original schedule and strict native-log guards must remain.

A residual-wait correction can preserve H and the original absolute deadline.
A permanently stalled clock cannot bound itself; an additional conservative
elapsed-only watchdog using the already-existing remaining duration was reported
to root before any edit. Its absolute epoch must never be compared with the
monotonic deadline. The scoped builder work, if admitted, belongs to a new sparse
worktree/branch at frozen 7101350e; this read-only report does not alter the old
shutdown source or authorize native execution.
