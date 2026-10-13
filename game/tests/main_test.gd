extends SceneTree
var checks := 0
var failures := 0
func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures += 1
		push_error(message)
func _initialize() -> void:
	call_deferred("run")
func frames(count: int) -> void:
	for i in count: await physics_frame
func run() -> void:
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await frames(3)
	check(main.screen == "menu" and main.menu_camera.current, "Native main menu and3D preview start")
	main.show_settings()
	await frames(2)
	check(main.screen == "settings", "Settings screen opens")
	main.show_progress()
	check(main.screen == "progress", "Local progression opens")
	main.show_connect()
	check(main.screen == "connect", "LAN connection controls open")
	main.open_economy("inventory")
	await frames(2)
	var original_panel = main.economy_panel
	check(original_panel.visible and original_panel.api.token.is_empty(), "Offline armory opens without fabricated online identity")
	main.show_menu()
	check(not original_panel.visible, "Armory closes without losing its session node")
	main.open_economy("cases")
	check(main.economy_panel == original_panel, "Same account UI instance reused between visits")
	main.show_menu()
	main.start_match({"mode": "offline", "difficulty": "normal", "name": "QA"})
	await frames(4)
	var game = main.match_game
	var actor = game.local_actor()
	check(game.actors.size() == 10 and actor.is_local, "Deploy creates playable5v5 session")
	check(absf(wrapf(main.input_look.x - actor.yaw, -PI, PI)) < 0.01, "Local view inherits the side's spawn facing")
	main.show_buy()
	check(main.paused and main.overlay != null, "Requisition opens")
	main.close_overlay()
	actor.credits = 2500
	game.request_buy("smg")
	check(actor.weapon_id == "smg" and actor.credits == 1400, "HUD match purchase buys weapon with match funds")
	game.time_left = 0.01
	await frames(3)
	check(game.phase == "live", "Round starts from buy phase")
	var mouse := InputEventMouseButton.new()
	mouse.button_index = MOUSE_BUTTON_LEFT
	mouse.pressed = true
	mouse.device = InputEvent.DEVICE_ID_EMULATION
	main._input(mouse)
	main._physics_process(1.0 / 60.0)
	check(not game._local_input.fire, "Touch-emulated mouse press never fires the weapon")
	var emulated_motion := InputEventMouseMotion.new()
	emulated_motion.device = InputEvent.DEVICE_ID_EMULATION
	emulated_motion.relative = Vector2(100, 50)
	main._input(emulated_motion)
	check(main.mouse_delta == Vector2.ZERO, "Touch-emulated mouse motion cannot double-apply aim")
	mouse.device = 0
	main._input(mouse)
	main._physics_process(1.0 / 60.0)
	check(game._local_input.fire, "Physical desktop mouse still fires normally")
	main._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	main._physics_process(1.0 / 60.0)
	check(not game._local_input.fire, "Application focus loss releases physical fire")
	main.touch.enabled = true
	main.touch.actions.fire = true
	main._physics_process(1.0 / 60.0)
	check(game._local_input.fire, "Dedicated touch fire button reaches authoritative input")
	main.touch.reset_input()
	main.touch.movement = Vector2(0.5, 0.5)
	main._physics_process(1.0 / 60.0)
	check(not game._local_input.fire and game._local_input.move == Vector2(0.5, 0.5), "Joystick movement alone cannot fire")
	main.touch.reset_input()
	var look_before: Vector2 = main.input_look
	main.touch.look_delta = Vector2(10, 5)
	main._physics_process(1.0 / 60.0)
	var expected_look: Vector2 = look_before - Vector2(10, 5) * float(main.profile.data.settings.touch_sensitivity)
	check(main.input_look.is_equal_approx(expected_look), "Touch aiming applies configured sensitivity exactly once")
	main.open_touch_editor()
	check(main.paused and main.touch.editing, "Mobile HUD editor opens without controlling character")
	main.touch.positions.fire = Vector2(0.5, 0.5)
	main.touch.reset_layout()
	check(main.touch.positions.fire == main.Touch.DEFAULT_POSITIONS.fire, "Reset HUD restores original usable layout")
	var escape := InputEventKey.new()
	escape.keycode = KEY_ESCAPE
	escape.pressed = true
	main._input(escape)
	check(not main.paused and not main.touch.editing, "Escape saves and fully closes HUD editor")
	var before: Vector3 = actor.position
	var key := InputEventKey.new()
	key.physical_keycode = KEY_W
	key.pressed = true
	Input.parse_input_event(key)
	await frames(25)
	key.pressed = false
	Input.parse_input_event(key)
	check(actor.position.distance_to(before) > 0.3, "Actual desktop W input moves local actor through main input pipeline")
	main.toggle_pause()
	check(main.paused and main.overlay != null, "Field menu opens")
	main.toggle_pause()
	check(not main.paused, "Field menu resumes")
	main.leave_match()
	await frames(3)
	check(main.screen == "menu" and main.match_game == null, "Leaving match restores menu without continuing world")
	main.queue_free()
	await frames(3)
	print("MAIN_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
