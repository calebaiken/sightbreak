extends SceneTree
## Gunplay measurements through the real authority path: Actor.tick_authority at 60 Hz, the same trace, falloff,
## headshot volumes, spread, recoil and cooldown code a match uses. Observation only: it asserts nothing about
## quality and sets nothing but the random seeds. Output is one JSON line per measurement, prefixed GUNPLAY_<KIND>,
## for scripts/summarize_gunplay.py.
##
## Options after `--`:
##   --only=profile,spread,timing,accuracy,duel   which measurements (default all)
##   --weapons=sidearm,smg,rifle,marksman         subset (default all four)
##   --trials=<int>   accuracy trials per weapon, distance and mode (default 40)
##   --duels=<int>    duels per weapon pair and distance (default 60)
##   --seed=<int>     base seed (default 7)
##   --verbose        also print one GUNPLAY_DUEL_TRIAL line per duel (health, ammo, ticks)
##
## Fixtures, not matches: a bare floor, one standing target that does not move or shoot back (accuracy), perfect
## aim at the chest from a standing start, no armour. What it measures is the weapon, not a player.
const Actor = preload("res://scripts/gameplay/actor.gd")
const Weapons = preload("res://scripts/gameplay/weapons.gd")
const DT := 1.0 / 60.0
const EYE := 1.62
const CHEST := 1.1
const FEET := 0.05
const DISTANCES := [5.0, 10.0, 20.0, 30.0, 45.0, 70.0]
const DUEL_DISTANCES := [8.0, 20.0, 40.0]
const MAX_SECONDS := 6.0

var world: Node3D
var weapons: Array = ["sidearm", "smg", "rifle", "marksman"]
var only: Array = ["profile", "spread", "timing", "accuracy", "duel"]
var trials := 40
var duels := 60
var base_seed := 7
var verbose := false
var blue := {}
var red := {}

func _initialize() -> void:
	_run.call_deferred()

func _options() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--only="):
			only = Array(argument.trim_prefix("--only=").split(","))
		elif argument.begins_with("--weapons="):
			weapons = Array(argument.trim_prefix("--weapons=").split(","))
		elif argument.begins_with("--trials="):
			trials = int(argument.trim_prefix("--trials="))
		elif argument.begins_with("--duels="):
			duels = int(argument.trim_prefix("--duels="))
		elif argument.begins_with("--seed="):
			base_seed = int(argument.trim_prefix("--seed="))
		elif argument == "--verbose":
			verbose = true

func _run() -> void:
	_options()
	world = Node3D.new()
	root.add_child(world)
	var floor_body := StaticBody3D.new()
	var floor_shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(400, 1, 400)
	floor_shape.shape = box
	floor_body.add_child(floor_shape)
	floor_body.position = Vector3(0, -0.5, 0)
	floor_body.collision_layer = 1
	world.add_child(floor_body)
	var slot := 0
	for weapon: String in weapons:
		blue[weapon] = _make(100 + slot, 0, weapon)
		red[weapon] = _make(200 + slot, 1, weapon)
		slot += 1
	await _settle(40)
	if only.has("profile"):
		for weapon: String in weapons:
			_profile(weapon)
	if only.has("spread"):
		for weapon: String in weapons:
			_spread(weapon)
	if only.has("timing"):
		for weapon: String in weapons:
			await _timing(weapon)
	if only.has("accuracy"):
		for weapon: String in weapons:
			for distance: float in DISTANCES:
				if distance > float(Weapons.get_weapon(weapon)["range"]) * 1.0001:
					continue
				for mode in _modes(weapon):
					_accuracy(weapon, distance, mode)
	if only.has("duel"):
		for index_a in range(weapons.size()):
			for index_b in range(index_a, weapons.size()):
				for distance: float in DUEL_DISTANCES:
					_duel(weapons[index_a], weapons[index_b], distance)
	world.queue_free()
	await process_frame
	quit(0)

func _make(id: int, team: int, weapon: String) -> SBActor:
	var actor := Actor.new()
	actor.configure(id, team, "gun-%d" % id, false)
	world.add_child(actor)
	actor.reset_for_round(_park(id))
	if weapon != "sidearm":
		actor.credits = 99999
		actor.buy_weapon(weapon)
	actor.reserve = 100000
	return actor

## Idle actors stand far from the firing line so they cannot intercept a shot.
func _park(id: int) -> Vector3:
	return Vector3(150.0 + float(id % 100) * 0.5, FEET, -150.0 + float(id % 7) * 20.0)

func _settle(ticks: int) -> void:
	for _tick in range(ticks):
		for actor: SBActor in _all():
			actor.input_state = {"look": Vector2(actor.yaw, 0.0)}
			actor.tick_authority(DT)
		await physics_frame

func _all() -> Array:
	var list: Array = []
	for weapon: String in weapons:
		list.append(blue[weapon])
		list.append(red[weapon])
	return list

func _park_all() -> void:
	for actor: SBActor in _all():
		actor.reset_for_round(_park(actor.actor_id))

func _modes(weapon: String) -> Array:
	var automatic: bool = Weapons.get_weapon(weapon)["automatic"]
	return ["hold", "burst3", "advance"] if automatic else ["hold", "advance"]

func _median(values: Array) -> float:
	if values.is_empty():
		return -1.0
	var sorted := values.duplicate()
	sorted.sort()
	return float(sorted[sorted.size() / 2])

func _emit(kind: String, data: Dictionary) -> void:
	print("GUNPLAY_%s %s" % [kind, JSON.stringify(data)])

## Recoil and cadence of one magazine held down from rest, then the time recoil takes to clear.
func _profile(weapon: String) -> void:
	_park_all()
	var shooter: SBActor = blue[weapon]
	shooter.reset_for_round(Vector3(0, FEET, 0))
	shooter._rng.seed = base_seed
	var spec := Weapons.get_weapon(weapon)
	var automatic: bool = spec["automatic"]
	var ticks := 0
	var shot_ticks: Array = []
	var recoil_y: Array = []
	var recoil_x: Array = []
	var peak_y := 0.0
	var peak_x := 0.0
	var capped_at := -1
	while shooter.ammo > 0 and ticks < 1200:
		var before := shooter.ammo
		shooter.input_state = {"look": Vector2(0.0, 0.0), "fire": true if automatic else ticks % 2 == 0}
		shooter.tick_authority(DT)
		if shooter.ammo < before:
			shot_ticks.append(ticks)
			recoil_y.append(snappedf(shooter.recoil.y, 0.0001))
			recoil_x.append(snappedf(shooter.recoil.x, 0.0001))
			peak_y = maxf(peak_y, shooter.recoil.y)
			peak_x = maxf(peak_x, absf(shooter.recoil.x))
			if capped_at < 0 and shooter.recoil.y >= 0.1599:
				capped_at = shot_ticks.size()
		ticks += 1
	var shots := shot_ticks.size()
	var span := float(shot_ticks[-1] - shot_ticks[0]) * DT if shots > 1 else 0.0
	var recovery_ticks := 0
	var recoil_at_release := shooter.recoil.length()
	while shooter.recoil != Vector2.ZERO and recovery_ticks < 1200:
		shooter.input_state = {"look": Vector2(0.0, 0.0)}
		shooter.tick_authority(DT)
		recovery_ticks += 1
	_emit("PROFILE", {
		"weapon": weapon, "shots": shots,
		"interval_data": spec["interval"], "interval_measured": snappedf(span / float(maxi(shots - 1, 1)), 0.0001),
		"seconds_to_empty": snappedf(float(shot_ticks[-1]) * DT, 0.001) if shots > 0 else 0.0,
		"recoil_peak_y_rad": snappedf(peak_y, 0.0001), "recoil_peak_x_rad": snappedf(peak_x, 0.0001),
		"recoil_after_shot_y": recoil_y.slice(0, 12), "shots_to_cap": capped_at,
		"recoil_at_release_rad": snappedf(recoil_at_release, 0.0001), "recovery_seconds": snappedf(float(recovery_ticks) * DT, 0.01),
	})

## Spread as the authority computes it for each stance.
func _spread(weapon: String) -> void:
	_park_all()
	var shooter: SBActor = blue[weapon]
	shooter.reset_for_round(Vector3(0, FEET, 0))
	shooter.velocity = Vector3.ZERO
	shooter._crouching = false
	var standing := shooter.current_spread(false)
	shooter._crouching = true
	var crouched := shooter.current_spread(false)
	shooter._crouching = false
	shooter.velocity = Vector3(Actor.WALK_SPEED, 0.0, 0.0)
	var walking := shooter.current_spread(false)
	shooter.velocity = Vector3.ZERO
	var airborne := shooter.current_spread(true)
	_emit("SPREAD", {"weapon": weapon, "standing_rad": snappedf(standing, 0.00001), "crouched_rad": snappedf(crouched, 0.00001), "walking_rad": snappedf(walking, 0.00001), "airborne_rad": snappedf(airborne, 0.00001), "walk_speed": Actor.WALK_SPEED})

## Reload and draw times as the authority counts them.
func _timing(weapon: String) -> void:
	_park_all()
	var shooter: SBActor = blue[weapon]
	shooter.reset_for_round(Vector3(0, FEET, 0))
	shooter.ammo = 0
	shooter.input_state = {"look": Vector2(0.0, 0.0), "reload": true}
	var ticks := 0
	shooter.tick_authority(DT)
	ticks += 1
	while shooter.reload_remaining > 0.0 and ticks < 1200:
		shooter.input_state = {"look": Vector2(0.0, 0.0)}
		shooter.tick_authority(DT)
		ticks += 1
	var spec := Weapons.get_weapon(weapon)
	_emit("TIMING", {"weapon": weapon, "reload_data": spec["reload"], "reload_measured": snappedf(float(ticks) * DT, 0.001), "magazine": spec["magazine"], "ammo_after": shooter.ammo, "deploy_seconds": Actor.DEPLOY_SECONDS})
	await physics_frame

## One standing target, perfect chest aim. Modes: hold (trigger held, or clicked at the weapon's own rate),
## burst3 (three shots, 0.3 s off, repeat) and advance (trigger held while walking at the target).
func _accuracy(weapon: String, distance: float, mode: String) -> void:
	_park_all()
	var shooter: SBActor = blue[weapon]
	var target: SBActor = red[weapon]
	var spec := Weapons.get_weapon(weapon)
	var automatic: bool = spec["automatic"]
	var shots_total := 0
	var hits_total := 0
	var heads_total := 0
	var kills := 0
	var kill_times: Array = []
	var kill_shots: Array = []
	var travelled_total := 0.0
	for trial in range(trials):
		shooter.reset_for_round(Vector3(0, FEET, 0))
		target.reset_for_round(Vector3(0, FEET, -distance))
		shooter._rng.seed = base_seed * 100003 + trial * 31 + int(distance)
		shooter.ammo = int(spec["magazine"])
		var aim := atan2(target.global_position.y + CHEST - (shooter.global_position.y + EYE), distance)
		var stats := {"shots": 0, "hits": 0, "heads": 0, "dead_tick": -1, "first_tick": -1, "shots_at_kill": 0}
		var tick_box := [0]
		var on_shot := func(_id: int, _origin: Vector3, _direction: Vector3) -> void:
			stats["shots"] = int(stats["shots"]) + 1
			if int(stats["first_tick"]) < 0:
				stats["first_tick"] = tick_box[0]
		var on_hit := func(_attacker: int, headshot: bool, lethal: bool) -> void:
			stats["hits"] = int(stats["hits"]) + 1
			if headshot:
				stats["heads"] = int(stats["heads"]) + 1
			if lethal and int(stats["dead_tick"]) < 0:
				stats["dead_tick"] = tick_box[0]
				# hit_confirmed fires inside _fire, before shot_fired for the same shot is emitted.
				stats["shots_at_kill"] = int(stats["shots"]) + 1
		shooter.shot_fired.connect(on_shot)
		shooter.hit_confirmed.connect(on_hit)
		var burst_shots := 0
		var pause := 0
		var last_shots := 0
		for tick in range(int(MAX_SECONDS / DT)):
			tick_box[0] = tick
			var fire := true if automatic else tick % 2 == 0
			if mode == "burst3":
				if pause > 0:
					pause -= 1
					fire = false
				elif burst_shots >= 3:
					burst_shots = 0
					pause = 18
					fire = false
			var move := Vector2(0.0, 1.0) if mode == "advance" else Vector2.ZERO
			shooter.input_state = {"look": Vector2(0.0, aim), "fire": fire, "move": move}
			shooter.tick_authority(DT)
			if int(stats["shots"]) > last_shots:
				burst_shots += int(stats["shots"]) - last_shots
				last_shots = int(stats["shots"])
			if not target.alive or shooter.ammo <= 0:
				break
		shooter.shot_fired.disconnect(on_shot)
		shooter.hit_confirmed.disconnect(on_hit)
		shots_total += int(stats["shots"])
		hits_total += int(stats["hits"])
		heads_total += int(stats["heads"])
		if int(stats["dead_tick"]) >= 0:
			kills += 1
			kill_times.append(float(int(stats["dead_tick"]) - int(stats["first_tick"])) * DT)
			kill_shots.append(int(stats["shots_at_kill"]))
		travelled_total += absf(shooter.global_position.z)
	_emit("ACCURACY", {
		"weapon": weapon, "distance": distance, "mode": mode, "trials": trials,
		"shots_per_trial": snappedf(float(shots_total) / float(trials), 0.1), "walked_m_mean": snappedf(travelled_total / float(trials), 0.01),
		"hit_rate": snappedf(float(hits_total) / float(maxi(shots_total, 1)), 0.001),
		"head_share_of_hits": snappedf(float(heads_total) / float(maxi(hits_total, 1)), 0.001),
		"kill_rate": snappedf(float(kills) / float(trials), 0.001),
		"kill_time_median_s": snappedf(_median(kill_times), 0.001), "kill_shots_median": _median(kill_shots),
	})

## Two operators of the given weapons start facing each other and open fire on the same tick, both aiming at the
## chest. The processing order inside a tick is shuffled per duel step so it does not decide the result.
func _duel(weapon_a: String, weapon_b: String, distance: float) -> void:
	var a_wins := 0
	var b_wins := 0
	var trades := 0
	var none := 0
	var win_times: Array = []
	var order := RandomNumberGenerator.new()
	for trial in range(duels):
		_park_all()
		var first: SBActor = blue[weapon_a]
		var second: SBActor = red[weapon_b]
		first.reset_for_round(Vector3(0, FEET, 0))
		second.reset_for_round(Vector3(0, FEET, -distance))
		first._rng.seed = base_seed * 7919 + trial * 2
		second._rng.seed = base_seed * 7919 + trial * 2 + 1
		order.seed = base_seed * 104729 + trial
		first.ammo = int(Weapons.get_weapon(weapon_a)["magazine"])
		second.ammo = int(Weapons.get_weapon(weapon_b)["magazine"])
		var aim_first := atan2(second.global_position.y + CHEST - (first.global_position.y + EYE), distance)
		var aim_second := atan2(first.global_position.y + CHEST - (second.global_position.y + EYE), distance)
		var automatic_first: bool = Weapons.get_weapon(weapon_a)["automatic"]
		var automatic_second: bool = Weapons.get_weapon(weapon_b)["automatic"]
		var finished_at := -1
		for tick in range(int(MAX_SECONDS / DT)):
			var pair: Array = [first, second]
			if order.randi() % 2 == 0:
				pair = [second, first]
			first.input_state = {"look": Vector2(0.0, aim_first), "fire": true if automatic_first else tick % 2 == 0}
			second.input_state = {"look": Vector2(PI, aim_second), "fire": true if automatic_second else tick % 2 == 0}
			for actor: SBActor in pair:
				actor.tick_authority(DT)
			if not first.alive or not second.alive:
				finished_at = tick
				break
			if first.ammo <= 0 and second.ammo <= 0:
				break
		if verbose:
			_emit("DUEL_TRIAL", {"a": weapon_a, "b": weapon_b, "distance": distance, "trial": trial, "a_health": snappedf(first.health, 0.1), "b_health": snappedf(second.health, 0.1), "a_ammo": first.ammo, "b_ammo": second.ammo, "ended_tick": finished_at})
		if first.alive and not second.alive:
			a_wins += 1
			win_times.append(float(finished_at) * DT)
		elif second.alive and not first.alive:
			b_wins += 1
		elif not first.alive and not second.alive:
			trades += 1
		else:
			none += 1
	_emit("DUEL", {"a": weapon_a, "b": weapon_b, "distance": distance, "duels": duels, "a_wins": a_wins, "b_wins": b_wins, "trades": trades, "unresolved": none, "a_win_time_median_s": snappedf(_median(win_times), 0.001)})
