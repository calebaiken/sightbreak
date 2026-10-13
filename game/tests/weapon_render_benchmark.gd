extends SceneTree
## Fixed-view cost of the first-person rifle: no weapon, procedural rifle, authored
## rifle with the static v2 hands, and authored rifle with the rigged arms (the
## default), alternated over several rounds on the same frame. A software-render
## diagnostic for relative cost only; it is not a device frame-rate measurement.
## Needs a native display. --rounds=N (default 3), --samples=N (default 40).
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const WeaponModel = preload("res://scripts/gameplay/weapon_model.gd")
var rounds := 3
var samples := 40

func _initialize() -> void:
	_run.call_deferred()

func _measure(actor: SBActor) -> Dictionary:
	for i in 8:
		actor.tick_visual(1.0 / 60.0)
		await process_frame
		await RenderingServer.frame_post_draw
	var times: Array[float] = []
	var draws := 0.0
	var primitives := 0.0
	for i in samples:
		var start := Time.get_ticks_usec()
		actor.tick_visual(1.0 / 60.0)
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
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--rounds="): rounds = maxi(1, int(argument.trim_prefix("--rounds=")))
		if argument.begins_with("--samples="): samples = maxi(12, int(argument.trim_prefix("--samples=")))
	root.size = Vector2i(1280, 720)
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	var world := Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	var actor := Actor.new()
	actor.configure(1, 0, "Benchmark fixture", true)
	world.add_child(actor)
	actor.reset_for_round(Vector3(3, 0.05, -12))
	actor.credits = 5000
	actor.buy_weapon("rifle")
	actor.yaw = 0.35
	actor.rotation.y = 0.35
	var results := {"none": [], "procedural": [], "static_hands": [], "authored": []}
	for round_index in rounds:
		for variant in ["none", "procedural", "static_hands", "authored"]:
			WeaponModel.use_authored = variant in ["static_hands", "authored"]
			WeaponModel.use_rigged_arms = variant == "authored"
			actor._build_gun()
			actor._gun.visible = variant != "none"
			results[variant].append(await _measure(actor))
	var summary := {"context": "Linux Xvfb / Mesa llvmpipe software rendering at 1280x720; relative cost only, NOT device FPS", "renderer": RenderingServer.get_video_adapter_name(), "rounds": rounds, "samples": samples}
	for variant in results:
		var medians: Array = results[variant].map(func(r): return r.median_ms)
		medians.sort()
		summary[variant] = {"draw_calls": results[variant][0].draw_calls, "primitives": results[variant][0].primitives, "median_of_medians_ms": medians[medians.size() / 2], "rounds_ms": medians}
	print("WEAPON_RENDER_BENCHMARK " + JSON.stringify(summary))
	quit()
