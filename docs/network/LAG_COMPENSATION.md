# Bounded combat-history foundation (diagnostic only)

Live weapons still use `SBActor.trace_shot` against current authoritative world and player volumes. No new firing RPC, client hit report, ammunition path, weapon timing change or damage rewind is enabled. Protocol remains5.

`SBHitHistory` stores at most14 immutable pose frames (ten actors at the current roster size). The dedicated match can opt into recording with `record_hit_history: true` in its server options. Default is disabled. Epoch changes, death/revival, team changes and >3m teleports break continuity. Queries require an exact retained tick; no fabricated pose across missing history or extrapolation. No client receives this server-only history.

The query reuses Claude's exact capsule/head intersection helpers and captured stance/transform values without moving any live physics or animation node. It accepts a caller-provided current static-world ray distance, which bounds every historical intersection. Integration must obtain that distance from authoritative physics. Smoke continues to conceal information rather than stop bullets, matching existing ballistic behavior. Current death state prevents hitting an already dead target again. Awarding damage, friendly-fire rules and simultaneous engagement ordering remain the live server's responsibility.

A candidate timing function combines **server-measured** RTT/2 with a **server-configured**100ms presentation delay and caps rewind at12 ticks/200ms. It rejects nonfinite/negative/unreasonable timing. Neither a client timestamp nor an asserted target tick may be used as authority. Deliberately inflated latency can still earn the capped allowance; this is a fairness tradeoff requiring measurement, not an anti-cheat guarantee. There is no live RTT estimator or shot/history hookup in this phase.

## Evidence and activation gates

`hit_history_test.gd`:638 checks passed, including standing/crouched live-volume parity, moving target previous-position hit/current miss, world-distance limit, shooter exclusion, future/epoch/stale rejection, teleport/team/death continuity and bounded storage/timing. Existing weapon and body-volume regressions remain mandatory in the full matrix.

**Not verified:** actual compensated engagements under the network latency matrix, animation/history alignment, moving world geometry, defender perspective behind cover, trade-kill policy, human fairness, performance on phones. Keep recording opt-in and damage rewind disabled. Integrate authoritative shot identity, input-ack timing, server RTT sampling and abuse bounds in a separate reviewed follow-up before any active rewind experiment. This foundation does not fulfill a production lag-compensation quality gate.

Independent review additionally ran10,000 multi-angle standing/crouched rays at40–140m with exact live parity. It identified an activation blocker: bot-to-human or account slot replacement without a recorded absence/death/team change/teleport can retain the preceding combat identity. Before any live rewind, introduce an explicit actor/account generation and invalidate old history on admission/reassignment. The current diagnostic-only history has no damage effect; slot replacement is not yet a supported compensated-combat case.
