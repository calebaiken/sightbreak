# Independent source review: REJECT

Frozen code `19304d5d736b09326d5d2503da09dc8cf7b45129`, report head
`0823ceee1b4bcf860f96cfda3344ac1e199aded0`, base
`b2e0293a546961230afbd73e5cd2a1a307d69e94`.
This source-only diagnostic does not yet meet its declared fail-closed/raw-receipt
contract. No native attempt or retry is approved by this review. The original
Windows qualification remains failed; the evidence does not establish missed
input on a living actor.

The review used the installed project gauntlet and No AI Slop guidance, the
preregistration, actual controller/helper/test/aggregate registration source,
source receipts, and original failed-run bytes. No engine, import, UID generation,
native input, OCR executable, export, CI or service was started. No project source
or canonical mission record was edited.

## Blocking witnesses

1. The actual `observed()` checks `latest.get('wall_msec', -1) > after` before it
   invokes the predicate (`scripts/verify_offline_export.py:560`). The new fence
   lives inside that predicate. Declare a dead, displaced snapshot with its
   `wall_msec` removed, then a valid living moving snapshot. The dead snapshot is
   skipped and the helper returns `LIVING_MOVEMENT_OBSERVED`. A negative timestamp
   produces the same result. The context stays `IN_PROGRESS` and contains no
   rejection. Thus an invalid snapshot can bypass the fence and a later state can
   replace it. A string timestamp instead raises `TypeError` before the fence.
   Preserve the existing handling of genuinely unavailable/stale publications,
   but validate and retain an available raw object's required schema/counters
   before freshness can discard a malformed object.
2. `local_input=None` at either the before-key boundary or response poll raises
   `AttributeError` at helper lines 58/100. The context remains `IN_PROGRESS`,
   without `precondition_loss`. Lists, booleans, strings and integers reproduce
   this. A null baseline actor also raises at line 23. The current tests do not
   cover these structural types. Validate nested objects and turn malformed
   context into the declared structured loss, preserving the actual rejected
   value. A scope change is also raised by the actual reader wrapper before the
   fence and therefore lacks the promised loss receipt.
3. Helper lines 19–22 replace every non-object snapshot with `{}` before recording
   it. A before-key null or string correctly prevents W-down, but the raw rejected
   state is lost. Keep normalization separate from the retained JSON value.
   Also, `[False, False]` passes the released movement equality check and allows
   a complete success; strict vector validation should reject boolean elements.

`probe_fence.py` extracts the actual controller `observed`, `wait_for` and, for
the scope witness, `offline_observation` AST. Its pure declared inputs exercise
77 cases, with reproducible assertions, full raw receipts for 19 representative
cases, and summaries for every case in `counterexamples.json`. The minimal
freshness-filter witnesses are named `dead_bad_counter_wall_msec_MISSING` and
`dead_bad_counter_wall_msec_-1`. These are controller counterexamples, never
claims that the stock game emitted those malformed states.

## Preserved behavior and limits

The original dead release dispatches no fresh key. Death, actor/life identity,
phase and round changes at the actual before-key/response predicates reject
before a moved state can pass. Valid living movement passes. Dispatch failure
still attempts W-up, and stale/missing publication timeouts release the key and
retain `RESPONSE_NOT_OBSERVED_BEFORE_ORIGINAL_DEADLINE`. The existing wait
passes its original ten seconds; the original whole deadline still limits it.

A declared blocking read that advances the clock to eleven seconds before
returning a successful predicate is accepted by the existing `wait_for` loop:
it checks time before the callback, rather than afterward. This limitation is
in unchanged baseline code. It is not an introduced deadline extension or an
additional blocking reason for this fence-only change. The pure clock does not
measure native operation duration.

The five declared Python groups rerun successfully: 49 methods, with the original
three Windows-only reader checks skipped on Linux. The new group contributes
11 methods. AST/source checks confirm unchanged capture calls, literal stage
budgets, whole/transition wait helpers, physical dispatch, tap delays, held guard,
HUD pause handling, game tree and CI. Aggregate registration adds only the new
pure group; the aggregate engine suite was not run. These controls do not negate
the blockers above.

I recomputed the timeline from the critic-owned original `offline-input` files;
it exactly equals the builder's timeline JSON. The original death transition is
tick 1166, before release ACK 1192, which has health zero and `alive=false`.
Direct inspection of original 11b pixels shows `005 HEALTH`. The clock origins
differ and sparse snapshots cannot place death precisely inside a capture or
assign cause to bots, diagnostics or capture cost. The original failed-run
review's plant elimination and unqualified device-resolution stages remain
separate from this controller change.

## Separate future Escape timing proposal

A preregistered source-only implementation is justified for review after the
fence blockers are corrected: replace only the focus-resume `tap('Escape')`
with Escape-down, the same 0.3-second hold and Escape-up, then enter the existing
resume ACK wait immediately. Keep generic tap behavior elsewhere unchanged.
The original trace records key-up completion at controller 137.703 and the
resume wait beginning at 138.828; source contains a deliberate one-second
post-up sleep while gameplay may already have resumed. Removing that known idle
sleep is a specific scheduling hypothesis, not evidence that bots or captures
caused the failed attempt, and it does not promise survival.

Require a new preregistration and exact separate source freeze, independent
review, pure scheduling/deadline/release controls, then a separately authorized
fixed-order acquisition. Preserve the original 0.3-second hold, ACK, full inertia
settle check, both fresh neutral samples, all 11a/11b/11c captures and fences,
physical W/LMB release ACK, fresh W fence, and all stage/whole deadlines. Do not
retry automatically, select a later life/round/seed, change health/bots/rules, or
accept precondition loss as qualification. This review grants no runtime
approval and no living-input/native gameplay acceptance.

The largest remaining source gap is complete validation and raw retention before
freshness filtering. Actual candidate living-input response remains unverified;
G1/G6/G7/G12 and broad release gates remain open.
