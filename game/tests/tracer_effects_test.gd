extends SceneTree
## Tracers: the pool's bounds and life, which shots carry one, and that a shot fired through the real authority tick
## draws one for an operator and never for the local player. Presentation only: nothing here reads or changes damage,
## ammo or the shot RNG. What a tracer looks like is judged on renders (muzzle_presentation_capture.gd), not here.
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const TracerEffects = preload("res://scripts/gameplay/tracer_effects.gd")
var failures: Array[String] = []
var checks := 0
## The rendering server of a --headless run keeps no instance data, so the checks that read a streak's placed transform
## and per-instance data back need a rendering display (validate.sh runs this suite both ways).
var rendered := DisplayServer.get_name() != "headless"

func _initialize() -> void:
	_run.call_deferred()

func check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

func _run() -> void:
	# Every third shot carries one, and the first of a burst does.
	var carried := 0
	for index in 30:
		if TracerEffects.carries(index):
			carried += 1
	check(carried == 10 and TracerEffects.carries(0) and not TracerEffects.carries(1) and not TracerEffects.carries(2) and TracerEffects.carries(3), "one shot in %d carries a tracer, starting with the first" % TracerEffects.EVERY)

	var world := Node3D.new()
	root.add_child(world)
	var tracers := TracerEffects.for_world(world)
	await process_frame
	check(TracerEffects.for_world(world) == tracers and world.get_children().filter(func(n): return n is TracerEffects).size() == 1, "one tracer pool per world")
	tracers.set_process(false)

	check(not tracers.trace(Vector3.ZERO, Vector3(0, 0, -TracerEffects.MIN_PATH * 0.5)) and tracers.active() == 0, "a path shorter than the minimum draws nothing")
	check(not tracers.trace(Vector3(NAN, 0, 0), Vector3(0, 0, -20)) and not tracers.trace(Vector3.ZERO, Vector3(INF, 0, 0)) and tracers.active() == 0, "a non-finite end point draws nothing")
	check(tracers.trace(Vector3(0, 1.3, 0), Vector3(0, 1.3, -20)) and tracers.active() == 1, "an ordinary path draws one")
	# A shot into the open is drawn only MAX_PATH long.
	tracers.trace(Vector3.ZERO, Vector3(0, 0, -400))
	var long_slot: Dictionary = tracers._slots[1]
	check(is_equal_approx(float(long_slot.path), TracerEffects.MAX_PATH) and is_equal_approx((long_slot.span as Vector3).length(), TracerEffects.MAX_PATH), "an open-air path is clamped to %.0f m" % TracerEffects.MAX_PATH)

	# The pool is fixed: more than CAP at once reuses the oldest slots and never grows.
	for i in TracerEffects.CAP + 6:
		tracers.trace(Vector3(i, 1, 0), Vector3(i, 1, -30))
	check(tracers.active() == TracerEffects.CAP and tracers._multi.instance_count == TracerEffects.CAP, "the pool never holds more than %d" % TracerEffects.CAP)

	# A streak lives for (path + STREAK) / SPEED seconds, then its instance is collapsed.
	for i in TracerEffects.CAP:
		tracers._slots[i].live = false
		tracers._hide(i)
	tracers._next = 0
	tracers.trace(Vector3(0, 1, 0), Vector3(0, 1, -19.0))
	var life := (19.0 + TracerEffects.STREAK) / TracerEffects.SPEED
	var steps := int(life / (1.0 / 60.0))
	for _i in maxi(steps - 1, 1):
		tracers._process(1.0 / 60.0)
	check(tracers.active() == 1, "a streak is still in flight just before the end of its life")
	if rendered:
		var data: Color = tracers._multi.get_instance_custom_data(0)
		check(data.r <= 1.0 and data.r > 0.9 and data.g < 1.0 and data.g > 0.5, "near the end the head has landed and the tail is catching up (head %.2f tail %.2f)" % [data.r, data.g])
	for _i in 6:
		tracers._process(1.0 / 60.0)
	check(tracers.active() == 0, "the streak is gone after its life")
	if rendered:
		check(tracers._multi.get_instance_transform(0).basis.get_scale().is_zero_approx(), "a finished streak's instance is collapsed")

	# The transform is never singular, whatever the direction (straight up and straight along X included).
	var directions: Array[Vector3] = [Vector3.UP, Vector3.DOWN, Vector3.RIGHT, Vector3(0, 0.0001, -1), Vector3(1, 1, 1).normalized()]
	var regular := true
	for d in directions:
		tracers.trace(Vector3(0, 5, 0), Vector3(0, 5, 0) + d * 30.0)
		var slot_index := (tracers._next + TracerEffects.CAP - 1) % TracerEffects.CAP
		if rendered:
			regular = regular and absf(tracers._multi.get_instance_transform(slot_index).basis.determinant()) > 0.001
	check(regular, "the streak's transform is never singular (%s)" % ("checked on the placed transforms" if rendered else "headless: not readable"))

	# Through the real authority tick: an operator who fires three times draws exactly one tracer; the local player none.
	var arena := Arena.new()
	world.add_child(arena)
	var operator_actor := Actor.new()
	operator_actor.configure(2, 1, "Operator")
	world.add_child(operator_actor)
	var local := Actor.new()
	local.configure(1, 0, "Local", true)
	world.add_child(local)
	operator_actor.reset_for_round(Vector3(0, 0.05, -9))
	local.reset_for_round(Vector3(0, 0.05, 12))
	await physics_frame
	await physics_frame
	for slot in tracers._slots:
		slot.live = false
	var before := tracers.active()
	# A held trigger on an automatic weapon: three shots in a row are numbered 0, 1, 2 and only the first carries one.
	operator_actor.credits = 20000
	check(operator_actor.buy_weapon("rifle"), "the operator buys the rifle")
	operator_actor.yaw = 0.0
	operator_actor.pitch = 0.0
	var shots := 0
	for _i in 1200:
		operator_actor.input_state = {"look": Vector2(0, 0), "fire": true}
		var ammo_before := operator_actor.ammo
		operator_actor.tick_authority(1.0 / 60.0)
		if operator_actor.ammo < ammo_before:
			shots += 1
		if shots >= 3:
			break
	operator_actor.input_state = {"look": Vector2(0, 0), "fire": false}
	check(shots == 3, "the operator fired three shots through the authority tick (%d)" % shots)
	check(tracers.active() - before == 1, "three held-trigger shots drew exactly one tracer (%d)" % (tracers.active() - before))
	# The sidearm is semi-automatic and every pull starts a new burst, so every pull of it carries one.
	for slot in tracers._slots:
		slot.live = false
	check(operator_actor.buy_weapon("sidearm") or operator_actor.inventory.has("sidearm"), "the operator has the sidearm")
	operator_actor._equip("sidearm")
	operator_actor.reload_remaining = 0.0
	var pulls := 0
	for i in 1200:
		operator_actor.input_state = {"look": Vector2(0, 0), "fire": i % 2 == 0}
		var ammo_before := operator_actor.ammo
		operator_actor.tick_authority(1.0 / 60.0)
		if operator_actor.ammo < ammo_before:
			pulls += 1
		if pulls >= 2:
			break
	check(pulls == 2 and tracers.active() == 2, "two pulls of the sidearm draw two tracers (%d pulls, %d tracers)" % [pulls, tracers.active()])
	for slot in tracers._slots:
		slot.live = false
	local._shot_index = 0
	local._tracer(Vector3(0, 1, 40))
	check(tracers.active() == 0, "the local player's own shot draws no tracer")

	# An operator's flash grows with the distance from the viewer so it stays readable down the yard.
	local.camera.current = true
	await process_frame
	var gap := local.camera.global_position.distance_to(operator_actor.global_position)
	var expected := clampf(1.0 + (gap - SBActor.WORLD_FLASH_NEAR) * SBActor.WORLD_FLASH_GROWTH, 1.0, SBActor.WORLD_FLASH_MAX)
	check(gap > 15.0 and is_equal_approx(operator_actor._flash_distance_gain(), expected) and expected > 1.2, "an operator %.0f m away has a %.2f times larger flash" % [gap, expected])
	operator_actor.global_position = Vector3(0, 0.05, 12 - 4.0)
	check(is_equal_approx(operator_actor._flash_distance_gain(), 1.0), "an operator within %.0f m has the plain flash" % SBActor.WORLD_FLASH_NEAR)
	operator_actor.global_position = Vector3(0, 0.05, 12 - 120.0)
	check(is_equal_approx(operator_actor._flash_distance_gain(), SBActor.WORLD_FLASH_MAX), "the growth is capped at %.1f times" % SBActor.WORLD_FLASH_MAX)

	check(failures.is_empty(), "no failures")
	print("TRACER EFFECTS TEST %s (%d checks)" % ["PASS" if failures.is_empty() else "FAIL", checks])
	world.queue_free()
	await process_frame
	quit(0 if failures.is_empty() else 1)
