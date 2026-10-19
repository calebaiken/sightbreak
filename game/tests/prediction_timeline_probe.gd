extends SceneTree
## Causal native probe: real authority ticks and replay, deterministic packet timing.
## This does not emulate ENet or change a shipping movement/authority method.

class ProbeMatch extends TacticalMatch:
	func _ready() -> void:
		set_process(false)
		set_physics_process(false)
	func _objective_tick(_delta: float) -> void:
		pass
	func _check_elimination() -> void:
		pass

const PEER := 42
const TICKS := 540
const OFFSET := Vector3(100, 0, 0)
var checks := 0
var failures: Array[String] = []
var output := ""

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)
		push_error(label)

func _initialize() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):
			output = arg.trim_prefix("--output=")
	call_deferred("run")

func block(parent: Node3D, at: Vector3, size: Vector3) -> void:
	var body := StaticBody3D.new()
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = size
	shape.shape = box
	body.add_child(shape)
	parent.add_child(body)
	body.position = at

func vector(value: Vector3) -> Array:
	return [value.x, value.y, value.z]

func percentile(values: Array, fraction: float) -> float:
	if values.is_empty():
		return 0.0
	var sorted := values.duplicate()
	sorted.sort()
	return float(sorted[int((sorted.size() - 1) * fraction)])

func controls(tick: int, jumping: bool) -> Dictionary:
	var section := (tick - 1) / 90 % 6
	return {"move": [Vector2(0, 1), Vector2(1, 0), Vector2(0, -1), Vector2(-1, 0), Vector2(1, 1), Vector2.ZERO][section],
		"look": Vector2.ZERO, "jump": jumping and tick % 180 >= 84 and tick % 180 < 96,
		"crouch": tick >= 360 and tick < 405}

func snapshot_metrics(_predictor: SBMovementPrediction) -> Dictionary:
	return {}

func prediction_metrics(_predictor: SBMovementPrediction) -> Dictionary:
	return {}

func report_metrics() -> Dictionary:
	return {}

func condition(name: String, delay: int, gap: bool, jumping: bool, enabled: bool) -> Dictionary:
	var world := Node3D.new()
	root.add_child(world)
	for offset: Vector3 in [Vector3.ZERO, OFFSET]:
		block(world, offset + Vector3(0, -0.5, 0), Vector3(40, 1, 40))
	var game := ProbeMatch.new()
	game.configure({"mode": "offline"})
	game.local_id = 0
	game.phase = "live"
	game.time_left = 1000
	game._bot_clock = 1000
	game._snapshot_generation = 1
	game._peer_actors[PEER] = 1
	world.add_child(game)
	var authority := SBActor.new()
	var predicted := SBActor.new()
	authority.configure(1, 0, "Authority", true)
	predicted.configure(2, 0, "Prediction", true)
	game.add_child(authority)
	game.actors[1] = authority
	world.add_child(predicted)
	authority.reset_for_round(Vector3(0, 0.05, 0))
	predicted.reset_for_round(OFFSET + Vector3(0, 0.05, 0))
	var predictor := SBMovementPrediction.new()
	var upstream: Array[Dictionary] = []
	var downstream: Array[Dictionary] = []
	var rows: Array = []
	var snapshots: Array = []
	var errors: Array = []
	var held_drift: Array = []
	var held_ticks := 0
	var dropped_packets := 0
	var maximum_authority_height := 0.0
	var last_applied_tick := -1
	var consumed_pose: Dictionary = {}
	var starting_ammo := predicted.ammo
	await physics_frame
	await physics_frame
	for tick in range(1, TICKS + 1):
		# Match._client_tick reconciles before generating this tick's input.
		while not downstream.is_empty() and int(downstream.front().due) <= tick:
			var delivery: Dictionary = downstream.pop_front()
			var state: Dictionary = delivery.state
			var ack := int(state.move_ack)
			var saved: Variant = null
			for record: Dictionary in predictor.pending:
				if int(record.command.sequence) == ack:
					saved = record.position
			var previous := predicted.global_position
			predicted.apply_snapshot(state, 1.0)
			predictor.reconcile(predicted, state, 1, previous, enabled)
			snapshots.append({"receive_tick": tick, "send_tick": delivery.tick, "ack": ack,
				"steps_since_consumption": delivery.held, "authority": vector(state.position - OFFSET),
				"pose_at_consumption": delivery.consumed, "same_ack_drift_m": delivery.drift,
				"saved_ack_pose": vector(saved - OFFSET) if saved is Vector3 else null,
				"ack_error_m": saved.distance_to(state.position) if saved is Vector3 else null,
				"replayed": vector(predicted.global_position - OFFSET), "pending": predictor.pending.size()})
			snapshots.back().merge(snapshot_metrics(predictor))
			last_applied_tick = int(delivery.tick)
		var command := controls(tick, jumping)
		predictor.predict(predicted, command, 1, enabled)
		if tick % 2 == 0:
			# A 100 ms upstream loss burst straddles each direction/jump edge.
			var drop := gap and tick % 90 >= 84
			if drop:
				dropped_packets += 1
			else:
				upstream.append({"due": tick + delay, "packet": predictor.packet().duplicate(true)})
		while not upstream.is_empty() and int(upstream.front().due) <= tick:
			var delivery: Dictionary = upstream.pop_front()
			if game._input_stream.accept(PEER, delivery.packet, 1, int(tick * 1000.0 / 60.0)):
				# Exact effect of the accepted-input timestamp at Match._input_rpc:1011.
				game._last_peer_input[1] = game._elapsed
		var previous_ack := int(game._last_input_sequence.get(1, 0))
		game._elapsed += SBMovementStep.STEP
		game._authority_tick(SBMovementStep.STEP)
		var ack := int(game._last_input_sequence.get(1, 0))
		if ack > previous_ack:
			consumed_pose[ack] = {"position": authority.global_position, "tick": tick}
		elif ack > 0:
			held_ticks += 1
		var original: Dictionary = consumed_pose.get(ack, {"position": authority.global_position, "tick": tick})
		var drift := authority.global_position.distance_to(original.position)
		if drift > 0:
			held_drift.append(drift)
		if tick % 3 == 0:
			var state := authority.snapshot()
			state.position += OFFSET
			state.move_ack = ack
			state.grounded = authority.is_on_floor()
			state.jump_held = authority._jump_previous
			downstream.append({"due": tick + delay + 1, "tick": tick, "state": state,
				"held": tick - int(original.tick), "consumed": vector(original.position), "drift": drift})
		var error := predicted.global_position.distance_to(authority.global_position + OFFSET)
		maximum_authority_height = maxf(maximum_authority_height, authority.global_position.y)
		if tick > 60:
			errors.append(error)
		rows.append({"tick": tick, "ack": ack, "sequence": predictor.sequence,
			"authority": vector(authority.global_position), "prediction": vector(predicted.global_position - OFFSET),
			"error_m": error, "held_steps": tick - int(original.tick), "same_ack_drift_m": drift,
			"last_snapshot_tick": last_applied_tick, "pending": predictor.pending.size(),
			"skipped": game._input_stream.skipped_commands})
		check(game._simulation_tick == tick, name + ": one authority step per physics tick")
		check(predictor.pending.size() <= SBMovementPrediction.MAX_HISTORY, name + ": bounded history")
		await physics_frame
	check(predicted.ammo == starting_ammo and predicted.reload_remaining == 0, name + ": movement does not grant combat")
	check(authority.ammo == starting_ammo and authority.health == 100, name + ": authority resources intact")
	check(not game._prediction_enabled and TacticalMatch.PROTOCOL_VERSION == 6, name + ": defaults and protocol intact")
	check(game._hit_history.frames.is_empty(), name + ": live hit history inactive")
	check(not jumping or maximum_authority_height > 0.4, name + ": jump condition actually leaves the floor")
	var held_snapshots := 0
	var unscored_held_snapshots := 0
	for sample: Dictionary in snapshots:
		if float(sample.same_ack_drift_m) > 0.01:
			held_snapshots += 1
			if sample.ack_error_m == null:
				unscored_held_snapshots += 1
	var result := {"name": name, "one_way_delay_ticks": delay, "upstream_bursts": gap, "jumping": jumping,
		"prediction_enabled": enabled, "ticks": TICKS, "held_ticks": held_ticks, "dropped_packets": dropped_packets,
		"skipped_commands": game._input_stream.skipped_commands, "same_time_error_p95_m": percentile(errors, 0.95),
		"same_time_error_max_m": percentile(errors, 1), "ack_error_p95_m": percentile(predictor.error_samples, 0.95) if enabled else null,
		"ack_error_sample_count": predictor.error_samples.size(), "held_snapshots": held_snapshots,
		"unscored_held_snapshots": unscored_held_snapshots, "maximum_authority_height_m": maximum_authority_height,
		"held_drift_max_m": percentile(held_drift, 1), "hard_corrections": predictor.hard_corrections,
		"rows": rows, "snapshots": snapshots}
	result.merge(prediction_metrics(predictor))
	world.queue_free()
	await process_frame
	await create_timer(0.5).timeout
	return result

func run() -> void:
	var cases: Array = []
	for settings: Array in [["flat-zero", 0, false, false, true], ["flat-100ms", 3, false, false, true],
		["flat-100ms-bursts", 3, true, false, true], ["jump-100ms-bursts", 3, true, true, true],
		["flat-200ms-bursts", 6, true, false, true], ["disabled-100ms-bursts", 3, true, false, false]]:
		cases.append(await condition(settings[0], settings[1], settings[2], settings[3], settings[4]))
	check(cases[0].held_ticks == 0 and cases[1].held_ticks == 0, "loss-free controls consume fresh commands after startup")
	check(cases[1].ack_error_p95_m < 0.001, "flat delayed control isolates movement from transport loss")
	check(cases[2].held_ticks > 0 and cases[2].held_drift_max_m > 0.3, "short loss bursts expose nonstationary acknowledged state")
	check(cases[2].skipped_commands > 0, "recovery exercises the existing bounded backlog policy")
	check(cases[5].ack_error_p95_m == null, "disabled prediction is not scored as predicted ACK accuracy")
	var result := {"scope": "fixed 60 Hz real authority/replay with deterministic in-process packet schedule; not ENet or activation evidence",
		"engine": Engine.get_version_info().string, "checks": checks, "failures": failures, "conditions": cases}
	result.merge(report_metrics())
	if not output.is_empty():
		var file := FileAccess.open(output, FileAccess.WRITE)
		file.store_string(JSON.stringify(result, "\t"))
		file.close()
	print("PREDICTION_TIMELINE_PROBE checks=%d failures=%d" % [checks, failures.size()])
	quit(1 if not failures.is_empty() else 0)
