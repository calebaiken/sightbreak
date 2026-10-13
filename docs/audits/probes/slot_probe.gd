extends SceneTree
## Opens ten raw ENet connections that never send a join request, then checks
## whether a legitimate eleventh client can still reach the dedicated server.
var idle: Array[ENetConnection] = []

func _initialize() -> void:
	_run.call_deferred()

func _pump(seconds: float) -> int:
	var connected := 0
	var deadline := Time.get_ticks_msec() + int(seconds * 1000)
	while Time.get_ticks_msec() < deadline:
		for host in idle:
			var event: Array = host.service(5)
			if event[0] == ENetConnection.EVENT_CONNECT:
				connected += 1
			elif event[0] == ENetConnection.EVENT_DISCONNECT:
				print("SLOT_PROBE idle_peer_disconnected_by_server")
		await process_frame
	return connected

func _run() -> void:
	var port := int(OS.get_cmdline_user_args()[0])
	for i in range(int(OS.get_cmdline_user_args()[1])):
		var host := ENetConnection.new()
		host.create_host(1, 8)
		host.connect_to_host("127.0.0.1", port, 255)
		idle.append(host)
	var connected := await _pump(3.0)
	print("SLOT_PROBE idle_connections_established=", connected)
	var player := ENetMultiplayerPeer.new()
	player.create_client("127.0.0.1", port)
	var reached := false
	var deadline := Time.get_ticks_msec() + 8000
	while Time.get_ticks_msec() < deadline:
		player.poll()
		for host in idle:
			var e: Array = host.service(0)
			if e[0] == ENetConnection.EVENT_DISCONNECT:
				print("SLOT_PROBE idle_peer_disconnected_during_attempt")
		if player.get_connection_status() == MultiplayerPeer.CONNECTION_CONNECTED:
			reached = true
			break
		await process_frame
	print("SLOT_PROBE legitimate_11th_client_connected=", reached, " status=", player.get_connection_status())
	quit(0)
