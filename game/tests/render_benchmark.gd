extends SceneTree
# Fixed-work software-render diagnostic, not a device FPS benchmark.
var output_dir := ""
var quality := "standard"
var render_scale := 1.0
var sample_count := 24
var warmup_count := 8
var animations: Array = []
var failures := 0
func _initialize() -> void: call_deferred("run")
func draw_frame() -> void:
	for actor in animations:
		actor.tick_visual(1.0 / 60.0)
	await process_frame
	await RenderingServer.frame_post_draw
func run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("A native rendering display is required")
		quit(2)
		return
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output_dir = arg.trim_prefix("--output=")
		if arg.begins_with("--quality="): quality = arg.trim_prefix("--quality=")
		if arg.begins_with("--samples="): sample_count = maxi(12, int(arg.trim_prefix("--samples=")))
		if arg.begins_with("--scale="): render_scale = clampf(float(arg.trim_prefix("--scale=")), 0.5, 1.0)
	if output_dir.is_empty():
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(output_dir)
	root.size = Vector2i(1280, 720)
	root.content_scale_size = Vector2i(1280, 720)
	root.msaa_3d = Viewport.MSAA_2X if quality == "standard" else Viewport.MSAA_DISABLED
	root.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	root.scaling_3d_scale = render_scale
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	var start := Time.get_ticks_usec()
	var world := Node3D.new()
	root.add_child(world)
	var arena = load("res://scripts/gameplay/arena.gd").new()
	world.add_child(arena)
	if arena.has_method("apply_detail_quality"): arena.apply_detail_quality(quality == "standard")
	for light in arena.find_children("*", "DirectionalLight3D", true, false): light.shadow_enabled = quality == "standard"
	var actor_script = load("res://scripts/gameplay/actor.gd")
	var actor = actor_script.new()
	actor.configure(1, 0, "Fixed rendering fixture", true)
	world.add_child(actor)
	actor.credits = 5000
	actor.buy_weapon("rifle")
	animations.append(actor)
	for i in 4:
		var other = actor_script.new()
		other.configure(i + 2, i % 2, "Fixed operator", false)
		world.add_child(other)
		other.reset_for_round(Vector3(-16 + i * 1.3, 0, -7 + i % 2))
		other.yaw = 0.18 * i
		other.rotation.y = other.yaw
		animations.append(other)
	var construction_ms := (Time.get_ticks_usec() - start) / 1000.0
	var views := [
		{"name": "approach", "at": Vector3(-14, 0, -18), "yaw": PI, "pitch": -0.12},
		{"name": "site", "at": Vector3(-16, 0, 3), "yaw": PI + 0.13, "pitch": -0.10},
		{"name": "overview", "at": Vector3(18, 8, -18), "yaw": PI * 0.76, "pitch": -0.42},
		{"name": "operators", "at": Vector3(-14, 0, -11), "yaw": PI, "pitch": -0.10}
	]
	var results := []
	for view in views:
		actor.reset_for_round(view.at)
		actor.yaw = view.yaw
		actor.pitch = view.pitch
		actor.rotation.y = view.yaw
		actor.camera.rotation.x = view.pitch
		actor._gun.visible = view.name != "overview" and view.name != "operators"
		var first_start := Time.get_ticks_usec()
		await draw_frame()
		var first_frame_ms := (Time.get_ticks_usec() - first_start) / 1000.0
		for i in warmup_count: await draw_frame()
		var frames: Array[float] = []
		for i in sample_count:
			var frame_start := Time.get_ticks_usec()
			await draw_frame()
			frames.append((Time.get_ticks_usec() - frame_start) / 1000.0)
		frames.sort()
		var sum := 0.0
		for value in frames: sum += value
		var result := {"view": view.name, "samples": sample_count, "first_present_ms": first_frame_ms, "median_frame_ms": frames[frames.size() / 2], "mean_frame_ms": sum / frames.size(), "p95_frame_ms": frames[mini(frames.size()-1,int(ceil(frames.size()*0.95))-1)], "p99_frame_ms": frames[-1], "draw_calls": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), "primitives": Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME), "texture_bytes": RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED), "static_bytes": Performance.get_monitor(Performance.MEMORY_STATIC)}
		results.append(result)
		if root.get_texture().get_image().save_png(output_dir.path_join(view.name + ".png")) != OK: failures += 1
	var report := {"context": "Linux Xvfb / Mesa llvmpipe CPU rendering; fixed synthetic camera/actors. NOT physical GPU/mobile FPS, thermal or battery evidence.", "engine": Engine.get_version_info().string, "renderer": RenderingServer.get_video_adapter_name(), "quality": quality, "render_scale": render_scale, "viewport": [1280, 720], "warmup_frames": warmup_count, "construction_ms": construction_ms, "views": results}
	var file := FileAccess.open(output_dir.path_join("metrics.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"\t"))
	file.close()
	animations.clear()
	world.queue_free()
	for i in 4:
		await process_frame
		await RenderingServer.frame_post_draw
	print("RENDER_BENCHMARK ", JSON.stringify(report))
	quit(1 if failures else 0)
