extends SceneTree
## Bullet impacts on Relay Yard's four surface families, at eye level, as a player sees them: a burst of hits on a
## concrete wall, a steel container, a plain crate and the asphalt, captured in the instant after the burst (sparks and
## dust) and again once the particles have gone (what stays). Uses only SBCombatEffects.impact, so the same script
## runs on a build with and without bullet holes.
##   --capture-dir=<dir> --prefix=<name> --tier=0..3 (default 1) --size=WxH (default 1280x720)
const SCENES := [
	# name, eye, look-at, hit centre, hit normal, spread axis
	["concrete-near", Vector3(-19.5, 1.62, -3.5), Vector3(-23.5, 1.5, -3.5), Vector3(-23.5, 1.5, -3.5), Vector3.RIGHT, Vector3.BACK],
	["concrete-far", Vector3(-10.0, 1.62, -3.5), Vector3(-23.5, 1.5, -3.5), Vector3(-23.5, 1.5, -3.5), Vector3.RIGHT, Vector3.BACK],
	["metal-near", Vector3(-1.0, 1.62, -11.0), Vector3(-5.5, 1.5, -11.0), Vector3(-5.5, 1.5, -11.0), Vector3.RIGHT, Vector3.BACK],
	["metal-far", Vector3(4.0, 1.62, -11.0), Vector3(-5.5, 1.5, -11.0), Vector3(-5.5, 1.5, -11.0), Vector3.RIGHT, Vector3.BACK],
	["crate-near", Vector3(0.0, 1.62, 3.0), Vector3(0.0, 0.7, 6.75), Vector3(0.0, 0.7, 6.75), Vector3.FORWARD, Vector3.RIGHT],
	["crate-far", Vector3(0.0, 1.62, -4.0), Vector3(0.0, 0.7, 6.75), Vector3(0.0, 0.7, 6.75), Vector3.FORWARD, Vector3.RIGHT],
	["asphalt-near", Vector3(11.0, 1.62, -1.0), Vector3(11.0, 0.0, -4.5), Vector3(11.0, 0.0, -4.5), Vector3.UP, Vector3.RIGHT],
	["asphalt-far", Vector3(11.0, 1.62, 8.0), Vector3(11.0, 0.0, -4.5), Vector3(11.0, 0.0, -4.5), Vector3.UP, Vector3.RIGHT],
]
var output := "res://../builds/qa/impact-presentation"
var prefix := "impact"
var tier := SBGraphicsQuality.MEDIUM

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var size := Vector2i(1280, 720)
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture-dir="):
			output = argument.trim_prefix("--capture-dir=")
		elif argument.begins_with("--prefix="):
			prefix = argument.trim_prefix("--prefix=")
		elif argument.begins_with("--tier="):
			tier = int(argument.trim_prefix("--tier="))
		elif argument.begins_with("--size="):
			var parts := argument.trim_prefix("--size=").split("x")
			if parts.size() == 2:
				size = Vector2i(int(parts[0]), int(parts[1]))
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
	var effects := SBCombatEffects.for_world(world)
	if effects.has_method("apply_graphics"):
		effects.apply_graphics(SBGraphicsQuality.config(tier))
	# Software rendering gives frames of 0.3 s or more, which would age a 0.2 s spark out between two frames. The
	# effects are stepped by hand at 60 Hz instead, so what is captured is what a player's frame shows.
	effects.set_process(false)
	for scene in SCENES:
		camera.look_at_from_position(scene[1], scene[2], Vector3.UP)
		for _i in 3:
			await process_frame
		var rng := RandomNumberGenerator.new()
		rng.seed = 20261024
		# A short burst, the way a rifle spray lands: a tight wandering group, one hit every few frames.
		for shot in 9:
			var spread: Vector3 = scene[5]
			var lift := Vector3.UP if absf(scene[4].y) < 0.9 else Vector3.BACK
			var at: Vector3 = scene[3] + spread * rng.randf_range(-0.5, 0.5) + lift * rng.randf_range(-0.35, 0.35) * (1.0 if absf(scene[4].y) < 0.9 else 0.3)
			effects.impact(at, scene[4], false)
			# One shot every 0.1 s, the pace of the rifle and the SMG.
			for _step in (6 if shot < 8 else 2):
				effects._process(1.0 / 60.0)
		await process_frame
		await RenderingServer.frame_post_draw
		_save(scene[0], "burst")
		# Let the sparks and dust finish (0.34 s at most), then record what is left on the surface.
		for _step in 90:
			effects._process(1.0 / 60.0)
		await process_frame
		await RenderingServer.frame_post_draw
		_save(scene[0], "after")
		if effects.has_method("clear_holes"):
			effects.clear_holes()
	world.queue_free()
	await process_frame
	quit()

func _save(name: String, stage: String) -> void:
	var image := root.get_texture().get_image()
	var path := output.path_join("%s-%s-%s.png" % [prefix, name, stage])
	if image.save_png(path) != OK:
		push_error("Capture failed: " + path)
	print("IMPACT_VIEW %s %s %dx%d draw_calls=%d primitives=%d" % [name, stage, image.get_width(), image.get_height(), int(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)), int(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME))])
