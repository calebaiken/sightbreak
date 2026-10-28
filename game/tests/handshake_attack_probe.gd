extends SceneTree
## Hostile handshake client for scripts/test_handshake_hardening.sh: speaks raw
## SceneMultiplayer authentication to a stock dedicated server.
## Args: --port=N --scenario=spam|fractional|huge|good_then_bad|bad_then_good|stale_layout|unreadable_layout
## Prints HANDSHAKE_ATTACK {scenario, admitted, replies, dropped_after}.
## "Good" hellos carry this build's PROTOCOL_VERSION and Relay Yard layout; mismatched ones carry the next protocol.
const Match = preload("res://scripts/gameplay/match.gd")
const GOOD := Match.PROTOCOL_VERSION
const BAD := Match.PROTOCOL_VERSION + 1
var port := 0
var scenario := ""
var api: SceneMultiplayer
var started := 0
var replies := 0
var admitted := false
var dropped_after := -1.0

func _initialize() -> void:
	_run.call_deferred()

func now() -> float:
	return (Time.get_ticks_msec() - started) / 1000.0

## A null layout leaves the field out, as every build before it existed did.
func _hello(protocol: Variant, layout: Variant = RelayYard.LAYOUT_REVISION) -> PackedByteArray:
	var hello := {"game": "sightbreak", "protocol": protocol, "build": "probe", "accepted": true, "reason": ""}
	if layout != null:
		hello["layout"] = layout
	return JSON.stringify(hello).to_utf8_buffer()

func _run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--port="): port = int(argument.trim_prefix("--port="))
		if argument.begins_with("--scenario="): scenario = argument.trim_prefix("--scenario=")
	started = Time.get_ticks_msec()
	api = get_multiplayer() as SceneMultiplayer
	api.auth_callback = func(_peer: int, _data: PackedByteArray) -> void: replies += 1
	api.auth_timeout = 30.0
	api.peer_authenticating.connect(_attack)
	api.peer_authentication_failed.connect(func(_peer: int) -> void: dropped_after = now())
	api.server_disconnected.connect(func() -> void: if dropped_after < 0.0: dropped_after = now())
	api.connected_to_server.connect(func() -> void: admitted = true)
	var peer := ENetMultiplayerPeer.new()
	peer.create_client("127.0.0.1", port)
	api.multiplayer_peer = peer
	while now() < 8.0 and dropped_after < 0.0:
		await process_frame
	print("HANDSHAKE_ATTACK " + JSON.stringify({"scenario": scenario, "admitted": admitted, "replies": replies, "dropped_after": snappedf(dropped_after, 0.01)}))
	api.auth_callback = Callable()
	api.multiplayer_peer = OfflineMultiplayerPeer.new()
	await process_frame
	quit()

func _attack(peer: int) -> void:
	match scenario:
		"spam":
			# A mismatched hello every frame, twenty at a time, while still connected.
			while api.get_authenticating_peers().has(peer) and now() < 7.0:
				for i in range(20):
					api.send_auth(peer, _hello(BAD))
				await process_frame
		"fractional":
			api.send_auth(peer, _hello(GOOD + 0.9))
			api.complete_auth(peer)
		"huge":
			api.send_auth(peer, '{"game":"sightbreak","protocol":1e400}'.to_utf8_buffer())
			api.complete_auth(peer)
		"good_then_bad":
			api.send_auth(peer, _hello(GOOD))
			api.send_auth(peer, _hello(BAD))
			await create_timer(0.3).timeout
			if api.get_authenticating_peers().has(peer):
				api.complete_auth(peer)
		"stale_layout":
			# The right protocol from a build that predates the layout field.
			api.send_auth(peer, _hello(GOOD, null))
			api.complete_auth(peer)
		"unreadable_layout":
			api.send_auth(peer, _hello(GOOD, "two"))
			api.complete_auth(peer)
		"bad_then_good":
			api.send_auth(peer, _hello(BAD))
			await create_timer(0.2).timeout
			if api.get_authenticating_peers().has(peer):
				api.send_auth(peer, _hello(GOOD))
				api.complete_auth(peer)
