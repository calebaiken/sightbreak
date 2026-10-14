extends SceneTree
## Independent reviewer probes. No HTTP service or synthetic authority claims.
class ReviewMatch extends TacticalMatch:
	var rejected: Array[String] = []
	func _ready() -> void:
		set_process(false)
		set_physics_process(false)
	func _reject_join(_peer: int, reason: String) -> void:
		rejected.append(reason)

class SpyBridge extends SBEconomyBridge:
	var inspected := 0
	var consumed := 0
	func inspect_ticket(_ticket: String) -> Dictionary:
		inspected += 1
		return {"ok": true, "data": {"player_id": "review-account", "display_name": "Review"}}
	func consume_ticket(_ticket: String) -> Dictionary:
		consumed += 1
		return {"ok": true, "data": {"player_id": "review-account"}}

var checks := 0
var failures := 0
var notices: Array[String] = []
func check(ok: bool, label: String) -> void:
	checks += 1
	print("REVIEW_CHECK %s %s" % ["PASS" if ok else "FAIL", label])
	if not ok: failures += 1
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	var policy := SBReconnectPolicy.new()
	policy.begin(1000)
	var deadline := policy.deadline
	for time in [1000, 3000, 10000, 20000, 30000]:
		policy.begin(time)
	check(policy.deadline == deadline, "repeated callbacks cannot renew recovery deadline")
	check(policy.available(deadline - 1) and not policy.available(deadline), "recovery deadline boundary is strict")
	for count in range(SBReconnectPolicy.MAX_ATTEMPTS):
		check(policy.take_attempt(1000 + count), "permitted attempt %d" % count)
	check(not policy.take_attempt(1006) and policy.attempts == SBReconnectPolicy.MAX_ATTEMPTS, "extra attempts remain bounded")
	policy.clear()
	check(policy.deadline == 0 and policy.attempts == 0, "successful or terminal episode can clear policy")
	var game := ReviewMatch.new()
	root.add_child(game)
	game.notification.connect(func(message: String): notices.append(message))
	game.options = {"mode": "server", "require_accounts": true}
	game.phase = "live"
	game._authority = true
	var bridge := SpyBridge.new()
	game.add_child(bridge)
	game._bridge = bridge
	var dummy_actor := SBActor.new()
	game.actors[1] = dummy_actor
	for token in ["x", "f".repeat(64), "expired".repeat(9) + "x"]:
		game._peer_lifecycle.forget(0)
		game._peer_lifecycle.connected(0, Time.get_ticks_msec())
		game.rejected.clear()
		if token.begins_with("expired"):
			game._reservations[token] = {"id": 1, "expires": -1.0}
		await game._join_rpc("Review", token, "unconsumed-ticket".repeat(3))
		check(game.rejected.size() == 1 and "invalid or expired" in game.rejected[0], "invalid or expired resume token rejected before guest fallback")
		check(bridge.inspected == 0 and bridge.consumed == 0 and game._peer_actors.is_empty(), "invalid resume cannot inspect/consume account ticket or gain authority")
	game._peer_lifecycle.forget(0)
	game._peer_lifecycle.connected(0, Time.get_ticks_msec())
	await game._join_rpc("Review", "", "unconsumed-ticket".repeat(3))
	check(bridge.inspected == 1 and bridge.consumed == 0, "positive control: ordinary fresh account join reaches inspection")
	game.actors.clear()
	dummy_actor.free()
	game._authority = false
	game.connection_state = "joining"
	game.reconnect_token = "a".repeat(64)
	game._recovery.begin(Time.get_ticks_msec() - SBReconnectPolicy.WINDOW_MSEC - 1)
	notices.clear()
	game._rejected_rpc("Account ticket rejected: terminal review reason")
	check(game._recovery.deadline == 0, "terminal admission cancels retry timer before another frame")
	game._client_tick(0.0)
	check(game.connection_state == "failed" and game._recovery.deadline == 0, "terminal admission cancels recovery episode")
	check(notices.size() == 1 and notices[0] == "Account ticket rejected: terminal review reason", "expired recovery cannot overwrite terminal rejection reason")
	game.connection_state = "authenticating"
	game._recovery.begin(Time.get_ticks_msec())
	game._client_handshake(1, JSON.stringify({"game": "sightbreak", "protocol": 999, "accepted": false, "reason": "review mismatch"}).to_utf8_buffer())
	var terminal_notices := notices.size()
	game._server_disconnected()
	game._connection_failed()
	check(game.connection_state == "failed" and game._recovery.deadline == 0 and notices.size() == terminal_notices, "explicit incompatible version stays terminal after delayed callbacks")
	game.connection_state = "connected"
	game._server_disconnected()
	deadline = game._recovery.deadline
	game._server_disconnected()
	check(game.connection_state == "reconnecting" and game._recovery.deadline == deadline and game._recovery.attempts == 0, "duplicate disconnect callbacks do not consume or renew recovery")
	game.connection_state = "connected"
	game.reconnect_token = ""
	game._recovery.clear()
	check(not game._retry_resume("review"), "unadmitted client without resume credential cannot start recovery")
	var old_peer := ENetMultiplayerPeer.new()
	var new_peer := ENetMultiplayerPeer.new()
	check(old_peer.create_client("127.0.0.1", 33599) == OK and new_peer.create_client("127.0.0.1", 33598) == OK, "native transport setup for stale-close test")
	game.multiplayer.multiplayer_peer = new_peer
	game._close_retired_client(old_peer)
	check(new_peer.get_connection_status() == MultiplayerPeer.CONNECTION_CONNECTING, "stale deferred close cannot terminate replacement transport")
	old_peer.close()
	new_peer.close()
	game.multiplayer.multiplayer_peer = OfflineMultiplayerPeer.new()
	game.queue_free()
	await process_frame
	await process_frame
	print("INDEPENDENT_RECONNECT_REVIEW checks=%d failures=%d" % [checks, failures])
	quit(0 if failures == 0 else 1)
