extends SceneTree

var checks := 0
var failures := 0
var events: Array[Dictionary] = []
var stream: SBInputStream
const PEER := 41
const EPOCH := 7

func command(sequence: int, move := Vector2.RIGHT, fire := false) -> Dictionary:
	return {"sequence": sequence, "move": move, "look": Vector2.ZERO, "fire": fire}

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(label)

func encoded(value: Variant) -> Variant:
	if value is Vector2:
		return [value.x, value.y]
	if value is Dictionary:
		var result: Dictionary = {}
		for key: Variant in value:
			result[str(key)] = encoded(value[key])
		return result
	if value is Array:
		var result: Array = []
		for item: Variant in value:
			result.append(encoded(item))
		return result
	return value

func state() -> Dictionary:
	return {"ack": stream.acknowledged.get(PEER, 0), "queue": encoded(stream.queues.get(PEER, {}).duplicate(true)), "rate": stream.rates.get(PEER, {}).duplicate(true), "rejected": stream.rejected}

func accept_trace(label: String, commands: Array, supplied_clock_ms: int, epoch := EPOCH) -> bool:
	var packet := {"epoch": epoch, "commands": commands}
	var wire := var_to_bytes(packet)
	var before := state()
	var accepted := stream.accept(PEER, bytes_to_var(wire), EPOCH, supplied_clock_ms)
	events.append({"event": label, "operation": "accept", "supplied_rate_clock_ms": supplied_clock_ms, "capture_monotonic_ms": Time.get_ticks_msec(), "packet": encoded(packet), "packet_variant_bytes_hex": wire.hex_encode(), "before": before, "accepted": accepted, "after": state()})
	return accepted

func pop_trace(label: String) -> Dictionary:
	var before := state()
	var popped := stream.pop(PEER)
	events.append({"event": label, "operation": "pop", "capture_monotonic_ms": Time.get_ticks_msec(), "before": before, "popped": encoded(popped), "after": state()})
	return popped

func _initialize() -> void:
	stream = SBInputStream.new()
	var original := [command(1, Vector2.RIGHT, true), command(2, Vector2.RIGHT, false)]
	check(accept_trace("fresh_batch", original, 1000), "fresh batch accepted")
	var queued: Dictionary = state().queue
	check(accept_trace("identical_queued_retry", original, 1100), "unacknowledged identical retry accepted")
	check(state().queue == queued and int(state().ack) == 0, "queued duplicate changes no command identity or ack")
	check(accept_trace("altered_queued_retry", [command(1, Vector2.LEFT, false), command(2, Vector2.LEFT, true)], 1150), "queued retry accepted without rewriting payload")
	check(state().queue == queued, "altered duplicate cannot rewrite original movement or fire edge")
	var first := pop_trace("consume_first")
	check(first.sequence == 1 and first.move == Vector2.RIGHT and first.fire and int(state().ack) == 1, "first original payload consumed once")
	check(accept_trace("partially_acked_retry", original, 1200), "partially acknowledged batch still has queued intent")
	check(stream.queues[PEER].size() == 1, "partially acknowledged retry does not requeue acked command")
	var second := pop_trace("consume_second")
	check(second.sequence == 2 and second.move == Vector2.RIGHT and not second.fire and int(state().ack) == 2, "second original payload consumed once")
	check(stream.queues[PEER].is_empty(), "queue empty after both consumed")
	# Outcome under comparison is recorded, not asserted to the candidate's answer.
	accept_trace("fully_acked_identical_replay", original, 1300)
	check(int(state().ack) == 2 and stream.queues[PEER].is_empty(), "fully acknowledged replay cannot create simulation work")
	accept_trace("fully_acked_altered_replay", [command(1, Vector2.LEFT), command(2, Vector2.LEFT, true)], 1350)
	check(int(state().ack) == 2 and stream.queues[PEER].is_empty(), "altered fully acknowledged replay cannot rewrite work")
	check(accept_trace("mixed_acked_and_new_intent", [command(2), command(3, Vector2.LEFT, true)], 1400), "mixed batch retains genuine newer intent")
	check(accept_trace("new_intent_queued_retry", [command(3, Vector2.LEFT, true)], 1450), "genuine queued retry remains accepted")
	var third := pop_trace("consume_new_intent")
	check(third.sequence == 3 and third.move == Vector2.LEFT and third.fire, "new intent preserves original left movement and edge")
	check(pop_trace("no_duplicate_simulation").is_empty(), "no duplicate simulation command")
	check(not accept_trace("old_epoch", [command(4)], 1500, EPOCH - 1), "old epoch rejected")
	check(not accept_trace("beyond_ahead_limit", [command(124)], 1550), "120-command ahead boundary enforced")
	var malformed := command(2)
	malformed.fire = "not a boolean"
	check(not accept_trace("malformed_acked_command_with_new_intent", [malformed, command(4)], 1600), "invalid stale payload cannot bypass sanitization")
	check(stream.queues[PEER].is_empty() and int(state().ack) == 3, "rejected batches do not mutate queued intent or ack")
	stream.forget(PEER)
	check(not stream.queues.has(PEER) and not stream.acknowledged.has(PEER) and not stream.rates.has(PEER), "disconnect forgets all stream-owned peer state")
	print("INPUT_BOUNDARY_RESULT " + JSON.stringify({"checks": checks, "failures": failures, "events": events, "scope": "Native production InputStream component, serialized dictionary boundary; supplied rate clock is fixture-controlled; no Match simulation/lifecycle timers, actor firing, UDP or stock-client reconnect exercised."}))
	quit(1 if failures else 0)
