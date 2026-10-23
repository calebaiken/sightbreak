# Focus-resume scheduling hypothesis, source only

Registered on 2026-10-23 after the fence correction freeze `fa718ef` and pure
evidence `f8a72e9`. Independent review `0d4f7e0` supports reviewing this separate
hypothesis after correction; it grants no native approval or survival guarantee.

The actual failed Windows trace has Escape-up completion at controller 137.703
and resume-wait start at 138.828. Current generic `tap()` deliberately sleeps
one second after key-up, while ordinary gameplay may already have resumed. This
known idle wait is the named, inspected engineering bar. No source-delta, bot,
capture-cost or physical-latency cause is inferred from that trace.

Change only the focus-resume invocation following 11a: replace `tap('Escape')`
with Escape-down, the same `pause(.3)`, and Escape-up. Immediately enter the
unchanged explicit unpaused ACK wait. Keep generic tap behavior everywhere else.
This is a scheduling hypothesis for one fixed-order future trial, not a retry
loop or a search for a later life, round or seed.

Preserve the corrected raw/type/freshness fence, 0.3-second key hold, explicit
ACK, complete one-simulation-second inertia constraint, both fresh neutral
samples, all 11a/11b/11c captures and context fences, physical W/LMB release ACK,
fresh-W fence and original ten-second/stage/whole deadlines. Health, AI, scene,
game tree, CI and canonical mission records remain unchanged.

Pure controls must execute the actual extracted focus-resume statements and
original dispatch/pause/wait helpers. Check hold duration, absence of the post-up
second, delayed explicit ACK, original ACK timeout and whole-budget capping,
existing cleanup of a held Escape when a deadline prevents completing the hold,
and unchanged generic tap delays. Compare controller AST against the fence-only
freeze, allowing exactly this one invocation replacement. Replay the unchanged
77 independent cases and existing focused controls on the final combined source.

Freeze separately, retain source-bound logs and handoff, then obtain independent
review and exact combined-source approval before any single living-input
acquisition. No engine, import, UID, native input, OCR executable, export, CI,
service or runtime retry is authorized in this component.
