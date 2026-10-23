extends SceneTree
## Observe production match state; only clients supply ordinary gameplay input.
## Actor 1 plants during its attacking half. Other clients turn at spawn.
## This controlled no-combat policy tests match/economy plumbing, not human play.
var game: ObservedMatch
var role := "client"
var port := 29940
var output := ""
var control := ""
var joined := false
var initial_id := 0
var snapshots := 0
var latest: Dictionary = {}
var events: Array = []
var last_state := ""
var next_sample := 0
var quitting := false
var match_summary: Dictionary = {}

class ObservedMatch extends TacticalMatch:
	var snapshot_count := 0
	func _apply_snapshot(data: Dictionary) -> void:
		super._apply_snapshot(data)
		snapshot_count += 1

func _initialize() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--role="): role = arg.trim_prefix("--role=")
		elif arg.begins_with("--port="): port = int(arg.trim_prefix("--port="))
		elif arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg.begins_with("--control="): control = arg.trim_prefix("--control=")
	call_deferred("start")

func start() -> void:
	game = ObservedMatch.new()
	game.configure({"mode": role, "port": port, "address": "127.0.0.1", "name": "Untrusted client label", "prediction": false,
		"require_accounts": role == "server", "economy_url": OS.get_environment("SIGHTBREAK_TEST_ECONOMY_URL"),
		"server_id": "local-relay", "join_ticket": OS.get_environment("SIGHTBREAK_JOIN_TICKET")})
	game.match_finished.connect(func(summary: Dictionary): match_summary = summary)
	root.add_child(game)

func client_input(actor: SBActor) -> Dictionary:
	# Server activity policy accepts real look changes. Keep input flowing through
	# ordinary RPCs even when the controlled scenario calls for holding position.
	var yaw := 0.08 if int(Time.get_ticks_msec() / 1000) % 2 == 0 else -0.08
	var move := Vector2.ZERO
	var interact := false
	if game.local_id == 1 and actor.team == 0 and game.phase == "live" and game.objective_state == "carried":
		interact = game.arena.is_at_site(actor.position) >= 0
		if not interact:
			var waypoint := SBBotAI.safe_navigate(game.arena, actor.position, game.arena.sites[0])
			var direction := waypoint - actor.position
			yaw = atan2(-direction.x, -direction.z)
			move = Vector2(0, 1)
	return {"look": Vector2(yaw, 0), "move": move, "interact": interact}

func state() -> Dictionary:
	var actor := game.local_actor()
	var report := {"role": role, "msec": Time.get_ticks_msec(), "phase": game.phase, "round": game.round_number,
		"attack": game.attack_score, "defend": game.defend_score, "time_left": game.time_left,
		"objective": game.objective_state, "reward_status": game.reward_status, "connection": game.connection_state,
		"joined": joined, "initial_id": initial_id, "local_id": game.local_id, "snapshots": game.snapshot_count,
		"elapsed": game._elapsed, "summary": match_summary, "protocol": game.PROTOCOL_VERSION,
		"stock_rules": {"buy": game.BUY_SECONDS, "round": game.ROUND_SECONDS, "plant": game.PLANT_SECONDS,
			"defuse": game.DEFUSE_SECONDS, "device": game.DEVICE_SECONDS, "win_score": game.WIN_SCORE}}
	if actor != null:
		report["display_name"] = actor.display_name
		report["team"] = actor.team
		report["position"] = {"x": actor.position.x, "y": actor.position.y, "z": actor.position.z}
	if role == "server":
		report["accounts"] = game._account_ids.duplicate()
		report["bindings"] = game._peer_actors.duplicate()
		report["ranked_started"] = game._ranked_started
		report["ranked_eligible"] = game._ranked_eligible
		report["match_id"] = game._match_id
		report["activity_seconds"] = game._activity_seconds.duplicate()
		report["match_duration"] = game._elapsed - game._match_started_elapsed
	return report

func save_report() -> void:
	latest = state()
	var file := FileAccess.open(output + ".tmp", FileAccess.WRITE)
	file.store_string(JSON.stringify({"latest": latest, "transitions": events}))
	file.close()
	DirAccess.rename_absolute(output + ".tmp", output)

func _process(_delta: float) -> bool:
	if game == null or quitting: return false
	if role == "client" and game.connection_state == "connected":
		if not joined:
			joined = true
			initial_id = game.local_id
			print("ACCOUNT_MATCH_ADMITTED " + str(initial_id))
		var actor := game.local_actor()
		if actor != null: game.set_local_input(client_input(actor))
	var key := "%s/%d/%s/%s/%s" % [game.phase, game.round_number, game.objective_state, game.reward_status, game.connection_state]
	if key != last_state:
		last_state = key
		events.append(state())
		print("ACCOUNT_MATCH_STATE " + key)
	if Time.get_ticks_msec() >= next_sample:
		next_sample = Time.get_ticks_msec() + 1000
		save_report()
	if FileAccess.file_exists(control):
		quitting = true
		save_report()
		game.queue_free()
		await process_frame
		await process_frame
		quit(0)
	return false
