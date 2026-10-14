extends SceneTree
## Real guest or isolated-account fixture. Credentials stay in process environment; no rewards claimed.
class MeasuredMatch extends TacticalMatch:
	var records: Array = []
	var lifecycle_events: Array = []
	var occupancy: Array = []
	var _occupancy_next := 0
	func event(kind: String, peer: int, detail: Dictionary = {}) -> void:
		lifecycle_events.append({"msec": Time.get_ticks_msec(), "kind": kind, "peer": peer, "actor": int(_peer_actors.get(peer, 0)), "detail": detail})
	func _peer_connected(peer: int) -> void:
		event("connected", peer)
		super._peer_connected(peer)
	func _peer_disconnected(peer: int) -> void:
		event("disconnected", peer)
		super._peer_disconnected(peer)
	func _reject_join(peer: int, reason: String) -> void:
		event("rejected", peer, {"reason": reason, "bound_actors": _peer_actors.values(), "reserved_actor_ids": _reservations.values().map(func(r): return r.id)})
		super._reject_join(peer, reason)
	func _service_peers() -> void:
		var now := Time.get_ticks_msec()
		if now >= _occupancy_next:
			_occupancy_next = now + 100
			var transport := multiplayer.multiplayer_peer as ENetMultiplayerPeer
			var states: Array = []
			for packet: ENetPacketPeer in transport.host.get_peers():
				states.append({"state":packet.get_state(), "port":packet.get_remote_port()})
			var bindings: Array = []
			for peer: int in _peer_actors:
				bindings.append({"peer":peer,"actor":_peer_actors[peer],"idle_msec":now-int(_peer_lifecycle.peers.get(peer, {}).get("last_input", now)),"input_ack":int(_input_stream.acknowledged.get(peer,0))})
			occupancy.append({"msec":now,"enet":states,"bindings":bindings,"authenticating":(multiplayer as SceneMultiplayer).get_authenticating_peers(),"pending":_pending_joins.size()})
		super._service_peers()
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
	var measuring := true
	func _authority_tick(delta: float) -> void:
		var start := Time.get_ticks_usec()
		if measuring and _last_tick_start > 0:
			tick_intervals.append(start - _last_tick_start)
		_last_tick_start = start
		super._authority_tick(delta)
		if not measuring: return
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
		if not measuring or _authority or connection_state != "connected":
			return
		for id: int in _connected_actor_ids:
			if id == local_id or not actors.has(id) or not actors[id].visible:
				continue
			var at: Vector3 = actors[id].position
			records.append({"t": _replica_buffer.clock - _replica_buffer.delay_seconds, "id": id, "x": at.x, "y": at.y, "z": at.z})

var game: MeasuredMatch
var role := "client"
var account_mode := false
var initial_accounts: Dictionary = {}
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
var recovered_at := -1.0
var initial_id := 0
var notices: Array = []
var barrier := ""
var barrier_ready := false
var measuring := false
var reported := false
var passed := false
var start_epoch := 0.0
var start_offset_seconds := 0.0
var startup_started_msec := 0

func _initialize() -> void:
	started_msec = Time.get_ticks_msec()
	startup_started_msec = started_msec
	previous_frame_usec = Time.get_ticks_usec()
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--role="): role = arg.get_slice("=", 1)
		elif arg.begins_with("--port="): port = int(arg.get_slice("=", 1))
		elif arg.begins_with("--seconds="): duration = float(arg.get_slice("=", 1))
		elif arg.begins_with("--barrier="): barrier = arg.trim_prefix("--barrier=")
		elif arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg == "--no-prediction": prediction_enabled = false
		elif arg == "--accounts": account_mode = true
		elif arg.begins_with("--reconnect-at="): reconnect_at = float(arg.trim_prefix("--reconnect-at="))
		elif arg.begins_with("--reconnect-delay="): reconnect_delay = float(arg.trim_prefix("--reconnect-delay="))
	call_deferred("start")

func start() -> void:
	game = MeasuredMatch.new()
	game.measuring = barrier.is_empty()
	game.notification.connect(func(message: String): notices.append({"seconds":wall_elapsed,"simulation_seconds":elapsed,"state":game.connection_state,"message":message}))
	game.configure({"mode": role, "port": port, "address": "127.0.0.1", "name": "Simulation fixture", "prediction": prediction_enabled, "require_accounts":account_mode and role == "server", "economy_url":OS.get_environment("SIGHTBREAK_TEST_ECONOMY_URL"), "server_id":"local-relay", "join_ticket":OS.get_environment("SIGHTBREAK_JOIN_TICKET")})
	root.add_child(game)
	if role == "server" and not account_mode:
		game._bot_clock = 1000
		game.phase = "live"
		game.time_left = 1000

func _process(delta: float) -> bool:
	if not barrier.is_empty():
		if reported:
			if FileAccess.file_exists(barrier.path_join("stop")):
				game.queue_free()
				quit(0 if passed else 1)
			return false
		if not measuring:
			if game == null: return false
			if not barrier_ready and (role == "server" or (game.connection_state == "connected" and game.accepted_snapshots > 0)):
				barrier_ready = true
				var ready := FileAccess.open(output + ".ready", FileAccess.WRITE)
				ready.store_string("ready")
				ready.close()
			if start_epoch == 0 and FileAccess.file_exists(barrier.path_join("start.json")):
				start_epoch = float(JSON.parse_string(FileAccess.get_file_as_string(barrier.path_join("start.json"))).epoch)
				# Map one shared wall epoch to the local monotonic clock once.
				started_msec = Time.get_ticks_msec() + int((start_epoch-Time.get_unix_time_from_system())*1000)
			if start_epoch == 0 or Time.get_ticks_msec() < started_msec: return false
			measuring = true
			if role == "server" and account_mode:
				initial_accounts = game._account_ids.duplicate()
				game.phase = "live"
				game.time_left = 1000
				game._bot_clock = 1000
			start_offset_seconds = (Time.get_ticks_msec()-started_msec)/1000.0
			previous_frame_usec = 0
			game.measuring = true
			game.records.clear()
			game.ticks.clear()
			game.tick_intervals.clear()
			game._last_tick_start = 0
			game.accepted_tick_steps.clear()
			game.accepted_snapshots = 0
			game.received_snapshots = 0
			game.received_payload_bytes = 0
			game.snapshot_steps.clear()
			game._prediction.error_samples.clear()
			game._prediction.corrections = 0
			game._prediction.hard_corrections = 0
			game._prediction.large_corrections.clear()
	elapsed += delta
	wall_elapsed = (Time.get_ticks_msec()-started_msec)/1000.0
	var frame_usec := Time.get_ticks_usec()
	if DisplayServer.get_name() != "headless" and previous_frame_usec > 0: render_frames.append((frame_usec-previous_frame_usec)/1000.0)
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
			if reconnect_passed and recovered_at < 0: recovered_at = wall_elapsed
		elif reconnect_at >= 0 and wall_elapsed >= reconnect_at:
			reconnect_started = true
			game.multiplayer.multiplayer_peer.close()
			game._server_disconnected()
			# Default exercises the real two-second client path; shorter stress delays
			# remain explicit so early reconnect failures cannot be hidden by retiming.
			game._reconnect_clock = reconnect_delay
	if wall_elapsed >= duration:
		# Latch freshness at the measurement boundary, before serializing evidence.
		var sample_msec := Time.get_ticks_msec()
		render_frames.sort()
		var render_metrics := {"native": DisplayServer.get_name() != "headless", "renderer":RenderingServer.get_video_adapter_name(), "samples":render_frames.size(), "draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), "primitives":Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME), "texture_bytes":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED)}
		if not render_frames.is_empty():
			render_metrics["wall_frame_interval_p50_ms"] = render_frames[render_frames.size()/2]
			render_metrics["wall_frame_interval_p95_ms"] = render_frames[mini(render_frames.size()-1, int(render_frames.size()*0.95))]
		var report := {"measurement_stop_lateness_seconds":maxf(0,wall_elapsed-duration),"measurement_start_epoch":start_epoch,"measurement_start_offset_seconds":start_offset_seconds,"startup_seconds":(started_msec-startup_started_msec)/1000.0,"initial_accounts":initial_accounts,"final_accounts":game._account_ids,"account_count":game._account_ids.size(),"account_ids":game._account_ids.values(),"ranked_started":game._ranked_started,"ranked_eligible":game._ranked_eligible,"reward_status":game.reward_status,"lifecycle_events":game.lifecycle_events,"occupancy":game.occupancy,"role": role, "joined": joined, "state": game.connection_state, "notifications":notices, "elapsed_seconds": elapsed, "wall_elapsed_seconds":wall_elapsed, "max_displacement": max_distance, "render_metrics":render_metrics,
			"first_movement_seconds": first_movement_seconds, "prediction_enabled": prediction_enabled, "prediction_errors_m": game._prediction.error_samples,
			"corrections": game._prediction.corrections, "hard_corrections": game._prediction.hard_corrections,
			"recovered_at_seconds":recovered_at,"recovery_seconds":recovered_at-reconnect_at if recovered_at >= 0 else -1,"reconnect_requested":reconnect_at >= 0,"reconnect_delay_seconds":reconnect_delay,"reconnect_passed":reconnect_passed,"initial_id":initial_id,"final_id":game.local_id,
			"pending_inputs": game._prediction.pending.size(), "large_corrections": game._prediction.large_corrections,
			"last_snapshot_age_seconds": (sample_msec - game.last_snapshot_msec) / 1000.0, "snapshots": game.received_snapshots, "snapshot_tick_gaps": game.snapshot_steps, "reencoded_snapshot_bytes": game.received_payload_bytes,
			"accepted_snapshots":game.accepted_snapshots,"last_accepted_age_seconds":(sample_msec-game.last_accepted_msec)/1000.0,"last_accepted_tick":game._replica_buffer.last_tick,"accepted_tick_gaps":game.accepted_tick_steps,
			"skipped_commands": game._input_stream.skipped_commands, "tick_usec": game.ticks, "tick_intervals_usec": game.tick_intervals, "poses": game.records, "stale_snapshots": game._replica_buffer.stale_packets}
		if not output.is_empty():
			var file := FileAccess.open(output + ".tmp", FileAccess.WRITE)
			file.store_string(JSON.stringify(report))
			file.close()
			DirAccess.rename_absolute(output + ".tmp", output)
		print("NETWORK_SIMULATION " + JSON.stringify({"role": role, "joined": joined, "last_snapshot_age_seconds": (sample_msec - game.last_snapshot_msec) / 1000.0, "snapshots": game.received_snapshots, "max_displacement": max_distance}))
		var success := role == "server" or (joined and game.connection_state == "connected" and sample_msec - game.last_snapshot_msec < 750 and game.received_snapshots >= 10 and max_distance > 0.1)
		if role != "server" and reconnect_at >= 0: success = success and reconnect_passed
		if role != "server": success = success and game.accepted_snapshots >= 10 and sample_msec-game.last_accepted_msec < 750
		if barrier.is_empty():
			game.queue_free()
			quit(0 if success else 1)
		else:
			passed = success
			reported = true
			game.measuring = false
	return false
