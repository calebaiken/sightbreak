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
	var accepted_snapshots := 0
	var last_accepted_msec := 0
	var accepted_tick_steps: Array = []
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
		var previous_tick := _replica_buffer.last_tick
		super._apply_snapshot(data)
		if _replica_buffer.last_tick > previous_tick:
			accepted_snapshots += 1
			last_accepted_msec = Time.get_ticks_msec()
			if previous_tick >= 0: accepted_tick_steps.append(_replica_buffer.last_tick - previous_tick)
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
var started_msec := 0
var previous_frame_usec := 0
var wall_elapsed := 0.0
var joined := false
var origin := Vector3.ZERO
var max_distance := 0.0
var prediction_enabled := true
var first_input_time := -1.0
var first_movement_seconds := -1.0
var render_frames: Array[float] = []
var reconnect_at := -1.0
var reconnect_delay := 2.0
var reconnect_started := false
var reconnect_passed := false
var initial_id := 0
var notices: Array = []

func _initialize() -> void:
	started_msec = Time.get_ticks_msec()
	previous_frame_usec = Time.get_ticks_usec()
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--role="): role = arg.get_slice("=", 1)
		elif arg.begins_with("--port="): port = int(arg.get_slice("=", 1))
		elif arg.begins_with("--seconds="): duration = float(arg.get_slice("=", 1))
		elif arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg == "--no-prediction": prediction_enabled = false
		elif arg.begins_with("--reconnect-at="): reconnect_at = float(arg.trim_prefix("--reconnect-at="))
		elif arg.begins_with("--reconnect-delay="): reconnect_delay = float(arg.trim_prefix("--reconnect-delay="))
	call_deferred("start")

func start() -> void:
	game = MeasuredMatch.new()
	game.notification.connect(func(message: String): notices.append({"seconds":wall_elapsed,"simulation_seconds":elapsed,"state":game.connection_state,"message":message}))
	game.configure({"mode": role, "port": port, "address": "127.0.0.1", "name": "Simulation fixture", "prediction": prediction_enabled})
	root.add_child(game)
	if role == "server":
		game._bot_clock = 1000
		game.phase = "live"
		game.time_left = 1000

func _process(delta: float) -> bool:
	elapsed += delta
	wall_elapsed = (Time.get_ticks_msec()-started_msec)/1000.0
	var frame_usec := Time.get_ticks_usec()
	if DisplayServer.get_name() != "headless": render_frames.append((frame_usec-previous_frame_usec)/1000.0)
	previous_frame_usec = frame_usec
	if game == null:
		return false
	if role != "server" and game.connection_state == "connected":
		var actor := game.local_actor()
		if not joined:
			joined = true
			initial_id = game.local_id
			origin = actor.position
			first_input_time = wall_elapsed
		max_distance = maxf(max_distance, origin.distance_to(actor.position))
		if first_movement_seconds < 0 and Vector2(actor.position.x - origin.x, actor.position.z - origin.z).length() > 0.01:
			first_movement_seconds = wall_elapsed - first_input_time
		var section := int(elapsed / 2) % 4
		var move := [Vector2(0, 1), Vector2(1, 0), Vector2(0, -1), Vector2(-1, 0)][section] as Vector2
		game.set_local_input({"move": move, "look": Vector2(PI, 0), "crouch": section == 2, "jump": section == 1 and fmod(elapsed, 2.0) < 0.2})
		if reconnect_started:
			reconnect_passed = game.local_id == initial_id
		elif reconnect_at >= 0 and wall_elapsed >= reconnect_at:
			reconnect_started = true
			game.multiplayer.multiplayer_peer.close()
			game._server_disconnected()
			# Default exercises the real two-second client path; shorter stress delays
			# remain explicit so early reconnect failures cannot be hidden by retiming.
			game._reconnect_clock = reconnect_delay
	if wall_elapsed >= duration:
		render_frames.sort()
		var render_metrics := {"native": DisplayServer.get_name() != "headless", "renderer":RenderingServer.get_video_adapter_name(), "samples":render_frames.size(), "draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), "primitives":Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME), "texture_bytes":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED)}
		if not render_frames.is_empty():
			render_metrics["wall_frame_interval_p50_ms"] = render_frames[render_frames.size()/2]
			render_metrics["wall_frame_interval_p95_ms"] = render_frames[mini(render_frames.size()-1, int(render_frames.size()*0.95))]
		var report := {"role": role, "joined": joined, "state": game.connection_state, "notifications":notices, "elapsed_seconds": elapsed, "wall_elapsed_seconds":wall_elapsed, "max_displacement": max_distance, "render_metrics":render_metrics,
			"first_movement_seconds": first_movement_seconds, "prediction_enabled": prediction_enabled, "prediction_errors_m": game._prediction.error_samples,
			"corrections": game._prediction.corrections, "hard_corrections": game._prediction.hard_corrections,
			"reconnect_requested":reconnect_at >= 0,"reconnect_delay_seconds":reconnect_delay,"reconnect_passed":reconnect_passed,"initial_id":initial_id,"final_id":game.local_id,
			"pending_inputs": game._prediction.pending.size(), "large_corrections": game._prediction.large_corrections,
			"last_snapshot_age_seconds": (Time.get_ticks_msec() - game.last_snapshot_msec) / 1000.0, "snapshots": game.received_snapshots, "snapshot_tick_gaps": game.snapshot_steps, "reencoded_snapshot_bytes": game.received_payload_bytes,
			"accepted_snapshots":game.accepted_snapshots,"last_accepted_age_seconds":(Time.get_ticks_msec()-game.last_accepted_msec)/1000.0,"last_accepted_tick":game._replica_buffer.last_tick,"accepted_tick_gaps":game.accepted_tick_steps,
			"skipped_commands": game._input_stream.skipped_commands, "tick_usec": game.ticks, "tick_intervals_usec": game.tick_intervals, "poses": game.records, "stale_snapshots": game._replica_buffer.stale_packets}
		if not output.is_empty():
			var file := FileAccess.open(output, FileAccess.WRITE)
			file.store_string(JSON.stringify(report))
			file.close()
		print("NETWORK_SIMULATION " + JSON.stringify({"role": role, "joined": joined, "last_snapshot_age_seconds": (Time.get_ticks_msec() - game.last_snapshot_msec) / 1000.0, "snapshots": game.received_snapshots, "max_displacement": max_distance}))
		var success := role == "server" or (joined and game.connection_state == "connected" and Time.get_ticks_msec() - game.last_snapshot_msec < 750 and game.received_snapshots >= 10 and max_distance > 0.1)
		if role != "server" and reconnect_at >= 0: success = success and reconnect_passed
		if role != "server": success = success and game.accepted_snapshots >= 10 and Time.get_ticks_msec()-game.last_accepted_msec < 750
		game.queue_free()
		quit(0 if success else 1)
	return false
