extends SceneTree
## Server-authoritative weapon, hit-volume and utility integrity (CLAUDE_AUDIT_0.3
## H-1, H-2, M-1, M-2, M-3, M-5, L-5). Every check runs the real authority path.
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const Weapons = preload("res://scripts/gameplay/weapons.gd")
const Utility = preload("res://scripts/gameplay/utility.gd")
const Match = preload("res://scripts/gameplay/match.gd")
const DT := 1.0 / 60.0
var failures: Array[String] = []
var checks := 0
var world: Node3D

func _initialize() -> void:
	_run.call_deferred()

func check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

func _actor(id: int, team: int, at: Vector3, weapon := "") -> SBActor:
	var actor := Actor.new()
	actor.configure(id, team, "integrity-%d" % id, false)
	world.add_child(actor)
	actor.reset_for_round(at)
	if not weapon.is_empty() and weapon != "sidearm":
		actor.credits = 99999
		actor.buy_weapon(weapon)
	actor.ammo = 10000
	return actor

func _settle(actors: Array, ticks := 20, state := {}) -> void:
	for i in range(ticks):
		for actor: SBActor in actors:
			var input: Dictionary = state.duplicate()
			if not input.has("look"):
				input.look = Vector2(actor.yaw, actor.pitch)
			actor.input_state = input
			actor.tick_authority(DT)
		await physics_frame

func _run() -> void:
	world = Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	await physics_frame
	await _fire_rates()
	await _quick_switch()
	await _recoil_pattern()
	await _spread_seed()
	await _hit_volumes()
	await _smoke_placement()
	await _halftime_loadout()
	world.queue_free()
	await process_frame
	print("WEAPON_INTEGRITY_TEST checks=%d failures=%d" % [checks, failures.size()])
	quit(0 if failures.is_empty() else 1)

func _fire_rates() -> void:
	var x := -18.0
	for weapon in Weapons.DATA:
		var actor := _actor(70, 0, Vector3(x, 0.05, -20), weapon)
		x += 3.0
		await _settle([actor], 30)
		var spec: Dictionary = Weapons.get_weapon(weapon)
		var shots: Array[int] = []
		for t in range(1800):
			var before := actor.ammo
			actor.input_state = {"look": Vector2(0, 1.4), "weapon": weapon, "fire": true if spec.automatic else t % 2 == 0}
			actor.tick_authority(DT)
			if actor.ammo < before:
				shots.append(t)
		var mean := float(shots[-1] - shots[0]) * DT / float(shots.size() - 1)
		var designed := float(spec.interval)
		# Semi-automatic weapons need a release tick between presses, so allow one extra tick.
		var tolerance := designed * 0.02 + (0.0 if spec.automatic else DT)
		check(absf(mean - designed) <= tolerance, "%s sustained interval %.4fs matches data %.4fs" % [weapon, mean, designed])
		actor.queue_free()
	await physics_frame

func _quick_switch() -> void:
	var actor := _actor(71, 0, Vector3(0, 0.05, -20), "marksman")
	await physics_frame
	await _settle([actor], 30)
	var fired: Array[int] = []
	var tick := [0]
	var record := func(_id: int, _origin: Vector3, _direction: Vector3) -> void: fired.append(tick[0])
	actor.shot_fired.connect(record)
	for t in range(200):
		tick[0] = t
		var state := {"look": Vector2(0, 1.4), "weapon": "marksman", "fire": t % 2 == 0}
		if fired.size() == 1 and t == fired[0] + 1:
			state = {"look": Vector2(0, 1.4), "weapon": "sidearm"}
		actor.input_state = state
		actor.tick_authority(DT)
		if fired.size() == 2:
			break
	actor.shot_fired.disconnect(record)
	var interval := float(Weapons.get_weapon("marksman").interval)
	check(fired.size() == 2 and float(fired[1] - fired[0]) * DT >= interval - DT * 0.5, "weapon swap cannot shorten the marksman interval (%.3fs)" % (float(fired[1] - fired[0]) * DT if fired.size() == 2 else -1.0))
	# A different, ready weapon is usable after only the deploy delay.
	actor.input_state = {"look": Vector2(0, 1.4), "weapon": "marksman", "fire": false}
	for t in range(80):
		actor.tick_authority(DT)
	var before_ammo := actor.ammo
	actor.input_state = {"look": Vector2(0, 1.4), "weapon": "marksman", "fire": true}
	actor.tick_authority(DT)
	check(actor.ammo == before_ammo - 1, "marksman fires once its own interval has elapsed")
	var switched_at := -1
	var pistol_at := -1
	for t in range(60):
		var state := {"look": Vector2(0, 1.4), "weapon": "sidearm", "fire": t % 2 == 1}
		actor.input_state = state
		var weapon_before := actor.weapon_id
		var pistol_ammo := actor.ammo if actor.weapon_id == "sidearm" else -1
		actor.tick_authority(DT)
		if weapon_before != "sidearm" and actor.weapon_id == "sidearm":
			switched_at = t
		if pistol_ammo >= 0 and actor.ammo < pistol_ammo:
			pistol_at = t
			break
	check(switched_at >= 0 and pistol_at > switched_at and absf(float(pistol_at - switched_at) * DT - Actor.DEPLOY_SECONDS) <= DT * 1.5, "ready sidearm costs only the deploy delay after a marksman shot")
	# Swapping cannot be used to clear accumulated recoil instantly.
	actor.recoil = Vector2(0.01, 0.12)
	actor.input_state = {"look": Vector2(0, 1.4), "weapon": "marksman"}
	actor.tick_authority(DT)
	check(actor.recoil.y > 0.11, "weapon swap keeps recovering recoil instead of zeroing it")
	actor.queue_free()
	await physics_frame

func _recoil_pattern() -> void:
	var actor := _actor(72, 0, Vector3(6, 0.05, -20), "rifle")
	await _settle([actor], 30)
	var bursts: Array = [[], []]
	for burst in range(2):
		var shots := 0
		while shots < 8:
			var before := actor.ammo
			actor.input_state = {"look": Vector2(0, 0), "weapon": "rifle", "fire": true}
			actor.tick_authority(DT)
			if actor.ammo < before:
				shots += 1
				bursts[burst].append(snappedf(actor.recoil.x, 0.00001))
		for t in range(240):
			actor.input_state = {"look": Vector2(0, 0), "weapon": "rifle"}
			actor.tick_authority(DT)
		check(actor.recoil == Vector2.ZERO, "burst %d recoil fully recovers" % burst)
	check(bursts[0] == bursts[1], "a fresh burst after full recovery repeats the learnable recoil pattern")
	actor.queue_free()
	await physics_frame

func _spread_seed() -> void:
	var first := _actor(7, 0, Vector3(-10, 0.05, 18), "rifle")
	var second := _actor(7, 0, Vector3(-6, 0.05, 18), "rifle")
	check(first._rng.seed != 7 * 7919 + 103 and first._rng.seed != second._rng.seed, "authoritative spread is not derived from the public actor id")
	first.queue_free()
	second.queue_free()
	await physics_frame

func _ray(shooter: SBActor, from: Vector3, to: Vector3) -> Dictionary:
	return shooter.trace_shot(from, (to - from).normalized(), from.distance_to(to))

func _hit_volumes() -> void:
	var target := _actor(80, 1, Vector3(0, 0.05, 6))
	var behind := _actor(81, 1, Vector3(0.25, 0.05, 10))
	var shooter := _actor(82, 0, Vector3(0, 0.05, 0), "rifle")
	# Spawn transforms reach the physics server at the next flush; settle afterwards.
	await physics_frame
	await _settle([target, behind, shooter], 20, {"look": Vector2(PI, 0)})
	var feet := target.global_position.y
	# Hit volumes are derived from the rendered head, not hand-tuned constants.
	var head_node: MeshInstance3D = target._head
	var rendered_radii: Vector3 = head_node.scale * 0.5
	var volume: Array = Actor.HEAD_VOLUMES[0]
	check(volume[0].is_equal_approx(head_node.position) and volume[1].is_equal_approx(rendered_radii), "primary head volume matches the rendered head mesh")
	var center := _ray(shooter, Vector3(0, feet + 1.56, 0.5), Vector3(0, feet + 1.56, 12))
	check(center.get("actor") == target and center.get("headshot") == true, "center of rendered head is a headshot")
	var chest := _ray(shooter, Vector3(0, feet + 1.10, 0.5), Vector3(0, feet + 1.10, 12))
	check(chest.get("actor") == target and chest.get("headshot") == false, "chest is a body hit")
	var beside := _ray(shooter, Vector3(0.25, feet + 1.56, 0.5), Vector3(0.25, feet + 1.56, 12))
	check(beside.get("actor") != target, "a ray 0.25 m beside the head does not hit the front operator")
	check(beside.get("actor") == behind and beside.get("headshot") == true, "the ray passes through empty capsule space to the operator behind")
	# Grid coverage: counted head cells should match the visible head and helmet.
	var counted := 0
	var visible := 0
	var outside := 0
	for iy in range(70):
		var y := 0.9 + iy * 0.01
		for ix in range(-40, 41):
			var lateral := ix * 0.01
			var hit := _ray(shooter, Vector3(lateral, feet + y, 0.5), Vector3(lateral, feet + y, 9.0))
			var is_head: bool = hit.get("actor") == target and hit.get("headshot") == true
			var hx := lateral / rendered_radii.x
			var hy := (y - head_node.position.y) / rendered_radii.y
			var kx := lateral / 0.175
			var ky := (y - 1.68) / 0.1175
			var drawn := hx * hx + hy * hy <= 1.0 or kx * kx + ky * ky <= 1.0
			if is_head: counted += 1
			if drawn: visible += 1
			if is_head and not drawn: outside += 1
	check(float(counted) / visible > 0.93 and float(counted) / visible < 1.07 and outside < visible * 0.05, "standing head volume matches drawn head (%d counted / %d drawn, %d outside)" % [counted, visible, outside])
	# Crouch squashes the drawn body; hit volumes follow it.
	await _settle([target], 20, {"look": Vector2(PI, 0), "crouch": true})
	var crouched_head := _ray(shooter, Vector3(0, feet + 1.56 * 0.72, 0.5), Vector3(0, feet + 1.56 * 0.72, 5.9))
	check(crouched_head.get("actor") == target and crouched_head.get("headshot") == true, "crouched drawn head is a headshot")
	var shoulder := _ray(shooter, Vector3(0.0, feet + 0.92, 0.5), Vector3(0.0, feet + 0.92, 5.9))
	check(shoulder.get("actor") == target and shoulder.get("headshot") == false, "crouched shoulder below the drawn head is a body hit")
	# The full authoritative shot path uses the same volumes.
	await _settle([target], 20, {"look": Vector2(PI, 0)})
	await _settle([shooter], 30, {"look": Vector2(PI, 0)})
	var health_before := target.health
	shooter.input_state = {"look": Vector2(PI, 0), "fire": true, "weapon": "rifle"}
	shooter.tick_authority(DT)
	check(not target.alive and target.last_hit_headshot and health_before == 100, "authoritative rifle head hit at six meters is lethal")
	for actor in [target, behind, shooter]:
		actor.queue_free()
	await physics_frame

func _smoke_placement() -> void:
	for case in [["container roof", Vector3(-7, 3.4, -11), 3.1], ["open ground", Vector3(0, 0.6, -2), 0.0]]:
		var smoke := Utility.new()
		smoke.kind = "smoke"
		world.add_child(smoke)
		smoke.global_position = case[1]
		smoke.velocity = Vector3.ZERO
		for t in range(130):
			smoke._physics_process(DT)
			if smoke._detonated:
				break
		var expected: float = case[2] + 1.6
		check(smoke._detonated and absf(smoke.global_position.y - expected) < 0.12, "%s smoke cloud rests %.2f m above its surface (got y=%.2f)" % [case[0], 1.6, smoke.global_position.y])
		smoke.queue_free()
	await physics_frame

func _halftime_loadout() -> void:
	var game := Match.new()
	game.configure({"mode": "offline", "difficulty": "easy"})
	world.add_child(game)
	await physics_frame
	var me: SBActor = game.local_actor()
	me.credits = 5000
	game.phase = "buy"
	game._buy(me.actor_id, "rifle")
	check(me.inventory.has("rifle") and me.weapon_id == "rifle", "rifle purchased before halftime")
	game.round_number = 6
	game._begin_round()
	check(me.inventory == ["sidearm"] and me.weapon_id == "sidearm" and me.credits == 1200, "halftime restores the pistol-round loadout with 1200 funds")
	check(me.ammo == int(Weapons.get_weapon("sidearm").magazine), "halftime sidearm is fully loaded")
	game.queue_free()
	await physics_frame
