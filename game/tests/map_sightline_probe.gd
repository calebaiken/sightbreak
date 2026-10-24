extends SceneTree
## Relay Yard exposure map. For every walkable 1 m cell it counts how many of the five defender
## anchors (bot_ai.gd DEFENDER_ANCHORS) have an unobstructed head-height line to it within a range
## limit, and prints an ASCII grid (north is +z at the top). Observation only; it asserts nothing.
## --range=<m> (default 38, the "normal" bot vision range) --sources=anchors|spawns
## --assert turns the layout rules of Relay Yard revision 2 into a test (see the ASSERT_ constants) and exits 1 on a failure.
const Arena = preload("res://scripts/gameplay/arena.gd")
const BotAI = preload("res://scripts/gameplay/bot_ai.gd")
var range_limit: float = 38.0
var use_spawns: bool = false
var assert_rules: bool = false
var failures: Array[String] = []
var checks: int = 0
## Layout revision 2 rules. They hold the structure the layout was built for, not a score: no defender hold position
## may see an attacker spawn; an attacker route is at least 44 m (the open pad was 37-39 m); no more than 60% of a route
## may be exposed to a defender hold position and no unbroken exposed stretch may exceed 20 m (the open pad: 97-100%
## and 30-38 m).
const ASSERT_MIN_ROUTE_M := 44.0
const ASSERT_MAX_EXPOSED_FRACTION := 0.60
const ASSERT_MAX_EXPOSED_RUN_M := 20

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--range="):
			range_limit = float(argument.trim_prefix("--range="))
		elif argument == "--sources=spawns":
			use_spawns = true
		elif argument == "--assert":
			assert_rules = true
	_run.call_deferred()

func check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

func _run() -> void:
	var world := Node3D.new()
	root.add_child(world)
	var arena: RelayYard = Arena.new()
	world.add_child(arena)
	for _i in 4:
		await physics_frame
	var space := world.get_world_3d().direct_space_state
	var sources: Array[Vector3] = []
	if use_spawns:
		sources.assign(arena.defend_spawns)
	else:
		sources.assign(BotAI.DEFENDER_ANCHORS)
	var head := Vector3.UP * 1.62
	var rows: Array[String] = []
	var spawn_exposed: Array = []
	var total_cells: int = 0
	var exposed_cells: int = 0
	for z in range(24, -25, -1):
		var line := ""
		for x in range(-24, 25):
			var cell := Vector3(x, 0.05, z)
			var probe := PhysicsPointQueryParameters3D.new()
			probe.position = cell + Vector3.UP * 0.9
			probe.collision_mask = 3
			if not space.intersect_point(probe, 1).is_empty():
				line += "#"
				continue
			total_cells += 1
			var seen: int = 0
			for source in sources:
				if source.distance_to(cell) > range_limit:
					continue
				var query := PhysicsRayQueryParameters3D.create(source + head, cell + head, 3)
				if space.intersect_ray(query).is_empty():
					seen += 1
			if seen > 0:
				exposed_cells += 1
			line += str(mini(seen, 9)) if seen > 0 else "."
		rows.append(line)
	for site_index in arena.sites.size():
		var site: Vector3 = arena.sites[site_index]
		var r: int = 24 - int(round(site.z))
		var c: int = int(round(site.x)) + 24
		rows[r] = rows[r].substr(0, c) + ("A" if site_index == 0 else "B") + rows[r].substr(c + 1)
	for spawn in arena.attack_spawns:
		var r2: int = 24 - int(round(spawn.z))
		var c2: int = int(round(spawn.x)) + 24
		var seen_spawn: int = 0
		for source in sources:
			var query2 := PhysicsRayQueryParameters3D.create(source + head, spawn + head, 3)
			if source.distance_to(spawn) <= range_limit and space.intersect_ray(query2).is_empty():
				seen_spawn += 1
		check(not assert_rules or seen_spawn == 0, "a defender hold position has a line to attacker spawn %s" % spawn)
		spawn_exposed.append({"spawn": spawn, "sources_with_line": seen_spawn, "nearest_source_m": snappedf(sources.map(func(s: Vector3) -> float: return s.distance_to(spawn)).min(), 0.1)})
		if r2 >= 0 and r2 < rows.size():
			rows[r2] = rows[r2].substr(0, c2) + "S" + rows[r2].substr(c2 + 1)
	print("SIGHTLINE_MAP range=%.0f sources=%s (digit = sources with line, . = none, # = solid, S = attacker spawn, A/B = sites)" % [range_limit, "defender_spawns" if use_spawns else "defender_anchors"])
	for line in rows:
		print(line)
	print("SIGHTLINE_SPAWNS " + JSON.stringify(spawn_exposed))
	# Route length over the bot navigation graph (what a bot actually walks), per spawn to each site.
	var paths: Dictionary = {}
	for from_name in ["attack", "defend"]:
		var spawns: Array[Vector3] = arena.attack_spawns if from_name == "attack" else arena.defend_spawns
		for site_index in arena.sites.size():
			var lengths: Array = []
			var exposure: Array = []
			for spawn in spawns:
				var route: PackedVector3Array = arena._navigation.get_point_path(arena._navigation.get_closest_point(spawn), arena._navigation.get_closest_point(arena.sites[site_index]))
				var total: float = 0.0
				var sampled: int = 0
				var exposed: int = 0
				var run: int = 0
				var longest: int = 0
				var run_start: Vector3 = Vector3.ZERO
				var runs: Array = []
				for i in range(1, route.size()):
					var leg: float = route[i - 1].distance_to(route[i])
					total += leg
					var steps: int = maxi(1, int(leg))
					for k in steps:
						var point: Vector3 = route[i - 1].lerp(route[i], float(k) / float(steps))
						var seen_here: bool = false
						for source in sources:
							if source.distance_to(point) <= range_limit and space.intersect_ray(PhysicsRayQueryParameters3D.create(source + head, point + head, 3)).is_empty():
								seen_here = true
								break
						sampled += 1
						if seen_here:
							exposed += 1
							if run == 0:
								run_start = point
							run += 1
							longest = maxi(longest, run)
						else:
							if run >= 8:
								runs.append("%d m from (%.0f, %.0f) to (%.0f, %.0f)" % [run, run_start.x, run_start.z, point.x, point.z])
							run = 0
				if run >= 8:
					runs.append("%d m from (%.0f, %.0f) to the site" % [run, run_start.x, run_start.z])
				if spawn == spawns[2]:
					print("SIGHTLINE_RUNS %s_to_%s centre spawn: %s" % [from_name, "A" if site_index == 0 else "B", "; ".join(runs)])
				if assert_rules and from_name == "attack":
					check(total >= ASSERT_MIN_ROUTE_M, "attacker route to site %d is %.1f m, under %.0f m" % [site_index, total, ASSERT_MIN_ROUTE_M])
					check(float(exposed) / maxf(1.0, float(sampled)) <= ASSERT_MAX_EXPOSED_FRACTION, "attacker route to site %d is %.0f%% exposed" % [site_index, 100.0 * float(exposed) / maxf(1.0, float(sampled))])
					check(longest <= ASSERT_MAX_EXPOSED_RUN_M, "attacker route to site %d has an unbroken exposed stretch of %d m" % [site_index, longest])
				lengths.append(snappedf(total, 0.1))
				exposure.append({"exposed_fraction": snappedf(float(exposed) / maxf(1.0, float(sampled)), 0.01), "longest_exposed_m": longest})
			paths["%s_to_%s" % [from_name, "A" if site_index == 0 else "B"]] = lengths
			paths["%s_to_%s_exposure" % [from_name, "A" if site_index == 0 else "B"]] = exposure
	print("SIGHTLINE_PATHS " + JSON.stringify(paths))
	print("SIGHTLINE_SUMMARY walkable_cells=%d cells_exposed_to_any_source=%d fraction=%.3f" % [total_cells, exposed_cells, float(exposed_cells) / maxf(1.0, float(total_cells))])
	world.queue_free()
	await process_frame
	if assert_rules:
		print("MAP_SIGHTLINE_TEST checks=%d failures=%d" % [checks, failures.size()])
		quit(0 if failures.is_empty() else 1)
	else:
		quit()
