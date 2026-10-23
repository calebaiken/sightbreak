extends SceneTree
var failures := 0
var checks := 0
var capture_dir := ""
const LONGEST := "Match complete; account reward submission failed. Server logs identify the match for review."
func _initialize() -> void: run.call_deferred()
func settle(n := 12) -> void:
	for i in n: await process_frame
func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures += 1
		push_error(message)
func target(main: Node, action: String) -> Rect2:
	var radius: float = main.touch.radius(action)
	return Rect2(main.touch.global_position + main.touch.control_point(action) - Vector2.ONE * radius, Vector2.ONE * radius * 2)
func measure(main: Node) -> Dictionary:
	var label: Label = main.status_label
	var rect := label.get_global_rect()
	var glyphs: Vector2 = label.get_theme_font("font").get_multiline_string_size(label.text, HORIZONTAL_ALIGNMENT_CENTER, rect.size.x, label.get_theme_font_size("font_size"))
	var block := Rect2(rect.position.x + (rect.size.x - glyphs.x) * 0.5, rect.position.y, glyphs.x, glyphs.y)
	var overlaps := []
	for action in main.touch.positions:
		if action != "move" and main.touch.enabled and target(main, action).intersects(block): overlaps.append(action)
	var bounds := Rect2(Vector2.ZERO, Vector2(root.content_scale_size))
	return {"label": str(rect), "block": str(block), "lines": label.get_line_count(), "overlaps": overlaps,
		"on_screen": bounds.encloses(block), "label_on_screen":bounds.encloses(rect), "line_height":label.get_line_height(), "score":str(main.score_label.get_global_rect()),
		"ammo_on_screen":bounds.encloses(main.ammo_label.get_global_rect()), "health_on_screen":bounds.encloses(main.health_label.get_global_rect())}
func apply_custom(_main: Node, _mode: String) -> void:
	pass # Exercise the persisted HUD restore path instead.
func run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture-dir="):
			capture_dir = argument.trim_prefix("--capture-dir=")
			DirAccess.make_dir_recursive_absolute(capture_dir)
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	main.profile.data.settings.touch_visible = true
	main.profile.data.settings.hud_positions = {}
	main.profile.data.settings.ui_text_scale = 1.3
	await settle()
	var cases := [["narrow_center",960,1.0]]
	for test in cases:
		var mode: String = test[0]
		root.content_scale_size = Vector2i(test[1],720)
		root.size = root.content_scale_size
		main.profile.data.settings.hud_scale = test[2]
		main.profile.data.settings.hud_positions = {"grenade":[0.459375,0.82], "smoke":[0.540625,0.82]}
		main.start_match({"mode":"offline", "difficulty":"easy", "name":"Independent status review"})
		await settle()
		main.match_game.set_physics_process(false)
		apply_custom(main,mode)
		for prompt in ["buy"]:
			main.match_game.phase = "buy" if prompt == "buy" else "live"
			if prompt != "buy": main.show_notification(LONGEST)
			main._process(0.01)
			await settle(20)
			var sample: Dictionary = measure(main)
			var observed_rects: Array[String] = []
			for observed_frame in 12:
				await process_frame
				var observed_rect: String = str(main.status_label.get_global_rect())
				if not observed_rects.has(observed_rect): observed_rects.append(observed_rect)
			var second: Dictionary = measure(main)
			var stable: bool = observed_rects.size() == 1
			var context := "%s %dx720 hud%.1f %s" % [mode,test[1],test[2],prompt]
			print("STATUS_EDGE "+JSON.stringify({"case":context,"measure":second,"stable":stable, "observed_rects":observed_rects}))
			check(second.overlaps.is_empty(), context+": clears all drawn targets")
			check(second.on_screen and second.label_on_screen, context+": text and its laid-out label remain inside viewport")
			check(second.ammo_on_screen and second.health_on_screen, context+": bottom HUD remains inside viewport")
			check(stable, context+": layout settles without oscillation")
			if not capture_dir.is_empty() and DisplayServer.get_name() != "headless" and mode in ["default","narrow_center","no_free_span"]:
				for frame_index in 2:
					await RenderingServer.frame_post_draw
					var frame_name := "%s-%d-%s-%02d.png"%[mode,test[1],prompt,frame_index]
					print("STATUS_FRAME "+JSON.stringify({"file":frame_name,"measure":measure(main)}))
					root.get_texture().get_image().save_png(capture_dir.path_join(frame_name))
					await process_frame
		# The desktop fallback must restore the full row after custom fitting.
		main.touch.enabled = false
		main._process(0.01)
		await settle()
		if "status_row" in main:
			check(main.status_row.get_theme_constant("margin_left") == 0 and main.status_row.get_theme_constant("margin_right") == 0, mode+": disabled touch restores full span")
		main.leave_match()
		await settle()
	main.queue_free()
	await settle()
	print("STATUS_EDGE_TEST checks=%d failures=%d"%[checks,failures])
	quit(1 if failures else 0)
