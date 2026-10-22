extends SceneTree
## Real-engine order oracle. --observe retains the intentionally failing baseline.
## --benchmark records same-host CPU samples; never device or input latency.
const DT := 1.0 / 60.0
class FixtureMatch extends TacticalMatch:
	func _ready() -> void:
		pass

var match_node: FixtureMatch
var checks := 0
var failures: Array[String] = []
var observe := false
var shots: Array = []
var eliminations: Array = []
var duel_references: Dictionary = {}
var duel_reference_poses: Dictionary = {}
var damage_events := 0

func _initialize() -> void:
	observe = OS.get_cmdline_user_args().has("--observe")
	_run.call_deferred()

func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures.append(message)
		if not observe: push_error(message)

func _run() -> void:
	print("AUTHORITY_ORDER engine=%s observe=%s" % [Engine.get_version_info().string, observe])
	match_node = FixtureMatch.new()
	match_node.configure({"mode": "offline"})
	root.add_child(match_node)
	match_node.set_physics_process(false)
	match_node.local_id = 0
	match_node.phase = "live"
	match_node.objective_state = "none"
	match_node.objective_carrier = 0
	var floor_body := StaticBody3D.new()
	var floor_collision := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(200, 0.2, 200)
	floor_collision.shape = box
	floor_body.add_child(floor_collision)
	match_node.add_child(floor_body)
	floor_body.position.y = -0.1
	for id in range(1, 11):
		var actor := match_node._spawn_actor(id, 0 if id <= 5 else 1, "order-%d" % id)
		actor.shot_fired.connect(func(source: int, _at: Vector3, _dir: Vector3) -> void: shots.append(source))
		actor.damage_taken.connect(func(_victim: int, _attacker: int, _amount: float) -> void: damage_events += 1)
		actor.eliminated.connect(func(victim: int, killer: int) -> void: eliminations.append([victim, killer]))
		match_node._peer_actors[100 + id] = id
		match_node._last_peer_input[id] = 0.0
	await physics_frame
	if OS.get_cmdline_user_args().has("--benchmark-only"):
		await _benchmark()
		await create_timer(0.6).timeout
		match_node.queue_free()
		await process_frame
		print("AUTHORITY_ORDER_BENCHMARK checks=%d failures=%d" % [checks, failures.size()])
		quit(0 if failures.is_empty() else 1)
		return
	for seed_value in range(8):
		for mirror in [false, true]:
			for reverse in [false, true]:
				await _duel(seed_value, mirror, reverse)
	for reverse in [false, true]:
		await _moving_target(reverse)
		await _stance_target(reverse)
		await _shielding(reverse)
		await _dead_before_tick(reverse)
		await _nonlethal(reverse)
	if OS.get_cmdline_user_args().has("--benchmark"):
		await _benchmark()
	await create_timer(0.6).timeout
	match_node.queue_free()
	await process_frame
	print("AUTHORITY_ORDER checks=%d failures=%d mode=%s" % [checks, failures.size(), "observation" if observe else "assertion"])
	quit(0 if observe or failures.is_empty() else 1)

func _prepare(seed_value: int, reverse: bool) -> void:
	var ordered: Dictionary = {}
	for offset in range(10):
		var id := 10 - offset if reverse else offset + 1
		ordered[id] = match_node.actors[id]
	match_node.actors = ordered
	match_node.phase = "live"
	match_node.time_left = 1000000
	match_node._bot_clock = 1000000
	match_node._damage_history.clear()
	for id in range(1, 11):
		var actor: SBActor = match_node.actors[id]
		actor.reset_for_round(Vector3(10 + id * 5, 0.01, 0))
		actor.inventory.assign(["sidearm", "rifle"])
		actor._equip("rifle")
		actor._deploy_remaining = 0
		actor._rng.seed = seed_value
		actor.input_state = {"look": Vector2.ZERO}
		actor.kills = 0
		actor.assists = 0
		actor.deaths = 0
		actor.credits = 800
	shots.clear()
	eliminations.clear()

func _settle() -> void:
	await physics_frame
	await physics_frame # Teleported shapes must reach PhysicsServer before move_and_slide.
	for tick in range(8):
		for actor: SBActor in match_node.actors.values():
			actor.tick_authority(DT)
		await physics_frame
	shots.clear()
	eliminations.clear()

func _state(actor: SBActor) -> Dictionary:
	return {"alive": actor.alive, "health": actor.health, "ammo": actor.ammo, "kills": actor.kills, "deaths": actor.deaths, "credits": actor.credits, "position": [actor.position.x, actor.position.y, actor.position.z]}

func _duel(seed_value: int, mirror: bool, reverse: bool) -> void:
	await process_frame # Flush prior death collision-disable before resetting this fixture.
	_prepare(seed_value, reverse)
	var a: SBActor = match_node.actors[1]
	var b: SBActor = match_node.actors[6]
	var sign_value := -1.0 if mirror else 1.0
	a.position = Vector3(0, 0.01, -3 * sign_value)
	b.position = Vector3(0, 0.01, 3 * sign_value)
	a.input_state = {"look": Vector2(PI if not mirror else 0.0, 0)}
	b.input_state = {"look": Vector2(0.0 if not mirror else PI, 0)}
	await _settle()
	a.input_state.fire = true
	b.input_state.fire = true
	match_node._authority_tick(DT)
	var label := "duel seed=%d mirror=%s reverse=%s" % [seed_value, mirror, reverse]
	print("CASE " + JSON.stringify({"kind": "duel", "seed": seed_value, "mirror": mirror, "reverse": reverse, "a": _state(a), "b": _state(b), "shots": shots.duplicate(), "eliminations": eliminations.duplicate()}))
	var equivalent := [a.health, b.health, a.ammo, b.ammo, a.kills, b.kills, a.deaths, b.deaths, shots.size(), eliminations.size()]
	var key := "%d/%s" % [seed_value, mirror]
	if reverse:
		check(equivalent == duel_references[key], label + " agrees with original insertion order")
		var poses: Array = duel_reference_poses[key]
		check(a.position.distance_to(poses[0]) <= 0.0001 and b.position.distance_to(poses[1]) <= 0.0001, label + " poses agree within 0.1 mm physics settling tolerance")
	else:
		duel_references[key] = equivalent
		duel_reference_poses[key] = [a.position, b.position]
	check(not a.alive and not b.alive, label + " accepts both lethal shots")
	check(a.ammo == 29 and b.ammo == 29 and shots.size() == 2, label + " consumes each eligible shot once")
	check(eliminations.size() == 2 and a.deaths == 1 and b.deaths == 1 and a.kills == 1 and b.kills == 1 and a.credits == 1100 and b.credits == 1100, label + " records each death and reward once")
	match_node._authority_tick(DT)
	check(shots.size() == 2 and eliminations.size() == 2 and a.ammo == 29 and b.ammo == 29, label + " dead actors do not fire next tick")

func _moving_target(reverse: bool) -> void:
	await process_frame
	_prepare(91, reverse)
	var a: SBActor = match_node.actors[1]
	var b: SBActor = match_node.actors[6]
	a.position = Vector3(0, 0.01, 0)
	b.position = Vector3(0.12, 0.01, -6)
	a.input_state = {"look": Vector2.ZERO}
	b.input_state = {"look": Vector2.ZERO}
	await _settle()
	b.velocity.x = SBMovementStep.WALK_SPEED
	b.input_state.move = Vector2(1, 0)
	a.input_state.fire = true
	match_node._authority_tick(DT)
	print("CASE " + JSON.stringify({"kind": "moving", "reverse": reverse, "a": _state(a), "b": _state(b), "shots": shots.duplicate(), "eliminations": eliminations.duplicate()}))
	check(b.alive and b.health == 100 and b.position.x > 0.20, "moving target uses post-movement pose reverse=%s" % reverse)

func _stance_target(reverse: bool) -> void:
	await process_frame
	_prepare(91, reverse)
	var a: SBActor = match_node.actors[1]
	var b: SBActor = match_node.actors[6]
	a.position = Vector3(0, 0.01, 0)
	b.position = Vector3(0, 0.01, -6)
	a.input_state = {"look": Vector2.ZERO}
	b.input_state = {"look": Vector2.ZERO}
	await _settle()
	b.input_state.crouch = true
	a.input_state.fire = true
	match_node._authority_tick(DT)
	print("CASE " + JSON.stringify({"kind": "stance", "reverse": reverse, "a": _state(a), "b": _state(b), "head_height": b.head_height}))
	check(b.alive and b.health == 100 and is_equal_approx(b.head_height, 1.13), "stance target uses post-movement crouch reverse=%s" % reverse)

func _shielding(reverse: bool) -> void:
	await process_frame
	_prepare(101, reverse)
	var a: SBActor = match_node.actors[1]
	var b: SBActor = match_node.actors[2]
	var front: SBActor = match_node.actors[6]
	var behind: SBActor = match_node.actors[7]
	a.position = Vector3(-0.4, 0.01, 0)
	b.position = Vector3(0.4, 0.01, 0)
	front.position = Vector3(0, 0.01, -4)
	behind.position = Vector3(0, 0.01, -4.8)
	a.input_state = {"look": Vector2(-atan(0.1), 0)}
	b.input_state = {"look": Vector2(atan(0.1), 0)}
	await _settle()
	a.input_state.fire = true
	b.input_state.fire = true
	match_node._authority_tick(DT)
	print("CASE " + JSON.stringify({"kind": "shield", "reverse": reverse, "front": _state(front), "behind": _state(behind), "a": _state(a), "b": _state(b), "shots": shots.duplicate(), "eliminations": eliminations.duplicate()}))
	check(not front.alive and behind.alive and behind.health == 100, "front living volume shields every same-tick ray reverse=%s" % reverse)
	check(a.ammo == 29 and b.ammo == 29 and shots.size() == 2 and eliminations.size() == 1, "shield batch has two shots and one elimination reverse=%s" % reverse)
	check(a.kills + b.kills == 1 and a.credits + b.credits == 1900 and front.deaths == 1 and behind.deaths == 0, "duplicate contacts cannot duplicate rewards reverse=%s" % reverse)

func _dead_before_tick(reverse: bool) -> void:
	await process_frame
	_prepare(17, reverse)
	await _settle()
	var b: SBActor = match_node.actors[6]
	b.apply_damage(200, 1)
	b.input_state = {"fire": true, "grenade": true, "smoke": true}
	var credits_before: int = match_node.actors[1].credits
	match_node._authority_tick(DT)
	check(shots.is_empty() and eliminations.size() == 1 and b.ammo == 30 and b.grenades == 1 and b.smokes == 1, "dead-before-tick actor has no actions reverse=%s" % reverse)
	check(b.deaths == 1 and match_node.actors[1].credits == credits_before, "dead-before-tick cannot repeat reward reverse=%s" % reverse)

func _nonlethal(reverse: bool) -> void:
	await process_frame
	_prepare(211, reverse)
	var a: SBActor = match_node.actors[1]
	var b: SBActor = match_node.actors[6]
	a.position = Vector3(0, 0.01, -3)
	b.position = Vector3(0, 0.01, 3)
	a.input_state = {"look": Vector2(PI, 0)}
	b.input_state = {"look": Vector2.ZERO}
	await _settle()
	a.health = 1000
	b.health = 1000
	a.input_state.fire = true
	b.input_state.fire = true
	match_node._authority_tick(DT)
	print("CASE " + JSON.stringify({"kind": "nonlethal", "reverse": reverse, "a": _state(a), "b": _state(b), "shots": shots.duplicate()}))
	check(a.alive and b.alive and a.health < 900 and absf(a.health - b.health) < 0.01, "nonlethal symmetric damage preserves falloff reverse=%s" % reverse)
	match_node._authority_tick(DT)
	check(a.ammo == 29 and b.ammo == 29 and shots.size() == 2, "same-tick batch cannot bypass weapon cooldown reverse=%s" % reverse)

## Performance fixture controls compensate the actual recovered recoil before
## each authority tick. Setup/input generation is excluded from timed tick calls.
func _benchmark_controls(firing: bool) -> void:
	for actor: SBActor in match_node.actors.values():
		var recovered := actor.recoil.move_toward(Vector2.ZERO, DT * 0.11)
		actor.input_state = {"look": Vector2((PI if actor.team == 0 else 0.0) - recovered.x, -recovered.y), "fire": firing}

func _benchmark() -> void:
	await process_frame
	_prepare(712, false)
	for pair in range(5):
		var a: SBActor = match_node.actors[1 + pair]
		var b: SBActor = match_node.actors[6 + pair]
		a.position = Vector3(pair * 4, 0.01, -3)
		b.position = Vector3(pair * 4, 0.01, 3)
		a.input_state = {"look": Vector2(PI, 0)}
		b.input_state = {"look": Vector2.ZERO}
		a.health = 1000000000
		b.health = 1000000000
	await _settle()
	for firing in [false, true]:
		# Benchmark-only supply avoids depletion/reload so active shot/trace/hit
		# cost is measured throughout every sample. Production magazine data stays intact.
		for actor: SBActor in match_node.actors.values():
			actor.ammo = 1000000
			actor.reserve = 1000000
		for tick in range(300):
			_benchmark_controls(firing)
			match_node._authority_tick(DT)
		for sample in range(7):
			var elapsed := 0
			var shots_before := shots.size()
			var damage_before := damage_events
			for tick in range(2000):
				_benchmark_controls(firing)
				var start := Time.get_ticks_usec()
				match_node._authority_tick(DT)
				elapsed += Time.get_ticks_usec() - start
			var shot_count := shots.size() - shots_before
			var hit_count := damage_events - damage_before
			_benchmark_probe(firing, sample, "after_ticks")
			print("CPU " + JSON.stringify({"fire": firing, "sample": sample, "ticks": 2000, "total_usec": elapsed, "usec_per_tick": float(elapsed) / 2000, "shots": shot_count, "damage_events": hit_count, "fixture": "ammo_sufficient_recoil_compensated"}))
			if firing:
				check(shot_count >= 3170 and shot_count <= 3180 and hit_count == shot_count, "active benchmark preserves cadence and every shot exercises damage")
			else:
				check(shot_count == 0 and hit_count == 0, "idle benchmark has no shots or damage")
			# Release deferred presentation/audio work outside the timed samples.
			await process_frame
			await process_frame
			_benchmark_probe(firing, sample, "after_frame_flush")

func _benchmark_probe(firing: bool, sample: int, stage: String) -> void:
	var effects := match_node.get_node_or_null("CombatEffects") as SBCombatEffects
	var pools := {}
	if effects != null:
		for key in effects._pools: pools[key] = effects._pools[key].slots.size()
	print("GROWTH " + JSON.stringify({"fire": firing, "sample": sample, "stage": stage, "objects": Performance.get_monitor(Performance.OBJECT_COUNT), "nodes": Performance.get_monitor(Performance.OBJECT_NODE_COUNT), "resources": Performance.get_monitor(Performance.OBJECT_RESOURCE_COUNT), "static_bytes": Performance.get_monitor(Performance.MEMORY_STATIC), "message_buffer_max": Performance.get_monitor(Performance.MEMORY_MESSAGE_BUFFER_MAX), "recorded_shots": shots.size(), "effect_pool_slots": pools, "audio_nodes": match_node.find_children("*", "AudioStreamPlayer3D", true, false).size()}))
