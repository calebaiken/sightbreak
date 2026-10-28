extends SceneTree
## Relay Yard revision 2 closes the straight line from the attacker spawn to a site, so a player has to walk the yard.
## This drives a real attacker through the engine's physics, the other nine held idle:
##   - along the route the bots use (Arena.bot_navigation), from three spawn slots to each site, and plants;
##   - along the scripted player of the native verifier, from the position the plant fixture gives the human
##     (offline_diagnostics.gd) over the waypoints in PLANT_ROUTE_SITE_A_REVISION_2 (scripts/verify_offline_match.py), both
##     read from their sources so the three cannot drift apart. Every leg is a straight line, so a corner that clips the
##     body shows up. It plants, and the old straight line from the same start is shown to end against the site shield;
##   - through each of the four lane-divider doors, on the graph (a crossing, not a detour) and with a body;
##   - the native focus test's W press from the stock human spawn, which needs the body to be able to move after it has already
##     been held into the screen wall (see _focus_press).
## The navigation grid is 2 m and the divider doors 2.5 m wide; this is where a mismatch between that graph and the
## collision world would show. It asserts the yard is traversable and plantable, not that it is fun or balanced.
const VERIFIER := "../scripts/verify_offline_match.py"
const FIXTURE := "res://scripts/offline_diagnostics.gd"
## The straight line the verifier walked before the layout had a shield beside site A: fixture start to the plant point.
const OLD_STRAIGHT_END := Vector3(-15.0, 0.0, 8.0)
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

## Where the plant fixture puts the human attacker, from the fixture's own source. Zero when it cannot be read.
func _fixture_start() -> Vector3:
	var file := FileAccess.open(FIXTURE, FileAccess.READ)
	if file == null:
		return Vector3.ZERO
	var found := RegEx.create_from_string("scenario == \"plant\":\\s*attackers\\[0\\] = Vector3\\((-?[0-9.]+), ([0-9.]+), (-?[0-9.]+)\\)").search(file.get_as_text())
	if found == null:
		return Vector3.ZERO
	return Vector3(float(found.get_string(1)), float(found.get_string(2)), float(found.get_string(3)))

## Holds `move` for `seconds` of simulated time, looking along `yaw`.
func _hold(seconds: float, move: Vector2, yaw: float) -> void:
	var held := 0.0
	while held < seconds:
		game.set_local_input({"move": move, "look": Vector2(yaw, 0.0)})
		await physics_frame
		held += STEP

## The native focus test (scripts/verify_offline_export.py) holds W through a focus loss, releases it, presses W again and
## requires the body to move. The screen wall is 2.2 m ahead of the attacker spawn row, so a body square to it stops dead and
## the second press goes nowhere; a turn of the mouse, however small, lets it slide along the wall. Returns how far the second
## press moved the body.
func _focus_press(start: Vector3, turn: float) -> float:
	var actor := await _start_match(start)
	var yaw := actor.yaw + turn
	await _hold(3.0, Vector2(0, 1), yaw)
	await _hold(1.0, Vector2.ZERO, yaw)
	var before := actor.global_position
	await _hold(3.0, Vector2(0, 1), yaw)
	var moved := before.distance_to(actor.global_position)
	await _end_match()
	return moved

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
	var fixture := _fixture_start()
	check(route.size() >= 2, "the native verifier's plant route can be read from %s" % VERIFIER)
	check(fixture != Vector3.ZERO, "the plant fixture's start for the human can be read from %s" % FIXTURE)
	if route.size() >= 2 and fixture != Vector3.ZERO:
		await _plant_route("scripted player route to site A", fixture, func(_arena: RelayYard, _from: Vector3) -> Array[Vector3]: return route)
		check(route[route.size() - 1].distance_to(OLD_STRAIGHT_END) < 0.01, "the verifier's route ends at the point the straight line used to reach")
		var actor := await _start_match(fixture)
		var seconds := await _walk(actor, [OLD_STRAIGHT_END])
		check(seconds < 0.0 or game.arena.is_at_site(actor.global_position) < 0, "the old straight line from the fixture start is blocked by the site shield (if this fails, the detour in %s is no longer needed)" % VERIFIER)
		await _end_match()
	for x: float in DOOR_X:
		await _through_door(x)
	var square := await _focus_press(spawns[0], 0.0)
	check(square < 0.01, "square to the screen wall the body stops dead (moved %.2f m), which is why the focus test turns first" % square)
	for turn: float in [0.03, -0.03, 0.14, -0.14]:
		var moved := await _focus_press(spawns[0], turn)
		check(moved > 0.15, "after a turn of %+.2f rad the second W press still moves the body (moved %.2f m)" % [turn, moved])
		print("LAYOUT_FOCUS_PRESS turn=%+.2f moved=%.2fm" % [turn, moved])
	Engine.time_scale = 1.0
	Engine.physics_ticks_per_second = 60
	# The AudioServer releases transient playback objects on its mixer cycles; quitting before they run is reported as a leak.
	await create_timer(0.6).timeout
	await process_frame
	await process_frame
	print("LAYOUT_ROUTE_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
