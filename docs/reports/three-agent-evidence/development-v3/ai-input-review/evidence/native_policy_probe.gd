extends SceneTree

# Additional native diagnostics after the neutral comparison. These fixtures do
# not make the candidate integrate: missing actor/match aliases are explicit.
class AliasActor extends SBActor:
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
	func eye_position() -> Vector3:
		return global_position + Vector3.UP * head_height

class AliasMatch extends Node3D:
	var arena: Node3D
	var actors: Dictionary = {}
	var _bot_state: Dictionary = {}
	var _team_ai_state: Dictionary = SBBotAI.create_team_state()
	var _heard: Dictionary = {}
	var _elapsed: float = 100.0
	var _rng := RandomNumberGenerator.new()
	var phase: String = "live"
	var options: Dictionary = {"difficulty": "easy"}
	var round_number: int = 2
	var time_left: float = 90.0
	var objective_state: String = "carried"
	var objective_carrier: int = 99
	var objective_position := Vector3.ZERO
	var human_id: int = 7
	var bot_difficulty: String:
		get: return str(options.difficulty)
	var bomb_carrier_id: int:
		get: return objective_carrier
	var bomb_planted: bool:
		get: return objective_state == "planted"
	var planted_position: Vector3:
		get: return objective_position
	func _is_bot(actor_id: int) -> bool:
		return actor_id != human_id

func _initialize() -> void:
	_run.call_deferred()

func emit_result(name: String, data: Dictionary) -> void:
	data["case"] = name
	print("NATIVE_POLICY ", JSON.stringify(data))

func _run() -> void:
	var ai: Script = load("res://scripts/gameplay/bot_ai.gd")
	var arena_script: Script = load("res://scripts/gameplay/arena.gd")
	var candidate_api: bool = arena_script.get_global_name() == "SBArena"
	var m := AliasMatch.new()
	root.add_child(m)
	m.arena = arena_script.new()
	m.add_child(m.arena)
	var bot := AliasActor.new()
	bot.configure(6, 1, "Bot")
	m.add_child(bot)
	bot.reset_for_round(Vector3(-14, 0.05, -2))
	var other := AliasActor.new()
	other.configure(1, 0, "Other")
	m.add_child(other)
	other.reset_for_round(Vector3(-14, 0.05, 8))
	m.actors = {6: bot, 1: other}
	await physics_frame
	await physics_frame

	for difficulty: String in ["easy", "normal", "hard"]:
		for distance: float in [10.0, 40.0]:
			m._team_ai_state = SBBotAI.create_team_state()
			var report_pos: Vector3 = bot.position + Vector3(distance, 0, 0)
			var report: Dictionary = {"position": report_pos, "time": m._elapsed, "reporter": 8, "target_id": 1}
			if candidate_api:
				m._team_ai_state.callouts = {1: report}
			else:
				m._team_ai_state[1].contacts = {1: report}
			var state: Dictionary = SBBotAI.create_state(bot)
			SBBotAI._update_auditory_and_team_memory(m, bot, state, SBBotAI.profile_for(difficulty))
			emit_result("team_report_bounds", {"difficulty": difficulty, "distance": distance, "report_accepted": state.heard_at == m._elapsed, "exact_position": state.heard_pos == report_pos})

	# Real actor LOS, source geometry, and source perception acquisition. A sound
	# alert must not be confused with a hit by a particular rear attacker.
	m._team_ai_state = SBBotAI.create_team_state()
	m._heard.clear()
	var before_state: Dictionary = SBBotAI.create_state(bot)
	var can_see: bool = bot.can_see(other)
	var rear_before: SBActor = SBBotAI.acquire_target(m, bot, before_state, SBBotAI.profile_for("easy"))
	var alerted: Dictionary = SBBotAI.create_state(bot)
	m._heard = {1: {"position": bot.position + Vector3(0, 0, -8), "time": m._elapsed}}
	SBBotAI._update_auditory_and_team_memory(m, bot, alerted, SBBotAI.profile_for("easy"))
	var rear_after: SBActor = SBBotAI.acquire_target(m, bot, alerted, SBBotAI.profile_for("easy"))
	emit_result("rear_visual_from_unrelated_sound", {"real_los_positive": can_see, "acquired_before": rear_before != null, "acquired_after": rear_after != null, "sound_position": m._heard[1].position, "enemy_position": other.position, "damage_time": alerted.damaged_at})

	# A nearer idle human should not reserve defusing indefinitely. A human
	# actually holding interact is a separate positive control.
	m.objective_state = "planted"
	m.objective_position = m.arena.sites[0]
	bot.position = m.objective_position + Vector3(1.0, 0.05, 0)
	other.actor_id = 7
	other.team = 1
	other.is_bot = false
	other.position = m.objective_position + Vector3(0.4, 0.05, 0)
	m.actors = {6: bot, 7: other}
	m._heard.clear()
	m._team_ai_state = SBBotAI.create_team_state()
	for human_interacting: bool in [false, true]:
		other.input_state = {"interact": human_interacting}
		other.defusing = human_interacting
		var state: Dictionary = SBBotAI.create_state(bot)
		var plan: Dictionary = SBBotAI._select_objective_and_destination(m, bot, state, SBBotAI.profile_for("normal"))
		var selected: int = ai.call("_choose_designated_defuser" if candidate_api else "nearest_defender", m)
		emit_result("idle_human_defuser_priority", {"human_holding_interact": human_interacting, "selected_actor": selected, "bot_interact": plan.interact, "bot_role": state.role})

	# Expected diagnostic failure on candidate: even after explicit actor/match
	# aliases, tick_bot calls apply_tick, which shipped SBActor does not implement.
	m.objective_state = "carried"
	other.alive = false
	m._bot_state = {6: SBBotAI.create_state(bot)}
	m._team_ai_state = SBBotAI.create_team_state()
	bot.input_state = {"sentinel": true}
	print("NATIVE_POLICY_BEGIN tick_bot_actual_actor_method_contract")
	SBBotAI.tick_bot(m, bot, 0.12)
	emit_result("tick_bot_command_sink", {"shipped_actor_has_apply_tick": bot.has_method("apply_tick"), "wrote_actor_input": not bot.input_state.has("sentinel"), "last_cmd_saved": m._bot_state[6].has("last_cmd")})
	m.queue_free()
	await process_frame
	await process_frame
	print("NATIVE_POLICY_COMPLETE errors_in_stderr_are_failures_not_a_pass")
	quit(0)
