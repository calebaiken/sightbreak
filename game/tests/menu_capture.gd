extends SceneTree
## Native capture tool (not a test): the main menu at the sizes and states the menu work is
## judged at. CAP_OUT=dir DISPLAY=:99 godot --rendering-method gl_compatibility --script res://tests/menu_capture.gd
## Account states come from the backend-derived fixture; the wide canvases are what a wider
## window would frame, not the shipped aspect behaviour.
func _initialize() -> void:
	call_deferred("run")

func frames(count: int) -> void:
	for i in count:
		await process_frame

func run() -> void:
	var out := OS.get_environment("CAP_OUT")
	DirAccess.make_dir_recursive_absolute(out)
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await frames(3)
	main.open_economy("inventory")
	await frames(2)
	var panel = main.economy_panel
	var world: Dictionary = (JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/backend_world.json")) as Dictionary).world
	for spec in [[Vector2i(1280, 720), 1.0, "ready"], [Vector2i(960, 720), 1.3, "ready"], [Vector2i(1280, 720), 1.0, "unavailable"], [Vector2i(1560, 720), 1.0, "signed_out"], [Vector2i(960, 720), 1.0, "expired"]]:
		var size: Vector2i = spec[0]
		root.content_scale_size = size
		root.size = size
		main.profile.data.settings.ui_text_scale = spec[1]
		main.ui.theme = main.build_theme()
		panel.api.token = "fixture-only" if spec[2] in ["ready", "unavailable"] else ""
		panel.session_expired = spec[2] == "expired"
		panel.account = (world.account as Dictionary).duplicate(true) if spec[2] == "ready" else {}
		panel.load_error = "Could not connect to the server" if spec[2] == "unavailable" else ""
		main.show_menu()
		await frames(8)
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("%s/menu-%dx%d-%d-%s.png" % [out, size.x, size.y, int(spec[1] * 100), spec[2]])
	main.queue_free()
	await frames(2)
	quit(0)
