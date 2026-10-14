extends SceneTree
## Suppress exactly one server hello at the application callback boundary.
## Native ENet, separate multiplayer roots, one process; no cellular claim.
class DropFirstHelloMatch extends TacticalMatch:
	var discarded_hellos := 0
	func _client_handshake(peer: int, data: PackedByteArray) -> void:
		if discarded_hellos == 0:
			discarded_hellos += 1
			return
		super._client_handshake(peer, data)
	func _handshake_failed(peer: int) -> void:
		if OS.get_cmdline_user_args().has("--negative-control"):
			_fail_connection("Negative control: old terminal auth-failure behavior")
		else:
			super._handshake_failed(peer)
var server: TacticalMatch
var port := 33542
func _initialize() -> void: call_deferred("run")
func setup(label: String, settings: Dictionary, drop_hello := false) -> TacticalMatch:
	var branch := Node.new()
	branch.name = label
	root.add_child(branch)
	set_multiplayer(SceneMultiplayer.new(), branch.get_path())
	var game: TacticalMatch = DropFirstHelloMatch.new() if drop_hello else TacticalMatch.new()
	game.configure(settings)
	branch.add_child(game)
	return game
func wait_until(test: Callable, seconds := 4.0) -> bool:
	var limit := Time.get_ticks_msec() + int(seconds * 1000)
	while not test.call() and Time.get_ticks_msec() < limit: await process_frame
	return test.call()
func dispose(game: TacticalMatch) -> void:
	var branch := game.get_parent()
	game.queue_free()
	await process_frame
	await process_frame
	set_multiplayer(null, branch.get_path())
	branch.queue_free()
	await process_frame
func run() -> void:
	server = setup("Server", {"mode": "server", "port": port})
	server.phase = "waiting"
	server._bot_clock = 1000
	var original := setup("Original", {"mode": "client", "port": port})
	var initial := await wait_until(func(): return original.connection_state == "connected")
	var credential := original.reconnect_token
	var actor := original.local_id
	await dispose(original)
	var retired := await wait_until(func(): return server._peer_actors.is_empty())
	var start := Time.get_ticks_msec()
	var resumed := setup("Resumed", {"mode": "client", "port": port, "reconnect_token": credential}, true) as DropFirstHelloMatch
	resumed._recovery.begin(start)
	var deadline := resumed._recovery.deadline
	var notices: Array[String] = []
	resumed.notification.connect(func(message: String): notices.append(message))
	await wait_until(func(): return resumed.connection_state in ["failed", "connected"], 12.0)
	var success := initial and retired and resumed.discarded_hellos == 1 and resumed.connection_state == "connected" and resumed.local_id == actor and resumed._replica_buffer.last_tick >= 0
	print("AUTH_LOSS_REVIEW " + JSON.stringify({"fixture_valid": initial and retired, "suppressed_server_hellos": resumed.discarded_hellos, "recovered_same_actor": resumed.local_id == actor, "fresh_accepted_tick": resumed._replica_buffer.last_tick, "state": resumed.connection_state, "elapsed_msec": Time.get_ticks_msec() - start, "original_deadline_msec": deadline, "notifications": notices, "passed": success, "scope": "one native process; ENet; one application hello reply suppressed"}))
	await dispose(resumed)
	await dispose(server)
	await process_frame
	quit(0 if success else 1)
