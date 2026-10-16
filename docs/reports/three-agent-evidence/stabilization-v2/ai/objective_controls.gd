extends SceneTree

var failures: Array[String] = []

func _initialize() -> void:
	_run.call_deferred()

func check(ok: bool, label: String) -> void:
	print("OBJECTIVE_CONTROL ", label, " pass=", ok)
	if not ok:
		failures.append(label)

func _run() -> void:
	var m := TacticalMatch.new()
	m.configure({"mode": "offline", "difficulty": "normal"})
	root.add_child(m)
	m.set_physics_process(false)
	m.local_id = 0
	for actor: SBActor in m.actors.values():
		actor.alive = false
	var carrier: SBActor = m.actors[1]
	carrier.reset_for_round(m.arena.sites[0])
	m._reset_bot_state(carrier)
	m.phase = "live"
	m.objective_state = "carried"
	m.objective_carrier = 1
	m.time_left = 100.0
	for frame in range(240):
		await physics_frame
		m._elapsed += 1.0 / 60.0
		if frame % 8 == 0:
			m._bot_input(carrier, 0.12)
		carrier.tick_authority(1.0 / 60.0)
		m._objective_tick(1.0 / 60.0)
		if m.objective_state == "planted":
			break
	check(m.objective_state == "planted" and m.objective_contributions.get(1, 0) > 0, "bot_plant_completes_authoritative_timer")
	carrier.alive = false
	var defender: SBActor = m.actors[6]
	defender.reset_for_round(m.objective_position + Vector3(0.4, 0.0, 0.0))
	m._reset_bot_state(defender)
	check(SBBotAI.nearest_defender(m) == 6, "living_defender_selected")
	for frame in range(360):
		await physics_frame
		m._elapsed += 1.0 / 60.0
		if frame % 8 == 0:
			m._bot_input(defender, 0.12)
		defender.tick_authority(1.0 / 60.0)
		m._objective_tick(1.0 / 60.0)
		if m.objective_state == "defused":
			break
	check(m.objective_state == "defused" and m.defend_score == 1, "bot_defuse_completes_authoritative_timer")
	m.local_id = 1
	m.round_number = 2
	m.objective_state = "carried"
	m.objective_carrier = 1
	carrier.alive = true
	carrier.position = m.arena.sites[1]
	var plan_b := SBBotAI.select_round_plan(m, 0)
	check(plan_b.target_site == 1, "human_carrier_at_b_redirects_team_plan")
	carrier.position = m.arena.sites[0]
	var plan_a := SBBotAI.select_round_plan(m, 0)
	check(plan_a.target_site == 0, "human_carrier_at_a_redirects_team_plan")
	m.queue_free()
	await process_frame
	await process_frame
	print("OBJECTIVE_CONTROLS failures=", JSON.stringify(failures))
	quit(0 if failures.is_empty() else 1)
