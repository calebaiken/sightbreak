# Lifecycle clock correction and causal expansion, before execution

The v1/v2 emitter used input_age_msec0 and deadline_remaining_msec20000 for
all bound rows. These placeholders do not follow PeerLifecycle's persistent
last_input and fixed connection deadline. Its expiry hook also lacked the
required idle/deadline wait and pre-service authority_tick. Preserve every
original runner/input/result. The v2 pass is only a causal-model check with
these unvalidated placeholders; do not claim full source-faithful lifecycle
acceptance from it.

Register v3 oracle correction: connected records last_input/connect timestamp
and deadline=connect+20000; admitted/accepted activity updates last_input only;
rows compute input age and remaining deadline from that state. Joined idle
expiry waits until last_input+30000 and runs the pre-service authority tick,
then expiry hook, disconnect hook, forget and fresh generation rebind. This
changes helper metadata/source timing, not any analyzer expectation or guard.
Rerun all26 pairs in separate v3 outputs; keep v1/v2 unchanged.

Add exact expiry pair: positive joined idle expiry with age>=30000; negative
changes only that emitted expiry row to input_age_msec0 and positive remaining
deadline20000. PeerLifecycle.expired permits (rejected OR notjoined) only when
now>=deadline, OR joined only when now-last_input>=30000. A joined row with age0
and deadline still future satisfies neither branch even with an unobserved
rejection. Require INVALID for this contradiction, independent of later cache
or ownership behavior. Retain source-positive pair and exact mutation.

Also register equal-clock versions of complete cached A/B and both epoch-order
traces, unchanged latest across multiple resets, intermediate accepted epoch2
between observed1→3 with later empty queue, out-of-range accepted epoch0/4,
post-reset accepted endpoint122 outside ACK0+120, and two source-valid UNKNOWN
orderings (accept/pop before reset; reset then accept/pop). A separate invalid
client cache combined with authority UNKNOWN must remain INVALID. These are
additive fresh cases; do not alter previous inputs or expectations.
