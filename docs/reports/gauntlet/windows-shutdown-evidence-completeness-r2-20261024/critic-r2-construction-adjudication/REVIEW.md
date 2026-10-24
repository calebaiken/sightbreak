# R2 pre-edit construction decision: REVISE the action compiler

This decision binds proposal `63021bac381c3f5e7119d3769131754c584f4823`, draft
SHA256 `bcfbe2e447ffc2d25ace3bc66839e864f17066abcbcdf5d1dfe045f3fc6fbe3e`.
Preregistration `43eeb1fe` precedes reading the exact proposal. Existing critic
reuse is explicit; the critic is independent of its builder. No draft was
imported or executed, no R2 production validator was inspected, and no fixture,
test, helper or product source was edited by this review. Static evidence is
sufficient to identify the contradictions below.

## Permitted smaller construction changes

The following narrowly described changes are independently justified. Preserve
their original bytes/results and all assertions; this is construction permission
only, requiring later exact-source validation and final independent review.

1. Change only the constructor call `_snapshot(20500, phase='live', ammo=13)`
   assigned to `reload_before` to wall **20000**, with the existing `_snapshot`
   derivation of its counters/elapsed. Default source lines 669–672 obtains
   `before_reload` before capture 05 and saved-HUD analysis, whose declared pause
   sequence begins at 20100. This correction removes that specific ordering
   contradiction without certifying the whole history.
2. In the named new-30 extended-elapsed test, add exactly the proposed after-query
   monotonic assignment `finished_monotonic + .01`, immediately after adjusting
   trial finish. `collect_trials` writes finish before the after query. Preserve
   the backwards wall-clock-step construction and its successful assertion;
   wall-clock changes are not a reason to invent an elapsed deadline. This
   matches the independently retained coherent control.
3. In the named new-30 publication-receipt error test, replace only the generic
   `study.write` patch with a `Path.open` wrapper matching the exact owned
   `trial.controller-capture/publication.json` path and forwarding every other
   call to the saved original. Inject the same `OSError` at the newly declared
   exclusive receipt-open boundary. Keep the original failing fake invocation,
   method name and all three assertions/exception expectations unchanged. The
   wrapper must still reach the fake invocation, retain both original streams,
   raise publication failure, and retain the original invocation as cause. The
   later exact-source check must establish that this is the actual publication
   open, rather than an earlier directory/stream failure. A mode-specific match
   to the exclusive write is an equally narrow implementation, if recorded.

These permissions do not cover `run_generated`, old-28 bodies/assertions, `Owner`,
the original 81 cases, or a generic normalization of source-inconsistent inputs.

## The proposed compiler and its call are not permitted yet

The declared ordering has useful parts: both named fences place their five
observed returns around raw capture in the correct relative order; OCR is placed
between HUD pause and the subsequent observation/resume; reload input and reload
wall receipt markers occur before capture 06. However, the draft cannot yet serve
as a source-shaped complete action stream.

**Held keys are lost across waits.** Frozen `trace()` at default-driver line 285
serializes `sorted(held_keys)`; `key()` adds/removes keys at lines 323–329.
`observed()` calls `wait_for`, then traces its observation without releasing keys
(lines 590–606). The draft's `action()` unconditionally resets `held_keys=[]`,
and `observed()` uses it for all three records. Its reload sequence sets R down
then emits a wait/return with no held R, before R-up. The explicit settings resume
likewise holds Escape across the acknowledgement. A compiler must carry a single
declared held-key state through every action, modifying it only at source input
edges, including direct scoped releases and cleanup. Replacing the empty list in
individual records is not a sufficient state model.

**Mandatory operations remain absent.** The old action stream retained by this
draft contains only capture pairs and four click/slider operations. The compiler
still omits, among others:

- initial `Real offline match readiness after one Deploy click` observed return
  before capture 02 (source line 609), and its deploy click edges after capture 01;
- `Living second-round player before fixed settings route` return (line 771)
  before the declared route and capture 06f, plus the source route operation
  records. A successful `approach_floor` necessarily emits movement completion;
  particular pulse/settle counts must follow a declared valid route branch;
- reopened deploy edges between capture 09 and the profile-load wait;
- W-down and button-down before held-input acknowledgement, focus-loss before/
  after edges, restore before/after edges and its `Restore actual native input
  focus` wait (lines 960–993), Escape down/up before the held-neutral return,
  and W-up/button-up before the released-controls return (lines 1003–1045).

These are source operations, not optional statements inferred from image labels.
Preserving an incomplete old action list cannot supply them. Add a source-linked
operation inventory with required and conditional nodes and state/receipt ties
before revising the compiler. This need not guess how many inertia-settle
iterations occurred: the frozen neutral samples have zero velocity, so their
declared branch has zero settle iterations and exactly two guard samples. Other
branches must derive their count/order from declared states. A Windows route
branch must likewise match its declared route/pulse receipts rather than invent
success from only its endpoint.

The snapshot associated with each observed return must match its actual receipt
and satisfy the source predicate/freshness boundary; a typed snapshot alone is
insufficient. Keep named-fence, pause, reload and settings constants typed, and
derive wait budgets, input seconds, remainder and OCR clocks from the same
declared graph. Do not move process/close callback identity or owner accounting
to make a new action schedule fit. If a valid declared schedule requires changes
beyond the registered constructor scope, propose those separately before edits.
The current source fixtures' compressed construction clocks and generated pixels
remain format data; this review does not qualify native timing, delivery,
rendered frames, or a complete historical gameplay trace.

## Evidence and decision limits

`PROPOSAL_BINDING.json` verifies that all three fixture/test files at the proposal
remain byte-exact 0f478, including old28/helper and new30. The source and draft
hashes, literal operation omissions, original action-call inventory and decisive
source excerpts are preserved in `STATIC_SOURCE_EVIDENCE.json`. Its static audit
also verifies all 858 final67a manifest members / 205551297 bytes unchanged. No
candidate scores or actual native results are adopted here.

Winner: frozen producer control flow and its held-key serialization. Reason:
the draft still serializes impossible held-key transitions and omits mandatory
source operations. Largest remaining construction gap: an explicit complete
source-derived operation/state graph with conditional branches and typed receipt
ties. Revise that draft and submit the exact version before applying its compiler
or call. Original 0f/67a rejection remains unchanged; public collection stays
**BLOCKED**. No native, API, SDK, proc, signal, helper, CI or capability trial ran
or is authorized by this bounded decision.
