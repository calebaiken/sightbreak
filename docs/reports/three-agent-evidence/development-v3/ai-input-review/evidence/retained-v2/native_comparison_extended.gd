extends SceneTree

# Both trees use exactly the same harness and actor/match RNG seeds. Godot runs
# real _physics_process, move_and_slide, world raycasts, utilities and combat.
# --fixed-fps 60 advances one fixed real physics step per rendered headless frame.
# Only buy periods are skipped; two naturally resolved rounds are observed.
class MeasuredMatch extends TacticalMatch:
	var sample_count: int = 0
	var decision_us: Array[int] = []
	var engagements: int = 0
	var target_switches: int = 0
	var movement_requests: int = 0
	var movement_stalls: int = 0
	var stuck_ticks: int = 0
	var objective_ticks: int = 0
	var objective_actors: Dictionary = {}
	var previous_positions: Dictionary = {}
	var previous_targets: Dictionary = {}
	var shots: int = 0
	var live_seconds: float = 0.0
	var live_ticks: int = 0
	var round_endings: Array = []
	var plant_count: int = 0
	var defuse_count: int = 0
	var done: bool = false
	var alive_actor_physics_ticks: int = 0
	var inactive_actor_physics_ticks: int = 0
	var plant_attempts: int = 0
	var defuse_attempts: int = 0
	var previous_interactions: Dictionary = {}
	var role_decisions: Dictionary = {}

	func _bot_input(actor: SBActor, delta: float) -> void:
		if phase != "live" or not actor.alive:
			super._bot_input(actor, delta)
			return
		var started: int = Time.get_ticks_usec()
		super._bot_input(actor, delta)
		decision_us.append(Time.get_ticks_usec() - started)
		sample_count += 1
		var state: Dictionary = _bot_state.get(actor.actor_id, {})
		var role: String = str(state.get("role", "unclassified"))
		role_decisions[role] = int(role_decisions.get(role, 0)) + 1
		var target: int = int(state.get("target", 0))
		var previous: int = int(previous_targets.get(actor.actor_id, 0))
		if target != 0:
			engagements += 1
			if previous != 0 and previous != target:
				target_switches += 1
		previous_targets[actor.actor_id] = target
		var move: Vector2 = actor.input_state.get("move", Vector2.ZERO)
		if move.length_squared() > 0.01:
			movement_requests += 1
			if previous_positions.has(actor.actor_id) and actor.position.distance_to(previous_positions[actor.actor_id]) < 0.05:
				movement_stalls += 1
		if float(state.get("stuck", 0.0)) > 0.9:
			stuck_ticks += 1
		previous_positions[actor.actor_id] = actor.position
		if bool(actor.input_state.get("interact", false)):
			objective_ticks += 1
			objective_actors[actor.actor_id] = true

	func _physics_process(delta: float) -> void:
		if done:
			return
		var old_phase: String = phase
		var old_objective: String = objective_state
		if old_phase == "live":
			live_seconds += delta
			live_ticks += 1
			for actor: SBActor in actors.values():
				if not actor.alive:
					continue
				alive_actor_physics_ticks += 1
				var move: Vector2 = actor.input_state.get("move", Vector2.ZERO)
				var target: int = int(_bot_state.get(actor.actor_id, {}).get("target", 0))
				if move.length_squared() <= 0.01 and target == 0 and not bool(actor.input_state.get("interact", false)):
					inactive_actor_physics_ticks += 1
		super._physics_process(delta)
		var active_interactions: Dictionary = {}
		for actor_id: int in _interactions:
			if float(_interactions[actor_id]) <= 0.0:
				continue
			active_interactions[actor_id] = true
			if not previous_interactions.has(actor_id):
				if old_objective == "planted":
					defuse_attempts += 1
				else:
					plant_attempts += 1
		previous_interactions = active_interactions
		if old_objective != "planted" and objective_state == "planted":
			plant_count += 1
		if old_objective != "defused" and objective_state == "defused":
			defuse_count += 1
		if old_phase == "live" and phase != "live":
			round_endings.append({"round": round_number, "score": [attack_score, defend_score], "objective": objective_state, "seconds": snappedf(live_seconds, 0.001)})
			previous_positions.clear()
			previous_targets.clear()
		if round_endings.size() >= 2 or _elapsed > 310.0:
			done = true
			set_physics_process(false)
		if phase == "buy":
			time_left = 0.0

	func report(difficulty: String, seed_value: int) -> Dictionary:
		var total: int = 0
		for value: int in decision_us:
			total += value
		decision_us.sort()
		var kills: int = 0
		for actor: SBActor in actors.values():
			kills += actor.kills
		return {"difficulty": difficulty, "seed": seed_value, "rounds": round_endings,
			"bot_decisions": sample_count, "decision_us_mean": float(total) / max(1, sample_count),
			"decision_us_p95": decision_us[int((decision_us.size() - 1) * 0.95)] if not decision_us.is_empty() else 0,
			"engagement_ticks": engagements, "target_switches": target_switches,
			"movement_requests": movement_requests, "movement_stalls": movement_stalls,
			"stuck_ticks_over_0_9": stuck_ticks, "objective_input_ticks": objective_ticks,
			"objective_actor_count": objective_actors.size(), "plants": plant_count, "defuses": defuse_count,
			"kills": kills, "shots": shots, "live_seconds": live_seconds, "live_physics_ticks": live_ticks,
			"completed": round_endings.size() == 2, "plant_attempts": plant_attempts, "defuse_attempts": defuse_attempts, "inactive_actor_seconds": float(inactive_actor_physics_ticks) / 60.0, "inactive_actor_ratio": float(inactive_actor_physics_ticks) / max(1, alive_actor_physics_ticks), "role_decisions": role_decisions}

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var all_results: Array = []
	for difficulty: String in ["easy", "normal", "hard"]:
		for seed_value: int in [1847, 2026, 3141]:
			var m := MeasuredMatch.new()
			m.configure({"mode": "offline", "difficulty": difficulty})
			root.add_child(m)
			m.local_id = 0
			m._rng.seed = seed_value
			# Reseed and restart the first round after all actors are bots, giving
			# both conditions the same first-round buy and fresh spawn state.
			m.round_number = 0
			m._begin_round()
			for actor: SBActor in m.actors.values():
				actor._rng.seed = seed_value * 100 + actor.actor_id
				actor.shot_fired.connect(func(_id: int, _pos: Vector3, _dir: Vector3) -> void: m.shots += 1)
			m.time_left = 0.0
			while not m.done:
				await physics_frame
			var result: Dictionary = m.report(difficulty, seed_value)
			all_results.append(result)
			print("AI_NATIVE_COMPARISON ", JSON.stringify(result))
			m.queue_free()
			await process_frame
			await process_frame
	print("AI_NATIVE_COMPARISON_COMPLETE conditions=", all_results.size())
	quit(0)
