# Corrected observer ready for a new trial

The first account trial remains blocked. Its flawed observer, raw SQL, strict
rejection and audit bytes are unchanged. The correction is a separate version,
`observe_owned_postgres_v2.py`, SHA-256
`d1ec8562d95f614cb6e3e996febb66cf6e4dda1cce5ab8a3e94f7639fd949179`.
The separate v2 recomputation SHA-256 is
`09599411b2f3a2b8754dccc54f4d3fd4c6168e3587d7f2471e9f70205fc0ebb0`.

V2 retains every received recovery SQL row, including identical table contents.
It recognizes only complete checkpoint JSON with a valid timezone-aware UTC
timestamp. After reading the replay checkpoint it starts a separate owned
read-only query and records the request time, actual database clock, checkpoint
hash, exact container, raw output and outcome. The v2 oracle requires both a
timestamped stream row after replay and this independently initiated final query.
It keeps the strict committed SQL observation before lost-worker kill/reply
release. Both prior earned payload hashes are excluded from the fresh run.

A new fresh-context critic independently accepts this preparation after 16 pure
controls. Its fake-process proofs cover BrokenPipe cleanup/PID persistence,
timeout output retention without acceptance, partial-checkpoint deferral, the
actual first-trial in-flight race and the actual oracle temporal fragment. Raw
proofs and failed proof-fixture attempts are retained in `v2-independent-review`.
These controls qualify the evidence tooling only; they do not accept a match.

No game, builder harness, stock timer, score, activity, reward or economy rule
changed. No new native/API/container/database workload was started. The next
trial waits for the lead's aggregate and coordinated engine lane, and must use
new fake accounts, isolated resources and output with a new earned payload.

Normal builder teardown can still preempt the final SQL query. Missing evidence
will reject the new trial. The blocking stdout loop also has no hard deadline
while awaiting a line or EOF; that remains an observer liveness limit. Neither
limitation permits inferred acceptance. After any run, the source/process/SQL
join and actual owned cleanup still need independent verification. Participation,
AFK resistance, remote impairment, devices and human play remain separate gaps.
