# Guest loopback input-consumption diagnostic

Status: source-only diagnostic preparation. Own checkout is
/workspace/sightbreak-windows-input-consumption-diagnostic, branch
codex/windows-input-consumption-diagnostic-20261023, from exact
49ae54b0e4f5d880bdf06e4eb783a616b2dff684. The completed route correction
(ea6c330a) and its handoff remain separate and untouched. Root/contributor branches
and canonical mission documents are not edited. All checks use CPU 4. No engine,
export, CI, native acquisition or qualification dispatch is authorized.

## Inspected benchmark and uncertainty

The bar is the sealed independent failure e6a2de33 for run 39940242244, job
120369601915. original-bindings.json binds exact unmodified ordinary-client,
authority, driver and screenshot records. They show two server disconnects, an
intervening reconnect, a client disconnect/reconnect notice, and a 38.836 s
sample gap around actual OS LMB-down. R-down follows a sampled unbound peer.
All 44 joined-actor samples have zero shots, no fire/reload intent and RIFLE
30/90. Three original fire/after-fire/failure images are byte-identical. These
facts do not identify the disconnect cause or prove client input consumption.
Original ordinary-input, e28c8e9 reload-completion and corridor failures remain.

Source inspection finds the distinct stages that existing actor telemetry misses:
main.gd polls physical R and mouse-event fire into local intent; a connected client
adds sanitized commands to a 120-entry prediction history; full unacknowledged
history stops generating more intent; outgoing packets contain the latest bounded
batch and current round epoch. Snapshot ordering/schema checks precede local
reconciliation. Authority requires current peer binding/lifecycle, validates the
round epoch and command window, then consumes a bounded command stream on physics
ticks. The source fixture currently samples actor state in _process, after these
stages, and can miss short input edges and the pre-forget peer generation.
No production defect has been proved. Do not accept stale generations, renew
liveness from acknowledged replay, rebind manually, replay input or fabricate an
effect to make this trace pass.

## Preregistered observability

Add an explicit controller flag that passes one debug observation flag to the
existing exported client and external authority fixture. Default commands and all
three stock schedules, positions, values, deadlines, waits and acceptance rules
remain unchanged. Diagnostic execution is separately labeled; no actual run is
released by this source work.

In existing match.gd, enable observation only for debug builds with that explicit
flag, empty account ticket/no account requirement, and a guest loopback client or
the explicit external guest authority fixture. Normal servers, remote clients,
account sessions, release builds and unrequested runs stay disabled. Do not add
RPCs, packet/snapshot fields or any protocol change.

Record bounded scalar-only stdout JSON with monotonic and UTC wall timestamps,
process/physics/drawn-frame counters and role. Capture client attempt/welcome/
disconnect, accepted/rejected snapshot headers and local ACK freshness, local
physical/controller-neutral/fire/R intent, generated sequence/pending saturation,
and actual sent packet sequence/epoch/action summaries. On the external authority,
capture pre-forget peer binding/lifecycle generation, input receive/accept/consume
summaries, queue/ACK/rejection counters, silence age and explicit lifecycle-expiry
versus transport-disconnect callback paths. Local diagnostic attempt numbering is
not an authoritative peer generation. Log only the observed guest actor's own
input/ammunition; omit tokens, tickets, account/profile data, payload bytes, aim,
other actors and hidden spatial state.

Keep counters and latest stage summaries in memory. Emit periodic summaries at
most once per wall second, plus lifecycle/control transitions, with a hard total
cap and an explicit truncation record. Disabled hooks return before collecting
state. Diagnostics never call input-generation/accept/pop/rebind methods, write
controls or change transport/rules. Their overhead is unmeasured; they cannot
establish physical performance or erase the original qualification failure.

Add a strict pure analyzer for these declared observation records. It must reject
malformed/nonmonotonic/mixed-role/missing-stage/truncated evidence, distinguish
packet acceptance from actual consumption, keep generation/binding identity
separate from actor reuse, and report observation gaps without assigning an
unobserved cause. A saturated pending queue alone cannot prove a transport or
render cause. Existing original logs contain no such records and must remain
insufficient for this diagnostic, with the original failure retained.

## Falsifiers and handoff

Before source handoff, verify that removing only marked diagnostic additions
recovers exact original match.gd/controller/fixture behavior, including RPC
signatures, authority checks, transport limits and input schedules. Add meaningful
pure negative controls for missing/reordered stages, old peer-generation reuse,
accepted-but-not-consumed packets, stale ACKs, full pending histories, observation
gaps, cap exhaustion, invalid values and privacy leakage. Queue executable Godot
controls in an existing maintained test script for admission/safe projection and
disabled observer invariance; they remain explicitly unexecuted in this component.
Run applicable maintained pure checks and repeat in an initialized depth-one
checkout without report imports. Preserve all failed/setup iterations and exact
source bindings. Fresh independent source review, diagnostic admission and a
separate root release are required before a new actual trial. If a source-provable
production defect emerges, preregister its correction as a separate component.
