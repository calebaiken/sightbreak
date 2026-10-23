extends SceneTree
## Synthetic policy/time fixtures exercise the actual server adapter. No simulated human-play claim.
var fixture_path: String = ""
var result_path: String = ""

func _initialize() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--fixture="):
			fixture_path = arg.trim_prefix("--fixture=")
		if arg.begins_with("--result="):
			result_path = arg.trim_prefix("--result=")
	call_deferred("_run")

func _run() -> void:
	var config: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(fixture_path))
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
		game._account_ids[id] = config.player_ids[id - 1]
		game._peer_actors[id + 100] = id
		game._activity_seconds[id] = 500.0
		game.objective_contributions[id] = id % 3
	var payload: Dictionary = game._ranked_payload()
	if payload.is_empty():
		push_error("Fixture eligibility unexpectedly rejected")
		quit(1)
		return
	var bridge := SBEconomyBridge.new()
	bridge.configure(config.api_url, config.server_id)
	root.add_child(bridge)
	var first: Dictionary = await bridge.submit_result(payload)
	if not bool(first.get("ok", false)):
		push_error("Reward bridge rejected fixture status=%d" % int(first.get("status", 0)))
		quit(1)
		return
	var replay: Dictionary = await bridge.submit_result(payload)
	if not bool(replay.get("ok", false)) or first.data != replay.data or first.data.rewards.size() != 10:
		push_error("Reward replay or ten-participant settlement mismatch")
		quit(1)
		return
	var winners: int = 0
	for reward: Dictionary in first.data.rewards:
		if not bool(reward.eligible) or int(reward.credits) <= 0:
			push_error("Fixture account did not receive expected eligible settlement")
			quit(1)
			return
		if bool(reward.won):
			winners += 1
	if winners != 5:
		push_error("Settlement did not preserve squad winners")
		quit(1)
		return
	var output := FileAccess.open(result_path, FileAccess.WRITE)
	output.store_string(JSON.stringify(first.data))
	output.close()
	print("REWARD_BRIDGE_HTTP_PASS ten-fixture-accounts five-winners identical-replay")
	game.queue_free()
	bridge.queue_free()
	await process_frame
	quit(0)
