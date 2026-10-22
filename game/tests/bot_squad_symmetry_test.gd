extends SceneTree
## Real-engine command oracle. --observe saves the deliberately failing baseline.
## Paired actors are assigned equal roles/poses; this is an artificial fixture.
const DT := 0.12
var m: TacticalMatch
var checks := 0
var failures: Array[String] = []
var observe := false
var samples := 0

func _initialize() -> void:
	observe = OS.get_cmdline_user_args().has("--observe")
	_run.call_deferred()

func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures.append(message)
		if not observe: push_error(message)

func _run() -> void:
	print("BOT_SQUAD_SYMMETRY engine=%s observe=%s" % [Engine.get_version_info().string, observe])
	m = TacticalMatch.new()
	m.configure({"mode": "offline", "difficulty": "normal"})
	root.add_child(m)
	m.set_physics_process(false)
	m.local_id = 0
	for difficulty in ["easy", "normal", "hard"]:
		for team in [0, 1]:
			for kind in ["close", "long", "travel", "stuck", "stuck_low", "stuck_jump", "idle", "smoke", "spent_smoke", "empty_smoke", "smoke_near", "smoke_far", "carrier_smoke", "carrier", "defuser", "cover"]:
				for slot in range(5):
					var a := await _sample(slot + 1, difficulty, team, kind)
					var b := await _sample(slot + 6, difficulty, team, kind)
					check(a == b, "%s team=%d %s slot=%d paired full command/role/destination" % [difficulty, team, kind, slot])
	await _inactive_controls()
	check(TacticalMatch.PROTOCOL_VERSION == 6, "protocol 6 is preserved")
	check(m._ranked_payload().is_empty(), "offline commands produce no ranked payload")
	m.queue_free()
	await process_frame
	await create_timer(0.6).timeout
	for failure in failures: print("BOT_SQUAD_FAILURE " + failure)
	print("BOT_SQUAD_SYMMETRY_RESULT samples=%d checks=%d failures=%d mode=%s" % [samples, checks, failures.size(), "observation" if observe else "assertion"])
	quit(0 if observe or failures.is_empty() else 1)

func _sample(id: int, difficulty: String, team: int, kind: String) -> Dictionary:
	m.options.difficulty = difficulty
	m.phase = "live"
	m.time_left = 100
	m.round_number = 2
	m._elapsed = 20.0
	m._rng.seed = 739
	m._heard.clear()
	m._team_ai_state = SBBotAI.create_team_state()
	m.objective_state = "carried"
	m.objective_carrier = 0
	m.objective_position = m.arena.sites[0]
	for other: SBActor in m.actors.values():
		other.alive = false
		other.position = Vector3(100 + other.actor_id * 4, 0, 100)
	var bot: SBActor = m.actors[id]
	bot.team = team
	bot.reset_for_round(Vector3(-14, 0, -10))
	bot.yaw = PI
	bot.pitch = 0
	m._reset_bot_state(bot)
	var state: Dictionary = m._bot_state[id]
	var slot := (id - 1) % 5
	var target_id := 10 if id <= 5 else 5
	var enemy: SBActor = m.actors[target_id]
	if kind in ["close", "long"]:
		enemy.team = 1 - team
		enemy.reset_for_round(Vector3(-14, 0, 2))
		if kind == "long":
			bot.position = Vector3(-22, 0, -18)
			enemy.position = Vector3(-22, 0, 8)
	elif kind in ["smoke", "spent_smoke", "empty_smoke", "smoke_near", "smoke_far", "carrier_smoke"]:
		bot.position = m.arena.sites[0] + Vector3(0, 0, -8)
		if team == 1: m.objective_state = "planted"
		if kind == "spent_smoke": state.smoke_used = true
		if kind == "empty_smoke": bot.smokes = 0
		if kind == "smoke_near": bot.position = m.arena.sites[0] + Vector3(0, 0, -5.0 if team == 0 else -3.5)
		if kind == "smoke_far": bot.position = m.arena.sites[0] + Vector3(0, 0, -14.0 if team == 0 else -11.0)
		if kind == "carrier_smoke" and team == 0: m.objective_carrier = id
	elif kind == "carrier":
		m.objective_carrier = id
		bot.position = m.arena.sites[0]
	elif kind in ["defuser", "cover"]:
		m.objective_state = "planted"
		bot.position = m.arena.sites[0] + Vector3(0, 0, 2)
		if kind == "cover" and team == 1:
			enemy.team = 1
			enemy.reset_for_round(m.arena.sites[0])
	elif kind == "idle":
		# Escorts choose a hold offset once at the site; settle that second plan too.
		for iteration in range(2):
			var idle_plan := SBBotAI._select_objective_and_destination(m, bot, state, SBBotAI.profile_for(difficulty))
			bot.position = idle_plan.destination
		# Center on the scan approach to expose the phase rather than a 180-degree turn.
		var approach := Vector3(0, 0, -18) if team == 1 else Vector3(0, 0, 20)
		var toward := approach - bot.position
		bot.yaw = atan2(-toward.x, -toward.z)
	state.last_position = bot.position
	if kind == "stuck": state.stuck = 1.9
	if kind == "stuck_low": state.stuck = 0.7
	if kind == "stuck_jump": state.stuck = 1.5
	await physics_frame
	await physics_frame
	if kind in ["close", "long"]:
		check(bot.can_see(enemy), "%s id=%d %s actual clear LOS" % [difficulty, id, kind])
	var protected_before := [bot.health, bot.ammo, bot.reserve, bot.credits, bot.smokes, bot.grenades]
	var plan := SBBotAI._select_objective_and_destination(m, bot, state, SBBotAI.profile_for(difficulty))
	m._bot_input(bot, DT)
	check(protected_before == [bot.health, bot.ammo, bot.reserve, bot.credits, bot.smokes, bot.grenades], "%s id=%d %s decision leaves authority state untouched" % [difficulty, id, kind])
	var command := bot.input_state.duplicate()
	var role := str(state.role)
	if kind == "close":
		check(int(state.target) == target_id and not command.fire, "%s id=%d close acquires real enemy before reaction" % [difficulty, id])
		check(command.crouch == (slot % 3 == 0), "%s id=%d close habit crouch" % [difficulty, id])
	elif kind == "long":
		check(int(state.target) == target_id, "%s id=%d long acquires real enemy" % [difficulty, id])
		check(command.crouch == (slot % 3 == 0 or difficulty != "easy"), "%s id=%d long difficulty crouch" % [difficulty, id])
		if difficulty != "easy": check(command.move == Vector2.ZERO, "%s id=%d long brakes" % [difficulty, id])
	elif kind == "smoke":
		var expected := difficulty != "easy" and (team == 1 or slot % 2 == 0)
		check(command.smoke == expected, "%s id=%d team=%d utility role gate" % [difficulty, id, team])
	elif kind in ["spent_smoke", "empty_smoke", "smoke_near", "smoke_far"]:
		check(not command.smoke, "%s id=%d %s suppresses smoke" % [difficulty, id, kind])
	elif kind == "carrier_smoke":
		check(command.smoke == (difficulty != "easy"), "%s id=%d carrier utility exception" % [difficulty, id])
	elif kind == "stuck":
		check(command.jump and is_equal_approx(command.move.x, 1.0 if slot % 2 == 0 else -1.0) and is_equal_approx(command.move.y, -0.6), "%s id=%d stuck recovery" % [difficulty, id])
	elif kind == "stuck_low":
		check(not command.jump and command.move == Vector2(0, 1), "%s id=%d below recovery threshold" % [difficulty, id])
	elif kind == "stuck_jump":
		check(command.jump and is_equal_approx(command.move.x, 1.0 if slot % 2 == 0 else -1.0) and is_equal_approx(command.move.y, 1.0), "%s id=%d jump before reverse threshold" % [difficulty, id])
	elif kind == "idle":
		check(command.move == Vector2.ZERO, "%s id=%d idle fixture actually scans without moving" % [difficulty, id])
	elif kind == "carrier" and team == 0:
		check(role == "carrier" and command.interact and command.move == Vector2.ZERO and not command.fire and not command.smoke, "%s id=%d carrier stops to plant" % [difficulty, id])
	elif kind == "defuser" and team == 1:
		check(role == "defuser" and command.interact and command.move == Vector2.ZERO, "%s id=%d nearest defender stops to defuse" % [difficulty, id])
	elif kind == "cover" and team == 1:
		check(role == "retake_cover" and not command.interact, "%s id=%d farther defender covers" % [difficulty, id])
	if kind == "travel" and team == 1:
		var expected_destination: Vector3 = m.arena.sites[slot % 2] if difficulty == "easy" else SBBotAI.DEFENDER_ANCHORS[slot]
		check(role == "anchor" and plan.destination == expected_destination, "%s id=%d defender slot destination" % [difficulty, id])
	# Normalize only ID-valued target bookkeeping; every emitted input field is compared.
	var result := {"command": command, "role": role, "destination": plan.destination}
	print("BOT_SQUAD_SAMPLE " + JSON.stringify({"id": id, "slot": slot, "difficulty": difficulty, "team": team, "kind": kind, "output": result}))
	if kind == "smoke" and difficulty != "easy" and (team == 1 or slot % 2 == 0):
		check(bool(state.smoke_used), "%s id=%d smoke decision marks used state" % [difficulty, id])
		m._bot_input(bot, DT)
		check(not bot.input_state.smoke, "%s id=%d repeat decision suppresses second smoke" % [difficulty, id])
		m._reset_bot_state(bot)
		m._bot_input(bot, DT)
		check(bot.input_state.smoke, "%s id=%d real bot state reset re-arms smoke" % [difficulty, id])
	if kind == "close":
		var first_fire := 1 if command.fire else 0
		for tick in range(2, 7):
			if first_fire > 0: break
			m._bot_input(bot, DT)
			if bot.input_state.fire: first_fire = tick
		check(first_fire == {"easy": 5, "normal": 3, "hard": 2}[difficulty], "%s id=%d actual reaction cadence first fire tick=%d" % [difficulty, id, first_fire])
	samples += 1
	return result

func _inactive_controls() -> void:
	var bot: SBActor = m.actors[1]
	for phase_value in ["buy", "post", "match_over"]:
		m.phase = phase_value
		bot.input_state = {"sentinel": true}
		m._bot_input(bot, DT)
		check(bot.input_state == {"sentinel": true}, "%s phase does not compute bot command" % phase_value)
	m.phase = "live"
	bot.alive = false
	bot.input_state = {"sentinel": true}
	m._bot_input(bot, DT)
	check(bot.input_state == {"sentinel": true}, "dead bot does not compute command")
