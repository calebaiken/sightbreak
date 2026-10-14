extends SceneTree
## Reads a synthetic ten-account fixture; actual authority payload builder is used.
var source := ""
func _initialize() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--fixture="): source = arg.trim_prefix("--fixture=")
	call_deferred("run")
func run() -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(source))
	var game := TacticalMatch.new()
	game.configure({"mode": "offline"})
	root.add_child(game)
	game.set_physics_process(false)
	game._start_ranked_match()
	game.phase = "match_over"
	game.attack_score = 7
	game.defend_score = 2
	game._elapsed = 600
	game._match_started_elapsed = 0
	game._started_at = Time.get_datetime_string_from_unix_time(int(Time.get_unix_time_from_system()) - 600) + "Z"
	for id in range(1, 11):
		game._account_ids[id] = fixture.player_ids[id - 1]
		game._peer_actors[id + 100] = id
		game._activity_seconds[id] = 500
	game._bridge = SBEconomyBridge.new()
	game.add_child(game._bridge)
	await game._submit_ranked_result()
	if game.reward_status != "queued_for_delivery":
		push_error("Outbox did not record queued handoff")
		quit(1)
		return
	print("OUTBOX_GAME_STAGED")
	# Parent test SIGKILLs the real process here; no graceful destructor can help.
