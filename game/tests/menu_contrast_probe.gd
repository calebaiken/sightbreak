extends SceneTree
## Native probe (needs a renderer, so it is not part of validate.sh): measures the contrast of
## every label in the main menu against what is really drawn behind it.
##
## The menu is rendered with its text hidden to get the background, then each label's colour is
## compared with the background under its rectangle, as a WCAG contrast ratio. Light text is
## judged against the BRIGHTEST tenth of the pixels behind it (where it is hardest to read), dark
## text against the darkest tenth. 4.5 is the WCAG minimum for body text, 3.0 for large text (24 px
## and up). The yard behind the menu turns slowly, so the number is the worst case over a few
## camera positions.
##
##   CONTRAST_OUT=dir DISPLAY=:99 godot --rendering-method gl_compatibility --script res://tests/menu_contrast_probe.gd
## Software-rendered (Mesa llvmpipe), not a phone display: it measures the design, not a screen.
const SIZES := [Vector2i(1280, 720), Vector2i(960, 720), Vector2i(1560, 720)]
var rows: Array[String] = []
var worst := 99.0
var below := 0
var measured := 0

func _initialize() -> void:
	call_deferred("run")

func frames(count: int) -> void:
	for i in count:
		await process_frame

func luminance(color: Color) -> float:
	var lin := func(c: float) -> float: return c / 12.92 if c <= 0.04045 else pow((c + 0.055) / 1.055, 2.4)
	return 0.2126 * lin.call(color.r) + 0.7152 * lin.call(color.g) + 0.0722 * lin.call(color.b)

func ratio(a: float, b: float) -> float:
	return (maxf(a, b) + 0.05) / (minf(a, b) + 0.05)

func snapshot() -> Image:
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image()

func run() -> void:
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await frames(3)
	var out := OS.get_environment("CONTRAST_OUT")
	for size: Vector2i in SIZES:
		root.content_scale_size = size
		root.size = size
		main.profile.data.settings.ui_text_scale = 1.0
		main.ui.theme = main.build_theme()
		main.show_menu()
		await frames(6)
		var labels: Array[Label] = []
		for node in main.ui.find_children("*", "Label", true, false):
			var label := node as Label
			if label.is_visible_in_tree() and not label.text.is_empty() and label.size.x > 0 and not (label.get_parent() is Button):
				labels.append(label)
		# Several camera positions: the yard drifts, so take the worst.
		var minimum := {}
		for step in 3:
			main.elapsed = float(step) * 120.0
			await frames(3)
			# Transparent, not hidden: a hidden label gives up its space and the layout moves.
			for label in labels:
				label.modulate.a = 0.0
			await frames(2)
			var background := await snapshot()
			for label in labels:
				label.modulate.a = 1.0
			await frames(2)
			if step == 0 and not out.is_empty():
				DirAccess.make_dir_recursive_absolute(out)
				background.save_png("%s/menu-background-%dx%d.png" % [out, size.x, size.y])
			for label in labels:
				var rect := label.get_global_rect().intersection(Rect2(Vector2.ZERO, Vector2(size)))
				if rect.size.x < 2 or rect.size.y < 2:
					continue
				var colour := label.get_theme_color("font_color")
				var text_l := luminance(colour)
				var samples: Array[float] = []
				for y in range(int(rect.position.y), int(rect.end.y), 2):
					for x in range(int(rect.position.x), int(rect.end.x), 2):
						samples.append(luminance(background.get_pixel(x, y)))
				samples.sort()
				var edge: float = samples[int(samples.size() * 0.9)] if text_l > 0.18 else samples[int(samples.size() * 0.1)]
				var value := ratio(text_l, edge)
				var key := label.get_path()
				if not minimum.has(key) or value < minimum[key].ratio:
					minimum[key] = {"ratio": value, "text": label.text.left(36), "size": label.get_theme_font_size("font_size")}
		for key in minimum:
			var entry: Dictionary = minimum[key]
			var needed := 3.0 if int(entry.size) >= 24 else 4.5
			measured += 1
			worst = minf(worst, float(entry.ratio))
			if float(entry.ratio) < needed:
				below += 1
				rows.append("%dx%d  %.2f (needs %.1f)  %dpx  %s" % [size.x, size.y, entry.ratio, needed, entry.size, entry.text])
	print("MENU_CONTRAST labels=%d below_threshold=%d worst=%.2f" % [measured, below, worst])
	for row in rows:
		print("  LOW ", row)
	main.queue_free()
	await frames(2)
	quit(0)
