extends SceneTree
## Relay Yard revision 2 closes the straight line from the attacker spawn to a site, so a player has to walk the yard.
## This drives a real attacker through the engine's physics, the other nine held idle, and plants:
##   - along the route the bots use (Arena.bot_navigation), from three spawn slots to each site, and
##   - along the scripted player of the native verifier (PLANT_ROUTE_SITE_A_REVISION_2 in scripts/verify_offline_match.py,
##     mirrored below: change both together), every leg a straight line, so a corner that clips the body shows up.
## The navigation grid is 2 m and the divider doors 2.5 m wide; this is where a mismatch between that graph and the
## collision world would show. It asserts the yard is traversable and plantable, not that it is fun or balanced.
const SPAWN_SLOTS := [0, 2, 4]
const HUMAN_ROUTE_SITE_A: Array[Vector2] = [Vector2(-16.5, -20), Vector2(-16.5, -14), Vector2(-12.5, -14), Vector2(-11, -10), Vector2(-10, -4), Vector2(-9.75, -2), Vector2(-10, 2), Vector2(-15, 8)]
const SPEED_UP := 5.0
const STEP := 1.0 / 60.0
var checks := 0
var failures := 0
var game: TacticalMatch

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(label)

func _initialize() -> void:
	_run.call_deferred()

## One idle-bot match with the local attacker (the device carrier) standing on spawn `slot`.
func _start_match(slot: int) -> SBActor:
	game = TacticalMatch.new()
	game.configure({"mode": "offline", "difficulty": "normal"})
	root.add_child(game)
	game._bot_clock = 1.0e12
	game.phase = "live"
	game.time_left = TacticalMatch.ROUND_SECONDS
	var actor := game.local_actor()
	actor.global_position = game.arena.attack_spawns[slot]
	await physics_frame
	return actor

func _end_match() -> void:
	game.queue_free()
	await process_frame
	await process_frame

## Steers at each point in turn, straight, and returns the simulated seconds taken or -1.0 when a leg overran its allowance.
func _walk(actor: SBActor, points: Array[Vector3]) -> float:
	var total := 0.0
	for point in points:
		var leg := 0.0
		var allowance := Vector2(point.x - actor.global_position.x, point.z - actor.global_position.z).length() / (SBMovementStep.WALK_SPEED * 0.5) + 2.0
		while true:
			var flat := Vector3(point.x - actor.global_position.x, 0.0, point.z - actor.global_position.z)
			if flat.length() < 0.45:
				break
			game.set_local_input({"move": Vector2(0, 1), "look": Vector2(atan2(-flat.x, -flat.z), 0.0)})
			await physics_frame
			leg += STEP
			total += STEP
			if leg > allowance:
				return -1.0
	return total

## Holds the use key where the walk ended. Returns true once the device is armed.
func _plant(actor: SBActor) -> bool:
	var held := 0.0
	while held < TacticalMatch.PLANT_SECONDS + 1.5:
		game.set_local_input({"move": Vector2.ZERO, "look": Vector2(actor.yaw, 0.0), "interact": true})
		await physics_frame
		held += STEP
		if game.objective_state == "planted":
			return true
	return false

func _attempt(label: String, slot: int, points_for: Callable) -> void:
	var actor := await _start_match(slot)
	var points: Array[Vector3] = points_for.call(game.arena, actor.global_position)
	var seconds := await _walk(actor, points)
	var site := game.arena.is_at_site(actor.global_position)
	check(seconds >= 0.0, "%s: reaches the end of the route" % label)
	check(site >= 0, "%s: ends inside a plant zone (at %s)" % [label, str(actor.global_position)])
	check(seconds >= 0.0 and site >= 0 and await _plant(actor), "%s: plants the device" % label)
	if seconds >= 0.0:
		print("LAYOUT_ROUTE %s slot=%d walked=%.1fs planted=%s" % [label, slot, seconds, game.objective_state == "planted"])
	await _end_match()

func _bot_route(site_index: int) -> Callable:
	return func(arena: RelayYard, from: Vector3) -> Array[Vector3]:
		var route: Array[Vector3] = []
		var path: PackedVector3Array = arena._navigation.get_point_path(arena._navigation.get_closest_point(from), arena._navigation.get_closest_point(arena.sites[site_index]))
		for point in path:
			route.append(point)
		route.append(arena.sites[site_index])
		return route

func _run() -> void:
	Engine.max_physics_steps_per_frame = 64
	Engine.physics_ticks_per_second = int(60.0 * SPEED_UP)
	Engine.time_scale = SPEED_UP
	for site_index in 2:
		for slot in SPAWN_SLOTS:
			await _attempt("bot route to site %s" % ("AB"[site_index]), slot, _bot_route(site_index))
	var human: Callable = func(arena: RelayYard, _from: Vector3) -> Array[Vector3]:
		var route: Array[Vector3] = []
		for point in HUMAN_ROUTE_SITE_A:
			route.append(Vector3(point.x, 0.0, point.y))
		return route
	await _attempt("scripted player route to site A", 2, human)
	Engine.time_scale = 1.0
	Engine.physics_ticks_per_second = 60
	print("LAYOUT_ROUTE_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
