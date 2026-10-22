extends SceneTree
## Bounded all-bot observation, informed by Claude PR28 bot_objective_metrics.gd.
## No authority-order override. --swap-start is an artificial initial condition.
## Time scale 4 changes physics delta; this is not native human gameplay or progression.
var m: TacticalMatch
var seed_value := 71
var swap_start := false
var rounds: Array = []
var current: Dictionary = {}
var reports := 0
var done := false
var started_ms := 0

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--seed="): seed_value = int(argument.trim_prefix("--seed="))
		elif argument == "--swap-start": swap_start = true
	_start.call_deferred()

func _start() -> void:
	m = TacticalMatch.new()
	m.configure({"mode": "offline", "difficulty": "normal"})
	root.add_child(m)
	m.local_id = 0
	m._rng.seed = seed_value
	for actor: SBActor in m.actors.values():
		actor._rng.seed = seed_value * 1000 + actor.actor_id
		if swap_start: actor.team = 1 - actor.team
	# Both start conditions repeat identical stock round-one setup after seeding.
	# No round timer, objective, authority policy, or insertion order is overridden.
	m.round_number = 0
	m._begin_round()
	m.notification.connect(_on_notification)
	m.match_finished.connect(func(_result: Dictionary) -> void: reports += 1)
	started_ms = Time.get_ticks_msec()
	Engine.time_scale = 4.0
	print("BOT_SQUAD_OBSERVATION_START " + JSON.stringify({"seed": seed_value, "swap_start": swap_start, "difficulty": "normal", "time_scale": 4, "protocol": m.PROTOCOL_VERSION, "authority": "stock_phased", "actor_order": m.actors.keys()}))

func _process(_delta: float) -> bool:
	if m == null or done: return false
	if m.phase == "live":
		if current.is_empty(): current = {"round": m.round_number, "planted": false, "sampled_live_seconds": 0.0}
		current.planted = current.planted or m.objective_state == "planted"
		current.sampled_live_seconds = m.ROUND_SECONDS - m.time_left
	if m.phase == "match_over" or m._elapsed > 2400:
		done = true
		_finish.call_deferred()
	return false

func _on_notification(message: String) -> void:
	if not (message.begins_with("Attackers win") or message.begins_with("Defenders win")): return
	var winner := 0 if message.begins_with("Attackers") else 1
	var winner_ids: Array = []
	for actor: SBActor in m.actors.values():
		if actor.team == winner: winner_ids.append(actor.actor_id)
	current["round"] = m.round_number
	current["winner_ids"] = winner_ids
	current["winner_role"] = winner
	current["planted"] = bool(current.get("planted", false)) or m.objective_state == "planted"
	current["reason"] = message
	rounds.append(current.duplicate())
	print("BOT_SQUAD_OBSERVATION_ROUND " + JSON.stringify(current))
	current = {}

func _finish() -> void:
	Engine.time_scale = 1.0
	var kills := 0
	for actor: SBActor in m.actors.values(): kills += actor.kills
	var valid := m.phase == "match_over" and reports == 1 and rounds.size() == m.round_number and m._ranked_payload().is_empty()
	print("BOT_SQUAD_OBSERVATION_MATCH " + JSON.stringify({"seed": seed_value, "swap_start": swap_start, "difficulty": "normal", "time_scale": 4, "rounds": rounds.size(), "kills": kills, "sim_seconds": m._elapsed, "wall_seconds": (Time.get_ticks_msec() - started_ms) / 1000.0, "phase": m.phase, "reports": reports, "ranked_payload_empty": m._ranked_payload().is_empty(), "valid": valid}))
	m.queue_free()
	await process_frame
	await create_timer(0.6).timeout
	quit(0 if valid else 1)
