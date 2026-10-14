extends SceneTree
## Deterministically suppresses welcome processing after authoritative admission.
## This is an application-delivery fault injection, not a packet-loss measurement.
class DropWelcomeMatch extends TacticalMatch:
	var discarded := false
	@rpc("authority", "call_remote", "reliable")
	func _welcome_rpc(_id: int, _token: String, _data: Dictionary) -> void:
		discarded = true
		connection_state = "failed"
		multiplayer.multiplayer_peer.close()
var server: TacticalMatch
var port := 33541
func _initialize() -> void:
	call_deferred("run")
func setup(label: String, settings: Dictionary, drop_welcome := false) -> TacticalMatch:
	var branch := Node.new()
	branch.name = label
	root.add_child(branch)
	set_multiplayer(SceneMultiplayer.new(), branch.get_path())
	var game: TacticalMatch = DropWelcomeMatch.new() if drop_welcome else TacticalMatch.new()
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
	var initially_joined := await wait_until(func(): return original.connection_state == "connected")
	var credential := original.reconnect_token
	var actor := original.local_id
	await dispose(original)
	var retired := await wait_until(func(): return server._peer_actors.is_empty())
	var resumed := setup("LostWelcome", {"mode": "client", "port": port, "reconnect_token": credential}, true) as DropWelcomeMatch
	var welcome_lost := await wait_until(func(): return resumed.discarded)
	await dispose(resumed)
	var second_retired := await wait_until(func(): return server._peer_actors.is_empty())
	var final_client := setup("RetryOldCredential", {"mode": "client", "port": port, "reconnect_token": credential})
	await wait_until(func(): return final_client.connection_state in ["failed", "connected"])
	var recovered := final_client.connection_state == "connected" and final_client.local_id == actor
	var fixture_valid := initially_joined and retired and welcome_lost and second_retired
	print("LOST_WELCOME_REVIEW " + JSON.stringify({"fixture_valid": fixture_valid, "welcome_suppressed_after_authority_commit": welcome_lost, "old_credential_retained_by_client": credential.length() == 64, "old_credential_still_valid": server._reservations.has(credential), "restored_same_actor": recovered, "final_state": final_client.connection_state, "scope": "one native process; ENet; deterministic application delivery suppression"}))
	await dispose(final_client)
	await dispose(server)
	await process_frame
	quit(0 if fixture_valid and recovered else 1)
