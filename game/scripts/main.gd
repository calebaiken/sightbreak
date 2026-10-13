extends Node

const Profile = preload("res://scripts/profile.gd")
const Touch = preload("res://scripts/ui/touch_controls.gd")
const SafeArea = preload("res://scripts/ui/safe_area.gd")
const BG := Color("10151c")
const PANEL := Color("19212b")
const MUTED := Color("8c9bad")
const GOLD := Color("c8b17c")
const CRIMSON := Color("b63045")
var profile = Profile.new()
var canvas: CanvasLayer
var ui: Control
var menu_world: Node3D
var menu_camera: Camera3D
var match_game
var touch
var screen := "menu"
var paused := false
var input_look := Vector2.ZERO
var mouse_delta := Vector2.ZERO
var status_label: Label
var score_label: Label
var phase_label: Label
var ammo_label: Label
var health_label: Label
var action_label: Label
var crosshair: Control
var objective_bar: ProgressBar
var score_panel: PanelContainer
var overlay: Control
var elapsed := 0.0
var server_mode := false
var smoke_mode := false
var smoke_frames := 0
var smoke_capture := ""
var demo_mode := false
var demo_time := 0.0
var economy_panel
var input_round := -1
var input_actor := -1
var switch_requested := false
var touch_score_until := 0.0
var reward_label: Label
var current_loadout: Dictionary = {}
var cosmetic_weapon := ""

func _ready() -> void:
	profile.load_profile()
	Input.use_accumulated_input = false
	apply_settings()
	var args := OS.get_cmdline_user_args()
	server_mode = "--server" in args
	smoke_mode = "--smoke" in args
	demo_mode = "--demo" in args
	for arg in args:
		if arg.begins_with("--capture="): smoke_capture = arg.trim_prefix("--capture=")
	if server_mode:
		var port := 27020
		var server_id := "local-relay"
		var economy_url := "http://127.0.0.1:8080"
		for arg in args:
			if arg.begins_with("--port="): port = int(arg.trim_prefix("--port="))
			if arg.begins_with("--server-id="): server_id = arg.trim_prefix("--server-id=")
			if arg.begins_with("--economy-url="): economy_url = arg.trim_prefix("--economy-url=")
		start_match({"mode": "server", "port": port, "name": "Dedicated", "require_accounts": "--require-accounts" in args, "server_id": server_id, "economy_url": economy_url})
		return
	canvas = CanvasLayer.new()
	add_child(canvas)
	ui = Control.new()
	ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	ui.theme = build_theme()
	canvas.add_child(ui)
	show_menu()
	if demo_mode: start_match({"mode": "offline", "difficulty": "normal", "name": "Operator"})

func build_theme() -> Theme:
	var theme := Theme.new()
	theme.default_font_size = 18
	theme.set_color("font_color", "Label", Color("e7eaf0"))
	theme.set_color("font_color", "Button", Color("e7eaf0"))
	theme.set_color("font_hover_color", "Button", Color.WHITE)
	theme.set_stylebox("normal", "Button", box(PANEL, 5, Color("344353")))
	theme.set_stylebox("hover", "Button", box(Color("2c3542"), 5, GOLD))
	theme.set_stylebox("pressed", "Button", box(Color("702536"), 5, CRIMSON))
	theme.set_stylebox("focus", "Button", box(Color.TRANSPARENT, 5, GOLD))
	theme.set_stylebox("normal", "LineEdit", box(Color("0b1119"), 4, Color("405064")))
	theme.set_stylebox("panel", "PanelContainer", box(PANEL, 5, Color("344353")))
	theme.set_constant("separation", "VBoxContainer", 12)
	theme.set_constant("separation", "HBoxContainer", 12)
	return theme

func box(color: Color, radius: int = 0, border: Color = Color.TRANSPARENT) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = color
	s.set_corner_radius_all(radius)
	s.set_border_width_all(1)
	s.border_color = border
	s.content_margin_left = 18
	s.content_margin_right = 18
	s.content_margin_top = 12
	s.content_margin_bottom = 12
	return s

func label(text: String, font_size: int = 18, color: Color = Color.WHITE) -> Label:
	var node := Label.new()
	node.text = text
	node.add_theme_font_size_override("font_size", font_size)
	node.add_theme_color_override("font_color", color)
	return node

func button(text: String, callback: Callable, height: float = 48) -> Button:
	var node := Button.new()
	node.text = text
	node.custom_minimum_size.y = height
	node.pressed.connect(callback)
	node.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	return node

func fill(node: Control) -> void:
	node.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

func clear_ui() -> void:
	if ui == null: return
	for child in ui.get_children():
		ui.remove_child(child)
		child.queue_free()
	status_label = null
	overlay = null
	touch = null
	crosshair = null
	score_panel = null

func margin_frame(parent: Control, amount: int = 36) -> MarginContainer:
	var margins := MarginContainer.new()
	fill(margins)
	for side in ["left", "top", "right", "bottom"]:
		margins.add_theme_constant_override("margin_" + side, amount)
	parent.add_child(margins)
	margins.resized.connect(func(): apply_safe_margins(margins, amount))
	apply_safe_margins.call_deferred(margins, amount)
	return margins

func apply_safe_margins(margins: MarginContainer, base: int) -> void:
	if not is_instance_valid(margins): return
	var viewport_size := get_viewport().get_visible_rect().size
	var safe: Rect2 = SafeArea.viewport_rect(viewport_size)
	margins.add_theme_constant_override("margin_left", base + int(safe.position.x))
	margins.add_theme_constant_override("margin_top", base + int(safe.position.y))
	margins.add_theme_constant_override("margin_right", base + int(viewport_size.x - safe.end.x))
	margins.add_theme_constant_override("margin_bottom", base + int(viewport_size.y - safe.end.y))

func ensure_menu_world() -> void:
	if is_instance_valid(menu_world): return
	menu_world = Node3D.new()
	menu_world.name = "MenuWorld"
	add_child(menu_world)
	if ResourceLoader.exists("res://scripts/gameplay/arena.gd"):
		var yard = load("res://scripts/gameplay/arena.gd").new()
		menu_world.add_child(yard)
	menu_camera = Camera3D.new()
	menu_world.add_child(menu_camera)
	menu_camera.position = Vector3(25, 19, 29)
	menu_camera.look_at(Vector3(0, 1, 0))
	menu_camera.current = true
	menu_camera.fov = 61

func show_menu() -> void:
	if is_instance_valid(economy_panel): economy_panel.hide()
	screen = "menu"
	paused = false
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	clear_ui()
	ensure_menu_world()
	var shade := ColorRect.new()
	shade.color = Color(0.02, 0.03, 0.045, 0.72)
	fill(shade)
	ui.add_child(shade)
	var margins := margin_frame(ui)
	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 18)
	margins.add_child(rows)
	var top := HBoxContainer.new()
	rows.add_child(top)
	top.add_child(label("S / B     TACTICAL OPERATIONS", 16, GOLD))
	var spring := Control.new()
	spring.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(spring)
	top.add_child(label("NATIVE ALPHA   /   01", 14, MUTED))
	var middle := HBoxContainer.new()
	middle.size_flags_vertical = Control.SIZE_EXPAND_FILL
	rows.add_child(middle)
	var left := VBoxContainer.new()
	left.custom_minimum_size.x = 440
	left.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	middle.add_child(left)
	left.add_child(label("SIGHTBREAK", 72))
	left.add_child(label("PRECISION. PRESSURE. PURPOSE.", 15, GOLD))
	var spacer := Control.new()
	spacer.custom_minimum_size.y = 8
	left.add_child(spacer)
	var play := button("DEPLOY  /  OFFLINE 5 v 5                 →", func(): start_match({"mode": "offline", "difficulty": ["easy", "normal", "hard"][clampi(int(profile.data.settings.difficulty), 0, 2)], "name": profile.data.display_name}), 60)
	play.add_theme_stylebox_override("normal", box(CRIMSON, 4, CRIMSON.lightened(0.15)))
	left.add_child(play)
	left.add_child(button("LOCAL NETWORK  /  DIRECT CONNECT", show_connect))
	var economy_row := HBoxContainer.new()
	left.add_child(economy_row)
	for tab in ["inventory", "cases", "market", "trades"]:
		var tab_name: String = tab
		var entry := button(tab_name.to_upper(), func(): open_economy(tab_name), 44)
		entry.add_theme_font_size_override("font_size", 13)
		entry.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		economy_row.add_child(entry)
	left.add_child(button("OPERATOR  /  LOCAL PROGRESSION", show_progress))
	left.add_child(button("SETTINGS  /  CONTROLS", show_settings))
	var right := VBoxContainer.new()
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.size_flags_vertical = Control.SIZE_SHRINK_END
	right.alignment = BoxContainer.ALIGNMENT_END
	middle.add_child(right)
	var map_title := label("RELAY YARD", 36)
	map_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	right.add_child(map_title)
	var map_note := label("02 SITES   /   03 ROUTES\nINDUSTRIAL TRANSFER STATION", 14, GOLD)
	map_note.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	right.add_child(map_note)
	var footer := HBoxContainer.new()
	rows.add_child(footer)
	footer.add_child(label("◈  LEVEL %02d     %s     /     TRAINING" % [profile.data.level, str(profile.data.display_name).to_upper()], 14, MUTED))
	var gap := Control.new()
	gap.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	footer.add_child(gap)
	footer.add_child(label("EARNED IN PLAY.  ZERO REAL-MONEY PURCHASES.", 13, GOLD))

func panel_screen(title: String, subtitle: String, back: Callable = show_menu) -> VBoxContainer:
	clear_ui()
	var shade := ColorRect.new()
	shade.color = Color(0.025, 0.04, 0.06, 0.95)
	fill(shade)
	ui.add_child(shade)
	var margins := margin_frame(ui, 32)
	var rows := VBoxContainer.new()
	margins.add_child(rows)
	var top := HBoxContainer.new()
	rows.add_child(top)
	top.add_child(button("← BACK", back, 42))
	top.add_child(label(title, 32))
	rows.add_child(label(subtitle, 15, MUTED))
	return rows

func show_connect() -> void:
	screen = "connect"
	var rows := panel_screen("LOCAL NETWORK", "Unranked LAN sessions • Server owns movement, combat and round rules • No online economy rewards")
	rows.add_child(label("Join a dedicated server", 26))
	var address := LineEdit.new()
	address.placeholder_text = "Server address"
	address.text = "127.0.0.1"
	rows.add_child(address)
	var port := SpinBox.new()
	port.min_value = 1024
	port.max_value = 65535
	port.value = 27020
	rows.add_child(port)
	rows.add_child(button("JOIN GUEST LAN MATCH", func(): start_match({"mode": "client", "address": address.text.strip_edges(), "port": int(port.value), "name": profile.data.display_name})))
	var server_id := LineEdit.new()
	server_id.text = "local-relay"
	server_id.placeholder_text = "Account server ID"
	rows.add_child(server_id)
	var account_status := label("Account sessions require ten authenticated players. Log in through the online account screen first.", 15, MUTED)
	account_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(account_status)
	var account_join := button("JOIN ACCOUNT SERVER", func(): pass)
	account_join.pressed.connect(func(): connect_account(address.text.strip_edges(), int(port.value), server_id.text.strip_edges(), account_status, account_join))
	rows.add_child(account_join)
	var info := label("Start the dedicated server on another terminal or machine:\n./scripts/godot.sh --headless -- --server --port=27020\n\nUDP port 27020 must be reachable on your local network.\nFor authenticated local sessions use ./scripts/serve-account-match.sh.\nInternet matchmaking and automatic server discovery are not available.", 18, MUTED)
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rows.add_child(info)

func connect_account(address: String, port: int, server_id: String, feedback: Label, submit: Button) -> void:
	if not is_instance_valid(economy_panel) or economy_panel.api.token.is_empty():
		feedback.text = "Log in at OPERATOR → ONLINE ACCOUNT & INVENTORY, then return here."
		return
	submit.disabled = true
	feedback.text = "Requesting a single-use server ticket…"
	var response: Dictionary = await economy_panel.api.request("/auth/game-ticket", HTTPClient.METHOD_POST, {"server_id": server_id})
	if not is_instance_valid(feedback): return
	submit.disabled = false
	if response.has("_error"):
		feedback.text = str(response._error)
		return
	start_match({"mode": "client", "address": address, "port": port, "name": profile.data.display_name, "join_ticket": str(response.ticket), "server_id": server_id})

func show_progress() -> void:
	screen = "progress"
	var rows := panel_screen("OPERATOR RECORD", "Offline training record • Separate from authenticated online accounts and tradable inventory")
	rows.add_child(label("LEVEL %d     /     %d XP     /     %d TRAINING CREDITS" % [profile.data.level, profile.data.xp, profile.data.credits], 28, GOLD))
	rows.add_child(label("%d MATCHES     %d WINS     %d ELIMINATIONS     %d DEATHS" % [profile.data.matches, profile.data.wins, profile.data.kills, profile.data.deaths], 20))
	var name_row := HBoxContainer.new()
	rows.add_child(name_row)
	var display := LineEdit.new()
	display.text = profile.data.display_name
	display.max_length = 20
	display.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name_row.add_child(display)
	name_row.add_child(button("SAVE NAME", func():
		profile.data.display_name = display.text.strip_edges() if not display.text.strip_edges().is_empty() else "Operator"
		profile.save()
	))
	rows.add_child(button("ONLINE ACCOUNT & INVENTORY", func(): open_economy("profile")))
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	rows.add_child(scroll)
	var history := VBoxContainer.new()
	history.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(history)
	if profile.data.history.is_empty(): history.add_child(label("Complete an offline match to establish your training record.", 18, MUTED))
	for result in profile.data.history:
		history.add_child(label("%s   •   %s   •   %d eliminations   •   +%d Credits" % [result.get("time", ""), "VICTORY" if result.get("won", false) else "DEFEAT", int(result.get("kills", 0)), int(result.get("credits_earned", 0))], 17, MUTED))

func setting_slider(parent: VBoxContainer, title: String, key: String, low: float, high: float, step: float) -> void:
	var row := HBoxContainer.new()
	parent.add_child(row)
	var caption := label(title, 17)
	caption.custom_minimum_size.x = 250
	row.add_child(caption)
	var slider := HSlider.new()
	slider.min_value = low
	slider.max_value = high
	slider.step = step
	slider.value = float(profile.data.settings[key])
	slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(slider)
	var value := label(str(slider.value), 16, GOLD)
	value.custom_minimum_size.x = 90
	row.add_child(value)
	slider.value_changed.connect(func(v: float):
		profile.data.settings[key] = v
		value.text = str(v)
		profile.save()
		apply_settings()
	)

func show_settings() -> void:
	screen = "settings"
	var rows := panel_screen("FIELD SETTINGS", "Controls and accessibility are saved on this device. Touch HUD layouts are editable during a match.")
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	rows.add_child(scroll)
	var settings := VBoxContainer.new()
	settings.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(settings)
	setting_slider(settings, "MOUSE SENSITIVITY", "sensitivity", 0.0005, 0.008, 0.0001)
	setting_slider(settings, "TOUCH SENSITIVITY", "touch_sensitivity", 0.001, 0.012, 0.0002)
	setting_slider(settings, "FIELD OF VIEW", "fov", 60, 100, 1)
	setting_slider(settings, "MASTER VOLUME", "volume", 0, 1, 0.05)
	setting_slider(settings, "TOUCH BUTTON SIZE", "hud_scale", 0.7, 1.6, 0.05)
	setting_slider(settings, "CROSSHAIR SIZE", "crosshair_size", 2, 12, 1)
	for definition in [["GYROSCOPE AIMING (supported devices)", "gyro"], ["SHOW TOUCH CONTROLS ON DESKTOP", "touch_visible"], ["REDUCED MOTION", "reduced_motion"]]:
		var key: String = definition[1]
		var check := CheckButton.new()
		check.text = definition[0]
		check.button_pressed = bool(profile.data.settings[key])
		check.toggled.connect(func(value: bool): profile.data.settings[key] = value; profile.save())
		settings.add_child(check)
	var quality := HBoxContainer.new()
	settings.add_child(quality)
	quality.add_child(label("FRAME LIMIT", 17))
	var frame_limit := OptionButton.new()
	for value in [30, 60, 90, 120]: frame_limit.add_item(str(value), value)
	frame_limit.select([30, 60, 90, 120].find(int(profile.data.settings.fps_limit)))
	frame_limit.item_selected.connect(func(index: int): profile.data.settings.fps_limit = frame_limit.get_item_id(index); profile.save(); apply_settings())
	quality.add_child(frame_limit)
	quality.add_child(label("BOT DIFFICULTY", 17))
	var difficulty := OptionButton.new()
	for value in ["RECRUIT", "STANDARD", "VETERAN"]: difficulty.add_item(value)
	difficulty.select(int(profile.data.settings.difficulty))
	difficulty.item_selected.connect(func(index: int): profile.data.settings.difficulty = index; profile.save())
	quality.add_child(difficulty)
	quality.add_child(label("GRAPHICS", 17))
	var graphics := OptionButton.new()
	graphics.add_item("LOW / NO SHADOWS")
	graphics.add_item("STANDARD")
	graphics.select(int(profile.data.settings.graphics_quality))
	graphics.item_selected.connect(func(index: int): profile.data.settings.graphics_quality = index; profile.save(); apply_settings())
	quality.add_child(graphics)
	var color_row := HBoxContainer.new()
	settings.add_child(color_row)
	color_row.add_child(label("CROSSHAIR COLOR", 17))
	var picker := ColorPickerButton.new()
	picker.color = Color(str(profile.data.settings.crosshair_color))
	picker.custom_minimum_size = Vector2(100, 35)
	picker.color_changed.connect(func(color: Color): profile.data.settings.crosshair_color = color.to_html(false); profile.save())
	color_row.add_child(picker)
	settings.add_child(label("WASD / left stick: move  •  Mouse / right stick: aim  •  LMB / R2: fire\nR: reload  •  E: hold plant / defuse  •  Space: jump  •  Ctrl: crouch\nB: buy  •  G: frag  •  Q: smoke  •  1 / 2: switch  •  Tab: score  •  Esc: pause", 17, MUTED))

func apply_settings() -> void:
	Engine.max_fps = int(profile.data.settings.fps_limit)
	AudioServer.set_bus_volume_db(0, linear_to_db(maxf(0.001, float(profile.data.settings.volume))))
	if not is_inside_tree(): return
	var high_quality := int(profile.data.settings.graphics_quality) > 0
	get_viewport().msaa_3d = Viewport.MSAA_2X if high_quality else Viewport.MSAA_DISABLED
	for light in find_children("*", "DirectionalLight3D", true, false): light.shadow_enabled = high_quality

func open_economy(tab: String) -> void:
	screen = "economy"
	clear_ui()
	if not is_instance_valid(economy_panel):
		economy_panel = load("res://scripts/ui/economy_ui.gd").new()
		economy_panel.configure(profile.data)
		economy_panel.theme = ui.theme
		canvas.add_child(economy_panel)
		economy_panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		economy_panel.closed.connect(show_menu)
		if economy_panel.has_signal("loadout_changed"):
			economy_panel.loadout_changed.connect(func(slots: Dictionary):
				current_loadout = slots.duplicate(true)
				cosmetic_weapon = ""
			)
	else:
		economy_panel.configure(profile.data)
		economy_panel.show()
	economy_panel.open_tab(tab)

func start_match(options: Dictionary) -> void:
	if is_instance_valid(match_game):
		remove_child(match_game)
		match_game.queue_free()
	if is_instance_valid(menu_world):
		remove_child(menu_world)
		menu_world.queue_free()
		menu_world = null
		menu_camera = null
	clear_ui()
	match_game = load("res://scripts/gameplay/match.gd").new()
	match_game.name = "Match"
	match_game.configure(options)
	add_child(match_game)
	match_game.match_finished.connect(on_match_finished)
	match_game.notification.connect(show_notification)
	match_game.exit_requested.connect(leave_match)
	screen = "game"
	paused = false
	input_look = Vector2.ZERO
	input_round = -1
	input_actor = -1
	cosmetic_weapon = ""
	apply_settings()
	mouse_delta = Vector2.ZERO
	if not server_mode:
		build_hud()
		if not DisplayServer.is_touchscreen_available(): Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func build_hud() -> void:
	clear_ui()
	for area in [Rect2(0, 0, 1, 0.16), Rect2(0, 0.83, 1, 0.17)]:
		var backdrop := ColorRect.new()
		backdrop.color = Color(0.015, 0.023, 0.032, 0.72)
		backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
		backdrop.anchor_left = area.position.x
		backdrop.anchor_top = area.position.y
		backdrop.anchor_right = area.end.x
		backdrop.anchor_bottom = area.end.y
		ui.add_child(backdrop)
	var margins := margin_frame(ui, 22)
	margins.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var rows := VBoxContainer.new()
	rows.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margins.add_child(rows)
	var top := HBoxContainer.new()
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	rows.add_child(top)
	var nameplate := VBoxContainer.new()
	nameplate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	nameplate.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(nameplate)
	nameplate.add_child(label("RELAY YARD", 20, GOLD))
	nameplate.add_child(label("SIGHTBREAK / TACTICAL", 12, MUTED))
	var central := VBoxContainer.new()
	central.mouse_filter = Control.MOUSE_FILTER_IGNORE
	top.add_child(central)
	score_label = label("00    /    00", 34)
	score_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	central.add_child(score_label)
	phase_label = label("DEPLOYING", 15, GOLD)
	phase_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	central.add_child(phase_label)
	var side := VBoxContainer.new()
	side.mouse_filter = Control.MOUSE_FILTER_IGNORE
	side.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(side)
	action_label = label("", 16, GOLD)
	action_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	side.add_child(action_label)
	var space := Control.new()
	space.mouse_filter = Control.MOUSE_FILTER_IGNORE
	space.size_flags_vertical = Control.SIZE_EXPAND_FILL
	rows.add_child(space)
	status_label = label("BUY PHASE  /  Press B to equip", 19, GOLD)
	status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	rows.add_child(status_label)
	objective_bar = ProgressBar.new()
	objective_bar.custom_minimum_size = Vector2(180, 8)
	objective_bar.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	objective_bar.show_percentage = false
	objective_bar.max_value = 1.0
	rows.add_child(objective_bar)
	var bottom := HBoxContainer.new()
	bottom.mouse_filter = Control.MOUSE_FILTER_IGNORE
	rows.add_child(bottom)
	health_label = label("100  /  HEALTH", 26)
	health_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	bottom.add_child(health_label)
	var controls := label("B  BUY     E  OBJECTIVE     TAB  TEAM     ESC  MENU", 13, MUTED)
	controls.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	bottom.add_child(controls)
	ammo_label = label("12 / 36", 26)
	ammo_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ammo_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	bottom.add_child(ammo_label)
	crosshair = Control.new()
	crosshair.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fill(crosshair)
	ui.add_child(crosshair)
	crosshair.draw.connect(draw_crosshair)
	touch = Touch.new()
	touch.enabled = DisplayServer.is_touchscreen_available() or bool(profile.data.settings.touch_visible)
	touch.hud_scale = float(profile.data.settings.hud_scale)
	touch.restore_layout(profile.data.settings.hud_positions)
	touch.buy_pressed.connect(show_buy)
	touch.pause_pressed.connect(toggle_pause)
	touch.switch_pressed.connect(func(): switch_requested = true)
	touch.scoreboard_pressed.connect(func(): touch_score_until = elapsed + 4.0)
	touch.layout_changed.connect(func(layout: Dictionary): profile.data.settings.hud_positions = layout; profile.save())
	ui.add_child(touch)

func draw_crosshair() -> void:
	if not is_instance_valid(crosshair): return
	var center: Vector2 = ui.size / 2
	var width: float = profile.data.settings.crosshair_size
	var color := Color(str(profile.data.settings.crosshair_color))
	for direction in [Vector2.LEFT, Vector2.RIGHT, Vector2.UP, Vector2.DOWN]:
		crosshair.draw_line(center + direction * 4, center + direction * (4 + width), Color(0, 0, 0, 0.7), 4)
		crosshair.draw_line(center + direction * 4, center + direction * (4 + width), color, 2)
	crosshair.draw_circle(center, 1.5, color)

func _input(event: InputEvent) -> void:
	if server_mode: return
	if event is InputEventMouseMotion and screen == "game" and not paused and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		mouse_delta += event.relative
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ESCAPE:
			if screen == "game":
				if touch != null and touch.editing:
					touch.editing = false
					profile.data.settings.hud_positions = touch.exported_layout()
					profile.save()
					touch.queue_redraw()
					paused = false
					Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
				else: toggle_pause()
			elif screen != "menu": show_menu()
		elif screen == "game" and not paused and event.keycode == KEY_B:
			show_buy()

func _physics_process(delta: float) -> void:
	if server_mode or screen != "game" or not is_instance_valid(match_game): return
	var actor = match_game.local_actor()
	if actor != null and (input_round != match_game.round_number or input_actor != actor.actor_id):
		input_look = Vector2(actor.yaw, actor.pitch)
		input_round = match_game.round_number
		input_actor = actor.actor_id
	var state: Dictionary = {"move": Vector2.ZERO, "look": input_look}
	if actor != null and actor.weapon_id != cosmetic_weapon:
		actor.apply_cosmetic(current_loadout.get(actor.weapon_id, {}))
		cosmetic_weapon = actor.weapon_id
	if not paused and actor != null:
		var sensitivity := float(profile.data.settings.sensitivity)
		input_look.x -= mouse_delta.x * sensitivity
		input_look.y -= mouse_delta.y * sensitivity
		mouse_delta = Vector2.ZERO
		var move := Vector2(float(Input.is_physical_key_pressed(KEY_D)) - float(Input.is_physical_key_pressed(KEY_A)), float(Input.is_physical_key_pressed(KEY_W)) - float(Input.is_physical_key_pressed(KEY_S)))
		if touch != null:
			move += touch.movement
			var touch_look: Vector2 = touch.consume_look()
			input_look -= touch_look * float(profile.data.settings.touch_sensitivity)
		if not Input.get_connected_joypads().is_empty():
			var device := int(Input.get_connected_joypads()[0])
			move += Vector2(Input.get_joy_axis(device, JOY_AXIS_LEFT_X), -Input.get_joy_axis(device, JOY_AXIS_LEFT_Y)).limit_length()
			var stick := Vector2(Input.get_joy_axis(device, JOY_AXIS_RIGHT_X), Input.get_joy_axis(device, JOY_AXIS_RIGHT_Y))
			if stick.length() > 0.15: input_look -= stick * delta * 2.6
		if bool(profile.data.settings.gyro) and DisplayServer.is_touchscreen_available():
			var gyro := Input.get_gyroscope()
			input_look -= Vector2(gyro.y, gyro.x) * delta * float(profile.data.settings.gyro_sensitivity)
		input_look.y = clampf(input_look.y, -1.45, 1.45)
		state.move = move.limit_length(1.0)
		state.look = input_look
		state.fire = Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT) or Input.get_joy_axis(0, JOY_AXIS_TRIGGER_RIGHT) > 0.4 or touch_action("fire")
		state.reload = Input.is_physical_key_pressed(KEY_R) or Input.is_joy_button_pressed(0, JOY_BUTTON_X) or touch_action("reload")
		state.jump = Input.is_physical_key_pressed(KEY_SPACE) or Input.is_joy_button_pressed(0, JOY_BUTTON_A) or touch_action("jump")
		state.crouch = Input.is_physical_key_pressed(KEY_CTRL) or Input.is_joy_button_pressed(0, JOY_BUTTON_B) or touch_action("crouch")
		state.interact = Input.is_physical_key_pressed(KEY_E) or Input.is_joy_button_pressed(0, JOY_BUTTON_Y) or touch_action("interact")
		state.grenade = Input.is_physical_key_pressed(KEY_G) or touch_action("grenade")
		state.smoke = Input.is_physical_key_pressed(KEY_Q) or touch_action("smoke")
		if switch_requested:
			var index: int = actor.inventory.find(actor.weapon_id)
			state.weapon = actor.inventory[(index + 1) % actor.inventory.size()]
			switch_requested = false
		elif Input.is_physical_key_pressed(KEY_1) and actor.inventory.size() > 1: state.weapon = actor.inventory[-1]
		elif Input.is_physical_key_pressed(KEY_2): state.weapon = "sidearm"
		if actor.camera != null: actor.camera.fov = float(profile.data.settings.fov)
	match_game.set_local_input(state)

func touch_action(action: String) -> bool:
	return touch != null and bool(touch.actions.get(action, false))

func _process(delta: float) -> void:
	elapsed += delta
	if server_mode: return
	if is_instance_valid(menu_camera) and menu_camera.is_inside_tree():
		menu_camera.position = Vector3(27 + sin(elapsed * 0.07) * 4, 18, 30)
		menu_camera.look_at(Vector3.ZERO)
	if smoke_mode:
		smoke_frames += 1
		if smoke_frames == 15:
			print("SIGHTBREAK_MAIN_READY screen=", screen)
			if not smoke_capture.is_empty() and DisplayServer.get_name() != "headless":
				await RenderingServer.frame_post_draw
				get_viewport().get_texture().get_image().save_png(smoke_capture)
			get_tree().quit(0)
	if demo_mode:
		demo_time += delta
		if demo_time > 3.0 and not smoke_capture.is_empty():
			var output_path := smoke_capture
			smoke_capture = ""
			await RenderingServer.frame_post_draw
			get_viewport().get_texture().get_image().save_png(output_path)
			print("SIGHTBREAK_DEMO_CAPTURED")
			get_tree().quit(0)
	if screen != "game" or not is_instance_valid(match_game): return
	var actor = match_game.local_actor()
	score_label.text = "%02d     /     %02d" % [match_game.attack_score, match_game.defend_score]
	phase_label.text = "ROUND %02d   •   %s   •   %02d:%02d" % [match_game.round_number, str(match_game.phase).to_upper(), int(match_game.time_left) / 60, int(match_game.time_left) % 60]
	action_label.text = "DEVICE  %02d s" % int(match_game.objective_timer) if match_game.objective_state == "planted" else str(match_game.objective_state).to_upper()
	if match_game.objective_state == "dropped": action_label.text = "DEVICE DROPPED  /  RECOVER"
	if match_game.phase == "waiting":
		var humans := 0
		for row in match_game.scoreboard():
			if not row.get("bot", true): humans += 1
		status_label.text = "WAITING FOR AUTHENTICATED PLAYERS   %d / 10" % humans
	if is_instance_valid(reward_label):
		reward_label.text = "ACCOUNT REWARDS  /  " + str(match_game.reward_status).to_upper().replace("_", " ")
	objective_bar.value = float(match_game.interaction_progress)
	objective_bar.visible = objective_bar.value > 0
	if actor != null:
		health_label.text = "%03d   /   HEALTH" % maxi(0, int(actor.health)) if actor.alive else "ELIMINATED  /  SPECTATING"
		ammo_label.text = "%s   %02d / %02d" % [str(actor.weapon_id).to_upper(), actor.ammo, actor.reserve]
		if match_game.phase == "buy": status_label.text = "MATCH FUNDS  %d   /   PRESS B TO EQUIP" % actor.credits
		elif match_game.phase != "waiting" and elapsed > float(status_label.get_meta("until", 0.0)): status_label.text = "HOLD E AT A SITE TO PLANT" if actor.team == 0 and str(match_game.objective_state) != "planted" else "HOLD E NEAR THE DEVICE TO DEFUSE" if str(match_game.objective_state) == "planted" else "DEFEND THE TWO OBJECTIVE SITES"
		crosshair.visible = actor.alive and not paused
	if (Input.is_physical_key_pressed(KEY_TAB) or elapsed < touch_score_until) and not paused:
		if not is_instance_valid(score_panel): show_scoreboard()
	elif is_instance_valid(score_panel):
		score_panel.queue_free()
		score_panel = null

func show_notification(message: String) -> void:
	print("MATCH: ", message)
	if is_instance_valid(status_label):
		status_label.text = message
		status_label.set_meta("until", elapsed + 5.0)

func make_overlay(title: String) -> VBoxContainer:
	if is_instance_valid(overlay): overlay.queue_free()
	overlay = ColorRect.new()
	overlay.color = Color(0.015, 0.025, 0.035, 0.92)
	fill(overlay)
	ui.add_child(overlay)
	var margins := margin_frame(overlay, 64)
	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 18)
	margins.add_child(rows)
	rows.add_child(label(title, 38, GOLD))
	paused = true
	if touch != null: touch.reset_input(); touch.enabled = false
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	return rows

func close_overlay() -> void:
	if is_instance_valid(overlay): overlay.queue_free()
	overlay = null
	paused = false
	mouse_delta = Vector2.ZERO
	if touch != null: touch.enabled = DisplayServer.is_touchscreen_available() or bool(profile.data.settings.touch_visible)
	if not DisplayServer.is_touchscreen_available(): Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func toggle_pause() -> void:
	if paused:
		close_overlay()
		return
	var rows := make_overlay("FIELD MENU")
	rows.add_child(label("The match continues while this menu is open.", 18, MUTED))
	rows.add_child(button("RESUME", close_overlay))
	rows.add_child(button("EDIT TOUCH HUD", func():
		close_overlay()
		touch.enabled = true
		touch.editing = true
		touch.queue_redraw()
		paused = true
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		var done := button("SAVE TOUCH LAYOUT", func():
			touch.editing = false
			profile.data.settings.hud_positions = touch.exported_layout()
			profile.save()
			build_hud()
			paused = false
		)
		done.position = Vector2(480, 130)
		done.custom_minimum_size = Vector2(280, 60)
		ui.add_child(done)
	))
	rows.add_child(button("LEAVE MATCH", leave_match))

func show_buy() -> void:
	if not is_instance_valid(match_game): return
	var rows := make_overlay("REQUISITION  /  MATCH EQUIPMENT")
	var actor = match_game.local_actor()
	var funds := int(actor.credits) if actor != null else 0
	rows.add_child(label("Available: %d match funds   •   Purchases are validated during the buy phase." % funds, 18, MUTED))
	var weapons = load("res://scripts/gameplay/weapons.gd")
	var catalog: Dictionary = weapons.DATA
	for key in catalog:
		var weapon_key: String = key
		var definition: Dictionary = catalog[key]
		rows.add_child(button("%s     /     %d" % [str(definition.get("name", key)).to_upper(), int(definition.get("cost", 0))], func():
			match_game.request_buy(weapon_key)
			close_overlay()
		))
	rows.add_child(button("BACK TO FIELD", close_overlay))

func show_scoreboard() -> void:
	score_panel = PanelContainer.new()
	score_panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	score_panel.position = ui.size * Vector2(0.18, 0.18)
	score_panel.custom_minimum_size = ui.size * Vector2(0.64, 0.60)
	ui.add_child(score_panel)
	var rows := VBoxContainer.new()
	score_panel.add_child(rows)
	rows.add_child(label("TEAM ROSTER     /     K  ·  A  ·  D", 24, GOLD))
	for actor in match_game.scoreboard():
		rows.add_child(label("%s    %s        %d  /  %d  /  %d" % ["ATK" if int(actor.get("team", 0)) == 0 else "DEF", str(actor.get("name", actor.get("display_name", "Operator"))), int(actor.get("kills", 0)), int(actor.get("assists", 0)), int(actor.get("deaths", 0))], 19))

func on_match_finished(summary: Dictionary) -> void:
	if server_mode: return
	var reward: Dictionary = {}
	if match_game.options.get("mode", "offline") == "offline": reward = profile.record_match(summary)
	var rows := make_overlay("OPERATION COMPLETE")
	rows.add_child(label("FINAL SCORE   %02d  /  %02d" % [match_game.attack_score, match_game.defend_score], 30))
	if not reward.is_empty():
		rows.add_child(label("OFFLINE TRAINING  +%d XP    +%d CREDITS    LEVEL %d" % [reward.xp, reward.credits, reward.level], 20, GOLD))
		if reward.save_error != OK: rows.add_child(label("Local progress could not be saved. Check device storage.", 18, CRIMSON))
	elif str(match_game.reward_status) != "unranked":
		reward_label = label("ACCOUNT REWARDS  /  " + str(match_game.reward_status).to_upper(), 18, MUTED)
		rows.add_child(reward_label)
	else: rows.add_child(label("Unranked LAN result. No online wallet or inventory rewards.", 18, MUTED))
	rows.add_child(button("RETURN TO OPERATIONS", leave_match))

func leave_match() -> void:
	if server_mode:
		get_tree().quit(1)
		return
	if is_instance_valid(match_game):
		remove_child(match_game)
		match_game.queue_free()
		match_game = null
	multiplayer.multiplayer_peer = null
	show_menu()
