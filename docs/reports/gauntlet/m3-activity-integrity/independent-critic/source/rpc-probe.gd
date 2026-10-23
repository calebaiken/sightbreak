extends SceneTree
## Real ENet endpoint probe. No activity, account, score or reward state is set.
class ActivityMatch extends TacticalMatch:
	var scenario := "stale-tail"
	var start_msec := -1
	var sequence := 0
	var send_clock := 0.0
	var rows: Array[Dictionary] = []
	var packets := 0
	var snapshots := 0
	func seconds() -> float:
		return -1.0 if start_msec < 0 else (Time.get_ticks_msec() - start_msec) / 1000.0
	func _ready() -> void:
		super._ready()
		if not _authority: return
		# Fixture geometry/phase isolates the actual RPC and authority from combat.
		_bot_clock = 10000
		phase = "live"
		time_left = 10000
		var floor_body := StaticBody3D.new()
		var shape := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = Vector3(100, 1, 100)
		shape.shape = box
		floor_body.add_child(shape)
		add_child(floor_body)
		floor_body.position = Vector3(0, 99.5, 0)
		for actor: SBActor in actors.values():
			actor.reset_for_round(Vector3(0, 100.05, 0) if actor.actor_id == 1 else Vector3(20 + actor.actor_id * 2, 100.05, 15))
			actor.input_state = {"move": Vector2.ZERO, "look": Vector2.ZERO}
	func _apply_snapshot(data: Dictionary) -> void:
		snapshots += 1
		super._apply_snapshot(data)
	func _client_tick(delta: float) -> void:
		if connection_state != "connected":
			super._client_tick(delta)
			return
		send_clock -= delta
		if send_clock > 0: return
		send_clock = 1.0 / 30.0
		sequence += 1
		var t := seconds()
		var yaw := 0.08 if scenario == "real-look" and int(maxf(0, t) * 4) % 2 == 0 else 0.0
		var commands: Array = [{"sequence": sequence, "move": Vector2.ZERO, "look": Vector2(yaw, 0)}]
		if t >= 0.5 and scenario == "stale-tail":
			commands.append({"sequence": 1, "move": Vector2.ZERO, "look": Vector2(0.08, 0)})
		_input_rpc.rpc_id(1, var_to_bytes({"epoch": _replica_buffer.epoch, "commands": commands}).compress(FileAccess.COMPRESSION_DEFLATE))
		packets += 1
	func _physics_process(delta: float) -> void:
		super._physics_process(delta)
		if not _authority or seconds() < 0: return
		var actor: SBActor = actors[1]
		rows.append({"t": seconds(), "elapsed": _elapsed, "last_activity": float(_last_activity.get(1, -100)),
			"ack": int(_last_input_sequence.get(1, 0)), "x": actor.position.x, "z": actor.position.z,
			"yaw": actor.yaw, "pitch": actor.pitch, "ammo": actor.ammo,
			"interaction_count": _interactions.size(), "peers": _peer_actors.size(), "rejected": _input_stream.rejected})

var game: ActivityMatch
var role := "client"
var scenario := "stale-tail"
var output := ""
var barrier := ""
var port := 29949
var ready_written := false
var reported := false

func _initialize() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--role="): role = arg.trim_prefix("--role=")
		elif arg.begins_with("--scenario="): scenario = arg.trim_prefix("--scenario=")
		elif arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg.begins_with("--barrier="): barrier = arg.trim_prefix("--barrier=")
		elif arg.begins_with("--port="): port = int(arg.trim_prefix("--port="))
	call_deferred("start")

func start() -> void:
	game = ActivityMatch.new()
	game.scenario = scenario
	game.configure({"mode": role, "port": port, "address": "127.0.0.1", "name": "Activity provenance probe"})
	root.add_child(game)

func _process(_delta: float) -> bool:
	if game == null or reported: return false
	if not ready_written and (role == "server" or game.connection_state == "connected"):
		var ready := FileAccess.open(output + ".ready", FileAccess.WRITE)
		ready.store_string("ready")
		ready.close()
		ready_written = true
	if game.start_msec < 0 and FileAccess.file_exists(barrier.path_join("start.json")):
		var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(barrier.path_join("start.json")))
		if data is Dictionary and data.get("epoch") is float:
			game.start_msec = Time.get_ticks_msec() + int((float(data.epoch) - Time.get_unix_time_from_system()) * 1000)
	if game.seconds() >= 4:
		reported = true
		var report := {"role": role, "scenario": scenario, "protocol": game.PROTOCOL_VERSION,
			"prediction": game._prediction_enabled, "hit_history_frames": game._hit_history.frames.size(),
			"ranked_started": game._ranked_started, "packets": game.packets, "snapshots": game.snapshots, "rows": game.rows}
		var file := FileAccess.open(output + ".tmp", FileAccess.WRITE)
		file.store_string(JSON.stringify(report))
		file.close()
		DirAccess.rename_absolute(output + ".tmp", output)
		finish.call_deferred()
	return false

func finish() -> void:
	while not FileAccess.file_exists(barrier.path_join("stop")):
		await create_timer(0.02).timeout
	game.queue_free()
	await process_frame
	await create_timer(0.7).timeout
	quit()
