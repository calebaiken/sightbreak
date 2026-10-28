extends SceneTree
## Evidence tool, not part of the maintained suite: one seeded all-bot offline match on the real engine, accelerated at
## faithful 1/60 s steps, with per-tick invariants. It only observes: it changes no game state and forces no outcome.
##
## Engine.time_scale also scales the physics delta, so the tick rate is raised by the same factor: each step is still
## 1/60 s of game time and only more of them run per second. Matches are deterministic for a seed on one build.
##
## Checks every physics step: finite positions, nothing below the floor or outside the arena, health/ammo/credit ranges,
## alive/dead consistency, equipped weapon owned, phase softlocks (buy 16.5 s, live 146 s, post 6.5 s) and that the match
## ends within 760 s on a legal score. Once a second it flags a living bot with no target that has not moved 0.6 m in
## about 8 s while 3.5 m or more from its destination ("stuck"; the detector is a heuristic, see the report).
## Per round it records the closest an attacker came to a site, when a site was first reached, when the device was
## planted or dropped, the round length and how many were alive at the end.
##
## usage: godot --headless --audio-driver Dummy --script <this file> -- --seed=N --difficulty=easy|normal|hard --timescale=5
## Prints one FUZZ_RESULT line of JSON.
const STEP := 1.0 / 60.0
const PHASE_LIMIT := {"buy": 16.5, "live": 146.0, "post": 6.5}
const MAX_SIM := 760.0
var m: TacticalMatch
var seed_value := 1
var difficulty := "normal"
var ts := 5.0
var sim := 0.0
var tick := 0
var violations: Array = []
var viol_keys := {}
var phase_name := ""
var phase_since := 0.0
var round_seen := 0
var round_reasons: Array = []
var rounds: Array = []
var rd := {}
var stuck_events: Array = []
var pos_hist := {}
var bounds := {"minx": 1e9, "maxx": -1e9, "minz": 1e9, "maxz": -1e9, "miny": 1e9, "maxy": -1e9}
var done := false

func _initialize() -> void:
	call_deferred("_start")

func _start() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--seed="): seed_value = int(a.trim_prefix("--seed="))
		elif a.begins_with("--difficulty="): difficulty = a.trim_prefix("--difficulty=")
		elif a.begins_with("--timescale="): ts = float(a.trim_prefix("--timescale="))
	m = TacticalMatch.new()
	m.configure({"mode": "offline", "difficulty": difficulty})
	root.add_child(m)
	m.local_id = 0
	m._rng.seed = seed_value
	for actor: SBActor in m.actors.values():
		actor._rng.seed = seed_value * 97 + actor.actor_id
	m.notification.connect(func(text: String) -> void:
		if " win • " in text: round_reasons.append(text))
	Engine.max_physics_steps_per_frame = 64
	Engine.physics_ticks_per_second = int(60.0 * ts)
	Engine.time_scale = ts
	physics_frame.connect(_on_physics)

func _violate(kind: String, detail: String) -> void:
	var key := kind + ":" + detail.left(60)
	if viol_keys.has(key): return
	viol_keys[key] = true
	if violations.size() < 40:
		violations.append({"t": snappedf(sim, 0.01), "round": m.round_number, "kind": kind, "detail": detail})

func _new_round_record() -> Dictionary:
	return {"round": m.round_number, "live_start": -1.0, "plant_t": -1.0, "site_reached_t": -1.0, "min_site_dist": 1e9,
		"first_kill_t": -1.0, "carrier_died_t": -1.0, "end_t": -1.0, "end_phase": "", "kills": 0, "attackers_alive_end": -1, "defenders_alive_end": -1}

func _finalize_round() -> void:
	if rd.is_empty() or rd.live_start < 0.0: return
	var a := 0
	var d := 0
	var kills := 0
	for actor: SBActor in m.actors.values():
		if actor.alive:
			if actor.team == 0: a += 1
			else: d += 1
	rd.attackers_alive_end = a
	rd.defenders_alive_end = d
	rd.end_t = snappedf(sim - rd.live_start, 0.1)
	rounds.append(rd.duplicate())
	rd = {}

func _on_physics() -> void:
	if done or m == null: return
	tick += 1
	sim += STEP
	if m.round_number != round_seen:
		rd = _new_round_record()
		round_seen = m.round_number
	if m.phase != phase_name:
		if phase_name == "live" and (m.phase == "post" or m.phase == "match_over"): _finalize_round()
		phase_name = m.phase
		phase_since = sim
		if m.phase == "live" and not rd.is_empty() and rd.live_start < 0.0: rd.live_start = sim
	elif PHASE_LIMIT.has(m.phase) and sim - phase_since > float(PHASE_LIMIT[m.phase]):
		_violate("SOFTLOCK", "phase=%s round=%d exceeded %.1fs" % [m.phase, m.round_number, PHASE_LIMIT[m.phase]])
	var live_t: float = sim - float(rd.get("live_start", sim))
	if m.phase == "live" and not rd.is_empty():
		if m.objective_state == "planted" and rd.plant_t < 0.0: rd.plant_t = snappedf(live_t, 0.1)
		if m.objective_state == "dropped" and rd.carrier_died_t < 0.0: rd.carrier_died_t = snappedf(live_t, 0.1)
	for actor: SBActor in m.actors.values():
		var p: Vector3 = actor.global_position
		if not (is_finite(p.x) and is_finite(p.y) and is_finite(p.z)) or not is_finite(actor.velocity.length()):
			_violate("NONFINITE_POS", "actor %d" % actor.actor_id)
			continue
		bounds.minx = minf(bounds.minx, p.x); bounds.maxx = maxf(bounds.maxx, p.x)
		bounds.minz = minf(bounds.minz, p.z); bounds.maxz = maxf(bounds.maxz, p.z)
		bounds.miny = minf(bounds.miny, p.y); bounds.maxy = maxf(bounds.maxy, p.y)
		if p.y < -1.5: _violate("FELL_THROUGH_FLOOR", "actor %d y=%.2f" % [actor.actor_id, p.y])
		if absf(p.x) > 60.0 or absf(p.z) > 60.0: _violate("OUT_OF_ARENA", "actor %d at %s" % [actor.actor_id, str(p)])
		if actor.health < 0.0 or actor.health > 100.0: _violate("HEALTH_RANGE", "actor %d hp=%.1f" % [actor.actor_id, actor.health])
		if actor.ammo < 0 or actor.reserve < 0: _violate("AMMO_NEGATIVE", "actor %d %d/%d" % [actor.actor_id, actor.ammo, actor.reserve])
		if actor.credits < 0 or actor.credits > 9000: _violate("CREDITS_RANGE", "actor %d cr=%d" % [actor.actor_id, actor.credits])
		if actor.alive and actor.health <= 0.0: _violate("ALIVE_AT_ZERO_HP", "actor %d" % actor.actor_id)
		if not actor.alive and actor.health > 0.0: _violate("DEAD_WITH_HP", "actor %d hp=%.1f" % [actor.actor_id, actor.health])
		if not actor.inventory.has(actor.weapon_id): _violate("WEAPON_NOT_IN_INVENTORY", "actor %d %s %s" % [actor.actor_id, actor.weapon_id, str(actor.inventory)])
		if m.phase == "live" and actor.alive and actor.team == 0 and not rd.is_empty():
			for s: Vector3 in m.arena.sites:
				rd.min_site_dist = minf(rd.min_site_dist, Vector2(p.x - s.x, p.z - s.z).length())
			if rd.site_reached_t < 0.0 and m.arena.is_at_site(p) >= 0: rd.site_reached_t = snappedf(live_t, 0.1)
	if tick % 60 == 0 and m.phase == "live":
		_sample_bots()
	if m.phase == "match_over":
		_finish("match_over")
	elif sim > MAX_SIM:
		_violate("NO_TERMINATION", "match not over after %.0fs round=%d score=%d:%d" % [sim, m.round_number, m.attack_score, m.defend_score])
		_finish("timeout")

func _sample_bots() -> void:
	var profile := SBBotAI.profile_for(difficulty)
	for actor: SBActor in m.actors.values():
		if not actor.alive: continue
		var hist: Array = pos_hist.get(actor.actor_id, [])
		hist.append([sim, actor.global_position, m.round_number])
		while hist.size() > 0 and (sim - float(hist[0][0]) > 8.5 or int(hist[0][2]) != m.round_number): hist.pop_front()
		pos_hist[actor.actor_id] = hist
		if hist.size() < 8: continue
		var moved: float = (hist[-1][1] as Vector3).distance_to(hist[0][1])
		var state: Dictionary = m._bot_state.get(actor.actor_id, {})
		if moved >= 0.6 or int(state.get("target", 0)) != 0: continue
		var plan: Dictionary = SBBotAI._select_objective_and_destination(m, actor, state, profile)
		var dest: Vector3 = plan.destination
		var gap := actor.global_position.distance_to(dest)
		if gap > 3.5 and not bool(plan.interact):
			var near := 0
			var neighbours: Array = []
			for other: SBActor in m.actors.values():
				if other != actor and other.alive and other.global_position.distance_to(actor.global_position) < 2.5:
					if other.global_position.distance_to(actor.global_position) < 1.2: near += 1
					var ost: Dictionary = m._bot_state.get(other.actor_id, {})
					neighbours.append({"id": other.actor_id, "team": other.team, "role": str(ost.get("role", "")), "pos": other.global_position.snapped(Vector3.ONE * 0.1), "move": str((other.input_state.get("move", Vector2.ZERO) as Vector2).snapped(Vector2.ONE * 0.1)), "vel": snappedf(other.velocity.length(), 0.01), "target": int(ost.get("target", 0))})
			var cmd: Dictionary = actor.input_state
			stuck_events.append({"t": snappedf(sim, 0.1), "round": m.round_number, "id": actor.actor_id, "team": actor.team, "role": str(state.get("role", "")), "pos": actor.global_position.snapped(Vector3.ONE * 0.1), "dest": dest.snapped(Vector3.ONE * 0.1), "gap": snappedf(gap, 0.1),
				"move": str((cmd.get("move", Vector2.ZERO) as Vector2).snapped(Vector2.ONE * 0.1)), "fire": bool(cmd.get("fire", false)), "interact": bool(cmd.get("interact", false)), "reload": bool(cmd.get("reload", false)), "reloading": snappedf(actor.reload_remaining, 0.1),
				"vel": snappedf(actor.velocity.length(), 0.01), "near_actors": near, "obj": m.objective_state, "weapon": actor.weapon_id, "ammo": "%d/%d" % [actor.ammo, actor.reserve], "neighbours": neighbours, "stuck_timer": snappedf(float(state.get("stuck", 0.0)), 0.1), "mem_age": snappedf(m._elapsed - float(state.get("seen_at", -100.0)), 0.1)})
			pos_hist[actor.actor_id] = []

func _finish(reason: String) -> void:
	done = true
	_finalize_round()
	var kills := 0
	var deaths := 0
	for actor: SBActor in m.actors.values():
		kills += actor.kills
		deaths += actor.deaths
	var ended_ok: bool = m.phase != "match_over" or maxi(m.attack_score, m.defend_score) >= 7 or m.round_number >= 12
	if not ended_ok: _violate("BAD_MATCH_END", "score=%d:%d round=%d" % [m.attack_score, m.defend_score, m.round_number])
	var unique_stuck := {}
	for e in stuck_events: unique_stuck["%d@%s" % [e.id, str(e.pos)]] = e
	var planted := 0
	for r in rounds: if r.plant_t >= 0.0: planted += 1
	var result := {
		"seed": seed_value, "difficulty": difficulty, "end": reason, "sim_seconds": snappedf(sim, 0.1), "rounds_played": m.round_number,
		"score_attack_defend": [m.attack_score, m.defend_score], "kills": kills, "deaths": deaths, "planted_rounds": planted,
		"reasons": round_reasons, "per_round": rounds, "violations": violations, "stuck_events": stuck_events.size(), "stuck_unique": unique_stuck.size(),
		"stuck_sample": stuck_events.slice(0, 10), "bounds": bounds,
	}
	print("FUZZ_RESULT ", JSON.stringify(result))
	Engine.time_scale = 1.0
	m.queue_free()
	_quit.call_deferred()

func _quit() -> void:
	await create_timer(0.3).timeout
	quit(0)
