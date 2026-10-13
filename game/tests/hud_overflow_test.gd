extends SceneTree
## Codex PR #1 blocker 1: long display names in the kill feed must never widen the
## HUD, move the score or push the ammunition block off-screen. Runs headless in
## validate.sh; pass --capture-dir=<dir> on a display for native screenshots.
var checks := 0
var failures := 0
var capture_dir := ""
const SIZES := [Vector2i(960, 720), Vector2i(1180, 820), Vector2i(1280, 720), Vector2i(1560, 720), Vector2i(1600, 720)]
## Longest permitted names: the server keeps 24 characters (offline names allow 20).
const NAMES := {
	"ordinary": ["Rook", "Kestrel"],
	"max_ascii": ["WWWWWWWWWWWWWWWWWWWWWWWW", "MMMMMMMMMMMMMMMMMMMMMMMM"],
	"unicode": ["Zoë ✦ Ærøskøbing Ωmega Ü", "東京湾岸第七中継基地防衛隊長の名前です長い名"],
}

func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures += 1
		push_error(message)

func _initialize() -> void:
	call_deferred("run")

func settle() -> void:
	for i in 6: await process_frame

func inside(rect: Rect2, bounds: Rect2) -> bool:
	return rect.position.x >= bounds.position.x - 1 and rect.position.y >= bounds.position.y - 1 and rect.end.x <= bounds.end.x + 1 and rect.end.y <= bounds.end.y + 1

func capture(filename: String) -> void:
	if capture_dir.is_empty() or DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	check(root.get_texture().get_image().save_png(capture_dir.path_join(filename + ".png")) == OK, "native screenshot written: " + filename)

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
	for text_scale in [1.0, 1.3]:
		main.profile.data.settings.ui_text_scale = text_scale
		for dimensions: Vector2i in SIZES:
			root.content_scale_size = dimensions
			root.size = dimensions
			main.start_match({"mode": "offline", "difficulty": "easy", "name": "Overflow QA"})
			await settle()
			var screen := Rect2(Vector2.ZERO, Vector2(dimensions))
			var context := "%dx%d @%d%%" % [dimensions.x, dimensions.y, int(text_scale * 100)]
			var game = main.match_game
			game.set_physics_process(false)
			var score_x: float = main.score_label.get_global_rect().get_center().x
			for set_name: String in NAMES:
				var pair: Array = NAMES[set_name]
				game.actors[2].display_name = pair[0]
				game.actors[7].display_name = pair[1]
				game.actors[8].display_name = pair[1].reverse()
				for i in range(main.KILL_FEED_ROWS):
					game.elimination_reported.emit(2 if i % 2 == 0 else 7, 8 if i % 2 == 0 else 2, i % 3 == 0)
				main._process(0.016)
				await settle()
				var label := "%s %s" % [context, set_name]
				check(absf(main.score_label.get_global_rect().get_center().x - dimensions.x * 0.5) < 1.0 and absf(main.score_label.get_global_rect().get_center().x - score_x) < 1.0, label + ": score stays centred")
				for critical in [main.ammo_label, main.utility_label, main.health_label, main.score_label, main.radar]:
					check(inside(critical.get_global_rect(), screen), label + ": %s stays on screen %s" % [critical.name, critical.get_global_rect()])
				var feed_rect: Rect2 = main.kill_feed.get_parent().get_global_rect() if main.kill_feed.get_parent() is Control else main.kill_feed.get_global_rect()
				check(inside(feed_rect, screen), label + ": kill feed stays on screen")
				check(not feed_rect.intersects(main.score_label.get_global_rect()) and not feed_rect.intersects(main.radar.get_global_rect()), label + ": kill feed clears score and radar")
				var pause_point: Vector2 = main.touch.control_point("pause")
				check(not feed_rect.intersects(Rect2(pause_point - Vector2.ONE * main.touch.radius("pause"), Vector2.ONE * main.touch.radius("pause") * 2)), label + ": kill feed clears the MENU button")
				check(main.kill_feed.get_child_count() == main.KILL_FEED_ROWS, label + ": feed keeps %d rows" % main.KILL_FEED_ROWS)
				var truncated := false
				for entry: Control in main.kill_feed.get_children():
					check(inside(entry.get_global_rect(), feed_rect), label + ": every feed row is fully visible")
					for name_label: Label in entry.find_children("*", "Label", true, false):
						var font := name_label.get_theme_font("font")
						var drawn := font.get_string_size(name_label.text, HORIZONTAL_ALIGNMENT_LEFT, -1, name_label.get_theme_font_size("font_size")).x
						check(drawn <= name_label.size.x + 1, label + ": '%s' is drawn whole, not clipped (%.0f > %.0f px)" % [name_label.text, drawn, name_label.size.x])
						if not name_label.has_meta("full_name"):
							continue
						var full: String = name_label.get_meta("full_name")
						if name_label.text != full:
							truncated = true
							var kept := name_label.text.trim_suffix("…")
							check(name_label.text.ends_with("…") and full.begins_with(kept) and not kept.is_empty(), label + ": '%s' is a prefix of '%s' ending in an ellipsis" % [name_label.text, full])
				if set_name == "ordinary":
					check(not truncated, label + ": ordinary names are never shortened")
				if set_name == "max_ascii" and text_scale == 1.0:
					await capture("%dx%d-killfeed-max" % [dimensions.x, dimensions.y])
				if set_name == "unicode" and text_scale == 1.3 and dimensions == Vector2i(1560, 720):
					await capture("%dx%d-killfeed-unicode-130" % [dimensions.x, dimensions.y])
			main.leave_match()
			await settle()
	main.profile.data.settings.ui_text_scale = 1.0
	# Truncation never separates a base character from its combining marks.
	main.start_match({"mode": "offline", "difficulty": "easy", "name": "Overflow QA"})
	await settle()
	var probe: Label = main.label("x", 14)
	main.ui.add_child(probe)
	var combining := "e\u0301e\u0301e\u0301e\u0301e\u0301e\u0301e\u0301e\u0301"
	for width in range(20, 90, 3):
		var fitted: String = main._fit_text(probe, combining, float(width))
		var kept := fitted.trim_suffix("…")
		check(kept.length() % 2 == 0, "fitting to %d px keeps every accent with its letter ('%s')" % [width, fitted])
	probe.queue_free()
	main.leave_match()
	await settle()
	main.queue_free()
	await settle()
	print("HUD_OVERFLOW_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
