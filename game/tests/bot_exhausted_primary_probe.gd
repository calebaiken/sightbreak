extends SceneTree
## Diagnostic common fixture. It asserts authority laws, not a new switch policy.
const DT := 0.12
const SEED := 52039
const PRIMARIES := ["smg", "rifle", "marksman"]
const DIFFICULTIES := ["easy", "normal", "hard"]
const TARGETS := [
	{"name": "near", "distance": 6.0, "visible": true},
	{"name": "fallback_boundary", "distance": 20.0, "visible": true},
	{"name": "far", "distance": 24.0, "visible": true},
	{"name": "outside_sidearm", "distance": 45.5, "visible": true},
	{"name": "outside_vision", "distance": 60.0, "visible": true},
	{"name": "no_target", "distance": 6.0, "visible": false}
]

class VisibilityActor extends "res://scripts/gameplay/actor.gd":
	var visible_enemy := false

	func can_see(other: SBActor) -> bool:
		return visible_enemy and other != null and other.alive

var m: TacticalMatch
var bot: VisibilityActor
var enemy: SBActor
var shots: Array[Dictionary] = []
var damage_events: Array[Dictionary] = []
var elimination_events: Array[Dictionary] = []
var event_serial := 0
var failures: Array[String] = []
var checks := 0
var matrix_cases := 0
var sequence_steps := 0
var sequences := 0
var control_steps := 0
var control_summaries: Array[Dictionary] = []
var pose_settle := {}

func _initialize() -> void:
	_run.call_deferred()

func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures.append(message)

func _json_value(value: Variant) -> Variant:
	if value is Vector2 or value is Vector2i:
		return [value.x, value.y]
	if value is Vector3:
		return [value.x, value.y, value.z]
	if value is Color:
		return [value.r, value.g, value.b, value.a]
	if value is Array:
		var result: Array = []
		for item in value:
			result.append(_json_value(item))
		return result
	if value is Dictionary:
		var result := {}
		for key in value:
			result[str(key)] = _json_value(value[key])
		return result
	return value

func emit_row(kind: String, value: Dictionary) -> void:
	print("BOT_EXHAUSTED_" + kind + " " + JSON.stringify(_json_value(value)))

func _run() -> void:
	emit_row("HEADER", {"engine": Engine.get_version_info(), "dt": DT, "seed": SEED,
		"weapon_definitions": SBWeapons.DATA, "profiles": SBBotAI.PROFILES,
		"matrix_cases_expected": 567, "sequences_expected": 72, "sequence_steps_expected": 576,
		"positive_controls_expected": 5, "control_steps_expected": 96,
		"visibility": "injected; production FOV and vision-range acquisition still run",
		"consumer": "production tick_authority_actions; no movement tick or full match"})
	m = TacticalMatch.new()
	m.configure({"mode": "offline", "difficulty": "normal"})
	root.add_child(m)
	m.set_physics_process(false)
	m.local_id = 0
	m.actors[6].free()
	bot = VisibilityActor.new()
	bot.actor_id = 6
	m.actors[6] = bot
	m.add_child(bot)
	# Match the stock _spawn_actor callback wiring before adding probe recorders.
	bot.eliminated.connect(m._eliminated)
	bot.damage_taken.connect(m._damaged)
	bot.shot_fired.connect(m._shot)
	bot.hit_confirmed.connect(m._confirmed_hit)
	bot.impact_created.connect(m._confirmed_impact)
	bot.shot_fired.connect(_record_shot)
	enemy = m.actors[1]
	enemy.damage_taken.connect(_record_target_damage)
	enemy.eliminated.connect(_record_target_elimination)
	for difficulty in DIFFICULTIES:
		for primary in PRIMARIES:
			for target in TARGETS:
				for active in ["exhausted", "reloadable"]:
					for sidearm in ["loaded", "dry", "unknown"]:
						await _case("core", difficulty, primary, active, sidearm, target)
				await _case("loaded_primary", difficulty, primary, "loaded", "loaded", target)
			for target in [TARGETS[0], TARGETS[2], TARGETS[5]]:
				await _case("reserve_only_sidearm", difficulty, primary, "exhausted", "reserve_only", target)
				await _case("unowned_sidearm", difficulty, primary, "exhausted", "unowned", target)
				for active in ["exhausted", "reloadable", "loaded"]:
					await _case("stale_active_cache", difficulty, primary, active, "loaded", target, "none", true)
				for objective in ["carrier", "defuser"]:
					await _case("objective_guard", difficulty, primary, "exhausted", "loaded", target, objective)
			for setting in [
				{"name": "idle_loaded", "target": TARGETS[5], "sidearm": "loaded", "active": "exhausted"},
				{"name": "far_loaded", "target": TARGETS[2], "sidearm": "loaded", "active": "exhausted"},
				{"name": "near_loaded", "target": TARGETS[0], "sidearm": "loaded", "active": "exhausted"},
				{"name": "outside_sidearm_loaded", "target": TARGETS[3], "sidearm": "loaded", "active": "exhausted"},
				{"name": "far_dry", "target": TARGETS[2], "sidearm": "dry", "active": "exhausted"},
				{"name": "idle_unknown", "target": TARGETS[5], "sidearm": "unknown", "active": "exhausted"},
				{"name": "far_reloadable_primary", "target": TARGETS[2], "sidearm": "loaded", "active": "reloadable"},
				{"name": "near_reserve_only_sidearm", "target": TARGETS[0], "sidearm": "reserve_only", "active": "exhausted"}
			]:
				await _sequence(difficulty, primary, setting)
	await _positive_controls()
	check(matrix_cases == 567, "all registered matrix cases completed")
	check(sequences == 72 and sequence_steps == 576, "all registered sequence steps completed")
	check(control_summaries.size() == 5 and control_steps == 96, "all mandatory positive controls completed")
	check(TacticalMatch.PROTOCOL_VERSION == 6, "protocol remains 6")
	check(m._ranked_payload().is_empty(), "offline probe has no ranked payload")
	m.queue_free()
	await process_frame
	for failure in failures:
		print("BOT_EXHAUSTED_FAILURE " + failure)
	emit_row("RESULT", {"matrix_cases": matrix_cases, "sequences": sequences,
		"sequence_steps": sequence_steps, "positive_controls": control_summaries,
		"control_steps": control_steps, "checks": checks, "failures": failures,
		"authority_checks_passed": failures.is_empty(),
		"behavior_acceptance": "diagnostic only; no new selection policy asserted"})
	quit(0 if failures.is_empty() else 1)

func _record_shot(_id: int, origin: Vector3, direction: Vector3) -> void:
	event_serial += 1
	shots.append({"serial": event_serial, "weapon": bot.weapon_id, "origin": origin, "direction": direction,
		"ammo_after_shot": bot.ammo, "reserve": bot.reserve})

func _record_target_damage(victim: int, attacker: int, amount: float) -> void:
	event_serial += 1
	damage_events.append({"serial": event_serial, "victim": victim, "attacker": attacker,
		"amount": amount, "victim_state": _enemy_snapshot()})

func _record_target_elimination(victim: int, killer: int) -> void:
	event_serial += 1
	elimination_events.append({"serial": event_serial, "victim": victim, "killer": killer,
		"victim_state": _enemy_snapshot(), "shooter_state": _snapshot()})

func _spec(difficulty: String, primary: String, active: String, sidearm: String,
		target: Dictionary, objective: String = "none", stale: bool = false) -> Dictionary:
	return {"difficulty": difficulty, "primary": primary, "active_resource": active,
		"sidearm_resource": sidearm, "target": target.duplicate(), "objective": objective,
		"stale_active_cache": stale}

func _prepare(s: Dictionary) -> void:
	m.options.difficulty = s.difficulty
	m.phase = "live"
	m.round_number = 2
	m.time_left = 100.0
	m._elapsed = 20.0
	m._rng.seed = SEED
	m._heard.clear()
	m._damage_history.clear()
	m._last_activity.clear()
	m._team_ai_state = SBBotAI.create_team_state()
	m.objective_state = "planted" if s.objective == "defuser" else "carried"
	m.objective_timer = 0.0
	m.interaction_progress = 0.0
	m._interactions.clear()
	m.objective_carrier = 6 if s.objective == "carrier" else 0
	m.objective_position = m.arena.sites[0]
	for other: SBActor in m.actors.values():
		other.alive = false
		other.position = Vector3(100 + other.actor_id * 4, 0, 100)
	bot.team = 0 if s.objective == "carrier" else 1
	bot.inventory.assign([s.primary] if s.sidearm_resource == "unowned" else ["sidearm", s.primary])
	if bot.weapon_id != s.primary:
		bot._equip(s.primary)
	var distance: float = float(s.target.distance)
	var direction := Vector3.RIGHT
	var spawn := Vector3(-distance * 0.5, 0, -20)
	if distance > 45.5:
		direction = Vector3(1, 0, 1).normalized()
		spawn = -direction * distance * 0.5
	if s.objective != "none":
		spawn = m.arena.sites[0]
		direction = Vector3.RIGHT
	bot.reset_for_round(spawn)
	bot._ammo_store.clear()
	match s.sidearm_resource:
		"loaded":
			bot._ammo_store["sidearm"] = Vector2i(15, 0)
		"reserve_only":
			bot._ammo_store["sidearm"] = Vector2i(0, 15)
		"dry":
			bot._ammo_store["sidearm"] = Vector2i.ZERO
	bot.ammo = 1 if s.active_resource == "loaded" else 0
	bot.reserve = int(SBWeapons.get_weapon(s.primary).magazine) if s.active_resource == "reloadable" else 0
	if s.stale_active_cache:
		var definition: Dictionary = SBWeapons.get_weapon(s.primary)
		bot._ammo_store[s.primary] = Vector2i(int(definition.magazine), int(definition.reserve)) if s.active_resource == "exhausted" else Vector2i.ZERO
	bot.alive = true
	bot.health = 100
	bot.credits = 800
	bot.kills = 0
	bot.assists = 0
	bot.deaths = 0
	bot.grenades = 0
	bot.smokes = 0
	bot.reload_remaining = 0.0
	bot._deploy_remaining = 0.0
	bot._weapon_cooldowns.clear()
	bot._fire_previous = false
	bot.recoil = Vector2.ZERO
	bot.velocity = Vector3.ZERO
	bot._crouching = false
	bot._rng.seed = SEED
	bot.input_state.clear()
	bot.position = spawn
	bot.yaw = atan2(-direction.x, -direction.z)
	bot.rotation.y = bot.yaw
	bot.pitch = atan2(-0.35, distance)
	bot.visible_enemy = bool(s.target.visible)
	enemy.team = 1 - bot.team
	enemy.reset_for_round(spawn + direction * distance)
	enemy.credits = 800
	enemy.kills = 0
	enemy.assists = 0
	enemy.deaths = 0
	m._reset_bot_state(bot)

func _snapshot() -> Dictionary:
	return _actor_snapshot(bot)

func _actor_snapshot(actor: SBActor) -> Dictionary:
	return {"actor_id": actor.actor_id, "team": actor.team, "weapon": actor.weapon_id,
		"ammo": actor.ammo, "reserve": actor.reserve,
		"reload": actor.reload_remaining, "deploy": actor._deploy_remaining,
		"cooldowns": actor._weapon_cooldowns.duplicate(true), "inventory": actor.inventory.duplicate(),
		"ammo_store": actor._ammo_store.duplicate(true), "health": actor.health, "alive": actor.alive,
		"credits": actor.credits, "kills": actor.kills, "assists": actor.assists, "deaths": actor.deaths,
		"grenades": actor.grenades, "smokes": actor.smokes,
		"recoil": actor.recoil, "position": actor.position, "velocity": actor.velocity,
		"yaw": actor.yaw, "pitch": actor.pitch, "fire_previous": actor._fire_previous,
		"floor_contact": actor.is_on_floor(), "crouching": actor._crouching,
		"actual_action_spread": actor.current_spread(not actor.is_on_floor())}

func _enemy_snapshot() -> Dictionary:
	var result := _actor_snapshot(enemy)
	result["input_state"] = enemy.input_state.duplicate(true)
	return result

func _objective_snapshot() -> Dictionary:
	return {"phase": m.phase, "round": m.round_number, "attack_score": m.attack_score,
		"defend_score": m.defend_score, "time_left": m.time_left, "state": m.objective_state,
		"timer": m.objective_timer, "progress": m.interaction_progress, "position": m.objective_position,
		"carrier": m.objective_carrier, "contributions": m.objective_contributions.duplicate(true),
		"interactions": m._interactions.duplicate(true), "elapsed": m._elapsed, "tick": m._simulation_tick}

func _settle_pose() -> void:
	var before := Engine.get_physics_frames()
	await physics_frame
	await physics_frame
	pose_settle = {"barriers": 2, "before_frame": before, "after_frame": Engine.get_physics_frames()}
	check(int(pose_settle.after_frame) > int(pose_settle.before_frame), "pose crosses a complete physics frame before world queries")

func _lane_observation() -> Dictionary:
	var origin := bot.global_position + Vector3.UP * bot.head_height
	var direction := Vector3(-sin(bot.yaw) * cos(bot.pitch), sin(bot.pitch), -cos(bot.yaw) * cos(bot.pitch)).normalized()
	var endpoint := origin + direction * (bot.position.distance_to(enemy.position) + 0.5)
	var query := PhysicsRayQueryParameters3D.create(origin, endpoint, 1, [bot.get_rid(), enemy.get_rid()])
	var hit := m.get_world_3d().direct_space_state.intersect_ray(query)
	var trace := bot.trace_shot(origin, direction, float(SBWeapons.get_weapon(bot.weapon_id).range))
	var trace_actor: SBActor = trace.get("actor")
	var in_bounds: bool = absf(bot.position.x) + 0.3 < 23.5 and absf(bot.position.z) + 0.3 < 23.5 and absf(enemy.position.x) + 0.3 < 23.5 and absf(enemy.position.z) + 0.3 < 23.5
	return {"shooter": bot.position, "target": enemy.position, "in_bounds": in_bounds,
		"pose_settle": pose_settle.duplicate(), "observation_frame": Engine.get_physics_frames(),
		"world_mask": 1, "ray_from": origin, "ray_to": endpoint,
		"world_clear": hit.is_empty(), "world_hit_position": hit.get("position"),
		"world_hit_path": str((hit.collider as Node).get_path()) if hit.has("collider") else "",
		"stock_trace": {"hit": trace.hit, "distance": trace.distance, "position": trace.position,
			"actor_id": trace_actor.actor_id if trace_actor != null else 0, "headshot": trace.get("headshot", false)}}

func _resources(snap: Dictionary) -> Dictionary:
	var rows := {}
	for weapon in ["sidearm", "smg", "rifle", "marksman"]:
		var row := {"owned": snap.inventory.has(weapon), "source": "unowned", "clip": null, "reserve": null,
			"equip_default": [int(SBWeapons.get_weapon(weapon).magazine), int(SBWeapons.get_weapon(weapon).reserve)]}
		if row.owned:
			if weapon == snap.weapon:
				row.source = "active_fields"
				row.clip = int(snap.ammo)
				row.reserve = int(snap.reserve)
			elif snap.ammo_store.has(weapon):
				var stored: Vector2i = snap.ammo_store[weapon]
				row.source = "holstered_store"
				row.clip = stored.x
				row.reserve = stored.y
			else:
				row.source = "unknown"
		rows[weapon] = row
	return rows

func _equip_semantics_total(snap: Dictionary) -> int:
	# Default amounts are a projection of _equip semantics, not known availability.
	var total := 0
	var resources := _resources(snap)
	for weapon in snap.inventory:
		var resource: Dictionary = resources[weapon]
		if resource.source == "unknown":
			total += int(resource.equip_default[0]) + int(resource.equip_default[1])
		else:
			total += int(resource.clip) + int(resource.reserve)
	return total

func _observe(label: String, s: Dictionary, step: int, kind: String = "") -> Dictionary:
	var before := _snapshot()
	var enemy_before := _enemy_snapshot()
	var objective_before := _objective_snapshot()
	var lane := _lane_observation()
	var shots_before := shots.size()
	var damages_before := damage_events.size()
	var eliminations_before := elimination_events.size()
	m._bot_input(bot, DT)
	var after_decision := _snapshot()
	var enemy_after_decision := _enemy_snapshot()
	var objective_after_decision := _objective_snapshot()
	var command: Dictionary = bot.input_state.duplicate(true)
	var decision_bot_state: Dictionary = m._bot_state[6].duplicate(true)
	check(before == after_decision, label + " decision leaves full protected snapshot unchanged")
	check(enemy_before == enemy_after_decision, label + " decision leaves full target snapshot unchanged")
	check(objective_before == objective_after_decision, label + " decision leaves objective authority unchanged")
	check(shots_before == shots.size() and damages_before == damage_events.size() and eliminations_before == elimination_events.size(), label + " decision emits no authority events")
	check(bool(lane.in_bounds), label + " controlled actor footprints remain in yard bounds")
	if s.objective == "none" and float(s.target.distance) <= 45.5:
		check(bool(lane.world_clear), label + " settled ordinary center line is unobstructed")
		if bool(enemy_before.alive) and float(s.target.distance) <= float(SBWeapons.get_weapon(bot.weapon_id).range):
			check(int(lane.stock_trace.actor_id) == 1, label + " stock center trace reaches the living target")
	check(str(command.weapon) == "" or before.inventory.has(str(command.weapon)), label + " request is owned")
	var expected_target := 1 if bot.visible_enemy and bool(enemy_before.alive) and float(s.target.distance) <= float(SBBotAI.profile_for(s.difficulty).vision_range) else 0
	check(int(m._bot_state[6].target) == expected_target, label + " production FOV/range acquisition matches controlled pose")
	check(bool(command.interact) == (s.objective != "none"), label + " objective guard matches controlled pose")
	bot.tick_authority_actions(DT)
	var after_action := _snapshot()
	var enemy_after_action := _enemy_snapshot()
	var objective_after_action := _objective_snapshot()
	var shot_delta := shots.size() - shots_before
	check(bot.ammo >= 0 and bot.reserve >= 0, label + " ammunition stays nonnegative")
	check(_equip_semantics_total(after_action) + shot_delta == _equip_semantics_total(before), label + " action conserves equip-semantics ammo with actual shots")
	check(before.inventory == after_action.inventory and before.health == after_action.health, label + " actor action preserves inventory and shooter health")
	var enemy_killed: bool = bool(enemy_after_decision.alive) and not enemy.alive
	check(int(after_action.credits) == mini(9000, int(after_decision.credits) + (300 if enemy_killed else 0)), label + " real kill reward is retained without fixture suppression")
	var switched := str(before.weapon) != str(after_action.weapon)
	if str(command.weapon) != "" and str(command.weapon) != str(before.weapon):
		check(str(after_action.weapon) == str(command.weapon) and is_equal_approx(float(after_action.deploy), SBActor.DEPLOY_SECONDS), label + " real equip consumes request and preserves draw delay")
	if int(before.ammo) == 0 and int(before.reserve) == 0 and not switched and float(before.reload) == 0.0:
		check(shot_delta == 0 and float(after_action.reload) == 0.0, label + " fully exhausted weapon cannot fire or start reload")
	var resources := _resources(before)
	var sidearm: Dictionary = resources.sidearm
	var known_sidearm_resources: bool = bool(sidearm.owned) and sidearm.source != "unknown" and int(sidearm.clip) + int(sidearm.reserve) > 0
	var result := {"label": label, "scenario": s, "step": step,
		"elapsed": m._elapsed, "visibility_injected": bot.visible_enemy,
		"lane": lane, "enemy_before": enemy_before, "enemy_after_decision": enemy_after_decision, "enemy_after_action": enemy_after_action,
		"objective_before": objective_before, "objective_after_decision": objective_after_decision, "objective_after_action": objective_after_action,
		"before": before, "after_decision": after_decision, "after_action": after_action,
		"resources_before": resources, "resources_after": _resources(after_action),
		"decision_bot_state": decision_bot_state, "bot_state_after_action": m._bot_state[6].duplicate(true), "command": command,
		"actual_shots": shots.slice(shots_before), "shot_delta": shot_delta,
		"damage_events": damage_events.slice(damages_before), "elimination_events": elimination_events.slice(eliminations_before),
		"target_damage_delta": float(enemy_after_decision.health) - float(enemy_after_action.health),
		"reward_delta": int(after_action.credits) - int(after_decision.credits),
		"equip_semantics_total_before": _equip_semantics_total(before), "equip_semantics_total_after": _equip_semantics_total(after_action),
		"known_sidearm_resources": known_sidearm_resources,
		"sidearm_center_distance_within_trace_range": float(s.target.distance) <= float(SBWeapons.get_weapon("sidearm").range),
		"switched": switched,
		"empty_reload_request": bool(command.reload) and int(before.ammo) == 0 and int(before.reserve) == 0 and not switched,
		"empty_fire_request": bool(command.fire) and int(before.ammo) == 0 and shot_delta == 0 and not switched}
	emit_row(kind if kind != "" else "STEP" if step >= 0 else "CASE", result)
	return result

func _case(group: String, difficulty: String, primary: String, active: String, sidearm: String,
		target: Dictionary, objective: String = "none", stale: bool = false) -> void:
	var s := _spec(difficulty, primary, active, sidearm, target, objective, stale)
	_prepare(s)
	await _settle_pose()
	var label := "%s/%s/%s/%s/%s/%s/%s" % [group, difficulty, primary, active, sidearm, target.name, objective]
	_observe(label, s, -1)
	matrix_cases += 1

func _sequence(difficulty: String, primary: String, setting: Dictionary) -> void:
	var s := _spec(difficulty, primary, setting.active, setting.sidearm, setting.target)
	_prepare(s)
	await _settle_pose()
	var label := "sequence/%s/%s/%s" % [difficulty, primary, setting.name]
	var summary := {"label": label, "switches": 0, "empty_reload_requests": 0,
		"empty_fire_requests": 0, "shots": 0, "known_sidearm_resource_steps": 0}
	for step in range(8):
		m._elapsed = 20.0 + DT * step
		var row := _observe(label, s, step)
		summary.switches += int(row.switched)
		summary.empty_reload_requests += int(row.empty_reload_request)
		summary.empty_fire_requests += int(row.empty_fire_request)
		summary.shots += int(row.shot_delta)
		summary.known_sidearm_resource_steps += int(row.known_sidearm_resources)
		sequence_steps += 1
	emit_row("SEQUENCE", summary)
	sequences += 1

func _positive_controls() -> void:
	var visible := {"name": "positive_clear_2m", "distance": 2.0, "visible": true}
	var hidden := {"name": "positive_hidden_2m", "distance": 2.0, "visible": false}
	await _control("kill_rifle", _spec("normal", "rifle", "loaded", "unowned", visible), 8)
	for primary in PRIMARIES:
		var steps := ceili(float(SBWeapons.get_weapon(primary).reload) / DT) + 3
		await _control("reload_" + primary, _spec("normal", primary, "reloadable", "unowned", hidden), steps)
	var sidearm_steps := ceili(SBActor.DEPLOY_SECONDS / DT) + ceili(float(SBWeapons.get_weapon("sidearm").reload) / DT) + 4
	await _control("reload_sidearm", _spec("normal", "rifle", "exhausted", "reserve_only", visible), sidearm_steps)

func _control(name: String, s: Dictionary, steps: int) -> void:
	s["control"] = name
	s["positive_lane"] = "2m along z=-20, wholly inside the stock yard"
	s["step_budget"] = steps
	s["initial_target_health"] = 10.0 if name == "kill_rifle" else 100.0
	s["visibility_schedule"] = "visible only on first step, then hidden" if name == "reload_sidearm" else "constant"
	_prepare(s)
	enemy.health = float(s.initial_target_health) # Initial fixture state only; never restored within the control.
	await _settle_pose()
	var lane := _lane_observation()
	check(bool(lane.in_bounds) and bool(lane.world_clear), name + " mandatory settled positive lane is clear and in bounds")
	check(int(lane.stock_trace.actor_id) == 1, name + " stock center trace reaches target before actions")
	var initial_shooter := _snapshot()
	var initial_target := _enemy_snapshot()
	var summary := {"name": name, "steps": steps, "initial_lane": lane,
		"initial_shooter": initial_shooter, "initial_target": initial_target,
		"shots": 0, "damage_events": 0, "target_damage": 0.0, "eliminations": 0,
		"draws": 0, "reload_starts": 0, "reload_completions": 0,
		"reload_start_steps": [], "reload_completion_steps": []}
	var start_step := -1
	for step in range(steps):
		m._elapsed = 20.0 + DT * step
		if name == "reload_sidearm":
			bot.visible_enemy = step == 0
		var row := _observe("control/" + name, s, step, "CONTROL_STEP")
		var before: Dictionary = row.after_decision
		var after: Dictionary = row.after_action
		summary.shots += int(row.shot_delta)
		summary.damage_events += row.damage_events.size()
		summary.target_damage += float(row.target_damage_delta)
		summary.eliminations += row.elimination_events.size()
		if row.switched:
			summary.draws += 1
		if before.weapon == after.weapon and float(before.reload) == 0.0 and float(after.reload) > 0.0:
			summary.reload_starts += 1
			summary.reload_start_steps.append(step)
			start_step = step
			check(is_equal_approx(float(after.reload), float(SBWeapons.get_weapon(str(after.weapon)).reload)), name + " accepted reload starts at configured full duration")
			check(before.ammo == after.ammo and before.reserve == after.reserve, name + " reload start does not transfer rounds")
		if before.weapon == after.weapon and float(before.reload) > 0.0 and float(after.reload) == 0.0:
			summary.reload_completions += 1
			summary.reload_completion_steps.append(step)
			var spec: Dictionary = SBWeapons.get_weapon(str(after.weapon))
			var transferred := mini(int(spec.magazine) - int(before.ammo), int(before.reserve))
			check(transferred > 0 and int(after.ammo) == int(before.ammo) + transferred - int(row.shot_delta) and int(after.reserve) == int(before.reserve) - transferred, name + " completed stock reload transfers only legal reserve rounds")
			var elapsed := float(step - start_step) * DT
			check(start_step >= 0 and elapsed + 0.000001 >= float(spec.reload) and elapsed <= float(spec.reload) + DT + 0.000001, name + " completion follows configured duration within one action tick")
		control_steps += 1
	var final_shooter := _snapshot()
	var final_target := _enemy_snapshot()
	summary["final_shooter"] = final_shooter
	summary["final_target"] = final_target
	if name == "kill_rifle":
		check(int(summary.shots) == 1 and int(summary.damage_events) >= 1 and is_equal_approx(float(summary.target_damage), 10.0), name + " requires an actual shot and target damage")
		check(int(summary.eliminations) == 1 and not bool(final_target.alive) and int(final_target.deaths) == int(initial_target.deaths) + 1, name + " requires one real target death")
		check(int(final_shooter.kills) == int(initial_shooter.kills) + 1 and int(final_shooter.credits) == int(initial_shooter.credits) + 300, name + " requires one ordinary kill and reward")
		check(int(summary.reload_starts) == 0 and int(summary.draws) == 0, name + " uses its initially loaded rifle")
	else:
		var weapon := "sidearm" if name == "reload_sidearm" else str(s.primary)
		var definition: Dictionary = SBWeapons.get_weapon(weapon)
		check(int(summary.reload_starts) == 1 and int(summary.reload_completions) == 1, name + " requires an accepted start and completed reload")
		check(final_shooter.weapon == weapon and int(final_shooter.ammo) == int(definition.magazine) and int(final_shooter.reserve) == 0 and float(final_shooter.reload) == 0.0, name + " finishes with the legal full magazine")
		check(int(summary.shots) == 0 and int(summary.damage_events) == 0 and int(summary.eliminations) == 0, name + " hidden target remains unharmed during reload witness")
		check(final_target == initial_target, name + " target resources and state remain unchanged")
		check(int(summary.draws) == (1 if name == "reload_sidearm" else 0), name + " preserves registered stock draw count")
	control_summaries.append(summary)
	emit_row("CONTROL", summary)
