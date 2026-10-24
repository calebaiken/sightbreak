# Absorbing rejection/deadline generation, before db912 execution

Exact held db912 capture and amendment plan are already committed. Root separately
identified this gap while holding the reader: connected/last_input/global accepted
facts alone do not carry a rejected flag/deadline forward. Register the concrete
independent generated family before running any new history controls.

Keep a real initial bound peer9 pipeline for required roles, then a fresh unbound
peer10 with source-proved connection C and last_input=C. A tick at P=C+1001
observes its deadline before expiry. Source reject() can happen once, at one of
C+100,500,600,750,1000,1001,1010,1500,5000,19500, or not at all. Reject at/after the
prefix sample follows it (equal-millisecond ordering allowed). Reject before it
must not already be eligible at that prefix service tick; otherwise source would
expire/forget the peer and that live-prefix history is discarded. No activity or
admission occurs for this unbound identity.

Final expiry sample occurs just after T=C+21000. Before that tick, a fresh foreign
connection/bind11 near T suppresses the tick's global emission and selects a
different peer. Thus the old peer10 deadline is not re-exposed before expiry.
Initial peer9 remains below idle30000, and peer11 is fresh. Both old initial
join deadline and all candidate rejection deadlines are elapsed at final expiry.
No intermediate service tick is invented during the source stall.

Generate source histories first, group by EVERY visible pre-expiry row byte,
and collect all final deadline projections possible for each prefix. Candidate
final deadlines are the unique set {C+20000} plus R+500 for every named rejection
time. A final deadline has one possible rejection time unless it equals the
initial deadline, which also has an unrejected witness; those alternatives are
all enumerated. This supplies finite closure for each named completion, rather
than comparing against one canonical history. Keep actual source witnesses for
valid cases and prefix/complete possibility sets for counterfactuals. No candidate
function supplies expected feasibility.

For a prefix already showing a noninitial deadline, the entry is proved rejected
and the deadline can never change again. Reject() is absorbing; active/admitted
cannot advance last_input afterward. For an initial-deadline prefix, a later
changed deadline cannot claim an earlier rejection already inconsistent with
that observed prefix. Mark infeasible completions INVALID, not merely UNKNOWN.
All source facts concern the same observed peer/generation; no legacy helper
repair or all-row timing obligation is added.

Retain original18 input/result pairs exactly. New repeat derives one explicitly
versioned expected status for mixed_rejection_projection as registered earlier;
all other original statuses stay binding. Repeat isolated3746 unchanged. This
family and all db912 results are separate from original e5/928 artifacts, never
final source/native acceptance.
