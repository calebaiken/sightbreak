# Linux lane verification

The first replay used 90740e0, before the independently accepted per-size PNG
steps, so its unrelated-field comparison failed correctly. The rejected trace
is retained; the initially empty results file was not passing evidence.

The corrected replay compares against 67a5f54, immediately before this lane.
It accepts either the earlier static matrix or the current expression as a
baseline, evaluates the baseline's default four-host matrix, and restores the
exact original scalar before comparing unrelated fields. Ten selection cases
pass, including the retained Windows/ARM choices and push/unknown fallbacks.
No step or requirement is removed to make the comparison pass.

Independent review and an actual returned run SHA/single Linux job are required
before treating dispatch as verified. Native layout timing remains unverified.
