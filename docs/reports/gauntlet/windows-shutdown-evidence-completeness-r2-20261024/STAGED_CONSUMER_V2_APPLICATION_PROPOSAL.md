# Exact staged V2 consumer proposal; not applied or executed

Base is currentd27ee9c6/d7aba source. Preserve all0f/67a/63021/7686/8ba drafts,
inputs and failures. Clock-only3f30af0f permits exact V2B definition conditionally;
it does not permit this consumer, compiler, data or source validator. The existing
DIFFERENT critic must preregister/review this exact file/hash before application.

## Proposed source/test construction changes

1. In scripts/shutdown_evidence_fixtures.py, rename the current exact original
   write_complete_trial function to _write_format_trial_v1 without changing its
   body. It remains a private synthetic content generator, never the evidence
   oracle or production loader. Its already permitted reload_before is20000.
2. Add only imports math/tempfile needed by adjacent
   STAGED_CONSUMER_V2_PROPOSAL.py. Copy that exact code (functions and class) into
   the fixture module. Copy the exact CLOCK_SEAM_V2B_PROPOSAL.py definition (with
   math already imported); do not substitute an altered clock.
3. Add this exact public wrapper after those definitions:

   def write_complete_trial(directory,identity,*,verbose=False,client_pid=101,
                            reopened_pid=201,observer=None,clock=None):
       if clock is None:clock=DeclaredClock()
       return write_declared_trial(directory,identity,clock=clock,
           format_writer=_write_format_trial_v1,snapshot=_snapshot,verbose=verbose,
           client_pid=client_pid,reopened_pid=reopened_pid,observer=observer)

4. In _snapshot, change only monitor sample literals draw_calls100→100.0 and
   primitives1000→1000.0. Source Performance.get_monitor produces floating counts;
   actual archived type/hash witnesses are retained in r6. This changes synthetic
   representation, not old raw logs. Game frame counters remain integer.
5. Apply only the previously reviewed five-site helper patch from
   CLOCK_HELPER_V2_PROPOSAL.patch: import/create one clock for all four trials,
   healthy query clocks, explicit fixture clock argument, and entire collector
   study.time facade. All old28 methods/113 assertions/Owner, query/fault/read
   schedules, accounting increments, failure artifact, failure branch and original
   callbacks stay unchanged. Existing new30's permitted two adapters stay exact.

No new production/default-driver/ownership/binding/retention/CI/route input change.
No fixture/helper edit or consumer call is authorized until independent decision.

## What the code constructs

V1 is called without an observer only inside a fresh private TemporaryDirectory to
precompute synthetic solid PNG/OCR/profile/snapshot content in memory. This is
not an attempt, source execution or retained native evidence. It creates no target
output or callback. Only its known synthetic path fields are explicitly rebased;
no archived/native bytes, general filters or reader inputs are normalized.

The staged producer then creates fresh owned target metadata/streams and emits
commands, callbacks, captures and OCR in source order, on the one declared clock.
A launch callback failure therefore stops before future captures/OCR/traces;
only actual modeled stage outputs plus the original-failure artifact remain.
Unknown/preexisting extras survive; preexisting producer files/symlinks reject.
All intermediate target metadata belongs to this fresh constructor; no preexisting
producer output is overwritten. Failed stages write explicit passedFalse/error
and preserve their partial streams/metadata before raising the original cause.

Macros carry one held-key state, explicit source pauses, input edges, button's
pre-delivery trace, waits/observed returns, deploy/focus loss/restore and direct
scoped Escape releases. Required source operations from2904 and the prior full
inventory appear in run()/hud()/named()/focus(). Frame and predicate snapshots
are declared synthetic content; no source predicate, actor life or seed is retried.

Native trace content is generated from declared snapshot transitions following
offline_diagnostics observe's phase/round/objective/contribution and local reload/
weapon/alive/utility edges, plus two declared local-shot signal snapshots. Status
is its own last publication; initial event/profile/seeds remain distinct from
later status. Event indices/observer clocks are explicit and files bind actual
bytes. This finite synthetic publication sequence does not establish that all
physical/native histories or notifications were observed.

The Windows route declares six pulse iterations, with15 ordered deduplicated
feedback snapshots (start plus14 fresh reads), source entry/finally release keys,
neutral settling pairs, distance/rate-derived durations, pulse-before/after and
release/completion records. Every native pulse gets source-shaped OS/check/edge/
wait/release fields tied to the current client PID and same original deadline.
This is a declared algorithmic feedback example; it does not prove a physical
trajectory, SendInput delivery or OS truth. All pulse operations are in-memory
receipt construction; WinUI/key_pulse/main/API are never called.

## Limits and planned checks after adjudication

Untraced pauses and selected operation/poll costs advance only the fixture clock,
never real sleep or runtime deadlines. Equal reads are legal; the four-arm clock
does not reset. Per-trial relative clocks restart at that trial's origin; process/
query/close stamps follow the same schedule rather than being edited afterward.
Original native logs are not cleaned or reused as synthetic positives. Existing
fixture snapshots/solid pixels and mocked OCR remain format data, not a qualified
complete physical/gameplay history, stock-RNG reconstruction or rendered timing.
Independent gameplay/native approval remains UNREVIEWED, and public collect BLOCKED.

The replacement and application are UNEXECUTED. After an explicit construction
permit, run the real fake-main wrapper and whole pure fixture/loader checks on
CPU4, compare old28/113/Owner and every preserved mutation, repeat exact81 original
cases separately, version source-faithful new controls without changing originals,
retain failed iterations, and qualify exact source plus initialized depth. Another
independent source verdict is still required; a construction permit cannot close it.
