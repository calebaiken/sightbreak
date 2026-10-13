# Movement timelines

## Remote interpolation — protocol 4

The authority increments a simulation tick every physics step and sends every third tick: exactly 20 snapshots per 60 simulation ticks. Every authorized packet includes `tick`, `epoch` and server elapsed time. A round or server-lobby reset changes the epoch; tick ordering is monotonic within a connection.

`SBSnapshotBuffer` stores at most 32 ordered transform frames. Rendering continuously samples an initially 100 ms delayed timeline; the development setting is clamped to 50–200 ms. Yaw takes the shortest angular path. Duplicate/stale packets are discarded. First visibility holds the first authorized pose while the buffer warms, preventing a forward-then-backward jump. Teleports over 3 m discard that actor's old timeline. Reconnect clears timestamps and epoch state.

Arrival-clock corrections are slewed with a bounded positive rate. A sustained latency increase can temporarily slow presentation while rebuilding the delay; it does not strand the render cursor permanently ahead of the received stream. Position may extrapolate for at most 50 ms after a missing sample, then holds. That extrapolation is not collision-aware and can overshoot stops/thin cover; it is a development limitation requiring further tuning. Metadata such as health, ammunition and death is applied immediately and never interpolated.

Privacy revocation takes effect immediately. This favors withholding fresh hidden state; a delayed visible model may disappear before visually reaching cover. Conservative relevance margins reduce this at corners, but dynamic peeking still needs human/mobile review. Client collision capsules share delayed remote poses; prediction must account for that discrepancy instead of claiming deterministic cross-machine physics.

## Local prediction — protocol 5, opt-in development implementation

`SBMovementStep` shares the original fixed-step actor movement with a client-only replay path. It never fires, reloads, damages, buys or awards anything. Clients generate numbered commands at 60 Hz and submit up to 12 redundant commands at 30 Hz. Compressed input is capped at 1,100 bytes (8 KiB decode ceiling); the server validates types, finite vectors, epoch, sequence window and packet rate. It processes at most one command per authority physics tick. Packets and client timestamps cannot grant simulation time.

Owner-only snapshots acknowledge the consumed/discarded command prefix and include grounded/jump-held state. The client restores the authoritative state and replays up to 120 pending commands **inside the physics callback**. Replaying inside an RPC/render callback is incorrect because `move_and_slide` would use its render timestep. Authoritative floor state seeds the first replay step; later steps rebuild collision contacts. Round epochs reset both sequence spaces and queues; reconnect starts a fresh sequence.

Held controls survive short packet gaps, preventing synthetic semi-auto/jump/utility presses. After 300 ms of silence, authority movement/actions stop while edge state is retained until a real release. A backlog above six commands discards stale intent and retains the newest two: transient loss cannot permanently add input delay. This may discard a brief jump/fire/reload action during burst loss. No extra combat ticks compensate for discarded commands.

Visual correction is limited to 0.35 m, exponentially decays, and ray-clamps the camera against static cover. Corrections over 2 m snap. The server remains final for collision and all competitive state. Godot floor/contact state is not fully serializable; dynamic actors use delayed replica collision poses. Ordinary corner and player collisions can therefore cause correction. Independent review requires this implementation to remain **opt-in**: pass `-- --network-prediction` when launching a native network client, or set the internal development match option `prediction: true`. The normal client keeps authoritative local movement; C1 remote interpolation remains enabled. Real-map p95 acknowledgment divergence around 0.6 m is substantial compared with the visual correction cap. Prediction feel and the 8.5/10 quality gate remain **UNVERIFIED / NOT ACCEPTED**.

Maintained movement replay: 725 checks, maximum 0.075834 m discrepancy in a six-step delayed static-world fixture covering forward/strafe/diagonal/reversal, jumping, landing, crouch, walls, epoch and reconnect. Input-stream tests cover bounded queues, immutable sequence identities, malformed input and recovery after a 200 ms burst outage. Real-process measurements and independent review are reported separately.

## Evidence

Maintained buffer suite: 15 checks, including warmup monotonicity and sustained latency changes. Independent real process callbacks observed 200 remote-position changes between packet arrivals. Two real clients passed movement, reconnect and state authorization tests.

`scripts/simulate_network.py` runs real Godot server/client processes through loopback UDP proxies. The fixture records independent authoritative positions at 60 Hz, then compares rendered positions at the chosen delayed server timestamp. This measures interpolation accuracy, not end-to-end input latency or phone performance. See the performance report for results and exact conditions.
