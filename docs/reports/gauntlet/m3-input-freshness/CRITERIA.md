# M3 input freshness: declared criteria

Status: IN PROGRESS; builder measurement is not independent acceptance.
Builder: `/root/freshness_builder`. Base: desktop mission commit `561d0cb`.
Reference implementation: PR20 runtime `f3ceaad98e089aa393c7f5fa650a52695094d979`,
shared probe/driver at `77f204083ab5bea4dc9149d3179daf540a994de4`.
The proposed six-line stream rejection is inspected directly. PR20's retained
Windows evidence and neutral packet are reference evidence, not new Linux passes.

## Defect under test

On the desktop base, `SBInputStream.accept` returns true when every command is
already acknowledged. Match therefore refreshes its action-silence and peer-idle
clocks without fresh intent. A snapshot outage can cap the stock client's pending
history while old movement persists. An adversarial replay can retain a slot.

## Independent components and expected results

- Stream correctness: reject a fully acknowledged packet without changing queue
  or acknowledgement; accept mixed stale/fresh commands and immutable queued
  retransmissions; preserve queue/rate bounds and epoch validation.
- Native snapshot gap (1–5 wall seconds): on the real authority, displacement
  and maximum speed in the fixed 3.8–4.8 window must both be below 0.001 m/m/s.
  Motion must stop within 0.350 s after the last consumed ACK; restored ACKs
  must allow signed leftward recovery below -0.9 m/s.
- Native stale replay after second 2: peer retirement must occur at 31.5–32.5
  wall seconds, with binding, lifecycle, input queue and pending-join tables empty.
- Positive controls: steady input and 200 ms input gap preserve two actual
  semi-auto edges (15→13 rounds), signed fresh recovery, one connected peer.
- Protocol/privacy: protocol 6, zero recipient privacy violations, bounded history
  <=120, default prediction false plus explicit true, zero active hit-history frames.
- Every native child exits 0 with no script/runtime/resource-leak error. An empty
  pre-start barrier is retried outside measurement, never read as a start epoch.
- Focused existing network, movement, privacy, resume and handshake regressions
  must pass. No timeout, packet size, rate limit, production clock, RPC or economy
  contract may be changed to meet a result.

## Method

Run the identical external PR20 probe/driver on isolated baseline and candidate
worktrees with official Godot 4.7.2. Same host, sequential source measurements,
loopback ENet and collision-only measurement platform; record raw rows, source
identities, hashes, commands, wall duration and every failed attempt. Run one
complete four-scenario × two-prediction-mode trial per source initially. Repeat
only if a failure or measurement uncertainty requires it. This bounded engineering
comparison is not a graphical, human-control, WAN, ten-client or CS2 parity claim.
A separate fresh-context critic must review actual outputs before acceptance.
