# R2 independent source verdict: REJECT 86fe3cbe

Exact reader 86fe3cbe3f191b328c1e08bf8d5adc0a937e39b1, independently preregistered
at 2f709b129987dcc0b681e62deede058083bad3dd before changed source/output inspection.
Initial REJECT02725f9c and its inputs are untouched. No Godot/native/CI work ran.

R2 fixes all29 frozen controls: the exact unchanged25 main and four supplement
cases now meet their original R3 expectations. Those scripts still print their
original c0738163 label; their checkout_head and actual analyzer SHA identify the
R2 replay. No frozen input was edited to get this result.

R2 wins against c0738163 on those retained cases. It remains rejected because
seven additional source-impossible lifecycle/stage records falsely complete,
and its new accepted-interval guard rejects a source-valid unordered multi-command
projection. The largest gap is connecting a bound peer/generation and welcome
attempt to the actual preceding lifecycle event, rather than aggregate coverage.

## Additional unchanged-source falsifiers

additional-controls-r2/ retains nine synthetic cases: one coherent baseline,
seven invalid traces falsely accepted, and one valid authority header projection
falsely rejected. Each includes both logs, the exact report and its source basis.
The analyzer is SHA256555632cafffa24f9ffc8514bba530f138feea455a83f42b2600d77d27d6aa23e.

- `bound_generation_never_connected`: only generation1 connects, but generation2 binds and consumes.
- `bound_peer_never_connected`: only peer71 connects; peer72 binds, welcomes and consumes.
- `binding_before_connection`: binding precedes its lifecycle connection event.
- `same_generation_rebound_to_other_actor`: live peer71/generation1 binds actor4, then actor5 without retirement/new connection; the old actor4 welcome still links as live.
- `first_accept_before_first_receive`: the first accepted event precedes the first receive, despite both direct/cumulative event histories beginning at ready.
- `one_command_two_sequence_endpoints`: count1 reports first20/last22, which cannot derive from one command even though the interval increases.
- `welcome_claims_unobserved_attempt`: one observed/counted attempt yields a welcome/send claiming local_attempt2.

The code checks peer_connected generation monotonicity but stores no connected
identity map. peer_bound can insert any positive unseen generation, and replace
an existing identity's actor. Accepted packets need no earlier receive, while
consumed only requires global nonempty receive/accepted arrays. Welcome identity
is saved without validating that its diagnostic attempt occurred.

`accepted_unordered_two_command_batch` is the positive boundary. SBInputStream.accept
iterates and validates commands, then stages a dictionary; it never requires the
incoming array to be ordered. With no ACK, commands2 and1 can be accepted and
pop sorts/consumes1. _native_input_packet reports array endpoints first2/last1,
not minimum/maximum. The new first<=last accepted rule rejects this valid authority
projection. This does not prove any packet delivery, cause or native execution;
the sparse client/authority summaries still cannot establish packet identity.
The prior reversed-single-command control stays invalid because its sole command
must give equal endpoints. Fix the declared header contract without changing wire
validation, RPCs or gameplay.

## Preserved reviewer corrections and scope

The first additional positive control used commands22/20 with a prior ACK21 while
claiming pop20. That source justification was incorrect:20 is already acknowledged.
Its exact script and output remain in additional_controls_r1_preserved.py and
additional-controls-r1/. R2 changes that positive projection to commands2/1,
no prior ACK and consumed1, with matching queue/ACK/actor-input fields. The reader
still rejects at the same new interval guard. All seven invalid cases stay byte
identical. This is a correction to the reviewer fixture, not a relaxed gate.

One shell redirection failed after sparse population omitted this own report
folder. setup-failure-1.json preserves the actual exit1 and stderr. No analyzer or
native execution began in that failed command. Restoring the explicit own report
cone corrected setup; no candidate/frozen-control changes occurred.

The independent510-path non-document Git union has508 unchanged files. Only the
reader blob changes and one new six-method pure test is added. Every runtime
hook, protocol/RPC, authority/privacy/economy path, route, default, schedule,
deadline, graphics, fixture and controller remains exact c0738163. source-union.json
retains the full path/mode/blob inventory. No diagnostic code fixes gameplay.

Builder handoff f01881dd0a57be6e4e524f5ddca173eaaf482bcd explicitly preserves
this rejection and the unchanged source. Independent complete and depth-one
checks each pass 199 methods: 196 passes and the same three existing Windows
skips. This comprises 193 previously reviewed methods plus six new identity
methods. Every pure-group raw log is retained and hash-verified; both identity
streams and hashes are retained. Shell syntax passes.

The independently initialized shallow checkout has exactly one commit at
86fe3cbe, clean tracked state, and 860 present files (470 non-document files)
matched byte-for-byte to frozen Git blobs. Its 10,318 sparse omissions are
listed explicitly. Both checkouts reproduce the same frozen 29/29 and additional
1/9 results without changing inputs or expectations. Complete source HEADs
include only this reviewer report over the candidate, as bound in source-union
and verification-summary receipts. All work used CPU 4.

The seven invalid new traces also replay through the actual pure CLI with
exit 0 and complete=true; the valid unordered authority projection returns
exit 1. additional-cli/ retains all eight actual command receipts, output JSON
and stdout/stderr. These are retained correctness failures, independent of the
passing maintained suite. The original log copies consumed by the frozen rig
use its original text-mode newline normalization; no raw-byte equivalence is
claimed for those derivatives. Initial source-audit.json independently bound
the original CRLF bytes, which remain unchanged.

Godot type/API compilation and the queued runtime controls remain unexecuted.
input_send_called is invocation only; input_consumed means pop/input assignment
before actor action gates. The old failed Windows logs lack trace and remain
insufficient, with cause UNRESOLVED. Neither passing frozen controls nor a future
source-only acceptance releases a native run or qualifies combined source.

Final ancillary evidence is committed locally at52dc54e489ed4c65844a79d7a37fec488df832ef.
Two ordinary Git pushes failed with the exact authentication error retained in
publication-failures.json. Initial rejection8cd68f81 is already pushed. No
credentials were read or changed; root explicitly took publication ownership.
