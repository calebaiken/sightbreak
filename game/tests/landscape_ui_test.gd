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
## The drawn text block of a centred, wrapping label: its widest line and its lines'
## total height, centred horizontally in the label's rect.
func text_block(label: Label) -> Rect2:
	var font := label.get_theme_font("font")
	var rect := label.get_global_rect()
	var block := font.get_multiline_string_size(label.text, HORIZONTAL_ALIGNMENT_CENTER, rect.size.x, label.get_theme_font_size("font_size"))
	return Rect2(rect.position.x + (rect.size.x - block.x) * 0.5, rect.position.y, block.x, block.y)
func touch_target(main: Node, action: String) -> Rect2:
	var radius: float = main.touch.radius(action)
	return Rect2(main.touch.global_position + main.touch.control_point(action) - Vector2.ONE * radius, Vector2.ONE * radius * 2)
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
	# Settings saved by an earlier run must not change this one.
	main.profile.data.settings.ui_text_scale = 1.0
	main.profile.data.settings.hud_scale = 1.0
	await settle()
	for dimensions in [Vector2i(1280, 720), Vector2i(1600, 720), Vector2i(960, 720), Vector2i(1560, 720), Vector2i(1024, 768)]:
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
	# Status text against every drawn touch control at each text size (the 100 % checks
	# above miss that larger text reached FRAG and SMOKE), for the buy, attack and defuse
	# prompts and the longest match notification.
	var longest := "Match complete; account reward submission failed. Server logs identify the match for review."
	for scale in [0.85, 1.0, 1.15, 1.3]:
		main.profile.data.settings.ui_text_scale = scale
		for dimensions in [Vector2i(1280, 720), Vector2i(1600, 720), Vector2i(960, 720), Vector2i(1560, 720), Vector2i(1024, 768)]:
			root.content_scale_size = dimensions
			root.size = dimensions
			await settle()
			main.start_match({"mode": "offline", "difficulty": "normal", "name": "Text scale QA"})
			await settle()
			for prompt in ["buy", "attack", "defuse", "notification"]:
				main.match_game.phase = "buy" if prompt == "buy" else "live"
				main.match_game.objective_state = "planted" if prompt == "defuse" else "carried"
				main.status_label.set_meta("until", 0.0)
				if prompt == "notification": main.show_notification(longest)
				main._process(0.01)
				await settle()
				main._process(0.01)
				await settle()
				var block := text_block(main.status_label)
				var hit: Array[String] = []
				for action in main.touch.positions:
					if action != "move" and touch_target(main, action).intersects(block): hit.append(action)
				check(hit.is_empty(), "%d%% text at %s: the %s status text clears every touch control %s" % [roundi(scale * 100), dimensions, prompt, hit])
				check(block.position.x >= 0 and block.end.x <= dimensions.x and block.position.y >= 0, "%d%% text at %s: the %s status text stays on screen" % [roundi(scale * 100), dimensions, prompt])
			main.leave_match()
			await settle()
	await status_layouts(main)
	# Without touch controls the status line keeps the full row and stays centred.
	main.profile.data.settings.ui_text_scale = 1.3
	main.profile.data.settings.touch_visible = false
	main.start_match({"mode": "offline", "difficulty": "normal", "name": "Desktop text QA"})
	await settle()
	main._process(0.01)
	await settle()
	check(absf(text_block(main.status_label).get_center().x - main.ui.size.x * 0.5) < 2.0, "without touch controls the status text stays centred")
	main.leave_match()
	main.profile.data.settings.ui_text_scale = 1.0
	main.profile.data.settings.touch_visible = true
	main.profile.data.settings.hud_positions = {}
	main.profile.data.settings.hud_scale = 1.0
	main.queue_free()
	await settle()
	print("LANDSCAPE_UI_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)

## Saved touch layouts and button sizes the player can choose. "centre gap" is the layout
## from the review of 98ff57c: FRAG and SMOKE leave a 6 px gap at the centre of a 960 x 720
## screen, which the old fitter chose and then wrapped the text into a 6 px column.
const STATUS_LAYOUTS := {
	"default": {},
	"centre gap": {"grenade": [0.459375, 0.82], "smoke": [0.540625, 0.82]},
	"centre button": {"interact": [0.5, 0.83]},
	"bottom wall": {"grenade": [0.30, 0.83], "smoke": [0.40, 0.83], "interact": [0.50, 0.83], "reload": [0.60, 0.83], "crouch": [0.70, 0.83]},
}
const STATUS_MAX_LINES := 3
const STATUS_FRAMES := 8
## Status line under saved layouts, enlarged buttons, every text size and long or
## non-Latin text, sampled over consecutive frames: it must hold still, stay within
## STATUS_MAX_LINES lines, clear every drawn touch control and the funds label, stay
## below the reticle, and never move the score, health or ammunition.
func status_layouts(main: Node) -> void:
	var texts := {
		"buy": "", "attack": "", "defuse": "",
		"notification": "Match complete; account reward submission failed. Server logs identify the match for review.",
		"unicode": "白雪・シラユキ eliminated Zoë Ångström-Nguyễn  /  ＲＥＬＡＹ ＡＲ",
	}
	# The review's exact reproduction: the layout saved in the profile before the match.
	main.profile.data.settings.ui_text_scale = 1.3
	main.profile.data.settings.hud_positions = STATUS_LAYOUTS["centre gap"]
	root.content_scale_size = Vector2i(960, 720)
	root.size = Vector2i(960, 720)
	await settle()
	main.start_match({"mode": "offline", "difficulty": "normal", "name": "Saved layout QA"})
	await settle()
	main.match_game.process_mode = Node.PROCESS_MODE_DISABLED
	await status_case(main, "saved centre gap 130% 960x720 buy", "buy", "")
	main.leave_match()
	main.profile.data.settings.hud_positions = {}
	await settle()
	# --status-quick keeps the hardest part of the matrix (the largest text on the two
	# narrowest screens) for native runs, which render every sampled frame in software.
	var quick := OS.get_cmdline_user_args().has("--status-quick")
	for scale in [1.3] if quick else [0.85, 1.0, 1.15, 1.3]:
		main.profile.data.settings.ui_text_scale = scale
		for dimensions in [Vector2i(960, 720), Vector2i(1024, 768)] if quick else [Vector2i(960, 720), Vector2i(1024, 768), Vector2i(1280, 720), Vector2i(1560, 720), Vector2i(1600, 720)]:
			root.content_scale_size = dimensions
			root.size = dimensions
			await settle()
			main.start_match({"mode": "offline", "difficulty": "normal", "name": "Status layout QA"})
			await settle()
			# Freeze the simulation so no match event replaces the text being sampled; the
			# HUD still updates every frame from the match state.
			main.match_game.process_mode = Node.PROCESS_MODE_DISABLED
			for button_scale in [1.0, 1.5]:
				for layout_name in STATUS_LAYOUTS:
					main.touch.reset_layout()
					main.touch.restore_layout(STATUS_LAYOUTS[layout_name])
					main.touch.hud_scale = button_scale
					for prompt in texts:
						await status_case(main, "%d%% text, %d%% buttons, %s layout, %s:" % [roundi(scale * 100), roundi(button_scale * 100), layout_name, dimensions], prompt, texts[prompt])
			main.leave_match()
			await settle()

func status_case(main: Node, context: String, prompt: String, text: String) -> void:
	var size: Vector2 = main.ui.size
	main.match_game.phase = "buy" if prompt == "buy" else "live"
	main.match_game.objective_state = "planted" if prompt == "defuse" else "carried"
	# Long enough that no detonation or round end replaces the text while sampling.
	main.match_game.objective_timer = 40.0
	main.match_game.time_left = 40.0
	main.status_label.set_meta("until", 0.0)
	if not text.is_empty(): main.show_notification(text)
	main._process(0.01)
	await process_frame
	var shown: String = main.status_label.text
	var rects: Array[Rect2] = []
	var tallest := 0.0
	var lines := 0
	for frame in STATUS_FRAMES:
		await process_frame
		if main.status_label.text != shown: continue
		rects.append(main.status_label.get_global_rect())
		tallest = maxf(tallest, main.status_label.size.y)
		lines = maxi(lines, main.status_label.get_line_count())
	var label: Label = main.status_label
	var line_height := label.get_theme_font("font").get_height(label.get_theme_font_size("font_size"))
	var block := text_block(label)
	var moved := rects.filter(func(rect: Rect2): return not rect.is_equal_approx(rects[0]))
	check(rects.size() == STATUS_FRAMES and moved.is_empty(), "%s %s status line holds still over %d consecutive frames (%d sampled, first %s, moved to %s)" % [context, prompt, STATUS_FRAMES, rects.size(), rects[0] if rects.size() else Rect2(), moved.slice(0, 2)])
	check(lines <= STATUS_MAX_LINES and tallest <= STATUS_MAX_LINES * (line_height + 4) + 2, "%s %s status line stays within %d lines (%d lines, %.0f px)" % [context, prompt, STATUS_MAX_LINES, lines, tallest])
	check(block.position.x >= 0 and block.end.x <= size.x and block.end.y <= size.y, "%s %s status text stays on screen %s" % [context, prompt, block])
	# The label's own rectangle as well as the estimated text block: Font's multiline size
	# does not wrap as the Label does, so the block alone can miss a wrapped label (the
	# review of 98ff57c measured a 180 px estimate for a 756 px label).
	var bounds := label.get_global_rect()
	check(bounds.position.x >= 0 and bounds.end.x <= size.x and bounds.position.y >= 0 and bounds.end.y <= size.y, "%s %s status label stays on screen %s" % [context, prompt, bounds])
	var under: Array[String] = []
	for action in main.touch.positions:
		if action != "move" and touch_target(main, action).intersects(bounds): under.append(action)
	check(under.is_empty() and not main.funds_label.get_global_rect().intersects(bounds), "%s %s status label's rectangle clears every touch control and the funds label %s" % [context, prompt, under])
	check(minf(block.position.y, bounds.position.y) > size.y * 0.5 + 40, "%s %s status text stays below the reticle %s" % [context, prompt, bounds])
	var hit: Array[String] = []
	for action in main.touch.positions:
		if action != "move" and touch_target(main, action).intersects(block): hit.append(action)
	check(hit.is_empty(), "%s %s status text clears every touch control %s" % [context, prompt, hit])
	check(not main.funds_label.get_global_rect().intersects(block), "%s %s status text clears the funds label" % [context, prompt])
	for critical: Control in [main.health_label, main.ammo_label]:
		var rect := critical.get_global_rect()
		check(rect.position.y >= 0 and rect.end.y <= size.y + 1 and rect.position.x >= 0 and rect.end.x <= size.x + 1, "%s %s %s stays on screen %s" % [context, prompt, critical.name, rect])
	check(absf(main.score_label.get_global_rect().get_center().x - size.x * 0.5) < 1.0 and main.score_label.get_global_rect().position.y < size.y * 0.25, "%s %s score stays centred at the top" % [context, prompt])
