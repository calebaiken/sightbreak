extends SceneTree
## Run using scripts/test_network.sh: separate real ENet server and client processes.
var match_node: TacticalMatch
var elapsed: float = 0.0
var role: String = "client"
var got_snapshot: bool = false
var origin := Vector3.ZERO
var initial_id: int = 0
var reconnect_started: bool = false
var reconnect_passed: bool = false
var deadline: float = 10.0

func _initialize() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg == "--server":
			role = "server"
	call_deferred("_start")

func _start() -> void:
	match_node = TacticalMatch.new()
	match_node.configure({"mode": role, "name": "Network QA", "address": "127.0.0.1", "port": 27991})
	root.add_child(match_node)
	if role == "server":
		if match_node.multiplayer.server_relay:
			push_error("Authoritative match must not enable client-to-client relay")
			quit(1)
			return
		match_node.phase = "live"
		match_node.time_left = 100
		# Disable bots for deterministic transport assertions; their ticks are covered separately.
		match_node._bot_clock = 100
		deadline = 14

func _process(delta: float) -> bool:
	elapsed += delta
	if match_node == null:
		return false
	if role == "server":
		if elapsed >= deadline:
			print("NETWORK_SERVER_PASS")
			quit(0)
		return false
	if match_node.connection_state == "connected" and match_node.local_actor() != null:
		var actor: SBActor = match_node.local_actor()
		if not got_snapshot:
			got_snapshot = true
			origin = actor.position
			initial_id = match_node.local_id
			print("NETWORK_CONNECTED id=%d actors=%d" % [initial_id, match_node.actors.size()])
		match_node.set_local_input({"move": Vector2(0, 1), "look": Vector2(PI, 0), "position": Vector3(999, 999, 999)})
		if elapsed > 2.5 and not reconnect_started:
			if match_node.actors.size() != 10 or actor.position.distance_to(origin) < 0.2 or actor.position.length() > 100:
				push_error("Authoritative movement/snapshot assertion failed")
				quit(1)
				return false
			reconnect_started = true
			match_node.multiplayer.multiplayer_peer.close()
			match_node.connection_state = "reconnecting"
			match_node._reconnect_clock = 0.7
		elif reconnect_started and elapsed > 4.0:
			reconnect_passed = match_node.local_id == initial_id
			if reconnect_passed:
				print("NETWORK_CLIENT_PASS movement snapshots reconnect")
				quit(0)
			else:
				push_error("Reconnect changed the reserved actor slot")
				quit(1)
	if elapsed > deadline:
		push_error("Network probe timed out: " + match_node.connection_state)
		quit(1)
	return false
