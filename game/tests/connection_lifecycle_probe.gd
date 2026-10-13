extends SceneTree
## Adversarial native clients ignore local timeouts and rejected-connection closure.
class QuietMatch extends TacticalMatch:
	var scenario := "silent"
	func _connected() -> void:
		if scenario == "silent":
			connection_state = "joining"
		else:
			super._connected()
	func _client_tick(_delta: float) -> void:
		pass
	@rpc("authority", "call_remote", "reliable")
	func _rejected_rpc(_message: String) -> void:
		connection_state = "hostile_ignored_rejection"
var game: TacticalMatch
var role := "client"
var scenario := "silent"
var port := 29900
var started := 0
var admitted := false
func _initialize() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--role="): role = arg.get_slice("=", 1)
		elif arg.begins_with("--scenario="): scenario = arg.get_slice("=", 1)
		elif arg.begins_with("--port="): port = int(arg.get_slice("=", 1))
	call_deferred("run")
func run() -> void:
	started = Time.get_ticks_msec()
	if role == "server":
		game = TacticalMatch.new()
	else:
		game = QuietMatch.new()
		game.scenario = scenario
	game.configure({"mode": role, "port": port, "address": "127.0.0.1"})
	root.add_child(game)
	if role == "server":
		game.phase = "live"
		game.time_left = 1000
		game._bot_clock = 1000
		if scenario == "reject":
			game.phase = "match_over"
func _process(_delta: float) -> bool:
	if game == null: return false
	var elapsed := (Time.get_ticks_msec() - started) / 1000.0
	if role == "client":
		admitted = admitted or game.connection_state == "connected"
		if game.connection_state == "reconnecting":
			var minimum := 19.5 if scenario == "silent" else (29.5 if scenario == "idle" else 0.4)
			var maximum := 22.0 if scenario == "silent" else (32.0 if scenario == "idle" else 3.0)
			var ok := elapsed >= minimum and elapsed <= maximum and (admitted == (scenario == "idle"))
			print("CONNECTION_LIFECYCLE " + JSON.stringify({"scenario": scenario, "admitted": admitted, "drop_seconds": elapsed, "ok": ok}))
			game.queue_free()
			quit(0 if ok else 1)
		elif elapsed > 34:
			push_error("Server failed to disconnect " + scenario)
			quit(1)
	elif elapsed > 36:
		var clean := game._peer_actors.is_empty() and game._peer_lifecycle.peers.is_empty() and game._pending_joins.is_empty() and game._join_slots.is_empty() and game._input_stream.queues.is_empty() and game._handshake_seen.is_empty()
		print("CONNECTION_LIFECYCLE_CLEAN " + JSON.stringify({"ok": clean, "peer_entries": game._peer_lifecycle.peers.size()}))
		game.queue_free()
		quit(0 if clean else 1)
	return false
