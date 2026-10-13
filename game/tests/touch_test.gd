extends SceneTree
const Touch = preload("res://scripts/ui/touch_controls.gd")
const SafeArea = preload("res://scripts/ui/safe_area.gd")
var checks := 0
var failures := 0
var clicks := 0
func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures += 1
		push_error(message)
func _initialize() -> void: call_deferred("run")
func press(index: int, position: Vector2, down: bool = true) -> void:
	var e := InputEventScreenTouch.new()
	e.index = index
	e.position = position
	e.pressed = down
	root.push_input(e)
func run() -> void:
	root.size = Vector2i(1280, 720)
	var touch = Touch.new()
	root.add_child(touch)
	touch.enabled = true
	await process_frame
	press(0, Vector2(100, 500))
	press(1, touch.control_point("fire"))
	press(2, touch.control_point("crouch"))
	press(3, Vector2(900, 300))
	check(touch.fingers.size() == 4, "Four independent touch pointers tracked")
	check(touch.actions.get("fire", false) and touch.actions.get("crouch", false), "Fire and crouch held simultaneously")
	var drag := InputEventScreenDrag.new()
	drag.index = 0
	drag.position = Vector2(130, 460)
	drag.relative = Vector2(30, -40)
	root.push_input(drag)
	check(touch.movement.x > 0 and touch.movement.y > 0, "Left joystick moves forward/right")
	drag = InputEventScreenDrag.new()
	drag.index = 3
	drag.position = Vector2(910, 302)
	drag.relative = Vector2(10, 2)
	root.push_input(drag)
	check(touch.consume_look() == Vector2(10, 2), "Fourth finger aims while firing and moving")
	press(1, touch.control_point("fire"), false)
	check(not touch.actions.get("fire", false) and touch.fingers.size() == 3, "One pointer release doesn't cancel other pointers")
	touch.reset_input()
	touch.editing = true
	var save := Button.new()
	save.text = "SAVE TOUCH LAYOUT"
	save.position = Vector2(480, 130)
	save.size = Vector2(250, 50)
	save.pressed.connect(func(): clicks += 1)
	root.add_child(save)
	await process_frame
	press(0, Vector2(500, 150))
	await process_frame
	press(0, Vector2(500, 150), false)
	await process_frame
	check(clicks == 1, "HUD edit overlay leaves save button reachable by touch")
	var old_position: Vector2 = touch.control_point("fire")
	press(2, old_position)
	drag = InputEventScreenDrag.new()
	drag.index = 2
	drag.position = Vector2(1100, 300)
	drag.relative = drag.position - old_position
	root.push_input(drag)
	press(2, drag.position, false)
	var layout: Dictionary = touch.exported_layout()
	var restored = Touch.new()
	restored.restore_layout(layout)
	check(restored.positions.fire.is_equal_approx(touch.positions.fire), "Edited positions serialize and restore")
	var scaled: Rect2 = SafeArea.scaled_rect(Vector2(1280, 720), Vector2(2400, 1350), Rect2(100, 50, 2250, 1250))
	check(scaled.position.is_equal_approx(Vector2(53.33333, 26.66667)), "Device safe inset scaled into viewport coordinates")
	check(scaled.end.x < 1280 and scaled.end.y < 720, "Device safe trailing insets retained")
	restored.free()
	save.queue_free()
	touch.queue_free()
	await process_frame
	print("TOUCH_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
