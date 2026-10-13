extends SceneTree
class ProbeMatch extends TacticalMatch:
	func _ready() -> void:
		set_physics_process(false)
		set_process(false)
	func _objective_tick(_delta: float) -> void:
		pass
	func _check_elimination() -> void:
		pass
	func _is_bot(_id: int) -> bool:
		return false
var failures := 0
func check(ok: bool, label: String) -> void:
	if not ok:
		failures += 1
		push_error(label)
func _initialize() -> void:
	call_deferred("run")
func make_match(offset: float) -> ProbeMatch:
	var game := ProbeMatch.new()
	game.phase = "live"
	game.time_left = 999
	game.local_id = 0
	game._snapshot_generation = 1
	root.add_child(game)
	var actor := SBActor.new()
	actor.configure(1, 0, "EdgeProbe", false)
	game.add_child(actor)
	actor.position.x = offset
	actor._deploy_remaining = 0
	game.actors[1] = actor
	game._peer_actors[99] = 1
	game._last_peer_input[1] = 0
	return game
func command(sequence: int) -> Dictionary:
	return {"sequence": sequence, "move": Vector2.ZERO, "look": Vector2.ZERO, "fire": true, "jump": true}
func run() -> void:
	var steady := make_match(100)
	var gap := make_match(200)
	await physics_frame
	for tick in range(180):
		steady._input_stream.accept(99, {"epoch": 1, "commands": [command(tick + 1)]}, 1, tick * 17)
		if tick % 2 == 0:
			gap._input_stream.accept(99, {"epoch": 1, "commands": [command(tick + 1)]}, 1, tick * 17)
		steady._authority_tick(1.0 / 60)
		gap._authority_tick(1.0 / 60)
		await physics_frame
	print("EDGE_PROBE steady_held_shots=%d gap_held_shots=%d gap_rejected=%d" % [15 - steady.actors[1].ammo, 15 - gap.actors[1].ammo, gap._input_stream.rejected])
	check(steady.actors[1].ammo == 14 and gap.actors[1].ammo == 14, "packet gaps cannot invent trigger releases")
	# A long input outage must stop actions without synthesizing new edges.
	gap._elapsed = 10
	for tick in range(30):
		gap._authority_tick(1.0 / 60)
	gap._last_peer_input[1] = 10
	gap._input_stream.accept(99, {"epoch": 1, "commands": [command(181)]}, 1, 4000)
	gap._authority_tick(1.0 / 60)
	check(gap.actors[1].ammo == 14, "sustained outage is not a trigger release")
	var prediction := SBMovementPrediction.new()
	var stream := SBInputStream.new()
	stream.accept(99, {"epoch": 1, "commands": [command(1)]}, 1, 0)
	stream.pop(99)
	prediction.sequence = 1
	for index in range(120):
		prediction.predict(steady.actors[1], {"move": Vector2.ZERO, "look": Vector2.ZERO}, 1, false)
	stream.reset_epoch() # same helper called by _begin_round
	var accepted := 0
	for index in range(200):
		prediction.predict(steady.actors[1], {"move": Vector2.ZERO, "look": Vector2.ZERO}, 2, false)
		if stream.accept(99, prediction.packet(), 2, 3000 + index * 34):
			accepted += 1
		stream.pop(99)
		var state: Dictionary = steady.actors[1].snapshot()
		state.move_ack = int(stream.acknowledged.get(99, 0))
		prediction.reconcile(steady.actors[1], state, 2, steady.actors[1].position, false)
	print("EPOCH_PROBE accepted=%d ack=%d client_sequence=%d pending=%d first_sequence=%d last_sequence=%d" % [accepted, stream.acknowledged[99], prediction.sequence, prediction.pending.size(), prediction.sequence, prediction.sequence])
	check(accepted == 200 and int(stream.acknowledged.get(99, 0)) == 200 and prediction.pending.is_empty(), "new epoch recovers a full previous history")
	steady.queue_free()
	gap.queue_free()
	await process_frame
	await create_timer(0.7).timeout
	print("INPUT_LIFECYCLE_TEST checks=3 failures=%d" % failures)
	quit(1 if failures else 0)
