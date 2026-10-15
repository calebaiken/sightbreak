extends SceneTree
## What the reload and the first shots cost, measured on this host (Mesa llvmpipe under Xvfb, software rendering):
## the triangle counts of everything the first-person weapon draws, draw calls and primitives per frame in four states
## (ready, mid-reload, a muzzle flash, the smoke after it), the CPU time of Actor.tick_visual per tick through a whole
## reload (the animation's own cost: skeleton seek, magazine poses, audio scheduling, without any drawing), and the size
## of the textures the viewmodel keeps resident (the imported, VRAM-compressed files). Relative numbers on one host only:
## llvmpipe's cost is dominated by the CPU's rasteriser and says nothing about a phone's GPU, battery or heat.
## Needs a native display.   --samples=N frames per state (default 30)   --size=WxH (default 1280x720)
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const Weapons = preload("res://scripts/gameplay/weapons.gd")
const TICK := 1.0 / 60.0
var samples := 30

func _initialize() -> void:
	_run.call_deferred()

func _triangles(mesh: Mesh) -> int:
	var total := 0
	for surface in mesh.get_surface_count():
		var arrays := mesh.surface_get_arrays(surface)
		total += (arrays[Mesh.ARRAY_INDEX] as PackedInt32Array).size() / 3 if arrays[Mesh.ARRAY_INDEX] != null and (arrays[Mesh.ARRAY_INDEX] as PackedInt32Array).size() > 0 else (arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array).size() / 3
	return total

func _frame_stats(actor: SBActor, prepare: Callable) -> Dictionary:
	var times: Array[float] = []
	var draws := 0.0
	var primitives := 0.0
	for i in 6:
		prepare.call(i)
		await process_frame
		await RenderingServer.frame_post_draw
	for i in samples:
		prepare.call(i + 6)
		var start := Time.get_ticks_usec()
		await process_frame
		await RenderingServer.frame_post_draw
		times.append((Time.get_ticks_usec() - start) / 1000.0)
		draws = RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)
		primitives = RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)
	times.sort()
	return {"draw_calls": draws, "primitives": primitives, "median_ms": times[times.size() / 2], "p95_ms": times[int(times.size() * 0.95)]}

func _run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("A native rendering display is required")
		quit(2)
		return
	var size := Vector2i(1280, 720)
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--samples="):
			samples = maxi(10, int(argument.trim_prefix("--samples=")))
		elif argument.begins_with("--size="):
			var parts := argument.trim_prefix("--size=").split("x")
			size = Vector2i(int(parts[0]), int(parts[1]))
	root.content_scale_size = size
	root.size = size
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	var world := Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	var actor := Actor.new()
	actor.configure(1, 0, "Perf probe", true)
	world.add_child(actor)
	actor.reset_for_round(Vector3(3, 0.05, -12))
	actor.credits = 5000
	actor.buy_weapon("rifle")
	actor._equip_blend = 0
	actor.yaw = 0.35
	actor.rotation.y = 0.35
	actor.camera.rotation.x = -0.025
	actor.ammo = 10
	actor.reserve = 90
	for i in 6:
		await process_frame
	var report := {"context": "Linux Xvfb / Mesa llvmpipe software rendering at %dx%d; relative cost only, NOT device performance" % [size.x, size.y], "renderer": RenderingServer.get_video_adapter_name()}
	# Triangles of what the first-person weapon draws.
	var parts := {}
	var total := 0
	for node: MeshInstance3D in actor._gun.find_children("*", "MeshInstance3D", true, false):
		if node.mesh == null:
			continue
		var count := _triangles(node.mesh)
		parts[node.name] = count
		total += count
	report["triangles"] = parts
	report["triangles_total_nodes"] = total
	report["viewmodel_draw_nodes"] = actor._gun.get_child_count()
	# The animation's CPU cost per tick through a whole reload (no drawing in this loop).
	var seconds := float(Weapons.get_weapon("rifle")["reload"])
	var tick_us: Array[float] = []
	actor.reload_remaining = 0.0
	actor.tick_visual(TICK)
	for tick in int(seconds / TICK) + 1:
		actor.reload_remaining = maxf(seconds - float(tick) * TICK, 0.001)
		var start := Time.get_ticks_usec()
		actor.tick_visual(TICK)
		tick_us.append(float(Time.get_ticks_usec() - start))
	actor.reload_remaining = 0.0
	actor.tick_visual(TICK)
	var idle_us: Array[float] = []
	for tick in 120:
		var start := Time.get_ticks_usec()
		actor.tick_visual(TICK)
		idle_us.append(float(Time.get_ticks_usec() - start))
	tick_us.sort()
	idle_us.sort()
	report["tick_visual_us_reload"] = {"median": tick_us[tick_us.size() / 2], "p95": tick_us[int(tick_us.size() * 0.95)], "max": tick_us.back()}
	report["tick_visual_us_idle"] = {"median": idle_us[idle_us.size() / 2], "p95": idle_us[int(idle_us.size() * 0.95)], "max": idle_us.back()}
	# Frames in four states.
	report["ready"] = await _frame_stats(actor, func(_i): actor.reload_remaining = 0.0; actor.tick_visual(TICK))
	report["mid_reload"] = await _frame_stats(actor, func(_i): actor.reload_remaining = seconds * 0.5; actor._reload_clock = seconds * 0.5; actor.tick_visual(0.001))
	report["flash"] = await _frame_stats(actor, func(_i): actor.reload_remaining = 0.0; actor.play_shot_effect(); actor.tick_visual(0.004))
	report["smoke"] = await _frame_stats(actor, func(_i): actor.reload_remaining = 0.0; actor._flash = 0.0; actor._smoke_age = 0.12; actor.tick_visual(0.001))
	# Texture memory the viewmodel keeps resident: the imported (compressed) textures of the rifle and the arms.
	var textures := {}
	var texture_bytes := 0
	for name in ["relay_ar_albedo", "relay_ar_orm", "relay_ar_normal", "relay_ar_arms_albedo", "relay_ar_arms_orm", "relay_ar_arms_normal"]:
		var path := "res://assets/weapons/relay_ar/%s.png" % name
		var imported := ProjectSettings.globalize_path("res://.godot/imported/%s.png-%s.ctex" % [name, path.md5_text()])
		var bytes := FileAccess.get_file_as_bytes(imported).size() if FileAccess.file_exists(imported) else -1
		textures[name] = bytes
		texture_bytes += maxi(bytes, 0)
	report["texture_bytes"] = textures
	report["texture_bytes_total"] = texture_bytes
	print("RELOAD_PERF " + JSON.stringify(report))
	quit()
