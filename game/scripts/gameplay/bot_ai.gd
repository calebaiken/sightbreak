class_name SBBotAI
extends RefCounted

## Modular Tactical Bot Intelligence for SIGHTBREAK.
## Separates perception, bounded memory, team coordination, objective roles,
## cover/navigation selection, and difficulty profiles from TacticalMatch.
## Produces only valid player-equivalent input_state dictionaries; never mutates
## authoritative health, ammo, cooldowns, hit registration, or economy balances.

const SOUND_MEMORY_SECONDS := 3.5
const TEAM_REPORT_RADIUS := 30.0
const TEAM_DEATH_ALERT_RADIUS := 24.0
const TARGET_HYSTERESIS_BONUS := 4.5
const MAX_BURST_SECONDS := 0.55
const BURST_COOLDOWN_SECONDS := 0.16

const PROFILES := {
	"easy": {
		"reaction_delay": 0.60,
		"turn_speed": 3.5,
		"aim_error": 0.045,
		"vision_range": 28.0,
		"fov_dot": -0.05,
		"memory_duration": 2.0,
		"hearing_range": 18.0,
		"sound_noise": 2.4,
		"recoil_compensation": 0.15,
		"retreat_hp": 0.0,
		"team_comms": false,
		"counter_strafe": false,
		"utility_use": false,
		"sidearm_fallback": false
	},
	"normal": {
		"reaction_delay": 0.35,
		"turn_speed": 5.0,
		"aim_error": 0.022,
		"vision_range": 38.0,
		"fov_dot": -0.15,
		"memory_duration": 3.8,
		"hearing_range": 26.0,
		"sound_noise": 1.1,
		"recoil_compensation": 0.65,
		"retreat_hp": 28.0,
		"team_comms": true,
		"counter_strafe": true,
		"utility_use": true,
		"sidearm_fallback": true
	},
	"hard": {
		"reaction_delay": 0.18,
		"turn_speed": 7.0,
		"aim_error": 0.008,
		"vision_range": 46.0,
		"fov_dot": -0.25,
		"memory_duration": 5.5,
		"hearing_range": 34.0,
		"sound_noise": 0.35,
		"recoil_compensation": 0.92,
		"retreat_hp": 38.0,
		"team_comms": true,
		"counter_strafe": true,
		"utility_use": true,
		"sidearm_fallback": true
	}
}

## Site-specific tactical anchor positions validated against RelayYard obstacle AABBs.
const SITE_HOLD_OFFSETS := {
	0: [
		Vector3(3.0, 0.0, 2.0),
		Vector3(0.0, 0.0, -4.0),
		Vector3(6.0, 0.0, -1.0),
		Vector3(-3.0, 0.0, -4.0),
		Vector3(3.0, 0.0, 5.0)
	],
	1: [
		Vector3(-3.0, 0.0, 2.0),
		Vector3(0.0, 0.0, -4.0),
		Vector3(-6.0, 0.0, -1.0),
		Vector3(3.0, 0.0, -4.0),
		Vector3(-3.0, 0.0, 5.0)
	]
}

## Defender pre-plant anchor positions covering West Freight (Site A), Mid, and East Relay (Site B).
const DEFENDER_ANCHORS := [
	Vector3(-15.0, 0.0, 12.0),
	Vector3(15.0, 0.0, 12.0),
	Vector3(-12.0, 0.0, 6.0),
	Vector3(12.0, 0.0, 6.0),
	Vector3(0.0, 0.0, 9.0)
]

## Mid-yardStaging waypoints for split/flank attacker approaches before converging on site.
const ATTACK_SPLIT_WAYPOINTS := {
	0: Vector3(-3.0, 0.0, -3.0),
	1: Vector3(3.0, 0.0, -3.0)
}

static func profile_for(difficulty: String) -> Dictionary:
	return PROFILES.get(difficulty, PROFILES["normal"])

static func get_profile(difficulty: String) -> Dictionary:
	return profile_for(difficulty)

static func create_state(actor: SBActor) -> Dictionary:
	return new_bot_state(actor.position if actor != null else Vector3.ZERO)

static func new_bot_state(initial_pos: Vector3 = Vector3.ZERO) -> Dictionary:
	return {
		"reaction": 0.0,
		"target": 0,
		"last_position": initial_pos,
		"stuck": 0.0,
		"last_seen": Vector3.ZERO,
		"seen_at": -100.0,
		"heard_pos": Vector3.ZERO,
		"heard_at": -100.0,
		"damaged_at": -100.0,
		"damaged_from": Vector3.ZERO,
		"attacker_id": 0,
		"burst_time": 0.0,
		"burst_cooldown": 0.0,
		"recovery_wp": -1,
		"recovery_until": -100.0,
		"smoke_used": false,
		"grenade_used": false,
		"role": "support"
	}

static func create_team_state() -> Dictionary:
	return new_team_state()

static func new_team_state() -> Dictionary:
	return {
		0: {
			"primary_site": 0,
			"target_site": 0,
			"contacts": {},
			"death_alert_pos": Vector3.ZERO,
			"death_alert_at": -100.0
		},
		1: {
			"primary_site": 0,
			"target_site": 0,
			"contacts": {},
			"death_alert_pos": Vector3.ZERO,
			"death_alert_at": -100.0
		}
	}

static func select_round_plan(match_node: Node, _team: int = 0) -> Dictionary:
	var round_num: int = int(match_node.round_number)
	var target_site: int = round_num % 2
	var carrier: SBActor = match_node.actors.get(match_node.objective_carrier) as SBActor
	if carrier != null and carrier.alive and not match_node._is_bot(carrier.actor_id):
		var dist_a: float = carrier.position.distance_to(match_node.arena.sites[0])
		var dist_b: float = carrier.position.distance_to(match_node.arena.sites[1])
		if minf(dist_a, dist_b) < 22.0 or carrier.position.z > -8.0:
			target_site = 0 if dist_a <= dist_b else 1
	if match_node.get("_team_ai_state") != null and match_node._team_ai_state is Dictionary:
		if not match_node._team_ai_state.has(0):
			match_node._team_ai_state[0] = {"primary_site": target_site, "target_site": target_site, "contacts": {}}
		else:
			match_node._team_ai_state[0]["primary_site"] = target_site
			match_node._team_ai_state[0]["target_site"] = target_site
	return {"target_site": target_site, "primary_site": target_site}

static func get_site_hold_position(arena: RelayYard, site_pos: Vector3, slot: int) -> Vector3:
	var site_idx: int = 0 if site_pos.x < 0.0 else 1
	var offsets: Array = SITE_HOLD_OFFSETS.get(site_idx, SITE_HOLD_OFFSETS[0])
	var candidate: Vector3 = site_pos + (offsets[posmod(slot, offsets.size())] as Vector3)
	if arena._clear_path(candidate, candidate + Vector3(0.01, 0.0, 0.01)):
		return candidate
	var nearest_wp: Vector3 = site_pos
	var best_dist: float = INF
	for wp: Vector3 in arena.waypoints:
		var d: float = wp.distance_squared_to(candidate)
		if d < best_dist:
			best_dist = d
			nearest_wp = wp
	return nearest_wp

static func choose_buy_weapon(actor: SBActor, difficulty: String, round_number: int) -> String:
	if difficulty != "easy" and actor.credits >= 3200 and (actor.actor_id + round_number) % 5 == 0:
		return "marksman"
	if actor.credits >= 2400:
		return "rifle"
	return "smg"

static func buy_equipment(actor: SBActor, difficulty: String, round_number: int) -> String:
	var choice: String = choose_buy_weapon(actor, difficulty, round_number)
	actor.buy_weapon(choice)
	var spec: Dictionary = SBWeapons.get_weapon(actor.weapon_id)
	actor.ammo = int(spec.get("magazine", 30))
	actor.reserve = int(spec.get("reserve", 60))
	actor.smokes = 1
	actor.grenades = 1
	return actor.weapon_id

static func record_damage(arg1: Variant, arg2: Variant, arg3: Variant, arg4: Variant, arg5: Variant = null) -> void:
	var bot_states: Dictionary
	var actors: Dictionary
	var victim_id: int
	var attacker_id: int
	var elapsed: float
	if arg1 is Node:
		var match_node: Node = arg1
		bot_states = match_node._bot_state
		actors = match_node.actors
		victim_id = int(arg2)
		attacker_id = int(arg3)
		elapsed = float(match_node._elapsed)
	else:
		bot_states = arg1 as Dictionary
		actors = arg2 as Dictionary
		victim_id = int(arg3)
		attacker_id = int(arg4)
		elapsed = float(arg5)
	if not bot_states.has(victim_id):
		return
	var state: Dictionary = bot_states[victim_id]
	state["damaged_at"] = elapsed
	state["attacker_id"] = attacker_id
	var attacker: SBActor = actors.get(attacker_id) as SBActor
	var victim: SBActor = actors.get(victim_id) as SBActor
	if attacker != null and victim != null and attacker.team != victim.team:
		# Legitimate directional hit indicator (like a player's damage indicator), not live wallhack tracking.
		var dir: Vector3 = (attacker.position - victim.position).normalized()
		state["damaged_from"] = victim.position + dir * 10.0

static func record_elimination(arg1: Variant, arg2: Variant, arg3: Variant, arg4: Variant, arg5: Variant = null) -> void:
	var team_state: Dictionary
	var bot_states: Dictionary
	var actors: Dictionary
	var victim_id: int
	var elapsed: float
	if arg1 is Node:
		var match_node: Node = arg1
		team_state = match_node._team_ai_state if match_node.get("_team_ai_state") is Dictionary else {}
		bot_states = match_node._bot_state
		actors = match_node.actors
		victim_id = int(arg2)
		elapsed = float(match_node._elapsed)
	else:
		team_state = arg1 as Dictionary
		bot_states = arg2 as Dictionary
		actors = arg3 as Dictionary
		victim_id = int(arg4)
		elapsed = float(arg5)
	var victim: SBActor = actors.get(victim_id) as SBActor
	if victim == null:
		return
	if not team_state.has(victim.team):
		team_state[victim.team] = {"primary_site": 0, "target_site": 0, "contacts": {}}
	var t_state: Dictionary = team_state[victim.team]
	t_state["death_alert_pos"] = victim.position
	t_state["death_alert_at"] = elapsed
	for ally: SBActor in actors.values():
		if ally.alive and ally.team == victim.team and ally.actor_id != victim_id and bot_states.has(ally.actor_id):
			if ally.position.distance_to(victim.position) <= TEAM_DEATH_ALERT_RADIUS:
				var st: Dictionary = bot_states[ally.actor_id]
				if elapsed - float(st.get("seen_at", -100.0)) > 1.5:
					st["heard_pos"] = victim.position
					st["heard_at"] = elapsed

static func nearest_defender(match_node: Node) -> int:
	var chosen: int = 0
	var nearest: float = INF
	for actor: SBActor in match_node.actors.values():
		if not actor.alive or actor.team != 1:
			continue
		# A human already holding interact keeps priority; bots provide covering fire.
		if not match_node._is_bot(actor.actor_id) and bool(actor.input_state.get("interact", false)) and actor.position.distance_to(match_node.objective_position) <= 2.8:
			return actor.actor_id
		var distance: float = actor.position.distance_squared_to(match_node.objective_position)
		if match_node._is_bot(actor.actor_id) and (distance < nearest or (is_equal_approx(distance, nearest) and actor.actor_id < chosen)):
			chosen = actor.actor_id
			nearest = distance
	return chosen

static func cover_position(match_node: Node, actor: SBActor, threat: SBActor) -> Vector3:
	if threat == null:
		return actor.position
	return cover_position_from_point(match_node, actor, threat.position)

static func cover_position_from_point(match_node: Node, actor: SBActor, threat_pos: Vector3) -> Vector3:
	var choice: Vector3 = actor.position
	var best_score: float = INF
	var space: PhysicsDirectSpaceState3D = match_node.get_world_3d().direct_space_state
	var threat_eye: Vector3 = threat_pos + Vector3.UP * 1.4
	for point: Vector3 in match_node.arena.waypoints:
		var distance: float = actor.position.distance_to(point)
		if distance < 1.0 or distance > 11.5:
			continue
		var query := PhysicsRayQueryParameters3D.create(threat_eye, point + Vector3.UP * 1.0, 1)
		if not space.intersect_ray(query).is_empty():
			# Prefer close cover that moves away from the threat line.
			var away_bonus: float = clampf((point.distance_to(threat_pos) - actor.position.distance_to(threat_pos)) * 0.25, -1.5, 1.5)
			var score: float = distance - away_bonus
			if score < best_score:
				best_score = score
				choice = point
	return choice

static func safe_navigate(arena: RelayYard, from: Vector3, to: Vector3) -> Vector3:
	var wp: Vector3 = arena.bot_navigation(from, to)
	if wp.distance_squared_to(from) > 0.001 or from.distance_to(to) <= 1.2:
		return wp
	# Fallback when 'from' or 'to' sits inside an expanded obstacle AABB so _clear_path fails on all waypoints.
	if arena.waypoints.is_empty():
		return to
	var start := -1
	var finish := -1
	var start_clear_dist := INF
	var finish_clear_dist := INF
	var nearest_start := 0
	var nearest_finish := 0
	var nearest_start_dist := INF
	var nearest_finish_dist := INF
	for i in range(arena.waypoints.size()):
		var p: Vector3 = arena.waypoints[i]
		var ds: float = from.distance_squared_to(p)
		if ds < nearest_start_dist:
			nearest_start_dist = ds
			nearest_start = i
		if ds < start_clear_dist and arena._clear_path(from, p):
			start_clear_dist = ds
			start = i
		var df: float = to.distance_squared_to(p)
		if df < nearest_finish_dist:
			nearest_finish_dist = df
			nearest_finish = i
		if df < finish_clear_dist and arena._clear_path(to, p):
			finish_clear_dist = df
			finish = i
	if start < 0:
		start = nearest_start
	if finish < 0:
		finish = nearest_finish
	if start == finish:
		return arena.waypoints[finish]
	var path: PackedVector3Array = arena._navigation.get_point_path(start, finish)
	if path.is_empty():
		return arena.waypoints[nearest_start]
	for i in range(path.size() - 1, -1, -1):
		if arena._clear_path(from, path[i]) and path[i].distance_squared_to(from) > 0.04:
			return path[i]
	return path[1] if path.size() > 1 else path[0]

static func acquire_target(match_node: Node, actor: SBActor, state: Dictionary, profile: Dictionary) -> SBActor:
	var best_enemy: SBActor = null
	var best_score: float = float(profile.get("vision_range", 35.0))
	var fov_dot: float = float(profile.get("fov_dot", -0.15))
	var current_target_id: int = int(state.get("target", 0))
	var recently_damaged: bool = match_node._elapsed - float(state.get("damaged_at", -100.0)) < 1.2
	var recent_attacker_id: int = int(state.get("attacker_id", 0))
	var facing := Vector3(-sin(actor.yaw), 0.0, -cos(actor.yaw))
	var defuser_id: int = nearest_defender(match_node) if match_node.objective_state == "planted" else 0

	for enemy: SBActor in match_node.actors.values():
		if enemy.team == actor.team or not enemy.alive:
			continue
		var distance: float = actor.position.distance_to(enemy.position)
		if distance > float(profile.get("vision_range", 35.0)):
			continue
		var toward: Vector3 = (enemy.position - actor.position).normalized()
		# Allow peripheral awareness if this specific enemy just shot us and is within line of sight.
		var in_fov: bool = facing.dot(toward) > fov_dot or (recently_damaged and enemy.actor_id == recent_attacker_id)
		if not in_fov:
			continue
		if not actor.can_see(enemy):
			continue
		var score: float = distance
		if enemy.actor_id == current_target_id:
			score -= TARGET_HYSTERESIS_BONUS
		if match_node.objective_state == "carried" and enemy.actor_id == match_node.objective_carrier:
			score -= 3.5
		if match_node.objective_state == "planted" and enemy.actor_id == defuser_id:
			score -= 6.0
		if recently_damaged and enemy.actor_id == recent_attacker_id:
			score -= 4.0
		if score < best_score:
			best_score = score
			best_enemy = enemy
	return best_enemy

static func _update_auditory_and_team_memory(match_node: Node, actor: SBActor, state: Dictionary, profile: Dictionary) -> void:
	var hearing_range: float = float(profile.get("hearing_range", 24.0))
	var best_sound_dist: float = hearing_range
	for heard_id: int in match_node._heard:
		if not match_node.actors.has(heard_id):
			continue
		var shooter: SBActor = match_node.actors[heard_id]
		if shooter.team == actor.team:
			continue
		var event: Dictionary = match_node._heard[heard_id]
		var age: float = match_node._elapsed - float(event.get("time", -100.0))
		if age >= SOUND_MEMORY_SECONDS:
			continue
		var pos: Vector3 = event.get("position", Vector3.ZERO)
		var dist: float = actor.position.distance_to(pos)
		if dist < best_sound_dist:
			best_sound_dist = dist
			state["heard_pos"] = pos
			state["heard_at"] = float(event.get("time", match_node._elapsed))

	if bool(profile.get("team_comms", true)) and match_node.get("_team_ai_state") != null:
		var team_dict: Dictionary = match_node._team_ai_state.get(actor.team, {})
		var contacts: Dictionary = team_dict.get("contacts", {})
		var mem_duration: float = float(profile.get("memory_duration", 3.8))
		for enemy_id: int in contacts.keys():
			var report: Dictionary = contacts[enemy_id]
			var age: float = match_node._elapsed - float(report.get("time", -100.0))
			if age > mem_duration:
				continue
			var report_pos: Vector3 = report.get("position", Vector3.ZERO)
			if actor.position.distance_to(report_pos) <= TEAM_REPORT_RADIUS:
				if float(report.get("time", -100.0)) > float(state.get("heard_at", -100.0)):
					state["heard_pos"] = report_pos
					state["heard_at"] = float(report.get("time", -100.0))

static func _share_sighting(match_node: Node, actor: SBActor, target: SBActor) -> void:
	if match_node.get("_team_ai_state") == null:
		return
	var team_dict: Dictionary = match_node._team_ai_state.get(actor.team, {})
	if not team_dict.has("contacts"):
		team_dict["contacts"] = {}
	team_dict["contacts"][target.actor_id] = {
		"position": target.position,
		"time": match_node._elapsed,
		"reporter": actor.actor_id
	}

static func _select_objective_and_destination(match_node: Node, actor: SBActor, state: Dictionary, profile: Dictionary) -> Dictionary:
	var interact: bool = false
	var role: String = "rifle"
	var primary_site: int = match_node.round_number % 2
	if match_node.get("_team_ai_state") != null and match_node._team_ai_state.has(0):
		primary_site = int(match_node._team_ai_state[0].get("primary_site", primary_site))
	var destination: Vector3 = match_node.arena.sites[primary_site]

	if match_node.objective_state == "planted":
		var planted_site: int = 0 if match_node.objective_position.x < 0.0 else 1
		destination = match_node.objective_position
		var defuser_id: int = nearest_defender(match_node)
		interact = actor.team == 1 and actor.actor_id == defuser_id and actor.position.distance_to(destination) <= 2.6
		if actor.team == 1 and actor.actor_id == defuser_id:
			role = "defuser"
		else:
			role = "post_plant_hold" if actor.team == 0 else "retake_cover"
			var offsets: Array = SITE_HOLD_OFFSETS.get(planted_site, SITE_HOLD_OFFSETS[0])
			var offset: Vector3 = offsets[actor.actor_id % offsets.size()]
			var candidate: Vector3 = match_node.arena.sites[planted_site] + offset
			if match_node.arena._clear_path(candidate, candidate + Vector3(0.01, 0.0, 0.01)):
				destination = candidate
			else:
				var hold_angle: float = float(actor.actor_id % 5) * TAU / 5.0
				destination = match_node.objective_position + Vector3(cos(hold_angle), 0.0, sin(hold_angle)) * 3.2
	elif actor.team == 0 and match_node.objective_state == "dropped":
		role = "recover_device"
		destination = match_node.objective_position
	elif actor.team == 0:
		var carrier: SBActor = match_node.actors.get(match_node.objective_carrier) as SBActor
		# If a human carrier has committed toward a specific site, adapt team target site to escort them.
		if carrier != null and carrier.alive and not match_node._is_bot(carrier.actor_id) and carrier.position.z > -8.0:
			primary_site = 0 if carrier.position.x < 0.0 else 1
			destination = match_node.arena.sites[primary_site]
		if actor.actor_id == match_node.objective_carrier:
			role = "carrier"
			destination = match_node.arena.sites[primary_site]
			interact = match_node.arena.is_at_site(actor.position) >= 0
		else:
			var slot: int = actor.actor_id % 5
			if slot == 2 and bool(profile.get("team_comms", true)) and actor.position.z < 2.0 and match_node.time_left > 55.0:
				# Mid/split lurk before converging on the target site.
				role = "split_flank"
				destination = ATTACK_SPLIT_WAYPOINTS.get(primary_site, destination)
			elif slot == 1 and carrier != null and carrier.alive and carrier.position.distance_to(destination) > 7.0:
				# Entry vanguard clearing slightly ahead of the carrier.
				role = "entry"
				destination = match_node.arena.sites[primary_site] + Vector3(0.0, 0.0, -2.2)
			else:
				role = "escort"
				var offsets: Array = SITE_HOLD_OFFSETS.get(primary_site, SITE_HOLD_OFFSETS[0])
				if actor.position.distance_to(match_node.arena.sites[primary_site]) < 9.0:
					destination = match_node.arena.sites[primary_site] + offsets[slot]
				else:
					destination = match_node.arena.sites[primary_site]
			var hearing_range: float = float(profile.get("hearing_range", 24.0))
			if match_node._elapsed - float(state.get("heard_at", -100.0)) < SOUND_MEMORY_SECONDS:
				var heard_pos: Vector3 = state.get("heard_pos", Vector3.ZERO)
				if actor.position.distance_to(heard_pos) <= hearing_range:
					destination = heard_pos
					role = "investigate_sound"
			for heard_id: int in match_node._heard:
				if match_node.actors.has(heard_id) and match_node.actors[heard_id].team != actor.team:
					var h_time: float = float(match_node._heard[heard_id].time)
					var h_pos: Vector3 = match_node._heard[heard_id].position
					if match_node._elapsed - h_time < SOUND_MEMORY_SECONDS and actor.position.distance_to(h_pos) <= hearing_range:
						destination = h_pos
						role = "investigate_sound"
	else:
		# Defender logic before plant
		var anchor_idx: int = (actor.actor_id - 6) % DEFENDER_ANCHORS.size()
		if anchor_idx < 0:
			anchor_idx = actor.actor_id % DEFENDER_ANCHORS.size()
		destination = DEFENDER_ANCHORS[anchor_idx] if bool(profile.get("team_comms", true)) else match_node.arena.sites[actor.actor_id % 2]
		role = "anchor"
		# Rotate toward confirmed team sightings or recent enemy gunfire.
		if match_node._elapsed - float(state.get("heard_at", -100.0)) < SOUND_MEMORY_SECONDS:
			var heard_pos: Vector3 = state.get("heard_pos", Vector3.ZERO)
			if actor.position.distance_to(heard_pos) < float(profile.get("hearing_range", 24.0)):
				destination = heard_pos
				role = "rotate_investigate"
		for heard_id: int in match_node._heard:
			if match_node.actors.has(heard_id) and match_node.actors[heard_id].team != actor.team:
				var h_time: float = float(match_node._heard[heard_id].time)
				var h_pos: Vector3 = match_node._heard[heard_id].position
				if match_node._elapsed - h_time < 2.0 and actor.position.distance_to(h_pos) < 22.0:
					destination = h_pos
					role = "rotate_investigate"

	state["role"] = role
	return {"destination": destination, "interact": interact, "primary_site": primary_site}

static func select_destination(match_node: Node, actor: SBActor, state: Dictionary, profile: Dictionary, _interact_override: bool = false, _defuser_id: int = 0) -> Vector3:
	_update_auditory_and_team_memory(match_node, actor, state, profile)
	var plan: Dictionary = _select_objective_and_destination(match_node, actor, state, profile)
	return plan.get("destination", actor.position)

static func tick_bot(match_node: Node, actor: SBActor, delta: float) -> void:
	compute_bot_input(match_node, actor, delta)

static func compute_bot_input(match_node: Node, actor: SBActor, delta: float) -> void:
	if not actor.alive or match_node.phase != "live":
		return
	if not match_node._bot_state.has(actor.actor_id):
		match_node._bot_state[actor.actor_id] = create_state(actor)
	var state: Dictionary = match_node._bot_state[actor.actor_id]
	var difficulty: String = str(match_node.options.get("difficulty", "normal"))
	var profile: Dictionary = profile_for(difficulty)
	var reaction_delay: float = float(profile.reaction_delay)

	_update_auditory_and_team_memory(match_node, actor, state, profile)
	var target: SBActor = acquire_target(match_node, actor, state, profile)
	var plan: Dictionary = _select_objective_and_destination(match_node, actor, state, profile)
	var destination: Vector3 = plan.destination
	var interact: bool = bool(plan.interact)

	var look := Vector2(actor.yaw, actor.pitch)
	var firing: bool = false
	var move := Vector2.ZERO
	var requested_weapon: String = ""
	var use_smoke: bool = false
	var use_grenade: bool = false
	var crouch: bool = false

	var spec: Dictionary = SBWeapons.get_weapon(actor.weapon_id)
	var magazine: int = int(spec.magazine)

	if target != null:
		if int(state.get("target", 0)) != target.actor_id:
			state["reaction"] = 0.0
			state["burst_time"] = 0.0
		state["target"] = target.actor_id
		state["last_seen"] = target.position
		state["seen_at"] = match_node._elapsed
		state["reaction"] = float(state.get("reaction", 0.0)) + delta
		if bool(profile.get("team_comms", true)):
			_share_sighting(match_node, actor, target)

		var target_distance: float = actor.position.distance_to(target.position)
		# Emergency sidearm transition when primary runs dry in close-to-mid combat.
		if bool(profile.get("sidearm_fallback", true)) and actor.ammo == 0 and actor.weapon_id != "sidearm" and actor.inventory.has("sidearm") and target_distance < 20.0 and not interact:
			requested_weapon = "sidearm"

		var aim: Vector3 = target.position + Vector3(0.0, 1.15, 0.0) - (actor.position + Vector3(0.0, 1.5, 0.0))
		var error: float = float(profile.aim_error)
		var recoil_comp: float = float(profile.get("recoil_compensation", 0.0))
		var desired := Vector2(
			atan2(-aim.x, -aim.z) - actor.recoil.x * recoil_comp + match_node._rng.randf_range(-error, error),
			atan2(aim.y, Vector2(aim.x, aim.z).length()) - actor.recoil.y * recoil_comp
		)
		var turn_speed: float = float(profile.turn_speed)
		look.x = rotate_toward(actor.yaw, desired.x, turn_speed * delta)
		look.y = move_toward(actor.pitch, desired.y, turn_speed * delta)

		# Burst/recoil discipline at long range so automatic weapons don't spray wildly over targets.
		var burst_cooldown: float = maxf(0.0, float(state.get("burst_cooldown", 0.0)) - delta)
		var burst_time: float = float(state.get("burst_time", 0.0))
		if burst_cooldown > 0.0:
			burst_time = 0.0
		elif target_distance > 22.0 and bool(spec.automatic) and actor.recoil.y > 0.11 and burst_time >= MAX_BURST_SECONDS:
			burst_cooldown = BURST_COOLDOWN_SECONDS
			burst_time = 0.0
		state["burst_cooldown"] = burst_cooldown

		# Reaction time never allows shooting before the muzzle reaches the target.
		var aligned: bool = absf(angle_difference(look.x, desired.x)) < 0.07 and absf(look.y - desired.y) < 0.07
		firing = float(state.get("reaction", 0.0)) >= reaction_delay and aligned and not interact and burst_cooldown <= 0.0
		if not bool(spec.automatic) and bool(actor.input_state.get("fire", false)):
			firing = false
		if firing:
			state["burst_time"] = burst_time + delta
		else:
			state["burst_time"] = maxf(0.0, burst_time - delta * 2.0)

		# Movement in combat: counter-strafe/brake at long range, strafe at close/mid range, or seek cover when reloading/critical HP.
		var should_seek_cover: bool = actor.reload_remaining > 0.0 or (actor.health <= float(profile.get("retreat_hp", 0.0)) and not interact)
		if should_seek_cover:
			var cover: Vector3 = cover_position(match_node, actor, target)
			var next_wp: Vector3 = safe_navigate(match_node.arena, actor.position, cover)
			var step: Vector3 = next_wp - actor.position
			if step.length_squared() > 0.01:
				var local_step: Vector3 = Basis(Vector3.UP, -look.x) * step.normalized()
				move = Vector2(local_step.x, -local_step.z)
		elif bool(profile.get("counter_strafe", false)) and target_distance > 20.0 and aligned:
			move = Vector2.ZERO
		else:
			move = Vector2(sin(match_node._elapsed * 1.1 + float(actor.actor_id)) * 0.4, 0.0)

		crouch = (actor.actor_id % 3 == 0) or (bool(profile.get("counter_strafe", false)) and target_distance > 18.0 and aligned)
	else:
		state["target"] = 0
		state["reaction"] = 0.0
		state["burst_time"] = 0.0
		state["burst_cooldown"] = 0.0

		# Switch back to primary rifle/smg/marksman when out of immediate combat if holding sidearm with primary ammo available.
		if actor.weapon_id == "sidearm" and actor.inventory.size() > 1:
			for w_id in ["rifle", "marksman", "smg"]:
				if actor.inventory.has(w_id):
					requested_weapon = w_id
					break

		# Tactical utility: carrier or support deploys smoke when approaching site or before defusing.
		if bool(profile.get("utility_use", false)) and actor.smokes > 0 and not bool(state.get("smoke_used", false)) and not interact:
			if actor.team == 0 and actor.position.distance_to(match_node.arena.sites[int(plan.primary_site)]) < 14.0 and actor.position.distance_to(match_node.arena.sites[int(plan.primary_site)]) > 5.0:
				if actor.actor_id == match_node.objective_carrier or actor.actor_id % 2 == 0:
					use_smoke = true
					state["smoke_used"] = true
			elif actor.team == 1 and match_node.objective_state == "planted" and actor.position.distance_to(match_node.objective_position) < 11.0 and actor.position.distance_to(match_node.objective_position) > 3.5:
				use_smoke = true
				state["smoke_used"] = true

		var mem_window: float = float(profile.get("memory_duration", 2.0))
		# Investigate a briefly remembered sighting; never aim/fire at hidden live coordinates.
		if match_node._elapsed - float(state.get("seen_at", -100.0)) < mem_window and not interact and match_node.objective_state != "planted":
			state["role"] = "pursue_memory"
			if actor.health <= float(profile.get("retreat_hp", 0.0)):
				destination = cover_position_from_point(match_node, actor, state["last_seen"])
			else:
				destination = state["last_seen"]
		elif match_node._elapsed - float(state.get("damaged_at", -100.0)) < 1.5 and not interact:
			# Turn toward directional damage indicator when hit from outside FOV.
			var dmg_origin: Vector3 = state.get("damaged_from", actor.position)
			var to_dmg: Vector3 = dmg_origin - actor.position
			if to_dmg.length_squared() > 0.1:
				var dmg_yaw: float = atan2(-to_dmg.x, -to_dmg.z)
				look = Vector2(rotate_toward(actor.yaw, dmg_yaw, float(profile.turn_speed) * delta), 0.0)

		if actor.position.distance_to(destination) > 1.8 and not interact:
			var waypoint: Vector3 = safe_navigate(match_node.arena, actor.position, destination)
			var direction: Vector3 = waypoint - actor.position
			if direction.length_squared() > 0.001:
				look = Vector2(atan2(-direction.x, -direction.z), 0.0)
				move = Vector2(0.0, 1.0)
		elif not interact:
			# Scan the approach rather than staring permanently away from the attackers.
			var approach := Vector3(0.0, 0.0, -18.0) if actor.team == 1 else Vector3(0.0, 0.0, 20.0)
			if match_node._elapsed - float(state.get("heard_at", -100.0)) < SOUND_MEMORY_SECONDS:
				approach = state.get("heard_pos", approach)
			var toward_approach: Vector3 = approach - actor.position
			var scan_yaw: float = atan2(-toward_approach.x, -toward_approach.z) + sin(match_node._elapsed * 0.65 + float(actor.actor_id)) * 0.7
			look = Vector2(rotate_toward(actor.yaw, scan_yaw, delta * 2.0), 0.0)

	# Stuck detection and multi-stage recovery.
	if actor.position.distance_to(state.get("last_position", actor.position)) < 0.05 and move.length() > 0.0:
		state["stuck"] = float(state.get("stuck", 0.0)) + delta
	else:
		state["stuck"] = 0.0
	state["last_position"] = actor.position
	if float(state.get("stuck", 0.0)) > 0.9:
		move.x = 1.0 if actor.actor_id % 2 == 0 else -1.0
		if float(state.get("stuck", 0.0)) > 1.8 and target == null and not interact:
			move.y = -0.6

	var safe_reload: bool = target == null and match_node._elapsed - float(state.get("seen_at", -100.0)) > 2.5 and actor.ammo <= magazine / 3
	actor.input_state = {
		"move": Vector2.ZERO if interact else move,
		"look": look,
		"fire": firing,
		"reload": not interact and requested_weapon == "" and (actor.ammo == 0 or safe_reload),
		"jump": float(state.get("stuck", 0.0)) > 1.5,
		"crouch": crouch,
		"interact": interact,
		"weapon": requested_weapon,
		"smoke": use_smoke,
		"grenade": use_grenade
	}
