# Independent source verdict: REJECT c0738163

Candidate c0738163965804297a1881905d5bb4646da40a16, base
49ae54b0e4f5d880bdf06e4eb783a616b2dff684, builder handoff
161d72c5f4018e5a8fb24669e1d5054bb6b12edb. Preregistration 2a25c7cb was
committed and pushed before implementation/output inspection. This review edits
only its own report directory. No native or CI release follows this verdict.

The unchanged base wins the source safety comparison because the candidate's
analyzer reports complete evidence for impossible emitted records. The candidate
adds useful read-only stages, but the strict analyzer is not ready. The largest
remaining gap is binding every direct stage to its actual metadata and current
client attempt/transport/actor identity throughout the trace.

## Blocking counterexamples

All cases are synthetic, independently authored, and replay the unchanged
scripts/analyze_input_consumption.py. Each retained folder contains both input
logs and the exact report. The coherent control is accepted. Nine invalid cases
also return diagnostic_complete true with an empty errors list:

- `stale_receive`: direct input_received latest wall_msec=1 while row wall_msec=8000.
- `receive_missing_metadata`: direct input_received has no input_received projection.
- `receive_unbound_different_peer`: receive row switches peer71/generation1 to unbound peer72/generation2 after the gate that requires a bound peer.
- `accepted_reversed_sequence_interval`: direct input_accepted first22/last20.
- `consumption_before_receive_accept`: first consumption precedes the first receive and acceptance in a trace beginning at ready.
- `client_send_different_transport`: post-welcome transport71 changes to72 without a new welcome.
- `client_send_unwelcomed_attempt`: post-welcome local_attempt1 changes to2 without a new attempt/welcome.
- `client_send_different_actor`: post-welcome local actor4 changes to5 without a new welcome.
- `send_outside_pending_interval`: a one-command send reports sequence20 when its only pending command is21.

Analyzer lines136–152 check fresh send/accepted/consumed metadata but omit direct
receive validation. Lines138–139 omit current welcome identity and the actual
pending interval. Lines151–152 accept a positive count without a valid first/last
interval. Lines177–189 link welcome events only, leaving later sends unbound.
These claims concern source/emitted-record consistency. They do not prove any
historical transport failure or gameplay defect.

## Preserved reviewer corrections

The r1 script/output remain unchanged. Its terminal-coverage case used identical
bytes to the coherent positive case with the opposite expectation. That test is
invalid and is excluded. R2 removes it:25 cases,13 unmet expectations. R3 narrows
four further expectations after inspecting the emitter: malformed receive epoch/
sequence can be real rejected traffic, and transition coalescing prevents complete
batch/epoch pairing from sparse event summaries. Those four are allowed aggregate
observations, not blocking false acceptance. R3 is the supported result:25 cases,
16 expectations met and nine source-inconsistent cases falsely accepted. R2 and
its exact script are preserved rather than silently replaced. The analyzer always
keeps cause_status UNRESOLVED, including those incomplete correlation examples.

## Passing source scope and remaining work

Independent source-audit.json covers all509 non-document Git paths/modes/blobs:
502 unchanged, five existing files byte-identical to base after erasing exactly
the marked additions, and two new Python files. Protocol/RPC bodies, authority,
privacy/economy code, routes, defaults, original schedules/deadlines and graphics
remain in that protected union. This is source erasure, not zero observer cost.
The observer is opt-in/debug/guest-loopback, with an explicit external fixture;
release, unrequested, account/ticket and normal-server modes are denied by the
source gate. It projects approved scalar fields, returns before collection when
disabled, caps output at1024 with an explicit truncation event, and calls no
transport or gameplay mutator. input_send_called follows invocation and cannot
prove delivery. input_consumed follows stream pop/actor input assignment, before
authoritative movement/action processing; it does not prove a shot/reload effect.
Expiry is emitted before forced disconnect, disconnect before binding removal.

All eight exact original Windows bound files match their retained sizes/hashes.
Both original input logs have zero observation records and the analyzer rejects
them as insufficient. Original run39940242244 ordinary-input failure and its
unknown cause remain unchanged. Screenshots were hashed, not visually reviewed.

Both complete and independently initialized depth-one checkouts pass193 pure
methods:173 maintained (170 pass/three old Windows skips), plus20 approach/Mac
methods. All17 per-group logs are retained and hash-verified in each checkout.
Bash syntax passes. Both three-file pure grammar checks pass using the existing
gdtoolkit4.3.4/Lark1.2.2; no tool was installed by this critic. Depth one is
shallow=true, exactly one commit at c0738163, clean tracked state, and859 present
tracked files independently match exact candidate blobs (469 non-document paths;
10,257 explicitly listed sparse omissions include historical reports). The same
25 independent controls replay unchanged with the same16 met/nine failed result.
The complete review HEAD includes only report additions over the candidate.

The supplemental duplicate/role controls reject duplicate JSON keys, duplicate
record indices and repeated consumption sequences. A tenth supported invalid case
falsely completes: authority-only peer_expired inside the client role. That exact
case also passes in depth one. Four supplement cases yield three expected
rejections/one false acceptance. Combined independent coverage is29 cases,19
expectations met and ten false-completeness cases, with no change to the frozen
R3 inputs. The10 supported invalid packets each replay through the actual CLI
with exit0, diagnostic_complete=true and no errors; cli-replays/ retains both
streams, output JSON and command receipts. These CLI exits are retained failures.

The declared schema has no terminal-capture marker. A valid early pipeline
prefix cannot establish complete later capture, shutdown or whole-run coverage.
Acquisition must bind whole retained streams to terminal supervision separately.
That limitation does not turn identical input bytes into opposing test outcomes. No Godot compile/type/API test, import/export,
engine/native run, observer, render or CI has executed for this review. Added
Godot runtime controls remain unexecuted. Even grammar/pure success cannot
establish executable readiness, successful native input or a gameplay fix.

Root may preregister a minimal analyzer correction from these retained inputs.
Require fresh exact-source review of that correction before combined-source
qualification and any separately preregistered actual Windows diagnostic trial.
