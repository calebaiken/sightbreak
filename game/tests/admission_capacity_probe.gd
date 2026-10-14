extends SceneTree
var game: TacticalMatch
var role := "client"
var expectation := "admitted"
var full := false
var control := ""
var port := 29910
var elapsed := 0.0
var reported := false
func _initialize() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--role="): role = arg.get_slice("=", 1)
		elif arg.begins_with("--expect="): expectation = arg.get_slice("=", 1)
		elif arg.begins_with("--control="): control = arg.trim_prefix("--control=")
		elif arg.begins_with("--port="): port = int(arg.get_slice("=", 1))
		elif arg == "--full": full = true
	call_deferred("run")
func run() -> void:
	game = TacticalMatch.new()
	game.configure({"mode": role, "port": port, "address": "127.0.0.1", "require_accounts": role == "server", "economy_url": "http://127.0.0.1:8182", "server_id": "local-relay", "join_ticket": OS.get_environment("SIGHTBREAK_JOIN_TICKET")})
	root.add_child(game)
	if role == "server" and full:
		for id in range(1, 11):
			game._reservations["capacity-fixture-%d" % id] = {"id": id, "expires": 10000.0}
func _process(delta: float) -> bool:
	elapsed += delta
	if game == null: return false
	if role == "server":
		if full and FileAccess.file_exists(control):
			game._reservations.clear()
			full = false
		return false
	if game.connection_state == "connected" and not reported:
		reported = true
		print("CAPACITY_ADMITTED id=%d" % game.local_id)
		if expectation != "admitted": finish(1)
	elif game.connection_state == "failed":
		print("CAPACITY_REJECTED")
		finish(0 if expectation == "rejected" else 1)
	if reported and FileAccess.file_exists(control):
		finish(0)
	if elapsed > 18:
		push_error("Capacity probe timed out")
		finish(1)
	return false
func finish(code: int) -> void:
	game.queue_free()
	quit(code)
