extends SceneTree
var match_node: TacticalMatch
var elapsed: float = 0
var role: String = "client"
var finished: bool = false

func _initialize() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--role="):
			role = arg.trim_prefix("--role=")
	call_deferred("_start")

func _start() -> void:
	if role == "mismatch":
		_start_mismatch()
		return
	match_node = TacticalMatch.new()
	match_node.configure({"mode": "server" if role == "server" else "client", "port": 27992, "address": "127.0.0.1", "name": "Client forged label", "require_accounts": role == "server", "economy_url": OS.get_environment("SIGHTBREAK_TEST_ECONOMY_URL") if OS.has_environment("SIGHTBREAK_TEST_ECONOMY_URL") else "http://127.0.0.1:8080", "server_id": "local-relay", "join_ticket": OS.get_environment("SIGHTBREAK_JOIN_TICKET") if role != "guest" else ""})
	root.add_child(match_node)

## An incompatible build's client: completes only the version handshake (protocol 99),
## so it can never reach _join_rpc. The next role reuses the same join ticket and must
## still be admitted to slot 1: the rejected attempt consumed neither ticket nor slot.
var mismatch_reply: Dictionary = {}
func _start_mismatch() -> void:
	var api := get_multiplayer() as SceneMultiplayer
	api.auth_timeout = 5.0
	api.auth_callback = _mismatch_reply
	api.peer_authenticating.connect(_mismatch_hello)
	var peer := ENetMultiplayerPeer.new()
	peer.create_client("127.0.0.1", 27992)
	api.multiplayer_peer = peer

func _mismatch_reply(_peer: int, data: PackedByteArray) -> void:
	var parsed: Variant = JSON.parse_string(data.get_string_from_utf8())
	mismatch_reply = parsed if parsed is Dictionary else {"unreadable": true}

func _mismatch_hello(peer: int) -> void:
	(get_multiplayer() as SceneMultiplayer).send_auth(peer, JSON.stringify({"game": "sightbreak", "protocol": 99, "accepted": true, "reason": ""}).to_utf8_buffer())

func _finish_mismatch(okay: bool) -> void:
	var api := get_multiplayer() as SceneMultiplayer
	api.peer_authenticating.disconnect(_mismatch_hello)
	api.auth_callback = Callable()
	api.multiplayer_peer = OfflineMultiplayerPeer.new()
	await process_frame
	await process_frame
	quit(0 if okay else 1)

func _process_mismatch() -> void:
	var peer := get_multiplayer().multiplayer_peer as ENetMultiplayerPeer
	var closed := peer == null or peer.get_connection_status() == MultiplayerPeer.CONNECTION_DISCONNECTED
	if not mismatch_reply.is_empty() and closed:
		var okay: bool = mismatch_reply.get("accepted") == false and "protocol 99" in str(mismatch_reply.get("reason", "")) and elapsed < 4.0
		print(("ACCOUNT_NETWORK_MISMATCH_PASS" if okay else "ACCOUNT_NETWORK_MISMATCH_FAIL") + " reply=%s closed_after=%.2f" % [JSON.stringify(mismatch_reply), elapsed])
		finished = true
		_finish_mismatch.call_deferred(okay)

func _process(delta: float) -> bool:
	elapsed += delta
	if role == "mismatch" and not finished:
		_process_mismatch()
		if elapsed > 8 and not finished:
			push_error("Account probe timeout: mismatch reply=%s" % JSON.stringify(mismatch_reply))
			quit(1)
		return false
	if match_node == null or finished:
		return false
	if role == "client" and match_node.connection_state == "connected" and match_node.local_actor() != null:
		var okay: bool = match_node.local_id == 1 and match_node.local_actor().display_name == "Account bridge QA" and match_node.phase == "waiting" and match_node.round_number == 0 and match_node.reward_status == "waiting_for_accounts"
		print("ACCOUNT_NETWORK_BOUND_PASS" if okay else "ACCOUNT_NETWORK_BOUND_FAIL")
		_finish.call_deferred(okay)
		finished = true
	elif role in ["guest", "replay"] and match_node.connection_state == "failed":
		print("ACCOUNT_NETWORK_REJECT_PASS " + role)
		_finish.call_deferred(true)
		finished = true
	if elapsed > (60 if role == "server" else 14):
		push_error("Account probe timeout: " + role + " " + match_node.connection_state)
		quit(1)
	return false

func _finish(okay: bool) -> void:
	match_node.queue_free()
	await process_frame
	await process_frame
	quit(0 if okay else 1)
