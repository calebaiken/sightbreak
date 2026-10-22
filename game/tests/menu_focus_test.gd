extends SceneTree
## Real scene focus and action routing; synthetic events are not hardware proof.
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
	var main_script = load("res://scripts/main.gd")
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--baseline-source="):
			main_script = GDScript.new()
			main_script.source_code = FileAccess.get_file_as_string(arg.trim_prefix("--baseline-source="))
			if main_script.reload() != OK:
				quit(2)
				return
	var main = main_script.new()
	root.add_child(main)
	await frames(3)
	main.start_match({"mode":"offline", "difficulty":"easy", "name":"Focus test"})
	await frames(2)
	for _i in 3:
		main.toggle_pause()
		await frames()
		var focused := root.gui_get_focus_owner()
		check(focused is Button and focused.text == "RESUME", "FIELD MENU initially focuses RESUME for keyboard/controller access")
		check(main.paused and main.match_suspended, "Keyboard menu pauses ordinary offline match")
		if focused is Button:
			var next := focused.find_next_valid_focus()
			check(next is Button and next.text == "SETTINGS", "Keyboard focus order reaches SETTINGS after RESUME")
			var cursor: Control = focused
			for expected in ["SETTINGS", "EDIT TOUCH HUD", "LEAVE MATCH", "RESUME"]:
				cursor = cursor.find_next_valid_focus()
				check(cursor is Button and cursor.text == expected, "FIELD MENU Tab cycle stays inside the overlay: " + expected)
			var previous := focused.find_prev_valid_focus()
			check(previous is Button and previous.text == "LEAVE MATCH", "FIELD MENU reverse navigation wraps to LEAVE MATCH")
			var action := InputEventAction.new()
			action.action = "ui_accept"
			action.pressed = true
			root.push_input(action)
			await frames(1)
			action = InputEventAction.new()
			action.action = "ui_accept"
			action.pressed = false
			root.push_input(action)
			await frames()
			check(not main.paused and not main.match_suspended, "ui_accept explicitly resumes from the focused button")
		else:
			main.close_overlay()
		await frames()
		check(root.gui_get_focus_owner() == null, "Closing the menu releases its focus owner")
	main.leave_match()
	main.queue_free()
	await frames(3)
	print("MENU_FOCUS_TEST checks=%d failures=%d scope=scene_focus_synthetic_actions_not_physical_hardware" % [checks,failures])
	quit(1 if failures else 0)
