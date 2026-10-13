extends SceneTree
## Synthetic repeated lifecycle transitions, not earned/ranked match evidence.
var game: TacticalMatch
var role := "client"
var port := 29830
var elapsed := 0.0
var next_reconnect := 6.0
var reconnects := 0
var first_id := 0
var pending := false
var max_peers := 0
var max_temp := 0
var reset_count := 0
var memory: Array = []
var output := ""
var failures := 0
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg == "--server": role = "server"
		if arg.begins_with("--port="): port = int(arg.get_slice("=", 1))
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
	_start.call_deferred()
func _start() -> void:
	game = TacticalMatch.new()
	game.configure({"mode": role, "port": port, "address": "127.0.0.1", "name": "Soak fixture"})
	root.add_child(game)
	if role == "server":
		game.phase = "live"
		game.time_left = 1000
		game._bot_clock = 1000
func _process(delta: float) -> bool:
	elapsed += delta
	if game == null: return false
	if role == "server":
		max_peers = maxi(max_peers, game._peer_actors.size())
		max_temp = maxi(max_temp, game._pending_joins.size() + game._join_slots.size() + game._join_accounts.size())
		if int(elapsed / 10) > reset_count and reset_count < 6:
			reset_count += 1
			game._end_round(reset_count % 2, "Synthetic soak transition")
			game._begin_round()
			game.phase = "live"
			game.time_left = 1000
			game._bot_clock = 1000
			memory.append(Performance.get_monitor(Performance.MEMORY_STATIC))
	elif game.connection_state == "connected":
		if first_id == 0: first_id = game.local_id
		if game.local_id != first_id: failures += 1
		if pending:
			reconnects += 1
			pending = false
		game.set_local_input({"move": Vector2(1, 0), "look": Vector2(PI, 0)})
		if elapsed >= next_reconnect and reconnects < 8:
			next_reconnect += 6
			pending = true
			game.multiplayer.multiplayer_peer.close()
			game.connection_state = "reconnecting"
			game._reconnect_clock = 0.3
	if elapsed >= (64.0 if role == "server" else 56.0):
		var ok := failures == 0 and (max_peers == 2 and game._peer_actors.is_empty() and game._pending_joins.is_empty() and game._join_slots.is_empty() and game._join_accounts.is_empty() and game._handshake_seen.is_empty() if role == "server" else reconnects == 8 and game.connection_state == "connected")
		var report := {"role": role, "passed": ok, "reconnects": reconnects, "same_actor_id": failures == 0, "max_peers": max_peers, "max_temporary_claims": max_temp, "resets": reset_count, "static_memory_samples": memory, "reservations_after": game._reservations.size(), "scope": "short synthetic lifecycle exercise; forced round transitions, no rewards"}
		var file := FileAccess.open(output, FileAccess.WRITE)
		file.store_string(JSON.stringify(report))
		file.close()
		print("NETWORK_SOAK " + JSON.stringify(report))
		game.queue_free()
		quit(0 if ok else 1)
	return false
