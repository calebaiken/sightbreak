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
