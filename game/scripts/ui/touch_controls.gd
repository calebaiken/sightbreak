class_name TacticalTouch
extends Control
const SafeArea = preload("res://scripts/ui/safe_area.gd")

signal layout_changed(layout: Dictionary)
signal buy_pressed
signal pause_pressed
signal switch_pressed
signal scoreboard_pressed

var enabled := false:
	set(value):
		if enabled != value: reset_input()
		enabled = value
		queue_redraw()
var editing := false:
	set(value):
		if editing != value: reset_input()
		editing = value
		queue_redraw()
var hud_scale := 1.0:
	set(value):
		hud_scale = clampf(value, 0.7, 1.5) if is_finite(value) else 1.0
		queue_redraw()
const MOVE_DEADZONE := 0.12
var movement := Vector2.ZERO
var look_delta := Vector2.ZERO
var actions: Dictionary = {}
## Remaining utility per action (e.g. {"grenade": 1}); empty buttons dim and show 0.
var counts: Dictionary = {}:
	set(value):
		if counts != value:
			counts = value.duplicate()
			queue_redraw()
# Roster and buy sit below the top-left radar; saved custom layouts are unchanged.
const DEFAULT_POSITIONS := {"fire": Vector2(0.89, 0.53), "jump": Vector2(0.91, 0.70),
	"crouch": Vector2(0.79, 0.83), "reload": Vector2(0.76, 0.62),
	"interact": Vector2(0.65, 0.68), "grenade": Vector2(0.60, 0.80),
	"smoke": Vector2(0.69, 0.80), "buy": Vector2(0.17, 0.36), "pause": Vector2(0.96, 0.07), "switch": Vector2(0.91, 0.84), "score": Vector2(0.06, 0.36), "move": Vector2(0.13, 0.74)}
var positions: Dictionary = DEFAULT_POSITIONS.duplicate()
## 0.3 defaults that the radar now covers. Saving a layout stores every button, so a
## saved position equal to one of these was never moved by the player; it follows
## the new default. Any position the player chose is kept.
const RETIRED_DEFAULTS := {"buy": Vector2(0.19, 0.14), "score": Vector2(0.08, 0.14)}
const LABELS := {"fire": "FIRE", "jump": "JUMP", "crouch": "LOW", "reload": "RELOAD",
	"interact": "USE", "grenade": "FRAG", "smoke": "SMOKE", "buy": "BUY", "pause": "MENU", "switch": "SWAP", "score": "TEAM"}
var fingers: Dictionary = {}
var move_origin := Vector2.ZERO
var move_position := Vector2.ZERO
var safe_rect := Rect2()

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	resized.connect(refresh_safe_area)
	visibility_changed.connect(func():
		if not is_visible_in_tree(): reset_input()
	)
	refresh_safe_area.call_deferred()

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT or what == NOTIFICATION_WM_WINDOW_FOCUS_OUT:
		reset_input()

func refresh_safe_area() -> void:
	reset_input()
	safe_rect = SafeArea.viewport_rect(size)
	queue_redraw()

func restore_layout(saved: Dictionary) -> void:
	for key in saved:
		if positions.has(key) and saved[key] is Array and saved[key].size() == 2:
			var x: Variant = saved[key][0]
			var y: Variant = saved[key][1]
			if not (x is float or x is int) or not (y is float or y is int): continue
			if not is_finite(float(x)) or not is_finite(float(y)): continue
			var restored := Vector2(clampf(float(x), 0.0, 1.0), clampf(float(y), 0.0, 1.0))
			if RETIRED_DEFAULTS.has(key) and restored.distance_to(RETIRED_DEFAULTS[key]) < 0.002:
				restored = DEFAULT_POSITIONS[key]
			positions[key] = restored
	queue_redraw()

func reset_layout() -> void:
	reset_input()
	positions = DEFAULT_POSITIONS.duplicate()
	queue_redraw()

func exported_layout() -> Dictionary:
	var out: Dictionary = {}
	for key in positions:
		out[key] = [positions[key].x, positions[key].y]
	return out

func reset_input() -> void:
	fingers.clear()
	actions.clear()
	movement = Vector2.ZERO
	look_delta = Vector2.ZERO
	queue_redraw()

func layout_rect() -> Rect2:
	return safe_rect if safe_rect.size.x > 0 and safe_rect.size.y > 0 else Rect2(Vector2.ZERO, size)

func effective_scale() -> float:
	var rect := layout_rect()
	return minf(hud_scale, clampf(minf(rect.size.x / 640.0, rect.size.y / 480.0), 0.7, 1.5))

func radius(action: String) -> float:
	return (65.0 if action == "move" else (40.0 if action == "fire" else 28.0)) * effective_scale()

func hit_radius(action: String) -> float:
	var scaled := radius(action) * 1.25
	return scaled if action in ["fire", "move"] else maxf(31.0, scaled)

func resolved_position(action: String) -> Vector2:
	var normalized: Vector2 = positions[action]
	var rect := layout_rect()
	if (rect.size.x < 1100 or rect.size.y < 650) and normalized.is_equal_approx(DEFAULT_POSITIONS[action]):
		if action == "grenade": normalized.x = 0.58
		elif action == "interact": normalized.y = 0.61
		elif action == "jump": normalized.y = 0.72
		elif action == "switch": normalized.y = 0.91
	return normalized

func control_point(action: String) -> Vector2:
	var rect := layout_rect()
	var point: Vector2 = rect.position + resolved_position(action) * rect.size
	var inset := Vector2.ONE * (hit_radius(action) + 1.0)
	# Keep the entire touch target inside notches and gesture insets, even at maximum scale.
	inset = inset.min(rect.size * 0.5)
	return point.clamp(rect.position + inset, rect.end - inset)

func action_at(point: Vector2) -> String:
	var closest := ""
	var best := INF
	for key in positions:
		if key == "move" and not editing: continue
		var distance := point.distance_to(control_point(key)) / hit_radius(key)
		if distance <= 1.0 and (distance < best or (distance == best and str(key) < closest)):
			closest = key
			best = distance
	return closest

func joystick_vector(offset: Vector2) -> Vector2:
	var stick := offset / radius("move")
	var length := stick.length()
	if length <= MOVE_DEADZONE: return Vector2.ZERO
	# A radial deadzone suppresses resting-thumb drift without a jump in speed.
	return stick.normalized() * clampf((length - MOVE_DEADZONE) / (1.0 - MOVE_DEADZONE), 0.0, 1.0) * Vector2(1, -1)

func _input(event: InputEvent) -> void:
	if not enabled or not is_visible_in_tree():
		return
	if event is InputEventScreenTouch:
		if event.pressed and not event.canceled:
			if not event.position.is_finite(): return
			var action := action_at(event.position)
			if editing:
				if action.is_empty() or fingers.values().has(action): return
				fingers[event.index] = action
			elif not action.is_empty():
				fingers[event.index] = action
				actions[action] = true
				if action == "buy": buy_pressed.emit()
				if action == "pause": pause_pressed.emit()
				if action == "switch": switch_pressed.emit()
				if action == "score": scoreboard_pressed.emit()
			elif (event.position.distance_to(control_point("move")) < radius("move") * 1.8 or (event.position.x < size.x * 0.43 and event.position.y > size.y * 0.28)) and not fingers.values().has("move"):
				fingers[event.index] = "move"
				move_origin = event.position
				move_position = event.position
			else:
				fingers[event.index] = "look"
		else:
			if not fingers.has(event.index): return
			var action: String = fingers.get(event.index, "")
			fingers.erase(event.index)
			if action == "move": movement = Vector2.ZERO
			elif not fingers.values().has(action): actions.erase(action)
			if editing: layout_changed.emit(exported_layout())
		get_viewport().set_input_as_handled()
		queue_redraw()
	elif event is InputEventScreenDrag and fingers.has(event.index):
		if not event.position.is_finite(): return
		var action: String = fingers[event.index]
		if editing and positions.has(action):
			var rect := safe_rect if safe_rect.size.x > 0 and safe_rect.size.y > 0 else Rect2(Vector2.ZERO, size)
			if rect.size.x <= 0 or rect.size.y <= 0: return
			var normalized: Vector2 = (event.position - rect.position) / rect.size
			positions[action] = normalized.clamp(Vector2.ZERO, Vector2.ONE)
		elif action == "move":
			move_position = event.position
			movement = joystick_vector(event.position - move_origin)
		elif action == "look" or action == "fire":
			if event.relative.is_finite(): look_delta += event.relative
		get_viewport().set_input_as_handled()
		queue_redraw()

func consume_look() -> Vector2:
	var value := look_delta
	look_delta = Vector2.ZERO
	return value

func _draw() -> void:
	if not enabled:
		return
	var font := ThemeDB.fallback_font
	var draw_scale := effective_scale()
	for key in positions:
		if key == "move": continue
		var point := control_point(key)
		var r := radius(key)
		# The compact plate stays within the existing 1.25-radius hit region.
		var compact: bool = key != "fire" and r < 32.0
		var paint_r := minf(r * 1.25, maxf(r, 26.0)) if compact else r
		var rim_r := paint_r + 1.0 if compact else paint_r
		var rim_shadow := 3.5 if compact else 5.25
		var icon_y := -13.0 if compact else -8.0
		var label_y := 6.0 if compact else 17.0
		draw_circle(point, paint_r, Color(0.045, 0.058, 0.072, 0.86))
		draw_arc(point, rim_r, 0, TAU, 48, Color(0.015, 0.02, 0.028, 0.96), rim_shadow)
		draw_arc(point, rim_r, 0, TAU, 48, Color(0.85, 0.72, 0.45, 0.95) if editing else Color(0.83, 0.87, 0.89, 0.95), 1.25)
		if key == "fire":
			draw_arc(point, paint_r - 5, -PI * 0.8, -PI * 0.2, 24, Color(0.77, 0.24, 0.30, 0.95), 2.5)
		if actions.get(key, false):
			draw_circle(point, paint_r - 3, Color(0.7, 0.15, 0.22, 0.65))
			draw_arc(point, rim_r, 0, TAU, 48, Color(0.85, 0.72, 0.45, 0.95), 2.0)
		var label_text: String = LABELS[key]
		var width := font.get_string_size(label_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 12).x
		var depleted: bool = counts.has(key) and int(counts[key]) <= 0
		var ink := Color(0.9, 0.92, 0.94, 0.35 if depleted else 0.9)
		var badge_offset := minf(r * 0.66, (hit_radius(key) - 12.625) / sqrt(2.0))
		var badge := point + Vector2(badge_offset, -badge_offset)
		if counts.has(key):
			# Badge paint precedes glyphs; digits remain above the original icon.
			draw_arc(badge, 9, 0, TAU, 48, Color(0.015, 0.02, 0.028, 0.96), 5.25)
			draw_circle(badge, 9, Color(0.78, 0.67, 0.43, 0.95) if not depleted else Color(0.3, 0.33, 0.37, 0.9))
			draw_arc(badge, 9, 0, TAU, 48, Color(0.83, 0.87, 0.89, 0.95), 1.25)
		var icon_surround := Color(0, 0, 0, 0.4 if depleted else 1.0)
		_draw_action_icon(key, point + Vector2(0, icon_y), icon_surround, 2.0)
		draw_string_outline(font, point + Vector2(-width / 2, label_y), label_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, 3, Color(0, 0, 0, 0.4 if depleted else 1.0))
		_draw_action_icon(key, point + Vector2(0, icon_y), ink)
		draw_string(font, point + Vector2(-width / 2, label_y), label_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(1, 1, 1, 0.4 if depleted else 1.0))
		if counts.has(key):
			var digits := str(int(counts[key]))
			var digit_width := font.get_string_size(digits, HORIZONTAL_ALIGNMENT_LEFT, -1, 12).x
			draw_string(font, badge + Vector2(-digit_width / 2, 4.5), digits, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(1, 1, 1) if depleted else Color(0.04, 0.05, 0.07))
	var origin := move_origin if not editing and fingers.values().has("move") else control_point("move")
	draw_arc(origin, 65 * draw_scale, 0, TAU, 48, Color(0.015, 0.02, 0.028, 0.96), 6.0)
	draw_arc(origin, 65 * draw_scale, 0, TAU, 48, Color(0.8, 0.85, 0.9, 0.95), 2.0)
	var knob := origin + Vector2(movement.x, -movement.y) * 40 * draw_scale
	draw_circle(knob, 23 * draw_scale, Color(0.015, 0.02, 0.028, 0.96))
	draw_arc(knob, 23 * draw_scale, 0, TAU, 48, Color(0.015, 0.02, 0.028, 0.96), 4.0)
	draw_circle(knob, 23 * draw_scale, Color(0.8, 0.85, 0.9, 0.9))
	if editing:
		draw_string(font, Vector2(size.x * 0.30, size.y * 0.45), "DRAG CONTROLS  /  TAP SAVE ABOVE", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color(0.9, 0.78, 0.5))

# Shared geometric glyphs require no textures or shader variants.
func _draw_action_icon(action: String, at: Vector2, color: Color, stroke_extra: float = 0.0) -> void:
	match action:
		"fire":
			draw_arc(at, 7, 0, TAU, 24, color, 1.5 + stroke_extra)
			for axis in [Vector2.LEFT, Vector2.RIGHT, Vector2.UP, Vector2.DOWN]: draw_line(at + axis * 10, at + axis * 14, color, 2 + stroke_extra)
			draw_circle(at, 2 + stroke_extra * 0.5, color)
		"reload":
			draw_arc(at, 8, -PI * 0.8, PI * 0.7, 22, color, 1.5 + stroke_extra)
			draw_line(at + Vector2(-5, -6), at + Vector2(-5, -1), color, 1.5 + stroke_extra)
			draw_line(at + Vector2(-5, -6), at + Vector2(0, -6), color, 1.5 + stroke_extra)
		"jump", "crouch":
			var sign_y := -1 if action == "jump" else 1
			draw_line(at + Vector2(-8, 3 * sign_y), at + Vector2(0, 8 * sign_y), color, 2 + stroke_extra)
			draw_line(at + Vector2(0, 8 * sign_y), at + Vector2(8, 3 * sign_y), color, 2 + stroke_extra)
			draw_line(at + Vector2(0, 8 * sign_y), at + Vector2(0, -7 * sign_y), color, 2 + stroke_extra)
		"switch":
			draw_line(at + Vector2(-10, -4), at + Vector2(10, -4), color, 1.5 + stroke_extra)
			draw_line(at + Vector2(10, -4), at + Vector2(6, -8), color, 1.5 + stroke_extra)
			draw_line(at + Vector2(10, 4), at + Vector2(-10, 4), color, 1.5 + stroke_extra)
			draw_line(at + Vector2(-10, 4), at + Vector2(-6, 8), color, 1.5 + stroke_extra)
		"grenade", "smoke":
			draw_rect(Rect2(at + Vector2(-5, -5), Vector2(10, 13)), color, false, 1.5 + stroke_extra)
			draw_line(at + Vector2(-3, -8), at + Vector2(4, -8), color, 2 + stroke_extra)
			if action == "smoke": draw_line(at + Vector2(-3, 0), at + Vector2(3, 0), color, 1.5 + stroke_extra)
		"pause":
			draw_line(at + Vector2(-4, -6), at + Vector2(-4, 7), color, 3 + stroke_extra)
			draw_line(at + Vector2(4, -6), at + Vector2(4, 7), color, 3 + stroke_extra)
		"score":
			for row in [-5, 0, 5]: draw_line(at + Vector2(-8, row), at + Vector2(8, row), color, 1.5 + stroke_extra)
		"buy":
			draw_rect(Rect2(at + Vector2(-8, -5), Vector2(16, 12)), color, false, 1.5 + stroke_extra)
			draw_line(at + Vector2(-3, -8), at + Vector2(3, -8), color, 2 + stroke_extra)
		"interact":
			draw_line(at + Vector2(-7, 0), at + Vector2(7, 0), color, 2 + stroke_extra)
			draw_line(at + Vector2(0, -7), at + Vector2(0, 7), color, 2 + stroke_extra)
