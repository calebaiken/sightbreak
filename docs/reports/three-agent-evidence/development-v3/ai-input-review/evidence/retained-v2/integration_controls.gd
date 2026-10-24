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

var control_failures: Array[String] = []

func check(ok: bool, label: String) -> void:
	print("CONTROL ", label, " pass=", ok)
	if not ok:
		control_failures.append(label)

func equipment(actor: SBActor) -> Dictionary:
	return {"credits": actor.credits, "weapon": actor.weapon_id, "inventory": actor.inventory.duplicate(), "ammo": actor.ammo, "reserve": actor.reserve, "smokes": actor.smokes, "grenades": actor.grenades}

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
	var profile := SBBotAI.profile_for("normal")
	for condition: Dictionary in [
		{"label": "near_enemy_sound", "distance": 10.0, "age": 1.0, "team": 1, "expected": true},
		{"label": "far_enemy_sound", "distance": 27.0, "age": 1.0, "team": 1, "expected": false},
		{"label": "expired_enemy_sound", "distance": 10.0, "age": 3.6, "team": 1, "expected": false},
		{"label": "ally_sound", "distance": 10.0, "age": 1.0, "team": 0, "expected": false}
	]:
		enemy.team = condition.team
		var event_pos: Vector3 = bot.position + Vector3(condition.distance, 0, 0)
		m._heard = {6: {"position": event_pos, "time": m._elapsed - float(condition.age)}}
		var state := SBBotAI.create_state(bot)
		var dest := SBBotAI.select_destination(m, bot, state, profile)
		check((dest == event_pos) == bool(condition.expected), condition.label)
	enemy.team = 1
	m._heard.clear()
	m._bot_state[3] = SBBotAI.create_state(bot)
	var remembered := Vector3(8, 0, 0)
	m._bot_state[3].last_seen = remembered
	m._bot_state[3].seen_at = m._elapsed - 1.0
	enemy.position = Vector3(-20, 0, 18)
	bot.sees_enemies = false
	SBBotAI.compute_bot_input(m, bot, 0.12)
	check(m._bot_state[3].role == "pursue_memory", "memory_positive_pursuit")
	var hidden_input := bot.input_state.duplicate(true)
	enemy.position = Vector3(20, 0, 18)
	SBBotAI.compute_bot_input(m, bot, 0.12)
	check(bot.input_state == hidden_input and m._bot_state[3].last_seen == remembered, "hidden_live_motion_does_not_change_input")
	check(not bool(bot.input_state.fire), "hidden_enemy_not_fired_on")
	m._elapsed += 4.0
	SBBotAI.compute_bot_input(m, bot, 0.12)
	check(m._bot_state[3].role != "pursue_memory" and bot.input_state.look != hidden_input.look, "memory_expires_changes_behavior")
	m._bot_state[3] = SBBotAI.create_state(bot)
	m._team_ai_state[0].contacts = {6: {"position": remembered, "time": m._elapsed, "reporter": 1}}
	SBBotAI._update_auditory_and_team_memory(m, bot, m._bot_state[3], profile)
	check(m._bot_state[3].heard_pos == remembered, "team_report_positive")
	var expired := SBBotAI.create_state(bot)
	m._elapsed += 4.0
	SBBotAI._update_auditory_and_team_memory(m, bot, expired, profile)
	check(expired.heard_at == -100.0, "team_report_expiration")
	var easy := SBBotAI.create_state(bot)
	m._elapsed -= 4.0
	SBBotAI._update_auditory_and_team_memory(m, bot, easy, SBBotAI.profile_for("easy"))
	check(easy.heard_at == -100.0, "easy_ignores_team_reports")
	m._team_ai_state = SBBotAI.create_team_state()

	var arena := RelayYard.new()
	root.add_child(arena)
	var real_bot := SBActor.new()
	real_bot.configure(6, 1, "IndependentBot")
	root.add_child(real_bot)
	var real_enemy := SBActor.new()
	real_enemy.configure(3, 0, "IndependentEnemy")
	root.add_child(real_enemy)
	real_bot.position = Vector3(-14, 0, 2)
	real_bot.yaw = 0.0
	real_enemy.position = Vector3(-14, 0, -10)
	await physics_frame
	await physics_frame
	m.arena = arena
	m.actors = {6: real_bot, 3: real_enemy}
	m._bot_state = {6: SBBotAI.create_state(real_bot)}
	check(real_bot.can_see(real_enemy), "native_clear_corridor_los_positive")
	check(SBBotAI.acquire_target(m, real_bot, m._bot_state[6], profile) == real_enemy, "native_clear_corridor_acquisition_positive")
	var cloud := SBUtility.new()
	cloud.kind = "smoke"
	root.add_child(cloud)
	cloud.position = Vector3(-14, 0, -4)
	cloud._detonate()
	check(not real_bot.can_see(real_enemy) and SBBotAI.acquire_target(m, real_bot, m._bot_state[6], profile) == null, "native_smoke_occlusion_negative")
	cloud.free()
	check(real_bot.can_see(real_enemy), "native_smoke_removal_restores_los")
	real_bot.position = Vector3(-7, 0, -4)
	real_enemy.position = Vector3(-7, 0, -18)
	await physics_frame
	await physics_frame
	check(not real_bot.can_see(real_enemy), "native_wall_occlusion_negative")
	real_bot.position = Vector3(-14, 0, -2)
	real_enemy.position = Vector3(-14, 0, 8)
	await physics_frame
	await physics_frame
	check(real_bot.can_see(real_enemy) and SBBotAI.acquire_target(m, real_bot, m._bot_state[6], profile) == null, "native_rear_fov_negative_with_clear_los")
	SBBotAI.record_damage(m._bot_state, m.actors, 6, 3, m._elapsed)
	check(SBBotAI.acquire_target(m, real_bot, m._bot_state[6], profile) == real_enemy, "native_visible_rear_damage_positive")

	real_bot.credits = 0
	real_bot.weapon_id = "rifle"
	real_bot.inventory.assign(["sidearm", "rifle"])
	real_bot.ammo = 2
	real_bot.reserve = 3
	real_bot.smokes = 0
	real_bot.grenades = 0
	var before := equipment(real_bot)
	check(not real_bot.buy_weapon("smg") and equipment(real_bot) == before, "failed_player_purchase_changes_no_resources")
	SBBotAI.buy_equipment(real_bot, "normal", 2)
	var after := equipment(real_bot)
	print("AUTHORITY_REPAIR before=", JSON.stringify(before), " after=", JSON.stringify(after))
	check(after == before, "repaired_bot_failed_purchase_preserves_resources")
	real_bot.reset_loadout()
	real_bot.reset_for_round(Vector3(-15, 0.05, 9))
	check(real_bot.inventory == ["sidearm"] and real_bot.ammo == 15 and real_bot.reserve == 60, "existing_reset_loadout_and_round_reset_contract")

	real_enemy.free()
	m.actors = {6: real_bot}
	m._heard.clear()
	m.objective_state = "carried"
	m._bot_state = {6: SBBotAI.create_state(real_bot)}
	var begin := real_bot.position
	for frame in range(600):
		await physics_frame
		if frame % 8 == 0:
			SBBotAI.compute_bot_input(m, real_bot, 0.12)
		real_bot.tick_authority(1.0 / 60.0)
	print("NATIVE_BLOCKED_ANCHOR from=", begin, " final=", real_bot.position, " move=", real_bot.input_state.move, " stuck=", m._bot_state[6].stuck)
	check(Vector2(real_bot.position.x - begin.x, real_bot.position.z - begin.z).length() < 1.0 and real_bot.position.distance_to(SBBotAI.DEFENDER_ANCHORS[0]) > 1.8, "reproduced_blocked_anchor_actual_actor_no_arrival_after_10s")
	real_bot.actor_id = 8
	m.actors = {8: real_bot}
	m._bot_state = {8: SBBotAI.create_state(real_bot)}
	var movable_begin := real_bot.position
	for frame in range(120):
		await physics_frame
		if frame % 8 == 0:
			SBBotAI.compute_bot_input(m, real_bot, 0.12)
		real_bot.tick_authority(1.0 / 60.0)
	print("NATIVE_REACHABLE_ANCHOR from=", movable_begin, " final=", real_bot.position)
	check(Vector2(real_bot.position.x - movable_begin.x, real_bot.position.z - movable_begin.z).length() > 1.0, "native_actor_movement_positive_control")
	real_bot.free()
	arena.free()
	m.free()
	await process_frame
	await process_frame
	print("INDEPENDENT_CONTROLS failures=", JSON.stringify(control_failures))
	quit(0 if control_failures.is_empty() else 1)
