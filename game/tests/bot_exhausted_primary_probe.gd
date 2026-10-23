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
var failures: Array[String] = []
var checks := 0
var matrix_cases := 0
var sequence_steps := 0
var sequences := 0

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
	bot.shot_fired.connect(_record_shot)
	enemy = m.actors[1]
	for difficulty in DIFFICULTIES:
		for primary in PRIMARIES:
			for target in TARGETS:
				for active in ["exhausted", "reloadable"]:
					for sidearm in ["loaded", "dry", "unknown"]:
						_case("core", difficulty, primary, active, sidearm, target)
				_case("loaded_primary", difficulty, primary, "loaded", "loaded", target)
			for target in [TARGETS[0], TARGETS[2], TARGETS[5]]:
				_case("reserve_only_sidearm", difficulty, primary, "exhausted", "reserve_only", target)
				_case("unowned_sidearm", difficulty, primary, "exhausted", "unowned", target)
				for active in ["exhausted", "reloadable", "loaded"]:
					_case("stale_active_cache", difficulty, primary, active, "loaded", target, "none", true)
				for objective in ["carrier", "defuser"]:
					_case("objective_guard", difficulty, primary, "exhausted", "loaded", target, objective)
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
				_sequence(difficulty, primary, setting)
	check(matrix_cases == 567, "all registered matrix cases completed")
	check(sequences == 72 and sequence_steps == 576, "all registered sequence steps completed")
	check(TacticalMatch.PROTOCOL_VERSION == 6, "protocol remains 6")
	check(m._ranked_payload().is_empty(), "offline probe has no ranked payload")
	m.queue_free()
	await process_frame
	for failure in failures:
		print("BOT_EXHAUSTED_FAILURE " + failure)
	emit_row("RESULT", {"matrix_cases": matrix_cases, "sequences": sequences,
		"sequence_steps": sequence_steps, "checks": checks, "failures": failures,
		"authority_checks_passed": failures.is_empty(),
		"behavior_acceptance": "diagnostic only; no new selection policy asserted"})
	quit(0 if failures.is_empty() else 1)

func _record_shot(_id: int, origin: Vector3, direction: Vector3) -> void:
	shots.append({"weapon": bot.weapon_id, "origin": origin, "direction": direction,
		"ammo_after_shot": bot.ammo, "reserve": bot.reserve})

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
	m._team_ai_state = SBBotAI.create_team_state()
	m.objective_state = "planted" if s.objective == "defuser" else "carried"
	m.objective_carrier = 6 if s.objective == "carrier" else 0
	m.objective_position = m.arena.sites[0]
	for other: SBActor in m.actors.values():
		other.alive = false
		other.position = Vector3(100 + other.actor_id * 4, 0, 100)
	bot.team = 0 if s.objective == "carrier" else 1
	bot.inventory.assign([s.primary] if s.sidearm_resource == "unowned" else ["sidearm", s.primary])
	if bot.weapon_id != s.primary:
		bot._equip(s.primary)
	bot.reset_for_round(m.arena.sites[0] if s.objective != "none" else Vector3(-14, 0, -10))
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
	bot.position = m.arena.sites[0] if s.objective != "none" else Vector3(-14, 0, -10)
	bot.yaw = -PI / 2.0
	bot.pitch = atan2(-0.35, float(s.target.distance))
	bot.visible_enemy = bool(s.target.visible)
	enemy.team = 1 - bot.team
	enemy.reset_for_round(bot.position + Vector3(float(s.target.distance), 0, 0))
	m._reset_bot_state(bot)

func _snapshot() -> Dictionary:
	return {"weapon": bot.weapon_id, "ammo": bot.ammo, "reserve": bot.reserve,
		"reload": bot.reload_remaining, "deploy": bot._deploy_remaining,
		"cooldowns": bot._weapon_cooldowns.duplicate(true), "inventory": bot.inventory.duplicate(),
		"ammo_store": bot._ammo_store.duplicate(true), "health": bot.health, "alive": bot.alive,
		"credits": bot.credits, "kills": bot.kills, "assists": bot.assists, "deaths": bot.deaths,
		"grenades": bot.grenades, "smokes": bot.smokes,
		"recoil": bot.recoil, "position": bot.position, "velocity": bot.velocity,
		"yaw": bot.yaw, "pitch": bot.pitch, "fire_previous": bot._fire_previous,
		"floor_contact": bot.is_on_floor(), "crouching": bot._crouching,
		"actual_action_spread": bot.current_spread(not bot.is_on_floor())}

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

func _observe(label: String, s: Dictionary, step: int) -> Dictionary:
	var before := _snapshot()
	var enemy_before := {"alive": enemy.alive, "health": enemy.health, "position": enemy.position}
	var shots_before := shots.size()
	m._bot_input(bot, DT)
	var after_decision := _snapshot()
	var command: Dictionary = bot.input_state.duplicate(true)
	var decision_bot_state: Dictionary = m._bot_state[6].duplicate(true)
	check(before == after_decision, label + " decision leaves full protected snapshot unchanged")
	check(str(command.weapon) == "" or before.inventory.has(str(command.weapon)), label + " request is owned")
	var expected_target := 1 if bot.visible_enemy and bool(enemy_before.alive) and float(s.target.distance) <= float(SBBotAI.profile_for(s.difficulty).vision_range) else 0
	check(int(m._bot_state[6].target) == expected_target, label + " production FOV/range acquisition matches controlled pose")
	check(bool(command.interact) == (s.objective != "none"), label + " objective guard matches controlled pose")
	bot.tick_authority_actions(DT)
	var after_action := _snapshot()
	var shot_delta := shots.size() - shots_before
	check(bot.ammo >= 0 and bot.reserve >= 0, label + " ammunition stays nonnegative")
	check(_equip_semantics_total(after_action) + shot_delta == _equip_semantics_total(before), label + " action conserves equip-semantics ammo with actual shots")
	check(before.inventory == after_action.inventory and before.health == after_action.health, label + " actor action preserves inventory and shooter health")
	var enemy_killed: bool = bool(enemy_before.alive) and not enemy.alive
	check(int(after_action.credits) == mini(9000, int(before.credits) + (300 if enemy_killed else 0)), label + " real kill reward is retained without fixture suppression")
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
		"enemy_before": enemy_before, "enemy_after": {"alive": enemy.alive, "health": enemy.health, "position": enemy.position},
		"before": before, "after_decision": after_decision, "after_action": after_action,
		"resources_before": resources, "resources_after": _resources(after_action),
		"decision_bot_state": decision_bot_state, "bot_state_after_action": m._bot_state[6].duplicate(true), "command": command,
		"actual_shots": shots.slice(shots_before), "shot_delta": shot_delta,
		"equip_semantics_total_before": _equip_semantics_total(before), "equip_semantics_total_after": _equip_semantics_total(after_action),
		"known_sidearm_resources": known_sidearm_resources,
		"sidearm_center_distance_within_trace_range": float(s.target.distance) <= float(SBWeapons.get_weapon("sidearm").range),
		"switched": switched,
		"empty_reload_request": bool(command.reload) and int(before.ammo) == 0 and int(before.reserve) == 0 and not switched,
		"empty_fire_request": bool(command.fire) and int(before.ammo) == 0 and shot_delta == 0 and not switched}
	emit_row("STEP" if step >= 0 else "CASE", result)
	return result

func _case(group: String, difficulty: String, primary: String, active: String, sidearm: String,
		target: Dictionary, objective: String = "none", stale: bool = false) -> void:
	var s := _spec(difficulty, primary, active, sidearm, target, objective, stale)
	_prepare(s)
	var label := "%s/%s/%s/%s/%s/%s/%s" % [group, difficulty, primary, active, sidearm, target.name, objective]
	_observe(label, s, -1)
	matrix_cases += 1

func _sequence(difficulty: String, primary: String, setting: Dictionary) -> void:
	var s := _spec(difficulty, primary, setting.active, setting.sidearm, setting.target)
	_prepare(s)
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
