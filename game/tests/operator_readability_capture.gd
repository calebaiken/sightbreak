extends SceneTree
## Can a player pick out an operator, in the sun and in the shade? Eight operators of both teams stand in a row of
## distances in front of a defender-spawn camera. Each frame is rendered twice, with and without the operators; the
## difference is the operator's silhouette, and the ring around it is its background. Contrast is Weber contrast in
## linear light, (operator - background) / background, per operator, with whether the sun reaches it.
##   --capture-dir=<dir> --prefix=<name> --tier=0..3 (default 1) --old-lighting (ambient 0.41, sun 1.18 as before M6)
##   --lighting=<ambient>,<sun> sets any pair. Fixture only: standing operators, no weapon or HUD, software rasteriser.
const EYE := Vector3(0.0, 1.62, 21.5)
const TARGET := Vector3(0.0, 1.3, -10.0)
## Distances from the camera at which one operator in the sun and one in the shade are wanted, where the yard has them.
const DISTANCES := [8.0, 12.0, 16.0, 20.0, 26.0, 32.0]
var output := "res://../builds/qa/operator-readability"
var prefix := "operators"
var tier := SBGraphicsQuality.MEDIUM
var ambient := -1.0
var sun_energy := -1.0

func _initialize() -> void:
	_run.call_deferred()

func _linear(c: Color) -> float:
	var l := c.srgb_to_linear()
	return 0.2126 * l.r + 0.7152 * l.g + 0.0722 * l.b

func _run() -> void:
	var size := Vector2i(1280, 720)
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture-dir="):
			output = argument.trim_prefix("--capture-dir=")
		elif argument.begins_with("--prefix="):
			prefix = argument.trim_prefix("--prefix=")
		elif argument.begins_with("--tier="):
			tier = int(argument.trim_prefix("--tier="))
		elif argument == "--old-lighting":
			ambient = 0.41
			sun_energy = 1.18
		elif argument.begins_with("--lighting="):
			var parts := argument.trim_prefix("--lighting=").split(",")
			ambient = float(parts[0])
			sun_energy = float(parts[1])
	root.content_scale_size = size
	root.size = size
	DirAccess.make_dir_recursive_absolute(output)
	SBGraphicsQuality.current = tier
	var world := Node3D.new()
	root.add_child(world)
	world.add_child(RelayYard.new())
	var camera := Camera3D.new()
	camera.fov = 82.0
	camera.near = 0.05
	camera.far = 200.0
	world.add_child(camera)
	camera.current = true
	SBGraphicsQuality.apply(world, root, tier, 1.0, false)
	var environment: Environment = world.find_children("*", "WorldEnvironment", true, false)[0].environment
	var sun: DirectionalLight3D = world.find_children("*", "DirectionalLight3D", true, false)[0]
	if ambient >= 0.0:
		environment.ambient_light_energy = ambient
		sun.light_energy = sun_energy
	await physics_frame
	await physics_frame
	var space := world.get_world_3d().direct_space_state
	var to_sun := sun.global_transform.basis.z
	# Every open floor point with a clear line from the camera, classified by whether the sun reaches a chest there.
	var candidates: Array[Dictionary] = []
	for gx in range(-10, 11, 1):
		for gz in range(-12, 20, 1):
			var at := Vector3(gx, 0.05, gz)
			var chest := at + Vector3(0, 1.1, 0)
			var body_clear := space.intersect_ray(PhysicsRayQueryParameters3D.create(at + Vector3(0, 2.2, 0), at + Vector3(0, 0.02, 0), 1)).is_empty()
			var sight := space.intersect_ray(PhysicsRayQueryParameters3D.create(EYE, chest, 1))
			if not body_clear or not sight.is_empty():
				continue
			var blocked := not space.intersect_ray(PhysicsRayQueryParameters3D.create(chest, chest + to_sun * 60.0, 1)).is_empty()
			candidates.append({"at": at, "shadowed": blocked, "distance": EYE.z - at.z})
	var bots: Array[SBActor] = []
	var used: Array[Vector3] = []
	for distance in DISTANCES:
		for want_shadow in [false, true]:
			var best := {}
			var best_error := 1.5
			for candidate in candidates:
				if candidate.shadowed != want_shadow:
					continue
				var error := absf(float(candidate.distance) - distance) + absf((candidate.at as Vector3).x) * 0.02
				var crowded := false
				for other in used:
					if Vector2(other.x, other.z).distance_to(Vector2(candidate.at.x, candidate.at.z)) < 1.6:
						crowded = true
				if not crowded and error < best_error:
					best = candidate
					best_error = error
			if best.is_empty():
				continue
			used.append(best.at)
			var bot := SBActor.new()
			bot.configure(10 + bots.size(), bots.size() % 2, "Fixture %d" % bots.size(), false)
			world.add_child(bot)
			bot.reset_for_round(best.at)
			bot.yaw = PI
			bot.rotation.y = PI
			bots.append(bot)
	camera.look_at_from_position(EYE, TARGET, Vector3.UP)
	for _i in 4:
		await process_frame
	for bot in bots:
		bot.tick_visual(0.016)
	await process_frame
	await RenderingServer.frame_post_draw
	var with_bots := root.get_texture().get_image()
	with_bots.save_png(output.path_join("%s-with.png" % prefix))
	for bot in bots:
		bot.visible = false
	await process_frame
	await RenderingServer.frame_post_draw
	var without := root.get_texture().get_image()
	without.save_png(output.path_join("%s-without.png" % prefix))
	var rows := []
	for bot in bots:
		var chest: Vector3 = bot.global_position + Vector3(0, 1.1, 0)
		var query := PhysicsRayQueryParameters3D.create(chest, chest + to_sun * 60.0, 1)
		var shadowed := not world.get_world_3d().direct_space_state.intersect_ray(query).is_empty()
		var feet := camera.unproject_position(bot.global_position)
		var head := camera.unproject_position(bot.global_position + Vector3(0, 1.9, 0))
		var half_width := absf(camera.unproject_position(bot.global_position + Vector3(0.55, 1.0, 0)).x - feet.x)
		var box := Rect2i(Vector2i(int(feet.x - half_width * 1.6), int(head.y - 6)), Vector2i(int(half_width * 3.2), int(feet.y - head.y + 12)))
		box = box.intersection(Rect2i(Vector2i.ZERO, size))
		var inside := 0.0
		var inside_count := 0
		var ring := 0.0
		var ring_count := 0
		for y in range(box.position.y, box.end.y):
			for x in range(box.position.x, box.end.x):
				var a := with_bots.get_pixel(x, y)
				var b := without.get_pixel(x, y)
				if absf(a.r - b.r) + absf(a.g - b.g) + absf(a.b - b.b) > 0.06:
					inside += _linear(a)
					inside_count += 1
				else:
					ring += _linear(b)
					ring_count += 1
		var operator_lum := inside / maxf(1.0, inside_count)
		var background_lum := ring / maxf(1.0, ring_count)
		var row := {"distance": EYE.z - bot.global_position.z, "x": bot.global_position.x, "team": bot.team, "shadowed": shadowed, "mask_px": inside_count,
			"operator_lin": snappedf(operator_lum, 0.0001), "background_lin": snappedf(background_lum, 0.0001),
			"weber": snappedf((operator_lum - background_lum) / maxf(0.0001, background_lum), 0.001)}
		rows.append(row)
		print("OPERATOR_METRIC ", JSON.stringify(row))
	var file := FileAccess.open(output.path_join("%s-metrics.json" % prefix), FileAccess.WRITE)
	file.store_string(JSON.stringify({"tier": tier, "ambient": environment.ambient_light_energy, "sun": sun.light_energy, "rows": rows}, "\t"))
	file.close()
	world.queue_free()
	await process_frame
	quit()
