extends RefCounted
class_name SBBotAI

const PROFILES := {
	"easy": {
		"fov_dot": 0.35,
		"max_sight_distance": 30.0,
		"hearing_range": 18.0,
		"reaction_delay": 0.42,
		"aim_jitter": 0.095,
		"turn_speed": 3.2,
		"memory_duration": 1.6,
		"burst_duration": 0.22,
		"burst_pause": 0.32,
		"strafe_freq": 1.4,
		"utility_chance": 0.20,
		"retreat_hp": 20.0,
		"sound_noise": 2.4,
	},
	"normal": {
		"fov_dot": 0.15,
		"max_sight_distance": 38.0,
		"hearing_range": 26.0,
		"reaction_delay": 0.22,
		"aim_jitter": 0.045,
		"turn_speed": 5.4,
		"memory_duration": 3.2,
		"burst_duration": 0.34,
		"burst_pause": 0.18,
		"strafe_freq": 2.3,
		"utility_chance": 0.55,
		"retreat_hp": 28.0,
		"sound_noise": 1.1,
	},
	"hard": {
		"fov_dot": -0.05,
		"max_sight_distance": 46.0,
		"hearing_range": 35.0,
		"reaction_delay": 0.11,
		"aim_jitter": 0.015,
		"turn_speed": 8.2,
		"memory_duration": 5.0,
		"burst_duration": 0.46,
		"burst_pause": 0.10,
		"strafe_freq": 3.1,
		"utility_chance": 0.85,
		"retreat_hp": 34.0,
		"sound_noise": 0.35,
	},
}

const SOUND_MEMORY_SECONDS := 5.0
const CALLOUT_MEMORY_SECONDS := 6.0
const STUCK_REPATH_SECONDS := 0.55
const TARGET_HYSTERESIS_BONUS := 8.5

const COVER_SPOTS: Array[Vector3] = [
	Vector3(-14.0, 0.0, -7.2),
	Vector3(-14.0, 0.0, -2.8),
	Vector3(14.0, 0.0, -7.2),
	Vector3(14.0, 0.0, -2.8),
	Vector3(-16.0, 0.0, 12.8),
	Vector3(-13.5, 0.0, 7.5),
	Vector3(16.0, 0.0, 12.8),
	Vector3(13.5, 0.0, 7.5),
	Vector3(-3.0, 0.0, -3.2),
	Vector3(3.0, 0.0, -3.2),
	Vector3(0.0, 0.0, 5.6),
	Vector3(-9.2, 0.0, 4.0),
	Vector3(9.2, 0.0, 4.0),
	Vector3(-9.2, 0.0, -11.0),
	Vector3(9.2, 0.0, -11.0),
]

const DEFENDER_ANCHORS: Array[Vector3] = [
	Vector3(-15.0, 0.0, 9.0),
	Vector3(15.0, 0.0, 9.0),
	Vector3(-12.0, 0.0, 6.0),
	Vector3(12.0, 0.0, 6.0),
	Vector3(0.0, 0.0, 12.0),
]

static func profile_for(difficulty: String) -> Dictionary:
	return PROFILES.get(difficulty, PROFILES["normal"])

static func get_profile(difficulty: String) -> Dictionary:
	return profile_for(difficulty)

static func create_state(actor: SBActor) -> Dictionary:
	var pos: Vector3 = actor.position if actor != null else Vector3.ZERO
	return new_bot_state(pos)

static func new_bot_state(initial_pos: Vector3 = Vector3.ZERO) -> Dictionary:
	return {
		"last_seen": initial_pos,
		"seen_at": -100.0,
		"heard_pos": initial_pos,
		"heard_at": -100.0,
		"target_seen_since": -100.0,
		"last_target": -1,
		"strafe_seed": float(posmod(int(absf(initial_pos.x * 13.0 + initial_pos.z * 7.0)) * 97, 100)) * 0.06,
		"stuck": 0.0,
		"last_pos": initial_pos,
		"role": "default",
		"damaged_from": initial_pos,
		"damaged_at": -100.0,
		"repath_offset": Vector3.ZERO,
		"repath_until": -100.0,
		"utility_cooldown_until": 0.0,
		"burst_timer": 0.0,
	}

static func create_team_state() -> Dictionary:
	return {
		"primary_site": 0,
		"target_site": 0,
		"site_locked": false,
		"callouts": {},
		"danger_zones": [],
	}

static func new_team_state() -> Dictionary:
	return create_team_state()

static func choose_buy_weapon(actor: SBActor, difficulty: String, round_number: int) -> String:
	if actor == null:
		return "pistol"
	if round_number == 1 or round_number == 7:
		return "pistol"
	if actor.credits >= 2900:
		return "rifle"
	if actor.credits >= 1850:
		if difficulty == "easy" and actor.credits < 2400:
			return "shotgun"
		return "shotgun" if (actor.id + round_number) % 3 == 0 else "smg"
	if actor.credits >= 1450:
		return "smg"
	return actor.weapon_id

static func buy_equipment(actor: SBActor, difficulty: String, round_number: int) -> String:
	if actor == null:
		return "pistol"
	var choice: String = choose_buy_weapon(actor, difficulty, round_number)
	if choice != "" and choice != actor.weapon_id:
		actor.buy_weapon(choice)
	return actor.weapon_id

static func select_round_plan(match_or_round: Variant, team_or_rng: Variant = 0) -> Variant:
	if match_or_round is int:
		var round_num: int = int(match_or_round)
		var rng: RandomNumberGenerator = team_or_rng as RandomNumberGenerator
		if rng == null:
			return posmod(round_num, 2)
		return int(rng.randi() % 2)
	var match_node: Node = match_or_round as Node
	if match_node == null:
		return {"target_site": 0, "primary_site": 0}
	if not match_node.get("_team_ai_state") is Dictionary or match_node._team_ai_state.is_empty():
		match_node._team_ai_state = create_team_state()
	var target_site: int = int(match_node._team_ai_state.get("primary_site", posmod(int(match_node.round_number), 2)))
	var carrier: SBActor = match_node.actors.get(match_node.bomb_carrier_id, null)
	if carrier != null and carrier.alive and match_node.arena != null and match_node.arena.sites.size() >= 2:
		var d0: float = carrier.position.distance_to(match_node.arena.sites[0])
		var d1: float = carrier.position.distance_to(match_node.arena.sites[1])
		if minf(d0, d1) < 22.0 and absf(d0 - d1) > 5.0:
			target_site = 0 if d0 < d1 else 1
			match_node._team_ai_state["site_locked"] = true
		elif not bool(match_node._team_ai_state.get("site_locked", false)):
			target_site = posmod(int(match_node.round_number) + int(match_node.bomb_carrier_id), 2)
	match_node._team_ai_state["primary_site"] = target_site
	match_node._team_ai_state["target_site"] = target_site
	return match_node._team_ai_state

static func get_site_hold_position(arena: SBArena, site_pos: Vector3, slot: int) -> Vector3:
	return _site_post_plant_anchor(arena, site_pos, slot)

static func record_damage(arg1: Variant, arg2: Variant, arg3: Variant, arg4: Variant, arg5: Variant = null) -> void:
	if arg1 is Node and arg2 is SBActor:
		var match_node: Node = arg1
		var victim: SBActor = arg2
		var attacker: SBActor = arg3 as SBActor
		if victim == null or attacker == null:
			return
		if not match_node._bot_state.has(victim.id):
			return
		var st: Dictionary = match_node._bot_state[victim.id]
		st["damaged_from"] = attacker.position
		st["damaged_at"] = float(match_node._elapsed)
		return
	if arg1 is Dictionary and arg2 is Dictionary:
		var bot_states: Dictionary = arg1
		var actors: Dictionary = arg2
		var victim_id: int = int(arg3)
		var attacker_id: int = int(arg4)
		var elapsed: float = float(arg5) if arg5 != null else 0.0
		if not bot_states.has(victim_id) or not actors.has(attacker_id):
			return
		var attacker_actor: SBActor = actors[attacker_id]
		if attacker_actor == null:
			return
		var st2: Dictionary = bot_states[victim_id]
		st2["damaged_from"] = attacker_actor.position
		st2["damaged_at"] = elapsed

static func record_elimination(arg1: Variant, arg2: Variant, arg3: Variant, arg4: Variant, arg5: Variant = null) -> void:
	if arg1 is Node and arg2 is SBActor:
		var match_node: Node = arg1
		var victim: SBActor = arg2
		var death_pos: Vector3 = arg4 if arg4 is Vector3 else victim.position
		if not match_node.get("_team_ai_state") is Dictionary or match_node._team_ai_state.is_empty():
			match_node._team_ai_state = create_team_state()
		var zones: Array = match_node._team_ai_state.get("danger_zones", [])
		zones.append({
			"team": victim.team,
			"position": death_pos,
			"time": float(match_node._elapsed),
		})
		match_node._team_ai_state["danger_zones"] = zones
		for id: int in match_node.actors:
			var ally: SBActor = match_node.actors[id]
			if ally == null or not ally.alive or not ally.is_bot or ally.team != victim.team:
				continue
			if ally.position.distance_to(death_pos) <= 22.0 and match_node._bot_state.has(id):
				var st: Dictionary = match_node._bot_state[id]
				st["heard_pos"] = death_pos
				st["heard_at"] = float(match_node._elapsed)
		return
	if arg1 is Dictionary and arg2 is Dictionary and arg3 is Dictionary:
		var team_state: Dictionary = arg1
		var bot_states: Dictionary = arg2
		var actors: Dictionary = arg3
		var victim_id: int = int(arg4)
		var elapsed: float = float(arg5) if arg5 != null else 0.0
		if not actors.has(victim_id):
			return
		var victim_actor: SBActor = actors[victim_id]
		var zones2: Array = team_state.get("danger_zones", [])
		zones2.append({
			"team": victim_actor.team,
			"position": victim_actor.position,
			"time": elapsed,
		})
		team_state["danger_zones"] = zones2
		for id: int in actors:
			var ally2: SBActor = actors[id]
			if ally2 == null or not ally2.alive or not ally2.is_bot or ally2.team != victim_actor.team:
				continue
			if ally2.position.distance_to(victim_actor.position) <= 22.0 and bot_states.has(id):
				var st2: Dictionary = bot_states[id]
				st2["heard_pos"] = victim_actor.position
				st2["heard_at"] = elapsed

static func select_destination(match_node: Node, actor: SBActor, state: Dictionary, profile: Dictionary, interact_override: bool = false, defuser_id: int = -1) -> Vector3:
	if not match_node.get("_team_ai_state") is Dictionary or match_node._team_ai_state.is_empty():
		match_node._team_ai_state = create_team_state()
	_sync_team_blackboard(match_node, actor)
	var plan: Dictionary = _select_objective_and_destination(match_node, actor, state, profile)
	if interact_override and defuser_id == actor.id and match_node.bomb_planted:
		return match_node.planted_position
	return Vector3(plan.get("destination", actor.position))

static func tick_bot(match_node: Node, actor: SBActor, delta: float) -> void:
	if actor == null or not actor.alive:
		return
	var cmd: Dictionary = compute_bot_input(match_node, actor, delta)
	var move: Vector2 = cmd.get("move", Vector2.ZERO)
	var look: Vector2 = cmd.get("look", Vector2(actor.yaw, actor.pitch))
	var sprint: bool = bool(cmd.get("sprint", true))
	var reload_req: bool = bool(cmd.get("reload", false))
	actor.apply_tick(delta, move, look, sprint, false, reload_req)
	cmd["interact"] = bool(cmd.get("interact", false))
	cmd["fire"] = bool(cmd.get("fire", false))
	cmd["smoke"] = bool(cmd.get("smoke", false))
	cmd["grenade"] = bool(cmd.get("grenade", false))
	if match_node != null and match_node.get("_bot_state") is Dictionary and match_node._bot_state.has(actor.id):
		match_node._bot_state[actor.id]["last_cmd"] = cmd

static func acquire_target(match_node: Node, actor: SBActor, state: Dictionary, profile: Dictionary) -> SBActor:
	if match_node == null or actor == null or not actor.alive:
		return null
	var arena: SBArena = match_node.arena
	var best_target: SBActor = null
	var best_score := -INF
	var forward := -actor.global_basis.z
	forward.y = 0.0
	if forward.length_squared() < 0.001:
		forward = Vector3.FORWARD
	else:
		forward = forward.normalized()

	var max_dist: float = float(profile.get("max_sight_distance", 38.0))
	var fov_dot: float = float(profile.get("fov_dot", 0.15))
	var alert_until: float = maxf(float(state.get("damaged_at", -100.0)) + 2.5, float(state.get("heard_at", -100.0)) + 2.2)
	var is_alert: bool = match_node._elapsed <= alert_until
	var previous_target_id: int = int(state.get("last_target", -1))

	for id: int in match_node.actors:
		var other: SBActor = match_node.actors[id]
		if other == null or not other.alive or other.team == actor.team:
			continue
		var to_enemy: Vector3 = other.position - actor.position
		var dist: float = to_enemy.length()
		if dist > max_dist:
			continue
		var dir := Vector3(to_enemy.x, 0.0, to_enemy.z).normalized()
		var facing_dot: float = forward.dot(dir)
		if not is_alert and dist > 4.5 and facing_dot < fov_dot:
			continue
		if arena != null and arena.smoke_obscures(actor.eye_position(), other.eye_position()):
			continue
		if not actor.can_see(other):
			continue

		var score: float = 100.0 - dist * 1.65 + facing_dot * 8.0
		if id == match_node.bomb_carrier_id:
			score += 6.0
		if other.planting or other.defusing:
			score += 14.0
		if id == previous_target_id:
			score += TARGET_HYSTERESIS_BONUS
		if score > best_score:
			best_score = score
			best_target = other

	if best_target != null:
		if previous_target_id != best_target.id:
			state["last_target"] = best_target.id
			state["target_seen_since"] = match_node._elapsed
		state["last_seen"] = best_target.position
		state["seen_at"] = match_node._elapsed
		if match_node.get("_team_ai_state") is Dictionary:
			var callouts: Dictionary = match_node._team_ai_state.get("callouts", {})
			callouts[actor.team] = {
				"position": best_target.position,
				"time": match_node._elapsed,
				"target_id": best_target.id,
			}
			match_node._team_ai_state["callouts"] = callouts
	else:
		var prev_target: SBActor = match_node.actors.get(previous_target_id, null) if previous_target_id != -1 else null
		if prev_target == null or not prev_target.alive or (match_node._elapsed - float(state.get("seen_at", -100.0))) > 0.35:
			state["last_target"] = -1
	return best_target

static func safe_navigate(arena: SBArena, from: Vector3, to: Vector3) -> Vector3:
	if arena == null:
		return to
	var flat_from := Vector3(from.x, 0.0, from.z)
	var safe_to := snap_to_walkable(arena, to, flat_from)
	if arena.waypoints.is_empty():
		return safe_to
	if arena.can_traverse(flat_from, safe_to) and flat_from.distance_to(safe_to) > 0.25:
		return safe_to

	var start := _nearest_visible_waypoint(arena, flat_from, -1)
	var finish := _nearest_visible_waypoint(arena, safe_to, -1)
	if start == -1 or finish == -1:
		return safe_to
	if start == finish and flat_from.distance_to(safe_to) > 0.35:
		var alt_finish := _nearest_visible_waypoint(arena, safe_to, start)
		if alt_finish != -1:
			finish = alt_finish
	var path: PackedVector3Array = arena._navigation.get_point_path(start, finish)
	if path.size() > 1:
		for idx in range(1, path.size()):
			var wp := path[idx]
			if flat_from.distance_to(wp) > 0.45:
				if idx + 1 < path.size() and arena.can_traverse(flat_from, path[idx + 1]):
					return path[idx + 1]
				return wp
		return path[path.size() - 1]
	if path.size() == 1 and flat_from.distance_to(path[0]) > 0.45 and arena.can_traverse(flat_from, path[0]):
		return path[0]
	if arena.can_traverse(flat_from, safe_to):
		return safe_to
	var step_candidate := snap_to_walkable(arena, flat_from + (safe_to - flat_from).limit_length(2.4), flat_from)
	if flat_from.distance_to(step_candidate) > 0.35 and arena.can_traverse(flat_from, step_candidate):
		return step_candidate
	return arena.bot_navigation(flat_from, safe_to)

static func snap_to_walkable(arena: SBArena, pos: Vector3, reference_from: Variant = null) -> Vector3:
	var flat_pos := Vector3(pos.x, 0.0, pos.z)
	if arena == null or not arena.is_blocked(flat_pos, 0.58):
		return flat_pos
	var has_ref: bool = reference_from is Vector3
	var ref_pos: Vector3 = Vector3(reference_from.x, 0.0, reference_from.z) if has_ref else flat_pos
	var to_ref: Vector3 = ref_pos - flat_pos
	var base_angle: float = atan2(to_ref.z, to_ref.x) if to_ref.length_squared() > 0.001 else 0.0
	var best_candidate := flat_pos
	var best_score := INF
	for radius in [0.9, 1.5, 2.2, 3.0, 3.8]:
		for i in range(12):
			var angle: float = base_angle + float(i) * (TAU / 12.0)
			var candidate := Vector3(
				clampf(flat_pos.x + cos(angle) * float(radius), -22.5, 22.5),
				0.0,
				clampf(flat_pos.z + sin(angle) * float(radius), -22.5, 22.5)
			)
			if arena.is_blocked(candidate, 0.58):
				continue
			var score: float = candidate.distance_to(flat_pos)
			if has_ref:
				score += candidate.distance_to(ref_pos) * 0.25
				if arena.can_traverse(ref_pos, candidate):
					score -= 3.5
			if score < best_score:
				best_score = score
				best_candidate = candidate
	if best_score < INF:
		return best_candidate
	var nearest_idx := _nearest_visible_waypoint(arena, flat_pos, -1)
	if nearest_idx != -1:
		return arena.waypoints[nearest_idx]
	return flat_pos

static func _nearest_visible_waypoint(arena: SBArena, pos: Vector3, exclude_index: int = -1) -> int:
	var best_vis := -1
	var best_vis_dist := INF
	var best_any := -1
	var best_any_dist := INF
	for i in range(arena.waypoints.size()):
		if i == exclude_index:
			continue
		var wp: Vector3 = arena.waypoints[i]
		var d: float = pos.distance_squared_to(wp)
		if d < best_any_dist:
			best_any_dist = d
			best_any = i
		if d < best_vis_dist and arena.can_traverse(pos, wp):
			best_vis_dist = d
			best_vis = i
	return best_vis if best_vis != -1 else best_any

static func find_tactical_cover(arena: SBArena, from: Vector3, threat_pos: Vector3) -> Vector3:
	var best_spot := from
	var best_score := -INF
	for spot: Vector3 in COVER_SPOTS:
		if arena != null and arena.is_blocked(spot, 0.58):
			continue
		var dist_self: float = from.distance_to(spot)
		if dist_self > 16.0:
			continue
		var occludes_threat: bool = arena != null and not arena.can_traverse(spot, threat_pos)
		var dist_threat: float = spot.distance_to(threat_pos)
		var score: float = (28.0 if occludes_threat else 0.0) - dist_self * 1.4 + minf(dist_threat, 20.0) * 0.5
		if score > best_score:
			best_score = score
			best_spot = spot
	return snap_to_walkable(arena, best_spot, from)

static func _update_auditory_and_team_memory(match_node: Node, actor: SBActor, state: Dictionary, profile: Dictionary) -> void:
	var prev_heard_at: float = float(state.get("heard_at", -100.0))
	if prev_heard_at > -50.0 and (match_node._elapsed - prev_heard_at) >= SOUND_MEMORY_SECONDS:
		state["heard_at"] = -100.0
		state["heard_pos"] = Vector3.ZERO
	var hearing_range: float = float(profile.get("hearing_range", 25.0))
	var best_heard_time: float = float(state.get("heard_at", -100.0))
	var best_heard_pos: Vector3 = state.get("heard_pos", actor.position)
	if match_node.get("_heard") is Dictionary:
		for heard_id: Variant in match_node._heard:
			var ev: Dictionary = match_node._heard[heard_id]
			var shooter: SBActor = match_node.actors.get(int(heard_id), null)
			var shooter_team: int = shooter.team if shooter != null else int(ev.get("team", -1))
			if shooter_team == -1 or shooter_team == actor.team:
				continue
			var pos: Vector3 = ev.get("position", Vector3.ZERO)
			var t: float = float(ev.get("time", -100.0))
			var age: float = match_node._elapsed - t
			if age < 0.0 or age >= SOUND_MEMORY_SECONDS:
				continue
			var dist: float = actor.position.distance_to(pos)
			if dist <= hearing_range and t >= best_heard_time:
				best_heard_time = t
				best_heard_pos = pos
	elif match_node.get("_heard") is Array:
		for item: Variant in match_node._heard:
			if not item is Dictionary:
				continue
			var ev2: Dictionary = item
			if int(ev2.get("team", -1)) == actor.team:
				continue
			var pos2: Vector3 = ev2.get("position", Vector3.ZERO)
			var t2: float = float(ev2.get("time", -100.0))
			var age2: float = match_node._elapsed - t2
			if age2 < 0.0 or age2 >= SOUND_MEMORY_SECONDS:
				continue
			if actor.position.distance_to(pos2) <= hearing_range and t2 >= best_heard_time:
				best_heard_time = t2
				best_heard_pos = pos2
	state["heard_at"] = best_heard_time
	state["heard_pos"] = best_heard_pos

	if match_node.get("_team_ai_state") is Dictionary:
		var callouts: Dictionary = match_node._team_ai_state.get("callouts", {})
		if callouts.has(actor.team):
			var callout: Dictionary = callouts[actor.team]
			var c_time: float = float(callout.get("time", -100.0))
			if match_node._elapsed - c_time < CALLOUT_MEMORY_SECONDS and match_node._elapsed - float(state.get("seen_at", -100.0)) > 1.5:
				if c_time > float(state.get("heard_at", -100.0)):
					state["heard_pos"] = callout.get("position", state["heard_pos"])
					state["heard_at"] = c_time

static func _sync_team_blackboard(match_node: Node, _actor: SBActor) -> void:
	if not match_node.get("_team_ai_state") is Dictionary or match_node._team_ai_state.is_empty():
		match_node._team_ai_state = create_team_state()
	var carrier: SBActor = match_node.actors.get(match_node.bomb_carrier_id, null)
	if carrier != null and carrier.alive and match_node.arena != null and match_node.arena.sites.size() >= 2:
		var d0: float = carrier.position.distance_to(match_node.arena.sites[0])
		var d1: float = carrier.position.distance_to(match_node.arena.sites[1])
		if minf(d0, d1) < 22.0 and absf(d0 - d1) > 5.0:
			var committed_site: int = 0 if d0 < d1 else 1
			match_node._team_ai_state["primary_site"] = committed_site
			match_node._team_ai_state["target_site"] = committed_site
			match_node._team_ai_state["site_locked"] = true

static func _select_objective_and_destination(match_node: Node, actor: SBActor, state: Dictionary, profile: Dictionary) -> Dictionary:
	var arena: SBArena = match_node.arena
	_update_auditory_and_team_memory(match_node, actor, state, profile)
	var destination: Vector3 = actor.position
	var interact := false
	var is_carrier: bool = (actor.id == match_node.bomb_carrier_id)
	var primary_site: int = int(match_node._team_ai_state.get("primary_site", 0)) if match_node.get("_team_ai_state") is Dictionary else 0
	var mem_window: float = float(profile.get("memory_duration", 2.0))
	var has_visual_memory: bool = (match_node._elapsed - float(state.get("seen_at", -100.0))) < mem_window
	var has_sound_memory: bool = (match_node._elapsed - float(state.get("heard_at", -100.0))) < SOUND_MEMORY_SECONDS

	if actor.team == SBArena.TEAM_ATTACK:
		if not match_node.bomb_planted:
			var site_pos: Vector3 = arena.sites[primary_site]
			if is_carrier:
				state["role"] = "carrier"
				destination = site_pos
				if actor.position.distance_to(site_pos) < SBArena.PLANT_RADIUS - 0.35:
					interact = true
				elif has_visual_memory:
					state["role"] = "pursue_memory"
					destination = Vector3(state.get("last_seen", destination))
			else:
				var carrier: SBActor = match_node.actors.get(match_node.bomb_carrier_id, null)
				if actor.slot == 4:
					state["role"] = "split_flank"
					destination = Vector3(0.0, 0.0, 4.0) if actor.position.z < 2.0 else site_pos
				elif actor.slot % 2 == 1:
					state["role"] = "entry"
					destination = site_pos + Vector3(2.2 if primary_site == 0 else -2.2, 0.0, -2.5)
				else:
					state["role"] = "escort"
					if carrier != null and carrier.alive:
						var offset := Vector3(-2.4 if actor.slot % 2 == 0 else 2.4, 0.0, -2.0)
						destination = snap_to_walkable(arena, carrier.position + offset, actor.position)
					else:
						destination = site_pos
				if has_visual_memory:
					state["role"] = "pursue_memory"
					destination = Vector3(state.get("last_seen", destination))
				elif has_sound_memory:
					state["role"] = "investigate_sound"
					destination = Vector3(state.get("heard_pos", destination))
		else:
			state["role"] = "post_plant_hold"
			destination = _site_post_plant_anchor(arena, match_node.planted_position, actor.slot)
			if has_visual_memory:
				state["role"] = "pursue_memory"
				destination = Vector3(state.get("last_seen", destination))
	else:
		if match_node.bomb_planted:
			var defuser_id: int = _choose_designated_defuser(match_node)
			if actor.id == defuser_id:
				state["role"] = "retake_defuse"
				destination = match_node.planted_position
				if actor.position.distance_to(match_node.planted_position) < SBArena.DEFUSE_RADIUS - 0.35:
					interact = true
			else:
				state["role"] = "retake_cover"
				destination = _site_post_plant_anchor(arena, match_node.planted_position, actor.slot)
				if has_visual_memory:
					state["role"] = "pursue_memory"
					destination = Vector3(state.get("last_seen", destination))
		else:
			state["role"] = "anchor"
			destination = DEFENDER_ANCHORS[posmod(actor.slot, DEFENDER_ANCHORS.size())]
			if has_visual_memory:
				state["role"] = "pursue_memory"
				destination = Vector3(state.get("last_seen", destination))
			elif has_sound_memory:
				state["role"] = "investigate_sound"
				destination = Vector3(state.get("heard_pos", destination))

	return {
		"destination": snap_to_walkable(arena, destination, actor.position) if not interact else destination,
		"interact": interact,
	}

static func _choose_designated_defuser(match_node: Node) -> int:
	var best_id := -1
	var best_dist := INF
	for id: int in match_node.actors:
		var a: SBActor = match_node.actors[id]
		if a == null or not a.alive or a.team != SBArena.TEAM_DEFEND:
			continue
		if a.defusing:
			return id
		var d: float = a.position.distance_to(match_node.planted_position)
		if d < best_dist:
			best_dist = d
			best_id = id
	return best_id

static func _site_post_plant_anchor(arena: SBArena, site_pos: Vector3, slot: int) -> Vector3:
	var offsets: Array[Vector3] = [
		Vector3(-3.2, 0.0, -2.6),
		Vector3(3.2, 0.0, -2.6),
		Vector3(-3.6, 0.0, 1.4),
		Vector3(3.6, 0.0, 1.4),
		Vector3(0.0, 0.0, -3.6),
	]
	var base_idx: int = posmod(slot, offsets.size())
	for step in range(offsets.size()):
		var candidate: Vector3 = site_pos + offsets[posmod(base_idx + step, offsets.size())]
		if arena == null or not arena.is_blocked(candidate, 0.58):
			return snap_to_walkable(arena, candidate, site_pos)
	return snap_to_walkable(arena, site_pos + Vector3(0.0, 0.0, -2.2), site_pos)

static func compute_bot_input(match_node: Node, actor: SBActor, delta: float) -> Dictionary:
	if not match_node._bot_state.has(actor.id):
		match_node._bot_state[actor.id] = create_state(actor)
	var state: Dictionary = match_node._bot_state[actor.id]
	var profile: Dictionary = profile_for(str(match_node.bot_difficulty))
	var arena: SBArena = match_node.arena

	_sync_team_blackboard(match_node, actor)
	_update_auditory_and_team_memory(match_node, actor, state, profile)

	var target: SBActor = acquire_target(match_node, actor, state, profile)
	var plan: Dictionary = _select_objective_and_destination(match_node, actor, state, profile)
	var destination: Vector3 = plan["destination"]
	var interact: bool = bool(plan["interact"])

	if target != null and interact and actor.position.distance_to(target.position) < 16.0:
		interact = false

	var move := Vector2.ZERO
	var look := Vector2(actor.yaw, actor.pitch)
	var sprint := true
	var fire := false
	var reload_req := bool(actor.ammo <= 0 and actor.reserve > 0)
	var use_smoke := false
	var use_grenade := false

	var weapon_def: Dictionary = SBWeapons.get_weapon(actor.weapon_id)
	var clip_size: int = int(weapon_def.get("clip_size", 30))
	if target == null and not interact and actor.ammo < int(float(clip_size) * 0.35) and actor.reserve > 0:
		reload_req = true

	if target != null:
		var aim_point: Vector3 = target.eye_position() - Vector3(0.0, 0.14, 0.0)
		var to_target: Vector3 = aim_point - actor.eye_position()
		var flat_len: float = maxf(0.001, Vector2(to_target.x, to_target.z).length())
		var desired_yaw: float = atan2(-to_target.x, -to_target.z)
		var desired_pitch: float = clampf(atan2(to_target.y, flat_len), -0.65, 0.65)

		var jitter: float = float(profile.get("aim_jitter", 0.045))
		var wobble_phase: float = match_node._elapsed * 5.3 + float(actor.id) * 1.7
		desired_yaw += sin(wobble_phase) * jitter
		desired_pitch += cos(wobble_phase * 1.13) * jitter * 0.55

		var turn_step: float = float(profile.get("turn_speed", 5.4)) * delta
		var new_yaw: float = rotate_toward(actor.yaw, desired_yaw, turn_step)
		var new_pitch: float = move_toward(actor.pitch, desired_pitch, turn_step * 0.8)
		look = Vector2(new_yaw, new_pitch)

		var dist_to_target: float = actor.position.distance_to(target.position)
		var seen_elapsed: float = match_node._elapsed - float(state.get("target_seen_since", match_node._elapsed))
		var yaw_error: float = absf(angle_difference(new_yaw, desired_yaw))
		var max_fire_cone: float = 0.24 if dist_to_target < 12.0 else 0.15

		if seen_elapsed >= float(profile.get("reaction_delay", 0.22)) and yaw_error <= max_fire_cone and not actor.reloading and actor.ammo > 0:
			var burst_len: float = float(profile.get("burst_duration", 0.34))
			var burst_pause: float = float(profile.get("burst_pause", 0.18))
			var cycle: float = burst_len + burst_pause
			var phase: float = fmod(maxf(0.0, seen_elapsed - float(profile.get("reaction_delay", 0.22))), cycle)
			if dist_to_target < 9.0 or phase <= burst_len:
				fire = true

		sprint = false
		var retreat_hp: float = float(profile.get("retreat_hp", 28.0))
		if (actor.hp <= retreat_hp or actor.reloading) and not interact:
			var cover_dest: Vector3 = find_tactical_cover(arena, actor.position, target.position)
			var wp_cover: Vector3 = safe_navigate(arena, actor.position, cover_dest)
			var dir_cover: Vector3 = (wp_cover - actor.position)
			dir_cover.y = 0.0
			if dir_cover.length_squared() > 0.05:
				var local_cover: Vector3 = Basis(Vector3.UP, -look.x) * dir_cover.normalized()
				move = Vector2(local_cover.x, -local_cover.z)
		else:
			var strafe_wave: float = sin(match_node._elapsed * float(profile.get("strafe_freq", 2.3)) + float(state.get("strafe_seed", 0.0)))
			var strafe_dir: float = 0.85 if strafe_wave >= 0.0 else -0.85
			if actor.weapon_id == "shotgun" or actor.weapon_id == "smg":
				move = Vector2(strafe_dir, 0.9 if dist_to_target > 7.5 else 0.0)
			elif dist_to_target > 22.0:
				move = Vector2(strafe_dir * 0.75, 0.65)
			else:
				move = Vector2(strafe_dir, 0.0)
	else:
		if match_node._elapsed > float(state.get("utility_cooldown_until", 0.0)) and actor.smokes > 0:
			var util_chance: float = float(profile.get("utility_chance", 0.5))
			if util_chance >= 0.45 and match_node._elapsed - float(state.get("seen_at", -100.0)) < 2.2:
				var mem_pos: Vector3 = state.get("last_seen", actor.position)
				if actor.position.distance_to(mem_pos) > 9.0 and actor.position.distance_to(mem_pos) < 26.0:
					use_smoke = true
					state["utility_cooldown_until"] = match_node._elapsed + 12.0

		var has_damage_look := false
		if match_node._elapsed - float(state.get("damaged_at", -100.0)) < 1.5 and not interact:
			var to_dmg: Vector3 = Vector3(state.get("damaged_from", actor.position)) - actor.position
			if to_dmg.length_squared() > 0.1:
				var dmg_yaw: float = atan2(-to_dmg.x, -to_dmg.z)
				look = Vector2(rotate_toward(actor.yaw, dmg_yaw, float(profile.get("turn_speed", 5.0)) * delta), 0.0)
				has_damage_look = true

		if actor.position.distance_to(destination) > 1.8 and not interact:
			var target_dest: Vector3 = destination
			if match_node._elapsed < float(state.get("repath_until", -100.0)):
				target_dest = snap_to_walkable(arena, actor.position + Vector3(state.get("repath_offset", Vector3.ZERO)), actor.position)
			var wp: Vector3 = safe_navigate(arena, actor.position, target_dest)
			var direction: Vector3 = wp - actor.position
			direction.y = 0.0
			if direction.length_squared() > 0.01:
				if not has_damage_look:
					var nav_yaw: float = atan2(-direction.x, -direction.z)
					look = Vector2(nav_yaw, 0.0)
				var local_step: Vector3 = Basis(Vector3.UP, -look.x) * direction.normalized()
				move = Vector2(local_step.x, -local_step.z)
		elif not interact and not has_damage_look:
			var scan_yaw: float = actor.yaw + sin(match_node._elapsed * 1.4 + float(actor.id)) * 0.65 * delta
			look = Vector2(scan_yaw, 0.0)

	if move.length() > 0.2 and not interact:
		if actor.position.distance_to(Vector3(state.get("last_pos", actor.position))) < 0.05:
			state["stuck"] = float(state.get("stuck", 0.0)) + delta
			if float(state["stuck"]) > STUCK_REPATH_SECONDS:
				var side_angle: float = actor.yaw + (PI * 0.5 if actor.id % 2 == 0 else -PI * 0.5)
				var escape_vec := Vector3(-sin(side_angle), 0.0, -cos(side_angle)) * 3.2
				state["repath_offset"] = escape_vec
				state["repath_until"] = match_node._elapsed + 0.9
				state["stuck"] = 0.0
				move = Vector2(1.0 if actor.id % 2 == 0 else -1.0, 1.0).normalized()
		else:
			state["stuck"] = 0.0
	state["last_pos"] = actor.position

	if interact:
		move = Vector2.ZERO
		sprint = false
		fire = false

	return {
		"move": move,
		"look": look,
		"sprint": sprint,
		"crouch": false,
		"fire": fire,
		"reload": reload_req,
		"interact": interact,
		"smoke": use_smoke,
		"grenade": use_grenade,
	}
