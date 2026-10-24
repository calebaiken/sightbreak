extends SceneTree
func _initialize() -> void:
	_run.call_deferred()
func _grab() -> Image:
	await process_frame
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image()
func _run() -> void:
	root.size = Vector2i(640, 360)
	var world := Node3D.new()
	root.add_child(world)
	world.add_child(RelayYard.new())
	var camera := Camera3D.new()
	world.add_child(camera)
	camera.current = true
	var effects := SBCombatEffects.for_world(world)
	effects.set_process(false)
	camera.look_at_from_position(Vector3(11, 1.62, -1), Vector3(11, 0.0, -4.5), Vector3.UP)
	for _i in 3: await process_frame
	var base: Image = await _grab()
	for tint in [Color("ffffff"), Color("706e66"), Color("5e6266"), Color("4a4e50"), Color("7a7258")]:
		effects._emit("dust", Vector3(11, 0.3, -4.5), Vector3.ZERO, 5.0, -INF, tint, 2.0)
		effects._process(0.01)
		var image: Image = await _grab()
		var sum := Vector3.ZERO
		var count := 0
		for y in range(image.get_height()):
			for x in range(image.get_width()):
				var a := base.get_pixel(x, y)
				var b := image.get_pixel(x, y)
				if absf(a.r - b.r) + absf(a.g - b.g) + absf(a.b - b.b) > 0.1:
					sum += Vector3(b.r, b.g, b.b)
					count += 1
		image.save_png("/tmp/claude-0/-home-user-sightbreak/dfa39eb1-8f79-5aa4-a243-6ac88bc445cd/scratchpad/gfx/probe/dust-%s.png" % tint.to_html(false))
		print("DUST_PROBE tint=%s pixels=%d mean=%s" % [tint.to_html(false), count, (sum / maxf(1.0, count)).snappedf(0.01)])
		pass
		effects._process(6.0)
	quit()
