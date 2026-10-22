extends SceneTree
## Actual authority-action measurements. No physical latency or feel claim.
const Actor = preload("res://scripts/gameplay/actor.gd")
const Weapons = preload("res://scripts/gameplay/weapons.gd")
const DT := 1.0 / 60.0
var checks := 0
var failures: Array[String] = []
var world: Node3D
var shooter: SBActor
var target: SBActor
var shots: Array[Dictionary] = []
var confirmations: Array[Dictionary] = []
var damages: Array[float] = []
var impacts: Array[Vector3] = []
var tick := 0

func _initialize() -> void:
	_run.call_deferred()

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures.append(message)
		push_error(message)

func record(kind: String, weapon: String, values: Dictionary) -> void:
	values.kind = kind
	values.weapon = weapon
	print("GUNPLAY_CASE " + JSON.stringify(values))

func _run() -> void:
	print("GUNPLAY_SOURCE " + JSON.stringify({"engine": Engine.get_version_info().string, "physics_hz": Engine.physics_ticks_per_second, "fixture": "real_actor_actions_real_rays"}))
	check(Engine.physics_ticks_per_second == 60, "probe uses the production 60 Hz step")
	world = Node3D.new()
	root.add_child(world)
	var floor_body := StaticBody3D.new()
	var collision := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(240, 0.2, 240)
	collision.shape = box
	floor_body.add_child(collision)
	world.add_child(floor_body)
	floor_body.position.y = -0.1
	shooter = Actor.new()
	shooter.configure(1, 0, "Weapon probe")
	world.add_child(shooter)
	target = Actor.new()
	target.configure(2, 1, "Contact probe")
	world.add_child(target)
	shooter.inventory.assign(Weapons.DATA.keys())
	shooter.shot_fired.connect(func(_id: int, origin: Vector3, direction: Vector3) -> void:
		shots.append({"tick": tick, "origin": origin, "direction": direction}))
	shooter.hit_confirmed.connect(func(_id: int, head: bool, lethal: bool) -> void:
		confirmations.append({"head": head, "lethal": lethal}))
	shooter.impact_created.connect(func(at: Vector3, _normal: Vector3, hit_actor: bool) -> void:
		if hit_actor: impacts.append(at))
	target.damage_taken.connect(func(_victim: int, _source: int, amount: float) -> void: damages.append(amount))
	await physics_frame
	for weapon: String in Weapons.DATA:
		await prepare(weapon)
		cadence(weapon)
		await prepare(weapon)
		reload_and_switch(weapon)
		await prepare(weapon)
		switch_cycle(weapon)
		await damage_and_feedback(weapon)
	world.queue_free()
	await process_frame
	await process_frame
	await create_timer(0.6).timeout
	print("GUNPLAY_RULES " + JSON.stringify({"checks": checks, "failures": failures}))
	quit(0 if failures.is_empty() else 1)

func prepare(weapon: String) -> void:
	shooter.reset_for_round(Vector3(0, 0.01, 0))
	target.team = 1
	target.reset_for_round(Vector3(80, 0.01, 80))
	shooter._equip(weapon)
	shooter._deploy_remaining = 0
	await physics_frame
	await physics_frame
	for step in range(4):
		shooter.input_state = {"look": Vector2(0, 1.4)}
		shooter.tick_authority(DT)
		await physics_frame
	shots.clear()
	confirmations.clear()
	damages.clear()
	impacts.clear()
	tick = 0

func advance(state: Dictionary) -> void:
	shooter.input_state = state
	shooter.tick_authority_actions(DT)
	tick += 1

func cadence(weapon: String) -> void:
	var spec: Dictionary = Weapons.get_weapon(weapon)
	# Explicit measurement ammunition, like weapon_integrity_test; not a loadout.
	shooter.ammo = 10000
	for step in range(1800):
		advance({"fire": bool(spec.automatic) or step % 2 == 0})
	var times: Array[int] = []
	var phase_error := 0.0
	var minimum_gap := INF
	var maximum_gap := 0.0
	for index in range(shots.size()):
		var at: int = shots[index].tick
		times.append(at)
		if bool(spec.automatic):
			phase_error = maxf(phase_error, absf(at * DT - index * float(spec.interval)))
		if index > 0:
			var gap: float = (at - int(shots[index - 1].tick)) * DT
			minimum_gap = minf(minimum_gap, gap)
			maximum_gap = maxf(maximum_gap, gap)
	check(not times.is_empty() and times[0] == 0, weapon + " ready initial press fires on the first action tick")
	check(shooter.ammo == 10000 - times.size(), weapon + " each emitted shot consumes exactly one round")
	if bool(spec.automatic):
		check(phase_error <= DT + 0.000001, weapon + " automatic cumulative cadence is within one tick of data")
	else:
		check(minimum_gap + 0.000001 >= float(spec.interval) and maximum_gap < float(spec.interval) + 2 * DT, weapon + " semi-auto cadence respects interval and sampled press edges")
	record("cadence", weapon, {"ticks": 1800, "shot_ticks": times, "automatic": spec.automatic, "data_interval": spec.interval, "minimum_gap": minimum_gap, "maximum_gap": maximum_gap, "maximum_phase_error": phase_error, "remaining_ammo": shooter.ammo})
	shooter._weapon_cooldowns.clear()
	shooter._fire_previous = false
	shooter.ammo = int(spec.magazine)
	shooter.reserve = 0
	shots.clear()
	for step in range(700):
		advance({"fire": true})
	var expected := int(spec.magazine) if bool(spec.automatic) else 1
	check(shots.size() == expected and shooter.ammo == int(spec.magazine) - expected, weapon + " held-trigger finite magazine respects automatic/edge rules")
	check(shooter.reserve == 0 and shooter.reload_remaining == 0, weapon + " empty reserve cannot create a reload or ammunition")
	record("held_finite_magazine", weapon, {"shots": shots.size(), "ammo": shooter.ammo, "reserve": shooter.reserve})

func reload_and_switch(weapon: String) -> void:
	var spec: Dictionary = Weapons.get_weapon(weapon)
	shooter.ammo = int(spec.magazine) - 5
	shooter.reserve = 3
	var total := shooter.ammo + shooter.reserve
	shooter.start_reload()
	var completed := 0
	for step in range(240):
		var before := shooter.ammo
		advance({"reload": true})
		check(shooter.ammo + shooter.reserve == total, weapon + " reload conserves rounds tick%d" % step)
		if shooter.reload_remaining > 0:
			check(shooter.ammo == before, weapon + " reload cannot transfer early tick%d" % step)
		else:
			completed = step + 1
			break
	check(completed > 0 and completed * DT + 0.000001 >= float(spec.reload) and completed * DT <= float(spec.reload) + DT + 0.000001, weapon + " reload completes within one tick after configured duration")
	check(shooter.ammo == int(spec.magazine) - 2 and shooter.reserve == 0, weapon + " partial reserve transfers only available rounds")
	record("partial_reload", weapon, {"data_seconds": spec.reload, "completion_ticks_after_start": completed, "seconds": completed * DT, "ammo": shooter.ammo, "reserve": shooter.reserve})
	shooter.ammo = int(spec.magazine) - 5
	shooter.reserve = 7
	shooter.start_reload()
	for step in range(int(float(spec.reload) / DT * 0.5)):
		advance({})
	var alternate := "rifle" if weapon == "sidearm" else "sidearm"
	var start_tick := tick
	advance({"weapon": alternate, "fire": true})
	check(shooter.weapon_id == alternate and shooter.reload_remaining == 0, weapon + " ordinary switch cancels reload")
	shots.clear()
	# A semi-auto alternate needs real release/press edges during deploy.
	for step in range(1, 40):
		advance({"weapon": alternate, "fire": step % 2 == 0})
		if not shots.is_empty(): break
	var deploy_ticks := int(shots[0].tick) - start_tick if not shots.is_empty() else -1
	check(deploy_ticks * DT + 0.000001 >= Actor.DEPLOY_SECONDS and deploy_ticks * DT <= Actor.DEPLOY_SECONDS + 2 * DT + 0.000001, weapon + " alternate respects deploy delay")
	advance({"weapon": weapon})
	check(shooter.ammo == int(spec.magazine) - 5 and shooter.reserve == 7 and shooter.reload_remaining == 0, weapon + " cancelled reload preserves original magazine and reserve")
	for step in range(240): advance({})
	check(shooter.ammo == int(spec.magazine) - 5 and shooter.reserve == 7, weapon + " cancelled reload never transfers later")
	record("reload_switch", weapon, {"alternate": alternate, "deploy_ticks": deploy_ticks, "ammo_after_return": shooter.ammo, "reserve_after_return": shooter.reserve})

func switch_cycle(weapon: String) -> void:
	var spec: Dictionary = Weapons.get_weapon(weapon)
	var alternate := "rifle" if weapon == "sidearm" else "sidearm"
	advance({"fire": true})
	advance({"weapon": alternate})
	advance({"weapon": weapon})
	for step in range(120):
		advance({"fire": step % 2 == 0})
		if shots.size() >= 2: break
	var gap_ticks := int(shots[1].tick) - int(shots[0].tick) if shots.size() == 2 else -1
	check(gap_ticks * DT + 0.000001 >= float(spec.interval), weapon + " round-trip switch cannot shorten its cycle")
	check(gap_ticks >= 20 and gap_ticks * DT <= maxf(2 * DT + Actor.DEPLOY_SECONDS, float(spec.interval)) + 2 * DT + 0.000001, weapon + " return switch costs only remaining cycle and deploy")
	record("switch_cycle", weapon, {"shot_gap_ticks": gap_ticks, "data_interval": spec.interval, "return_switch_tick": 2, "deploy_seconds": Actor.DEPLOY_SECONDS})

func damage_and_feedback(weapon: String) -> void:
	var spec: Dictionary = Weapons.get_weapon(weapon)
	for head in [false, true]:
		await prepare(weapon)
		target.position = Vector3(0, 0.01, -2)
		await physics_frame
		await physics_frame
		# Short-range center aim leaves ample room for the stock spread cone.
		var aim_y := 1.56 if head else 1.0
		shooter.yaw = 0
		shooter.pitch = atan2(aim_y - shooter.head_height, 2.0)
		shooter.recoil = Vector2.ZERO
		shooter._rng.seed = 17
		advance({"fire": true})
		check(shots.size() == 1 and shooter.ammo == int(spec.magazine) - 1, weapon + " damage probe consumes one round")
		check(damages.size() == 1 and confirmations.size() == 1, weapon + " real hit emits one damage and one confirmation")
		check(impacts.size() == 1, weapon + " hit emits one actual actor contact position")
		if shots.size() != 1 or damages.size() != 1 or confirmations.size() != 1 or impacts.size() != 1: continue
		var distance: float = (shots[0].origin as Vector3).distance_to(impacts[0])
		var expected := float(spec.damage) * lerpf(1.0, float(spec.falloff), distance / float(spec.range)) * (float(spec.head) if head else 1.0)
		check(target.last_hit_headshot == head, weapon + " produced ray reaches declared body/head volume")
		check(absf(damages[0] - minf(100.0, expected)) < 0.00001, weapon + " damage agrees with stock distance falloff and head multiplier")
		check(bool(confirmations[0].head) == head and bool(confirmations[0].lethal) == (expected >= 100), weapon + " feedback reports actual head/lethal result")
		var authoritative := shooter.snapshot()
		shooter.tick_visual(0.2)
		check(shooter.hit_feedback_remaining == 0 and shooter.snapshot() == authoritative, weapon + " expiring feedback leaves authority unchanged")
		record("damage", weapon, {"head": head, "distance": distance, "expected_damage": expected, "applied_damage": damages[0], "confirmation": confirmations[0]})
	for control in ["miss", "friendly", "dry", "reload", "deploy"]:
		await prepare(weapon)
		shooter.yaw = 0
		shooter.pitch = 0
		if control == "friendly":
			target.team = 0
			target.position = Vector3(0, 0.01, -2)
		elif control == "dry":
			shooter.ammo = 0
			shooter.reserve = 0
		elif control == "reload":
			shooter.ammo -= 1
			shooter.start_reload()
		elif control == "deploy":
			shooter._deploy_remaining = Actor.DEPLOY_SECONDS
		await physics_frame
		var before := shooter.ammo
		advance({"fire": true})
		check(damages.is_empty() and confirmations.is_empty() and target.health == 100, weapon + " " + control + " produces no damage confirmation")
		if control in ["dry", "reload", "deploy"]:
			check(shots.is_empty() and shooter.ammo == before, weapon + " " + control + " cannot emit or consume a shot")
		record("negative", weapon, {"control": control, "shots": shots.size(), "damage_events": damages.size(), "confirmations": confirmations.size(), "ammo": shooter.ammo})
