extends SceneTree

# DIAGNOSTIC ADAPTER, NOT AN INTEGRATION REPAIR. The candidate refers to actor
# names/methods that its own shipped SBActor does not have. Supply only read-only
# aliases here to reach unchanged candidate helpers, then explicitly bridge a
# returned command to the REAL SBActor.tick_authority movement/weapon engine.
# The strict probe separately exercises unmodified actors and match loading.
class FixtureActor extends SBActor:
	var id: int:
		get: return actor_id
	var slot: int = 0
	var hp: float:
		get: return health
	var reloading: bool:
		get: return reload_remaining > 0.0
	var is_bot: bool = true
	var planting: bool = false
	var defusing: bool = false
	var force_hidden: bool = true
	func eye_position() -> Vector3:
		return global_position + Vector3.UP * head_height
	func can_see(other: SBActor) -> bool:
		return false if force_hidden else super.can_see(other)

class FixtureMatch extends Node3D:
	var arena: Node3D
	var actors: Dictionary = {}
	var _bot_state: Dictionary = {}
	var _team_ai_state: Dictionary = SBBotAI.create_team_state()
	var _heard: Dictionary = {}
	var _elapsed: float = 100.0
	var _rng := RandomNumberGenerator.new()
	var phase: String = "live"
	var time_left: float = 90.0
	var round_number: int = 2
	var objective_state: String = "carried"
	var objective_carrier: int = 99
	var objective_position := Vector3.ZERO
	var options: Dictionary = {"difficulty": "normal"}
	var bot_difficulty: String:
		get: return str(options.difficulty)
	var bomb_carrier_id: int:
		get: return objective_carrier
	var bomb_planted: bool:
		get: return objective_state == "planted"
	var planted_position: Vector3:
		get: return objective_position
	func _is_bot(_id: int) -> bool:
		return true

var ai: Script
var bridge_count: int = 0

func _initialize() -> void:
	_run.call_deferred()

func emit_result(name: String, data: Dictionary) -> void:
	data["case"] = name
	print("NATIVE_BEHAVIOR ", JSON.stringify(data))

func reset_memory(m: FixtureMatch, bot: FixtureActor) -> void:
	m._bot_state = {bot.actor_id: SBBotAI.create_state(bot)}
	m._team_ai_state = SBBotAI.create_team_state()
	m._heard.clear()
	bot.input_state.clear()

func decide(m: FixtureMatch, bot: FixtureActor, delta: float = 0.12) -> Dictionary:
	var returned: Variant = ai.call("compute_bot_input", m, bot, delta)
	if returned is Dictionary:
		bridge_count += 1
		bot.input_state = returned.duplicate(true)
	return bot.input_state.duplicate(true)

func equipment(a: SBActor) -> Dictionary:
	return {"credits": a.credits, "weapon": a.weapon_id, "inventory": a.inventory.duplicate(), "ammo": a.ammo, "reserve": a.reserve, "smokes": a.smokes, "grenades": a.grenades}

func _run() -> void:
	ai = load("res://scripts/gameplay/bot_ai.gd")
	var arena_script: Script = load("res://scripts/gameplay/arena.gd")
	var m := FixtureMatch.new()
	root.add_child(m)
	m.arena = arena_script.new()
	m.add_child(m.arena)
	m._rng.seed = 1847
	var bot := FixtureActor.new()
	bot.configure(6, 1, "DiagnosticBot")
	m.add_child(bot)
	bot.reset_for_round(Vector3(-14, 0.05, 2))
	bot.smokes = 0
	bot.grenades = 0
	var enemy := FixtureActor.new()
	enemy.configure(1, 0, "DiagnosticEnemy")
	m.add_child(enemy)
	enemy.reset_for_round(Vector3(-4, 0.05, 2))
	enemy.collision_layer = 0
	enemy.collision_mask = 0
	m.actors = {6: bot, 1: enemy}
	await physics_frame
	await physics_frame
	emit_result("fixture_scope", {"actor": "SBActor with explicit aliases", "arena_class": arena_script.get_global_name(), "real_tick_authority": true, "production_match": false, "candidate_return_requires_manual_input_bridge": true, "physics_fps": Engine.physics_ticks_per_second})

	# A V2 caller ignores compute_bot_input's return; verify its actual command sink.
	reset_memory(m, bot)
	bot.input_state = {"sentinel": true}
	var raw_return: Variant = ai.call("compute_bot_input", m, bot, 0.12)
	emit_result("compute_input_sink", {"return_is_dictionary": raw_return is Dictionary, "wrote_actor_input": not bot.input_state.has("sentinel"), "actor_input": bot.input_state})

	# Direct sound events use the exact production _shot dictionary schema. Perception
	# is deliberately hidden to avoid confounding the auditory path with vision.
	for side: int in [1, 0]:
		bot.team = side
		enemy.team = 1 - side
		bot.actor_id = 6 if side == 1 else 3
		bot.slot = 0 if side == 1 else 2
		m.actors = {bot.actor_id: bot, 1: enemy}
		for difficulty: String in ["easy", "normal", "hard"]:
			m.options.difficulty = difficulty
			var profile: Dictionary = SBBotAI.profile_for(difficulty)
			for scenario: Dictionary in [
				{"tag": "near", "distance": 10.0, "age": 0.0, "ally": false},
				{"tag": "easy_inside", "distance": 17.9, "age": 0.0, "ally": false},
				{"tag": "easy_boundary", "distance": 18.0, "age": 0.0, "ally": false},
				{"tag": "easy_outside", "distance": 18.1, "age": 0.0, "ally": false},
				{"tag": "easy_bypass20", "distance": 20.0, "age": 0.0, "ally": false},
				{"tag": "normal_outside", "distance": 27.0, "age": 0.0, "ally": false},
				{"tag": "all_outside", "distance": 36.0, "age": 0.0, "ally": false},
				{"tag": "expired", "distance": 10.0, "age": 5.1, "ally": false},
				{"tag": "future", "distance": 10.0, "age": -1.0, "ally": false},
				{"tag": "ally", "distance": 10.0, "age": 0.0, "ally": true}
			]:
				reset_memory(m, bot)
				enemy.team = side if scenario.ally else 1 - side
				var sound_pos: Vector3 = bot.position + Vector3(float(scenario.distance), 0, 0)
				m._heard = {1: {"position": sound_pos, "time": m._elapsed - float(scenario.age)}}
				var state: Dictionary = m._bot_state[bot.actor_id]
				var destination: Vector3 = ai.call("select_destination", m, bot, state, profile)
				emit_result("hearing", {"team": side, "difficulty": difficulty, "scenario": scenario.tag, "distance": scenario.distance, "age": scenario.age, "declared_range": profile.hearing_range, "heard_at": state.heard_at, "heard_exact": state.heard_pos == sound_pos, "destination_exact_sound": destination == sound_pos, "destination": destination, "role": state.role})
			enemy.team = 1 - side
			var exact_count: int = 0
			var error_sum: float = 0.0
			for index in range(16):
				reset_memory(m, bot)
				var pos := bot.position + Vector3(4.15 + float(index) * 0.17, 0.0, -4.31 + float(index) * 0.11)
				m._heard = {1: {"position": pos, "time": m._elapsed}}
				var state: Dictionary = m._bot_state[bot.actor_id]
				SBBotAI._update_auditory_and_team_memory(m, bot, state, profile)
				var error_distance: float = (state.heard_pos as Vector3).distance_to(pos)
				error_sum += error_distance
				if state.heard_pos == pos:
					exact_count += 1
			emit_result("sound_precision", {"team": side, "difficulty": difficulty, "declared_sound_noise": profile.sound_noise, "samples": 16, "exact_count": exact_count, "mean_position_error_m": error_sum / 16.0})

	# Directional hit response must retain facing priority while route movement
	# remains world-space coherent. No visual target or gunfire event is supplied.
	bot.team = 1
	bot.actor_id = 6
	bot.slot = 0
	enemy.team = 0
	m.actors = {6: bot, 1: enemy}
	m.options.difficulty = "normal"
	bot.yaw = 0.0
	for visual_memory: bool in [false, true]:
		reset_memory(m, bot)
		if visual_memory:
			m._bot_state[6].seen_at = m._elapsed - 0.2
			m._bot_state[6].last_seen = bot.position + Vector3(0, 0, -8)
		var undamaged: Dictionary = decide(m, bot)
		reset_memory(m, bot)
		if visual_memory:
			m._bot_state[6].seen_at = m._elapsed - 0.2
			m._bot_state[6].last_seen = bot.position + Vector3(0, 0, -8)
		SBBotAI.record_damage(m._bot_state, m.actors, 6, 1, m._elapsed)
		var damaged: Dictionary = decide(m, bot)
		var expected_yaw: float = rotate_toward(bot.yaw, -PI / 2.0, float(SBBotAI.profile_for("normal").turn_speed) * 0.12)
		var move: Vector2 = damaged.get("move", Vector2.ZERO)
		var look: Vector2 = damaged.get("look", Vector2.ZERO)
		var world_move: Vector3 = Basis(Vector3.UP, look.x) * Vector3(move.x, 0, -move.y)
		emit_result("damage_priority", {"has_visual_memory": visual_memory, "undamaged_look": undamaged.get("look"), "damaged_look": look, "expected_yaw": expected_yaw, "retained_damage_yaw": absf(angle_difference(look.x, expected_yaw)) < 0.001, "move": move, "world_move": world_move, "damaged_at": m._bot_state[6].damaged_at})

	# Full native collision-backed arrival, not just a nonzero next waypoint.
	# Each source's own five anchor constants are used; maps differ, so do not use
	# this adapted comparison as an integrated like-for-like performance claim.
	m.actors = {6: bot}
	enemy.free()
	for slot in range(5):
		bot.actor_id = 6 + slot
		bot.slot = slot
		m.actors = {bot.actor_id: bot}
		var origin := Vector3(float(slot - 2) * 2.2, 0.05, 20.5)
		bot.reset_for_round(origin)
		bot.smokes = 0
		bot.grenades = 0
		reset_memory(m, bot)
		var declared: Vector3 = SBBotAI.DEFENDER_ANCHORS[slot]
		var min_distance: float = INF
		var arrival_frame: int = -1
		var near_ticks: int = 0
		var samples: Array = []
		for frame in range(1200):
			await physics_frame
			m._elapsed += 1.0 / 60.0
			if frame % 8 == 0:
				decide(m, bot)
			bot.tick_authority(1.0 / 60.0)
			var distance: float = Vector2(bot.position.x - declared.x, bot.position.z - declared.z).length()
			min_distance = minf(min_distance, distance)
			if distance <= 1.8:
				near_ticks += 1
				if arrival_frame == -1:
					arrival_frame = frame
			if frame % 120 == 0:
				samples.append({"frame": frame, "position": bot.position, "distance": distance, "input": bot.input_state, "stuck": m._bot_state[bot.actor_id].stuck})
		emit_result("anchor_arrival", {"slot": slot, "origin": origin, "declared_anchor": declared, "minimum_distance_m": min_distance, "arrival_seconds": float(arrival_frame) / 60.0 if arrival_frame >= 0 else -1.0, "seconds_within_1_8m": float(near_ticks) / 60.0, "final_position": bot.position, "final_input": bot.input_state, "samples": samples})

	# Equipment remains actual SBActor.buy_weapon. Aliases only allow the candidate
	# selector's nonexistent actor.id reference to be measured separately.
	for difficulty: String in ["easy", "normal", "hard"]:
		for credits: int in [0, 1100, 1450, 1850, 2400, 2600, 2900, 5000]:
			for round_number: int in [1, 2]:
				bot.reset_loadout()
				bot.alive = true
				bot.credits = credits
				bot.ammo = 2
				bot.reserve = 3
				bot.smokes = 0
				bot.grenades = 0
				var before: Dictionary = equipment(bot)
				var choice: String = SBBotAI.choose_buy_weapon(bot, difficulty, round_number)
				SBBotAI.buy_equipment(bot, difficulty, round_number)
				emit_result("equipment", {"difficulty": difficulty, "round": round_number, "initial_credits": credits, "choice": choice, "choice_valid": SBWeapons.DATA.has(choice), "before": before, "after": equipment(bot)})
	emit_result("completed", {"manual_input_bridges": bridge_count, "production_integration_pass": false})
	m.queue_free()
	await process_frame
	await process_frame
	quit(0)
