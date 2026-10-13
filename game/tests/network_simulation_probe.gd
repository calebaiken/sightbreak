extends SceneTree
## Real guest server/client fixture. No account credentials or rewards involved.
class MeasuredMatch extends TacticalMatch:
	var records: Array = []
	var ticks: Array = []
	var received_payload_bytes := 0
	var received_snapshots := 0
	var last_snapshot_msec := 0
	var snapshot_steps: Array = []
	var last_received_tick := -1
	var tick_intervals: Array = []
	var _last_tick_start := 0
	func _authority_tick(delta: float) -> void:
		var start := Time.get_ticks_usec()
		if _last_tick_start > 0:
			tick_intervals.append(start - _last_tick_start)
		_last_tick_start = start
		super._authority_tick(delta)
		ticks.append(Time.get_ticks_usec() - start)
		# Independent 60 Hz ground truth, not a copy of the 20 Hz send timeline.
		for id: int in _peer_actors.values():
			var at: Vector3 = actors[id].position
			records.append({"t": _elapsed, "id": id, "x": at.x, "y": at.y, "z": at.z})
	func _apply_snapshot(data: Dictionary) -> void:
		received_snapshots += 1
		last_snapshot_msec = Time.get_ticks_msec()
		# Explicit size proxy including the welcome, not actual transport bytes.
		received_payload_bytes += var_to_bytes(data).compress(FileAccess.COMPRESSION_DEFLATE).size()
		if last_received_tick >= 0:
			snapshot_steps.append(int(data.tick) - last_received_tick)
		last_received_tick = int(data.tick)
		super._apply_snapshot(data)
	func _process(delta: float) -> void:
		super._process(delta)
		if _authority or connection_state != "connected":
			return
		for id: int in _connected_actor_ids:
			if id == local_id or not actors.has(id) or not actors[id].visible:
				continue
			var at: Vector3 = actors[id].position
			records.append({"t": _replica_buffer.clock - _replica_buffer.delay_seconds, "id": id, "x": at.x, "y": at.y, "z": at.z})

var game: MeasuredMatch
var role := "client"
var port := 29400
var duration := 14.0
var output := ""
var elapsed := 0.0
var joined := false
var origin := Vector3.ZERO
var max_distance := 0.0
var prediction_enabled := true
var first_input_time := -1.0
var first_movement_seconds := -1.0

func _initialize() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--role="): role = arg.get_slice("=", 1)
		elif arg.begins_with("--port="): port = int(arg.get_slice("=", 1))
		elif arg.begins_with("--seconds="): duration = float(arg.get_slice("=", 1))
		elif arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg == "--no-prediction": prediction_enabled = false
	call_deferred("start")

func start() -> void:
	game = MeasuredMatch.new()
	game.configure({"mode": role, "port": port, "address": "127.0.0.1", "name": "Simulation fixture", "prediction": prediction_enabled})
	root.add_child(game)
	if role == "server":
		game._bot_clock = 1000
		game.phase = "live"
		game.time_left = 1000

func _process(delta: float) -> bool:
	elapsed += delta
	if game == null:
		return false
	if role != "server" and game.connection_state == "connected":
		var actor := game.local_actor()
		if not joined:
			joined = true
			origin = actor.position
			first_input_time = elapsed
		max_distance = maxf(max_distance, origin.distance_to(actor.position))
		if first_movement_seconds < 0 and Vector2(actor.position.x - origin.x, actor.position.z - origin.z).length() > 0.01:
			first_movement_seconds = elapsed - first_input_time
		var section := int(elapsed / 2) % 4
		var move := [Vector2(0, 1), Vector2(1, 0), Vector2(0, -1), Vector2(-1, 0)][section] as Vector2
		game.set_local_input({"move": move, "look": Vector2(PI, 0), "crouch": section == 2, "jump": section == 1 and fmod(elapsed, 2.0) < 0.2})
	if elapsed >= duration:
		var report := {"role": role, "joined": joined, "state": game.connection_state, "elapsed_seconds": elapsed, "max_displacement": max_distance,
			"first_movement_seconds": first_movement_seconds, "prediction_enabled": prediction_enabled, "prediction_errors_m": game._prediction.error_samples,
			"corrections": game._prediction.corrections, "hard_corrections": game._prediction.hard_corrections,
			"pending_inputs": game._prediction.pending.size(), "large_corrections": game._prediction.large_corrections,
			"last_snapshot_age_seconds": (Time.get_ticks_msec() - game.last_snapshot_msec) / 1000.0, "snapshots": game.received_snapshots, "snapshot_tick_gaps": game.snapshot_steps, "reencoded_snapshot_bytes": game.received_payload_bytes,
			"skipped_commands": game._input_stream.skipped_commands, "tick_usec": game.ticks, "tick_intervals_usec": game.tick_intervals, "poses": game.records, "stale_snapshots": game._replica_buffer.stale_packets}
		if not output.is_empty():
			var file := FileAccess.open(output, FileAccess.WRITE)
			file.store_string(JSON.stringify(report))
			file.close()
		print("NETWORK_SIMULATION " + JSON.stringify({"role": role, "joined": joined, "last_snapshot_age_seconds": (Time.get_ticks_msec() - game.last_snapshot_msec) / 1000.0, "snapshots": game.received_snapshots, "max_displacement": max_distance}))
		var success := role == "server" or (joined and game.connection_state == "connected" and Time.get_ticks_msec() - game.last_snapshot_msec < 750 and game.received_snapshots >= 10 and max_distance > 0.1)
		game.queue_free()
		quit(0 if success else 1)
	return false
