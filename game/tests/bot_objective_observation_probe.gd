extends SceneTree
## Opt-in component reconstruction. This is not a replay or a stock-match gate.
const FIXTURE := "res://tests/fixtures/bot_objective_timeout.jsonl"
const DT := 1.0 / 60.0
const FORWARD_TICKS := 120

class ObservationMatch extends "res://scripts/gameplay/match.gd":
	var observe := false
	var decisions: Array = []
	var interactions: Array = []
	var authority_steps: Array = []

	func _bot_input(actor: SBActor, delta: float) -> void:
		var observation: Dictionary = {"enabled": true} if observe else {}
		var before: Dictionary = observe_state() if observe else {}
		SBBotAI.compute_bot_input(self, actor, delta, observation)
		if observe and observation.get("status", "") == "complete":
			decisions.append({"tick": _simulation_tick, "elapsed": _elapsed, "dt": delta,
				"actor_id": actor.actor_id, "position": actor.position,
				"before": before, "after": observe_state(), "observation": observation.duplicate(true)})

	func _authority_tick(delta: float) -> void:
		var before: Dictionary = observe_state() if observe else {}
		super._authority_tick(delta)
		if observe:
			authority_steps.append({"tick": _simulation_tick, "dt": delta,
				"before": before, "after": observe_state()})

	func _objective_tick(delta: float) -> void:
		var state_before: Dictionary = observe_state() if observe else {}
		var before := {}
		if observe:
			for actor: SBActor in actors.values():
				before[str(actor.actor_id)] = {"alive": actor.alive, "team": actor.team,
					"position": actor.position, "interact": bool(actor.input_state.get("interact", false)),
					"move": actor.input_state.get("move", Vector2.ZERO), "site": arena.is_at_site(actor.position),
					"objective_distance": actor.position.distance_to(objective_position),
					"progress": float(_interactions.get(actor.actor_id, 0.0))}
		var old_state := objective_state
		var old_carrier := objective_carrier
		super._objective_tick(delta)
		if observe:
			interactions.append({"tick": _simulation_tick, "dt": delta,
				"objective_before": old_state, "objective_after": objective_state,
				"carrier_before": old_carrier, "carrier_after": objective_carrier,
				"actors_before": before, "progress_after": _interactions.duplicate(true),
				"before": state_before, "after": observe_state()})

	func observe_state() -> Dictionary:
		var actor_rows := {}
		for actor: SBActor in actors.values():
			actor_rows[str(actor.actor_id)] = {"team": actor.team, "kills": actor.kills, "assists": actor.assists, "deaths": actor.deaths, "position": actor.position, "velocity": actor.velocity,
				"yaw": actor.yaw, "pitch": actor.pitch, "alive": actor.alive, "health": actor.health,
				"weapon": actor.weapon_id, "ammo": actor.ammo, "reserve": actor.reserve,
				"reload": actor.reload_remaining, "deploy": actor._deploy_remaining,
				"ammo_store": actor._ammo_store.duplicate(true), "inventory": actor.inventory.duplicate(),
				"credits": actor.credits, "grenades": actor.grenades, "smokes": actor.smokes,
				"recoil": actor.recoil, "rng": str(actor._rng.state),
				"cooldowns": actor._weapon_cooldowns.duplicate(true), "shot_index": actor._shot_index,
				"fire_previous": actor._fire_previous, "jump_previous": actor._jump_previous,
				"grenade_previous": actor._grenade_previous, "smoke_previous": actor._smoke_previous,
				"crouching": actor._crouching, "head_height": actor.head_height,
				"floor_contact": actor.is_on_floor(), "collision_disabled": actor._collision.disabled,
				"collision_height": actor._collision.shape.height, "collision_position": actor._collision.position,
				"input": actor.input_state.duplicate(true)}
		var utilities: Array = []
		for child: Node in get_children():
			if child is SBUtility:
				utilities.append({"kind": child.kind, "position": child.position, "velocity": child.velocity,
					"owner_id": child.owner_id, "owner_team": child.owner_team, "fuse": child._fuse,
					"lifetime": child._lifetime, "detonated": child._detonated, "visual_only": child.visual_only})
		return {"actors": actor_rows, "utilities": utilities, "rng": str(_rng.state), "bots": _bot_state.duplicate(true),
			"teams": _team_ai_state.duplicate(true), "heard": _heard.duplicate(true),
			"objective": objective_state, "carrier": objective_carrier,
			"objective_position": objective_position, "objective_timer": objective_timer,
			"contributions": objective_contributions.duplicate(true), "interaction_progress": interaction_progress,
			"damage_history": _damage_history.duplicate(true), "round": round_number,
			"attack_score": attack_score, "defend_score": defend_score, "bot_clock": _bot_clock,
			"interactions": _interactions.duplicate(true), "time_left": time_left,
			"tick": _simulation_tick, "elapsed": _elapsed, "phase": phase}


var m: ObservationMatch
var initial: Dictionary
var poses: Array[Dictionary] = []
var failures: Array[String] = []
var checks := 0
var emitted_decisions := 0
var emitted_interactions := 0
var emitted_authority := 0
var contract: Dictionary

func _initialize() -> void:
	_run.call_deferred()

func check(value: bool, message: String) -> void:
	checks += 1
	if not value: failures.append(message)

func _json(value: Variant) -> Variant:
	if value is Vector2 or value is Vector2i: return [value.x, value.y]
	if value is Vector3: return [value.x, value.y, value.z]
	if value is Array:
		var result: Array = []
		for item in value: result.append(_json(item))
		return result
	if value is Dictionary:
		var result := {}
		for key in value: result[str(key)] = _json(value[key])
		return result
	return value

func emit_row(kind: String, value: Dictionary) -> void:
	print("BOT_OBJECTIVE_" + kind + " " + JSON.stringify(_json(value)))

func _v(value: Array) -> Vector3:
	return Vector3(float(value[0]), float(value[1]), float(value[2]))

func _prepare(pose: Dictionary) -> void:
	m.observe = false
	m.decisions.clear()
	m.interactions.clear()
	m.authority_steps.clear()
	m.phase = "live" # POST pose is a declared one-decision reconstruction only.
	m.round_number = int(pose.round_number)
	m.time_left = float(pose.time_left)
	m._elapsed = float(pose.elapsed)
	m._simulation_tick = int(pose.simulation_tick)
	m._bot_clock = 0.0
	m.attack_score = int(pose.attack_score)
	m.defend_score = int(pose.defend_score)
	m.objective_state = str(pose.objective_state)
	m.objective_carrier = int(pose.objective_carrier)
	m.objective_position = _v(pose.objective_position)
	m.objective_timer = float(pose.objective_timer)
	m.interaction_progress = 0.0
	m._interactions.clear()
	m.objective_contributions.clear()
	m._bot_state.clear()
	m._team_ai_state = SBBotAI.create_team_state()
	m._heard.clear()
	m._damage_history.clear()
	for child: Node in m.get_children():
		if child is SBUtility: child.queue_free()
	m._rng.seed = int(initial.match_seed)
	for record: Dictionary in pose.actors:
		var actor: SBActor = m.actors[int(record.id)]
		actor.team = int(record.team)
		actor.inventory.assign(record.inventory)
		actor._equip(str(record.weapon))
		actor._ammo_store.clear()
		actor.reset_for_round(_v(record.position))
		actor.alive = bool(record.alive)
		actor._collision.disabled = not actor.alive
		actor.health = float(record.health)
		actor.velocity = _v(record.velocity)
		actor.yaw = float(record.yaw)
		actor.pitch = float(record.pitch)
		actor.rotation.y = actor.yaw
		actor.ammo = int(record.ammo)
		actor.reserve = int(record.reserve)
		actor.reload_remaining = float(record.reload)
		actor.credits = int(record.credits)
		actor.kills = int(record.kills)
		actor.assists = int(record.assists)
		actor.deaths = int(record.deaths)
		actor.grenades = int(record.grenades)
		actor.smokes = int(record.smokes)
		actor._rng.seed = int(initial.actor_spread_seeds[str(actor.actor_id)])
		actor.input_state = {"move": Vector2.ZERO, "look": Vector2(actor.yaw, actor.pitch),
			"interact": false, "fire": false, "reload": false, "jump": false, "crouch": false,
			"weapon": "", "smoke": false, "grenade": false}
		m._reset_bot_state(actor)
	SBBotAI.select_round_plan(m)

func _settle() -> void:
	var before := Engine.get_physics_frames()
	await physics_frame
	await physics_frame
	check(Engine.get_physics_frames() > before, "real physics pose barrier")

func _flush(label: String) -> void:
	for row: Dictionary in m.decisions:
		row["label"] = label
		emit_row("DECISION", row)
		emitted_decisions += 1
	for row: Dictionary in m.authority_steps:
		row["label"] = label
		emit_row("AUTHORITY", row)
		emitted_authority += 1
	for row: Dictionary in m.interactions:
		row["label"] = label
		emit_row("INTERACTION", row)
		emitted_interactions += 1
	m.decisions.clear()
	m.interactions.clear()
	m.authority_steps.clear()

func _pair(pose: Dictionary) -> void:
	var snapshots: Array = []
	var before_states: Array = []
	for enabled in [false, true]:
		_prepare(pose)
		await _settle()
		before_states.append(m.observe_state())
		m.observe = enabled
		m._bot_input(m.actors[6], 0.12)
		snapshots.append(m.observe_state())
	var equal: bool = _json(before_states[0]) == _json(before_states[1]) and _json(snapshots[0]) == _json(snapshots[1])
	check(equal, "observation preserves command, resources, memory and RNG at event " + str(pose.event_index))
	emit_row("PAIR", {"event_index": pose.event_index, "equal": equal,
		"before_off": before_states[0], "before_on": before_states[1],
		"after_off": snapshots[0], "after_on": snapshots[1]})
	_flush("pose_" + str(pose.event_index))

func _control(kind: String) -> void:
	_prepare(poses[2])
	var actor: SBActor = m.actors[6]
	actor.position = m.arena.sites[0]
	if kind == "defuse":
		actor.team = 1
		m.objective_state = "planted"
		m.objective_position = actor.position
		m.objective_timer = TacticalMatch.DEVICE_SECONDS
	if kind == "wrong_site": actor.position = Vector3(0.0, 0.0, -20.0)
	await _settle()
	m.observe = true
	var positive: bool = kind in ["plant", "defuse"]
	var ticks: int = 181 if kind == "plant" else (301 if kind == "defuse" else 1)
	if not positive: m._interactions[6] = 0.25
	emit_row("CONTROL_START", {"name": kind, "state": m.observe_state()})
	for tick in range(ticks):
		m._simulation_tick += 1
		m._elapsed += DT
		if tick % 8 == 0: m._bot_input(actor, 0.12)
		if not positive:
			actor.input_state["interact"] = kind != "no_interact"
			actor.input_state["move"] = Vector2(0.0, 1.0) if kind == "moving" else Vector2.ZERO
		# Isolated interaction controls keep other actors stationary. Subject uses
		# real movement/actions; objective consumer considers every actor normally.
		actor.tick_authority_movement(DT)
		actor.tick_authority_actions(DT)
		m._objective_tick(DT)
		if m.objective_state in ["planted", "defused"] and (kind != "defuse" or m.objective_state == "defused"): break
	var valid: bool
	if positive:
		valid = m.objective_state == ("planted" if kind == "plant" else "defused") and int(m.objective_contributions.get(6, 0)) == 1
	else:
		valid = not m._interactions.has(6) and m.objective_state == "carried" and int(m.objective_contributions.get(6, 0)) == 0
	check(valid, "authority control " + kind)
	emit_row("CONTROL", {"name": kind, "valid": valid, "objective": m.objective_state,
		"contributions": m.objective_contributions.duplicate(true), "ticks": m.interactions.size(), "final": m.observe_state()})
	_flush("control_" + kind)

func _freshness_controls() -> void:
	_prepare(poses[0])
	await _settle()
	var actor: SBActor = m.actors[6]
	var output := {"enabled": true}
	SBBotAI.compute_bot_input(m, actor, 0.12, output)
	check(output.get("status") == "complete", "fresh live decision")
	emit_row("CALL", {"case": "live_complete", "output": output.duplicate(true)})
	actor.alive = false
	SBBotAI.compute_bot_input(m, actor, 0.12, output)
	check(output.get("status") == "dead" and not output.has("decision"), "live to dead clears output")
	emit_row("CALL", {"case": "live_to_dead", "output": output.duplicate(true)})
	actor.alive = true
	m.phase = "post"
	SBBotAI.compute_bot_input(m, actor, 0.12, output)
	check(output.get("status") == "non_live" and not output.has("decision"), "live to post clears output")
	emit_row("CALL", {"case": "live_to_post", "output": output.duplicate(true)})
	m.phase = "live"
	for value in [false, 1, "true"]:
		output["enabled"] = true
		SBBotAI.compute_bot_input(m, actor, 0.12, output)
		output["enabled"] = value
		SBBotAI.compute_bot_input(m, actor, 0.12, output)
		check(output.get("status") == "disabled" and not output.has("decision"), "strict opt-in clears old output")
		var label := "enabled_to_disabled" if value is bool else ("integer_opt_in" if value is int else "string_opt_in")
		emit_row("CALL", {"case": label, "output": output.duplicate(true)})
	output["enabled"] = true
	SBBotAI.compute_bot_input(m, actor, 0.12, output)
	m.options["mode"] = "client"
	SBBotAI.compute_bot_input(m, actor, 0.12, output)
	check(output.get("status") == "blocked" and not output.has("decision"), "online clears old output")
	emit_row("CALL", {"case": "offline_to_online", "output": output.duplicate(true)})
	m.options["mode"] = "offline"
	SBBotAI.compute_bot_input(m, actor, 0.12, output)
	SBBotAI.acquire_target(m, actor, m._bot_state[6], SBBotAI.profile_for("normal"), output)
	check(output.get("operation") == "perception" and not output.has("decision"), "direct perception replaces decision")
	emit_row("CALL", {"case": "direct_perception", "output": output.duplicate(true)})
	for other: SBActor in m.actors.values():
		if other.team != actor.team: other.alive = false
	output["navigation_destination"] = Vector3(999, 999, 999)
	output["target_distance"] = 999.0
	output["aligned"] = true
	SBBotAI.compute_bot_input(m, actor, 0.12, output)
	check(output.get("target_distance") == null and output.get("aligned") == null, "branch-only output resets")
	emit_row("CALL", {"case": "branch_change", "output": output.duplicate(true)})
	var empty := {}
	SBBotAI.compute_bot_input(m, actor, 0.12, empty)
	check(empty.is_empty(), "empty default collects nothing")
	emit_row("CALL", {"case": "empty_default", "output": empty})

func _run() -> void:
	var file := FileAccess.open(FIXTURE, FileAccess.READ)
	if file == null:
		push_error("Original objective fixture unavailable")
		quit(1)
		return
	while not file.eof_reached():
		var line := file.get_line()
		if line.is_empty(): continue
		var value: Variant = JSON.parse_string(line)
		if not value is Dictionary:
			push_error("Malformed original objective fixture")
			quit(1)
			return
		if int(value.event_index) == 0: initial = value
		elif int(value.event_index) in [120, 122, 127]: poses.append(value)
	file.close()
	if initial.is_empty() or poses.size() != 3:
		push_error("Incomplete original objective fixture")
		quit(1)
		return
	contract = JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/bot_objective_contract.json"))
	if contract.is_empty():
		push_error("Objective contract unavailable")
		quit(1)
		return
	var header := contract.duplicate(true)
	header["engine"] = Engine.get_version_info()
	header["time_scale"] = Engine.time_scale
	header["physics_ticks_per_second"] = Engine.physics_ticks_per_second
	header["profiles"] = SBBotAI.PROFILES
	header["rules"] = initial.rules
	header["protocol"] = TacticalMatch.PROTOCOL_VERSION
	emit_row("HEADER", header)
	m = ObservationMatch.new()
	m.configure({"mode": "offline", "difficulty": str(initial.difficulty)})
	root.add_child(m)
	m.set_physics_process(false)
	m.local_id = 0
	check(is_equal_approx(Engine.time_scale, 1.0), "stock time scale")
	await _freshness_controls()
	for pose in poses: await _pair(pose)
	# Use the last actual LIVE pose for forward ticks; POST has no valid remaining
	# LIVE timer. Both source phase and time_left are retained in this slice.
	_prepare(poses[1])
	await _settle()
	m.observe = true
	emit_row("START", {"label": "forward_live_122", "source_event": 122, "state": m.observe_state()})
	for tick in range(FORWARD_TICKS):
		m._elapsed += DT
		m._authority_tick(DT)
		await physics_frame
	_flush("forward_live_122")
	for kind in ["plant", "defuse", "wrong_site", "moving", "no_interact"]: await _control(kind)
	check(m._ranked_payload().is_empty(), "offline fixture has no ranked payload")
	check(TacticalMatch.PROTOCOL_VERSION == 6, "protocol 6")
	m.queue_free()
	await process_frame
	await process_frame
	emit_row("RESULT", {"checks": checks, "failures": failures, "pairs": 3, "controls": 5,
		"decisions": emitted_decisions, "interactions": emitted_interactions, "authority": emitted_authority,
		"scope": "diagnostic_only_no_objective_quality_acceptance"})
	quit(0 if failures.is_empty() else 1)
