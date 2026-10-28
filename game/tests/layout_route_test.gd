extends SceneTree
## Relay Yard revision 2 closes the straight line from the attacker spawn to a site, so a player has to walk the yard.
## This drives a real attacker through the engine's physics, the other nine held idle:
##   - along the route the bots use (Arena.bot_navigation), from three spawn slots to each site, and plants;
##   - along the scripted player of the native verifier, read from PLANT_ROUTE_SITE_A_REVISION_2 in
##     scripts/verify_offline_match.py so the two cannot drift apart, every leg a straight line, so a corner that clips the
##     body shows up, and plants;
##   - through each of the four lane-divider doors, on the graph (a crossing, not a detour) and with a body.
## The navigation grid is 2 m and the divider doors 2.5 m wide; this is where a mismatch between that graph and the
## collision world would show. It asserts the yard is traversable and plantable, not that it is fun or balanced.
const VERIFIER := "../scripts/verify_offline_match.py"
const SPAWN_SLOTS := [0, 2, 4]
## Inner doors (x = 10, between the divider and the mid hub) and outer doors (x = 17.25, between the divider and the wall cargo).
const DOOR_X := [-17.25, -10.0, 10.0, 17.25]
const DOOR_FROM_Z := -6.0
const DOOR_TO_Z := 3.0
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

## One idle-bot match with the local attacker (the device carrier) standing at `at`.
func _start_match(at: Vector3) -> SBActor:
	game = TacticalMatch.new()
	game.configure({"mode": "offline", "difficulty": "normal"})
	root.add_child(game)
	game._bot_clock = 1.0e12
	game.phase = "live"
	game.time_left = TacticalMatch.ROUND_SECONDS
	var actor := game.local_actor()
	actor.global_position = at
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

## The bots' route from `from` to `to`: the graph's own path, then the destination.
func _nav_route(arena: RelayYard, from: Vector3, to: Vector3) -> Array[Vector3]:
	var route: Array[Vector3] = []
	for point in arena._navigation.get_point_path(arena._navigation.get_closest_point(from), arena._navigation.get_closest_point(to)):
		route.append(point)
	route.append(to)
	return route

## The verifier's scripted plant route, as (x, z) pairs from its own source. Empty when it cannot be read.
func _verifier_route() -> Array[Vector3]:
	var route: Array[Vector3] = []
	var file := FileAccess.open(ProjectSettings.globalize_path("res://").path_join(VERIFIER).simplify_path(), FileAccess.READ)
	if file == null:
		return route
	var block := RegEx.create_from_string("PLANT_ROUTE_SITE_A_REVISION_2\\s*=\\s*\\[([^\\]]*)\\]").search(file.get_as_text())
	if block == null:
		return route
	for point in RegEx.create_from_string("\\((-?[0-9.]+),\\s*(-?[0-9.]+)\\)").search_all(block.get_string(1)):
		route.append(Vector3(float(point.get_string(1)), 0.0, float(point.get_string(2))))
	return route

func _plant_route(label: String, start: Vector3, points_for: Callable) -> void:
	var actor := await _start_match(start)
	var points: Array[Vector3] = points_for.call(game.arena, actor.global_position)
	var seconds := await _walk(actor, points)
	var site := game.arena.is_at_site(actor.global_position)
	check(seconds >= 0.0, "%s: reaches the end of the route" % label)
	check(site >= 0, "%s: ends inside a plant zone (at %s)" % [label, str(actor.global_position)])
	check(seconds >= 0.0 and site >= 0 and await _plant(actor), "%s: plants the device" % label)
	if seconds >= 0.0:
		print("LAYOUT_ROUTE %s walked=%.1fs planted=%s" % [label, seconds, game.objective_state == "planted"])
	await _end_match()

func _through_door(x: float) -> void:
	var label := "door x=%.2f" % x
	var from := Vector3(x, 0.0, DOOR_FROM_Z)
	var to := Vector3(x, 0.0, DOOR_TO_Z)
	var actor := await _start_match(from)
	var points := _nav_route(game.arena, from, to)
	var length := 0.0
	var previous := from
	for point in points:
		length += previous.distance_to(point)
		previous = point
	check(length <= 12.0, "%s: the bots' graph crosses the divider in %.1f m, not by a detour" % [label, length])
	var seconds := await _walk(actor, points)
	check(seconds >= 0.0 and Vector2(actor.global_position.x - to.x, actor.global_position.z - to.z).length() < 1.0, "%s: a body walks through (ended at %s)" % [label, str(actor.global_position)])
	print("LAYOUT_DOOR %s graph=%.1fm walked=%.1fs" % [label, length, seconds])
	await _end_match()

func _run() -> void:
	Engine.max_physics_steps_per_frame = 64
	Engine.physics_ticks_per_second = int(60.0 * SPEED_UP)
	Engine.time_scale = SPEED_UP
	var spawns: Array[Vector3] = []
	var probe := RelayYard.new()
	probe._build()
	spawns.assign(probe.attack_spawns)
	probe.free()
	for site_index in 2:
		for slot in SPAWN_SLOTS:
			var to_site := func(arena: RelayYard, from: Vector3) -> Array[Vector3]: return _nav_route(arena, from, arena.sites[site_index])
			await _plant_route("bot route to site %s from slot %d" % ["AB"[site_index], slot], spawns[slot], to_site)
	var route := _verifier_route()
	check(route.size() >= 4, "the native verifier's plant route can be read from %s" % VERIFIER)
	if route.size() >= 4:
		await _plant_route("scripted player route to site A", spawns[2], func(_arena: RelayYard, _from: Vector3) -> Array[Vector3]: return route)
	for x: float in DOOR_X:
		await _through_door(x)
	Engine.time_scale = 1.0
	Engine.physics_ticks_per_second = 60
	# The AudioServer releases transient playback objects on its mixer cycles; quitting before they run is reported as a leak.
	await create_timer(0.6).timeout
	await process_frame
	await process_frame
	print("LAYOUT_ROUTE_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
