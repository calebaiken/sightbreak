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
	await hud_mode_transitions(main)
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

func hud_footer(main: Node) -> Label:
	for node in main.ui.find_children("*", "Label", true, false):
		if "ROSTER" in node.text and "MENU" in node.text: return node
	return null

func check_hud_mode(main: Node, expected: bool, context: String) -> void:
	var footer := hud_footer(main)
	check(is_instance_valid(footer), context + " keeps its control-hint label")
	if is_instance_valid(footer):
		check(footer.visible == not expected, context + " shows keyboard hints only in desktop mode")
		if not expected:
			check(footer.text == "B  BUY     E  OBJECTIVE     TAB  ROSTER     ESC  MENU", context + " restores the actual keyboard bindings")
	if expected:
		var pause_left: float = main.touch.global_position.x + main.touch.control_point("pause").x - main.touch.radius("pause")
		check(main.action_label.get_global_rect().end.x < pause_left, context + " clears the MENU target from device-state text")
	check(absf(main.score_label.get_global_rect().get_center().x - main.ui.size.x * 0.5) < 1.0, context + " keeps the score centered")
	for node: Control in [main.health_label, main.ammo_label]:
		var rect := node.get_global_rect()
		check(rect.position.x >= 0 and rect.end.x <= main.ui.size.x + 1 and rect.position.y >= 0 and rect.end.y <= main.ui.size.y + 1, context + " keeps health/ammunition on screen")

## Exercise live settings signals without rebuilding the HUD. Pausing disables
## touch input independently of the selected presentation; mobile forces touch.
func hud_mode_transitions(main: Node) -> void:
	var cases := [
		{"size":Vector2i(1280,720), "scale":1.0, "initial":false, "mobile":false},
		{"size":Vector2i(960,720), "scale":1.0, "initial":false, "mobile":false},
		{"size":Vector2i(1280,720), "scale":1.3, "initial":false, "mobile":false},
		{"size":Vector2i(960,720), "scale":1.3, "initial":false, "mobile":false},
		{"size":Vector2i(1280,720), "scale":1.0, "initial":true, "mobile":false},
		{"size":Vector2i(1280,720), "scale":1.3, "initial":false, "mobile":true},
	]
	var saved := {"fire":[0.86,0.57], "move":[0.18,0.76]}
	for item in cases:
		root.content_scale_size = item.size
		root.size = item.size
		main.simulated_capabilities = {"mobile":item.mobile,"touchscreen":true}
		main.profile.data.settings.ui_text_scale = item.scale
		main.profile.data.settings.touch_visible = item.initial
		main.profile.data.settings.hud_positions = saved.duplicate(true)
		main.profile.data.settings.hud_scale = 1.5
		main.start_match({"mode":"offline","difficulty":"easy","name":"HUD mode simulation"})
		main.match_game.process_mode = Node.PROCESS_MODE_DISABLED
		main.set_physics_process(false)
		await frames(4)
		var context := "%s at %d%% mobile=%s initial=%s" % [item.size, roundi(item.scale * 100), item.mobile, item.initial]
		check_hud_mode(main, item.mobile or item.initial, context + " initial")
		var original_touch: Control = main.touch
		var original_action: Label = main.action_label
		var original_status: Label = main.status_label
		var original_layout: Dictionary = main.touch.exported_layout()
		var ids: Array = main.match_game.actors.keys()
		main.add_kill_feed(ids[0], ids[1], false)
		var original_feed: Node = main.kill_feed.get_child(0)
		for requested in [not item.initial, item.initial]:
			main.toggle_pause()
			main.show_match_settings()
			await frames()
			var settings_overlay: Control = main.overlay
			var toggle: CheckButton
			for node in main.overlay.find_children("*", "CheckButton", true, false):
				if node.text == "SHOW TOUCH CONTROLS ON DESKTOP": toggle = node
			check(is_instance_valid(toggle), context + " has the actual desktop touch preference")
			if not is_instance_valid(toggle): continue
			toggle.button_pressed = requested
			await frames(4)
			var expected: bool = item.mobile or requested
			check(main.profile.data.settings.touch_visible == requested, context + " setting signal changes the preference")
			check(main.paused and main.match_suspended and not main.touch.enabled, context + " settings keeps input disabled and training suspended")
			check(main.overlay == settings_overlay and main.touch == original_touch and main.action_label == original_action and main.status_label == original_status and original_feed.get_parent() == main.kill_feed, context + " mode change preserves active overlay and HUD nodes")
			check_hud_mode(main, expected, context + " paused preference=%s" % requested)
			main.close_overlay()
			await frames(4)
			check(main.touch.enabled == expected and not main.paused and not main.match_suspended, context + " explicit resume follows selected mode")
			check(main.touch.exported_layout() == original_layout and main.profile.data.settings.hud_positions == saved and is_equal_approx(main.touch.hud_scale, 1.5), context + " mode change preserves saved custom layout and button scale")
			check_hud_mode(main, expected, context + " resumed preference=%s" % requested)
		# A focus interruption must not reinterpret temporary input disablement as
		# a desktop-mode selection or bypass the existing neutral-input guard.
		main.touch.actions.fire = true
		main.touch.movement = Vector2.ONE
		main._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
		await frames()
		check_hud_mode(main, item.mobile or item.initial, context + " focus paused")
		check(main.waiting_for_input_release and not main.touch.enabled and main.touch.actions.is_empty() and main.touch.movement == Vector2.ZERO, context + " focus loss retains input guard and clears held touch")
		main._notification(Node.NOTIFICATION_APPLICATION_FOCUS_IN)
		main.close_overlay()
		main._physics_process(1.0/60)
		check(not main.match_game._local_input.fire and main.match_game._local_input.move == Vector2.ZERO, context + " explicit resume has no stale touch movement/fire")
		main.leave_match()
		await frames(3)
	main.set_physics_process(true)
	main.profile.data.settings.ui_text_scale = 1.0
	main.profile.data.settings.hud_scale = 1.0
	main.profile.data.settings.hud_positions = {}
