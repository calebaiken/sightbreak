extends SceneTree
var main
var start_time := 0
var previous_frame := 0
var timings: Array[float] = []
var completed := false
var output_dir := "/workspace/sightbreak/builds/qa"
func _initialize() -> void: call_deferred("run")
func run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("Render probe requires a real rendering display.")
		quit(2)
		return
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output_dir = arg.trim_prefix("--output=")
	var scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	main = scene
	main.start_match({"mode": "offline", "difficulty": "normal", "name": "Render probe"})
	main.match_game.time_left = 0.1
	main.match_game.local_actor().credits = 5000
	main.match_game.request_buy("rifle")
	start_time = Time.get_ticks_usec()
	previous_frame = start_time
func _process(_delta: float) -> bool:
	if main == null or completed: return false
	var now := Time.get_ticks_usec()
	if now - start_time > 2000000: timings.append((now - previous_frame) / 1000.0)
	previous_frame = now
	if now - start_time >= 10000000:
		completed = true
		finish.call_deferred()
	return false
func finish() -> void:
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(output_dir)
	root.get_texture().get_image().save_png(output_dir.path_join("combat-final.png"))
	timings.sort()
	var total := 0.0
	for t in timings: total += t
	var mean := total / maxf(1, timings.size())
	var results := {"context": "Native Linux Xvfb; Mesa llvmpipe CPU software rendering. NOT physical mobile performance.", "godot": Engine.get_version_info().string,
		"renderer": RenderingServer.get_video_adapter_name(), "resolution": [root.size.x, root.size.y], "sample_frames": timings.size(),
		"sample_seconds": total / 1000, "mean_frame_ms": mean, "p95_frame_ms": timings[int(timings.size() * 0.95)],
		"mean_fps": 1000.0 / mean, "draw_calls": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
		"primitives": Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME), "memory_static_bytes": Performance.get_monitor(Performance.MEMORY_STATIC)}
	var file := FileAccess.open(output_dir.path_join("render-metrics.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(results, "\t"))
	file.close()
	print("NATIVE_RENDER_PROBE ", JSON.stringify(results))
	main.queue_free()
	main = null
	for i in 5:
		await process_frame
		await RenderingServer.frame_post_draw
	quit(0)
