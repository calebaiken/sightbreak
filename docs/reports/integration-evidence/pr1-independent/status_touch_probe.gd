extends SceneTree
func _initialize() -> void: run.call_deferred()
func settle() -> void:
	for i in 6: await process_frame
func run() -> void:
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	main.profile.data.settings.touch_visible = true
	main.profile.data.settings.hud_positions = {}
	await settle()
	for scale in [1.0, 1.3]:
		main.profile.data.settings.ui_text_scale = scale
		for dimensions in [Vector2i(960, 720), Vector2i(1280, 720), Vector2i(1560, 720), Vector2i(1600, 720)]:
			root.content_scale_size = dimensions
			root.size = dimensions
			main.start_match({"mode":"offline", "difficulty":"easy", "name":"Independent touch probe"})
			await settle()
			main.match_game.set_physics_process(false)
			for phase in ["buy", "live"]:
				main.match_game.phase = phase
				main._process(0.01)
				await settle()
				var overlaps := []
				var glyph_size: Vector2 = main.status_label.get_theme_font("font").get_string_size(main.status_label.text, HORIZONTAL_ALIGNMENT_LEFT, -1, main.status_label.get_theme_font_size("font_size"))
				var status_box: Rect2 = main.status_label.get_global_rect()
				var glyph_box := Rect2(Vector2(status_box.get_center().x - glyph_size.x / 2.0, status_box.position.y), glyph_size)
				for action in main.touch.positions:
					var point: Vector2 = main.touch.control_point(action)
					var radius: float = main.touch.radius(action)
					if Rect2(point - Vector2.ONE * radius, Vector2.ONE * radius * 2).intersects(glyph_box): overlaps.append(action)
				print(JSON.stringify({"dimensions":str(dimensions),"scale":scale,"phase":phase,"overlaps":overlaps,"status_rect":str(main.status_label.get_global_rect()), "glyph_rect":str(glyph_box),"text":main.status_label.text}))
			main.leave_match()
			await settle()
	main.queue_free()
	await settle()
	quit()
