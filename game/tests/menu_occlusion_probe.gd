extends SceneTree
## Native controlled probe for geometry hidden underneath the opaque account UI.
var output := ""
func _initialize() -> void: call_deferred("run")
func settle(count: int) -> void:
	for i in count: await process_frame
func run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="): output = argument.trim_prefix("--output=")
	if output.is_empty() or DisplayServer.get_name() == "headless":
		push_error("Use a native graphical display and --output=/absolute/directory")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(output)
	root.content_scale_size = Vector2i(1280, 720)
	root.size = Vector2i(1280, 720)
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await settle(4)
	main.set_process(false) # Identical fixed camera throughout the comparison.
	main.open_economy("inventory")
	await settle(4)
	var results: Array = []
	for mode in ["visible-before", "hidden", "visible-after"]:
		main.menu_world.visible = mode != "hidden"
		await settle(4)
		var milliseconds: Array[float] = []
		var draws: Array[float] = []
		var triangles: Array[float] = []
		var previous := Time.get_ticks_usec()
		for i in 12:
			await RenderingServer.frame_post_draw
			var now := Time.get_ticks_usec()
			milliseconds.append(float(now - previous) / 1000.0)
			previous = now
			draws.append(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
			triangles.append(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME))
		milliseconds.sort()
		draws.sort()
		triangles.sort()
		var image_error := root.get_texture().get_image().save_png(output.path_join(mode + ".png"))
		results.append({"mode": mode, "samples": milliseconds.size(), "median_frame_ms": milliseconds[6], "p95_frame_ms": milliseconds[11], "median_draw_calls": draws[6], "median_primitives": triangles[6], "capture_error": image_error})
	main.menu_world.hide()
	main.show_menu()
	await settle(3)
	var restored: bool = main.menu_world.visible and not main.economy_panel.visible
	var file := FileAccess.open(output.path_join("measurements.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"renderer": RenderingServer.get_video_adapter_name(), "results": results, "menu_restored": restored, "scope": "Linux native software rendering only; static opaque account screen, no device performance claim"}, "\t"))
	file.close()
	main.queue_free()
	await settle(3)
	print("MENU_OCCLUSION_PROBE samples=36 restored=", restored)
	quit(0 if restored else 1)
