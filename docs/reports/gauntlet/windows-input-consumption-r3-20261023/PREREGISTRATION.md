# R3 lifecycle identity and packet projection correction

This isolated correction starts from rejected R2 handoff
`f01881dd0a57be6e4e524f5ddca173eaaf482bcd`, frozen source
`86fe3cbe3f191b328c1e08bf8d5adc0a937e39b1`. Preserve that branch, source,
preregistrations, raw failures, all 29 original controls and every R2 result.
Independent rejection `8cd68f818d8642953c4d4bda38ee14cccb55a9c5` supplies nine
additional cases. The unchanged rig SHA-256 is
`f68a7a2990e7d13246b87c5e0c9092d0023d6c761b751ab806b65139f91e4cfe`.
Its first reviewer positive fixture had a wrong ACK/pop justification; the
reviewer's original correction and both packets remain untouched. Use only the
final supported `additional-controls-r2/` expectations for this correction.

Before implementation, the source-supported requirements are:

- A `peer_bound` event must refer to the exact peer/generation from a preceding
  observed `peer_connected` lifecycle entry. A generation/peer never connected,
  or a binding before connection, cannot complete the diagnostic. A live identity
  binds once; it cannot bind another actor without retirement and a fresh
  generation. Preserve the existing retired-generation and actor exclusivity
  checks. `SBPeerLifecycle.connected`, `begin_join`, `current`, `admitted` and
  Match `_join_rpc` provide this source basis; lifecycle events always emit.
- Every client row's diagnostic attempt must equal the number of actual observed
  `client_attempt` events so far, and its cumulative attempt counter must agree.
  `_native_input_observe` starts attempt at zero, increments only for that reason,
  and always emits its lifecycle record. A welcome claiming attempt 2 after only
  one observed attempt must be incomplete. Preserve welcome retirement and exact
  send identity checks without inventing a transport/actor rebind.
- First direct acceptance must follow a direct receive observation. The first
  receive/accept transition for each reason emits, and `_input_rpc` calls receive
  synchronously before acceptance. Do not impose one-to-one batch correlation
  across coalesced later records or require received malformed payloads to pass
  authority validation.
- Accepted packet headers require positive array endpoints; count 1 requires
  equal endpoints. For count 2..12 the endpoints may be unordered or equal.
  `_native_input_packet` reports array endpoints, while `SBInputStream.accept`
  validates each command and stages a dictionary without ordering or uniqueness
  requirements. R2's `first <= last` accepted criterion was a meaningful root
  mistake, now corrected from actual source. Keep its exact criterion/history,
  regression outputs and rejected source; do not edit older controls to conceal it.
  The old reversed-single-command case remains invalid because its endpoints
  differ. Keep client-generated send ordering unchanged: prediction builds that
  batch in order, unlike arbitrary accepted input.

Change only the offline analyzer and a new meaningful pure lifecycle/header test
file. Preserve all runtime hooks, native/controller paths, transport/RPC/authority,
privacy/economy gates, stock rules/health/deadlines, existing tests, and canonical
mission documents. Any additional source correction requires a preregistration
expansion before edits. No production behavior changes are authorized.

Before editing source, replay the nine unchanged new cases against the old reader
and retain its exact failures. After freezing source, require all 29 old and nine
new independent expectations unchanged, positive unordered/duplicate endpoint
controls, invalid single-endpoint/order/identity falsifiers, the maintained pure
suite plus identity/lifecycle methods, and a properly initialized depth-one replay.
Bind the full non-document Git union and raw original logs; old native logs must
remain incomplete. Reuse the existing shallow checkout after preserving its R2
proof rather than cloning more source. All execution is CPU 4 only.

No Godot, import/export, native helper, CI, dispatch, new actual attempt or release.
Fresh independent source review remains required. Observed stage completeness
does not identify the original disconnect cause or qualify gameplay.
