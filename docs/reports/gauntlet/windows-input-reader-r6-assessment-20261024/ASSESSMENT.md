# R6 transition-model assessment: further work required before freeze

This is an interim independent MODEL/COVERAGE assessment, not a final R6 source
verdict. There is no frozen final R6 candidate or sealed handoff. Root reused the
existing R5 reviewer; no new thread or fresh-context review is claimed. Own
assessment checkout starts at preregistration4f0a1906 and retains R5 product bytes.
Only own report/model artifacts changed. R5 c909a9cb, source7d8ec7dd, its branch,
depth view and complete108/30 inputs/results remain unchanged.

The move from direct-row guards to per-stream transition constraints is needed.
The assessed snapshots show improvement, but passing the old30 examples does not
establish a sound state model. The main remaining issue is preserving one feasible
history across partial observations: unknown packet fields can be correlated,
and global call deltas are not automatically local peer deltas.

## Registered assessment and exact snapshots

Initial registration9498e5f9, unchanged external SHA-256
fa1b3943656eaf438083a95ec52c9b334164b8c41837b61e51fbe9fa87e1c538,
precedes R6 implementation inspection. MODEL_CASES f6019781 precedes prototype
execution. Queue oracle5b7c0f6a and the separately registered aggregate relation
are independent source models, not candidate-derived expected outputs.

The copied snapshots are explicitly UNAPPROVED and UNFROZEN working bytes:

| Snapshot | SHA-256 | Isolated assessment |
| --- | --- | --- |
| First draft | 9248707cf88d6777c7f6a77b53e43ceec0d46e33d3f4ec005ddf4bd0177fa5aa | 13 cases:8 matched, four invalid transitions admitted, one valid explicit-owner case UNKNOWN |
| Revised draft | 0ac7310b5367cef781fdbb97fa840b3c8f8b10d01e1be2d367d7c6b65ca31ed3 | Same13:12 matched, prior four invalid transitions reject, one source-valid multi-peer trace INVALID |
| Same revised draft, added relation | same | Five aggregate cases:positive matches; four impossible payload histories admitted |

These execute only InputTransitions on separately generated queue/event state
and projected rows. They are not whole-analyzer `diagnostic_complete` results,
Godot execution, API proof or final-candidate qualification. All raw ground truth,
projection, expected/actual/error and snapshot bytes are retained in prototype/
and prototype-*-results/. The results are bound to these hashes, not any later
builder working copy.

## Model findings supplied before readiness

The first draft discarded all known keys/signatures after count>2. The source
oracle proved four consequences: skipping mandatory fresh endpoint1, replacing
an earlier immutable payload, forgetting exactness after observed empty queue,
and allowing backlog-size7/skip5 to pop2 instead of rank>=6. Builder registered
f28488bb before refining definite facts, exact-empty recovery, ordering bounds
and unselected-pop inference. The revised13-case run independently confirms
those four defects are corrected in the captured revision.

The revised model still falsely rejects the source-valid multi-peer prefix:
A/B are bound; A accepts1 and pops1; B receives its first batch while queue0.
Since B's last binding row, the GLOBAL accepted count advanced for A. In the
revised generic branch `a` is global, exact_a is None and exact_c is0, yet
`a and exact_c == 0` forces B's queue to be nonempty. The error is
`accepted input vanished without any pop`. No B acceptance occurred. This is
local/global attribution error, not an UNKNOWN policy choice. The later explicit
B pop seen in an A row cannot even be reached until this earlier valid prefix
is handled. The complete source-derived trace is retained.

A second independent relation survives the revised definite-fact model. A sole
accepted count2 packet exposes two distinct fresh keys1/2 and fire aggregate1.
No later acceptance/reset occurs. After pop1/fireFalse, pop2 must have fireTrue;
bothFalse or bothTrue cannot come from that same immutable packet. Individual
unknown flags are correlated. The revised model assigns both flags None and
admits all four counterfactuals (two flag choices, direct/coalesced observation
forms). It chooses locally convenient payload values across rows instead of
preserving one feasible earlier packet assignment. This uses exposed identities
and a sole packet/queue, not guessed whole packet identity.

## Required model and coverage obligations

- Keep proved must-keys and immutable facts when new packet bodies are unknown.
  Observed queue0 restores exact empty state. Fresh known endpoints stay queued
  unless accounted for by pop/skipping/reset. Sparse sequences remain legitimate;
  command identities need not be consecutive.
- Preserve relations as well as individual values. A count2 aggregate can relate
  both queued commands even when neither flag is individually known. Alternatives
  must describe histories that remain feasible over later observations; intersecting
  must-facts is a safe abstraction only if residual uncertainty is not silently
  labeled complete when it admits a demonstrably impossible conjunction.
- Decompose global accepted/consumed/skipped changes into possible per-peer
  assignments. Use proven local counts or sound bounds; never impose a global
  nonzero acceptance on a peer with no proved ownership. Direct events, explicit
  consumed identity, sole-call cardinality and ACK/header exclusion can establish
  ownership. Keep genuine unresolved ownership UNKNOWN without calling native
  behavior invalid.
- Distinguish selected peer from event owner. Source updates counters/latest and
  diagnostic.last_peer before emission; later peer-A activity can select A while
  latest consumed still identifies B. A known prior B queue plus a sole B pop can
  determine its new state without a new B-selected projection. The oracle includes
  this positive and a separate genuinely ambiguous duplicate-owner UNKNOWN case.
- Couple event order, ACK and packet epoch. Equal millisecond timestamps permit
  alternatives, not arbitrary reordering of a directly emitted last operation.
  Header checks on hidden acceptance must use a feasible pre-accept ACK. Include
  callbacks on both sides of an epoch boundary and old latest metadata with
  unchanged counters; an ordinary epoch reset clears all peer queues/ACKs while
  retaining rejection/skipped totals.
- Prove backlog/cardinality relations without inventing middle keys. Seven unique
  positive queued keys at initialACK0 pop the second-largest after skip5, so the
  popped key is at least6. Preserve sparse valid queues and explicit full-window
  positives as well as invalid rank/cardinality cases.
- Exercise complete lifecycle/reset contexts: reconnect same peer/new generation,
  live-bound round reset, zero-bound lobby replacement, connected-but-unbound peer,
  and expiry before actual disconnect. Only replacement resets global rejected/
  skipped state; observer counters/latest survive. Retain preserve-versus-reset
  alternatives rather than accepting partial old-state remnants.

MODEL_CASES and AGGREGATE_MODEL_CASES register these obligations before relevant
executions. Some lifecycle/equal-order/multi-owner families are coverage gates
for the later frozen review, not claimed executed passes in this assessment.
The largest unresolved risk is unsound admission or rejection after collapsing
joint state uncertainty into independent scalar bounds.

## Fixture adjudications and next boundary

[FIXTURE_ADJUDICATION.md](FIXTURE_ADJUDICATION.md) confirms both pending
constructions. The old seq21/22 corpus positive is impossible (sorted pop and a
later ACK22→21 regression); retain it as an obsolete positive and create a
separate feasible version consuming21 while latest accepted is22, queue1 remains.
The queued-duplicate unit positive needs only its copied receive queue changed
from0 to1 before restamp; duplicate acceptance remains1 and the old queued
fireTrue assertion remains intact. Exact old inputs/test source are retained.
Builder registered0719aafb before edits. No old assertion or expectation should
be forced to pass by repairing input after mutation.

Builder has received these findings before calling a candidate ready. It must
register and preserve any further refinement, then freeze exact source and a
sealed handoff. Final independent review needs whole-reader positives/negatives,
old histories plus explicitly versioned replacements, all non-doc composition/
modes/bytes, and declared source/depth proof. Prototype-class results alone do
not satisfy that gate. No R6 readiness, native/CI release, quality, actual input,
physical latency or whole packet/coverage acceptance is granted here.
