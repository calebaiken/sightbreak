extends SceneTree
## Capability/input simulation through the real main controller, not hardware QA.
var checks := 0
var failures := 0

func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures += 1
		push_error(message)

func frames(count := 2) -> void:
	for _i in count: await process_frame

func _initialize() -> void:
	run.call_deferred()

func run() -> void:
	if FileAccess.file_exists("user://offline_training.json"):
		push_error("Use a fresh isolated state directory; player saves are never overwritten")
		quit(2)
		return
	var baseline := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--baseline-source="): baseline = arg.trim_prefix("--baseline-source=")
	var adapter := "\nvar simulated_capabilities := {\"mobile\":false,\"touchscreen\":false}\nvar simulated_pads: Array[int] = []\nvar simulated_axes := {}\nfunc input_capabilities() -> Dictionary:\n\treturn simulated_capabilities\nfunc connected_controllers() -> Array[int]:\n\treturn simulated_pads\nfunc controller_axis(device: int, axis: int) -> float:\n\treturn float(simulated_axes.get(Vector2i(device,axis),0.0))\nfunc controller_button(_device: int, _button: int) -> bool:\n\treturn false\n"
	var script := GDScript.new()
	if baseline.is_empty():
		script.source_code = "extends \"res://scripts/main.gd\"\n" + adapter
	else:
		# Baseline ONLY: replace the hardware-query boundary with declared simulated
		# capability. All controller decisions/capture/focus code remain unchanged.
		script.source_code = FileAccess.get_file_as_string(baseline).replace("DisplayServer.is_touchscreen_available()", "bool(input_capabilities().touchscreen)").replace("Input.get_connected_joypads()", "connected_controllers()").replace("Input.get_joy_axis(", "controller_axis(").replace("Input.is_joy_button_pressed(", "controller_button(") + adapter
	check(script.reload() == OK, "Capability adapter compiles")
	if failures: quit(1); return
	var main = script.new()
	root.add_child(main)
	await frames(3)
	for mobile in [false, true]:
		for capable in [false, true]:
			for requested in [false, true]:
				main.simulated_capabilities = {"mobile":mobile,"touchscreen":capable}
				main.profile.data.settings.touch_visible = requested
				check(main.uses_touch_controls() == (mobile or requested), "Touch policy mobile=%s capability=%s explicit=%s" % [mobile,capable,requested])
	main.simulated_capabilities = {"mobile":false,"touchscreen":true}
	main.profile.data.settings.touch_visible = false
	main.start_match({"mode":"offline","difficulty":"easy","name":"Input simulation"})
	await frames(2)
	var game = main.match_game
	game.process_mode = Node.PROCESS_MODE_DISABLED
	game.phase = "live" # Routing unit fixture only; never exported-objective evidence.
	check(not main.touch.enabled, "Touchscreen desktop HUD defaults to keyboard/mouse")
	var graphical := DisplayServer.get_name() != "headless"
	if graphical: check(Input.mouse_mode == Input.MOUSE_MODE_CAPTURED, "Touchscreen desktop captures mouse at match start")
	main.toggle_pause()
	check(main.paused and main.match_suspended and Input.mouse_mode == Input.MOUSE_MODE_VISIBLE, "Pause releases pointer and suspends offline match")
	main.close_overlay()
	if graphical: check(Input.mouse_mode == Input.MOUSE_MODE_CAPTURED, "Explicit desktop resume recaptures pointer")
	main.open_touch_editor()
	main.finish_touch_editor()
	if graphical: check(Input.mouse_mode == Input.MOUSE_MODE_CAPTURED, "Touch-editor dismissal follows desktop policy")
	main.simulated_capabilities.touchscreen = false
	main.profile.data.settings.touch_visible = true
	main.build_hud()
	main.close_overlay()
	check(main.touch.enabled and Input.mouse_mode == Input.MOUSE_MODE_VISIBLE, "Explicit desktop touch enables HUD and leaves pointer visible even without detected hardware")
	var motion := InputEventMouseMotion.new()
	motion.device = InputEvent.DEVICE_ID_EMULATION
	motion.screen_relative = Vector2(100,50)
	main._input(motion)
	check(main.mouse_delta == Vector2.ZERO, "Touch-generated mouse motion cannot duplicate aim")
	var mouse := InputEventMouseButton.new()
	mouse.button_index = MOUSE_BUTTON_LEFT
	mouse.pressed = true
	mouse.device = InputEvent.DEVICE_ID_EMULATION
	main._input(mouse)
	check(not main.physical_mouse_fire, "Touch-generated mouse cannot duplicate firing")
	main.touch.actions.fire = true
	main.touch.movement = Vector2(0.7,0.7)
	main.touch.look_delta = Vector2(10,5)
	mouse.device = 0
	main._input(mouse)
	var look_before: Vector2 = main.input_look
	main._physics_process(1.0/60)
	check(game._local_input.fire and game._local_input.move.length() <= 1.001, "Simultaneous real mouse/touch yields one bounded input state")
	check(main.input_look.is_equal_approx(look_before - Vector2(10,5)*float(main.profile.data.settings.touch_sensitivity)), "Touch aim is consumed once alongside physical mouse")
	var key := InputEventKey.new()
	key.physical_keycode = KEY_W
	key.pressed = true
	Input.parse_input_event(key.duplicate())
	main._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	main._physics_process(1.0/60)
	check(game._local_input.move == Vector2.ZERO, "Focus loss releases local held keyboard movement")
	check(not game._local_input.fire and game._local_input.move == Vector2.ZERO and main.mouse_delta == Vector2.ZERO, "Focus loss neutralizes simultaneous movement/fire/aim")
	main._notification(Node.NOTIFICATION_APPLICATION_FOCUS_IN)
	check(main.paused and Input.mouse_mode == Input.MOUSE_MODE_VISIBLE, "Focus restoration waits for explicit resume")
	main.close_overlay()
	main.switch_requested = true
	main._physics_process(1.0/60)
	check(not game._local_input.fire and game._local_input.move == Vector2.ZERO, "Explicit resume has no phantom keyboard/touch input")
	check(not main.switch_requested, "Focus-release wait discards queued weapon-switch edges")
	main.profile.data.settings.touch_visible = false
	main.build_hud()
	main.close_overlay()
	var release := key.duplicate()
	release.pressed = false
	# Source ordering reproduction: snapshots can see neutral input before a
	# controller tick acknowledges physical release. No native acceptance claim.
	var observer = preload("res://scripts/offline_diagnostics.gd").new()
	main.set_physics_process(false)
	check(main.waiting_for_input_release, "Held key retains focus-release guard before acknowledgment")
	Input.parse_input_event(release.duplicate())
	var released_before_tick: Dictionary = observer._snapshot(game)
	check(released_before_tick.ui.waiting_for_input_release and game._local_input.move == Vector2.ZERO and not game._local_input.fire, "Neutral command observation alone can precede controller release acknowledgment")
	Input.parse_input_event(key.duplicate())
	main._physics_process(1.0/60)
	check(main.waiting_for_input_release and game._local_input.move == Vector2.ZERO, "A premature fresh press before controller release acknowledgment remains safely blocked")
	var premature: Dictionary = observer._snapshot(game)
	Input.parse_input_event(release.duplicate())
	main._physics_process(1.0/60)
	var acknowledged: Dictionary = observer._snapshot(game)
	check(not acknowledged.ui.waiting_for_input_release, "Read-only observation distinguishes actual controller release acknowledgment")
	Input.parse_input_event(key.duplicate())
	main._physics_process(1.0/60)
	check(game._local_input.move.y == 1.0 and not main.waiting_for_input_release, "A fresh key press after acknowledged release reaches actual controller input")
	print("FOCUS_RELEASE_ORDERING " + JSON.stringify({"before_controller_tick": released_before_tick, "premature_press": premature, "acknowledged_release": acknowledged, "fresh_input": [game._local_input.move.x, game._local_input.move.y]}))
	Input.parse_input_event(release.duplicate())
	main._physics_process(1.0/60)
	main.set_physics_process(true)
	main.simulated_pads.assign([7])
	main.simulated_axes[Vector2i(7,JOY_AXIS_TRIGGER_RIGHT)] = 0.8
	await frames()
	main._physics_process(1.0/60)
	check(not main.uses_touch_controls() and not main.touch.enabled, "Controller connection does not switch desktop touch mode")
	check(game._local_input.fire, "Connected nonzero controller ID retains fire input")
	main._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	main._notification(Node.NOTIFICATION_APPLICATION_FOCUS_IN)
	main.close_overlay()
	main._physics_process(1.0/60)
	check(not game._local_input.fire, "A held controller trigger cannot resume fire after focus loss")
	main.simulated_axes.clear()
	main._physics_process(1.0/60)
	main.simulated_axes[Vector2i(3,JOY_AXIS_TRIGGER_RIGHT)] = 0.8
	main.simulated_pads.assign([3])
	main._physics_process(1.0/60)
	check(game._local_input.fire and not main.uses_touch_controls(), "Switching controller IDs preserves fire and selected desktop mode")
	main.simulated_axes.clear()
	main.simulated_pads.clear()
	main._physics_process(1.0/60)
	check(not game._local_input.fire and not main.uses_touch_controls(), "Controller disconnect clears input without changing mode")
	main.simulated_pads.assign([7,9])
	main.simulated_axes[Vector2i(9,JOY_AXIS_TRIGGER_RIGHT)] = 0.8
	main._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	main._notification(Node.NOTIFICATION_APPLICATION_FOCUS_IN)
	main.close_overlay()
	mouse.pressed = true
	main._input(mouse)
	main._physics_process(1.0/60)
	check(game._local_input.fire, "An unused second controller cannot block desktop resume")
	main.physical_mouse_fire = false
	main.simulated_axes[Vector2i(7,JOY_AXIS_LEFT_X)] = 0.1
	main._physics_process(1.0/60)
	check(game._local_input.move == Vector2.ZERO, "Accepted neutral left-stick drift does not move the player")
	main.simulated_axes[Vector2i(7,JOY_AXIS_RIGHT_X)] = 0.12
	main.simulated_axes[Vector2i(7,JOY_AXIS_RIGHT_Y)] = 0.12
	var diagonal_look: Vector2 = main.input_look
	main._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	main._notification(Node.NOTIFICATION_APPLICATION_FOCUS_IN)
	main.close_overlay()
	main._physics_process(1.0/60)
	check(main.input_look.is_equal_approx(diagonal_look), "Diagonal right-stick motion cannot resume aim before release")
	main.simulated_axes.clear()
	main.simulated_pads.clear()
	main._physics_process(1.0/60)
	main.touch.enabled = false
	main.touch.actions.fire = true
	main.touch.movement = Vector2.ONE
	main._physics_process(1.0/60)
	check(not game._local_input.fire and game._local_input.move == Vector2.ZERO, "Disabled touch input cannot inject stale movement or fire")
	main.touch.reset_input()
	main.simulated_capabilities = {"mobile":true,"touchscreen":false}
	main.build_hud()
	main.close_overlay()
	check(main.touch.enabled and Input.mouse_mode == Input.MOUSE_MODE_VISIBLE, "Mobile defaults to touch independently of reported hardware")
	main.leave_match()
	main.queue_free()
	await frames(3)
	print("INPUT_MODE_TEST checks=%d failures=%d graphical_pointer=%s scope=simulated_capabilities_and_input_not_physical_hardware baseline=%s" % [checks,failures,graphical,not baseline.is_empty()])
	quit(1 if failures else 0)
