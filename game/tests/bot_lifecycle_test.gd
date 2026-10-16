extends SceneTree

# Real physics and bot decisions drive every round; no forced winners, planted
# states or elapsed-time claims about rewarded online matches are involved.
var match_node: TacticalMatch
var elapsed: float = 0.0
var observed_round: int = 0
var initial_team: int = 0
var halftime_seen: bool = false
var planted_seen: bool = false
var results: Array = []
var done: bool = false

func _initialize() -> void:
	call_deferred("_start")

func _start() -> void:
	match_node = TacticalMatch.new()
	match_node.configure({"mode": "offline", "difficulty": "normal"})
	root.add_child(match_node)
	match_node.local_id = 0
	match_node._rng.seed = 1847
	for actor: SBActor in match_node.actors.values():
		actor._rng.seed = 100 + actor.actor_id
	initial_team = match_node.actors[1].team
	match_node.match_finished.connect(func(result: Dictionary) -> void: results.append(result))
	Engine.time_scale = 4.0

func _process(delta: float) -> bool:
	if match_node == null or done:
		return false
	elapsed += delta
	planted_seen = planted_seen or match_node.objective_state == "planted"
	if observed_round != match_node.round_number:
		observed_round = match_node.round_number
		print("BOT_LIFECYCLE round=%d score=%d:%d simulated_seconds=%.1f" % [observed_round, match_node.attack_score, match_node.defend_score, elapsed])
		if observed_round == 7:
			halftime_seen = match_node.actors[1].team != initial_team
	if match_node.phase == "match_over" or elapsed > 1900:
		done = true
		_finish.call_deferred()
	return false

func _finish() -> void:
	Engine.time_scale = 1.0
	var kills: int = 0
	for actor: SBActor in match_node.actors.values():
		kills += actor.kills
	var success: bool = match_node.phase == "match_over" and results.size() == 1 and halftime_seen and kills > 0 and observed_round >= 7 and observed_round <= 12
	print("BOT_LIFECYCLE_RESULT passed=%s rounds=%d score=%d:%d kills=%d halftime=%s plant_observed=%s reports=%d simulated_seconds=%.1f" % [success, observed_round, match_node.attack_score, match_node.defend_score, kills, halftime_seen, planted_seen, results.size(), elapsed])
	match_node.queue_free()
	await process_frame
	# The final shots still have mixer-owned playback references after deletion.
	await create_timer(0.5).timeout
	quit(0 if success else 1)
