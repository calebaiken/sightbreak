extends SceneTree
## Two real CharacterBody3D instances, identical static geometry, delayed snapshots.
var checks := 0
var failures := 0
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(label)
func block(parent: Node3D, at: Vector3, size: Vector3) -> void:
	var body := StaticBody3D.new()
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = size
	shape.shape = box
	body.add_child(shape)
	parent.add_child(body)
	body.position = at
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	native_input_observation_controls() # INPUT_OBSERVATION_HOOK
	var world := Node3D.new()
	root.add_child(world)
	var authority := SBActor.new()
	var predicted := SBActor.new()
	authority.configure(1, 0, "Authority", true)
	predicted.configure(2, 0, "Prediction", true)
	for offset in [0.0, 100.0]:
		block(world, Vector3(offset, -0.5, 0), Vector3(40, 1, 40))
		block(world, Vector3(offset, 1.5, -4), Vector3(6, 3, 0.5))
	world.add_child(authority)
	world.add_child(predicted)
	authority.reset_for_round(Vector3(0, 0.05, 0))
	predicted.reset_for_round(Vector3(100, 0.05, 0))
	var predictor := SBMovementPrediction.new()
	var snapshots: Array[Dictionary] = []
	var original_ammo := predicted.ammo
	var maximum := 0.0
	var jumped := false
	var crouched := false
	await physics_frame
	await physics_frame
	for tick in range(360):
		var section := tick / 60
		var move := [Vector2(0, 1), Vector2(1, 1), Vector2(-1, 0), Vector2(0, -1), Vector2(0, 1), Vector2.ZERO][section] as Vector2
		var controls := {"move": move, "look": Vector2.ZERO, "jump": tick == 75 or tick == 185, "crouch": tick >= 240 and tick < 285, "fire": true, "reload": true}
		SBMovementStep.advance(authority, controls, 1.0 / 60.0)
		predictor.predict(predicted, controls, 1, true)
		jumped = jumped or authority.position.y > 0.4
		crouched = crouched or authority._crouching
		var state := authority.snapshot()
		state.position += Vector3(100, 0, 0)
		state.move_ack = tick + 1
		state.jump_held = authority._jump_previous
		state.grounded = authority.is_on_floor()
		snapshots.append(state)
		if tick >= 6 and tick % 3 == 0:
			var previous := predicted.position
			predicted.apply_snapshot(snapshots[tick - 6], 1.0)
			predictor.reconcile(predicted, snapshots[tick - 6], 1, previous, true)
		var error := predicted.position.distance_to(authority.position + Vector3(100, 0, 0))
		maximum = maxf(maximum, error)
		check(error < 0.13, "bounded replay error tick=%d error=%f" % [tick, error])
		check(absf(predicted.position.x - 100) >= 3.0 or absf(predicted.position.z + 4) >= 0.25, "prediction does not overlap wall")
		await physics_frame
	check(jumped and crouched, "fixture covers jump landing and crouch")
	check(predicted.ammo == original_ammo and predicted.reload_remaining == 0, "movement replay does not fire or reload")
	check(predictor.pending.size() <= 9 and predictor.hard_corrections == 0, "history drains and ordinary replay avoids hard correction")
	predictor.reconcile(predicted, snapshots.back(), 2, predicted.position, true)
	check(predictor.pending.is_empty() and predictor.visual_offset == Vector3.ZERO, "round epoch clears pending history and correction")
	predictor.reset(true)
	check(predictor.sequence == 0 and predictor.pending.is_empty(), "reconnect resets sequence")
	world.queue_free()
	await process_frame
	print("MOVEMENT_PREDICTION_TEST checks=%d failures=%d maximum_error_m=%f" % [checks, failures, maximum])
	quit(1 if failures else 0)
# BEGIN INPUT OBSERVATION TESTS
func native_input_observation_controls() -> void:
	var requested := PackedStringArray(["--native-input-observation"])
	var guest := {"mode": "client", "address": "127.0.0.1"}
	check(TacticalMatch._native_input_allowed(guest, requested, true), "explicit debug guest loopback observer admitted")
	check(not TacticalMatch._native_input_allowed(guest, requested, false), "release observer denied")
	check(not TacticalMatch._native_input_allowed(guest, PackedStringArray(), true), "unrequested observer denied")
	for patch: Dictionary in [{"address": "192.0.2.1"}, {"join_ticket": "fictional-test-ticket"}, {"require_accounts": true}, {"mode": "offline"}, {"mode": "server"}]:
		check(not TacticalMatch._native_input_allowed(guest.merged(patch, true), requested, true), "remote/account/offline/normal-server observer denied")
	check(TacticalMatch._native_input_allowed({"mode": "server", "_native_input_fixture": true}, requested, true), "explicit source guest fixture observer admitted")
	check(not TacticalMatch._native_input_allowed({"mode": "server", "_native_input_fixture": true, "require_accounts": true}, requested, true), "account fixture observer denied")
	var command := {"sequence": 7, "move": Vector2.LEFT, "look": Vector2(1, 1), "fire": true, "reload": false, "private_sentinel": "DO_NOT_PROJECT"}
	var before := var_to_bytes(command)
	var projected := TacticalMatch._native_input_controls(command)
	check(var_to_bytes(command) == before and projected.size() == 4, "control projection preserves source and copies only declared fields")
	check(projected.move == [-1.0, 0.0] and projected.fire and not projected.reload, "own input projection retains sampled intent")
	check(not JSON.stringify(projected).contains("DO_NOT_PROJECT") and not projected.has("look"), "projection omits private and aim fields")
	check(not TacticalMatch._native_input_controls({"fire": 1, "reload": "true"}).fire, "malformed flags cannot become observed fire")
	var packet := {"epoch": 3, "commands": []}
	for index in range(20): packet.commands.append(command.duplicate(true))
	var packet_before := var_to_bytes(packet)
	var header := TacticalMatch._native_input_packet(packet)
	check(header.count == 20 and header.fire == 12 and header.moving == 12 and header.epoch == 3, "packet projection reports full count but bounds inspected commands")
	check(var_to_bytes(packet) == packet_before and not JSON.stringify(header).contains("DO_NOT_PROJECT"), "packet projection is read-only and omits body")
	var inactive := TacticalMatch.new()
	inactive._local_input = command.duplicate(true)
	var input_before := var_to_bytes(inactive._local_input)
	inactive._native_input_observe("input_consumed", 42, command)
	check(inactive._native_input_observation.is_empty() and var_to_bytes(inactive._local_input) == input_before and inactive._prediction.pending.is_empty() and inactive._input_stream.queues.is_empty(), "disabled observer collects nothing and changes no input/prediction/stream state")
	inactive.free()
# END INPUT OBSERVATION TESTS
