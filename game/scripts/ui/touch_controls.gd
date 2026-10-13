class_name TacticalTouch
extends Control
const SafeArea = preload("res://scripts/ui/safe_area.gd")

signal layout_changed(layout: Dictionary)
signal buy_pressed
signal pause_pressed
signal switch_pressed
signal scoreboard_pressed

var enabled := false
var editing := false
var hud_scale := 1.0
var movement := Vector2.ZERO
var look_delta := Vector2.ZERO
var actions: Dictionary = {}
var positions := {"fire": Vector2(0.89, 0.53), "jump": Vector2(0.91, 0.75),
	"crouch": Vector2(0.79, 0.83), "reload": Vector2(0.76, 0.62),
	"interact": Vector2(0.65, 0.72), "grenade": Vector2(0.61, 0.9),
	"smoke": Vector2(0.69, 0.9), "buy": Vector2(0.19, 0.14), "pause": Vector2(0.96, 0.07), "switch": Vector2(0.91, 0.9), "score": Vector2(0.08, 0.14)}
const LABELS := {"fire": "FIRE", "jump": "JUMP", "crouch": "LOW", "reload": "LOAD",
	"interact": "USE", "grenade": "FRAG", "smoke": "SMOKE", "buy": "BUY", "pause": "II", "switch": "SWAP", "score": "TEAM"}
var fingers: Dictionary = {}
var move_origin := Vector2.ZERO
var move_position := Vector2.ZERO
var safe_rect := Rect2()

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	resized.connect(refresh_safe_area)
	refresh_safe_area.call_deferred()

func refresh_safe_area() -> void:
	safe_rect = SafeArea.viewport_rect(size)
	queue_redraw()

func restore_layout(saved: Dictionary) -> void:
	for key in saved:
		if positions.has(key) and saved[key] is Array and saved[key].size() == 2:
			positions[key] = Vector2(clampf(float(saved[key][0]), 0.05, 0.95), clampf(float(saved[key][1]), 0.06, 0.94))
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

func radius(action: String) -> float:
	return (40.0 if action == "fire" else 28.0) * hud_scale

func control_point(action: String) -> Vector2:
	var rect := safe_rect if safe_rect.size.x > 0 else Rect2(Vector2.ZERO, size)
	return rect.position + positions[action] * rect.size

func _input(event: InputEvent) -> void:
	if not enabled or not is_visible_in_tree():
		return
	if event is InputEventScreenTouch:
		if event.pressed:
			var action := ""
			for key in positions:
				if event.position.distance_to(control_point(key)) <= radius(key) * 1.25:
					action = key
					break
			if editing:
				if action.is_empty(): return
				fingers[event.index] = action
			elif not action.is_empty():
				fingers[event.index] = action
				actions[action] = true
				if action == "buy": buy_pressed.emit()
				if action == "pause": pause_pressed.emit()
				if action == "switch": switch_pressed.emit()
				if action == "score": scoreboard_pressed.emit()
			elif event.position.x < size.x * 0.43 and event.position.y > size.y * 0.28 and not fingers.values().has("move"):
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
		var action: String = fingers[event.index]
		if editing and positions.has(action):
			var normalized: Vector2 = (event.position - safe_rect.position) / safe_rect.size
			positions[action] = Vector2(clampf(normalized.x, 0.05, 0.95), clampf(normalized.y, 0.08, 0.92))
		elif action == "move":
			move_position = event.position
			movement = ((event.position - move_origin) / (65.0 * hud_scale)).limit_length(1.0)
			movement.y = -movement.y
		elif action == "look" or action == "fire":
			look_delta += event.relative
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
	for key in positions:
		var point := control_point(key)
		var r := radius(key)
		draw_circle(point, r, Color(0.08, 0.1, 0.13, 0.65))
		draw_arc(point, r, 0, TAU, 48, Color(0.85, 0.72, 0.45, 0.95) if editing else Color(0.9, 0.9, 0.9, 0.55), 2.0)
		if actions.get(key, false): draw_circle(point, r - 5, Color(0.7, 0.15, 0.22, 0.55))
		var label_text: String = LABELS[key]
		var width := font.get_string_size(label_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 12).x
		draw_string(font, point + Vector2(-width / 2, 5), label_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color.WHITE)
	var origin := move_origin if fingers.values().has("move") else Vector2(size.x * 0.13, size.y * 0.74)
	draw_arc(origin, 65 * hud_scale, 0, TAU, 48, Color(0.8, 0.85, 0.9, 0.24), 2.0)
	draw_circle(origin + Vector2(movement.x, -movement.y) * 40 * hud_scale, 23 * hud_scale, Color(0.8, 0.85, 0.9, 0.25))
	if editing:
		draw_string(font, Vector2(size.x * 0.30, size.y * 0.45), "DRAG BUTTONS  /  ESC TO SAVE", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color(0.9, 0.78, 0.5))
