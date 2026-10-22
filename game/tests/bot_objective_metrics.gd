extends SceneTree
## Objective-play measurement for complete all-bot offline matches on the real engine.
## One match per process so every run starts clean. Prints one BOT_METRIC_ROUND line per
## round and one BOT_METRIC_MATCH line. Pure observation: it changes no game state, forces no
## winner and sets nothing except the random seeds and the time scale.
## --seed=<int> (default 1847) --difficulty=easy|normal|hard (default normal) --time-scale=<float> (default 4)
## --reverse-order processes actors 10 down to 1 each tick (the stock order is 1 up to 10), to test whether the
## lower ids win same-tick trades.
## --swap-start makes actors 6-10 the first attackers (the stock match starts with actors 1-5), so a squad effect
## can be told apart from a role effect: run every seed both ways.
var match_node: TacticalMatch
var seed_value: int = 1847
var difficulty: String = "normal"
var time_scale: float = 4.0
var swap_start: bool = false
var reverse_order: bool = false
var wall_elapsed: float = 0.0
var previous_phase: String = ""
var rounds: Array = []
var current: Dictionary = {}
var finished: bool = false
var attack_side_at_start: Dictionary = {}

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--seed="):
			seed_value = int(argument.trim_prefix("--seed="))
		elif argument.begins_with("--difficulty="):
			difficulty = argument.trim_prefix("--difficulty=")
		elif argument.begins_with("--time-scale="):
			time_scale = float(argument.trim_prefix("--time-scale="))
		elif argument == "--swap-start":
			swap_start = true
		elif argument == "--reverse-order":
			reverse_order = true
	call_deferred("_start")

func _start() -> void:
	match_node = TacticalMatch.new()
	match_node.configure({"mode": "offline", "difficulty": difficulty})
	root.add_child(match_node)
	match_node.local_id = 0
	if reverse_order:
		var in_order: Array = match_node.actors.values()
		match_node.actors.clear()
		in_order.reverse()
		for actor: SBActor in in_order:
			match_node.actors[actor.actor_id] = actor
	if swap_start:
		# Redo round 1 with the sides exchanged: the first attackers are actors 6-10.
		for actor: SBActor in match_node.actors.values():
			actor.team = 1 - actor.team
		match_node.round_number -= 1
		match_node._begin_round()
	match_node._rng.seed = seed_value
	for actor: SBActor in match_node.actors.values():
		actor._rng.seed = seed_value * 1000 + actor.actor_id
	match_node.notification.connect(_on_notification)
	match_node.elimination_reported.connect(_on_elimination)
	Engine.time_scale = time_scale

func _live_time() -> float:
	return match_node.ROUND_SECONDS - match_node.time_left

func _alive(team: int) -> int:
	var count: int = 0
	for actor: SBActor in match_node.actors.values():
		if actor.alive and actor.team == team:
			count += 1
	return count

func _begin_round_record() -> void:
	var carrier: SBActor = match_node.actors.get(match_node.objective_carrier) as SBActor
	current = {
		"round": match_node.round_number,
		"carrier": match_node.objective_carrier,
		"carrier_died_at": -1.0,
		"carrier_at_site_at": -1.0,
		"max_plant_hold": 0.0,
		"planted_at": -1.0,
		"first_kill_at": -1.0,
		"attackers_alive_15s": -1,
		"defenders_alive_15s": -1,
		"attackers_alive_30s": -1,
		"defenders_alive_30s": -1,
		"live_time": 0.0,
		"stuck_bots_max": 0,
		"kills": [],
		"reason": "",
		"winner": -1,
		"site": -1,
	}
	if carrier == null:
		current["carrier"] = -1

func _process(delta: float) -> bool:
	if match_node == null or finished:
		return false
	wall_elapsed += delta
	var phase: String = match_node.phase
	if phase == "live" and previous_phase != "live":
		_begin_round_record()
	if phase == "live" and not current.is_empty():
		var live: float = _live_time()
		current["live_time"] = live
		var carrier: SBActor = match_node.actors.get(match_node.objective_carrier) as SBActor
		if carrier != null:
			if not carrier.alive and float(current["carrier_died_at"]) < 0.0:
				current["carrier_died_at"] = live
			if carrier.alive and match_node.arena.is_at_site(carrier.position) >= 0 and float(current["carrier_at_site_at"]) < 0.0:
				current["carrier_at_site_at"] = live
			current["max_plant_hold"] = maxf(float(current["max_plant_hold"]), float(match_node._interactions.get(carrier.actor_id, 0.0)))
		if match_node.objective_state == "planted" and float(current["planted_at"]) < 0.0:
			current["planted_at"] = live
			current["site"] = 0 if match_node.objective_position.x < 0.0 else 1
		if float(current["first_kill_at"]) < 0.0 and (_alive(0) < 5 or _alive(1) < 5):
			current["first_kill_at"] = live
		var stuck_now: int = 0
		for actor_id in match_node._bot_state:
			var bot_state: Dictionary = match_node._bot_state[actor_id]
			var bot: SBActor = match_node.actors.get(actor_id) as SBActor
			if bot != null and bot.alive and float(bot_state.get("stuck", 0.0)) > 1.0:
				stuck_now += 1
		current["stuck_bots_max"] = maxi(int(current["stuck_bots_max"]), stuck_now)
		if live >= 15.0 and int(current["attackers_alive_15s"]) < 0:
			current["attackers_alive_15s"] = _alive(0)
			current["defenders_alive_15s"] = _alive(1)
		if live >= 30.0 and int(current["attackers_alive_30s"]) < 0:
			current["attackers_alive_30s"] = _alive(0)
			current["defenders_alive_30s"] = _alive(1)
	previous_phase = phase
	if phase == "match_over" or wall_elapsed > 2400.0:
		finished = true
		_finish.call_deferred()
	return false

func _on_elimination(killer_id: int, victim_id: int, _headshot: bool) -> void:
	if current.is_empty():
		return
	var killer: SBActor = match_node.actors.get(killer_id) as SBActor
	var victim: SBActor = match_node.actors.get(victim_id) as SBActor
	if killer == null or victim == null:
		return
	var kills: Array = current["kills"]
	kills.append({"t": snappedf(_live_time(), 0.1), "victim_team": victim.team, "victim": [snappedf(victim.position.x, 0.1), snappedf(victim.position.z, 0.1)], "killer": [snappedf(killer.position.x, 0.1), snappedf(killer.position.z, 0.1)], "distance": snappedf(killer.position.distance_to(victim.position), 0.1), "weapon": killer.weapon_id})

func _on_notification(text: String) -> void:
	if current.is_empty() or not (text.begins_with("Attackers win") or text.begins_with("Defenders win")):
		return
	current["winner"] = 0 if text.begins_with("Attackers") else 1
	current["reason"] = text.split("•")[-1].strip_edges()
	rounds.append(current.duplicate())
	print("BOT_METRIC_ROUND " + JSON.stringify(current))
	current = {}

func _finish() -> void:
	Engine.time_scale = 1.0
	var kills: int = 0
	for actor: SBActor in match_node.actors.values():
		kills += actor.kills
	var planted: int = 0
	for row: Dictionary in rounds:
		if float(row["planted_at"]) >= 0.0:
			planted += 1
	print("BOT_METRIC_MATCH " + JSON.stringify({"seed": seed_value, "swap_start": swap_start, "reverse_order": reverse_order, "difficulty": difficulty, "rounds": rounds.size(), "attack_score": match_node.attack_score, "defend_score": match_node.defend_score, "kills": kills, "planted_rounds": planted, "sim_seconds": wall_elapsed, "phase": match_node.phase}))
	match_node.queue_free()
	await process_frame
	await create_timer(0.5).timeout
	quit(0)
