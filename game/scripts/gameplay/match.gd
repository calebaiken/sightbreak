class_name TacticalMatch
extends Node3D

signal match_finished(summary: Dictionary)
signal notification(text: String)
signal exit_requested
## Structured elimination for the HUD feed; mirrored to clients by the server.
signal elimination_reported(killer_id: int, victim_id: int, headshot: bool)
## Network protocol, checked in SceneMultiplayer's authentication stage before any
## gameplay RPC. Godot routes RPCs by method index, so builds whose RPC methods,
## arguments or snapshot meaning differ must never be admitted together; they would
## stall silently. Bump this with any such change. 0.3.0 had no handshake.
const PROTOCOL_VERSION := 6
const HANDSHAKE_SECONDS := 5.0
const JOIN_TIMEOUT_SECONDS := 20.0
const HELLO_LIMIT := 512

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
var _team_ai_state: Dictionary = SBBotAI.create_team_state()
var _peer_actors: Dictionary = {}
var _reservations: Dictionary = {}
## One bounded previous credential per actor until welcome is confirmed by input.
## Never authorizes eviction of a live peer or a second actor.
var _resume_aliases: Dictionary = {}
var _last_peer_input: Dictionary = {}
var _damage_history: Dictionary = {}
var _interactions: Dictionary = {}
var _gate := SBInputGate.new()
var _privacy := SBStatePrivacy.new()
var _replica_buffer := SBSnapshotBuffer.new()
var _simulation_tick := 0
var _hit_history := SBHitHistory.new()
var _snapshot_generation := 0
var _input_stream := SBInputStream.new()
var _prediction := SBMovementPrediction.new()
var _prediction_enabled := false
var _pending_reconciliation: Dictionary = {}
var _last_input_sequence: Dictionary = {}
var _local_input: Dictionary = {"move": Vector2.ZERO, "look": Vector2.ZERO}
var _snapshot_clock: float = 0.0
var _input_clock: float = 0.0
var _bot_clock: float = 0.0
var _heard: Dictionary = {}
var _spectator: Camera3D
var _finished_emitted: bool = false
var _elapsed: float = 0.0
var _reconnect_clock: float = 0.0
var _recovery := SBReconnectPolicy.new()
var _reconnect_at_msec := 0
## Seconds spent in the current pre-game client state (connecting, authenticating,
## joining); bounded by JOIN_TIMEOUT_SECONDS.
var _state_clock: float = 0.0
## Server: peers that failed the version check, dropped once their reply is sent.
var _handshake_drops: Dictionary = {}
var _handshake_seen: Dictionary = {}
var _auth_started := 0.0
var reward_status: String = "unranked"
var _bridge: SBEconomyBridge
var _account_ids: Dictionary = {}
var _pending_joins: Dictionary = {}
var _join_slots: Dictionary = {}
var _join_accounts: Dictionary = {}
var _peer_lifecycle := SBPeerLifecycle.new()
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
## At most one hitscan contact per actor per authoritative tick (ten-actor roster).
## Cleared before/after each tick; never replicated or consulted by prediction.
var _pending_hitscan_hits: Array[Dictionary] = []

func configure(settings: Dictionary) -> void:
	options = settings.duplicate()
	_prediction_enabled = bool(options.get("prediction", OS.get_cmdline_user_args().has("--network-prediction")))
	_replica_buffer.delay_seconds = clampf(float(options.get("interpolation_delay", 0.10)), 0.05, 0.20)
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
	# Only an explicitly configured debug/offline observer can declare initial
	# objective-test conditions. Trace-only and all network runs return no fixture.
	var initial_conditions: Dictionary = preload("res://scripts/offline_diagnostics.gd").fixture_for(options, arena)
	var stock_attack_spawns: Array[Vector3] = arena.attack_spawns.duplicate()
	var stock_defend_spawns: Array[Vector3] = arena.defend_spawns.duplicate()
	if not initial_conditions.is_empty():
		_rng.seed = int(initial_conditions.seed)
		arena.attack_spawns.assign(initial_conditions.attack_spawns)
		arena.defend_spawns.assign(initial_conditions.defend_spawns)
	if _authority:
		for id in range(1, 11):
			var side := 0 if id <= 5 else 1
			if initial_conditions.get("scenario", "") == "defuse" and id in [1, 6]: side = 1 - side
			var actor := _spawn_actor(id, side, str(options.get("name", "Operator")) if id == local_id else BOT_NAMES[id - 1])
			if not initial_conditions.is_empty(): actor._rng.seed = int(initial_conditions.seed) * 97 + id
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
	# Restore stock spawn definitions before the first physics tick. Only the
	# declared first-round actor locations/side and RNG initialization differed.
	if not initial_conditions.is_empty():
		arena.attack_spawns.assign(stock_attack_spawns)
		arena.defend_spawns.assign(stock_defend_spawns)
	if mode == "server":
		_host()
	elif mode == "client":
		multiplayer.connected_to_server.connect(_connected)
		multiplayer.connection_failed.connect(_connection_failed)
		multiplayer.server_disconnected.connect(_server_disconnected)
		var api := multiplayer as SceneMultiplayer
		api.peer_authenticating.connect(_send_hello)
		api.peer_authentication_failed.connect(_handshake_failed)
		_connect_client()

func _exit_tree() -> void:
	if str(options.get("mode", "offline")) != "offline":
		multiplayer.multiplayer_peer = OfflineMultiplayerPeer.new()
		(multiplayer as SceneMultiplayer).auth_callback = Callable()

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
	_bot_state[actor.actor_id] = SBBotAI.create_state(actor)

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

func _process(delta: float) -> void:
	if _authority or connection_state != "connected":
		return
	_replica_buffer.advance(delta)
	for actor: SBActor in actors.values():
		if actor.actor_id == local_id or not actor.visible:
			continue
		var pose := _replica_buffer.sample(actor.actor_id)
		if pose.is_empty():
			continue
		actor.global_position = pose.position
		actor.velocity = pose.velocity
		actor.yaw = pose.yaw
		actor.pitch = pose.pitch
		actor.rotation.y = actor.yaw
	if local_actor() != null and local_actor().alive and _prediction_enabled:
		_prediction.present(local_actor(), delta)
	_update_spectator()

func _authority_tick(delta: float) -> void:
	_simulation_tick += 1
	if options.get("mode", "offline") == "server":
		_service_peers()
	for peer_id: int in _peer_actors:
		var id: int = _peer_actors[peer_id]
		var command := _input_stream.pop(peer_id)
		if not command.is_empty():
			# Only immutable consumed intent can qualify activity. Packet tails may
			# contain acknowledged, replaced or backlog-discarded commands.
			var old_look: Vector2 = actors[id].input_state.get("look", Vector2.ZERO)
			var new_look: Vector2 = command.look
			if old_look.distance_to(new_look) > 0.004 or ((command.move as Vector2).length() > 0.1 and actors[id].velocity.length() > 0.2) or (bool(command.interact) and _interactions.has(id)):
				_last_activity[id] = _elapsed
			actors[id].input_state = command
			_last_input_sequence[id] = int(command.sequence)
		# On a short packet gap keep held controls, as before input sequencing.
		# Neutralizing every gap invents new semi-auto/jump rising edges. The
		# existing 300 ms silence guard below releases controls on sustained loss.
	if not _handshake_drops.is_empty():
		_drop_rejected_peers()
	_bot_clock -= delta
	if _bot_clock <= 0:
		_bot_clock = 0.12
		for actor: SBActor in actors.values():
			if _is_bot(actor.actor_id):
				_bot_input(actor, 0.12)
	if local_actor() != null:
		local_actor().input_state = _local_input.duplicate()
	var suspended_actor_edges: Dictionary = {}
	_pending_hitscan_hits.clear()
	# Shared post-movement shot geometry: no actor fires at a later actor's old pose.
	for actor: SBActor in actors.values():
		if phase != "live":
			actor.input_state = {"move": Vector2.ZERO, "look": actor.input_state.get("look", Vector2(actor.yaw, actor.pitch))}
		elif not _is_bot(actor.actor_id) and actor.actor_id != local_id:
			if _elapsed - float(_last_peer_input.get(actor.actor_id, -10.0)) > 0.3:
				suspended_actor_edges[actor.actor_id] = [actor._fire_previous, actor._jump_previous, actor._grenade_previous, actor._smoke_previous]
				actor.input_state = {"move": Vector2.ZERO, "look": Vector2(actor.yaw, actor.pitch)}
		actor.tick_authority_movement(delta)
	# All traces precede this tick's hitscan damage, so eligible return fire and
	# front-actor shielding cannot disappear because of Dictionary insertion order.
	for actor: SBActor in actors.values():
		actor.tick_authority_actions(delta, _queue_hitscan_hit)
		var suspended_edges: Array = suspended_actor_edges.get(actor.actor_id, [])
		if not suspended_edges.is_empty():
			# Silence stops movement/actions, but is not a real button release.
			actor._fire_previous = suspended_edges[0]
			actor._jump_previous = suspended_edges[1]
			actor._grenade_previous = suspended_edges[2]
			actor._smoke_previous = suspended_edges[3]
		if _ranked_started and phase != "match_over" and _peer_actors.values().has(actor.actor_id):
			if _elapsed - float(_last_activity.get(actor.actor_id, -100)) <= 10:
				_activity_seconds[actor.actor_id] = float(_activity_seconds.get(actor.actor_id, 0)) + delta
	for hit: Dictionary in _pending_hitscan_hits:
		var source: SBActor = hit.source
		source.resolve_shot_hit(hit.target, hit.amount, hit.headshot)
	_pending_hitscan_hits.clear()
	# Opt-in diagnostics only: no live shot ever consults historical state.
	if options.get("mode", "offline") == "server" and bool(options.get("record_hit_history", false)):
		_hit_history.record(_simulation_tick, _snapshot_generation, actors)
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
	# 60 Hz physics / three ticks = exact 20 Hz. A float countdown previously
	# retained a positive residue on tick three and actually replicated at 15 Hz.
	if options.get("mode", "offline") == "server" and _simulation_tick % 3 == 0:
		for peer_id: int in _active_peers():
			var packed: PackedByteArray = var_to_bytes(_snapshot(int(_peer_actors[peer_id]))).compress(FileAccess.COMPRESSION_DEFLATE)
			_snapshot_rpc.rpc_id(peer_id, packed)

func _queue_hitscan_hit(source: SBActor, target: SBActor, amount: float, headshot: bool) -> void:
	_pending_hitscan_hits.append({"source": source, "target": target, "amount": amount, "headshot": headshot})

func _is_bot(id: int) -> bool:
	return id != local_id and not (_peer_actors.values() if _authority else _connected_actor_ids).has(id)

func _begin_round() -> void:
	_snapshot_generation += 1
	_input_stream.reset_epoch()
	_last_input_sequence.clear()
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
	_team_ai_state = SBBotAI.create_team_state()
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
			actor.buy_weapon(SBBotAI.choose_buy_weapon(actor, str(options.get("difficulty", "normal")), round_number))
		actor.input_state = {"move": Vector2.ZERO, "look": Vector2(PI if actor.team == 0 else 0, 0)}
	SBBotAI.select_round_plan(self, 0)
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
				_announce_team("Relay device recovered", 0)
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
	SBBotAI.record_damage(_bot_state, actors, victim, attacker, _elapsed)

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
	SBBotAI.record_elimination(_team_ai_state, _bot_state, actors, victim, _elapsed)
	if victim == objective_carrier and objective_state == "carried":
		objective_state = "dropped"
		objective_position = killed.position
		objective_carrier = 0
		_announce_team("Relay device dropped", 0)

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
			var recipient: int = _peer_actors[peer_id]
			var viewer := SBStatePrivacy.observer(self, recipient)
			if viewer == null:
				continue
			if actors[recipient].team == actors[id].team or _privacy.observable(self, viewer, actors[id], SBStatePrivacy.viewpoint(self, recipient)):
				_shot_rpc.rpc_id(peer_id, id, origin, actors[id].weapon_id)
			elif viewer.global_position.distance_to(origin) <= 65:
				# A sound supplies an approximate audible location, never a hidden ID
				# or continuous tracking stream. Preserve the existing 65 m audio range.
				_audible_shot_rpc.rpc_id(peer_id, origin.snapped(Vector3.ONE), actors[id].weapon_id)

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
		var recipient: int = _peer_actors[peer_id]
		if _privacy.point_visible(self, SBStatePrivacy.observer(self, recipient), at + normal * 0.02, SBStatePrivacy.viewpoint(self, recipient)):
			_impact_rpc.rpc_id(peer_id, at, normal, hit_actor)

@rpc("authority", "call_remote", "unreliable", 4)
func _impact_rpc(at: Vector3, normal: Vector3, hit_actor: bool) -> void:
	if _authority or not at.is_finite() or not normal.is_finite(): return
	if absf(at.x) > 256 or absf(at.y) > 256 or absf(at.z) > 256: return
	if normal.length_squared() < 0.5 or normal.length_squared() > 1.5: return
	load("res://scripts/gameplay/combat_effects.gd").for_world(self).impact(at, normal.normalized(), hit_actor)

func _bot_input(actor: SBActor, delta: float) -> void:
	SBBotAI.compute_bot_input(self, actor, delta)

func _nearest_defender() -> int:
	return SBBotAI.nearest_defender(self)

func _cover_position(actor: SBActor, threat: SBActor) -> Vector3:
	return SBBotAI.cover_position(self, actor, threat)

func _update_spectator() -> void:
	var actor: SBActor = local_actor()
	if actor == null or not actor.alive:
		_spectator.current = true
		if actor:
			for teammate: SBActor in actors.values():
				if teammate.alive and teammate.team == actor.team:
					_spectator.global_position = SBStatePrivacy.spectator_position(get_world_3d(), teammate)
					_spectator.look_at(teammate.global_position + Vector3(0, 1.3, 0))
					break
	elif actor.camera:
		actor.camera.current = true

func _announce(message: String) -> void:
	notification.emit(message)
	if options.get("mode", "offline") == "server":
		for peer_id: int in _active_peers():
			_notice_rpc.rpc_id(peer_id, message)

func _announce_team(message: String, team: int) -> void:
	if options.get("mode", "offline") != "server":
		if local_actor() != null and local_actor().team == team:
			notification.emit(message)
		return
	for peer_id: int in _active_peers():
		if actors[_peer_actors[peer_id]].team == team:
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
	# Version handshake before any gameplay RPC (see PROTOCOL_VERSION).
	var api := multiplayer as SceneMultiplayer
	api.auth_timeout = HANDSHAKE_SECONDS
	api.auth_callback = _server_handshake
	api.peer_authentication_failed.connect(_handshake_failed)
	multiplayer.multiplayer_peer = peer
	multiplayer.peer_disconnected.connect(_peer_disconnected)
	multiplayer.peer_connected.connect(_peer_connected)
	connection_state = "hosting"
	print("SIGHTBREAK_SERVER_READY port=%d" % int(options.get("port", 27020)))

func _connect_client() -> void:
	if _recovery.deadline > 0 and not _recovery.take_attempt(Time.get_ticks_msec()):
		_fail_connection("Reconnect window expired. Join again to request a fresh session.")
		return
	_close_client()
	_replica_buffer.clear()
	_prediction.reset(true)
	_pending_reconciliation.clear()
	connection_state = "connecting"
	_state_clock = 0.0
	var api := multiplayer as SceneMultiplayer
	api.auth_timeout = HANDSHAKE_SECONDS
	api.auth_callback = _client_handshake
	var peer := ENetMultiplayerPeer.new()
	var error: Error = peer.create_client(str(options.get("address", "127.0.0.1")), int(options.get("port", 27020)))
	if error != OK:
		_connection_failed()
		return
	multiplayer.multiplayer_peer = peer
	notification.emit("Connecting to Relay Yard…")

func _connected() -> void:
	connection_state = "joining"
	_state_clock = 0.0
	_join_rpc.rpc_id(1, str(options.get("name", "Operator")).left(24), reconnect_token, str(options.get("join_ticket", "")))

func _connection_failed() -> void:
	# Keep a more specific reason (version mismatch, join timeout) already shown.
	if connection_state == "failed":
		return
	if _retry_resume("Transport unavailable; retrying the reserved session…"):
		return
	_fail_connection("Connection failed. Check the address and UDP port.")

## The hello both sides exchange during SceneMultiplayer authentication.
func _hello(accepted: bool, reason: String) -> PackedByteArray:
	return JSON.stringify({"game": "sightbreak", "protocol": PROTOCOL_VERSION, "build": str(ProjectSettings.get_setting("application/config/version", "")), "accepted": accepted, "reason": reason}).to_utf8_buffer()

## Untrusted peer data: bounded size, a JSON object or nothing.
static func _read_hello(data: PackedByteArray) -> Dictionary:
	if data.size() > HELLO_LIMIT:
		return {}
	var parsed: Variant = JSON.parse_string(data.get_string_from_utf8())
	return parsed if parsed is Dictionary and str(parsed.get("game", "")) == "sightbreak" else {}

## The hello's protocol number, or -1 for anything but a whole number (2.9, inf,
## text and missing values are unreadable rather than rounded).
static func _hello_protocol(hello: Dictionary) -> int:
	var value: Variant = hello.get("protocol")
	if not (value is float or value is int):
		return -1
	var number := float(value)
	return int(number) if is_finite(number) and number == floorf(number) and number >= 0.0 and number < 1000000.0 else -1

func _server_handshake(peer_id: int, data: PackedByteArray) -> void:
	# Only a peer's first hello counts. Later ones are ignored, so a peer cannot
	# re-arm its drop timer, multiply replies or reverse a decision.
	if _handshake_seen.has(peer_id):
		return
	_handshake_seen[peer_id] = true
	# A lost close must not retain one of the ten ENet transports indefinitely.
	# ENet ACK/ping health is separate from the 30-second gameplay-input idle rule.
	var transport := multiplayer.multiplayer_peer as ENetMultiplayerPeer
	var packet_peer := transport.get_peer(peer_id)
	packet_peer.ping_interval(500)
	packet_peer.set_timeout(32, 3000, 5000)
	var api := multiplayer as SceneMultiplayer
	var hello := _read_hello(data)
	var protocol := _hello_protocol(hello)
	if protocol == PROTOCOL_VERSION:
		api.send_auth(peer_id, _hello(true, ""))
		api.complete_auth(peer_id)
		return
	# Never admitted: no join, slot or account ticket is touched for this peer.
	var reason := "This server uses network protocol %d; this client sent %s." % [PROTOCOL_VERSION, "protocol %d" % protocol if protocol >= 0 else "no readable protocol"]
	api.send_auth(peer_id, _hello(false, reason))
	_handshake_drops[peer_id] = Time.get_ticks_msec() + 500
	print("PROTOCOL_REJECTED peer=%d client_protocol=%d" % [peer_id, protocol])

func _client_handshake(peer_id: int, data: PackedByteArray) -> void:
	var hello := _read_hello(data)
	var protocol := _hello_protocol(hello)
	if hello.get("accepted") is bool and hello.accepted and protocol == PROTOCOL_VERSION:
		(multiplayer as SceneMultiplayer).complete_auth(peer_id)
		connection_state = "joining"
		_state_clock = 0.0
		return
	var detail := str(hello.get("reason", "")).left(200) if not hello.is_empty() else "The server's version handshake could not be read."
	_fail_connection("Version mismatch: this client uses SIGHTBREAK network protocol %d. %s Install the same SIGHTBREAK version as the server to join." % [PROTOCOL_VERSION, detail])
	print("PROTOCOL_CLIENT_REJECTED server_protocol=%d" % protocol)

func _send_hello(peer_id: int) -> void:
	if _authority or peer_id != 1:
		return
	connection_state = "authenticating"
	_auth_started = _elapsed
	(multiplayer as SceneMultiplayer).send_auth(peer_id, _hello(true, ""))

func _handshake_failed(peer_id: int) -> void:
	if _authority:
		# A peer without the handshake (0.3.0 and earlier clients) or a silent one.
		_handshake_drops.erase(peer_id)
		_handshake_seen.erase(peer_id)
		print("PROTOCOL_TIMEOUT peer=%d" % peer_id)
		return
	if connection_state == "failed":
		return
	if _recovery.deadline > 0 and _retry_resume("Version check interrupted; retrying the reserved session…"):
		return
	if _elapsed - _auth_started < HANDSHAKE_SECONDS - 0.5:
		# The server hung up before the timeout; any reason it queued was discarded
		# with the connection, so do not guess that it is the older side.
		_fail_connection("The server closed the connection during the version check. It may run a different SIGHTBREAK version, or the connection dropped. Join a server running the same version as this client.")
	else:
		_fail_connection("No version handshake from the server within %d seconds. It is probably running an older SIGHTBREAK release (0.3.0 has no handshake) or is not a SIGHTBREAK server. Join a server running the same version as this client." % int(HANDSHAKE_SECONDS))

## Disconnects peers that failed the version check once their reply had time to go out.
func _drop_rejected_peers() -> void:
	var api := multiplayer as SceneMultiplayer
	for peer_id: int in _handshake_drops.keys():
		if Time.get_ticks_msec() < int(_handshake_drops[peer_id]):
			continue
		_handshake_drops.erase(peer_id)
		if api.get_authenticating_peers().has(peer_id):
			api.disconnect_peer(peer_id)

## Terminal client failure: shows the reason and never retries on its own.
func _fail_connection(message: String) -> void:
	connection_state = "failed"
	notification.emit(message)
	print("PROTOCOL_CLIENT_FAILED " + message)
	_recovery.clear()
	var retired := multiplayer.multiplayer_peer
	_close_retired_client.call_deferred(retired)

func _close_retired_client(retired: MultiplayerPeer) -> void:
	# A queued failure must not close a later replacement transport.
	if retired != null and retired == multiplayer.multiplayer_peer:
		retired.close()

func _close_client() -> void:
	if multiplayer.multiplayer_peer != null and not (multiplayer.multiplayer_peer is OfflineMultiplayerPeer):
		multiplayer.multiplayer_peer.close()

func _retry_resume(message: String) -> bool:
	if reconnect_token.length() != 64 or connection_state == "failed":
		return false
	_recovery.begin(Time.get_ticks_msec())
	if not _recovery.available(Time.get_ticks_msec()):
		_fail_connection("Reconnect window expired. Join again to request a fresh session.")
		return true
	if connection_state != "reconnecting":
		connection_state = "reconnecting"
		_replica_buffer.clear()
		_reconnect_clock = _recovery.delay_seconds()
		_reconnect_at_msec = 0
		var retired := multiplayer.multiplayer_peer
		_close_retired_client.call_deferred(retired)
		notification.emit(message)
	return true

func _server_disconnected() -> void:
	if connection_state == "failed" or connection_state == "reconnecting":
		return
	if _retry_resume("Server disconnected. Attempting to reconnect…"):
		return
	# Preserve the initial disconnect notification for clients without a session;
	# their next admission failure is terminal and has no automatic retry episode.
	connection_state = "reconnecting"
	_replica_buffer.clear()
	_reconnect_clock = 2
	_reconnect_at_msec = 0
	notification.emit("Server disconnected. Attempting to reconnect…")

func _client_tick(delta: float) -> void:
	for utility: SBUtility in _remote_utilities.values():
		utility.set_replica_lifetime(utility._lifetime - delta)
	var actor: SBActor = local_actor()
	if actor != null and connection_state == "connected":
		if not _pending_reconciliation.is_empty():
			var previous_position := actor.global_position
			actor.apply_snapshot(_pending_reconciliation.state, 1.0)
			_prediction.reconcile(actor, _pending_reconciliation.state, int(_pending_reconciliation.epoch), previous_position, _prediction_enabled)
			_pending_reconciliation.clear()
		var controls := _local_input.duplicate()
		if phase != "live" or not actor.alive:
			controls = {"move": Vector2.ZERO, "look": controls.get("look", Vector2(actor.yaw, actor.pitch))}
		_prediction.predict(actor, controls, _replica_buffer.epoch, _prediction_enabled)
	if actor and actor.alive:
		var look: Vector2 = _local_input.get("look", Vector2(actor.yaw, actor.pitch))
		# Aim responds locally; movement replays against server acknowledgments.
		if look.is_finite():
			actor.rotation.y = look.x
			actor.camera.rotation.x = clampf(look.y, -1.42, 1.42) + actor.recoil.y
			actor.camera.rotation.y = actor.recoil.x
	var now := Time.get_ticks_msec()
	if _recovery.deadline > 0 and now >= _recovery.deadline:
		_fail_connection("Reconnect window expired. Join again to request a fresh session.")
	if connection_state == "reconnecting":
		if _reconnect_at_msec == 0:
			_reconnect_at_msec = now + int(_reconnect_clock * 1000)
		if now >= _reconnect_at_msec:
			_connect_client()
	if connection_state == "connecting" and _recovery.deadline > 0 and now - _recovery.attempt_started >= SBReconnectPolicy.ATTEMPT_MSEC:
		_retry_resume("Transport capacity has not recovered; retrying the reserved session…")
	if connection_state in ["connecting", "authenticating", "joining"]:
		_state_clock += delta
		if _state_clock > JOIN_TIMEOUT_SECONDS:
			_fail_connection("The server did not admit this player within %d seconds (%s). Check the address and try again." % [int(JOIN_TIMEOUT_SECONDS), connection_state])
	_input_clock -= delta
	if connection_state == "connected" and _input_clock <= 0:
		_input_clock = 1.0 / 30.0
		var packet := _prediction.packet()
		if not packet.commands.is_empty():
			var packed := var_to_bytes(packet).compress(FileAccess.COMPRESSION_DEFLATE)
			if packed.size() > 1100:
				packet.commands = [packet.commands.back()]
				packed = var_to_bytes(packet).compress(FileAccess.COMPRESSION_DEFLATE)
			_input_rpc.rpc_id(1, packed)

func _peer_connected(peer_id: int) -> void:
	if not _peer_lifecycle.connected(peer_id, Time.get_ticks_msec()):
		(multiplayer as SceneMultiplayer).disconnect_peer(peer_id)

func _service_peers() -> void:
	for peer_id: int in _peer_lifecycle.expired(Time.get_ticks_msec()):
		# Server enforces release even if a hostile client ignores rejection RPCs.
		(multiplayer as SceneMultiplayer).disconnect_peer(peer_id)
		_peer_disconnected(peer_id)

func _reject_join(peer_id: int, reason: String) -> void:
	_pending_joins.erase(peer_id)
	_join_slots.erase(peer_id)
	_join_accounts.erase(peer_id)
	_peer_lifecycle.reject(peer_id, Time.get_ticks_msec())
	if multiplayer.get_peers().has(peer_id):
		_rejected_rpc.rpc_id(peer_id, reason)

func _join_current(peer_id: int, attempt: int) -> bool:
	return _peer_lifecycle.current(peer_id, attempt, Time.get_ticks_msec()) and int(_pending_joins.get(peer_id, -1)) == attempt and multiplayer.get_peers().has(peer_id)

func _available_join_slot(account: String, reconnect_id: int) -> int:
	if not account.is_empty():
		if _join_accounts.values().has(account):
			return 0
		for account_actor: int in _account_ids:
			if str(_account_ids[account_actor]) == account:
				return 0 if _peer_actors.values().has(account_actor) or _join_slots.values().has(account_actor) else account_actor
	if reconnect_id != 0:
		return 0 if _peer_actors.values().has(reconnect_id) or _join_slots.values().has(reconnect_id) else reconnect_id
	for candidate: int in actors:
		if _peer_actors.values().has(candidate) or _join_slots.values().has(candidate):
			continue
		var reserved := false
		for entry: Dictionary in _reservations.values():
			if int(entry.id) == candidate and _elapsed < float(entry.expires):
				reserved = true
		if not reserved:
			return candidate
	return 0

@rpc("any_peer", "call_remote", "reliable")
func _join_rpc(player_name: String, token: String, join_ticket: String = "") -> void:
	if not _authority or options.get("mode", "offline") != "server":
		return
	var peer_id: int = multiplayer.get_remote_sender_id()
	var attempt := _peer_lifecycle.begin_join(peer_id, Time.get_ticks_msec())
	if attempt < 0 or _peer_actors.has(peer_id):
		return
	if phase == "match_over":
		_reject_join(peer_id, "This match is complete. The next lobby opens when the remaining players leave.")
		return
	if player_name.length() > 128 or token.length() > 128 or join_ticket.length() > 128:
		_reject_join(peer_id, "Invalid admission data.")
		return
	_expire_reservations()
	_pending_joins[peer_id] = attempt
	var account := ""
	var id := 0
	if not token.is_empty():
		# A resume credential never falls through to a new guest/account identity.
		var reservation_token := token
		if token.length() == 64 and not _reservations.has(token):
			for alias: Dictionary in _resume_aliases.values():
				if str(alias.token) == token and Time.get_ticks_msec() < int(alias.expires):
					reservation_token = str(alias.current_token)
					break
		if token.length() != 64 or not _reservations.has(reservation_token):
			_reject_join(peer_id, "Reconnect reservation is invalid or expired. Join again for a fresh session.")
			return
		var record: Dictionary = _reservations[reservation_token]
		if _elapsed >= float(record.expires) or not actors.has(int(record.id)):
			_reject_join(peer_id, "Reconnect reservation is invalid or expired. Join again for a fresh session.")
			return
		id = int(record.id)
		if _peer_actors.values().has(id) or _join_slots.values().has(id):
			# Valid reservation, but the old transport has not retired. Do not evict
			# live authority, inspect/consume a ticket, or allocate another actor.
			_pending_joins.erase(peer_id)
			_peer_lifecycle.reject(peer_id, Time.get_ticks_msec())
			_retry_join_rpc.rpc_id(peer_id)
			return
	var needs_ticket := bool(options.get("require_accounts", false)) and id == 0
	if bool(options.get("require_accounts", false)):
		if id != 0:
			account = str(_account_ids.get(id, ""))
		else:
			var inspected: Dictionary = await _bridge.inspect_ticket(join_ticket)
			if not _join_current(peer_id, attempt):
				return
			if not bool(inspected.get("ok", false)):
				_reject_join(peer_id, str(inspected.get("error", "Account verification failed.")))
				return
			account = str(inspected.data.get("player_id", ""))
			player_name = str(inspected.data.get("display_name", "Operator"))
		if account.is_empty():
			_reject_join(peer_id, "The account service returned an invalid identity.")
			return
	id = _available_join_slot(account, id)
	if id == 0:
		_reject_join(peer_id, "No slot is available for this account; disconnected players retain their slots for 60 seconds.")
		return
	# Reserve capacity before the irreversible one-use ticket consumption.
	_join_slots[peer_id] = id
	if not account.is_empty():
		_join_accounts[peer_id] = account
	if needs_ticket:
		var response: Dictionary = await _bridge.consume_ticket(join_ticket)
		if not _join_current(peer_id, attempt):
			return
		if not bool(response.get("ok", false)) or str(response.get("data", {}).get("player_id", "")) != account:
			_reject_join(peer_id, "Account ticket consumption failed; request a fresh ticket.")
			return
	if phase == "match_over" or not _peer_lifecycle.admitted(peer_id, attempt, Time.get_ticks_msec()):
		_reject_join(peer_id, "Admission expired; reconnect with a fresh ticket.")
		return
	_pending_joins.erase(peer_id)
	_join_slots.erase(peer_id)
	_join_accounts.erase(peer_id)
	# Rotate reconnect credentials so a reused bearer token cannot claim two slots.
	for old_token: String in _reservations.keys():
		if int(_reservations[old_token].id) == id:
			_reservations.erase(old_token)
	var new_token: String = Crypto.new().generate_random_bytes(32).hex_encode()
	_reservations[new_token] = {"id": id, "expires": _elapsed + 86400.0}
	if not token.is_empty():
		var prior: Dictionary = _resume_aliases.get(id, {})
		var expires := Time.get_ticks_msec() + SBReconnectPolicy.WINDOW_MSEC
		if str(prior.get("token", "")) == token:
			expires = int(prior.expires)
		_resume_aliases[id] = {"token": token, "current_token": new_token, "peer": peer_id, "generation": attempt, "expires": expires}
	else:
		_resume_aliases.erase(id)
	_peer_actors[peer_id] = id
	_last_input_sequence[id] = 0
	if not account.is_empty():
		_account_ids[id] = account
	_last_activity[id] = _elapsed
	var clean_name := SBDesign.plain_line(player_name, 24)
	actors[id].display_name = clean_name if not clean_name.is_empty() else "Operator"
	_welcome_rpc.rpc_id(peer_id, id, new_token, _snapshot(id))
	_announce(actors[id].display_name + " joined Relay Yard")
	if phase == "waiting" and _peer_actors.size() == 10 and _account_ids.size() == 10:
		_start_ranked_match()

func _peer_disconnected(peer_id: int) -> void:
	_peer_lifecycle.forget(peer_id)
	_pending_joins.erase(peer_id)
	_join_slots.erase(peer_id)
	_join_accounts.erase(peer_id)
	_handshake_drops.erase(peer_id)
	_gate.forget(peer_id)
	_handshake_seen.erase(peer_id)
	_input_stream.forget(peer_id)
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
func _input_rpc(packed: PackedByteArray) -> void:
	if not _authority:
		return
	var peer_id: int = multiplayer.get_remote_sender_id()
	if not _peer_actors.has(peer_id) or not _peer_lifecycle.allow_input(peer_id, Time.get_ticks_msec()) or packed.is_empty() or packed.size() > 1100:
		return
	var decoded: Variant = bytes_to_var(packed.decompress_dynamic(8192, FileAccess.COMPRESSION_DEFLATE))
	if not decoded is Dictionary:
		return
	var data: Dictionary = decoded
	if not _input_stream.accept(peer_id, data, _snapshot_generation, Time.get_ticks_msec()):
		return
	_peer_lifecycle.active(peer_id, Time.get_ticks_msec())
	var id: int = int(_peer_actors[peer_id])
	var alias: Dictionary = _resume_aliases.get(id, {})
	if int(alias.get("peer", -1)) == peer_id and int(alias.get("generation", -1)) == int(_peer_lifecycle.peers[peer_id].generation):
		# The stock client cannot send these inputs before processing its welcome.
		# Retire the previous credential only after this generation proves delivery.
		_resume_aliases.erase(id)
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
	_recovery.clear()
	connection_state = "connected"
	_apply_snapshot(data)
	notification.emit("Connected • account session" if reward_status != "unranked" else "Connected • LAN practice session")

@rpc("authority", "call_remote", "unreliable_ordered", 3)
func _snapshot_rpc(data: PackedByteArray) -> void:
	if not _authority and connection_state == "connected" and data.size() < 32768:
		var unpacked: Variant = bytes_to_var(data.decompress_dynamic(65536, FileAccess.COMPRESSION_DEFLATE))
		if unpacked is Dictionary:
			_apply_snapshot(unpacked)

@rpc("authority", "call_remote", "unreliable", 4)
func _shot_rpc(id: int, at: Vector3 = Vector3.ZERO, weapon: String = "") -> void:
	if not _authority and actors.has(id) and actors[id].visible:
		actors[id].play_shot_effect()
	elif not _authority:
		# Event and snapshot channels may arrive in either order at a corner.
		# Preserve authorized audio without exposing or moving a hidden actor.
		_audible_shot_rpc(at, weapon)

@rpc("authority", "call_remote", "unreliable", 4)
func _audible_shot_rpc(at: Vector3, weapon: String) -> void:
	if _authority or not at.is_finite() or at.length() > 1024 or not SBWeapons.DATA.has(weapon):
		return
	# Bound transient audio nodes even when delayed unreliable packets bunch up.
	if get_tree().get_nodes_in_group("network_shot_audio").size() >= 24:
		return
	var audio := AudioStreamPlayer3D.new()
	audio.stream = SBActor._shot_streams.get(weapon)
	audio.max_distance = 65
	audio.unit_size = 9
	audio.volume_db = -10
	add_child(audio)
	audio.add_to_group("network_shot_audio")
	audio.position = at
	audio.finished.connect(audio.queue_free)
	audio.play()

@rpc("authority", "call_remote", "reliable")
func _retry_join_rpc() -> void:
	if not _retry_resume("Previous session is still retiring; retrying the reserved actor…"):
		_fail_connection("No reconnect credential is available. Join again for a fresh session.")

@rpc("authority", "call_remote", "reliable")
func _rejected_rpc(message: String) -> void:
	_fail_connection(message)

@rpc("authority", "call_remote", "reliable")
func _notice_rpc(message: String) -> void:
	notification.emit(message)

func _snapshot(recipient_id: int = 0) -> Dictionary:
	if recipient_id != 0:
		return _privacy.snapshot(self, recipient_id)
	# Full state is retained solely for authority/offline rule tests. Both wire
	# call sites always pass a server-bound recipient ID.
	var utilities: Array = []
	for child: Node in get_children():
		if child is SBUtility:
			utilities.append({"id": child.get_instance_id(), "kind": child.kind, "position": child.position, "detonated": child._detonated, "life": child._lifetime})
	var states: Array = []
	for actor: SBActor in actors.values():
		states.append(actor.snapshot())
	return {"tick": _simulation_tick, "epoch": _snapshot_generation, "actors": states, "utilities": utilities, "humans": _peer_actors.values(), "contributions": objective_contributions, "reward_status": reward_status, "phase": phase, "round": round_number, "attack": attack_score, "defend": defend_score, "time": time_left, "objective": objective_state, "objective_timer": objective_timer, "objective_position": objective_position, "carrier": objective_carrier, "interactions": _interactions, "elapsed": _elapsed}

func _apply_snapshot(data: Dictionary) -> void:
	if not SBSnapshotSchema.valid(data):
		return
	var discontinuity := int(data.epoch) != _replica_buffer.epoch
	if not _authority and not _replica_buffer.push(int(data.tick), float(data.elapsed), int(data.epoch), data.actors):
		return
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
		var newly_spawned := not actors.has(id)
		if not actors.has(id):
			_spawn_actor(id, int(state.team), str(state.get("name", "Operator")))
		var actor: SBActor = actors[id]
		var previous_position := actor.global_position
		var previous_yaw := actor.yaw
		var previous_pitch := actor.pitch
		var relevant: bool = state.get("relevant", true)
		if not relevant:
			# Erase cached spatial/private state on revocation. A modified client
			# can remember old observations, but receives no fresh hidden updates.
			actor.apply_snapshot({"team": state.team, "alive": state.alive, "kills": state.kills, "deaths": state.deaths, "assists": state.assists, "position": Vector3.ZERO, "velocity": Vector3.ZERO, "health": 0, "credits": 0, "ammo": 0, "reserve": 0, "grenades": 0, "smokes": 0, "inventory": []}, 1.0)
		else:
			var presentation := state.duplicate()
			for field: String in ["health", "credits", "ammo", "reserve", "grenades", "smokes", "reload"]:
				if not presentation.has(field):
					presentation[field] = 0
			if not presentation.has("inventory"):
				presentation.inventory = []
			var snap := newly_spawned or not actor.visible or discontinuity
			if not _authority and id == local_id:
				# move_and_slide chooses its timestep from the current callback. Replay
				# must run on the fixed physics callback, never the RPC/render callback.
				_pending_reconciliation = {"state": presentation, "epoch": int(data.epoch)}
				if snap:
					actor.apply_snapshot(presentation, 1.0)
			else:
				actor.apply_snapshot(presentation, 1.0 if snap else 0.05)
			if not _authority and id != local_id and not snap:
				# Metadata is current; transforms advance only on the render timeline.
				actor.global_position = previous_position
				actor.yaw = previous_yaw
				actor.pitch = previous_pitch
				actor.rotation.y = previous_yaw
		actor.display_name = state.name
		actor.visible = relevant
		actor.collision_layer = 2 if relevant else 0
		actor.collision_mask = 3 if relevant else 0
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
			# A newly relevant mature cloud must not replay its birth animation.
			if visual.kind == "smoke":
				visual._cloud_elapsed = maxf(0, 12.0 - float(state.get("life", 12.0)))
			visual._detonate()
		# Replica physics is off, so the server's remaining lifetime drives the
		# fade; visuals then thin exactly as the authoritative concealment shrinks.
		if visual._detonated and state.has("life"):
			visual.set_replica_lifetime(float(state.life))
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
	if bool(response.get("ok", false)) and bool(response.get("queued", false)):
		reward_status = "queued_for_delivery"
		_announce("Match rewards queued for delivery; account balance updates after backend confirmation.")
	elif bool(response.get("ok", false)):
		reward_status = "committed"
		_announce("Account match rewards committed by the economy service.")
	else:
		reward_status = "submission_failed"
		_announce("Match complete; account reward submission failed. Server logs identify the match for review.")
		push_warning("Reward submission failed for match " + _match_id + ": " + str(response.get("status", 0)))
	if _peer_actors.is_empty():
		_reset_server_match.call_deferred()

func _expire_reservations() -> void:
	for id: int in _resume_aliases.keys():
		if Time.get_ticks_msec() >= int(_resume_aliases[id].expires):
			_resume_aliases.erase(id)
	for token: String in _reservations.keys():
		var record: Dictionary = _reservations[token]
		if _elapsed >= float(record.expires) and not _peer_actors.values().has(int(record.id)):
			_account_ids.erase(int(record.id))
			_resume_aliases.erase(int(record.id))
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
	_snapshot_generation += 1
	_input_stream = SBInputStream.new()
	_last_input_sequence.clear()
	_gate = SBInputGate.new()
	_bot_state.clear()
	_account_ids.clear()
	for peer_id: int in _pending_joins.keys():
		_reject_join(peer_id, "The server lobby reset; reconnect with a fresh ticket.")
	_pending_joins.clear()
	_join_slots.clear()
	_join_accounts.clear()
	_reservations.clear()
	_resume_aliases.clear()
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
