# Movement timelines

## Remote interpolation — protocol 4

The authority increments a simulation tick every physics step and sends every third tick: exactly 20 snapshots per 60 simulation ticks. Every authorized packet includes `tick`, `epoch` and server elapsed time. A round or server-lobby reset changes the epoch; tick ordering is monotonic within a connection.

`SBSnapshotBuffer` stores at most 32 ordered transform frames. Rendering continuously samples an initially 100 ms delayed timeline; the development setting is clamped to 50–200 ms. Yaw takes the shortest angular path. Duplicate/stale packets are discarded. First visibility holds the first authorized pose while the buffer warms, preventing a forward-then-backward jump. Teleports over 3 m discard that actor's old timeline. Reconnect clears timestamps and epoch state.

Arrival-clock corrections are slewed with a bounded positive rate. A sustained latency increase can temporarily slow presentation while rebuilding the delay; it does not strand the render cursor permanently ahead of the received stream. Position may extrapolate for at most 50 ms after a missing sample, then holds. That extrapolation is not collision-aware and can overshoot stops/thin cover; it is a development limitation requiring further tuning. Metadata such as health, ammunition and death is applied immediately and never interpolated.

Privacy revocation takes effect immediately. This favors withholding fresh hidden state; a delayed visible model may disappear before visually reaching cover. Conservative relevance margins reduce this at corners, but dynamic peeking still needs human/mobile review. Client collision capsules share delayed remote poses; prediction must account for that discrepancy instead of claiming deterministic cross-machine physics.

## Local prediction work

Movement-only replay and ordered redundant input commands are under development on the movement branch. Combat, purchases, objective interactions and rewards remain authoritative. No completed prediction or reconciliation result is claimed by this interpolation milestone.

## Evidence

Maintained buffer suite: 15 checks, including warmup monotonicity and sustained latency changes. Independent real process callbacks observed 200 remote-position changes between packet arrivals. Two real clients passed movement, reconnect and state authorization tests.

`scripts/simulate_network.py` runs real Godot server/client processes through loopback UDP proxies. The fixture records independent authoritative positions at 60 Hz, then compares rendered positions at the chosen delayed server timestamp. This measures interpolation accuracy, not end-to-end input latency or phone performance. See the performance report for results and exact conditions.
