# Criteria registration timing

Original independent criteria/binding commit
`69d3bde6df62242ae4d73a5aab15d25fe311a9da` was authored and committed at
2026-10-23 07:15:41 UTC; the binding JSON records 07:15:40.981730 UTC. Its initial
claim to precede dispatch was incorrect. Root reported the one dispatch at
07:15:05 UTC, 36 seconds before the independent criteria commit. This correction
preserves the original commit instead of rewriting it.

No actual new-run output was read before the criteria/binding were committed.
The first run-specific tool retrieval was a job-list request after commit and
push; it reported run `39916539053`, Windows job `120291226421`, queued, no steps
or conclusion. Root's own selected-run preregistration `cb95c10` precedes dispatch.
The independent criteria are therefore registered before actual-output review,
but not independently committed before dispatch. They do not authorize another
run or change any original requirement.
