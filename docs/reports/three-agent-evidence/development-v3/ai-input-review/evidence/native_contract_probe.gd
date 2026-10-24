extends SceneTree

# No actor/arena compatibility aliases: exercise the shipped classes and the
# actual Node-plus-integer-ID callback shape in TacticalMatch._damaged.
class ContractMatch extends Node3D:
	var arena: Node3D
	var actors: Dictionary = {}
	var _bot_state: Dictionary = {}
	var _team_ai_state: Dictionary = SBBotAI.create_team_state()
	var _heard: Dictionary = {}
	var _elapsed: float = 10.0
	var _rng := RandomNumberGenerator.new()
	var phase: String = "live"
	var options: Dictionary = {"difficulty": "normal"}
	var round_number: int = 2
	var time_left: float = 90.0
	var objective_state: String = "carried"
	var objective_carrier: int = 1
	var objective_position := Vector3.ZERO
	func _is_bot(_id: int) -> bool:
		return true

func _initialize() -> void:
	_run.call_deferred()

func emit_result(name: String, data: Dictionary) -> void:
	data["case"] = name
	print("NATIVE_CONTRACT ", JSON.stringify(data))

func equipment(a: SBActor) -> Dictionary:
	return {"credits": a.credits, "weapon": a.weapon_id, "inventory": a.inventory.duplicate(), "ammo": a.ammo, "reserve": a.reserve, "smokes": a.smokes, "grenades": a.grenades}

func _run() -> void:
	var ai: Script = load("res://scripts/gameplay/bot_ai.gd")
	var arena_script: Script = load("res://scripts/gameplay/arena.gd")
	var methods: Dictionary = {}
	for item: Dictionary in ai.get_script_method_list():
		methods[item.name] = {"arguments": item.args.size(), "return": item.return}
	emit_result("bot_api", {"methods": methods, "arena_class": arena_script.get_global_name()})
	var m := ContractMatch.new()
	root.add_child(m)
	m.arena = arena_script.new()
	m.add_child(m.arena)
	var bot := SBActor.new()
	bot.configure(6, 1, "UnmodifiedBot")
	m.add_child(bot)
	bot.reset_for_round(Vector3(-14.0, 0.05, 2.0))
	var enemy := SBActor.new()
	enemy.configure(1, 0, "UnmodifiedEnemy")
	m.add_child(enemy)
	enemy.reset_for_round(Vector3(-14.0, 0.05, -10.0))
	m.actors = {6: bot, 1: enemy}
	m._bot_state[6] = SBBotAI.create_state(bot)
	await physics_frame
	await physics_frame
	var properties: Array = []
	for item: Dictionary in bot.get_property_list():
		properties.append(item.name)
	var missing: Array = []
	for key: String in ["id", "slot", "hp", "reloading", "is_bot", "planting", "defusing"]:
		if not properties.has(key):
			missing.append(key)
	emit_result("shipped_actor_surface", {"missing_candidate_properties": missing, "has_apply_tick": bot.has_method("apply_tick"), "has_eye_position": bot.has_method("eye_position"), "has_tick_authority": bot.has_method("tick_authority")})
	SBBotAI.record_damage(m, 6, 1, 25.0)
	emit_result("production_damage_callback_ids", {"damaged_at": m._bot_state[6].damaged_at, "expected": m._elapsed, "recorded": m._bot_state[6].damaged_at == m._elapsed})
	m._bot_state[6] = SBBotAI.create_state(bot)
	SBBotAI.record_damage(m._bot_state, m.actors, 6, 1, m._elapsed)
	emit_result("dictionary_damage_callback", {"damaged_at": m._bot_state[6].damaged_at, "damaged_from": m._bot_state[6].damaged_from, "recorded": m._bot_state[6].damaged_at == m._elapsed})
	m._bot_state[6] = SBBotAI.create_state(bot)
	SBBotAI.record_elimination(m, 1, 6, enemy.position)
	emit_result("production_elimination_callback_ids", {"team_state": m._team_ai_state, "heard_at": m._bot_state[6].heard_at})
	bot.input_state = {"sentinel": true}
	print("NATIVE_CONTRACT_BEGIN shipped_compute")
	SBBotAI.compute_bot_input(m, bot, 0.12)
	emit_result("shipped_compute", {"input_state": bot.input_state, "wrote_input": not bot.input_state.has("sentinel")})
	bot.credits = 5000
	bot.reset_loadout()
	bot.ammo = 2
	bot.reserve = 3
	bot.smokes = 0
	bot.grenades = 0
	var before: Dictionary = equipment(bot)
	var choice: String = SBBotAI.choose_buy_weapon(bot, "normal", 1)
	SBBotAI.buy_equipment(bot, "normal", 1)
	emit_result("first_round_equipment", {"choice": choice, "choice_is_valid": SBWeapons.DATA.has(choice), "before": before, "after": equipment(bot)})
	bot.credits = 2000
	print("NATIVE_CONTRACT_BEGIN shipped_mid_budget_choice")
	var mid_choice: String = SBBotAI.choose_buy_weapon(bot, "normal", 2)
	emit_result("mid_budget_choice", {"choice": mid_choice, "valid": SBWeapons.DATA.has(mid_choice)})
	print("NATIVE_CONTRACT_BEGIN shipped_match_load")
	var match_script: Script = load("res://scripts/gameplay/match.gd")
	emit_result("shipped_match_load", {"resource_loaded": match_script != null, "can_instantiate": match_script != null and match_script.can_instantiate()})
	m.queue_free()
	await process_frame
	await process_frame
	print("NATIVE_CONTRACT_COMPLETE errors_in_stderr_are_failures_not_a_pass")
	quit(0)
