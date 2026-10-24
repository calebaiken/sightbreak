# Rejection state rule is bounded by actual stream lifetime

Late static scope check found Match1468–1479 replaces _input_stream during
_reset_server_match. This deliberately preserves observer counters/latest while
resetting stream rejected/skipped/queues. Do not implement a universal equality
between observer rejection counter and stream_rejected across such a reset.

The retained independent inverse rejection falsifier and normalized malformed
fixture contradictions keep the same live peer binding, epoch1 and lifecycle
counter history. The reset requires _peer_actors.is_empty() and increments
_snapshot_generation. No peer disconnect can be hidden because all lifecycle
calls emit. Thus the possible stream replacement does not explain state0 in
these cases; their false-accept verdict remains supported. The paired positive
state1/counter1 keeps exactly that same lifetime/context and passes.

The initial fresh-case source_basis text is short and lacks this reset caveat;
raw files remain unchanged. This adjudication narrows the rule to the actual
falsifier instead of treating source reads as support for an unbounded rule.
