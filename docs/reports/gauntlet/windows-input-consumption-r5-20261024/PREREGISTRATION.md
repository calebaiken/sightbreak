# R5 bounded stream-state and projection correction

Registered before code edits. Base/source bar is rejected R4
`642dd0e0543698cae5d90b9046d5875beabed111`, handoff `d139124e`.
The independent final rejection is `ad12f7ae08ca9cf1eaf05807ea41c44104544fdc`:
six false accepts in five invariant groups, with exact13 controls reproducing
7/13 in actual and initialized depth-one views. Read its REVIEW and
STREAM_RESET_ADJUDICATION before implementation. The actual immutable Match,
SBInputStream and peer lifecycle implementations are the source oracle.

This own branch/worktree is `codex/windows-input-consumption-r5-20261024` at
`/workspace/sightbreak-windows-input-consumption-r5`. It was created sparse with
no checkout, then populated with explicit read-tree and a complete11728-path
index. It shares `/workspace/sightbreak/.git/objects`; no full clone was made.
R4 remains clean at its pushed handoff. Its complete history/raw reports and
earlier artifacts are preserved. Exact selected R4 builder92 controls and final
critic13 are separately copied into this report before edits.

Measurable source requirements are:

- Accepted count1 has one exposed sequence, which must exceed the effective ACK
  (absent observation ACK-1 means internal ACK0). Count2 exposes both commands
  and requires at least one fresh endpoint. All accepted endpoints obey the
  source ACK+120 upper bound. Count>=3 can have stale/duplicate endpoints and
  an unexposed fresh middle command; accept this valid positive without assuming
  sorted extrema, unique commands, packet identity or full trace coverage.
- Queue count cannot exceed120: only unique unacknowledged keys within ACK+120
  are queued, and pop/forget/reset remove keys. Check all authority observations,
  including a coalesced acceptance first observed in a later tick.
- A count0 packet projection has first=last=-1 and zero action aggregates. The
  existing count-bound action check supplies the zero counts. Count>0 consisting
  of nondictionaries may also expose -1/-1 and remains valid before validation.
  Positive sequences/epoch are not imposed on received malformed payloads.
- When a metadata stage counter advances, its latest timestamp is between the
  previous emitted row's wall time and the current row's wall time, inclusive.
  Equal millisecond timestamps are allowed. Unchanged counters retain metadata.
  Hidden/coalesced calls need no invented direct row or packet attribution.
- Rejection state and observer rejection calls agree within a proved stream
  lifetime. SBInputStream.reject paths increment `rejected` before the Match
  rejection hook. The observer starts before networking and its cumulative J
  never resets, so stream_rejected<=J always. Between consecutive rows require
  delta(stream_rejected)=delta(J), except when a possible stream replacement
  exists: authority epoch advances and no bound identity continuously witnesses
  that interval. A possible replacement permits state reset bounded by prior
  state plus new rejection calls. Do not require global state==J across resets.
  Track bound membership until direct disconnect, because Match observes before
  removing the peer. An epoch change while a binding remains live cannot replace
  the stream; an ordinary round reset only clears queues/ACKs. Include both
  legitimate lobby-reset and live-binding epoch-change controls.

The maintained positive malformed helper and two versioned malformed old cases
increment the observer rejection counter but leave stream_rejected0. The R4
critic independently adjudicates this contradiction in the same live epoch.
Minimum source-faithful correction is state1 from rejection onward, preserving
all existing assertions and malformed payload semantics. The earlier R3 malformed
positive has the same missing state. Preserve all exact old fixtures/results
and expectations; label these newly obsolete positives rather than claiming all
old92 requirements pass unchanged. Add new source-faithful versions with only
the state correction. Do not edit old R4 report generators or frozen artifacts.

Allowed code is the offline analyzer, minimum identity-fixture state correction
and a new pure stream/projection suite. No runtime, transport, RPC, authority,
privacy, economy, native/controller, workflow or canonical documents change.
All execution is CPU4 pure/static Python and shell parsing only. No Godot,
engine/API, native helper, CI, Mac review, dispatch or actual attempt.

Before code changes, import the frozen reader and retain its verdicts for all
exact final critic13. After source freeze, require these13, all prior negatives
and valid controls, explicitly versioned source-faithful replacements, meaningful
new ACK/queue/projection/timing/reset tests and the maintained pure union in actual
and properly initialized depth-one views. Preserve failure iterations and setup
errors. Bind the full non-document Git union/modes/bytes including sparse omissions,
and disclose shared alternates. Freeze/push source, then builder evidence for a
different independent critic. The builder cannot approve readiness or native work.

## Timing fixture expansion before restamp edit

The first implementation rejects all six final falsifiers, with13/13 fresh
verdicts. Its focused45 methods expose one additional source-inconsistent
positive fixture: the lifecycle failed-attempt restamp moves welcome to wall6000
but retains a first-observed applied-snapshot timestamp4000 in a later row.
The preceding welcome row has no snapshot counter, so a newly counted snapshot
cannot predate it. Preserve the exact old lifecycle file and failing output.
Minimum fixture correction is to place the first snapshot call at the preceding
emitted row time (inclusive), retain that cached snapshot/latest on subsequent
rows and recompute snapshot_age. All old method names, assertion ASTs and test
mutations remain. This is construction-time normalization before assertions,
never post-mutation parser repair. Source current-time capture and cumulative
counter emission provide the basis; no runtime behavior changes.
