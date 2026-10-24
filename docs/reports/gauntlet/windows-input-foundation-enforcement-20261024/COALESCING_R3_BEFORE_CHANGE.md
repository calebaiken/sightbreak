# Coalesced selection, before R3 revision

R2's115-method run has35 assertion failures and one error; all originals remain.
Do not assume all are fixture defects. Source observer updates last_peer/last_actor
and stage counters BEFORE deciding whether to emit. A coalesced gate/decode/input
hook can therefore change selection between emitted authority ticks. R2's blanket
same-peer/sticky-actor tick rule is too strict for those source-supported histories.

R3 will keep ready, live generation, binding and timer constraints. A tick's
selection/known prior actor change with unobserved named-input counter progress
will remain UNKNOWN, not falsely INVALID or complete. A never-bound actor and a
change with no supporting hook counter remain contradictions. New pure controls
will use an explicit coalesced gate-rejection source witness and preserve all old
assertions. The broader coalescing caller model is still unqualified. Do not retime
old derived fixtures or reinterpret the35 failures as passing without adjudication.
