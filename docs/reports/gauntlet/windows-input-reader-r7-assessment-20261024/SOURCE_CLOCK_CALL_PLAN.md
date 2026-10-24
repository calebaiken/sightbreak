# Independent source-clock/call family before d2cab execution

Use literal independent PeerLifecycle operation replay, retaining exact operation
and observer times separately. Test LifecycleHypotheses directly with source
projections; this is isolated expiry component coverage, not a full engine or
automatic service-scheduling simulator. Expected values are fixed before import.

Admission positives: C0/1000/20000; admit at C+0/1/19999; observe peer_bound after
0/1/500/20000/30000 additional milliseconds. Call admission before its original
join deadline, even when the later synchronous hook is after it. Expire at or
after joined idle30000, with no accepted ambiguity. All45 have concrete source
witnesses and expect CONSISTENT. Three call-at-deadline counterfactuals expect
INVALID (admitted() uses strict now<deadline), retaining a later matching expiry.

RPC positives: gate input at oldL+29999; receive hook after0/1/2/30001 extra ms;
active call after0/1 further ms; accepted hook after0/1/30000 further ms. The
initial gate can pass before idle while later active fails, leaving last_input
unchanged. Rejection cannot interleave within this synchronous callback. All24
have concrete source witnesses; expire afterward with no unallocated calls and
expect CONSISTENT. Do not substitute hook time for active/admitted call time.

Anonymous activity reachability: prior selected offset0/29998/29999/30000/30001
from oldL; targetL=priorTime+0/1/29999/30000/59998/60000; budget0/1/2/3 global
accepted calls. A concrete local update chain uses strictly less than30000 per
successful update, starts no earlier than the prior snapshot and cannot revive
an already-idle entry. Construct all needed successful update times, then fill
surplus global count with possible foreign calls. No feasible local chain means
INVALID (a mathematical strict-step/count bound, not finite-grid absence).
Feasible anonymous required/residual ownership is UNKNOWN per declared policy;
unchanged/no-call case is CONSISTENT. These120 cases do not infer actual ownership
from a hypothetical witness. Separate explicit foreign-call pairs debit known
nonlocal calls: local unchanged is CONSISTENT; forged local advancement is INVALID.

Keep all state rows, source histories, expected/actual/model detail, and failures.
These fresh counts are independent of builder7362/105. Existing3746/18/40 are
replayed afresh in separate paths at exact held d2cab. No old file is changed.
