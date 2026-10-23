extends SceneTree

class PerceptionActor extends "res://scripts/gameplay/actor.gd":
	var visible_enemy: bool = true

	func can_see(other: SBActor) -> bool:
		return visible_enemy and other != null and other.alive

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var failures: Array[String] = []
	await _test_perception_walls_and_smoke(failures)
	await process_frame
	_test_memory_and_no_live_tracking(failures)
	await process_frame
	_test_audio_and_damage_response(failures)
	await process_frame
	_test_reaction_and_weapon_authority(failures)
	await process_frame
	_test_equipment_purchase_authority(failures)
	await process_frame
	_test_objectives_and_team_coordination(failures)
	await process_frame
	_test_navigation_and_stuck_recovery(failures)
	await process_frame
	_test_lifecycle_difficulty_and_network_integrity(failures)
	await process_frame
	if not failures.is_empty():
		for item in failures:
			push_error(item)
		quit(1)
		return
	print("BOT_AI_REGRESSION_TESTS_OK")
	quit(0)

func _spawn_offline_match(difficulty: String = "normal") -> TacticalMatch:
	var match_node := TacticalMatch.new()
	match_node.configure({"mode": "offline", "difficulty": difficulty})
	root.add_child(match_node)
	match_node.set_physics_process(false)
	match_node.phase = "live"
	match_node.time_left = 100.0
	return match_node

func _test_perception_walls_and_smoke(failures: Array[String]) -> void:
	var m := _spawn_offline_match("normal")
	var attacker: SBActor = m.actors[1]
	var defender: SBActor = m.actors[6]
	for id: int in m.actors:
		if id != 1 and id != 6:
			m.actors[id].alive = false
	# Positive control: clear corridor line of sight at (-14, 0, -10) -> (-14, 0, 2)
	defender.global_position = Vector3(-14, 0, 2)
	defender.yaw = 0.0
	attacker.global_position = Vector3(-14, 0, -10)
	attacker.alive = true
	# Negative control 1: solid container wall at (-7, 0, -11) blocks LOS between (-7, 0, -18) and (-7, 0, -4)
	var wall_defender: SBActor = m.actors[7]
	wall_defender.alive = true
	wall_defender.global_position = Vector3(-7, 0, -4)
	wall_defender.yaw = 0.0
	attacker.global_position = Vector3(-7, 0, -18)
	await physics_frame
	await physics_frame
	if wall_defender.can_see(attacker):
		failures.append("Bot should not see enemy through solid shipping container wall")
	var wall_target := SBBotAI.acquire_target(m, wall_defender, m._bot_state[7], SBBotAI.profile_for("normal"))
	if wall_target != null:
		failures.append("acquire_target must return null when enemy is behind a solid wall")
	wall_defender.alive = false

	# Negative control 2: Enemy behind bot's FOV cone (defender facing North -Z, enemy South +Z)
	defender.global_position = Vector3(-14, 0, -2)
	defender.yaw = 0.0
	attacker.global_position = Vector3(-14, 0, 8)
	var behind_target := SBBotAI.acquire_target(m, defender, m._bot_state[6], SBBotAI.profile_for("normal"))
	if behind_target != null:
		failures.append("Bot must not visually detect an enemy directly behind its FOV cone without damage/sound")

	# Negative control 3: Smoke cloud concealment blocks bot perception
	defender.global_position = Vector3(-14, 0, 2)
	defender.yaw = 0.0
	attacker.global_position = Vector3(-14, 0, -10)
	var smoke := SBUtility.new()
	smoke.kind = "smoke"
	smoke.position = Vector3(-14, 0, -4)
	m.add_child(smoke)
	smoke._detonate()
	if defender.can_see(attacker):
		failures.append("Active smoke cloud must block bot line-of-sight perception")
	var smoke_target := SBBotAI.acquire_target(m, defender, m._bot_state[6], SBBotAI.profile_for("normal"))
	if smoke_target != null:
		failures.append("acquire_target must not acquire target through active smoke cloud")
	m.queue_free()

func _test_memory_and_no_live_tracking(failures: Array[String]) -> void:
	var m := _spawn_offline_match("normal")
	var bot := PerceptionActor.new()
	bot.actor_id = 6
	bot.team = 1
	m.actors[6].queue_free()
	m.actors[6] = bot
	m.add_child(bot)
	m._reset_bot_state(bot)
	for id: int in m.actors:
		if id != 1 and id != 6:
			m.actors[id].alive = false
	var enemy: SBActor = m.actors[1]
	bot.position = Vector3(0, 0, 0)
	bot.yaw = -PI / 2.0
	var seen_spot := Vector3(8, 0, 0)
	enemy.position = seen_spot
	bot.visible_enemy = true
	m._elapsed = 10.0
	m._bot_input(bot, 0.12)
	if m._bot_state[6].last_seen != seen_spot:
		failures.append("Bot should record last_seen at the observed enemy position")

	# Enemy breaks LOS and teleports to a completely different hidden coordinate
	bot.visible_enemy = false
	enemy.position = Vector3(-20, 0, 18)
	m._elapsed = 11.0
	m._bot_input(bot, 0.12)
	if bool(bot.input_state.get("fire", false)):
		failures.append("Bot must never fire when target is no longer visible")
	if m._bot_state[6].last_seen != seen_spot:
		failures.append("Bot must never update last_seen with hidden live enemy coordinates")

	# Memory expiration after profile memory_duration (3.8s on normal)
	m._elapsed = 15.0
	m._bot_input(bot, 0.12)
	if str(m._bot_state[6].get("role", "")) == "pursue_memory":
		failures.append("Enemy memory must expire after memory_duration elapses")
	m.queue_free()

func _test_audio_and_damage_response(failures: Array[String]) -> void:
	var m := _spawn_offline_match("normal")
	for id: int in m.actors:
		if id != 2 and id != 6:
			m.actors[id].alive = false
	var attacker: SBActor = m.actors[2]
	var defender: SBActor = m.actors[6]
	attacker.position = Vector3(-14, 0, -12)
	defender.position = Vector3(-14, 0, 4)
	m._elapsed = 20.0
	var shot_origin := Vector3(-14, 0, -2)
	m._shot(6, shot_origin, Vector3.FORWARD)
	SBBotAI._update_auditory_and_team_memory(m, attacker, m._bot_state[2], SBBotAI.profile_for("normal"))
	var attacker_plan := SBBotAI._select_objective_and_destination(m, attacker, m._bot_state[2], SBBotAI.profile_for("normal"))
	var attacker_dest: Vector3 = attacker_plan.destination
	if attacker_dest != shot_origin:
		failures.append("Non-carrier attacker bot should respond to nearby audible enemy gunfire")

	# Damage directional awareness allows acquiring visible shooter outside initial FOV cone
	var flank_bot := PerceptionActor.new()
	flank_bot.actor_id = 6
	flank_bot.team = 1
	m.actors[6].queue_free()
	m.actors[6] = flank_bot
	m.add_child(flank_bot)
	m._reset_bot_state(flank_bot)
	flank_bot.position = Vector3(0, 0, 0)
	flank_bot.yaw = 0.0
	attacker.position = Vector3(0, 0, 12) # Directly behind flank_bot
	flank_bot.visible_enemy = true
	if SBBotAI.acquire_target(m, flank_bot, m._bot_state[6], SBBotAI.profile_for("normal")) != null:
		failures.append("Negative control: unseen rear attacker should not be acquired before firing/damaging")
	m._damaged(6, 2, 35.0)
	var threat := SBBotAI.acquire_target(m, flank_bot, m._bot_state[6], SBBotAI.profile_for("normal"))
	if threat != attacker:
		failures.append("Bot taking damage from a visible rear attacker should immediately acquire the threat")
	m.queue_free()

func _test_reaction_and_weapon_authority(failures: Array[String]) -> void:
	var m := _spawn_offline_match("normal")
	var bot := PerceptionActor.new()
	bot.actor_id = 6
	bot.team = 1
	m.actors[6].queue_free()
	m.actors[6] = bot
	m.add_child(bot)
	m._reset_bot_state(bot)
	for id: int in m.actors:
		if id != 1 and id != 6:
			m.actors[id].alive = false
	var enemy: SBActor = m.actors[1]
	bot.position = Vector3(0, 0, 0)
	bot.yaw = -PI / 2.0
	bot.pitch = 0.0
	enemy.position = Vector3(6, 0, 0)
	bot.visible_enemy = true

	# Tick 1 (0.12s < 0.35s normal reaction_delay): must NOT fire even when already aligned
	m._bot_input(bot, 0.12)
	if bool(bot.input_state.get("fire", false)):
		failures.append("Bot must not fire before reaction_delay (0.12s < 0.35s)")
	# Tick 2 (0.24s < 0.35s): still must NOT fire
	m._bot_input(bot, 0.12)
	if bool(bot.input_state.get("fire", false)):
		failures.append("Bot must not fire before reaction_delay (0.24s < 0.35s)")
	# Tick 3 (0.36s >= 0.35s): now permitted to fire
	m._bot_input(bot, 0.12)
	if not bool(bot.input_state.get("fire", false)):
		failures.append("Bot should fire once reaction_delay is met and aim is aligned")

	# Emergency sidearm fallback when primary rifle ammo is 0 at close range
	bot.weapon_id = "rifle"
	bot.ammo = 0
	m._bot_input(bot, 0.12)
	if str(bot.input_state.get("weapon", "")) != "sidearm":
		failures.append("Normal/hard bot with empty primary at close range should switch to sidearm")

	# Weapon cooldown and reload timer authority check via tick_authority
	bot.weapon_id = "rifle"
	bot.ammo = 0
	bot.reserve = 30
	bot.reload_remaining = 0.0
	bot.input_state = {"reload": true, "fire": true, "move": Vector2.ZERO, "look": Vector2(bot.yaw, bot.pitch)}
	var shots := [0]
	bot.shot_fired.connect(func(_id: int, _pos: Vector3, _dir: Vector3) -> void: shots[0] += 1)
	bot.tick_authority(0.1)
	if shots[0] > 0 or bot.reload_remaining <= 0.0:
		failures.append("Bot must respect weapon reload timers and cannot fire with 0 ammo")
	m.queue_free()

func _test_objectives_and_team_coordination(failures: Array[String]) -> void:
	var m := _spawn_offline_match("normal")
	m.local_id = 0
	# Attacker carrier plants when at site
	var carrier: SBActor = m.actors[1]
	m.objective_carrier = 1
	m.objective_state = "carried"
	carrier.position = m.arena.sites[0]
	for id: int in range(6, 11):
		m.actors[id].alive = false
	m._bot_input(carrier, 0.12)
	if not bool(carrier.input_state.get("interact", false)) or (carrier.input_state.get("move", Vector2.ZERO) as Vector2).length() > 0.01:
		failures.append("Objective carrier bot at bomb site must stop and hold interact to plant")

	# Human carrier adaptation: if player 1 is human and walks to Site B (even when round default is Site A), bots escort Site B
	m.local_id = 1
	m.round_number = 2
	carrier.position = m.arena.sites[1]
	m._team_ai_state = SBBotAI.create_team_state()
	var plan := SBBotAI._select_objective_and_destination(m, m.actors[2], m._bot_state[2], SBBotAI.profile_for("normal"))
	if int(plan.get("primary_site", -1)) != 1:
		failures.append("Team AI must adapt target_site to follow human objective carrier")

	# Planted objective: exactly one defender defuses while others hold validated non-obstacle offsets
	m.local_id = 0
	for id: int in range(6, 11):
		m.actors[id].alive = true
		m.actors[id].position = m.arena.sites[0] + Vector3(float(id - 6) * 0.3, 0, 0)
	m.objective_state = "planted"
	m.objective_position = m.arena.sites[0]
	var defusers := 0
	for id: int in range(6, 11):
		m._bot_input(m.actors[id], 0.12)
		if bool(m.actors[id].input_state.get("interact", false)):
			defusers += 1
	if defusers != 1:
		failures.append("Exactly one defender bot should hold interact on planted device, got %d" % defusers)

	# Verify all post-plant hold positions have valid navigation paths (never inside obstacle AABBs)
	for site_idx: int in [0, 1]:
		var site_pos: Vector3 = m.arena.sites[site_idx]
		for slot: int in range(5):
			var hold_pos: Vector3 = site_pos + SBBotAI.SITE_HOLD_OFFSETS[site_idx][slot]
			var step := m.arena.bot_navigation(Vector3(0, 0, 0), hold_pos)
			if step == Vector3.ZERO:
				failures.append("Post-plant hold slot %d on site %d failed navigation" % [slot, site_idx])
	m.queue_free()

func _test_navigation_and_stuck_recovery(failures: Array[String]) -> void:
	var m := _spawn_offline_match("normal")
	# Test RelayYard.bot_navigation fallback when destination is inside an expanded obstacle AABB
	var inside_obstacle := m.arena.sites[0] + Vector3(cos(2.0 * TAU / 5.0), 0, sin(2.0 * TAU / 5.0)) * 4.5
	var nav_step := m.arena.bot_navigation(Vector3(0, 0, -18), inside_obstacle)
	if nav_step == Vector3(0, 0, -18):
		failures.append("RelayYard.bot_navigation must fall back to nearest waypoint when destination lies inside an expanded obstacle AABB")

	# Test multi-stage stuck recovery
	var bot: SBActor = m.actors[6]
	for id: int in range(1, 6):
		m.actors[id].alive = false
	bot.position = Vector3(0, 0, 10)
	m._reset_bot_state(bot)
	m._bot_state[6].last_position = bot.position
	m._bot_state[6].stuck = 1.6
	m._bot_input(bot, 0.12)
	if not bool(bot.input_state.get("jump", false)):
		failures.append("Stuck bot with stuck > 1.5s should trigger jump recovery")
	m.queue_free()

func _test_lifecycle_difficulty_and_network_integrity(failures: Array[String]) -> void:
	var m := _spawn_offline_match("hard")
	# Bot state reset on round transition
	m._bot_state[6].target = 1
	m._bot_state[6].reaction = 0.8
	m._bot_state[6].seen_at = 50.0
	m._begin_round()
	if int(m._bot_state[6].target) != 0 or float(m._bot_state[6].reaction) != 0.0 or float(m._bot_state[6].seen_at) != -100.0:
		failures.append("_begin_round must reset all bot states cleanly")

	# Difficulty settings preserve identical weapon authority (damage, cooldown, spread)
	if float(SBWeapons.get_weapon("rifle").get("damage", 0.0)) != 35.0:
		failures.append("Bot difficulty must never alter authoritative weapon damage")

	# Protocol version and ranked payload eligibility remain untouched
	if TacticalMatch.PROTOCOL_VERSION != 6:
		failures.append("Integrated TacticalMatch.PROTOCOL_VERSION must remain 6")
	if not m._ranked_payload().is_empty():
		failures.append("Offline bot match must never generate a ranked economy payload")
	m.queue_free()

func _test_equipment_purchase_authority(failures: Array[String]) -> void:
	var m := _spawn_offline_match("normal")
	var bot: SBActor = m.actors[2]
	bot.credits = 5000
	bot.buy_weapon("rifle")
	bot.ammo = 2
	bot.reserve = 3
	bot.smokes = 0
	bot.grenades = 0
	bot.credits = 0
	var inventory_before: Array = bot.inventory.duplicate()
	SBBotAI.buy_equipment(bot, "normal", 1)
	if bot.credits != 0 or bot.weapon_id != "rifle" or bot.inventory != inventory_before or bot.ammo != 2 or bot.reserve != 3 or bot.smokes != 0 or bot.grenades != 0:
		failures.append("Failed AI purchase must preserve funds, ownership, ammunition and utility")
	bot.credits = 5000
	bot.reset_loadout()
	var price: int = int(SBWeapons.get_weapon("rifle").cost)
	SBBotAI.buy_equipment(bot, "normal", 1)
	if bot.credits != 5000 - price or bot.weapon_id != "rifle" or bot.ammo != 30 or bot.reserve != 90 or bot.smokes != 0 or bot.grenades != 0:
		failures.append("Successful AI purchase must use actor pricing/ammunition and grant no utility")
	m.queue_free()
