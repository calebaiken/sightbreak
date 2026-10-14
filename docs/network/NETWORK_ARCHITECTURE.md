# Competitive networking architecture

Baseline examined: `cf9a630417fa1e50d76b59dd6f45ce8819de6ce8`.

The Godot dedicated server owns ten actors, bots, collision, firing, ammunition, damage, objectives, round transitions and match funds. Physics runs at 60 Hz; the authority intends snapshots every 50 ms and clients send input at 30 Hz. Independent measurement found **15 Hz actual baseline replication**: floating-point residue in the decrement/reset timer defers the third-tick send until the fourth tick. Clients predict view orientation only at this baseline. Remote actors perform one 90% lerp per received snapshot and then hold until the next arrival.

SceneMultiplayer authenticates a bounded JSON protocol hello before gameplay RPCs. Protocol 2 rejects version mismatch before consuming an account ticket. Optional one-use, server-scoped tickets bind backend account identity; guest LAN matches cannot earn account rewards. ENet is unencrypted: tickets and reconnect bearer tokens require trusted LAN use. Disabling peer relay prevents direct client-to-client RPC routing.

## Authorization defects to address

Welcome and periodic snapshots use the same complete dictionary for all peers, including all actor positions, velocities, health, ammunition, inventory, match funds, objective carrier and interactions. Rendering/radar concealment does not protect this wire data. Global shot IDs, impact coordinates and utility trajectories are additional channels.

Recipient filtering must preserve a public roster for scores and elimination names while separately authorizing spatial state. Server hit detection continues to use the complete authoritative scene. Dead clients may follow only a surviving teammate, with visibility derived from that permitted camera. No free spectator entitlement is implied by a missing local actor.

## Reliability gaps

Protocol authentication times out, but a compatible peer can stay connected without joining. Account rejection relies on client cooperation to close. Reservations are in memory. The input gate rejects newer packets arriving within 12 ms. Result delivery makes three attempts but has no durable outbox. One inactive/disconnected participant currently invalidates rewards for all ten players; changing that policy requires a product decision.

These are development foundations, not Internet deployment approval. See the milestone record in `docs/engineering/PARALLEL_WORK.md`.

## Current engineering stack (supersedes baseline gaps above)

Privacy-v2 is based on corrected Claude77e0433; movement-v2 stacks on privacy; lifecycle-v2 stacks on movement. The authority remains60Hz. Snapshots are exactly20Hz with tick/epoch headers, per-recipient authorization and remote render buffering. Numbered bounded redundant commands are submitted30Hz and consumed at most once per server physics step. Local prediction is development opt-in. See dedicated movement/privacy contracts.

`SBPeerLifecycle` owns wall-clock admission/idle deadlines, per-transport generations and input decode quotas. `match.gd` owns actual peer↔actor binding and provisional account/slot claims; the economy bridge owns trusted ticket inspect/consume HTTP calls. HTTP continuations must validate generation/deadline before committing a binding. A pending request cannot bypass slot reservation or revive a disconnected peer. The new read-only backend inspect route must be deployed alongside an account-enabled lifecycle server; older backends fail admission safely with404.


The supervised account server stages immutable results locally and a SQLite FULL/WAL worker delivers them idempotently. `queued_for_delivery` is not `committed`; balances remain backend-authoritative. See `RESULT_OUTBOX.md`. Hit history is a separately disabled diagnostic module; live shot validation still uses the current authoritative collision scene. No art interface changes are required.
