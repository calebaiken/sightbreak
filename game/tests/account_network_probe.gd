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
	match_node = TacticalMatch.new()
	match_node.configure({"mode": "server" if role == "server" else "client", "port": 27992, "address": "127.0.0.1", "name": "Client forged label", "require_accounts": role == "server", "economy_url": "http://127.0.0.1:8080", "server_id": "local-relay", "join_ticket": OS.get_environment("SIGHTBREAK_JOIN_TICKET") if role != "guest" else ""})
	root.add_child(match_node)

func _process(delta: float) -> bool:
	elapsed += delta
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
