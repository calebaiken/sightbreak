extends Node

const Profile = preload("res://scripts/profile.gd")
const OfflineDiagnostics = preload("res://scripts/offline_diagnostics.gd")
const Touch = preload("res://scripts/ui/touch_controls.gd")
const SafeArea = preload("res://scripts/ui/safe_area.gd")
const Design = preload("res://scripts/ui/design_tokens.gd")
const Radar = preload("res://scripts/ui/radar.gd")
const WeaponGlyph = preload("res://scripts/ui/weapon_glyph.gd")
const Weapons = preload("res://scripts/gameplay/weapons.gd")
const BG := Design.OBSIDIAN
const PANEL := Design.GRAPHITE
const MUTED := Design.STEEL
const GOLD := Design.GOLD
const CRIMSON := Design.CRIMSON
const KILL_FEED_SECONDS := 5.0
const KILL_FEED_ROWS := 4
const KILL_FEED_GAP := 3
## Clearance between the status line and a touch target, and the status band's height in
## lines (a notification can wrap to three lines at the largest text size).
## Clearance between the status line and anything it must not cover.
const STATUS_TOUCH_GAP := 8.0
## The status line wraps to at most this many lines.
const STATUS_MAX_LINES := 3
## Each extra line costs as much as this fraction of the row's width of distance from
## the centre, so the line wraps rather than moving far aside, but not into a column.
const STATUS_LINE_COST := 0.25
## When no stretch of its row is clear, the line rises, but its top stays below this
## fraction of the HUD's height (the reticle is at 0.5).
const STATUS_RISE_LIMIT := 0.58
const KILL_FEED_SEPARATION := 6
const TEXT_SCALES := [0.9, 1.0, 1.15, 1.3]
const WEAPON_ROLES := {"sidearm": "SIDEARM", "smg": "SMG", "rifle": "RIFLE", "marksman": "MARKSMAN"}
var profile = Profile.new()
var offline_diagnostics
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
var physical_mouse_fire := false
var status_label: Label
var status_row: Control
var status_fit_key: Array = []
var score_label: Label
var phase_label: Label
var squad_label: Label
var ammo_label: Label
var utility_label: Label
var funds_label: Label
var health_label: Label
var health_bar: ProgressBar
var action_label: Label
var hud_action_margin: MarginContainer
var hud_controls: Label
var hud_touch_mode := -1
var crosshair: Control
var radar: Control
var attack_pips: Control
var defend_pips: Control
var kill_feed: VBoxContainer
var kill_feed_frame: Control
var kill_feed_reserve := 0.0
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
var application_focused := true
var applied_window_mode := -1
var waiting_for_input_release := false
var reward_label: Label
var current_loadout: Dictionary = {}
var cosmetic_weapon := ""
var match_suspended := false

func _ready() -> void:
	var startup_probe := "--smoke" in OS.get_cmdline_user_args()
	if startup_probe: print("SIGHTBREAK_STARTUP phase=ready_enter msec=", Time.get_ticks_msec())
	profile.load_profile()
	Input.use_accumulated_input = false
	apply_settings()
	if startup_probe: print("SIGHTBREAK_STARTUP phase=settings_applied msec=", Time.get_ticks_msec())
	var args := OS.get_cmdline_user_args()
	offline_diagnostics = OfflineDiagnostics.create(args, profile.data)
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
	if startup_probe: print("SIGHTBREAK_STARTUP phase=menu_begin msec=", Time.get_ticks_msec())
	show_menu()
	if startup_probe: print("SIGHTBREAK_STARTUP phase=menu_constructed msec=", Time.get_ticks_msec())
	if demo_mode: start_match({"mode": "offline", "difficulty": "normal", "name": "Operator"})

func text_scale() -> float:
	return clampf(float(profile.data.settings.get("ui_text_scale", 1.0)), 0.85, 1.3)

func build_theme() -> Theme:
	return Design.build_theme(text_scale())

func box(color: Color, _radius: int = 0, border: Color = Color.TRANSPARENT) -> StyleBoxFlat:
	return Design.box(color, border)

func label(text: String, font_size: int = 18, color: Color = Design.TEXT, heading := false) -> Label:
	var node := Design.label(text, int(round(font_size * text_scale())), color, heading)
	return node

func wrapped_label(text: String, font_size: int = 18, color: Color = Design.TEXT) -> Label:
	var node := label(text, font_size, color)
	node.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	node.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return node

func scroll_rows(parent: Control) -> VBoxContainer:
	var scroll := ScrollContainer.new()
	scroll.name = "ContentScroll"
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	parent.add_child(scroll)
	var content := VBoxContainer.new()
	content.name = "ScrollRows"
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", Design.SPACE_M)
	scroll.add_child(content)
	return content

## Capability reporting is separate from the player's selected control mode.
## A touchscreen laptop is still a desktop; a controller never selects touch.
func input_capabilities() -> Dictionary:
	return {"mobile": OS.has_feature("mobile"), "touchscreen": DisplayServer.is_touchscreen_available()}

func uses_touch_controls() -> bool:
	return bool(input_capabilities().mobile) or bool(profile.data.settings.touch_visible)

func update_pointer_mode() -> void:
	sync_hud_input_mode()
	var capture := application_focused and screen == "game" and not paused and not uses_touch_controls()
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED if capture else Input.MOUSE_MODE_VISIBLE
	if is_instance_valid(touch) and not touch.editing:
		touch.enabled = uses_touch_controls() and not paused and application_focused

## Selected mode also controls the HUD while a menu temporarily disables touch.
## Preserve the current HUD, overlay, feed and saved touch layout on a mode change.
func sync_hud_input_mode() -> void:
	if not is_instance_valid(hud_action_margin) or not is_instance_valid(hud_controls): return
	var touch_mode := uses_touch_controls()
	if hud_touch_mode == int(touch_mode): return
	hud_touch_mode = int(touch_mode)
	hud_action_margin.add_theme_constant_override("margin_right", 80 if touch_mode else 0)
	hud_controls.visible = not touch_mode

func connected_controllers() -> Array[int]:
	return Input.get_connected_joypads()

func controller_axis(device: int, axis: int) -> float:
	return Input.get_joy_axis(device, axis)

func controller_button(device: int, key: int) -> bool:
	return Input.is_joy_button_pressed(device, key)

## Focus loss cannot rely on an OS delivering every key/button-up event.
## Require neutral controls after explicit resume before accepting held input.
func controls_released() -> bool:
	for key in [KEY_W, KEY_A, KEY_S, KEY_D, KEY_R, KEY_E, KEY_SPACE, KEY_CTRL, KEY_G, KEY_Q, KEY_1, KEY_2]:
		if Input.is_physical_key_pressed(key): return false
	if Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT): return false
	var pads := connected_controllers()
	if not pads.is_empty():
		var device := pads[0]
		if Vector2(controller_axis(device, JOY_AXIS_LEFT_X), controller_axis(device, JOY_AXIS_LEFT_Y)).length() > 0.15: return false
		if Vector2(controller_axis(device, JOY_AXIS_RIGHT_X), controller_axis(device, JOY_AXIS_RIGHT_Y)).length() > 0.15: return false
		if controller_axis(device, JOY_AXIS_TRIGGER_RIGHT) > 0.4: return false
		for key in [JOY_BUTTON_A, JOY_BUTTON_B, JOY_BUTTON_X, JOY_BUTTON_Y]:
			if controller_button(device, key): return false
	return true

func button(text: String, callback: Callable, height: float = 48, variant := "secondary") -> Button:
	var node := Button.new()
	node.text = text
	node.custom_minimum_size.y = maxf(height, Design.TOUCH_MIN)
	node.pressed.connect(callback)
	node.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	if variant != "secondary":
		Design.apply_button(node, variant)
	return node

func fill(node: Control) -> void:
	node.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

## A short accent rule, or a full-width hairline when width is zero.
func divider(width: float = 64, color: Color = GOLD) -> ColorRect:
	var rule := ColorRect.new()
	rule.color = color
	rule.custom_minimum_size = Vector2(width, 2 if width > 0 else 1)
	rule.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN if width > 0 else Control.SIZE_EXPAND_FILL
	rule.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return rule

func section(parent: Control, title: String) -> void:
	var header := VBoxContainer.new()
	header.add_theme_constant_override("separation", Design.SPACE_XS)
	parent.add_child(header)
	header.add_child(label(title, Design.TYPE_SMALL, GOLD, true))
	header.add_child(divider(0, Design.LINE))

func clear_ui() -> void:
	if ui == null: return
	for child in ui.get_children():
		ui.remove_child(child)
		child.queue_free()
	status_label = null
	status_row = null
	status_fit_key = []
	hud_action_margin = null
	hud_controls = null
	hud_touch_mode = -1
	overlay = null
	touch = null
	crosshair = null
	score_panel = null
	radar = null
	kill_feed = null

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

## Left-to-right scrim: legible menu column without hiding the live yard.
func scrim(strength_left: float, strength_right: float) -> Control:
	var shade := Control.new()
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fill(shade)
	shade.draw.connect(func():
		var left := Color(BG, strength_left)
		var right := Color(BG, strength_right)
		shade.draw_polygon(PackedVector2Array([Vector2.ZERO, Vector2(shade.size.x, 0), shade.size, Vector2(0, shade.size.y)]), PackedColorArray([left, right, right, left]))
	)
	shade.resized.connect(shade.queue_redraw)
	return shade

## Darkening along the top and bottom edges of the menu, under the build line, the operation
## notes and the footer, which sit straight on the lit yard. Measured: with only the left-to-right
## scrim those lines read at a contrast of 1.3 to 2.9 (WCAG asks 4.5); see menu_contrast_probe.gd.
func menu_bands(strength: float) -> Control:
	var bands := Control.new()
	bands.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fill(bands)
	bands.draw.connect(func():
		var dark := Color(BG, strength)
		var clear := Color(BG, 0.0)
		var top := minf(150.0, bands.size.y * 0.25)
		var bottom := minf(190.0, bands.size.y * 0.3)
		bands.draw_polygon(PackedVector2Array([Vector2.ZERO, Vector2(bands.size.x, 0), Vector2(bands.size.x, top), Vector2(0, top)]), PackedColorArray([dark, dark, clear, clear]))
		bands.draw_polygon(PackedVector2Array([Vector2(0, bands.size.y - bottom), Vector2(bands.size.x, bands.size.y - bottom), bands.size, Vector2(0, bands.size.y)]), PackedColorArray([clear, clear, dark, dark]))
	)
	bands.resized.connect(bands.queue_redraw)
	return bands

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
	apply_settings()

## Menu text, by id, in one table so a translation can replace it (menu_labels).
const MENU_LABELS := {
	"deploy": "DEPLOY   ·   OFFLINE 5V5", "lan": "LOCAL NETWORK   ·   DIRECT CONNECT",
	"inventory": "INVENTORY", "cases": "CASES", "market": "MARKET", "trades": "TRADES",
	"record": "OPERATOR RECORD", "settings": "SETTINGS",
	"tagline": "PRECISION · PRESSURE · PURPOSE", "operation": "CURRENT OPERATION",
	"operation_note": "2 SITES  ·  3 ROUTES  ·  FIRST TO 7", "callsign": "CALLSIGN",
	"policy": "EARNED IN PLAY  ·  NO REAL-MONEY PURCHASES",
	"build": "DEVELOPMENT BUILD",
	"record_title": "TRAINING RECORD  ·  THIS DEVICE", "level": "LEVEL", "xp_to": "XP TO LEVEL",
	"credits": "TRAINING CREDITS", "matches": "MATCHES", "wins": "WINS",
	"eliminations": "ELIMINATIONS", "deaths": "DEATHS", "online": "ONLINE", "earned": "EARNED CREDITS",
	"account_loading": "LOADING ACCOUNT…", "account_unloaded": "ACCOUNT NOT LOADED",
	"credits_unavailable": "EARNED CREDITS UNAVAILABLE", "session_ended": "SESSION ENDED",
	"sign_in_again": "SIGN IN AGAIN IN THE ARMORY", "last_confirmed": "LAST CONFIRMED",
}
## Slack that side-by-side menu columns must keep; below it they stack instead.
const MENU_SAFETY := 32.0
const MENU_COLUMN_GAP := 24.0
var menu_labels: Dictionary = {}
var menu_layout := {}

func menu_text(id: String) -> String:
	if id == "build": return "DEVELOPMENT BUILD  ·  " + str(ProjectSettings.get_setting("application/config/version"))
	return str(menu_labels.get(id, MENU_LABELS[id]))

## Space the menu's content may use: the safe area less the frame's margins.
func menu_region() -> Vector2:
	var safe: Rect2 = SafeArea.viewport_rect(get_viewport().get_visible_rect().size)
	return safe.size - Vector2.ONE * 72.0

func show_menu() -> void:
	if is_instance_valid(economy_panel): economy_panel.hide()
	screen = "menu"
	paused = false
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	clear_ui()
	ensure_menu_world()
	menu_world.show()
	ui.add_child(scrim(0.94, 0.62))
	ui.add_child(menu_bands(0.86))
	var margins := margin_frame(ui)
	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", Design.SPACE_L)
	margins.add_child(rows)
	var top := HBoxContainer.new()
	rows.add_child(top)
	top.add_child(label("S / B", Design.TYPE_SMALL, GOLD, true))
	top.add_child(label("TACTICAL OPERATIONS", Design.TYPE_SMALL, MUTED, true))
	# The build label takes the rest of the row, right-aligned: it truncates only if the
	# row is too narrow for it, and never collapses.
	var build := Design.ellipsize(label(menu_text("build"), Design.TYPE_MICRO + 1, MUTED))
	build.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	top.add_child(build)
	# The columns sit in a vertical scroller, so content taller than the screen scrolls
	# instead of leaving it, and a horizontal scroller is never needed: the layout below
	# chooses side-by-side or stacked from measured widths.
	var scroll := ScrollContainer.new()
	scroll.name = "MenuScroll"
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	scroll.follow_focus = true
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	rows.add_child(scroll)
	var middle := BoxContainer.new()
	middle.name = "MenuColumns"
	middle.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	middle.size_flags_vertical = Control.SIZE_EXPAND_FILL
	middle.add_theme_constant_override("separation", int(MENU_COLUMN_GAP))
	scroll.add_child(middle)
	var footer := HBoxContainer.new()
	rows.add_child(footer)
	var callsign := Design.ellipsize(label("%s   ·   %s" % [menu_text("callsign"), Design.plain_line(str(profile.data.display_name)).to_upper()], Design.TYPE_SMALL, MUTED))
	callsign.set_meta("user_text", true)
	footer.add_child(callsign)
	footer.add_child(label(menu_text("policy"), Design.TYPE_MICRO + 1, GOLD))
	# Measure, then choose. Both columns are built, measured with the real theme and
	# fonts, and only then placed: side by side if their widths and the safety slack fit
	# the region, stacked if not; compact (no tagline, tighter spacing) if the full
	# variant is taller than the room. Nothing here depends on the layout's own result.
	var region := menu_region()
	var compact := false
	var columns := {}
	var side_by_side := true
	var content_height := 0.0
	var room_height := 0.0
	for attempt in 2:
		columns = menu_columns(region, compact)
		middle.add_child(columns.left)
		middle.add_child(columns.right)
		menu_fit_nav(columns.left, region)
		var left_min: Vector2 = columns.left.get_combined_minimum_size()
		var right_min: Vector2 = columns.right.get_combined_minimum_size()
		side_by_side = left_min.x + right_min.x + MENU_COLUMN_GAP + MENU_SAFETY <= region.x
		content_height = maxf(left_min.y, right_min.y) if side_by_side else left_min.y + MENU_COLUMN_GAP + right_min.y
		room_height = region.y - top.get_combined_minimum_size().y - footer.get_combined_minimum_size().y - 2 * Design.SPACE_L
		if compact or content_height <= room_height:
			break
		for column: Control in [columns.left, columns.right]:
			middle.remove_child(column)
			column.free()
		compact = true
	middle.vertical = not side_by_side
	var right: Control = columns.right
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL if side_by_side else Control.SIZE_FILL
	right.size_flags_vertical = Control.SIZE_SHRINK_END if side_by_side else Control.SIZE_SHRINK_BEGIN
	for line: Control in right.get_children():
		if line is Label:
			line.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT if side_by_side else HORIZONTAL_ALIGNMENT_LEFT
	menu_layout = {"side_by_side": side_by_side, "compact": compact, "content_height": content_height, "room_height": room_height, "region": region, "slack": region.x - (columns.left.get_combined_minimum_size().x + columns.right.get_combined_minimum_size().x + MENU_COLUMN_GAP) if side_by_side else INF}

## A navigation entry that cannot widen its column: its text truncates instead.
func menu_entry(id: String, text: String, callback: Callable, height: float, variant := "secondary") -> Button:
	var entry := button(text, callback, height, variant)
	entry.name = "Menu_" + id
	entry.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	entry.tooltip_text = text.replace("   ", " ")
	return entry

func menu_columns(region: Vector2, compact: bool) -> Dictionary:
	var separation: int = Design.SPACE_S if compact else Design.SPACE_M
	var left := VBoxContainer.new()
	left.name = "MenuNav"
	left.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	left.add_theme_constant_override("separation", separation)
	var wordmark_size := Design.fit_font_size("SIGHTBREAK", Design.TYPE_DISPLAY, minf(440.0, region.x))
	left.set_meta("wordmark_size", wordmark_size)
	left.add_child(_wordmark(wordmark_size))
	if not compact:
		left.add_child(label(menu_text("tagline"), Design.TYPE_SMALL, GOLD, true))
		left.add_child(divider(72))
	var play := menu_entry("deploy", menu_text("deploy"), func(): start_match({"mode": "offline", "difficulty": ["easy", "normal", "hard"][clampi(int(profile.data.settings.difficulty), 0, 2)], "name": profile.data.display_name}), 60, "primary")
	play.add_theme_font_override("font", Design.heading_font())
	left.add_child(play)
	left.add_child(menu_entry("lan", menu_text("lan"), show_connect, Design.TOUCH_MIN))
	var grid := GridContainer.new()
	grid.name = "ArmoryEntries"
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", Design.SPACE_S)
	grid.add_theme_constant_override("v_separation", Design.SPACE_S)
	left.add_child(grid)
	for tab in ["inventory", "cases", "market", "trades"]:
		var tab_name: String = tab
		grid.add_child(menu_entry(tab_name, menu_text(tab_name), func(): open_economy(tab_name), Design.TOUCH_MIN))
	grid.add_child(menu_entry("record", menu_text("record"), show_progress, Design.TOUCH_MIN))
	grid.add_child(menu_entry("settings", menu_text("settings"), show_settings, Design.TOUCH_MIN))
	var right := VBoxContainer.new()
	right.name = "MenuStatus"
	right.alignment = BoxContainer.ALIGNMENT_END
	right.add_theme_constant_override("separation", Design.SPACE_XS)
	right.add_child(menu_record_card())
	var record_gap := Control.new()
	record_gap.custom_minimum_size.y = Design.SPACE_M if compact else Design.SPACE_L
	right.add_child(record_gap)
	if not compact:
		var kicker := label(menu_text("operation"), Design.TYPE_SMALL, Design.STEEL_BRIGHT, true)
		right.add_child(kicker)
	right.add_child(label("RELAY YARD", 36, Design.TEXT, true))
	right.add_child(label(menu_text("operation_note"), Design.TYPE_SMALL, GOLD))
	return {"left": left, "right": right}

## Sets the nav column's width from its entries' natural widths, measured once the
## column is in the tree (so with the real theme and fonts), then lets every entry
## truncate: a string longer than the column can no longer widen it.
func menu_fit_nav(left: Control, region: Vector2) -> void:
	var grid := left.find_child("ArmoryEntries", true, false) as GridContainer
	var natural := wordmark_width(int(left.get_meta("wordmark_size")))
	# Each entry keeps its own natural width as a floor (capped at what the region can
	# give it) and only then may truncate; otherwise the grid would hand a cell less
	# than its text needs.
	for entry: Button in left.find_children("Menu_*", "Button", true, false):
		var cap := (region.x - grid.get_theme_constant("h_separation")) * 0.5 if entry.get_parent() == grid else region.x
		entry.custom_minimum_size.x = minf(entry.get_combined_minimum_size().x, cap)
		entry.clip_text = true
		entry.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		if entry.get_parent() != grid:
			natural = maxf(natural, entry.custom_minimum_size.x)
	natural = maxf(natural, grid.get_combined_minimum_size().x)
	left.custom_minimum_size.x = minf(natural, region.x)

## The wordmark: display type that does not scale with the text-size setting (it is a
## headline, not body text) but is fitted to its column's width.
func _wordmark(size: int) -> Label:
	var node := Design.label("SIGHTBREAK", size, Design.TEXT, true)
	node.name = "Wordmark"
	return node

func wordmark_width(size: int) -> float:
	return Design.heading_font().get_string_size("SIGHTBREAK", HORIZONTAL_ALIGNMENT_LEFT, -1, size).x

## The main menu's record: the offline training level with its distance to the next
## level (Profile.xp_for_level), training credits, matches, wins, eliminations and
## deaths, all from the profile, and the online identity and earned Credits only while
## signed in. Training credits and earned Credits stay on separate lines; no statistic
## appears that the profile or account does not store. Names truncate, never widen it.
func menu_record_card() -> PanelContainer:
	var card := PanelContainer.new()
	card.name = "RecordCard"
	card.add_theme_stylebox_override("panel", Design.box(Color(Design.GRAPHITE, 0.82), Design.LINE, 1, Vector2(Design.SPACE_L, Design.SPACE_M)))
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card.custom_minimum_size.x = 260
	var stack := VBoxContainer.new()
	stack.add_theme_constant_override("separation", Design.SPACE_XS)
	card.add_child(stack)
	stack.add_child(Design.ellipsize(label(menu_text("record_title"), Design.TYPE_MICRO, MUTED, true)))
	var xp := int(profile.data.xp)
	var level := Profile.level_for_xp(xp)
	var floor_xp := Profile.xp_for_level(level)
	var next_xp := Profile.xp_for_level(level + 1)
	stack.add_child(label("%s %02d" % [menu_text("level"), level], Design.TYPE_H3, Design.TEXT, true))
	var to_next := Design.ellipsize(label("%d %s %02d" % [next_xp - xp, menu_text("xp_to"), level + 1], Design.TYPE_SMALL, GOLD))
	to_next.name = "XPToNext"
	stack.add_child(to_next)
	var progress := ProgressBar.new()
	progress.name = "LevelProgress"
	progress.show_percentage = false
	progress.max_value = float(next_xp - floor_xp)
	progress.value = float(xp - floor_xp)
	progress.custom_minimum_size.y = 5
	progress.add_theme_stylebox_override("background", Design.box(Design.OBSIDIAN, Color.TRANSPARENT, 0, Vector2.ZERO))
	progress.add_theme_stylebox_override("fill", Design.box(Design.GOLD, Color.TRANSPARENT, 0, Vector2.ZERO))
	stack.add_child(progress)
	stack.add_child(Design.ellipsize(label("%d %s" % [int(profile.data.credits), menu_text("credits")], Design.TYPE_MICRO + 1, Design.STEEL_BRIGHT)))
	stack.add_child(Design.ellipsize(label("%d %s   ·   %d %s" % [int(profile.data.matches), menu_text("matches"), int(profile.data.wins), menu_text("wins")], Design.TYPE_MICRO + 1, MUTED)))
	stack.add_child(Design.ellipsize(label("%d %s   ·   %d %s" % [int(profile.data.kills), menu_text("eliminations"), int(profile.data.deaths), menu_text("deaths")], Design.TYPE_MICRO + 1, MUTED)))
	if is_instance_valid(economy_panel):
		# Only what the server has said: an account that has not loaded has no name and no
		# balance here, and a balance is never shown as 0 because it is missing.
		var summary: Dictionary = economy_panel.account_summary()
		if summary.state != "signed_out":
			var who: String = Design.plain_line(str(summary.name)).to_upper()
			var identity_line := menu_text("online")
			var credits_line := menu_text("credits_unavailable")
			match summary.state:
				"expired":
					identity_line = menu_text("session_ended")
					credits_line = menu_text("sign_in_again")
				"loading":
					identity_line += "   ·   " + menu_text("account_loading")
				"unavailable":
					identity_line += "   ·   " + menu_text("account_unloaded")
				_:
					identity_line += "   ·   " + who if not who.is_empty() else ""
					if not str(summary.credits).is_empty():
						credits_line = "%s %s" % [summary.credits, menu_text("earned")]
						if summary.state == "stale":
							credits_line += "   ·   " + menu_text("last_confirmed")
			var online := Design.ellipsize(label(identity_line, Design.TYPE_MICRO + 1, GOLD))
			online.name = "OnlineIdentity"
			online.set_meta("user_text", true)
			stack.add_child(online)
			var online_credits := Design.ellipsize(label(credits_line, Design.TYPE_MICRO + 1, GOLD))
			online_credits.name = "OnlineCredits"
			stack.add_child(online_credits)
	return card

func panel_screen(title: String, subtitle: String, back: Callable = show_menu) -> VBoxContainer:
	clear_ui()
	var shade := ColorRect.new()
	shade.color = Color(BG, 0.96)
	fill(shade)
	ui.add_child(shade)
	var margins := margin_frame(ui, 32)
	var rows := VBoxContainer.new()
	margins.add_child(rows)
	var top := HBoxContainer.new()
	rows.add_child(top)
	top.add_child(button("←  BACK", back, Design.TOUCH_MIN, "ghost"))
	top.add_child(wrapped_label(title, Design.TYPE_H1))
	(top.get_child(1) as Label).add_theme_font_override("font", Design.heading_font())
	rows.add_child(wrapped_label(subtitle, Design.TYPE_SMALL, MUTED))
	return scroll_rows(rows)

func show_connect() -> void:
	screen = "connect"
	var rows := panel_screen("LOCAL NETWORK", "Unranked LAN sessions  ·  The server owns movement, combat and round rules  ·  No online economy rewards")
	section(rows, "JOIN A DEDICATED SERVER")
	var address := LineEdit.new()
	address.custom_minimum_size.y = Design.TOUCH_MIN
	address.placeholder_text = "Server address"
	address.text = "127.0.0.1"
	rows.add_child(address)
	var port := SpinBox.new()
	port.custom_minimum_size.y = Design.TOUCH_MIN
	port.min_value = 1024
	port.max_value = 65535
	port.value = 27020
	port.prefix = "UDP port"
	rows.add_child(port)
	rows.add_child(button("JOIN GUEST LAN MATCH", func(): start_match({"mode": "client", "address": address.text.strip_edges(), "port": int(port.value), "name": profile.data.display_name}), Design.TOUCH_MIN, "primary"))
	section(rows, "ACCOUNT SERVER")
	var server_id := LineEdit.new()
	server_id.custom_minimum_size.y = Design.TOUCH_MIN
	server_id.text = "local-relay"
	server_id.placeholder_text = "Account server ID"
	rows.add_child(server_id)
	var account_status := wrapped_label("Account sessions start when ten signed-in players have joined. Sign in through the armory first.", Design.TYPE_SMALL, MUTED)
	rows.add_child(account_status)
	var account_join := button("JOIN ACCOUNT SERVER", func(): pass)
	account_join.pressed.connect(func(): connect_account(address.text.strip_edges(), int(port.value), server_id.text.strip_edges(), account_status, account_join))
	rows.add_child(account_join)
	rows.add_child(wrapped_label("Ask the host for its address. UDP port 27020 must be reachable on your local network. Internet matchmaking and server discovery are not available in this build.", Design.TYPE_SMALL, MUTED))

func connect_account(address: String, port: int, server_id: String, feedback: Label, submit: Button) -> void:
	if not is_instance_valid(economy_panel) or economy_panel.api.token.is_empty():
		feedback.text = "Sign in at ARMORY → PROFILE, then return here."
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
	var rows := panel_screen("OPERATOR RECORD", "Offline training record  ·  Separate from online accounts and tradable inventory")
	rows.add_child(wrapped_label("LEVEL %d   ·   %d XP   ·   %d TRAINING CREDITS" % [profile.data.level, profile.data.xp, profile.data.credits], 26, GOLD))
	rows.add_child(wrapped_label("%d MATCHES   ·   %d WINS   ·   %d ELIMINATIONS   ·   %d DEATHS" % [profile.data.matches, profile.data.wins, profile.data.kills, profile.data.deaths], Design.TYPE_H3))
	section(rows, "CALLSIGN")
	var name_row := HBoxContainer.new()
	rows.add_child(name_row)
	var display := LineEdit.new()
	display.text = profile.data.display_name
	display.max_length = 20
	display.custom_minimum_size.y = Design.TOUCH_MIN
	display.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name_row.add_child(display)
	name_row.add_child(button("SAVE NAME", func():
		profile.data.display_name = display.text.strip_edges() if not display.text.strip_edges().is_empty() else "Operator"
		profile.save()
	))
	rows.add_child(button("ONLINE ACCOUNT & INVENTORY", func(): open_economy("profile")))
	section(rows, "RECENT TRAINING")
	var history := VBoxContainer.new()
	rows.add_child(history)
	if profile.data.history.is_empty(): history.add_child(wrapped_label("Complete an offline match to establish your training record.", Design.TYPE_BODY, MUTED))
	for result in profile.data.history:
		history.add_child(wrapped_label("%s   ·   %s   ·   %d eliminations   ·   +%d Credits" % [result.get("time", ""), "VICTORY" if result.get("won", false) else "DEFEAT", int(result.get("kills", 0)), int(result.get("credits_earned", 0))], Design.TYPE_SMALL + 1, MUTED))

func setting_slider(parent: VBoxContainer, title: String, key: String, low: float, high: float, step: float, percent := false) -> void:
	var row := HBoxContainer.new()
	parent.add_child(row)
	row.custom_minimum_size.y = Design.TOUCH_MIN
	var caption := label(title, Design.TYPE_BODY)
	caption.custom_minimum_size.x = 250
	row.add_child(caption)
	var slider := HSlider.new()
	slider.min_value = low
	slider.max_value = high
	slider.step = step
	slider.value = float(profile.data.settings[key])
	slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	slider.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(slider)
	var format := func(v: float) -> String: return "%d%%" % int(round(v * 100)) if percent else str(v)
	var value := label(format.call(slider.value), Design.TYPE_BODY, GOLD)
	value.custom_minimum_size.x = 90
	value.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	row.add_child(value)
	slider.value_changed.connect(func(v: float):
		profile.data.settings[key] = v
		value.text = format.call(v)
		profile.save()
		apply_settings()
	)

func setting_toggle(parent: VBoxContainer, title: String, key: String) -> void:
	var check := CheckButton.new()
	check.custom_minimum_size.y = Design.TOUCH_MIN
	check.text = title
	check.button_pressed = bool(profile.data.settings[key])
	check.toggled.connect(func(value: bool): profile.data.settings[key] = value; profile.save())
	parent.add_child(check)

func setting_choice(parent: Control, title: String, choices: Array, selected: int, on_select: Callable) -> void:
	var row := HBoxContainer.new()
	parent.add_child(row)
	var caption := label(title, Design.TYPE_BODY)
	caption.custom_minimum_size.x = 250
	row.add_child(caption)
	var options := OptionButton.new()
	options.custom_minimum_size.y = Design.TOUCH_MIN
	options.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	for choice in choices: options.add_item(str(choice))
	options.select(clampi(selected, 0, choices.size() - 1))
	options.item_selected.connect(on_select)
	row.add_child(options)

func show_settings() -> void:
	screen = "settings"
	var rows := panel_screen("FIELD SETTINGS", "Saved on this device. Touch HUD layouts are editable during a match from the field menu.")
	populate_settings(rows)

func populate_settings(rows: VBoxContainer) -> void:
	section(rows, "CONTROLS")
	setting_slider(rows, "MOUSE SENSITIVITY", "sensitivity", 0.0005, 0.008, 0.0001)
	setting_slider(rows, "TOUCH SENSITIVITY", "touch_sensitivity", 0.001, 0.012, 0.0002)
	setting_slider(rows, "TOUCH BUTTON SIZE", "hud_scale", 0.7, 1.5, 0.05, true)
	setting_toggle(rows, "GYROSCOPE AIMING (supported devices)", "gyro")
	setting_toggle(rows, "SHOW TOUCH CONTROLS ON DESKTOP", "touch_visible")
	section(rows, "DISPLAY & PERFORMANCE")
	if not OS.has_feature("mobile"):
		setting_choice(rows, "WINDOW MODE", ["WINDOWED", "BORDERLESS FULLSCREEN", "EXCLUSIVE FULLSCREEN"], int(profile.data.settings.window_mode), func(index: int): profile.data.settings.window_mode = index; profile.save(); apply_settings())
	setting_choice(rows, "GRAPHICS", SBGraphicsQuality.available_labels(), SBGraphicsQuality.clamp_tier(int(profile.data.settings.graphics_quality)), func(index: int): profile.data.settings.graphics_quality = index; profile.save(); apply_settings())
	setting_slider(rows, "3D RENDER SCALE", "render_scale", 0.5, 1.0, 0.05, true)
	var limits := [30, 60, 90, 120]
	setting_choice(rows, "FRAME LIMIT", limits, limits.find(int(profile.data.settings.fps_limit)), func(index: int): profile.data.settings.fps_limit = limits[index]; profile.save(); apply_settings())
	setting_slider(rows, "FIELD OF VIEW", "fov", 60, 100, 1)
	section(rows, "ACCESSIBILITY")
	var scale_labels: Array = []
	for value in TEXT_SCALES: scale_labels.append("%d%%" % int(round(value * 100)))
	var current_scale := 0
	for i in range(TEXT_SCALES.size()):
		if absf(TEXT_SCALES[i] - text_scale()) < absf(TEXT_SCALES[current_scale] - text_scale()): current_scale = i
	setting_choice(rows, "INTERFACE TEXT SIZE", scale_labels, current_scale, func(index: int):
		profile.data.settings.ui_text_scale = TEXT_SCALES[index]
		profile.save()
		ui.theme = build_theme()
		refresh_settings.call_deferred()
	)
	setting_toggle(rows, "REDUCED MOTION", "reduced_motion")
	setting_slider(rows, "CROSSHAIR SIZE", "crosshair_size", 2, 12, 1)
	var color_row := HBoxContainer.new()
	rows.add_child(color_row)
	var color_caption := label("CROSSHAIR COLOR", Design.TYPE_BODY)
	color_caption.custom_minimum_size.x = 250
	color_row.add_child(color_caption)
	var picker := ColorPickerButton.new()
	picker.color = Color(str(profile.data.settings.crosshair_color))
	picker.custom_minimum_size = Vector2(120, Design.TOUCH_MIN)
	picker.color_changed.connect(func(color: Color): profile.data.settings.crosshair_color = color.to_html(false); profile.save())
	color_row.add_child(picker)
	section(rows, "AUDIO & OPPONENTS")
	setting_slider(rows, "MASTER VOLUME", "volume", 0, 1, 0.05, true)
	setting_choice(rows, "BOT DIFFICULTY", ["RECRUIT", "STANDARD", "VETERAN"], int(profile.data.settings.difficulty), func(index: int): profile.data.settings.difficulty = index; profile.save())
	section(rows, "BINDINGS")
	rows.add_child(wrapped_label("WASD / left stick: move  ·  Mouse / right stick: aim  ·  LMB / R2: fire\nR: reload  ·  E: hold plant / defuse  ·  Space: jump  ·  Ctrl: crouch\nB: buy  ·  G: frag  ·  Q: smoke  ·  1 / 2: switch  ·  Tab: roster  ·  Esc: field menu", Design.TYPE_SMALL + 1, MUTED))
	rows.add_child(wrapped_label("TOUCH: left thumb moves; drag the open area or FIRE to aim. Hold FIRE to shoot; hold USE to plant or defuse. Field menu → EDIT TOUCH HUD moves buttons and the joystick; RESET POSITIONS restores the layout.", Design.TYPE_SMALL + 1, GOLD))

func refresh_settings() -> void:
	if screen == "game":
		build_hud()
		show_match_settings()
	else: show_settings()

func apply_display_mode() -> void:
	if OS.has_feature("mobile") or DisplayServer.get_name() == "headless": return
	var desired := clampi(int(profile.data.settings.window_mode), 0, 2)
	if desired == applied_window_mode: return
	var modes := [DisplayServer.WINDOW_MODE_WINDOWED, DisplayServer.WINDOW_MODE_FULLSCREEN, DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN]
	DisplayServer.window_set_mode(modes[desired])
	applied_window_mode = desired

func apply_settings() -> void:
	apply_display_mode()
	update_pointer_mode()
	Engine.max_fps = int(profile.data.settings.fps_limit)
	AudioServer.set_bus_volume_db(0, linear_to_db(maxf(0.001, float(profile.data.settings.volume))))
	if not is_inside_tree(): return
	SBGraphicsQuality.apply(self, get_viewport(), int(profile.data.settings.graphics_quality), float(profile.data.settings.render_scale))

func open_economy(tab: String) -> void:
	screen = "economy"
	# The account shell is fully opaque; retain cached resources without rendering the yard.
	if is_instance_valid(menu_world): menu_world.hide()
	clear_ui()
	if not is_instance_valid(economy_panel):
		economy_panel = load("res://scripts/ui/economy_ui.gd").new()
		economy_panel.configure(profile.data)
		economy_panel.theme = ui.theme
		canvas.add_child(economy_panel)
		economy_panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		economy_panel.closed.connect(show_menu)
		economy_panel.account_changed.connect(func():
			if screen == "menu": show_menu())
		if economy_panel.has_signal("loadout_changed"):
			economy_panel.loadout_changed.connect(func(slots: Dictionary):
				current_loadout = slots.duplicate(true)
				cosmetic_weapon = ""
			)
	else:
		economy_panel.configure(profile.data)
		economy_panel.theme = ui.theme
		economy_panel.show()
	economy_panel.open_tab(tab)

func start_match(options: Dictionary) -> void:
	if offline_diagnostics != null:
		options = offline_diagnostics.configure_match(options)
	if is_instance_valid(match_game):
		remove_child(match_game)
		match_game.queue_free()
	if is_instance_valid(menu_world):
		remove_child(menu_world)
		menu_world.queue_free()
		menu_world = null
		menu_camera = null
	clear_ui()
	match_suspended = false
	match_game = load("res://scripts/gameplay/match.gd").new()
	match_game.name = "Match"
	match_game.configure(options)
	add_child(match_game)
	if offline_diagnostics != null: offline_diagnostics.begin_match(match_game)
	match_game.match_finished.connect(on_match_finished)
	match_game.notification.connect(show_notification)
	match_game.exit_requested.connect(leave_match)
	match_game.elimination_reported.connect(add_kill_feed)
	screen = "game"
	paused = false
	input_look = Vector2.ZERO
	input_round = -1
	input_actor = -1
	cosmetic_weapon = ""
	apply_settings()
	mouse_delta = Vector2.ZERO
	physical_mouse_fire = false
	if not server_mode:
		build_hud()
		update_pointer_mode()

func _hud_block(alignment: int) -> VBoxContainer:
	var block := VBoxContainer.new()
	block.mouse_filter = Control.MOUSE_FILTER_IGNORE
	block.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	block.alignment = BoxContainer.ALIGNMENT_END
	block.add_theme_constant_override("separation", 3)
	block.set_meta("align", alignment)
	return block

func _pips(team: int) -> Control:
	# Five squad pips: filled for living operators, outlined when eliminated.
	var pips := Control.new()
	pips.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pips.custom_minimum_size = Vector2(78, 16)
	pips.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	pips.set_meta("alive", 5)
	pips.set_meta("team", team)
	pips.draw.connect(func():
		var alive := int(pips.get_meta("alive"))
		var side := int(pips.get_meta("team"))
		var tint := Design.squad_color(side)
		for i in range(5):
			# Attack fills from the score outward on the left, defense on the right.
			var slot := 4 - i if side == 0 else i
			var rect := Rect2(Vector2(slot * 15.5, 2), Vector2(11, 11))
			if i < alive:
				pips.draw_rect(rect, tint)
			else:
				pips.draw_rect(rect, Color(tint, 0.5), false, 1.2)
	)
	return pips

func build_hud() -> void:
	clear_ui()
	# Lightweight vertex-only fades preserve contrast without blocking a third of the view.
	var shade := Control.new()
	shade.name = "CombatShade"
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fill(shade)
	ui.add_child(shade)
	shade.draw.connect(func():
		var tint := Color(0.018, 0.024, 0.032, 0.72)
		var clear := Color(0.018, 0.024, 0.032, 0.0)
		shade.draw_polygon(PackedVector2Array([Vector2.ZERO, Vector2(shade.size.x, 0), Vector2(shade.size.x, 110), Vector2(0, 110)]), PackedColorArray([tint, tint, clear, clear]))
		shade.draw_polygon(PackedVector2Array([Vector2(0, shade.size.y), shade.size, shade.size - Vector2(0, 110), Vector2(0, shade.size.y - 110)]), PackedColorArray([tint, tint, clear, clear]))
	)
	shade.resized.connect(shade.queue_redraw)
	var margins := margin_frame(ui, 22)
	margins.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var rows := VBoxContainer.new()
	rows.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margins.add_child(rows)
	var top := HBoxContainer.new()
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	rows.add_child(top)
	var left := VBoxContainer.new()
	left.mouse_filter = Control.MOUSE_FILTER_IGNORE
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.custom_minimum_size.x = 240
	top.add_child(left)
	radar = Radar.new()
	radar.name = "Radar"
	radar.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	left.add_child(radar)
	radar.bind(match_game)
	var central := VBoxContainer.new()
	central.mouse_filter = Control.MOUSE_FILTER_IGNORE
	central.add_theme_constant_override("separation", 2)
	top.add_child(central)
	var score_row := HBoxContainer.new()
	score_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	score_row.alignment = BoxContainer.ALIGNMENT_CENTER
	score_row.add_theme_constant_override("separation", Design.SPACE_M)
	central.add_child(score_row)
	attack_pips = _pips(0)
	score_row.add_child(attack_pips)
	score_label = label("00  :  00", Design.TYPE_H1, Design.TEXT, true)
	score_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	score_row.add_child(score_label)
	defend_pips = _pips(1)
	score_row.add_child(defend_pips)
	phase_label = label("DEPLOYING", Design.TYPE_MICRO + 1, GOLD, true)
	phase_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	central.add_child(phase_label)
	squad_label = label("", Design.TYPE_MICRO, MUTED, true)
	squad_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	central.add_child(squad_label)
	var side := VBoxContainer.new()
	side.mouse_filter = Control.MOUSE_FILTER_IGNORE
	side.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	side.custom_minimum_size.x = 240
	top.add_child(side)
	hud_action_margin = MarginContainer.new()
	hud_action_margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	side.add_child(hud_action_margin)
	var side_stack := VBoxContainer.new()
	side_stack.mouse_filter = Control.MOUSE_FILTER_IGNORE
	side_stack.add_theme_constant_override("separation", Design.SPACE_S)
	hud_action_margin.add_child(side_stack)
	action_label = wrapped_label("", Design.TYPE_BODY, GOLD)
	action_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	side_stack.add_child(action_label)
	# A plain Control, unlike a container, ignores its children's minimum size, so
	# no display name can widen the HUD, move the score or push the ammunition
	# off-screen. add_kill_feed() fits each row to this frame's width.
	kill_feed_frame = Control.new()
	kill_feed_frame.name = "KillFeedFrame"
	kill_feed_frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	kill_feed_frame.clip_contents = true
	side_stack.add_child(kill_feed_frame)
	# Reserve KILL_FEED_ROWS rows of the default Latin face at the current text size.
	# Rows in other scripts can be taller; _fit_kill_feed_frame() grows the frame to them.
	var probe := label("Ag", Design.TYPE_SMALL)
	kill_feed_frame.add_child(probe)
	var row_height := ceilf(probe.get_combined_minimum_size().y + _kill_feed_style(false).get_minimum_size().y)
	probe.free()
	kill_feed_reserve = KILL_FEED_ROWS * row_height + (KILL_FEED_ROWS - 1) * KILL_FEED_GAP
	kill_feed_frame.custom_minimum_size.y = kill_feed_reserve
	kill_feed = VBoxContainer.new()
	kill_feed.name = "KillFeed"
	kill_feed.mouse_filter = Control.MOUSE_FILTER_IGNORE
	kill_feed.add_theme_constant_override("separation", KILL_FEED_GAP)
	kill_feed.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	kill_feed_frame.add_child(kill_feed)
	kill_feed_frame.resized.connect(_refit_kill_feed_rows)
	var space := Control.new()
	space.mouse_filter = Control.MOUSE_FILTER_IGNORE
	space.size_flags_vertical = Control.SIZE_EXPAND_FILL
	rows.add_child(space)
	# The status row is a plain Control that reserves one line, like the kill-feed frame,
	# so the label never sizes the layout. _fit_status_line() places the label in it, and
	# a wrapped label grows upward into the open space, so nothing below it moves and its
	# size never feeds back into the next frame's placement.
	status_row = Control.new()
	status_row.name = "StatusRow"
	status_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	rows.add_child(status_row)
	status_label = wrapped_label("BUY PHASE  /  " + ("Tap BUY to equip" if uses_touch_controls() else "Press B to equip"), Design.TYPE_BODY, GOLD)
	status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	status_label.max_lines_visible = STATUS_MAX_LINES
	# The line floats over the 3D view and the weapon: a dark halo keeps it readable on
	# the light sidearm, sky and concrete alike.
	Design.legible(status_label)
	status_row.add_child(status_label)
	var line_probe := label("Ag", Design.TYPE_BODY)
	status_row.add_child(line_probe)
	status_row.custom_minimum_size.y = ceilf(line_probe.get_combined_minimum_size().y)
	line_probe.free()
	objective_bar = ProgressBar.new()
	objective_bar.custom_minimum_size = Vector2(200, 8)
	objective_bar.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	objective_bar.show_percentage = false
	objective_bar.max_value = 1.0
	rows.add_child(objective_bar)
	var bottom := HBoxContainer.new()
	bottom.mouse_filter = Control.MOUSE_FILTER_IGNORE
	rows.add_child(bottom)
	var vitals := _hud_block(HORIZONTAL_ALIGNMENT_LEFT)
	bottom.add_child(vitals)
	# Funds sit just above the health readout but take no layout height, so the
	# bottom row, and the status line above it, keep their positions.
	var funds_anchor := Control.new()
	funds_anchor.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vitals.add_child(funds_anchor)
	funds_label = label("0  ·  FUNDS", Design.TYPE_SMALL, GOLD, true)
	funds_label.name = "Funds"
	funds_label.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.8))
	funds_label.add_theme_constant_override("shadow_offset_y", 1)
	funds_label.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	funds_label.grow_vertical = Control.GROW_DIRECTION_BEGIN
	funds_anchor.add_child(funds_label)
	health_label = wrapped_label("100  ·  HEALTH", 22)
	health_label.name = "Health"
	health_label.add_theme_font_override("font", Design.heading_font())
	health_label.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.8))
	health_label.add_theme_constant_override("shadow_offset_y", 2)
	vitals.add_child(health_label)
	health_bar = ProgressBar.new()
	health_bar.custom_minimum_size = Vector2(170, 6)
	health_bar.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	health_bar.show_percentage = false
	health_bar.max_value = 100
	health_bar.value = 100
	health_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vitals.add_child(health_bar)
	hud_controls = wrapped_label("B  BUY     E  OBJECTIVE     TAB  ROSTER     ESC  MENU", Design.TYPE_MICRO + 1, MUTED)
	hud_controls.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hud_controls.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	bottom.add_child(hud_controls)
	var loadout := _hud_block(HORIZONTAL_ALIGNMENT_RIGHT)
	bottom.add_child(loadout)
	ammo_label = wrapped_label("12 / 36", 22)
	ammo_label.name = "Ammo"
	ammo_label.add_theme_font_override("font", Design.heading_font())
	ammo_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	loadout.add_child(ammo_label)
	utility_label = wrapped_label("", Design.TYPE_MICRO + 1, MUTED)
	utility_label.name = "Utility"
	utility_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	loadout.add_child(utility_label)
	crosshair = Control.new()
	crosshair.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fill(crosshair)
	ui.add_child(crosshair)
	crosshair.draw.connect(draw_crosshair)
	crosshair.resized.connect(crosshair.queue_redraw)
	crosshair.queue_redraw()
	touch = Touch.new()
	touch.enabled = uses_touch_controls()
	touch.hud_scale = float(profile.data.settings.hud_scale)
	touch.restore_layout(profile.data.settings.hud_positions)
	touch.buy_pressed.connect(show_buy)
	touch.pause_pressed.connect(toggle_pause)
	touch.switch_pressed.connect(func(): switch_requested = true)
	touch.scoreboard_pressed.connect(func(): touch_score_until = elapsed + 4.0)
	touch.layout_changed.connect(func(layout: Dictionary): profile.data.settings.hud_positions = layout; profile.save())
	ui.add_child(touch)
	sync_hud_input_mode()

## Reticle gap follows the actual authoritative spread cone of the next shot.
func crosshair_gap(actor) -> float:
	if actor == null or actor.camera == null: return 4.0
	var spread: float = actor.current_spread(absf(actor.velocity.y) > 0.5)
	var half_height := get_viewport().get_visible_rect().size.y * 0.5
	var pixels := tan(spread) / tan(deg_to_rad(actor.camera.fov) * 0.5) * half_height
	return clampf(3.0 + pixels, 3.0, 36.0)

func draw_crosshair() -> void:
	if not is_instance_valid(crosshair): return
	var center: Vector2 = get_viewport().get_visible_rect().size / 2
	var width: float = profile.data.settings.crosshair_size
	var color := Color(str(profile.data.settings.crosshair_color))
	var actor = match_game.local_actor() if is_instance_valid(match_game) else null
	var gap := crosshair_gap(actor)
	for direction in [Vector2.LEFT, Vector2.RIGHT, Vector2.UP, Vector2.DOWN]:
		crosshair.draw_line(center + direction * gap, center + direction * (gap + width), Color(0, 0, 0, 0.7), 4)
		crosshair.draw_line(center + direction * gap, center + direction * (gap + width), color, 2)
	crosshair.draw_circle(center, 1.5, color)
	# Confirmation follows resolved authoritative damage, never a speculative client ray.
	if actor != null and actor.hit_feedback_remaining > 0:
		var hit_color := Design.CRIMSON_BRIGHT if actor.hit_feedback_lethal else GOLD if actor.hit_feedback_headshot else Color.WHITE
		hit_color.a = clampf(actor.hit_feedback_remaining / 0.08, 0.0, 1.0)
		for diagonal in [Vector2(-1, -1), Vector2(1, -1), Vector2(-1, 1), Vector2(1, 1)]:
			crosshair.draw_line(center + diagonal * 9, center + diagonal * 14, Color(0, 0, 0, hit_color.a * 0.6), 4)
			crosshair.draw_line(center + diagonal * 9, center + diagonal * 14, hit_color, 2)

func add_kill_feed(killer_id: int, victim_id: int, headshot: bool) -> void:
	if not is_instance_valid(kill_feed) or not is_instance_valid(match_game): return
	var killer: SBActor = match_game.actors.get(killer_id)
	var victim: SBActor = match_game.actors.get(victim_id)
	if victim == null: return
	var involved: bool = victim_id == match_game.local_id or killer_id == match_game.local_id
	var entry := PanelContainer.new()
	entry.mouse_filter = Control.MOUSE_FILTER_IGNORE
	entry.size_flags_horizontal = Control.SIZE_SHRINK_END
	var style := _kill_feed_style(involved)
	entry.add_theme_stylebox_override("panel", style)
	var row := HBoxContainer.new()
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_theme_constant_override("separation", KILL_FEED_SEPARATION)
	entry.add_child(row)
	# Display names are user supplied: plain one-line labels only, never rich text.
	var names: Array[Label] = []
	if killer != null and killer != victim:
		names.append(_kill_feed_name(killer))
		row.add_child(names[-1])
	var marker := label("HEADSHOT" if headshot else "›", Design.TYPE_MICRO, GOLD if headshot else MUTED, headshot)
	row.add_child(marker)
	names.append(_kill_feed_name(victim))
	row.add_child(names[-1])
	entry.set_meta("born", elapsed)
	entry.set_meta("headshot", headshot)
	kill_feed.add_child(entry)
	_fit_kill_feed_row(entry)
	while kill_feed.get_child_count() > KILL_FEED_ROWS:
		var oldest := kill_feed.get_child(0)
		kill_feed.remove_child(oldest)
		oldest.queue_free()
	_fit_kill_feed_frame()

## Mode changes resize the frame without replacing existing rows. Always fit
## from the stored names so widening can recover text that now fits again.
func _refit_kill_feed_rows() -> void:
	if not is_instance_valid(kill_feed): return
	for entry: PanelContainer in kill_feed.get_children():
		if not entry.is_queued_for_deletion(): _fit_kill_feed_row(entry)
	_fit_kill_feed_frame()

func _fit_kill_feed_row(entry: PanelContainer) -> void:
	var row: HBoxContainer = entry.get_child(0)
	var names: Array[Label] = []
	var marker: Label
	for child: Label in row.get_children():
		if child.has_meta("full_name"): names.append(child)
		else: marker = child
	var headshot := bool(entry.get_meta("headshot", false))
	marker.text = "HEADSHOT" if headshot else "›"
	var style := entry.get_theme_stylebox("panel")
	# Fit the row to the frame: names keep their natural width when they fit and
	# otherwise share the remaining space, ending in an ellipsis. When space is
	# tight the headshot marker shortens to "HS" before any name is cut.
	var frame_width := kill_feed_frame.size.x if kill_feed_frame.size.x > 1.0 else 220.0
	var widths: Array[float] = []
	for name_label in names:
		widths.append(_text_width(name_label, str(name_label.get_meta("full_name"))) + 1.0)
	var fixed := KILL_FEED_SEPARATION * names.size() + style.get_minimum_size().x + 2.0
	if headshot and widths.reduce(func(total, width): return total + width, 0.0) + _text_width(marker, marker.text) + fixed > frame_width:
		marker.text = "HS"
	var budget := maxf(0.0, frame_width - fixed - _text_width(marker, marker.text))
	if names.size() == 2 and widths[0] + widths[1] > budget:
		var share := budget * 0.5
		if widths[0] < share: widths[1] = budget - widths[0]
		elif widths[1] < share: widths[0] = budget - widths[1]
		else: widths = [share, share]
	elif names.size() == 1:
		widths[0] = minf(widths[0], budget)
	for index in range(names.size()):
		var fitted := _fit_text(names[index], str(names[index].get_meta("full_name")), maxf(24.0, floorf(widths[index])))
		names[index].text = fitted
		names[index].custom_minimum_size.x = ceilf(_text_width(names[index], fitted))

## A row is as tall as the tallest face its text is shaped with. A name in a script
## the default font lacks is drawn in a system fallback face whose line height is
## the OS's choice (Noto Sans CJK is 2 px taller than the Latin face at 14 px), so
## the frame takes its height from the rendered rows, never less than the Latin
## reserve. Only the height is set: the frame still ignores its rows' widths.
func _fit_kill_feed_frame() -> void:
	var rows := 0
	var height := 0.0
	for entry: Control in kill_feed.get_children():
		if entry.is_queued_for_deletion(): continue
		rows += 1
		height += entry.get_combined_minimum_size().y
	height += maxi(0, rows - 1) * KILL_FEED_GAP
	kill_feed_frame.custom_minimum_size.y = maxf(kill_feed_reserve, ceilf(height))

func _kill_feed_name(actor: SBActor) -> Label:
	var full_name := _limit_stacked_marks(Design.plain_line(actor.display_name, 24))
	var name_label := label(full_name, Design.TYPE_SMALL, Design.squad_color(actor.team))
	name_label.set_meta("full_name", full_name)
	return name_label

## Generic combining diacritics can be stacked into a column several rows tall
## ("zalgo" text), which would push other kill-feed rows out of the clipped frame.
## At most two follow any character. Script-specific marks (Indic, Thai, Arabic)
## lie outside these blocks and are untouched.
static func _limit_stacked_marks(text: String) -> String:
	var result := ""
	var run := 0
	for index in range(text.length()):
		var code := text.unicode_at(index)
		var stacking := (code >= 0x0300 and code <= 0x036F) or (code >= 0x1AB0 and code <= 0x1AFF) \
			or (code >= 0x1DC0 and code <= 0x1DFF) or (code >= 0x20D0 and code <= 0x20FF) or (code >= 0xFE20 and code <= 0xFE2F)
		run = run + 1 if stacking else 0
		if run <= 2:
			result += String.chr(code)
	return result

## Longest prefix of text that fits width with an explicit trailing ellipsis,
## measured in the label's own font. Godot's built-in overrun can drop the
## ellipsis when the cut text exactly fills the width, so it is not relied on.
## Cuts fall only on grapheme-cluster boundaries from the text server (ICU), so a
## letter never loses its marks and no conjunct, flag or keycap is split.
func _fit_text(node: Label, text: String, width: float) -> String:
	if _text_width(node, text) <= width:
		return text
	var room := width - _text_width(node, "…")
	var cut := 0
	for boundary: int in TextServerManager.get_primary_interface().string_get_character_breaks(text):
		if boundary >= text.length() or _text_width(node, text.left(boundary)) > room:
			break
		cut = boundary
	return text.left(cut).strip_edges(false, true) + "…"

func _kill_feed_style(involved: bool) -> StyleBoxFlat:
	return Design.box(Color(Design.OBSIDIAN, 0.62), GOLD if involved else Color.TRANSPARENT, 1, Vector2(8, 3))

func _text_width(node: Label, text: String) -> float:
	return node.get_theme_font("font").get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, node.get_theme_font_size("font_size")).x

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT or what == NOTIFICATION_WM_WINDOW_FOCUS_OUT:
		physical_mouse_fire = false
		mouse_delta = Vector2.ZERO
		application_focused = false
		waiting_for_input_release = true
		switch_requested = false
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		if is_instance_valid(touch): touch.reset_input()
		if screen == "game" and is_instance_valid(match_game):
			set_match_suspended(true)
			if not paused: toggle_pause()
	elif what == NOTIFICATION_APPLICATION_FOCUS_IN or what == NOTIFICATION_WM_WINDOW_FOCUS_IN:
		application_focused = true

func _input(event: InputEvent) -> void:
	if server_mode or not application_focused: return
	# Touch-to-mouse emulation is needed by menus, but must never fire the weapon.
	if event is InputEventMouse and event.device == InputEvent.DEVICE_ID_EMULATION:
		return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		physical_mouse_fire = event.pressed and screen == "game" and not paused
	if event is InputEventMouseMotion and screen == "game" and not paused and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		mouse_delta += event.screen_relative
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ESCAPE:
			if screen == "game":
				if touch != null and touch.editing:
					finish_touch_editor()
				else: toggle_pause()
			elif screen != "menu": show_menu()
		elif screen == "game" and not paused and event.keycode == KEY_B:
			show_buy()

func _physics_process(delta: float) -> void:
	if server_mode or screen != "game" or not is_instance_valid(match_game): return
	if offline_diagnostics != null: offline_diagnostics.observe(match_game, delta)
	var actor = match_game.local_actor()
	if actor != null and (input_round != match_game.round_number or input_actor != actor.actor_id):
		input_look = Vector2(actor.yaw, actor.pitch)
		input_round = match_game.round_number
		input_actor = actor.actor_id
	var state: Dictionary = {"move": Vector2.ZERO, "look": input_look, "fire": false}
	if actor != null: actor.reduced_motion = bool(profile.data.settings.reduced_motion)
	if actor != null and actor.weapon_id != cosmetic_weapon:
		actor.apply_cosmetic(current_loadout.get(actor.weapon_id, {}))
		cosmetic_weapon = actor.weapon_id
	if application_focused and not paused and actor != null:
		if waiting_for_input_release:
			if not controls_released():
				mouse_delta = Vector2.ZERO
				physical_mouse_fire = false
				switch_requested = false
				if is_instance_valid(touch): touch.reset_input()
				match_game.set_local_input(state)
				return
			waiting_for_input_release = false
		var sensitivity := float(profile.data.settings.sensitivity)
		input_look.x -= mouse_delta.x * sensitivity
		input_look.y -= mouse_delta.y * sensitivity
		mouse_delta = Vector2.ZERO
		var move := Vector2(float(Input.is_physical_key_pressed(KEY_D)) - float(Input.is_physical_key_pressed(KEY_A)), float(Input.is_physical_key_pressed(KEY_W)) - float(Input.is_physical_key_pressed(KEY_S)))
		if touch != null and touch.enabled:
			move += touch.movement
			var touch_look: Vector2 = touch.consume_look()
			input_look -= touch_look * float(profile.data.settings.touch_sensitivity)
		var pads := connected_controllers()
		var device := pads[0] if not pads.is_empty() else -1
		if device >= 0:
			var stick_move := Vector2(controller_axis(device, JOY_AXIS_LEFT_X), -controller_axis(device, JOY_AXIS_LEFT_Y))
			if stick_move.length() > 0.15: move += stick_move.limit_length()
			var stick := Vector2(controller_axis(device, JOY_AXIS_RIGHT_X), controller_axis(device, JOY_AXIS_RIGHT_Y))
			if stick.length() > 0.15: input_look -= stick * delta * 2.6
		if bool(profile.data.settings.gyro) and uses_touch_controls():
			var gyro := Input.get_gyroscope()
			input_look -= Vector2(gyro.y, gyro.x) * delta * float(profile.data.settings.gyro_sensitivity)
		input_look.y = clampf(input_look.y, -1.45, 1.45)
		state.move = move.limit_length(1.0)
		state.look = input_look
		state.fire = physical_mouse_fire or (device >= 0 and controller_axis(device, JOY_AXIS_TRIGGER_RIGHT) > 0.4) or touch_action("fire")
		state.reload = Input.is_physical_key_pressed(KEY_R) or (device >= 0 and controller_button(device, JOY_BUTTON_X)) or touch_action("reload")
		state.jump = Input.is_physical_key_pressed(KEY_SPACE) or (device >= 0 and controller_button(device, JOY_BUTTON_A)) or touch_action("jump")
		state.crouch = Input.is_physical_key_pressed(KEY_CTRL) or (device >= 0 and controller_button(device, JOY_BUTTON_B)) or touch_action("crouch")
		state.interact = Input.is_physical_key_pressed(KEY_E) or (device >= 0 and controller_button(device, JOY_BUTTON_Y)) or touch_action("interact")
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
	return touch != null and touch.enabled and bool(touch.actions.get(action, false))

## Guidance follows the same phase, side and carrier eligibility as objectives.
## The authority still decides whether a nearby held interaction can progress.
func objective_hint(actor: SBActor) -> String:
	if match_game.phase == "post": return "ROUND COMPLETE"
	if match_game.phase == "match_over": return "OPERATION COMPLETE"
	if not actor.alive: return "SPECTATING YOUR SQUAD"
	if match_game.phase != "live": return ""
	var use_key := "USE" if uses_touch_controls() else "E"
	if match_game.objective_state == "planted":
		return "HOLD %s NEAR THE DEVICE TO DEFUSE" % use_key if actor.team == 1 else "DEFEND THE DEVICE"
	if actor.team == 0:
		if match_game.objective_state == "dropped": return "RECOVER THE RELAY DEVICE"
		if match_game.objective_carrier != actor.actor_id: return "ESCORT THE DEVICE CARRIER"
		return "HOLD %s AT A SITE TO PLANT" % use_key
	return "DEFEND THE TWO OBJECTIVE SITES"

func _process(delta: float) -> void:
	elapsed += delta
	if server_mode: return
	# The menu measures the room it has when it is built. When that room changes (a window
	# resize, a rotation, the device's safe area) it is built again, so a layout chosen for
	# a wide screen is never kept on a narrow one.
	if screen == "menu" and menu_layout.has("region") and menu_region() != menu_layout.region:
		show_menu()
	if is_instance_valid(menu_camera) and menu_camera.is_inside_tree() and menu_camera.is_visible_in_tree():
		menu_camera.position = Vector3(27 + sin(elapsed * 0.07) * 4, 18, 30)
		menu_camera.look_at(Vector3.ZERO)
	if smoke_mode:
		smoke_frames += 1
		if smoke_frames == 1: print("SIGHTBREAK_STARTUP phase=first_process msec=", Time.get_ticks_msec())
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
	if screen != "game" or not is_instance_valid(match_game) or not is_instance_valid(score_label): return
	sync_hud_input_mode()
	var actor = match_game.local_actor()
	score_label.text = "%02d  :  %02d" % [match_game.attack_score, match_game.defend_score]
	var seconds := int(ceil(match_game.time_left))
	phase_label.text = "ROUND %02d   ·   %s   ·   %02d:%02d" % [match_game.round_number, str(match_game.phase).to_upper(), seconds / 60, seconds % 60]
	var urgent: bool = match_game.phase == "live" and match_game.time_left <= 10.0 and match_game.objective_state != "planted"
	phase_label.add_theme_color_override("font_color", Design.CRIMSON_BRIGHT if urgent else GOLD)
	var alive := [0, 0]
	for operator: SBActor in match_game.actors.values():
		if operator.alive: alive[clampi(operator.team, 0, 1)] += 1
	for pair in [[attack_pips, alive[0]], [defend_pips, alive[1]]]:
		if is_instance_valid(pair[0]) and int(pair[0].get_meta("alive")) != pair[1]:
			pair[0].set_meta("alive", pair[1])
			pair[0].queue_redraw()
	action_label.text = "DEVICE  %02d s" % int(match_game.objective_timer) if match_game.objective_state == "planted" else "DEVICE  /  " + str(match_game.objective_state).to_upper()
	if match_game.objective_state == "dropped": action_label.text = "DEVICE DROPPED  /  RECOVER"
	# Connection callbacks retain their typed reason separately from combat notices.
	var connection_blocked: bool = match_game.connection_state not in ["offline", "hosting", "connected"]
	var critical_notice: String = match_game.connection_notice if connection_blocked else ""
	if not critical_notice.is_empty():
		status_label.text = critical_notice
	elif match_game.phase == "waiting":
		var humans := 0
		for row in match_game.scoreboard():
			if not row.get("bot", true): humans += 1
		status_label.text = "WAITING FOR AUTHENTICATED PLAYERS   %d / 10" % humans
	if is_instance_valid(reward_label):
		reward_label.text = "ACCOUNT REWARDS  /  " + str(match_game.reward_status).to_upper().replace("_", " ")
	objective_bar.value = float(match_game.interaction_progress)
	objective_bar.visible = objective_bar.value > 0
	var expired := false
	for entry in kill_feed.get_children():
		var age := elapsed - float(entry.get_meta("born", elapsed))
		entry.modulate.a = clampf((KILL_FEED_SECONDS - age) / 0.6, 0.0, 1.0)
		if age > KILL_FEED_SECONDS and not entry.is_queued_for_deletion():
			entry.queue_free()
			expired = true
	if expired: _fit_kill_feed_frame()
	if is_instance_valid(radar): radar.queue_redraw()
	if actor != null:
		squad_label.text = "YOU  ·  " + Design.squad_name(actor.team)
		squad_label.add_theme_color_override("font_color", Design.squad_color(actor.team))
		health_label.text = "%03d  ·  HEALTH" % maxi(0, int(actor.health)) if actor.alive else "ELIMINATED  ·  SPECTATING"
		var critical: bool = actor.alive and actor.health <= 25
		var health_color: Color = CRIMSON.lightened(0.3) if critical else Design.TEXT
		if health_label.get_theme_color("font_color") != health_color: health_label.add_theme_color_override("font_color", health_color)
		health_bar.value = maxf(0, actor.health) if actor.alive else 0.0
		health_bar.add_theme_stylebox_override("fill", Design.box(CRIMSON.lightened(0.3) if critical else Design.STEEL_BRIGHT, Color.TRANSPARENT, 0, Vector2.ZERO))
		ammo_label.text = "%s   %02d / %02d" % [str(actor.weapon_id).to_upper(), actor.ammo, actor.reserve]
		if actor.reload_remaining > 0: ammo_label.text = "RELOADING   %0.1fs" % actor.reload_remaining
		var ammo_color: Color = GOLD if actor.reload_remaining > 0 else CRIMSON.lightened(0.3) if actor.ammo == 0 else Design.TEXT
		if ammo_label.get_theme_color("font_color") != ammo_color: ammo_label.add_theme_color_override("font_color", ammo_color)
		funds_label.text = "%d  ·  FUNDS" % actor.credits
		utility_label.text = "FRAG ×%d    SMOKE ×%d" % [actor.grenades, actor.smokes]
		if touch != null: touch.counts = {"grenade": actor.grenades, "smoke": actor.smokes}
		if connection_blocked:
			pass # Never replace a current connection/recovery reason with a tactical hint.
		elif match_game.phase == "buy": status_label.text = "BUY PHASE   /   %s TO EQUIP" % ("TAP BUY" if uses_touch_controls() else "PRESS B")
		elif match_game.phase == "live" and match_game.objective_state == "planted":
			# The armed device creates an urgent role. Combat already has its own feed;
			# successive notices cannot postpone this guidance until after the player dies.
			status_label.text = objective_hint(actor)
		elif match_game.phase != "waiting" and elapsed > float(status_label.get_meta("until", 0.0)):
			status_label.text = objective_hint(actor)
		_fit_status_line()
		crosshair.visible = actor.alive and not paused
		crosshair.queue_redraw()
	if (Input.is_physical_key_pressed(KEY_TAB) or elapsed < touch_score_until) and not paused:
		if not is_instance_valid(score_panel): show_scoreboard()
	elif is_instance_valid(score_panel):
		score_panel.queue_free()
		score_panel = null

## Places the status line where it covers no drawn touch control and not the funds
## label, as near the screen centre as it can go, wrapping to at most STATUS_MAX_LINES
## lines. A clear stretch must hold the text at that line count, so a narrow gap between
## buttons is never chosen. If no stretch of the row is clear the line rises just above
## the controls in its way, its top no higher than STATUS_RISE_LIMIT; if nothing there is
## clear either, it takes the whole row (covering a control is then unavoidable). Every input is geometry the label does not affect, and
## the result is recomputed only when an input changes, so it cannot oscillate.
func _fit_status_line() -> void:
	if not is_instance_valid(status_row) or not is_instance_valid(status_label):
		return
	var row := status_row.get_global_rect()
	var blocks: Array[Rect2] = []
	if is_instance_valid(funds_label) and funds_label.is_visible_in_tree():
		blocks.append(funds_label.get_global_rect().grow(STATUS_TOUCH_GAP))
	var touch_on: bool = touch != null and touch.enabled
	if touch_on:
		for action in touch.positions:
			var radius: float = touch.radius(action)
			var point: Vector2 = touch.global_position + touch.control_point(action)
			blocks.append(Rect2(point - Vector2.ONE * radius, Vector2.ONE * radius * 2).grow(STATUS_TOUCH_GAP))
	var key := [status_label.text, row, status_label.get_theme_font_size("font_size"), blocks]
	if key == status_fit_key:
		return
	status_fit_key = key
	# Narrowest width, and the height, at which the text takes each line count.
	var widths: Array[float] = []
	var heights: Array[float] = []
	for lines in range(1, STATUS_MAX_LINES + 1):
		var width := _status_width(lines, row.size.x)
		widths.append(width)
		heights.append(_status_height(width) if width > 0 else 0.0)
	var centre := row.get_center().x
	var ceiling := ui.size.y * STATUS_RISE_LIMIT
	# Row-local bottom edges to try, lowest first: the row's own bottom, then the top edge
	# of each block above it, the lowest positions at which the line clears that block.
	var bottoms: Array[float] = [row.size.y]
	for block in blocks:
		var edge := block.position.y - row.position.y
		if edge < row.size.y and not bottoms.has(edge): bottoms.append(edge)
	bottoms.sort()
	bottoms.reverse()
	var fit := "overlap"
	for bottom in bottoms:
		var best := Rect2()
		var best_cost := INF
		for index in STATUS_MAX_LINES:
			var width: float = widths[index]
			var top := row.position.y + bottom - heights[index]
			if width <= 0 or (bottom < row.size.y and top < ceiling):
				continue
			for span in _status_spans(row, top, row.position.y + bottom, blocks):
				if span.y - span.x < width:
					continue
				var left := clampf(centre - width * 0.5, span.x, span.y - width)
				var cost := absf(left + width * 0.5 - centre) + index * STATUS_LINE_COST * row.size.x
				if cost < best_cost:
					best_cost = cost
					best = Rect2(left - row.position.x, bottom - heights[index], width, heights[index])
		if best_cost < INF:
			_place_status(best)
			fit = "row" if bottom == row.size.y else "risen"
			break
	if fit == "overlap":
		# Nothing is clear: take the whole row and accept covering a control.
		var height := _status_height(row.size.x)
		_place_status(Rect2(0, row.size.y - height, row.size.x, height))
	status_label.set_meta("fit", fit)

## Narrowest width (whole pixels, at most the row's width) at which the status text wraps
## to no more than the given number of lines, or 0 if even the row's width needs more.
func _status_width(lines: int, limit: float) -> float:
	if _status_lines(limit) > lines:
		return 0.0
	var low := 1.0
	var high := ceilf(limit)
	while high - low > 1.0:
		var middle := floorf((low + high) * 0.5)
		if _status_lines(middle) <= lines: high = middle
		else: low = middle
	return high

func _status_lines(width: float) -> int:
	status_label.size = Vector2(width, status_label.size.y)
	return status_label.get_line_count()

func _status_height(width: float) -> float:
	status_label.size = Vector2(width, status_label.size.y)
	return ceilf(status_label.get_minimum_size().y)

## Stretches of the status row's width that no block overlaps between top and bottom.
func _status_spans(row: Rect2, top: float, bottom: float, blocks: Array[Rect2]) -> Array[Vector2]:
	var free: Array[Vector2] = [Vector2(row.position.x, row.end.x)]
	for block in blocks:
		if block.end.y <= top or block.position.y >= bottom:
			continue
		var kept: Array[Vector2] = []
		for part in free:
			if block.end.x <= part.x or block.position.x >= part.y:
				kept.append(part)
				continue
			if block.position.x > part.x: kept.append(Vector2(part.x, block.position.x))
			if block.end.x < part.y: kept.append(Vector2(block.end.x, part.y))
		free = kept
	return free

## A Control keeps its cached minimum size until the next frame, and an autowrapped
## label's minimum height depends on its width, so the cache is refreshed for the new
## width before the height is set. Otherwise the stale height of the last width measured
## would win and the label would change size a frame later.
func _place_status(rect: Rect2) -> void:
	status_label.size = Vector2(rect.size.x, status_label.size.y)
	status_label.update_minimum_size()
	status_label.position = rect.position
	status_label.size = rect.size

func show_notification(message: String) -> void:
	print("MATCH: ", message)
	if is_instance_valid(status_label):
		status_label.text = message
		status_label.set_meta("until", elapsed + 5.0)

func make_overlay(title: String) -> VBoxContainer:
	if is_instance_valid(overlay): overlay.queue_free()
	overlay = ColorRect.new()
	overlay.color = Design.SCRIM
	fill(overlay)
	ui.add_child(overlay)
	var margins := margin_frame(overlay, 56)
	var rows := scroll_rows(margins)
	rows.add_theme_constant_override("separation", Design.SPACE_L)
	var heading := wrapped_label(title, 34, GOLD)
	heading.add_theme_font_override("font", Design.heading_font())
	rows.add_child(heading)
	paused = true
	physical_mouse_fire = false
	if touch != null: touch.reset_input(); touch.enabled = false
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	return rows

## Offline training has no other players: menus genuinely pause it. Network
## matches keep running because the server does not wait for one client.
func set_match_suspended(suspended: bool) -> void:
	if not is_instance_valid(match_game) or str(match_game.options.get("mode", "offline")) != "offline":
		match_suspended = false
		return
	match_suspended = suspended
	match_game.process_mode = Node.PROCESS_MODE_DISABLED if suspended else Node.PROCESS_MODE_INHERIT

func close_overlay() -> void:
	if is_instance_valid(overlay): overlay.queue_free()
	overlay = null
	paused = false
	physical_mouse_fire = false
	mouse_delta = Vector2.ZERO
	set_match_suspended(false)
	update_pointer_mode()

func toggle_pause() -> void:
	if paused:
		close_overlay()
		return
	var rows := make_overlay("FIELD MENU")
	set_match_suspended(true)
	rows.add_child(label("Training is paused." if match_suspended else "The match continues while this menu is open.", Design.TYPE_BODY, MUTED))
	var resume := button("RESUME", close_overlay, Design.TOUCH_MIN, "primary")
	rows.add_child(resume)
	rows.add_child(button("SETTINGS", show_match_settings))
	rows.add_child(button("EDIT TOUCH HUD", open_touch_editor))
	rows.add_child(button("LEAVE MATCH", leave_match, Design.TOUCH_MIN, "ghost"))
	resume.grab_focus()

func show_match_settings() -> void:
	var rows := make_overlay("FIELD SETTINGS")
	set_match_suspended(true)
	populate_settings(rows)
	rows.add_child(button("BACK TO FIELD MENU", func(): close_overlay(); toggle_pause(), Design.TOUCH_MIN, "ghost"))

func open_touch_editor() -> void:
	close_overlay()
	set_match_suspended(true)
	touch.enabled = true
	touch.editing = true
	paused = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	var toolbar := HBoxContainer.new()
	toolbar.alignment = BoxContainer.ALIGNMENT_CENTER
	toolbar.add_theme_constant_override("separation", 16)
	toolbar.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	var safe := SafeArea.viewport_rect(ui.size)
	toolbar.offset_left = safe.position.x + 24
	toolbar.offset_right = -(ui.size.x - safe.end.x) - 24
	toolbar.offset_top = safe.position.y + 120
	toolbar.add_child(button("SAVE TOUCH LAYOUT", finish_touch_editor, 60, "primary"))
	toolbar.add_child(button("RESET POSITIONS", func(): touch.reset_layout(), 60))
	ui.add_child(toolbar)

func finish_touch_editor() -> void:
	touch.editing = false
	profile.data.settings.hud_positions = touch.exported_layout()
	profile.save()
	build_hud()
	paused = false
	physical_mouse_fire = false
	mouse_delta = Vector2.ZERO
	set_match_suspended(false)
	update_pointer_mode()

## Buy state for one weapon: owned, affordable, or the shortfall.
## Real availability of a weapon for the local player: what the card's chip says, and
## the full sentence for its tooltip. Match funds only; Credits never appear here.
func requisition_state(actor, key: String) -> Dictionary:
	var spec: Dictionary = Weapons.get_weapon(key)
	var funds := int(actor.credits) if actor != null else 0
	var cost := int(spec.get("cost", 0))
	var buy_phase: bool = is_instance_valid(match_game) and match_game.phase == "buy"
	if actor != null and actor.inventory.has(key):
		var held := "EQUIPPED" if actor.weapon_id == key else "OWNED"
		return {"available": false, "cost": cost, "chip": held, "tone": "held", "note": held}
	if not buy_phase:
		return {"available": false, "cost": cost, "chip": "PREPARATION ONLY", "tone": "locked", "note": "%d  ·  PREPARATION ONLY" % cost}
	if funds < cost:
		return {"available": false, "cost": cost, "chip": "NEED %d MORE" % (cost - funds), "tone": "short", "note": "%d  ·  NEED %d MORE" % [cost, cost - funds]}
	return {"available": true, "cost": cost, "chip": "BUY", "tone": "buy", "note": "%d" % cost}

func show_buy() -> void:
	if not is_instance_valid(match_game): return
	var rows := make_overlay("REQUISITION")
	var actor = match_game.local_actor()
	var funds := int(actor.credits) if actor != null else 0
	var funds_row := HBoxContainer.new()
	funds_row.add_theme_constant_override("separation", Design.SPACE_M)
	funds_row.alignment = BoxContainer.ALIGNMENT_BEGIN
	rows.add_child(funds_row)
	var funds_kicker := label("MATCH FUNDS", Design.TYPE_SMALL, MUTED, true)
	funds_kicker.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	funds_row.add_child(funds_kicker)
	var funds_value := label(str(funds), Design.TYPE_H2, GOLD, true)
	funds_value.name = "Funds"
	funds_row.add_child(funds_value)
	if match_game.phase != "buy":
		rows.add_child(wrapped_label("Equipment can be requisitioned during the 15-second preparation phase.", Design.TYPE_SMALL, Design.CRIMSON_BRIGHT))
	else:
		rows.add_child(wrapped_label("Purchases last for this match only and are validated by the match authority.", Design.TYPE_SMALL, MUTED))
	var cards := HFlowContainer.new()
	cards.add_theme_constant_override("h_separation", Design.SPACE_M)
	cards.add_theme_constant_override("v_separation", Design.SPACE_M)
	rows.add_child(cards)
	# Stat meters are relative to the best weapon in each stat, from the same table the
	# match uses.
	var peak := {"damage": 0.0, "rate": 0.0, "magazine": 0.0}
	for key in Weapons.DATA:
		var data: Dictionary = Weapons.DATA[key]
		peak.damage = maxf(peak.damage, float(data.damage))
		peak.rate = maxf(peak.rate, 1.0 / float(data.interval))
		peak.magazine = maxf(peak.magazine, float(data.magazine))
	for key in Weapons.DATA:
		var weapon_key: String = key
		cards.add_child(requisition_card(weapon_key, requisition_state(actor, weapon_key), peak))
	rows.add_child(button("BACK TO FIELD", close_overlay, Design.TOUCH_MIN, "ghost"))

## One requisition card: a button (so availability is its disabled state) holding the
## weapon's glyph, name, role, three stat meters, its price and a state chip.
func requisition_card(key: String, state: Dictionary, peak: Dictionary) -> Button:
	var spec: Dictionary = Weapons.get_weapon(key)
	var card := Button.new()
	card.name = "Buy_" + key
	card.focus_mode = Control.FOCUS_ALL
	card.disabled = not state.available
	card.tooltip_text = "%s   ·   %s\n%d DMG   ·   %.1f RPS   ·   %d RND\n%s" % [str(spec.name).to_upper(), WEAPON_ROLES.get(key, ""), int(spec.damage), 1.0 / float(spec.interval), int(spec.magazine), state.note]
	Design.apply_button(card)
	var held: bool = state.tone == "held"
	if held:
		var held_style := Design.box(Design.GRAPHITE_RAISED, Design.GOLD_DIM)
		card.add_theme_stylebox_override("disabled", held_style)
	card.pressed.connect(func():
		match_game.request_buy(key)
		close_overlay()
	)
	var frame := MarginContainer.new()
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side in ["left", "right", "top", "bottom"]:
		frame.add_theme_constant_override("margin_" + side, Design.SPACE_M)
	card.add_child(frame)
	var column := VBoxContainer.new()
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_theme_constant_override("separation", Design.SPACE_XS)
	frame.add_child(column)
	var dim: bool = not state.available and not held
	var ink: Color = Design.TEXT if not dim else Design.STEEL
	var name_label := label(str(spec.name).to_upper(), Design.TYPE_H3, ink, true)
	column.add_child(name_label)
	column.add_child(label(WEAPON_ROLES.get(key, ""), Design.TYPE_MICRO, MUTED, true))
	var glyph := WeaponGlyph.new()
	glyph.weapon_id = key
	glyph.tint = Color(Design.GOLD if held else Design.STEEL_BRIGHT, 0.4 if dim else 0.9)
	glyph.custom_minimum_size = Vector2(0, 40)
	column.add_child(glyph)
	for stat in [["DMG", float(spec.damage) / peak.damage, "%d" % int(spec.damage)], ["RATE", (1.0 / float(spec.interval)) / peak.rate, "%.1f/s" % (1.0 / float(spec.interval))], ["MAG", float(spec.magazine) / peak.magazine, "%d" % int(spec.magazine)]]:
		column.add_child(_stat_meter(stat[0], stat[1], stat[2], dim))
	var footer := HBoxContainer.new()
	footer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(footer)
	var price := label("FREE" if int(state.cost) == 0 else str(state.cost), Design.TYPE_H3, Design.GOLD if state.available else MUTED, true)
	footer.add_child(price)
	var spring := Control.new()
	spring.mouse_filter = Control.MOUSE_FILTER_IGNORE
	spring.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	footer.add_child(spring)
	var chip := PanelContainer.new()
	chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var chip_fill: Color = {"buy": Design.CRIMSON, "held": Color(Design.GOLD, 0.16), "short": Color(Design.CRIMSON, 0.12), "locked": Color(Design.STEEL, 0.1)}[state.tone]
	chip.add_theme_stylebox_override("panel", Design.box(chip_fill, Color.TRANSPARENT, 1, Vector2(8, 3)))
	footer.add_child(chip)
	var chip_label := label(state.chip, Design.TYPE_MICRO + 1, {"buy": Color.WHITE, "held": Design.GOLD, "short": Design.CRIMSON_BRIGHT, "locked": MUTED}[state.tone], true)
	chip_label.name = "State"
	chip.add_child(chip_label)
	# A button ignores its children's size, so the card takes its content's once the
	# theme's fonts apply (in the tree).
	card.ready.connect(func():
		var content := frame.get_combined_minimum_size()
		card.custom_minimum_size = Vector2(maxf(272, content.x), content.y)
	)
	return card

func _stat_meter(caption: String, fraction: float, value: String, dim: bool) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_theme_constant_override("separation", Design.SPACE_S)
	var name_label := label(caption, Design.TYPE_MICRO, MUTED, true)
	name_label.custom_minimum_size.x = 40 * text_scale()
	row.add_child(name_label)
	var bar := ProgressBar.new()
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bar.show_percentage = false
	bar.max_value = 1.0
	bar.value = clampf(fraction, 0.0, 1.0)
	bar.custom_minimum_size = Vector2(0, 5)
	bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	bar.add_theme_stylebox_override("background", Design.box(Design.OBSIDIAN, Color.TRANSPARENT, 0, Vector2.ZERO))
	bar.add_theme_stylebox_override("fill", Design.box(Color(Design.STEEL_BRIGHT, 0.45 if dim else 0.85), Color.TRANSPARENT, 0, Vector2.ZERO))
	row.add_child(bar)
	var value_label := label(value, Design.TYPE_MICRO, Design.STEEL_BRIGHT if not dim else MUTED)
	value_label.custom_minimum_size.x = 44 * text_scale()
	value_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	row.add_child(value_label)
	return row

func show_scoreboard() -> void:
	score_panel = PanelContainer.new()
	score_panel.name = "Scoreboard"
	score_panel.add_theme_stylebox_override("panel", Design.panel("overlay"))
	ui.add_child(score_panel)
	fill(score_panel)
	var safe := SafeArea.viewport_rect(ui.size)
	score_panel.offset_left = safe.position.x + safe.size.x * 0.15
	score_panel.offset_right = -(ui.size.x - safe.end.x) - safe.size.x * 0.15
	score_panel.offset_top = safe.position.y + safe.size.y * 0.12
	score_panel.offset_bottom = -(ui.size.y - safe.end.y) - safe.size.y * 0.12
	var rows := scroll_rows(score_panel)
	rows.add_theme_constant_override("separation", 3)
	var roster: Array = match_game.scoreboard()
	for team in [0, 1]:
		var header := HBoxContainer.new()
		rows.add_child(header)
		var title := label("%s   %02d" % [Design.squad_name(team), match_game.attack_score if team == 0 else match_game.defend_score], Design.TYPE_H3, Design.squad_color(team), true)
		title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		header.add_child(title)
		header.add_child(label("K  ·  A  ·  D  ·  OBJ", Design.TYPE_MICRO, MUTED, true))
		for entry in roster:
			if int(entry.get("team", 0)) != team: continue
			var row := HBoxContainer.new()
			rows.add_child(row)
			var tint: Color = GOLD if entry.get("local", false) else Design.TEXT
			if not entry.get("alive", true): tint = Color(tint, 0.45)
			var player := label(str(entry.get("name", "Operator")) + ("   BOT" if entry.get("bot", false) else ""), Design.TYPE_BODY + 1, tint)
			player.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			player.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
			row.add_child(player)
			row.add_child(label("%d  ·  %d  ·  %d  ·  %d" % [int(entry.get("kills", 0)), int(entry.get("assists", 0)), int(entry.get("deaths", 0)), int(entry.get("objectives", 0))], Design.TYPE_BODY + 1, tint))

func on_match_finished(summary: Dictionary) -> void:
	if server_mode: return
	var reward: Dictionary = {}
	if match_game.options.get("mode", "offline") == "offline": reward = profile.record_match(summary)
	if offline_diagnostics != null: offline_diagnostics.completed(match_game, summary, profile.data)
	var rows := make_overlay("OPERATION COMPLETE")
	var outcome := "DRAW" if summary.get("draw", false) else "VICTORY" if summary.get("won", false) else "DEFEAT"
	var outcome_label := label(outcome, Design.TYPE_DISPLAY - 12, GOLD if outcome == "VICTORY" else Design.CRIMSON_BRIGHT if outcome == "DEFEAT" else MUTED, true)
	rows.add_child(outcome_label)
	rows.add_child(label("FINAL   %02d  :  %02d   ·   %d ROUNDS" % [match_game.attack_score, match_game.defend_score, int(summary.get("rounds", 0))], Design.TYPE_H2))
	rows.add_child(wrapped_label("%d ELIMINATIONS   ·   %d ASSISTS   ·   %d DEATHS   ·   %d OBJECTIVES" % [int(summary.get("kills", 0)), int(summary.get("assists", 0)), int(summary.get("deaths", 0)), int(summary.get("objectives", 0))], Design.TYPE_BODY + 1, MUTED))
	if not reward.is_empty():
		rows.add_child(wrapped_label("OFFLINE TRAINING  +%d XP    +%d CREDITS    LEVEL %d" % [reward.xp, reward.credits, reward.level], Design.TYPE_H3, GOLD))
		if reward.save_error != OK: rows.add_child(label("Local progress could not be saved. Check device storage.", Design.TYPE_BODY, Design.CRIMSON_BRIGHT))
	elif str(match_game.reward_status) != "unranked":
		reward_label = label("ACCOUNT REWARDS  /  " + str(match_game.reward_status).to_upper(), Design.TYPE_BODY, MUTED)
		rows.add_child(reward_label)
	else: rows.add_child(wrapped_label("Unranked LAN result. No online wallet or inventory rewards.", Design.TYPE_BODY, MUTED))
	rows.add_child(button("RETURN TO OPERATIONS", leave_match, Design.TOUCH_MIN, "primary"))

func leave_match() -> void:
	physical_mouse_fire = false
	if offline_diagnostics != null: offline_diagnostics.finish()
	if server_mode:
		get_tree().quit(1)
		return
	if is_instance_valid(match_game):
		remove_child(match_game)
		match_game.queue_free()
		match_game = null
	match_suspended = false
	multiplayer.multiplayer_peer = null
	show_menu()
