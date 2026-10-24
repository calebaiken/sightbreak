# Source-conditional failed callback amendment before new tests/revision

Static review after frozenf52 found a legitimate source-scope concern: completing
the old deterministic main loop before foundation inference can apply its
successful-connection generation/reset assertions to a failed connection callback.
Match._peer_connected880–883 emits peer_connected even when PeerLifecycle.connected
returns false for an already live peer or MAX_PEERS capacity. Existing foundation
intentionally classifies these caller branches UNKNOWN, not impossible. The prior
focused tests exercise foundation directly and do not test this complete-reader
path. No claim was made that their passing run covered it.

Before candidate execution add two complete declared-projection witnesses from
TimedAuthority's source-timed state: duplicate connect for existing live peer9
at11200; successful connections for peers10–18 then failed capacity peer19.
A failed callback emits its hook without changing generation/lifecycle/stream
state. Their full reader status must UNKNOWN; a later independent frame regression
must INVALID. All fields remain from named operations, never arbitrary-row repair.
Retain exact f52 outputs before revision, even if INVALID shows this concern.

Design repair, if reproduced: classify failed callbacks from the observed live
peer ledger using the exact source condition (already present or count>=10).
Keep source state intact and defer UNKNOWN for this unsupported caller branch.
Apply successful-generation/new-stream checks only on proved successful callback;
preserve every original guard within that scope. Stop queue inference at such a
callback because original model assumes successful connection; do not resume a
fabricated stream reset. All independent deterministic prefix/counter/pipeline
checks still run and outrank UNKNOWN. Foundation still validates its available
source projection and remains independently UNKNOWN. This is conditional source
control flow, not a whitelist for arbitrary negative fields or weakened old tests.

No old135 test/helper/assertion edit is allowed. Additive new tests only, retain
sourcef52/code/current literal outputs and both failing/successful iterations.
A different critic must judge the final source and this added scope reasoning.
