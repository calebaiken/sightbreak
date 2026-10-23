extends SceneTree
## Independent source geometry probe; no exported/pixel acceptance is implied.
var receipt_path := ""
var cases: Array = []
var failures := 0

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--receipt="): receipt_path = argument.trim_prefix("--receipt=")
	run.call_deferred()

func settle(count := 5) -> void:
	for _i in count: await process_frame

func bounds(rect: Rect2) -> Array:
	return [rect.position.x, rect.position.y, rect.size.x, rect.size.y]

func snapshot(main: Node, entry: Control) -> Dictionary:
	var frame: Rect2 = main.kill_feed_frame.get_global_rect()
	var labels: Array = []
	var clipped: Array = []
	for node: Label in entry.find_children("*", "Label", true, false):
		var rect := node.get_global_rect()
		var row := {"text":node.text, "bounds":bounds(rect), "full_name":node.get_meta("full_name", "")}
		labels.append(row)
		if rect.position.x < frame.position.x - 0.1 or rect.end.x > frame.end.x + 0.1: clipped.append(row)
	var outer := entry.get_global_rect()
	return {"frame":bounds(frame), "entry":bounds(outer), "labels":labels, "clipped_labels":clipped,
		"row_inside_frame":outer.position.x >= frame.position.x - 0.1 and outer.end.x <= frame.end.x + 0.1,
		"selected_touch":main.uses_touch_controls(), "touch_enabled":main.touch.enabled, "paused":main.paused}

func run() -> void:
	if FileAccess.file_exists("user://offline_training.json"):
		push_error("Independent probe requires fresh isolated state")
		quit(2)
		return
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await settle()
	for dimensions in [Vector2i(1280,720), Vector2i(960,720)]:
		for scale in [1.0,1.3]:
			root.content_scale_size = dimensions
			root.size = dimensions
			main.profile.data.settings.touch_visible = false
			main.profile.data.settings.ui_text_scale = scale
			main.profile.data.settings.hud_positions = {}
			main.profile.data.settings.hud_scale = 1.0
			main.start_match({"mode":"offline", "difficulty":"easy", "name":"Independent feed probe"})
			main.match_game.process_mode = Node.PROCESS_MODE_DISABLED
			main.set_physics_process(false)
			await settle()
			var ids: Array = main.match_game.actors.keys()
			main.match_game.actors[ids[0]].display_name = "WWWWWWWWWWWWWWWWWWWWWWWW"
			main.match_game.actors[ids[1]].display_name = "MMMMMMMMMMMMMMMMMMMMMMMM"
			main.add_kill_feed(ids[0],ids[1],true)
			await settle()
			var entry: Control = main.kill_feed.get_child(0)
			var item := {"dimensions":[dimensions.x,dimensions.y], "text_scale":scale, "before":snapshot(main,entry)}
			main.toggle_pause()
			main.show_match_settings()
			await settle()
			var toggle: CheckButton
			for node in main.overlay.find_children("*","CheckButton",true,false):
				if node.text == "SHOW TOUCH CONTROLS ON DESKTOP": toggle = node
			if not is_instance_valid(toggle):
				push_error("Actual settings touch toggle missing")
				quit(2)
				return
			toggle.button_pressed = true
			await settle()
			item["paused_opt_in"] = snapshot(main,entry)
			main.close_overlay()
			await settle()
			item["resumed_opt_in"] = snapshot(main,entry)
			item["same_row"] = main.kill_feed.get_child(0) == entry
			var valid: bool = item.before.row_inside_frame and item.before.clipped_labels.is_empty() and item.resumed_opt_in.row_inside_frame and item.resumed_opt_in.clipped_labels.is_empty() and item.same_row
			item["passed"] = valid
			if not valid: failures += 1
			cases.append(item)
			print("LONG_FEED_TRANSITION_CASE " + JSON.stringify(item))
			main.leave_match()
			await settle()
	main.queue_free()
	await settle()
	var receipt := {"scope":"Independent headless source geometry, no native/pixel acceptance", "cases":cases, "failures":failures}
	if not receipt_path.is_empty():
		var file := FileAccess.open(receipt_path,FileAccess.WRITE)
		file.store_string(JSON.stringify(receipt,"  "))
		file.close()
	print("LONG_FEED_TRANSITION_TEST cases=%d failures=%d" % [cases.size(),failures])
	quit(1 if failures else 0)
