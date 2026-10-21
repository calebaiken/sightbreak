class_name SBOfflineDiagnostics
extends RefCounted
## Explicit debug/offline observation only. This never reads commands from files.
## Objective fixtures alter declared initial layout/side/seeds before physics;
## ordinary full-match tracing changes none of those conditions or game rules.
const SAMPLE_SECONDS := 0.2
const MAX_EVENTS := 4096
const FIXTURE_KEY := "_offline_diagnostics"

var directory := ""
var scenario := ""
var fixture_seed := 42
var active := false
var _prepared := false
var _initial_profile: Dictionary = {}
var _started := false
var _finished := false
var _clock := 0.0
var _event_count := 0
var _events_dropped := 0
var _previous: Dictionary = {}
var _completion_calls := 0
var _interact_held := false
var _summary: Dictionary = {}
var _training_after: Dictionary = {}

static func create(args, profile_data: Dictionary):
	if not (args is Array or args is PackedStringArray): return null
	var requested: bool = "--offline-validation" in args
	var destination := ""
	var selected := ""
	var selected_seed := "42"
	for arg in args:
		if str(arg).begins_with("--offline-trace-dir="): destination = str(arg).trim_prefix("--offline-trace-dir=")
		elif str(arg).begins_with("--offline-scenario="): selected = str(arg).trim_prefix("--offline-scenario=")
		elif str(arg).begins_with("--offline-seed="): selected_seed = str(arg).trim_prefix("--offline-seed=")
	if not requested and destination.is_empty() and selected.is_empty(): return null
	if not OS.is_debug_build() or not requested or not destination.is_absolute_path():
		print("OFFLINE_DIAGNOSTICS_REJECTED explicit debug validation and absolute trace directory required")
		return null
	if "--server" in args or "--require-accounts" in args:
		print("OFFLINE_DIAGNOSTICS_REJECTED network server arguments")
		return null
	if selected not in ["", "plant", "defuse"] or not selected_seed.is_valid_int() or int(selected_seed) < 0 or int(selected_seed) > 2147483647:
		print("OFFLINE_DIAGNOSTICS_REJECTED unknown scenario or invalid seed")
		return null
	if profile_data.get("scope", "") != "offline_training":
		print("OFFLINE_DIAGNOSTICS_REJECTED offline training profile required")
		return null
	if not profile_data.get("history", []) is Array:
		print("OFFLINE_DIAGNOSTICS_REJECTED malformed training history")
		return null
	if not selected.is_empty() and (int(profile_data.get("matches", 0)) != 0 or not (profile_data.get("history", []) as Array).is_empty()):
		print("OFFLINE_DIAGNOSTICS_REJECTED objective fixtures require fresh training history")
		return null
	var result := SBOfflineDiagnostics.new()
	result.directory = destination.simplify_path()
	result.scenario = selected
	result.fixture_seed = int(selected_seed)
	result._initial_profile = profile_data.duplicate(true)
	return result

func configure_match(options: Dictionary) -> Dictionary:
	var selected := options.duplicate()
	active = false
	if not OS.is_debug_build() or str(options.get("mode", "offline")) != "offline":
		print("OFFLINE_DIAGNOSTICS_IGNORED mode=", options.get("mode", "offline"))
		return selected
	# Admit the output before fixture_for can change any initial conditions.
	# A reused observer or stale evidence never authorizes a fixture.
	if _started or not _fresh_output():
		print("OFFLINE_DIAGNOSTICS_REJECTED fresh process/output required")
		return selected
	var error := DirAccess.make_dir_recursive_absolute(directory)
	if error != OK:
		print("OFFLINE_DIAGNOSTICS_REJECTED output unavailable: ", error_string(error))
		return selected
	_prepared = true
	active = true
	selected[FIXTURE_KEY] = self
	return selected

func _fresh_output() -> bool:
	for name in ["status.json", "status.json.tmp", "events.jsonl"]:
		if FileAccess.file_exists(directory.path_join(name)): return false
	return not FileAccess.file_exists(directory)

## Called only during match initialization; network options can never authorize it.
## Returning no fixture for trace-only runs preserves normal RNG/spawns/teams.
static func fixture_for(options: Dictionary, arena) -> Dictionary:
	if not OS.is_debug_build() or str(options.get("mode", "offline")) != "offline": return {}
	var observer: Variant = options.get(FIXTURE_KEY)
	if not observer is SBOfflineDiagnostics or not observer.active or not observer._prepared or observer._started or not observer._fresh_output() or observer.scenario not in ["plant", "defuse"]: return {}
	var attackers: Array[Vector3] = arena.attack_spawns.duplicate()
	var defenders: Array[Vector3] = arena.defend_spawns.duplicate()
	# East/back floor positions clear the existing obstacles and retain all actors.
	for index in range(5): defenders[index] = Vector3(13.2 + index * 2.2, 0.05, 20.5)
	if observer.scenario == "plant":
		attackers[0] = Vector3(-15, 0.05, 2)
	else:
		# Keep the other defenders outside normal initial sight range of A.
		# Their stock AI remains active and may engage/rotate once play starts.
		for index in range(5): defenders[index].z = -20.5
		# The first attacker in ordinary insertion order (actor 2 after the side
		# swap) remains the ordinary carrier chosen by _begin_round, not forced.
		attackers[0] = Vector3(-15, 0.05, 10)
		defenders[0] = Vector3(-20, 0.05, 9)
	return {"scenario": observer.scenario, "seed": observer.fixture_seed,
		"attack_spawns": attackers, "defend_spawns": defenders}

func _can_observe(game) -> bool:
	return active and _prepared and OS.is_debug_build() and is_instance_valid(game) and game._authority and str(game.options.get("mode", "offline")) == "offline"

static func _vector(value: Vector3) -> Array:
	return [value.x, value.y, value.z]

func _actor(actor) -> Dictionary:
	return {"id": actor.actor_id, "team": actor.team, "alive": actor.alive,
		"position": _vector(actor.position), "velocity": _vector(actor.velocity),
		"yaw": actor.yaw, "pitch": actor.pitch, "health": actor.health,
		"weapon": actor.weapon_id, "ammo": actor.ammo, "reserve": actor.reserve,
		"reload": actor.reload_remaining, "credits": actor.credits,
		"grenades": actor.grenades, "smokes": actor.smokes,
		"inventory": actor.inventory.duplicate(), "kills": actor.kills,
		"deaths": actor.deaths, "assists": actor.assists}

func _snapshot(game) -> Dictionary:
	var local = game.local_actor()
	var actors: Array = []
	for actor in game.actors.values(): actors.append(_actor(actor))
	var state := {"schema": 1, "scope": "debug_offline_read_only_observation",
		"scenario": scenario if not scenario.is_empty() else "standard",
		"wall_msec": Time.get_ticks_msec(), "elapsed": game._elapsed,
		"drawn_frames": Engine.get_frames_drawn(),
		"simulation_tick": game._simulation_tick, "time_scale": Engine.time_scale,
		"phase": game.phase, "time_left": game.time_left,
		"round_number": game.round_number, "attack_score": game.attack_score,
		"defend_score": game.defend_score, "objective_state": game.objective_state,
		"objective_timer": game.objective_timer, "objective_carrier": game.objective_carrier,
		"objective_position": _vector(game.objective_position),
		"interaction_progress": game.interaction_progress,
		"local_contribution": int(game.objective_contributions.get(game.local_id, 0)),
		"local_actor": _actor(local) if local != null else {}, "actors": actors,
		"completion_calls": _completion_calls, "events_dropped": _events_dropped}
	if local != null:
		state["local_input"] = {"interact": bool(local.input_state.get("interact", false)),
			"fire": bool(local.input_state.get("fire", false)),
			"reload": bool(local.input_state.get("reload", false)),
			"move": [float((local.input_state.get("move", Vector2.ZERO) as Vector2).x), float((local.input_state.get("move", Vector2.ZERO) as Vector2).y)]}
	var controller: Node = game.get_parent()
	if controller != null and controller.has_method("input_capabilities"):
		state["ui"] = {"screen": controller.screen, "paused": controller.paused,
			"status_text": controller.status_label.text if is_instance_valid(controller.status_label) else "",
			"scoreboard_visible": is_instance_valid(controller.score_panel) and controller.score_panel.is_visible_in_tree(),
			"focused": controller.application_focused, "touch_controls": controller.uses_touch_controls(),
			"capabilities": controller.input_capabilities(), "mouse_mode": Input.mouse_mode,
			"window_mode": DisplayServer.window_get_mode(),
			"window_size": [DisplayServer.window_get_size().x, DisplayServer.window_get_size().y]}
	if not _summary.is_empty():
		state["summary"] = _summary
		state["training_after"] = _training_after
	return state

func _event(kind: String, data: Dictionary, terminal := false) -> void:
	if _event_count >= MAX_EVENTS + 2:
		_events_dropped += 1
		return
	if _event_count >= MAX_EVENTS and not terminal:
		_events_dropped += 1
		return
	var record := data.duplicate(true)
	record["event"] = kind
	record["event_index"] = _event_count
	record["observer_wall_msec"] = Time.get_ticks_msec()
	var path := directory.path_join("events.jsonl")
	var file := FileAccess.open(path, FileAccess.READ_WRITE if FileAccess.file_exists(path) else FileAccess.WRITE)
	if file == null:
		push_error("Offline diagnostics cannot append event: " + error_string(FileAccess.get_open_error()))
		active = false
		return
	file.seek_end()
	file.store_line(JSON.stringify(record))
	file.close()
	_event_count += 1

func _status(state: Dictionary) -> void:
	var path := directory.path_join("status.json")
	var file := FileAccess.open(path + ".tmp", FileAccess.WRITE)
	if file == null:
		push_error("Offline diagnostics cannot write status: " + error_string(FileAccess.get_open_error()))
		active = false
		return
	file.store_string(JSON.stringify(state))
	file.close()
	var error := DirAccess.rename_absolute(path + ".tmp", path)
	if error != OK:
		push_error("Offline diagnostics cannot commit status: " + error_string(error))
		active = false

func begin_match(game) -> void:
	if not _can_observe(game): return
	if _started:
		push_error("Offline diagnostics requires a fresh process/output for each match")
		active = false
		return
	for name in ["status.json", "status.json.tmp", "events.jsonl"]:
		if FileAccess.file_exists(directory.path_join(name)):
			push_error("Offline diagnostics refuses existing evidence: " + name)
			active = false
			return
	var error := DirAccess.make_dir_recursive_absolute(directory)
	if error != OK:
		push_error("Offline diagnostics cannot create output: " + error_string(error))
		active = false
		return
	_started = true
	var initial := _snapshot(game)
	initial["initial_profile"] = _initial_profile
	initial["initial_conditions"] = "stock_spawns_teams_random_seeds" if scenario.is_empty() else "declared_initial_spawns_side_and_seeds_only"
	initial["match_seed"] = str(game._rng.seed)
	var spread_seeds := {}
	for actor in game.actors.values(): spread_seeds[str(actor.actor_id)] = str(actor._rng.seed)
	initial["actor_spread_seeds"] = spread_seeds
	initial["difficulty"] = str(game.options.get("difficulty", "normal"))
	initial["rules"] = {"buy_seconds": game.BUY_SECONDS, "round_seconds": game.ROUND_SECONDS,
		"device_seconds": game.DEVICE_SECONDS, "plant_seconds": game.PLANT_SECONDS,
		"defuse_seconds": game.DEFUSE_SECONDS, "win_score": game.WIN_SCORE}
	initial["protocol"] = game.PROTOCOL_VERSION
	initial["prediction_enabled"] = game._prediction_enabled
	_event("initial", initial)
	_status(initial)
	_previous = _snapshot(game)
	var local = game.local_actor()
	if local != null:
		local.shot_fired.connect(func(_id, _origin, _direction):
			if _can_observe(game): _event("local_shot", _snapshot(game)))
	game.notification.connect(func(message):
		if _can_observe(game): _event("notification", {"message": message, "elapsed": game._elapsed, "simulation_tick": game._simulation_tick}))

func observe(game, delta: float) -> void:
	if not _started or not _can_observe(game): return
	if _finished:
		# Preserve the final result while still observing rendered UI/frame
		# freshness. This neither processes input nor emits another completion.
		_clock += delta
		if _clock >= SAMPLE_SECONDS:
			_clock = 0.0
			_status(_snapshot(game))
		return
	# Observe edges every physics tick, independently of normalized progress and
	# the five-Hz status sampler. Main calls this before consuming the next input,
	# so an edge is timestamped one tick after its first authoritative use.
	var input_actor = game.local_actor()
	var held: bool = input_actor != null and bool(input_actor.input_state.get("interact", false))
	if held != _interact_held:
		_interact_held = held
		_event("local_interact_input", {"held": held, "elapsed": game._elapsed,
			"simulation_tick": game._simulation_tick, "round_number": game.round_number,
			"interaction_progress": game.interaction_progress})
	_clock += delta
	if _clock < SAMPLE_SECONDS: return
	_clock = 0.0
	var state := _snapshot(game)
	for key in ["phase", "round_number", "objective_state", "local_contribution"]:
		if state.get(key) != _previous.get(key): _event(key, state)
	var local: Dictionary = state.local_actor
	var prior: Dictionary = _previous.local_actor
	if not local.is_empty() and not prior.is_empty():
		if bool(float(local.reload) > 0) != bool(float(prior.reload) > 0): _event("reload", state)
		if local.weapon != prior.weapon: _event("weapon", state)
		if local.alive != prior.alive: _event("alive", state)
		if local.grenades != prior.grenades or local.smokes != prior.smokes: _event("utility", state)
	_status(state)
	_previous = state

func completed(game, summary: Dictionary, profile_data: Dictionary) -> void:
	if not _started or not _can_observe(game): return
	if game.phase != "match_over" or not game._finished_emitted or profile_data.get("scope", "") != "offline_training":
		print("OFFLINE_DIAGNOSTICS_REJECTED completion without normal offline match result")
		return
	_completion_calls += 1
	_summary = summary.duplicate(true)
	_training_after = profile_data.duplicate(true)
	var state := _snapshot(game)
	_event("completed" if _completion_calls == 1 else "duplicate_completion", state, true)
	_status(state)
	_finished = true

func finish() -> void:
	active = false
