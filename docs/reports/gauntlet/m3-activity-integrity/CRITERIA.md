# M3 activity provenance criteria

Declared before product changes or engine execution. Builder base:
`872a57618c079c5854dea47d361cc7da732378ec`, branch
`fix/consumed-command-activity`. Scope: the authority of activity observations.

The reference is the existing product contract in `docs/network.md:40`, the
immutable input queue in `game/scripts/network/input_stream.gd:14–84`, and the
existing match activity and reward rules. Real aim changes remain eligible;
this work does not promise resistance to aim automation or multi-account farms.
The stock ten-account experiment at `471fbd8` remains valid within its recorded
scope and does not qualify meaningful human participation.

## Counterexample to establish in the pinned engine

After neutral command 1 is acknowledged, send ordinary valid compressed input
RPC packets containing a fresh neutral command followed by acknowledged command
1 with an off-angle look. The stream admits the fresh command and discards the
acknowledged one. The original match nevertheless reads `commands.back()` to
renew its ten-second activity window. Repeat while actual authority consumes
neutral input. Retain server observations of received/consumed sequence, actual
pose, activity timestamp, ammunition and interaction state.

The baseline must show at least three renewals from this discarded look while
actual authoritative aim, horizontal position, ammunition and objective progress
remain unchanged. The candidate must show zero such renewals. The same endpoint
must continue accepting/consuming fresh neutral input; rejecting all traffic
does not pass. Use real ENet processes and the unchanged production `_input_rpc`.
The harness may freeze a deterministic test lane and use synthetic activity
fixture state, but must identify those fixtures and never claim a played account
match or a backend grant.

## Required compatibility controls

- A consumed real aim delta above 0.004 renews activity; a subthreshold delta and
  a packet not yet consumed do not. Heading wrap, sanitized finite look and
  previously queued immutable command identities retain stream behavior.
- Consumed movement with observed velocity above 0.2, an existing objective hold,
  and an actual emitted shot retain their activity sources. A dry or rejected
  fire request alone does not qualify.
- Dead/spectator input and buy/post aim retain the current input-activity policy.
  Do not add alive/live, kill, damage, travel-distance or objective-count gates.
- A dropped backlog command, a modified duplicate, an acknowledged stale tail,
  malformed input and a prior-epoch command cannot renew activity through their
  discarded fields. Consumed neutral input with no qualifying event stays idle.
- One authority tick consumes one command and grants at most one delta of activity.
  The ten-second window, terminal stop, 75% requirement, 300-second minimum,
  all-original-account/disconnect rule and result/economy formulas remain intact.
- Protocol 6, opt-in prediction, live rewind off, recipient privacy, account
  admission, result durability and offline/online separation remain unchanged.

Use the same oracle on the baseline and candidate and retain failures. Run the
focused activity/stream/lifecycle/match tests, the prior real input-freshness
probe where resources permit, and the maintained aggregate suite on the final
combined source. A separate fresh-context critic must inspect raw evidence and
source before acceptance. G3/G16 remain IN PROGRESS.

## Execution constraints

No engine/native/OCR work until the root releases its local CPU lane. Native
receipts must identify exact source, engine SHA256, command, exit and raw hashes.
Software-render/headless timing does not measure device performance or human play.
