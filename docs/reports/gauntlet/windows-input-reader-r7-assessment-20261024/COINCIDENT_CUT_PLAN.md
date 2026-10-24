# Independent coincident-deadline/cut closure before d2cab execution

Generate an isolated PeerLifecycle timer-observation family with C0/1000,
unbound or admitted atC, initial deadlineC+20000 and last_input=C, no accepted
calls. First observation offset19499/19500/20000 has authority_tick or (joined
only) input_received reason. Second observation offset equal-first/20000/30000
is authority_tick. Observed deadline offsets19999/20000/20001 at each prefix and
expiry. Final expiry offset20000/29999/30000/30001, never before prior sample.

Independently enumerate no rejection or the unique reject timeD-500 for every
observed/tested deadline, at EVERY legal ordered cut between observations. Gaps
are inclusive: one event at the same millisecond may occur after an earlier
sample and before a later sample. Reject() is once and absorbing; input_received
is a source synchronous allow-input barrier forbidding a rejected state there.
Replay literal operations and compare all projected deadline/L/joined fields.
Expected classification quantifies every feasible witness's original expired()
predicate, exactly as the declared isolated guard policy. A different reject
time cannot explain a named observed deadline; no finite-grid absence is used.

This is the PeerLifecycle timer API/observation model; it does not simulate Match
calling expired() automatically after each authority-tick snapshot. Do not claim
these abstract queries are complete emitted/served native traces. Full-reader
source-service pairs are the separate40 generated and18 history controls.
Retain ALL query rows, complete feasible witness/cut sets, expected/actual and
errors in compressed JSONL plus exact matrix counts/hash.

Also use one unchanged feasible full-reader input from each of the four earlier
visible-prefix groups. Alter only its later same-generation peer_disconnected
remaining deadline after successful expiry, before forget. For noninitial
rejected prefixes restore the initial deadline; for an initial-deadline prefix
choose D+1 with a reject instant earlier than the already observed expiry.
Each is INVALID; the already-used expiry cannot be contradicted before forget.
Keep original positive input bytes/results separate and untouched.
