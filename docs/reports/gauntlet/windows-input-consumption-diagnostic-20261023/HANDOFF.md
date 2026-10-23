# Guest loopback input diagnostic handoff

Exact source is c0738163965804297a1881905d5bb4646da40a16, from Windows actual
49ae54b0e4f5d880bdf06e4eb783a616b2dff684. Preregistration 0bf075ee precedes
implementation. Own branch is codex/windows-input-consumption-diagnostic-20261023
at /workspace/sightbreak-windows-input-consumption-diagnostic. The separate
initial-pulse correction ea6c330a is not included or modified here. Canonical
mission documents, root and contributor branches remain untouched.

This is source-only observability. It fixes no demonstrated product defect.
No Godot, native process, export, CI, diagnostic acquisition or qualification
attempt ran. Fresh independent source review, actual admission and root release
are required before any actual trial.

## Original evidence

Sealed actual critic e6a2de333928153c11314bae790ebabe55fdaabf independently fails
run 39940242244, job 120369601915. original-bindings.json identifies the original
client/server logs, actions, authority telemetry, results and three identical
PNGs. They remain unchanged. Ordinary input has two disconnects with an
intervening reconnect, a 38.836 s authority observation gap around OS LMB-down,
and R-down after a sampled unbound peer. All 44 joined-actor samples show no
shots or fire/reload input and a full rifle magazine. These facts cannot identify
the disconnect origin or prove client consumption. All historical failures remain.

The final analyzer replay of these exact old logs returns exit 1,
diagnostic_complete=false and two missing-observation errors, retained in
original-log-insufficiency-final*. It does not retrofit a diagnostic pass.

## Implementation and limits

match.gd adds 120 lines for opt-in hooks and a bounded observer. Admission requires
a debug build and explicit --native-input-observation, a guest loopback client
with no ticket/account requirement, or the explicitly marked external guest
source fixture. Normal servers, remote/account clients, release builds and
unrequested runs remain disabled. Only observation state changes; protocol 6,
RPC signatures, packet/snapshot contents, transport limits and authoritative
rules remain intact.

Client records separate engine physical-key/button state, main's mouse-event
fire flag, sampled local intent, pending history saturation, generated sequence,
accepted snapshot/ACK freshness and process/physics/drawn-frame counts. Connection
attempt/welcome/disconnect records include the actual ENet transport ID. The
local diagnostic attempt counter is distinct from the authority peer generation.

`input_send_called` marks the existing RPC invocation returning, with the actual
selected batch's sequence/epoch/action summary. It proves neither a successful
RPC result nor wire delivery. Authority `input_received`, `input_accepted` and
`input_consumed` are separate hooks; consumption records the actual popped
immutable command before later actor action/effect gates. Existing source-fixture
shot/reload effects remain the separate effect evidence. Pre-forget binding,
lifecycle generation, ACK/queue/rejection counters and explicit expiry versus
disconnect callbacks distinguish observed paths without assigning an unseen cause.

Only bounded scalars for the observed guest actor are projected. Tokens, tickets,
accounts, profile data, aim, payload bytes and hidden spatial state are omitted.
Counters/latest summaries stay in observer memory; stdout emits periodic summaries
at most once per wall second plus lifecycle/control transitions. At 1,024 records,
the observer emits an explicit limit record and stops. The analyzer rejects such
truncation. Overhead and Godot type/API/runtime behavior remain unmeasured.

The controller's new --observe-input-consumption flag adds that debug user argument
to client and external authority commands. Existing schedules, screenshot order,
values, waits, pass predicates and absolute budgets remain. Adding the flag does
not release a run or convert diagnostic observations into qualification results.

## Verification

Both full-source and initialized depth-one runs pass all 15 maintained pure groups:
173 methods, 170 passes and the three existing Windows skips. Two additional
approach/Mac-menu groups pass 20 methods. Each run has 193 methods, 190 passes and
three skips. Shell syntax passes. Original per-group logs and hashes are retained
under complete-pure/ and depth-one-pure/.

The 19 new pure methods reject malformed/private fields, stale/reused generations,
actor aliases, packet acceptance without consumption, stale stage metadata,
missing direct events, invalid epoch/history, mixed roles and cap exhaustion.
Welcome links use actual transport ID, actor and observed live authority generation;
they do not guess from actor reuse. Saturation and observation gaps stay facts,
with cause_status=UNRESOLVED. Five in-memory mutations of privacy, retired-binding,
freshness, direct-event and truncation guards each fail their targeted falsifier.
mutation-controls/ retains all expected failed tests; source bytes remain unchanged.

Removing only marked diagnostic additions recovers exact original bytes for
match.gd, the external fixture, controller, existing native test and validate.sh.
The maintained pure source-erasure controls bind those five original SHA-256s
without Git history or report imports. The observer also has a forbidden-mutator
source control. Seventeen new Godot checks are queued in the existing maintained
movement_prediction_test.gd for admission, read-only projections and disabled
invariance; they were not executed.

Pinned gdtoolkit 4.3.4 with Lark parses all three changed GDScript files in both
source checkouts. This is a pure grammar check, not Godot compilation or type/API
validation. The parser is installed only in this checkout's .local/gdtoolkit.
The initial grammar and pure development outputs remain alongside final reports.

The fresh .local/depth-one-source is shallow=true with exactly one commit at
c0738163. Its tracked source is clean, and all 473 available code/instruction
files match byte-for-byte in depth-one-source-bindings.json. All work used CPU 4.

## Largest remaining uncertainty and next step

The native observer has not compiled or executed in Godot. The original disconnect,
snapshot gap and missing ordinary input consumption still have no proved cause.
Full pending history can stop new intent; missing snapshots, host scheduling,
transport loss and lifecycle expiry need actual stage records to distinguish them.
A complete analyzer result establishes observed pipeline coverage only. It cannot
approve gameplay, identify an unobserved transport/render cause or erase a failure.

Fresh source critic /root/windows_connection_trace_fresh_source_critic owns review.
Root will separately combine qualified diagnostic code with the accepted initial
pulse correction, then commission admission/release if an actual trial is justified.
No production correction or new native attempt is authorized by this handoff.

Reproduce pure verification in a fresh output directory:

```sh
taskset -c 4 python docs/reports/gauntlet/windows-input-consumption-diagnostic-20261023/run_pure.py --source . --output .local/review-pure
```
