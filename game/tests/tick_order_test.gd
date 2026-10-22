extends SceneTree
## The authoritative tick must not favour any actor id. A shot lands the moment its actor is processed, so a fixed
## processing order let the lowest ids win every same-tick trade (actors 1-5 won about 71% of all-bot rounds
## whichever side they played, 46% with the order reversed). The order is now a uniform shuffle each tick.
##
## The check that matters is per pair, not per actor: rotating the start by one place per tick makes every actor lead
## equally often yet leaves ids 5 and 6 in that order nine ticks in ten.
const TICKS := 20000
const PAIR_TOLERANCE := 0.03
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	run.call_deferred()

func check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

func order_ids(match_node: TacticalMatch) -> Array:
	return match_node._tick_order().map(func(actor: SBActor) -> int: return actor.actor_id)

func run() -> void:
	var match_node := TacticalMatch.new()
	match_node.configure({"mode": "offline", "difficulty": "normal"})
	root.add_child(match_node)
	await process_frame
	var ids: Array = match_node.actors.keys()
	ids.sort()
	check(ids.size() == 10, "ten actors in an offline match")

	match_node._order_rng.seed = 20261022
	var first_orders: Array = []
	var before_count := {}
	var lead := {}
	for id: int in ids:
		lead[id] = 0
	for a_index in range(ids.size()):
		for b_index in range(a_index + 1, ids.size()):
			before_count["%d,%d" % [ids[a_index], ids[b_index]]] = 0
	var distinct_orders := {}
	var every_tick_complete := true
	for tick in range(TICKS):
		# Step the counter as the physics loop does, so an order derived from the tick is exercised too.
		match_node._simulation_tick = tick
		var order: Array = order_ids(match_node)
		var sorted_order := order.duplicate()
		sorted_order.sort()
		if sorted_order != ids:
			every_tick_complete = false
			check(false, "tick %d does not process every actor exactly once: %s" % [tick, str(order)])
			break
		if tick < 8:
			first_orders.append(order)
		lead[order[0]] += 1
		distinct_orders[str(order)] = true
		var position := {}
		for index in range(order.size()):
			position[order[index]] = index
		for a_index in range(ids.size()):
			for b_index in range(a_index + 1, ids.size()):
				if position[ids[a_index]] < position[ids[b_index]]:
					before_count["%d,%d" % [ids[a_index], ids[b_index]]] += 1
	check(every_tick_complete, "every tick processed every actor exactly once")
	check(distinct_orders.size() > TICKS / 2, "orders vary tick to tick (%d distinct in %d)" % [distinct_orders.size(), TICKS])

	var worst_pair := ""
	var worst_gap := 0.0
	for key: String in before_count:
		var fraction: float = float(before_count[key]) / TICKS
		var gap: float = absf(fraction - 0.5)
		if gap > worst_gap:
			worst_gap = gap
			worst_pair = key
		check(gap <= PAIR_TOLERANCE, "actors %s: the first goes first %.1f%% of ticks (allowed %.0f%% to %.0f%%)" % [key, fraction * 100.0, (0.5 - PAIR_TOLERANCE) * 100.0, (0.5 + PAIR_TOLERANCE) * 100.0])
	for id: int in ids:
		var share: float = float(lead[id]) / TICKS
		check(absf(share - 0.1) <= 0.02, "actor %d leads %.1f%% of ticks (about 10%% expected)" % [id, share * 100.0])
	print("TICK_ORDER_PAIRS worst_pair=%s gap=%.4f over %d ticks" % [worst_pair, worst_gap, TICKS])

	# The same seed gives the same sequence; a different seed does not.
	match_node._order_rng.seed = 20261022
	var again: Array = []
	for _tick in range(8):
		again.append(order_ids(match_node))
	check(again == first_orders, "the same seed gives the same orders")
	match_node._order_rng.seed = 7
	var other: Array = []
	for _tick in range(8):
		other.append(order_ids(match_node))
	check(other != first_orders, "a different seed gives different orders")

	# The shuffle must not touch the gameplay random stream.
	match_node._rng.seed = 99
	var expected_roll := RandomNumberGenerator.new()
	expected_roll.seed = 99
	for _tick in range(50):
		match_node._tick_order()
	check(match_node._rng.randi() == expected_roll.randi(), "shuffling leaves the gameplay random stream alone")

	match_node.queue_free()
	await process_frame
	print("TICK_ORDER_TEST checks=%d failures=%d" % [checks, failures.size()])
	quit(0 if failures.is_empty() else 1)
