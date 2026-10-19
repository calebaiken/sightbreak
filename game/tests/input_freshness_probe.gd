extends SceneTree
## Real ENet and authority physics. Snapshot loss is injected at the client
## application boundary; transport ACKs remain live. No runtime RPC is replaced.
class FreshnessMatch extends TacticalMatch:
	var scenario := "snapshot-gap"
	var start_msec := -1
	var rows: Array[Dictionary] = []
	var dropped_snapshots := 0
	var accepted_snapshots := 0
	var privacy_violations := 0
	var replay_packet := PackedByteArray()
	var replay_clock := 0.0
	var observed_peer := 0
	var disconnected_at := -1.0
	var shots := 0
	var max_pending := 0
	func seconds() -> float:
		return -1.0 if start_msec < 0 else (Time.get_ticks_msec() - start_msec) / 1000.0
	func _ready() -> void:
		super._ready()
		# Identical collision-only platform above Relay Yard isolates travel from
		# map contacts. The actual actor, weapons, authority and privacy code run.
		var floor_body := StaticBody3D.new()
		var shape := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = Vector3(100, 1, 100)
		shape.shape = box
		floor_body.add_child(shape)
		add_child(floor_body)
		floor_body.position = Vector3(0, 99.5, 0)
		if _authority:
			_bot_clock = 10000
			phase = "live"
			time_left = 10000
			for actor: SBActor in actors.values():
				actor.reset_loadout()
				actor.reset_for_round(Vector3(0, 100.05, 0) if actor.actor_id == 1 else Vector3(20 + actor.actor_id * 2, 100.05, 15))
				actor.input_state = {"move": Vector2.ZERO, "look": Vector2.ZERO}
			actors[1].shot_fired.connect(func(_id, _at, _direction): shots += 1)
	func _apply_snapshot(data: Dictionary) -> void:
		# Check even discarded packets: impairment must not conceal a disclosure.
		for state: Dictionary in data.actors:
			if state.id == local_id:
				continue
			for field: String in SBStatePrivacy.OWN + ["move_ack", "grounded", "jump_held"]:
				if state.has(field): privacy_violations += 1
			if int(state.team) != int(data.actors[local_id - 1].team):
				for field: String in SBStatePrivacy.TEAM:
					if state.has(field): privacy_violations += 1
		var t := seconds()
		if scenario == "snapshot-gap" and t >= 1.0 and t < 5.0:
			dropped_snapshots += 1
			return
		accepted_snapshots += 1
		super._apply_snapshot(data)
	func _client_tick(delta: float) -> void:
		var t := seconds()
		if scenario == "stale-replay" and t >= 2.0:
			# Hostile control: resend the same immutable batch, then ignore the
			# disconnect. This tests the real 30-second server idle cleanup.
			replay_clock -= delta
			if connection_state == "connected" and replay_clock <= 0:
				replay_clock = 1.0 / 30.0
				_input_rpc.rpc_id(1, replay_packet)
			return
		if scenario == "input-gap" and t >= 1.0 and t < 1.2:
			return
		var move := Vector2.ZERO
		if t >= 0 and t < 3.5: move = Vector2(0.2, 0)
		elif t >= 6.0: move = Vector2(-0.2, 0)
		# One held semi-auto press spanning the outage, then a genuine release
		# and press. Neither silence nor resumption may invent another edge.
		set_local_input({"move": move, "look": Vector2.ZERO, "fire": t >= 0 and not (t >= 6.2 and t < 6.4)})
		super._client_tick(delta)
		if scenario == "stale-replay":
			replay_packet = var_to_bytes(_prediction.packet()).compress(FileAccess.COMPRESSION_DEFLATE)
	func _physics_process(delta: float) -> void:
		super._physics_process(delta)
		var t := seconds()
		if t < 0: return
		if _authority:
			if not _peer_actors.is_empty(): observed_peer = int(_peer_actors.keys()[0])
			elif observed_peer != 0 and disconnected_at < 0: disconnected_at = t
			var actor: SBActor = actors[1]
			rows.append({"t": t, "simulation_t": _elapsed, "ack": int(_last_input_sequence.get(1, 0)), "last_input": float(_last_peer_input.get(1, -1)), "peer_last_input_msec": int(_peer_lifecycle.peers.get(observed_peer, {}).get("last_input", -1)), "peer_count": _peer_actors.size(), "x": actor.position.x, "vx": actor.velocity.x, "move_x": (actor.input_state.get("move", Vector2.ZERO) as Vector2).x, "fire_held": actor._fire_previous, "shots": shots, "ammo": actor.ammo, "rejected": _input_stream.rejected})
		else:
			max_pending = maxi(max_pending, _prediction.pending.size())
			rows.append({"t": t, "state": connection_state, "sequence": _prediction.sequence, "pending": _prediction.pending.size(), "accepted_snapshots": accepted_snapshots, "dropped_snapshots": dropped_snapshots, "x": local_actor().position.x if local_actor() != null else 0.0})

var game: FreshnessMatch
var role := "client"
var scenario := "snapshot-gap"
var output := ""
var barrier := ""
var port := 29680
var duration := 8.0
var prediction := false
var ready_written := false
var reported := false
var barrier_read_retries := 0

func _initialize() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--role="): role = arg.trim_prefix("--role=")
		elif arg.begins_with("--scenario="): scenario = arg.trim_prefix("--scenario=")
		elif arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg.begins_with("--barrier="): barrier = arg.trim_prefix("--barrier=")
		elif arg.begins_with("--port="): port = int(arg.trim_prefix("--port="))
		elif arg.begins_with("--seconds="): duration = float(arg.trim_prefix("--seconds="))
		elif arg == "--prediction": prediction = true
	call_deferred("run")

func run() -> void:
	game = FreshnessMatch.new()
	game.scenario = scenario
	var settings := {"mode": role, "port": port, "address": "127.0.0.1", "name": "Freshness probe"}
	if prediction: settings.prediction = true # Otherwise exercise the actual default.
	game.configure(settings)
	root.add_child(game)

func _process(_delta: float) -> bool:
	if game == null or reported: return false
	if not ready_written and (role == "server" or game.connection_state == "connected"):
		var ready := FileAccess.open(output + ".ready", FileAccess.WRITE)
		ready.store_string("ready")
		ready.close()
		ready_written = true
	if game.start_msec < 0 and FileAccess.file_exists(barrier.path_join("start.json")):
		# A Windows preflight observed a transient unreadable/empty start file
		# despite atomic publication. Stay outside measurement until valid data is
		# available; the Python watchdog still bounds a permanently bad barrier.
		var parsed := JSON.new()
		var error := parsed.parse(FileAccess.get_file_as_string(barrier.path_join("start.json")))
		var epoch_value: Variant = parsed.data.get("epoch") if error == OK and parsed.data is Dictionary else null
		if not (epoch_value is float or epoch_value is int) or not is_finite(float(epoch_value)) or float(epoch_value) <= 0:
			barrier_read_retries += 1
			if barrier_read_retries == 1: print("INPUT_FRESHNESS_BARRIER_RETRY role=" + role)
			return false
		var epoch := float(epoch_value)
		game.start_msec = Time.get_ticks_msec() + int((epoch - Time.get_unix_time_from_system()) * 1000)
	if game.seconds() >= duration:
		reported = true
		var report := {"role": role, "scenario": scenario, "barrier_read_retries": barrier_read_retries, "protocol": TacticalMatch.PROTOCOL_VERSION, "prediction": game._prediction_enabled, "hit_history_frames": game._hit_history.frames.size(), "rows": game.rows, "dropped_snapshots": game.dropped_snapshots, "accepted_snapshots": game.accepted_snapshots, "privacy_violations": game.privacy_violations, "max_pending": game.max_pending, "disconnected_at": game.disconnected_at, "shots": game.shots, "final_peer_count": game._peer_actors.size(), "lifecycle_entries": game._peer_lifecycle.peers.size(), "input_queues": game._input_stream.queues.size(), "pending_joins": game._pending_joins.size()}
		var file := FileAccess.open(output + ".tmp", FileAccess.WRITE)
		file.store_string(JSON.stringify(report))
		file.close()
		DirAccess.rename_absolute(output + ".tmp", output)
		finish.call_deferred()
	return false

func finish() -> void:
	while not FileAccess.file_exists(barrier.path_join("stop")):
		await create_timer(0.05).timeout
	game.queue_free()
	await process_frame
	await create_timer(0.7).timeout
	print("INPUT_FRESHNESS_PROBE role=%s scenario=%s completed" % [role, scenario])
	quit()
