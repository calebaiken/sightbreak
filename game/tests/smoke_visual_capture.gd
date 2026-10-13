extends SceneTree
## Fixed-camera smoke review frames (requires a display). Identical script for
## before/after comparison; also reports how much of an inside-the-cloud view is
## occluded, so presentation changes cannot quietly weaken concealment.
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
var output := ""

func _initialize() -> void:
	_run.call_deferred()

func shot(name: String) -> Image:
	for i in 3: await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	if not output.is_empty():
		image.save_png(output.path_join(name + ".png"))
	print("SMOKE CAPTURE: " + name)
	return image

func _red_pixels(image: Image) -> int:
	var count := 0
	for y in range(0, image.get_height(), 2):
		for x in range(0, image.get_width(), 2):
			var c := image.get_pixel(x, y)
			if c.r > 0.6 and c.g < 0.25 and c.b < 0.25:
				count += 1
	return count

func _run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture-dir="):
			output = argument.trim_prefix("--capture-dir=")
		if argument == "--quality=low":
			SBUtility.high_quality_smoke = false
	if not output.is_empty():
		DirAccess.make_dir_recursive_absolute(output)
	root.size = Vector2i(1280, 720)
	root.msaa_3d = Viewport.MSAA_2X
	var world := Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	for i in range(3):
		var operator := Actor.new()
		operator.configure(10 + i, i % 2, "Smoke fixture")
		world.add_child(operator)
		operator.reset_for_round(Vector3(-2.5 + i * 2.5, 0.05, -1.5 + (i % 2) * 2.0))
		operator.rotation.y = PI * 0.15 * i
	var camera := Camera3D.new()
	world.add_child(camera)
	camera.fov = 70
	camera.current = true
	var smoke := SBUtility.new()
	smoke.kind = "smoke"
	world.add_child(smoke)
	smoke.global_position = Vector3(0, 0.2, 0)
	smoke._detonate()
	smoke.set_physics_process(false)
	await create_timer(1.2).timeout
	camera.position = Vector3(1.5, 1.7, -14)
	camera.look_at(Vector3(0, 1.4, 0))
	# Concealment probe: an operator behind the cloud must leave no visible trace.
	var hidden := Actor.new()
	hidden.configure(20, 1, "Concealed fixture")
	world.add_child(hidden)
	hidden.reset_for_round(Vector3(0.3, 0.05, 4.0))
	var with_target := await shot("smoke-mid")
	hidden.visible = false
	var without_target := await shot("smoke-mid-empty")
	# Count only inside the operator's projected bounds: the cloud rim animates
	# over time, so whole-frame differences would not isolate the operator.
	var bounds := Rect2(camera.unproject_position(hidden.global_position), Vector2.ZERO)
	for corner in [Vector3(-0.45, 0, -0.45), Vector3(0.45, 1.85, 0.45), Vector3(-0.45, 1.85, 0.45), Vector3(0.45, 0, -0.45)]:
		bounds = bounds.expand(camera.unproject_position(hidden.global_position + corner))
	bounds = bounds.grow(2).intersection(Rect2(Vector2.ZERO, Vector2(with_target.get_size())))
	var leaked := 0
	for y in range(int(bounds.position.y), int(bounds.end.y)):
		for x in range(int(bounds.position.x), int(bounds.end.x)):
			var a := with_target.get_pixel(x, y)
			var b := without_target.get_pixel(x, y)
			if absf(a.r - b.r) + absf(a.g - b.g) + absf(a.b - b.b) > 0.06:
				leaked += 1
	print("SMOKE_CONCEALMENT leaked_pixels=%d probe_area=%d" % [leaked, int(bounds.get_area())])
	hidden.queue_free()
	camera.position = Vector3(0.6, 1.6, -5.2)
	camera.look_at(Vector3(0, 1.6, 0))
	await shot("smoke-close")
	camera.position = Vector3(0.2, 1.6, 0.3)
	camera.look_at(Vector3(0, 1.5, -10))
	var inside := await shot("smoke-inside")
	# Inside the cloud the yard must not be legible: measure luminance variance.
	var values: Array[float] = []
	for y in range(0, inside.get_height(), 8):
		for x in range(0, inside.get_width(), 8):
			values.append(inside.get_pixel(x, y).get_luminance())
	var mean := 0.0
	for value in values: mean += value
	mean /= values.size()
	var variance := 0.0
	for value in values: variance += (value - mean) * (value - mean)
	variance /= values.size()
	print("SMOKE_INSIDE_LUMINANCE mean=%.3f stddev=%.4f" % [mean, sqrt(variance)])
	# One-way check: standing in a side lobe (beyond the central sphere) and looking
	# out, a bright marker just past the cloud edge must stay hidden, as it is from outside.
	var marker := MeshInstance3D.new()
	var marker_mesh := BoxMesh.new()
	marker_mesh.size = Vector3(0.3, 1.2, 1.2)
	marker.mesh = marker_mesh
	var marker_material := StandardMaterial3D.new()
	marker_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	marker_material.albedo_color = Color(1, 0, 0)
	marker.material_override = marker_material
	world.add_child(marker)
	var center := smoke.global_position
	assert(not SBUtility.core_contains(Vector3(3.45, 0.25, 0.55)) and SBUtility.core_contains(Vector3(2.2, 0.25, 0.55)))
	marker.global_position = center + Vector3(3.6, 0.25, 0.55)
	camera.global_position = center + Vector3(2.2, 0.25, 0.55)
	camera.look_at(marker.global_position)
	var looking_out := await shot("smoke-lobe-out")
	smoke.visible = false
	var control := await shot("smoke-lobe-control")
	smoke.visible = true
	print("SMOKE_LOBE_VIEW marker_pixels=%d control_pixels=%d" % [_red_pixels(looking_out), _red_pixels(control)])
	world.queue_free()
	for i in 3: await process_frame
	quit()
