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
	check(touch.consume_look() == Vector2.ZERO, "Touch aim is consumed once without an artificial smoothing tail")
	for sample in [Vector2(3, 1), Vector2(4, -2), Vector2(-1, 5)]:
		drag.relative = sample
		root.push_input(drag)
	check(touch.consume_look() == Vector2(6, 4), "High-frequency touch motion sums exactly across physics ticks")
	drag.relative = Vector2(NAN, 1)
	root.push_input(drag)
	check(touch.consume_look() == Vector2.ZERO, "Malformed non-finite touch motion cannot corrupt camera aim")
	drag.index = 0
	drag.position = Vector2(INF, 100)
	var old_movement: Vector2 = touch.movement
	root.push_input(drag)
	check(touch.movement == old_movement, "Malformed pointer position cannot poison joystick movement")
	press(12, Vector2(NAN, 200))
	check(not touch.fingers.has(12), "Malformed pointer press cannot reserve a finger action")
	drag.index = 1
	drag.position = touch.control_point("fire") + Vector2(4, -3)
	drag.relative = Vector2(4, -3)
	root.push_input(drag)
	check(touch.consume_look() == Vector2(4, -3) and touch.actions.get("fire", false), "Fire-button drag aims continuously without releasing automatic fire")
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
	# Saved HUD data is user-controlled; invalid coordinates cannot poison rendering/input.
	var baseline: Vector2 = restored.positions.fire
	restored.restore_layout({"fire": [NAN, 0.5], "jump": ["bad", {}], "unknown": [0.5, 0.5]})
	check(restored.positions.fire == baseline, "Non-finite layout values ignored")
	restored.restore_layout({"fire": [-30, 30]})
	check(restored.positions.fire == Vector2(0, 1), "Finite layout positions clamped")
	touch.editing = false
	touch.safe_rect = Rect2(80, 24, 1120, 640)
	touch.hud_scale = 1.5
	touch.positions.fire = Vector2(0, 1)
	var edge: Vector2 = touch.control_point("fire")
	check(edge.x - touch.radius("fire") >= 80 and edge.y + touch.radius("fire") <= 664, "Whole enlarged button stays inside safe bounds")
	touch.hud_scale = NAN
	check(touch.hud_scale == 1.0, "Invalid HUD scale falls back to usable default")
	check(touch.joystick_vector(Vector2(2, -2)) == Vector2.ZERO, "Radial deadzone suppresses resting-thumb drift")
	check(touch.joystick_vector(Vector2(500, -500)).length() <= 1.00001, "Diagonal joystick movement has unit limit")
	check(touch.joystick_vector(Vector2(8, 0)).length() < 0.01, "Deadzone transition is continuous")
	touch.positions.fire = Vector2(0.8, 0.5)
	touch.positions.reload = Vector2(0.82, 0.5)
	check(touch.action_at(touch.control_point("reload")) == "reload", "Overlapping targets choose nearest center instead of dictionary order")
	press(5, touch.control_point("fire"))
	press(6, touch.control_point("fire"))
	press(5, touch.control_point("fire"), false)
	check(touch.actions.get("fire", false), "Second finger keeps shared fire action held")
	var cancel := InputEventScreenTouch.new()
	cancel.index = 6
	cancel.pressed = true
	cancel.canceled = true
	root.push_input(cancel)
	check(not touch.actions.get("fire", false), "OS cancellation releases action even with pressed flag")
	press(7, touch.control_point("fire"))
	touch._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	check(touch.fingers.is_empty() and touch.actions.is_empty(), "Backgrounding releases held fire and pointers")
	press(8, touch.control_point("fire"))
	touch.enabled = false
	check(touch.actions.is_empty() and touch.movement == Vector2.ZERO, "Disabling controls clears all input")
	touch.enabled = true
	press(9, touch.control_point("fire"))
	touch.hide()
	check(touch.actions.is_empty(), "Hidden HUD cannot leave a stuck fire input")
	touch.show()
	touch.editing = true
	var old_stick: Vector2 = touch.control_point("move")
	press(10, old_stick)
	drag = InputEventScreenDrag.new()
	drag.index = 10
	drag.position = Vector2(400, 500)
	drag.relative = drag.position - old_stick
	root.push_input(drag)
	press(10, drag.position, false)
	check(touch.control_point("move").distance_to(Vector2(400, 500)) < 1, "Joystick anchor can be customized")
	restored.restore_layout(touch.exported_layout())
	check(restored.positions.move == touch.positions.move, "Joystick anchor persists with button layout")
	check(touch.movement == Vector2.ZERO and touch.actions.is_empty(), "Editing controls never moves or fires character")
	check(SafeArea.scaled_rect(Vector2(1280, 720), Vector2(2400, 1350), Rect2(9999, 9999, 1, 1)) == Rect2(0, 0, 1280, 720), "Stale device safe area falls back to viewport")
	touch.size = Vector2(1920, 720)
	touch.safe_rect = Rect2(70, 0, 1780, 720)
	check(touch.control_point("pause").x + touch.radius("pause") <= 1850, "Ultrawide landscape HUD respects trailing notch inset")
	restored.free()
	save.queue_free()
	touch.queue_free()
	await process_frame
	print("TOUCH_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
