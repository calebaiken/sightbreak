extends SceneTree
## Hostile handshake server for scripts/test_handshake_hardening.sh: answers the
## stock client's hello in ways a real server never should.
## Args: --port=N --scenario=hang_up|reject_then_hang_up|accepted_text|accepted_stale_layout
const Match = preload("res://scripts/gameplay/match.gd")
var scenario := ""
var api: SceneMultiplayer

func _initialize() -> void:
	_run.call_deferred()

## A null layout leaves the field out, as every build before it existed did.
func _reply(accepted: Variant, layout: Variant = RelayYard.LAYOUT_REVISION) -> PackedByteArray:
	var hello := {"game": "sightbreak", "protocol": Match.PROTOCOL_VERSION, "build": "probe", "accepted": accepted, "reason": "Probe server refuses this client."}
	if layout != null:
		hello["layout"] = layout
	return JSON.stringify(hello).to_utf8_buffer()

func _on_hello(peer: int, _data: PackedByteArray) -> void:
	match scenario:
		"hang_up":
			api.disconnect_peer(peer)
		"reject_then_hang_up":
			# ENet discards the queued reply with the connection.
			api.send_auth(peer, _reply(false))
			api.disconnect_peer(peer)
		"accepted_text":
			api.send_auth(peer, _reply("yes"))
			api.complete_auth(peer)
		"accepted_stale_layout":
			# A server that admits on the protocol number alone: it accepts, with no layout in its hello.
			api.send_auth(peer, _reply(true, null))
			api.complete_auth(peer)

func _run() -> void:
	var port := 0
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--port="): port = int(argument.trim_prefix("--port="))
		if argument.begins_with("--scenario="): scenario = argument.trim_prefix("--scenario=")
	api = get_multiplayer() as SceneMultiplayer
	api.auth_callback = _on_hello
	api.auth_timeout = 30.0
	var peer := ENetMultiplayerPeer.new()
	if peer.create_server(port, 4) != OK:
		print("PROBE_SERVER_FAILED")
		quit(1)
		return
	api.multiplayer_peer = peer
	print("SIGHTBREAK_SERVER_READY")
	var started := Time.get_ticks_msec()
	while Time.get_ticks_msec() - started < 15000:
		await process_frame
	api.auth_callback = Callable()
	api.multiplayer_peer = OfflineMultiplayerPeer.new()
	await process_frame
	quit()
