extends SceneTree
var checks := 0
var failures := 0
var capture_dir := ""
func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures += 1
		push_error(message)
func _initialize() -> void: call_deferred("run")
func settle() -> void:
	for i in 6: await process_frame
func check_horizontal(node: Control, context: String) -> void:
	var overflowing: Array[String] = []
	for child in node.find_children("*", "Control", true, false):
		if not child.is_visible_in_tree(): continue
		var rect: Rect2 = child.get_global_rect()
		if rect.position.x < -1 or rect.end.x > node.size.x + 1:
			overflowing.append("%s:%s" % [child.get_class(), rect])
	check(overflowing.is_empty(), context + " stays inside landscape width: " + str(overflowing))
func capture(_main: Node, filename: String) -> void:
	if capture_dir.is_empty() or DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	var error := root.get_texture().get_image().save_png(capture_dir.path_join(filename + ".png"))
	check(error == OK, "Native screenshot written: " + filename)
func run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture-dir="):
			capture_dir = argument.trim_prefix("--capture-dir=")
			DirAccess.make_dir_recursive_absolute(capture_dir)
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	main.profile.data.settings.touch_visible = true
	main.profile.data.settings.hud_positions = {}
	await settle()
	for dimensions in [Vector2i(1280, 720), Vector2i(1600, 720), Vector2i(960, 720), Vector2i(1560, 720)]:
		root.content_scale_size = dimensions
		root.size = dimensions
		await settle()
		check(main.ui.size.is_equal_approx(Vector2(dimensions)), "Test uses requested logical landscape " + str(dimensions))
		for page in ["show_menu", "show_connect", "show_settings", "show_progress"]:
			main.call(page)
			await settle()
			check_horizontal(main.ui, str(dimensions) + " " + page)
			if page in ["show_menu", "show_settings"]: await capture(main, "%dx%d-%s" % [dimensions.x, dimensions.y, page])
			if page != "show_menu":
				var scrolls: Array[Node] = main.ui.find_children("ContentScroll", "ScrollContainer", true, false)
				check(scrolls.size() == 1, page + " has one vertical content scroller")
				var scroll: ScrollContainer = scrolls[0]
				check(scroll.get_global_rect().end.y <= dimensions.y + 1, page + " scroller stays above bottom safe margin")
		main.start_match({"mode": "offline", "difficulty": "normal", "name": "Landscape QA"})
		await settle()
		check_horizontal(main.ui, str(dimensions) + " combat HUD")
		check(main.crosshair.get_global_rect().get_center().is_equal_approx(Vector2(dimensions) * 0.5), "Reticle canvas remains at optical viewport center")
		check(absf(main.score_label.get_global_rect().get_center().x - dimensions.x * 0.5) < 1.0, "Match score stays horizontally centered independent of side labels")
		for control_name in main.touch.positions:
			var point: Vector2 = main.touch.control_point(control_name)
			var radius: float = main.touch.radius(control_name)
			check(point.x - radius >= 0 and point.y - radius >= 0 and point.x + radius <= dimensions.x and point.y + radius <= dimensions.y, control_name + " full touch target stays in landscape")
		await capture(main, "%dx%d-touch-hud" % [dimensions.x, dimensions.y])
		for action in ["grenade", "smoke"]:
			var point: Vector2 = main.touch.control_point(action)
			var radius: float = main.touch.radius(action)
			check(not Rect2(point - Vector2.ONE * radius, Vector2.ONE * radius * 2).intersects(main.status_label.get_global_rect()), action + " default button clears match instructions")
		var funds_rect: Rect2 = main.funds_label.get_global_rect()
		check(funds_rect.position.y >= 0 and funds_rect.end.y <= main.health_label.get_global_rect().position.y + 1, "Funds label sits on screen above the health readout")
		for control_name in main.touch.positions:
			var point: Vector2 = main.touch.control_point(control_name)
			var radius: float = main.touch.radius(control_name)
			check(not Rect2(point - Vector2.ONE * radius, Vector2.ONE * radius * 2).intersects(funds_rect), "Funds label clears the %s touch control" % control_name)
		var swap_point: Vector2 = main.touch.control_point("switch")
		check(swap_point.y + main.touch.radius("switch") < main.ammo_label.get_global_rect().position.y, "Swap button clears weapon/ammunition text")
		var pause_point: Vector2 = main.touch.control_point("pause")
		check(pause_point.x - main.touch.radius("pause") > main.action_label.get_global_rect().end.x, "Pause button clears device state text")
		check("TAP BUY" in main.status_label.text, "Mobile buy prompt names actual touch control")
		main.match_game.phase = "live"
		main.status_label.set_meta("until", 0.0)
		main._process(0.01)
		check(not "HOLD E " in main.status_label.text, "Mobile objective prompt has no keyboard-only action")
		main.show_buy()
		await settle()
		check_horizontal(main.ui, str(dimensions) + " requisition")
		main.close_overlay()
		main.touch_score_until = main.elapsed + 20
		main.show_scoreboard()
		await settle()
		check_horizontal(main.ui, str(dimensions) + " scoreboard")
		check(main.score_panel.get_global_rect().end.y <= dimensions.y, "All ten roster rows bounded by viewport")
		main.touch_score_until = 0
		main.open_touch_editor()
		await settle()
		check_horizontal(main.ui, str(dimensions) + " HUD editor")
		main.finish_touch_editor()
		main.leave_match()
		await settle()
	main.queue_free()
	await settle()
	print("LANDSCAPE_UI_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
