class_name TacticalMatch
extends Node3D

signal match_finished(summary: Dictionary)
signal notification(text: String)
signal exit_requested
## Structured elimination for the HUD feed; mirrored to clients by the server.
signal elimination_reported(killer_id: int, victim_id: int, headshot: bool)

const BUY_SECONDS := 15.0
const ROUND_SECONDS := 100.0
const DEVICE_SECONDS := 35.0
const PLANT_SECONDS := 3.0
const DEFUSE_SECONDS := 5.0
const WIN_SCORE := 7
const BOT_NAMES := ["Flint", "Sable", "Rook", "Cipher", "Vale", "Ember", "Kestrel", "Slate", "Morrow", "Echo"]
var phase: String = "buy"
var round_number: int = 0
var attack_score: int = 0
var defend_score: int = 0
var time_left: float = BUY_SECONDS
var objective_state: String = "carried"
var objective_timer: float = 0.0
var interaction_progress: float = 0.0
var objective_position := Vector3.ZERO
var objective_carrier: int = 1
var objective_contributions: Dictionary = {}
var arena: RelayYard
var actors: Dictionary = {}
var options: Dictionary = {}
var local_id: int = 1
var connection_state: String = "offline"
var reconnect_token: String = ""
var _authority: bool = true
var _bot_state: Dictionary = {}
var _peer_actors: Dictionary = {}
var _reservations: Dictionary = {}
var _last_peer_input: Dictionary = {}
var _damage_history: Dictionary = {}
var _interactions: Dictionary = {}
var _gate := SBInputGate.new()
var _local_input: Dictionary = {"move": Vector2.ZERO, "look": Vector2.ZERO}
var _snapshot_clock: float = 0.0
var _input_clock: float = 0.0
var _bot_clock: float = 0.0
var _heard: Dictionary = {}
var _spectator: Camera3D
var _finished_emitted: bool = false
var _elapsed: float = 0.0
var _reconnect_clock: float = 0.0
var _reconnect_attempts: int = 0
var reward_status: String = "unranked"
var _bridge: SBEconomyBridge
var _account_ids: Dictionary = {}
var _pending_joins: Dictionary = {}
var _activity_seconds: Dictionary = {}
var _last_activity: Dictionary = {}
var _ranked_eligible: bool = false
var _ranked_started: bool = false
var _started_at: String = ""
var _match_id: String = ""
var _match_started_elapsed: float = 0.0
var _connected_actor_ids: Array = []
var _device: Node3D
var _device_emission: StandardMaterial3D
var _device_audio: AudioStreamPlayer3D
var _beep_clock: float = 0.0
var _remote_utilities: Dictionary = {}
var _rng := RandomNumberGenerator.new()

func configure(settings: Dictionary) -> void:
	options = settings.duplicate()
	reconnect_token = str(options.get("reconnect_token", ""))

func _ready() -> void:
	name = "Match"
	_rng.randomize()
	arena = RelayYard.new()
	add_child(arena)
	_build_device_visual()
	_spectator = Camera3D.new()
	_spectator.position = Vector3(0, 32, 20)
	add_child(_spectator)
	_spectator.look_at(Vector3.ZERO)
	var mode: String = str(options.get("mode", "offline"))
	_authority = mode != "client"
	local_id = 1 if mode == "offline" else 0
	if _authority:
		for id in range(1, 11):
			_spawn_actor(id, 0 if id <= 5 else 1, str(options.get("name", "Operator")) if id == local_id else BOT_NAMES[id - 1])
		if mode == "server" and bool(options.get("require_accounts", false)):
			phase = "waiting"
			time_left = 0
			reward_status = "waiting_for_accounts"
			_bridge = SBEconomyBridge.new()
			_bridge.configure(str(options.get("economy_url", "http://127.0.0.1:8080")), str(options.get("server_id", "local-relay")))
			add_child(_bridge)
			for actor: SBActor in actors.values():
				actor.reset_for_round(arena.attack_spawns[(actor.actor_id - 1) % 5] if actor.team == 0 else arena.defend_spawns[(actor.actor_id - 1) % 5])
		else:
			_begin_round()
	if mode == "server":
		_host()
	elif mode == "client":
		multiplayer.connected_to_server.connect(_connected)
		multiplayer.connection_failed.connect(_connection_failed)
		multiplayer.server_disconnected.connect(_server_disconnected)
		_connect_client()

func _exit_tree() -> void:
	if str(options.get("mode", "offline")) != "offline":
		multiplayer.multiplayer_peer = OfflineMultiplayerPeer.new()

func _spawn_actor(id: int, team: int, player_name: String) -> SBActor:
	var actor := SBActor.new()
	actor.name = "Operator_%d" % id
	actor.configure(id, team, player_name, id == local_id)
	actors[id] = actor
	objective_contributions[id] = 0
	add_child(actor)
	actor.eliminated.connect(_eliminated)
	actor.damage_taken.connect(_damaged)
	actor.shot_fired.connect(_shot)
	actor.hit_confirmed.connect(_confirmed_hit)
	actor.impact_created.connect(_confirmed_impact)
	_reset_bot_state(actor)
	return actor

func _reset_bot_state(actor: SBActor) -> void:
	_bot_state[actor.actor_id] = {"reaction": 0.0, "target": 0, "last_position": actor.position, "stuck": 0.0, "last_seen": Vector3.ZERO, "seen_at": -100.0}

func local_actor() -> SBActor:
	return actors.get(local_id) as SBActor

func set_local_input(value: Dictionary) -> void:
	_local_input = value.duplicate()

func request_buy(id: String) -> void:
	if phase != "buy":
		notification.emit("Equipment is available during preparation.")
		return
	if _authority:
		_buy(local_id, id)
	elif connection_state == "connected":
		_buy_rpc.rpc_id(1, id)

func _buy(id: int, weapon: String) -> void:
	var actor: SBActor = actors.get(id)
	if actor == null or phase != "buy":
		return
	if not actor.buy_weapon(weapon) and id == local_id:
		var spec: Dictionary = SBWeapons.get_weapon(weapon)
		if actor.inventory.has(weapon):
			notification.emit("%s is already in your loadout." % str(spec.name).to_upper())
		elif SBWeapons.DATA.has(weapon) and actor.credits < int(spec.cost):
			notification.emit("Need %d more match funds for the %s." % [int(spec.cost) - actor.credits, str(spec.name).to_upper()])
		else:
			notification.emit("Purchase unavailable.")

func scoreboard() -> Array:
	var result: Array = []
	for actor: SBActor in actors.values():
		result.append({"id": actor.actor_id, "name": actor.display_name, "team": actor.team, "kills": actor.kills, "assists": actor.assists, "deaths": actor.deaths, "credits": actor.credits, "alive": actor.alive, "objectives": int(objective_contributions.get(actor.actor_id, 0)), "local": actor.actor_id == local_id, "bot": _is_bot(actor.actor_id)})
	result.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a.kills > b.kills)
	return result

func _physics_process(delta: float) -> void:
	_elapsed += delta
	if _authority:
		_authority_tick(delta)
	else:
		_client_tick(delta)
	for actor: SBActor in actors.values():
		actor.tick_visual(delta)
	_update_spectator()
	_update_device_visual(delta)

func _authority_tick(delta: float) -> void:
	_bot_clock -= delta
	if _bot_clock <= 0:
		_bot_clock = 0.12
		for actor: SBActor in actors.values():
			if _is_bot(actor.actor_id):
				_bot_input(actor, 0.12)
	if local_actor() != null:
		local_actor().input_state = _local_input.duplicate()
	for actor: SBActor in actors.values():
		if phase != "live":
			actor.input_state = {"move": Vector2.ZERO, "look": actor.input_state.get("look", Vector2(actor.yaw, actor.pitch))}
		elif not _is_bot(actor.actor_id) and actor.actor_id != local_id:
			if _elapsed - float(_last_peer_input.get(actor.actor_id, -10.0)) > 0.3:
				actor.input_state = {"move": Vector2.ZERO, "look": Vector2(actor.yaw, actor.pitch)}
		actor.tick_authority(delta)
		if _ranked_started and phase != "match_over" and _peer_actors.values().has(actor.actor_id):
			if _elapsed - float(_last_activity.get(actor.actor_id, -100)) <= 10:
				_activity_seconds[actor.actor_id] = float(_activity_seconds.get(actor.actor_id, 0)) + delta
	if phase == "live":
		_objective_tick(delta)
		_check_elimination()
	if phase != "match_over":
		time_left = maxf(0, time_left - delta)
		if time_left <= 0:
			if phase == "buy":
				phase = "live"
				time_left = ROUND_SECONDS
				_announce("Round live. Secure Relay Yard.")
			elif phase == "live" and objective_state != "planted":
				_end_round(1, "Time expired")
			elif phase == "post":
				_begin_round()
	_snapshot_clock -= delta
	if options.get("mode", "offline") == "server" and _snapshot_clock <= 0:
		_snapshot_clock = 0.05
		var packed: PackedByteArray = var_to_bytes(_snapshot()).compress(FileAccess.COMPRESSION_DEFLATE)
		for peer_id: int in _active_peers():
			_snapshot_rpc.rpc_id(peer_id, packed)

func _is_bot(id: int) -> bool:
	return id != local_id and not (_peer_actors.values() if _authority else _connected_actor_ids).has(id)

func _begin_round() -> void:
	for child: Node in get_children():
		if child is SBUtility:
			child.queue_free()
	if round_number == 6:
		for actor: SBActor in actors.values():
			actor.team = 1 - actor.team
			actor.credits = 1200
			actor.reset_loadout()
		var swap: int = attack_score
		attack_score = defend_score
		defend_score = swap
		_announce("Halftime — teams switched sides")
	round_number += 1
	phase = "buy"
	time_left = BUY_SECONDS
	objective_state = "carried"
	objective_timer = 0
	interaction_progress = 0
	_interactions.clear()
	_damage_history.clear()
	_heard.clear()
	var attack_index: int = 0
	var defend_index: int = 0
	objective_carrier = 0
	for actor: SBActor in actors.values():
		var spawn: Vector3
		if actor.team == 0:
			spawn = arena.attack_spawns[attack_index % arena.attack_spawns.size()]
			attack_index += 1
			if objective_carrier == 0 or actor.actor_id == local_id:
				objective_carrier = actor.actor_id
		else:
			spawn = arena.defend_spawns[defend_index % arena.defend_spawns.size()]
			defend_index += 1
		actor.reset_for_round(spawn)
		_reset_bot_state(actor)
		if _is_bot(actor.actor_id):
			actor.buy_weapon("rifle" if actor.credits >= 2400 else "smg")
		actor.input_state = {"move": Vector2.ZERO, "look": Vector2(PI if actor.team == 0 else 0, 0)}
	_announce("Round %d • prepare your equipment" % round_number)

func _objective_tick(delta: float) -> void:
	interaction_progress = 0
	if objective_state == "planted":
		objective_timer = maxf(0, objective_timer - delta)
		if objective_timer <= 0:
			_end_round(0, "Relay device detonated")
			return
	if objective_state == "dropped":
		for actor: SBActor in actors.values():
			if actor.alive and actor.team == 0 and actor.position.distance_to(objective_position) < 2:
				objective_carrier = actor.actor_id
				objective_state = "carried"
				_announce("Relay device recovered")
				break
	for actor: SBActor in actors.values():
		var eligible: bool = actor.alive and bool(actor.input_state.get("interact", false)) and (actor.input_state.get("move", Vector2.ZERO) as Vector2).length() < 0.2
		var planting: bool = actor.team == 0 and actor.actor_id == objective_carrier and objective_state == "carried" and arena.is_at_site(actor.position) >= 0
		var defusing: bool = actor.team == 1 and objective_state == "planted" and actor.position.distance_to(objective_position) <= 2.8
		if not eligible or not (planting or defusing):
			_interactions.erase(actor.actor_id)
			continue
		var progress: float = float(_interactions.get(actor.actor_id, 0.0)) + delta
		_interactions[actor.actor_id] = progress
		var required: float = PLANT_SECONDS if planting else DEFUSE_SECONDS
		if actor.actor_id == local_id:
			interaction_progress = progress / required
		if progress >= required:
			_interactions.clear()
			actor.credits = mini(9000, actor.credits + 300)
			objective_contributions[actor.actor_id] = int(objective_contributions.get(actor.actor_id, 0)) + 1
			if planting:
				objective_state = "planted"
				objective_position = actor.position
				objective_timer = DEVICE_SECONDS
				_announce("Relay device armed — defend the site")
			else:
				objective_state = "defused"
				_end_round(1, "Relay device defused")
			break

func _check_elimination() -> void:
	if phase != "live":
		return
	var attackers: int = 0
	var defenders: int = 0
	for actor: SBActor in actors.values():
		if actor.alive:
			if actor.team == 0:
				attackers += 1
			else:
				defenders += 1
	if defenders == 0:
		_end_round(0, "Defenders eliminated")
	elif attackers == 0 and objective_state != "planted":
		_end_round(1, "Attackers eliminated")

func _end_round(winner: int, reason: String) -> void:
	if phase != "live":
		return
	if winner == 0:
		attack_score += 1
	else:
		defend_score += 1
	for actor: SBActor in actors.values():
		actor.credits = mini(9000, actor.credits + (2700 if actor.team == winner else 1900))
	phase = "post"
	for child: Node in get_children():
		if child is SBUtility:
			child.queue_free()
	time_left = 5
	_announce(("Attackers" if winner == 0 else "Defenders") + " win • " + reason)
	if maxi(attack_score, defend_score) >= WIN_SCORE or round_number >= 12:
		phase = "match_over"
		_emit_results()
		if _ranked_started:
			_submit_ranked_result()
		elif options.get("mode", "offline") == "server" and _peer_actors.is_empty():
			_reset_server_match.call_deferred()

func _emit_results() -> void:
	if _finished_emitted:
		return
	_finished_emitted = true
	var actor: SBActor = local_actor()
	var won: bool = actor != null and ((actor.team == 0 and attack_score > defend_score) or (actor.team == 1 and defend_score > attack_score))
	match_finished.emit({"won": won, "draw": attack_score == defend_score, "rounds": round_number, "attack_score": attack_score, "defend_score": defend_score, "kills": actor.kills if actor else 0, "assists": actor.assists if actor else 0, "deaths": actor.deaths if actor else 0, "objectives": int(objective_contributions.get(local_id, 0)), "duration": _elapsed, "offline": options.get("mode", "offline") == "offline", "scoreboard": scoreboard()})

func _damaged(victim: int, attacker: int, amount: float) -> void:
	if not _authority:
		return
	if not _damage_history.has(victim):
		_damage_history[victim] = {}
	_damage_history[victim][attacker] = float(_damage_history[victim].get(attacker, 0)) + amount

func _eliminated(victim: int, killer: int) -> void:
	if not _authority:
		return
	var killed: SBActor = actors.get(victim)
	var source: SBActor = actors.get(killer)
	if killed == null:
		return
	killed.deaths += 1
	if source and source.team != killed.team:
		source.kills += 1
		source.credits = mini(9000, source.credits + 300)
		_announce(source.display_name + "  ›  " + killed.display_name)
	_report_elimination(killer, victim, killed.last_hit_headshot)
	for assistant_id: int in _damage_history.get(victim, {}):
		if assistant_id != killer and actors.has(assistant_id) and float(_damage_history[victim][assistant_id]) >= 20:
			var helper: SBActor = actors[assistant_id]
			if helper.team != killed.team:
				helper.assists += 1
	if victim == objective_carrier and objective_state == "carried":
		objective_state = "dropped"
		objective_position = killed.position
		objective_carrier = 0
		_announce("Relay device dropped")

func _report_elimination(killer: int, victim: int, headshot: bool) -> void:
	elimination_reported.emit(killer, victim, headshot)
	if options.get("mode", "offline") == "server":
		for peer_id: int in _active_peers():
			_elimination_rpc.rpc_id(peer_id, killer, victim, headshot)

@rpc("authority", "call_remote", "reliable")
func _elimination_rpc(killer: int, victim: int, headshot: bool) -> void:
	if _authority or not actors.has(victim):
		return
	elimination_reported.emit(killer, victim, headshot)

func _shot(id: int, origin: Vector3, _direction: Vector3) -> void:
	_heard[id] = {"position": origin, "time": _elapsed}
	_last_activity[id] = _elapsed
	if options.get("mode", "offline") == "server":
		for peer_id: int in _active_peers():
			_shot_rpc.rpc_id(peer_id, id)

func _confirmed_hit(id: int, headshot: bool, lethal: bool) -> void:
	# Emitted only after authority ray damage; never trust a client hit claim.
	if not _authority or not actors.has(id): return
	if options.get("mode", "offline") == "server":
		for peer_id: int in _active_peers():
			if int(_peer_actors.get(peer_id, 0)) == id:
				_hit_feedback_rpc.rpc_id(peer_id, id, headshot, lethal)

@rpc("authority", "call_remote", "reliable")
func _hit_feedback_rpc(id: int, headshot: bool, lethal: bool) -> void:
	if _authority or id != local_id or not actors.has(id): return
	actors[id].show_hit_feedback(headshot, lethal)

func _confirmed_impact(at: Vector3, normal: Vector3, hit_actor: bool) -> void:
	if not _authority or options.get("mode", "offline") != "server": return
	for peer_id: int in _active_peers():
		_impact_rpc.rpc_id(peer_id, at, normal, hit_actor)

@rpc("authority", "call_remote", "unreliable", 4)
func _impact_rpc(at: Vector3, normal: Vector3, hit_actor: bool) -> void:
	if _authority or not at.is_finite() or not normal.is_finite(): return
	if absf(at.x) > 256 or absf(at.y) > 256 or absf(at.z) > 256: return
	if normal.length_squared() < 0.5 or normal.length_squared() > 1.5: return
	load("res://scripts/gameplay/combat_effects.gd").for_world(self).impact(at, normal.normalized(), hit_actor)

func _bot_input(actor: SBActor, delta: float) -> void:
	if not actor.alive or phase != "live":
		return
	var state: Dictionary = _bot_state[actor.actor_id]
	var difficulty: String = str(options.get("difficulty", "normal"))
	var reaction_delay: float = 0.6 if difficulty == "easy" else (0.18 if difficulty == "hard" else 0.35)
	var target: SBActor = null
	var nearest: float = 28.0
	for enemy: SBActor in actors.values():
		if enemy.team == actor.team or not enemy.alive:
			continue
		var distance: float = actor.position.distance_to(enemy.position)
		var facing := Vector3(-sin(actor.yaw), 0, -cos(actor.yaw))
		var toward: Vector3 = (enemy.position - actor.position).normalized()
		if distance < nearest and facing.dot(toward) > -0.15 and actor.can_see(enemy):
			nearest = distance
			target = enemy
	var destination: Vector3 = arena.sites[0 if round_number % 2 == 0 else 1]
	var interact: bool = false
	if objective_state == "planted":
		destination = objective_position
		var defuser_id: int = _nearest_defender()
		interact = actor.team == 1 and actor.actor_id == defuser_id and actor.position.distance_to(destination) <= 2.6
		if actor.team == 0 or actor.actor_id != defuser_id:
			# Hold separate approach angles while one teammate works the device.
			var hold_angle: float = float(actor.actor_id % 5) * TAU / 5.0
			destination += Vector3(cos(hold_angle), 0, sin(hold_angle)) * 4.5
	elif actor.team == 0 and objective_state == "dropped":
		destination = objective_position
	elif actor.team == 0:
		interact = actor.actor_id == objective_carrier and arena.is_at_site(actor.position) >= 0
	else:
		destination = arena.sites[actor.actor_id % 2]
		for heard_id: int in _heard:
			if actors.has(heard_id) and actors[heard_id].team != actor.team and _elapsed - float(_heard[heard_id].time) < 2.0 and actor.position.distance_to(_heard[heard_id].position) < 22:
				destination = _heard[heard_id].position
	var look := Vector2(actor.yaw, actor.pitch)
	var firing: bool = false
	var move := Vector2.ZERO
	if target:
		if int(state.target) != target.actor_id:
			state.reaction = 0.0
		state.target = target.actor_id
		state.last_seen = target.position
		state.seen_at = _elapsed
		state.reaction = float(state.reaction) + delta
		var aim: Vector3 = target.position + Vector3(0, 1.15, 0) - (actor.position + Vector3(0, 1.5, 0))
		var error: float = 0.045 if difficulty == "easy" else (0.008 if difficulty == "hard" else 0.022)
		var desired := Vector2(atan2(-aim.x, -aim.z) + _rng.randf_range(-error, error), atan2(aim.y, Vector2(aim.x, aim.z).length()))
		var turn_speed: float = 3.5 if difficulty == "easy" else (7.0 if difficulty == "hard" else 5.0)
		look.x = rotate_toward(actor.yaw, desired.x, turn_speed * delta)
		look.y = move_toward(actor.pitch, desired.y, turn_speed * delta)
		# Reaction time never allows shooting before the muzzle reaches the target.
		var aligned: bool = absf(angle_difference(look.x, desired.x)) < 0.07 and absf(look.y - desired.y) < 0.07
		firing = float(state.reaction) >= reaction_delay and aligned and not interact
		if not bool(SBWeapons.get_weapon(actor.weapon_id).automatic) and bool(actor.input_state.get("fire", false)):
			firing = false
		move = Vector2(sin(_elapsed * 1.1 + actor.actor_id) * 0.4, 0)
		if actor.reload_remaining > 0:
			var cover: Vector3 = _cover_position(actor, target)
			var step: Vector3 = arena.bot_navigation(actor.position, cover) - actor.position
			# Convert the world cover route into the aiming frame so the bot keeps watching danger.
			var local_step: Vector3 = Basis(Vector3.UP, -look.x) * step.normalized()
			move = Vector2(local_step.x, -local_step.z)
	else:
		state.target = 0
		state.reaction = 0.0
		# Investigate a briefly remembered sighting; never aim/fire at hidden live coordinates.
		if _elapsed - float(state.seen_at) < 2.0 and not interact and objective_state != "planted":
			destination = state.last_seen
		if actor.position.distance_to(destination) > 1.8 and not interact:
			var waypoint: Vector3 = arena.bot_navigation(actor.position, destination)
			var direction: Vector3 = waypoint - actor.position
			look = Vector2(atan2(-direction.x, -direction.z), 0)
			move = Vector2(0, 1)
		elif not interact:
			# Scan the approach rather than staring permanently away from the attackers.
			var approach := Vector3(0, 0, -18) if actor.team == 1 else Vector3(0, 0, 20)
			var toward_approach: Vector3 = approach - actor.position
			var scan_yaw: float = atan2(-toward_approach.x, -toward_approach.z) + sin(_elapsed * 0.65 + actor.actor_id) * 0.7
			look = Vector2(rotate_toward(actor.yaw, scan_yaw, delta * 2.0), 0)
	if actor.position.distance_to(state.last_position) < 0.05 and move.length() > 0:
		state.stuck = float(state.stuck) + delta
	else:
		state.stuck = 0.0
	state.last_position = actor.position
	if float(state.stuck) > 0.9:
		move.x = 1 if actor.actor_id % 2 == 0 else -1
	var magazine: int = int(SBWeapons.get_weapon(actor.weapon_id).magazine)
	var safe_reload: bool = target == null and _elapsed - float(state.seen_at) > 2.5 and actor.ammo <= magazine / 3
	actor.input_state = {"move": Vector2.ZERO if interact else move, "look": look, "fire": firing, "reload": not interact and (actor.ammo == 0 or safe_reload), "jump": float(state.stuck) > 1.5, "crouch": target != null and actor.actor_id % 3 == 0, "interact": interact}

func _nearest_defender() -> int:
	var chosen: int = 0
	var nearest: float = INF
	for actor: SBActor in actors.values():
		if not actor.alive or actor.team != 1:
			continue
		# A human already holding interact keeps priority; bots provide covering fire.
		if not _is_bot(actor.actor_id) and bool(actor.input_state.get("interact", false)) and actor.position.distance_to(objective_position) <= 2.8:
			return actor.actor_id
		var distance: float = actor.position.distance_squared_to(objective_position)
		if _is_bot(actor.actor_id) and (distance < nearest or (is_equal_approx(distance, nearest) and actor.actor_id < chosen)):
			chosen = actor.actor_id
			nearest = distance
	return chosen

func _cover_position(actor: SBActor, threat: SBActor) -> Vector3:
	var choice: Vector3 = actor.position
	var nearest: float = 10.0
	for point: Vector3 in arena.waypoints:
		var distance: float = actor.position.distance_to(point)
		if distance < nearest and distance > 1:
			var query := PhysicsRayQueryParameters3D.create(threat.position + Vector3.UP * 1.4, point + Vector3.UP * 1.0, 1)
			if not get_world_3d().direct_space_state.intersect_ray(query).is_empty():
				choice = point
				nearest = distance
	return choice

func _update_spectator() -> void:
	var actor: SBActor = local_actor()
	if actor == null or not actor.alive:
		_spectator.current = true
		if actor:
			for teammate: SBActor in actors.values():
				if teammate.alive and teammate.team == actor.team:
					_spectator.global_position = teammate.global_position + Vector3(sin(teammate.yaw) * 3, 2.8, cos(teammate.yaw) * 3)
					_spectator.look_at(teammate.global_position + Vector3(0, 1.3, 0))
					break
	elif actor.camera:
		actor.camera.current = true

func _announce(message: String) -> void:
	notification.emit(message)
	if options.get("mode", "offline") == "server":
		for peer_id: int in _active_peers():
			_notice_rpc.rpc_id(peer_id, message)

func _active_peers() -> Array:
	var connected: Array = []
	var transport := multiplayer.multiplayer_peer as ENetMultiplayerPeer
	if transport == null:
		return connected
	for peer_id: int in _peer_actors:
		if multiplayer.get_peers().has(peer_id):
			var peer: ENetPacketPeer = transport.get_peer(peer_id)
			if peer != null and peer.get_state() == ENetPacketPeer.STATE_CONNECTED and peer.get_channels() > 0:
				connected.append(peer_id)
	return connected

func _host() -> void:
	var peer := ENetMultiplayerPeer.new()
	var error: Error = peer.create_server(int(options.get("port", 27020)), 10)
	if error != OK:
		connection_state = "failed"
		notification.emit("Cannot bind dedicated server port: %s" % error_string(error))
		return
	# Clients only exchange inputs/snapshots with this authority. Disabling the
	# implicit peer relay also avoids peer-list traffic to simultaneously closing
	# ENet channels during reconnect; gameplay never needs client-to-client RPCs.
	multiplayer.server_relay = false
	multiplayer.multiplayer_peer = peer
	multiplayer.peer_disconnected.connect(_peer_disconnected)
	connection_state = "hosting"
	print("SIGHTBREAK_SERVER_READY port=%d" % int(options.get("port", 27020)))

func _connect_client() -> void:
	connection_state = "connecting"
	var peer := ENetMultiplayerPeer.new()
	var error: Error = peer.create_client(str(options.get("address", "127.0.0.1")), int(options.get("port", 27020)))
	if error != OK:
		_connection_failed()
		return
	multiplayer.multiplayer_peer = peer
	notification.emit("Connecting to Relay Yard…")

func _connected() -> void:
	connection_state = "joining"
	_join_rpc.rpc_id(1, str(options.get("name", "Operator")).left(24), reconnect_token, str(options.get("join_ticket", "")))

func _connection_failed() -> void:
	connection_state = "failed"
	notification.emit("Connection failed. Check the address and UDP port.")

func _server_disconnected() -> void:
	if connection_state == "failed":
		return
	connection_state = "reconnecting"
	_reconnect_clock = 2
	_reconnect_attempts = 0
	notification.emit("Server disconnected. Attempting to reconnect…")

func _client_tick(delta: float) -> void:
	var actor: SBActor = local_actor()
	if actor and actor.alive:
		var look: Vector2 = _local_input.get("look", Vector2(actor.yaw, actor.pitch))
		# Predict view orientation only; movement and combat remain authoritative.
		if look.is_finite():
			actor.rotation.y = look.x
			actor.camera.rotation.x = clampf(look.y, -1.42, 1.42) + actor.recoil.y
			actor.camera.rotation.y = actor.recoil.x
	if connection_state == "reconnecting":
		_reconnect_clock -= delta
		if _reconnect_clock <= 0:
			_connect_client()
	_input_clock -= delta
	if connection_state == "connected" and _input_clock <= 0:
		_input_clock = 1.0 / 30.0
		_input_rpc.rpc_id(1, _local_input)

@rpc("any_peer", "call_remote", "reliable")
func _join_rpc(player_name: String, token: String, join_ticket: String = "") -> void:
	if not _authority or options.get("mode", "offline") != "server":
		return
	var peer_id: int = multiplayer.get_remote_sender_id()
	if phase == "match_over":
		_rejected_rpc.rpc_id(peer_id, "This match is complete. The next lobby opens when the remaining players leave.")
		return
	if _peer_actors.has(peer_id) or _pending_joins.has(peer_id):
		return
	_expire_reservations()
	var account: String = ""
	var id: int = 0
	if token.length() == 64 and _reservations.has(token):
		var record: Dictionary = _reservations[token]
		if _elapsed < float(record.expires) and not _peer_actors.values().has(int(record.id)):
			id = int(record.id)
	if bool(options.get("require_accounts", false)):
		if id != 0:
			account = str(_account_ids.get(id, ""))
		else:
			_pending_joins[peer_id] = true
			var response: Dictionary = await _bridge.consume_ticket(join_ticket)
			_pending_joins.erase(peer_id)
			if not multiplayer.get_peers().has(peer_id):
				return
			if not bool(response.get("ok", false)):
				_rejected_rpc.rpc_id(peer_id, str(response.get("error", "Account verification failed.")))
				return
			account = str(response.data.get("player_id", ""))
			player_name = str(response.data.get("display_name", "Operator"))
			if account.is_empty():
				_rejected_rpc.rpc_id(peer_id, "The account service returned an invalid identity.")
				return
			for account_actor: int in _account_ids:
				if str(_account_ids[account_actor]) == account:
					if _peer_actors.values().has(account_actor):
						_rejected_rpc.rpc_id(peer_id, "This account is already connected to this server.")
						return
					id = account_actor
	if id == 0:
		for candidate: int in actors:
			var reserved: bool = false
			for entry: Dictionary in _reservations.values():
				if int(entry.id) == candidate and _elapsed < float(entry.expires):
					reserved = true
			if not _peer_actors.values().has(candidate) and not reserved:
				id = candidate
				break
	if id == 0:
		_rejected_rpc.rpc_id(peer_id, "Server is full; disconnected players retain their slots for 60 seconds.")
		return
	# Rotate reconnect credentials so a reused bearer token cannot claim two slots.
	for old_token: String in _reservations.keys():
		if int(_reservations[old_token].id) == id:
			_reservations.erase(old_token)
	var new_token: String = Crypto.new().generate_random_bytes(32).hex_encode()
	_reservations[new_token] = {"id": id, "expires": _elapsed + 86400.0}
	_peer_actors[peer_id] = id
	if not account.is_empty():
		_account_ids[id] = account
	_last_activity[id] = _elapsed
	var clean_name := SBDesign.plain_line(player_name, 24)
	actors[id].display_name = clean_name if not clean_name.is_empty() else "Operator"
	_welcome_rpc.rpc_id(peer_id, id, new_token, _snapshot())
	_announce(actors[id].display_name + " joined Relay Yard")
	if phase == "waiting" and _peer_actors.size() == 10 and _account_ids.size() == 10:
		_start_ranked_match()

func _peer_disconnected(peer_id: int) -> void:
	if not _peer_actors.has(peer_id):
		return
	var id: int = int(_peer_actors[peer_id])
	_peer_actors.erase(peer_id)
	if _ranked_started and phase != "match_over":
		_ranked_eligible = false
		reward_status = "ineligible_disconnect"
	_gate.forget(peer_id)
	for token: String in _reservations:
		if int(_reservations[token].id) == id:
			_reservations[token].expires = _elapsed + 60.0
	_announce.call_deferred(actors[id].display_name + " disconnected; bot taking over")
	if phase == "match_over" and _peer_actors.is_empty() and reward_status != "submitting":
		_reset_server_match.call_deferred()

@rpc("any_peer", "call_remote", "unreliable_ordered", 1)
func _input_rpc(data: Dictionary) -> void:
	if not _authority:
		return
	var peer_id: int = multiplayer.get_remote_sender_id()
	if not _peer_actors.has(peer_id):
		return
	var clean: Dictionary = _gate.validate(peer_id, data, Time.get_ticks_msec())
	if clean.is_empty():
		return
	var id: int = int(_peer_actors[peer_id])
	var old_look: Vector2 = actors[id].input_state.get("look", Vector2.ZERO)
	var new_look: Vector2 = clean.look
	if old_look.distance_to(new_look) > 0.004 or ((clean.move as Vector2).length() > 0.1 and actors[id].velocity.length() > 0.2) or (bool(clean.interact) and _interactions.has(id)):
		_last_activity[id] = _elapsed
	actors[id].input_state = clean
	_last_peer_input[id] = _elapsed

@rpc("any_peer", "call_remote", "reliable", 2)
func _buy_rpc(id: String) -> void:
	if not _authority:
		return
	var peer_id: int = multiplayer.get_remote_sender_id()
	if _peer_actors.has(peer_id) and id.length() <= 24 and _gate.allow_buy(peer_id, Time.get_ticks_msec()):
		_buy(int(_peer_actors[peer_id]), id)

@rpc("authority", "call_remote", "reliable")
func _welcome_rpc(id: int, token: String, data: Dictionary) -> void:
	if _authority:
		return
	local_id = id
	for actor: SBActor in actors.values():
		actor.is_local = actor.actor_id == local_id
	reconnect_token = token
	connection_state = "connected"
	_apply_snapshot(data)
	notification.emit("Connected • account session" if reward_status != "unranked" else "Connected • LAN practice session")

@rpc("authority", "call_remote", "unreliable_ordered", 3)
func _snapshot_rpc(data: PackedByteArray) -> void:
	if not _authority and data.size() < 32768:
		var unpacked: Variant = bytes_to_var(data.decompress_dynamic(65536, FileAccess.COMPRESSION_DEFLATE))
		if unpacked is Dictionary:
			_apply_snapshot(unpacked)

@rpc("authority", "call_remote", "unreliable", 4)
func _shot_rpc(id: int) -> void:
	if actors.has(id):
		actors[id].play_shot_effect()

@rpc("authority", "call_remote", "reliable")
func _rejected_rpc(message: String) -> void:
	connection_state = "failed"
	notification.emit(message)
	multiplayer.multiplayer_peer.close()

@rpc("authority", "call_remote", "reliable")
func _notice_rpc(message: String) -> void:
	notification.emit(message)

func _snapshot() -> Dictionary:
	var utilities: Array = []
	for child: Node in get_children():
		if child is SBUtility:
			utilities.append({"id": child.get_instance_id(), "kind": child.kind, "position": child.position, "detonated": child._detonated, "life": child._lifetime})
	var states: Array = []
	for actor: SBActor in actors.values():
		states.append(actor.snapshot())
	return {"actors": states, "utilities": utilities, "humans": _peer_actors.values(), "contributions": objective_contributions, "reward_status": reward_status, "phase": phase, "round": round_number, "attack": attack_score, "defend": defend_score, "time": time_left, "objective": objective_state, "objective_timer": objective_timer, "objective_position": objective_position, "carrier": objective_carrier, "interactions": _interactions, "elapsed": _elapsed}

func _apply_snapshot(data: Dictionary) -> void:
	reward_status = str(data.get("reward_status", "unranked"))
	_connected_actor_ids = data.get("humans", [])
	phase = data.phase
	round_number = int(data.round)
	attack_score = int(data.attack)
	defend_score = int(data.defend)
	time_left = float(data.time)
	objective_state = data.objective
	objective_timer = float(data.objective_timer)
	objective_position = data.objective_position
	objective_carrier = int(data.carrier)
	_elapsed = float(data.elapsed)
	var progress: float = float(data.interactions.get(local_id, 0))
	interaction_progress = progress / (DEFUSE_SECONDS if objective_state == "planted" else PLANT_SECONDS)
	for state: Dictionary in data.actors:
		var id: int = int(state.get("id", state.get("actor_id", 0)))
		if not actors.has(id):
			_spawn_actor(id, int(state.team), str(state.get("name", "Operator")))
		actors[id].apply_snapshot(state, 0.05)
	objective_contributions = data.get("contributions", {}).duplicate()
	_sync_utility_visuals(data.get("utilities", []))
	if phase == "match_over":
		_emit_results()

func _sync_utility_visuals(states: Array) -> void:
	var present: Array = []
	for state: Dictionary in states:
		var id: int = int(state.id)
		present.append(id)
		if not _remote_utilities.has(id):
			var utility := SBUtility.new()
			utility.kind = str(state.kind)
			utility.visual_only = true
			add_child(utility)
			utility.set_physics_process(false)
			_remote_utilities[id] = utility
		var visual: SBUtility = _remote_utilities[id]
		visual.position = state.position
		if bool(state.detonated) and not visual._detonated:
			visual._detonate()
		# Replica physics is off, so the server's remaining lifetime drives the
		# fade; visuals then thin exactly as the authoritative concealment shrinks.
		if visual._detonated and state.has("life"):
			visual._lifetime = float(state.life)
			if visual.kind == "smoke":
				visual._apply_dissipation()
	for id: int in _remote_utilities.keys():
		if not present.has(id):
			_remote_utilities[id].queue_free()
			_remote_utilities.erase(id)

func _start_ranked_match() -> void:
	_ranked_started = true
	_ranked_eligible = true
	reward_status = "eligible_pending_completion"
	_started_at = Time.get_datetime_string_from_system(true) + "Z"
	_match_started_elapsed = _elapsed
	var random: PackedByteArray = Crypto.new().generate_random_bytes(16)
	random[6] = (random[6] & 15) | 64
	random[8] = (random[8] & 63) | 128
	var hex: String = random.hex_encode()
	_match_id = "%s-%s-%s-%s-%s" % [hex.substr(0, 8), hex.substr(8, 4), hex.substr(12, 4), hex.substr(16, 4), hex.substr(20, 12)]
	_activity_seconds.clear()
	_begin_round()

func _ranked_payload() -> Dictionary:
	var duration: float = _elapsed - _match_started_elapsed
	if not _ranked_eligible or _account_ids.size() != 10 or _peer_actors.size() != 10 or duration < 300 or attack_score == defend_score:
		return {}
	var participants: Array = []
	for id: int in actors:
		if float(_activity_seconds.get(id, 0)) / duration < 0.75:
			return {}
		var actor: SBActor = actors[id]
		participants.append({"player_id": _account_ids[id], "won": (actor.team == 0 and attack_score > defend_score) or (actor.team == 1 and defend_score > attack_score), "active_seconds": mini(int(duration), int(_activity_seconds[id])), "objective_contributions": int(objective_contributions.get(id, 0)), "abandoned": false})
	return {"match_id": _match_id, "mode": "ranked_5v5", "started_at": _started_at, "ended_at": Time.get_datetime_string_from_system(true) + "Z", "participants": participants}

func _submit_ranked_result() -> void:
	var payload: Dictionary = _ranked_payload()
	if payload.is_empty():
		reward_status = "ineligible_match"
		_announce("This match does not qualify for online rewards.")
		if _peer_actors.is_empty():
			_reset_server_match.call_deferred()
		return
	reward_status = "submitting"
	var response: Dictionary = await _bridge.submit_result(payload)
	if bool(response.get("ok", false)):
		reward_status = "committed"
		_announce("Account match rewards committed by the economy service.")
	else:
		reward_status = "submission_failed"
		_announce("Match complete; account reward submission failed. Server logs identify the match for review.")
		push_warning("Reward submission failed for match " + _match_id + ": " + str(response.get("status", 0)))
	if _peer_actors.is_empty():
		_reset_server_match.call_deferred()

func _expire_reservations() -> void:
	for token: String in _reservations.keys():
		var record: Dictionary = _reservations[token]
		if _elapsed >= float(record.expires) and not _peer_actors.values().has(int(record.id)):
			_account_ids.erase(int(record.id))
			_reservations.erase(token)

func _build_device_visual() -> void:
	_device = Node3D.new()
	_device.name = "RelayDevice"
	add_child(_device)
	var housing := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(0.46, 0.22, 0.32)
	housing.mesh = box
	var metal := StandardMaterial3D.new()
	metal.albedo_color = Color("343f49")
	metal.metallic = 0.7
	metal.roughness = 0.35
	housing.material_override = metal
	_device.add_child(housing)
	housing.position.y = 0.15
	var lamp := MeshInstance3D.new()
	var lamp_box := BoxMesh.new()
	lamp_box.size = Vector3(0.35, 0.035, 0.19)
	lamp.mesh = lamp_box
	_device_emission = StandardMaterial3D.new()
	_device_emission.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_device_emission.albedo_color = Color("e2b968")
	lamp.material_override = _device_emission
	_device.add_child(lamp)
	lamp.position.y = 0.285
	var antenna := MeshInstance3D.new()
	var cylinder := CylinderMesh.new()
	cylinder.top_radius = 0.013
	cylinder.bottom_radius = 0.022
	cylinder.height = 0.5
	antenna.mesh = cylinder
	antenna.material_override = metal
	_device.add_child(antenna)
	antenna.position = Vector3(0.18, 0.37, -0.1)
	_device_audio = AudioStreamPlayer3D.new()
	_device_audio.stream = SBActor._synthesize_sound(0.09, 920, 0.0)
	_device_audio.unit_size = 6
	_device_audio.max_distance = 35
	_device_audio.volume_db = -10
	_device.add_child(_device_audio)
	_device.visible = false

func _update_device_visual(delta: float) -> void:
	_device.visible = objective_state in ["planted", "dropped"] and phase == "live"
	if not _device.visible:
		return
	_device.position = objective_position
	if objective_state == "planted":
		var flash: float = 0.55 + 0.45 * sin(_elapsed * (12 if objective_timer < 5 else 5))
		_device_emission.albedo_color = Color("ef5457") * flash
		_beep_clock -= delta
		if _beep_clock <= 0 and options.get("mode", "offline") != "server":
			_device_audio.play()
			_beep_clock = 0.3 if objective_timer < 5 else 1.2
	else:
		_device_emission.albedo_color = Color("e2b968")

func _reset_server_match() -> void:
	if options.get("mode", "offline") != "server" or not _peer_actors.is_empty() or reward_status == "submitting":
		return
	for actor: SBActor in actors.values():
		remove_child(actor)
		actor.queue_free()
	for child: Node in get_children():
		if child is SBUtility:
			child.queue_free()
	actors.clear()
	_gate = SBInputGate.new()
	_bot_state.clear()
	_account_ids.clear()
	_pending_joins.clear()
	_reservations.clear()
	_activity_seconds.clear()
	_last_activity.clear()
	_last_peer_input.clear()
	_damage_history.clear()
	_interactions.clear()
	_heard.clear()
	objective_contributions.clear()
	_ranked_started = false
	_ranked_eligible = false
	_finished_emitted = false
	_match_id = ""
	_started_at = ""
	_match_started_elapsed = 0
	_elapsed = 0
	round_number = 0
	attack_score = 0
	defend_score = 0
	objective_state = "carried"
	objective_timer = 0
	interaction_progress = 0
	local_id = 0
	for id in range(1, 11):
		var actor: SBActor = _spawn_actor(id, 0 if id <= 5 else 1, BOT_NAMES[id - 1])
		actor.reset_for_round(arena.attack_spawns[(id - 1) % 5] if actor.team == 0 else arena.defend_spawns[(id - 1) % 5])
	if bool(options.get("require_accounts", false)):
		phase = "waiting"
		time_left = 0
		reward_status = "waiting_for_accounts"
	else:
		reward_status = "unranked"
		_begin_round()
