# Validate observed prefix invariants before unresolved inference

The preserved priority-counterexample against ca9 returns UNKNOWN although its
last process_frames1 regresses from prior6. The new lifecycle prepass can exit
before the existing definitive observation-order checks. That is a candidate
classification defect, not a claim that its fixture is valid.

R4 will prevalidate the complete existing role/index/counter/latest/clock/frame
prefix invariants before lifecycle or packet inference. Preserve their exact
predicates/messages and keep the old checks in place, so no packet/history rule
is removed. The separate pure helper may duplicate those fixed invariants at
this phase boundary; no game, privacy, timer engine, input data or old assertion
change. Test coupled unknown projections plus each definite prefix contradiction,
including frames, indexes, counters and stale latest metadata. A matching valid-
order unresolved projection stays UNKNOWN. Preserve R3 as the critic's current
frozen target; R4 needs its own later freeze/review and cannot inherit acceptance.

No native/API/helper/SDK/CI, actual207-row replay, study or capability action.
