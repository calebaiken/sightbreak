extends SceneTree

# This probe loads the frozen bot_ai.gd unchanged. ProbeActor exposes the
# missing smoke_charges alias solely to reach downstream logic after the
# separately reproduced actor-property integration failure.
class ProbeActor extends SBActor:
	var smoke_charges: int = 0
	var sees_enemies: bool = false
	func _ready() -> void:
		pass
	func can_see(other: SBActor) -> bool:
		return sees_enemies and other.alive

class ProbeArena extends RelayYard:
	func _ready() -> void:
		pass
	func bot_navigation(_from: Vector3, to: Vector3) -> Vector3:
		return to
	func _clear_path(_from: Vector3, _to: Vector3) -> bool:
		return true

class ProbeMatch extends Node3D:
	var actors: Dictionary = {}
	var _bot_state: Dictionary = {}
	var _team_ai_state: Dictionary = SBBotAI.create_team_state()
	var _heard: Dictionary = {}
	var _elapsed: float = 10.0
	var _rng := RandomNumberGenerator.new()
	var phase: String = "live"
	var time_left: float = 100.0
	var round_number: int = 1
	var objective_state: String = "carried"
	var objective_carrier: int = 1
	var objective_position := Vector3.ZERO
	var options: Dictionary = {"difficulty": "normal"}
	var arena: RelayYard
	func _is_bot(id: int) -> bool:
		return id != 1

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var m := ProbeMatch.new()
	m.arena = ProbeArena.new()
	m.add_child(m.arena)
	root.add_child(m)
	var bot := ProbeActor.new()
	bot.actor_id = 3
	bot.team = 0
	bot.position = Vector3(0, 0, -10)
	m.add_child(bot)
	var enemy := ProbeActor.new()
	enemy.actor_id = 6
	enemy.team = 1
	enemy.position = Vector3(10, 0, -10)
	m.add_child(enemy)
	m.actors = {3: bot, 6: enemy}
	m._bot_state[3] = SBBotAI.create_state(bot)
	SBBotAI.compute_bot_input(m, bot, 0.12)
	var undamaged: Dictionary = bot.input_state.duplicate(true)
	m._bot_state[3] = SBBotAI.create_state(bot)
	SBBotAI.record_damage(m._bot_state, m.actors, 3, 6, m._elapsed)
	SBBotAI.compute_bot_input(m, bot, 0.12)
	print("DAMAGE_DIRECTION baseline_look=", undamaged.look, " damaged_look=", bot.input_state.look,
		" direction_yaw=", -PI / 2.0, " equal=", undamaged.look == bot.input_state.look)
	m._bot_state[3] = SBBotAI.create_state(bot)
	var before: Dictionary = SBBotAI._select_objective_and_destination(m, bot, m._bot_state[3], SBBotAI.profile_for("normal"))
	m._heard = {6: {"position": Vector3(10, 0, -10), "time": m._elapsed}}
	SBBotAI._update_auditory_and_team_memory(m, bot, m._bot_state[3], SBBotAI.profile_for("normal"))
	var after: Dictionary = SBBotAI._select_objective_and_destination(m, bot, m._bot_state[3], SBBotAI.profile_for("normal"))
	print("ATTACKER_AUDIO heard=", m._bot_state[3].heard_pos, " before=", before.destination,
		" after=", after.destination, " ignored=", before.destination == after.destination)
	for difficulty in ["easy", "normal", "hard"]:
		m._bot_state[3] = SBBotAI.create_state(bot)
		SBBotAI._update_auditory_and_team_memory(m, bot, m._bot_state[3], SBBotAI.profile_for(difficulty))
		print("SOUND_PRECISION difficulty=", difficulty, " heard=", m._bot_state[3].heard_pos,
			" exact=", m._bot_state[3].heard_pos == m._heard[6].position)
	bot.team = 1
	bot.actor_id = 6
	enemy.actor_id = 3
	enemy.team = 0
	m.actors = {6: bot, 3: enemy}
	m._heard = {3: {"position": bot.position + Vector3(20, 0, 0), "time": m._elapsed}}
	var easy_state := SBBotAI.create_state(bot)
	SBBotAI._update_auditory_and_team_memory(m, bot, easy_state, SBBotAI.profile_for("easy"))
	var easy_plan := SBBotAI._select_objective_and_destination(m, bot, easy_state, SBBotAI.profile_for("easy"))
	print("EASY_HEARING declared_range=", SBBotAI.profile_for("easy").hearing_range,
		" heard_at=", easy_state.heard_at, " sound_distance=20 destination=", easy_plan.destination,
		" raw_sound=", m._heard[3].position, " bypassed=", easy_plan.destination == m._heard[3].position)
	var real_arena := RelayYard.new()
	root.add_child(real_arena)
	await physics_frame
	for anchor: Vector3 in SBBotAI.DEFENDER_ANCHORS:
		if not real_arena._clear_path(anchor, anchor + Vector3(0.01, 0.0, 0.01)):
			print("BLOCKED_DEFENDER_ANCHOR ", anchor)
	for pair: Array in [[Vector3(-15, 0, 9), Vector3(-15, 0, 12)], [Vector3(0, 0, 12), Vector3(0, 0, 9)]]:
		var wp: Vector3 = SBBotAI.safe_navigate(real_arena, pair[0], pair[1])
		print("BLOCKED_ANCHOR_NAV from=", pair[0], " target=", pair[1], " step=", wp, " no_progress=", wp == pair[0])
	real_arena.free()
	m.free()
	quit(0)
