extends SceneTree
## The main menu's account lines and its response to a changing screen, on the real menu:
##   * the record card shows only what the server has said about the account: an unloaded
##     account has no name and no balance, an ended session says so, and "0 earned credits" appears
##     only for a balance the server stated to be zero;
##   * leaving the armory while it is still loading, then the load finishing, updates the card;
##   * when the screen's size or the device's safe area changes, the menu is built again for the
##     room it now has, settles in a frame or two, and stays settled (no rebuild every frame).
## The safe-area insets are synthetic (DeviceSafeArea.simulated_insets), not device measurements.
const DESIGN = preload("res://scripts/ui/design_tokens.gd")
const SAFE_AREA = preload("res://scripts/ui/safe_area.gd")
var failures: Array[String] = []
var checks := 0

func _initialize() -> void:
	call_deferred("run")

func check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

func frames(count: int) -> void:
	for i in count:
		await process_frame

func world() -> Dictionary:
	return (JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/backend_world.json")) as Dictionary).world

func card_text(main: Node, node_name: String) -> String:
	var label := main.ui.find_child(node_name, true, false) as Label
	return "" if label == null else label.text

func state_lines(main: Node, panel: Node) -> Array[String]:
	main.show_menu()
	await frames(3)
	return [card_text(main, "OnlineIdentity"), card_text(main, "OnlineCredits")]

func set_account(panel: Node, state: String) -> void:
	var account: Dictionary = (world().account as Dictionary).duplicate(true)
	panel.api.token = "fixture-only"
	panel.session_expired = false
	panel.is_loading = false
	panel.load_error = ""
	panel.account = account
	match state:
		"signed_out":
			panel.api.token = ""
			panel.account = {}
		"expired":
			panel.api.token = ""
			panel.session_expired = true
			panel.account = {}
		"loading":
			panel.is_loading = true
			panel.account = {}
		"unavailable":
			panel.account = {}
			panel.load_error = "Could not connect to the server"
		"stale":
			panel.load_error = "Could not connect to the server"
		"zero":
			panel.account.credits = 0
		"missing":
			panel.account.erase("credits")

func record_card(main: Node, panel: Node) -> void:
	var expectations := {
		"signed_out": ["", ""],
		"expired": ["SESSION ENDED", "SIGN IN AGAIN IN THE ARMORY"],
		"loading": ["ONLINE   ·   LOADING ACCOUNT…", "EARNED CREDITS UNAVAILABLE"],
		"unavailable": ["ONLINE   ·   ACCOUNT NOT LOADED", "EARNED CREDITS UNAVAILABLE"],
		"ready": ["ONLINE   ·   QA FIXTURE", "1,250 EARNED CREDITS"],
		"stale": ["ONLINE   ·   QA FIXTURE", "1,250 EARNED CREDITS   ·   LAST CONFIRMED"],
		"zero": ["ONLINE   ·   QA FIXTURE", "0 EARNED CREDITS"],
		"missing": ["ONLINE   ·   QA FIXTURE", "EARNED CREDITS UNAVAILABLE"],
	}
	for state in expectations:
		set_account(panel, state)
		var lines := await state_lines(main, panel)
		check(lines == expectations[state], "Record card, %s: %s (wanted %s)" % [state, str(lines), str(expectations[state])])
		if state not in ["zero", "signed_out", "ready", "stale"]:
			check(not lines[1].begins_with("0 ") and "0 EARNED" not in lines[1], "Record card, %s: no balance is invented" % state)
	# A name that is only control characters leaves no empty segment.
	set_account(panel, "ready")
	panel.account.display_name = "\n​"
	var lines := await state_lines(main, panel)
	check(lines[0] == "ONLINE" and lines[1] == "1,250 EARNED CREDITS", "A name with nothing printable leaves just ONLINE: " + str(lines))
	# Back during the refresh: the menu shows the account as loading, then follows the answer.
	set_account(panel, "loading")
	main.show_menu()
	await frames(3)
	check(card_text(main, "OnlineIdentity") == "ONLINE   ·   LOADING ACCOUNT…", "Back during the refresh shows the account as loading")
	var nav_before: Node = main.ui.find_child("MenuNav", true, false)
	panel.is_loading = false
	panel.account = (world().account as Dictionary).duplicate(true)
	panel._announce_account()
	await frames(3)
	check(main.screen == "menu" and card_text(main, "OnlineCredits") == "1,250 EARNED CREDITS", "When the refresh finishes behind the menu, the card shows the confirmed balance")
	check(main.ui.find_child("MenuNav", true, false) != nav_before, "...by building the menu again")
	set_account(panel, "loading")
	main.show_menu()
	await frames(3)
	panel.is_loading = false
	panel.load_error = "Could not connect to the server"
	panel._announce_account()
	await frames(3)
	check(card_text(main, "OnlineIdentity") == "ONLINE   ·   ACCOUNT NOT LOADED" and card_text(main, "OnlineCredits") == "EARNED CREDITS UNAVAILABLE", "When the refresh fails behind the menu, the card says the account is not loaded")
	# While the armory itself is on screen the menu is not rebuilt underneath it.
	main.open_economy("inventory")
	await frames(2)
	var screen_before: String = main.screen
	panel._announce_account()
	await frames(2)
	check(main.screen == screen_before and main.screen == "economy", "An account change while the armory is open leaves it open")
	main.show_menu()
	await frames(2)

func resized_menu(main: Node, panel: Node) -> void:
	set_account(panel, "ready")
	main.profile.data.settings.ui_text_scale = 1.3
	main.ui.theme = main.build_theme()
	SAFE_AREA.simulated_insets = Vector4(96, 0, 96, 21)
	var fresh := {}
	var sequence := [Vector2i(1600, 720), Vector2i(960, 720), Vector2i(1560, 720), Vector2i(1024, 768), Vector2i(960, 720), Vector2i(1600, 720)]
	var rebuilt_ids: Array[int] = []
	for dimensions: Vector2i in sequence:
		root.content_scale_size = dimensions
		root.size = dimensions
		# No call to show_menu: the menu must notice by itself.
		await frames(4)
		var context := "%dx%d at 130%% with 96/21 px insets" % [dimensions.x, dimensions.y]
		check(main.screen == "menu", context + ": still on the menu")
		check(main.menu_layout.region == main.menu_region(), context + ": the layout was measured for this room (%s vs %s)" % [main.menu_layout.region, main.menu_region()])
		var live: Dictionary = main.menu_layout.duplicate()
		var nav: Node = main.ui.find_child("MenuNav", true, false)
		# Stable: several more frames change nothing.
		await frames(6)
		check(main.ui.find_child("MenuNav", true, false) == nav, context + ": the menu does not rebuild frame after frame once settled")
		# The same layout a fresh build chooses.
		main.show_menu()
		await frames(4)
		fresh = main.menu_layout
		check(fresh.side_by_side == live.side_by_side and fresh.compact == live.compact, context + ": the live layout is the one a fresh build chooses (side_by_side %s/%s, compact %s/%s)" % [live.side_by_side, fresh.side_by_side, live.compact, fresh.compact])
		# Nothing is drawn into the insets.
		var safe: Rect2 = SAFE_AREA.viewport_rect(Vector2(dimensions))
		var intruders: Array[String] = []
		for node: Control in main.ui.find_children("*", "Control", true, false):
			if not (node is Label or node is Button) or not node.is_visible_in_tree() or node.size.x <= 0:
				continue
			var rect := node.get_global_rect()
			if rect.position.x < safe.position.x - 1 or rect.end.x > safe.end.x + 1:
				intruders.append("%s '%s' %s" % [node.get_class(), String(node.get("text")).left(16), rect])
		check(intruders.is_empty(), context + ": no label or button enters the insets (safe x %.0f to %.0f) %s" % [safe.position.x, safe.end.x, str(intruders.slice(0, 3))])
	# At the narrow size the menu stacks; at the wide one it sits side by side.
	root.content_scale_size = Vector2i(1600, 720)
	root.size = Vector2i(1600, 720)
	await frames(4)
	check(main.menu_layout.side_by_side, "At 1600 wide the columns share a row")
	root.content_scale_size = Vector2i(960, 720)
	root.size = Vector2i(960, 720)
	await frames(4)
	check(not main.menu_layout.side_by_side, "Resized to 960 wide with the same menu object, the columns stack")
	# A safe-area change with the same size is noticed too.
	var region_before: Vector2 = main.menu_layout.region
	SAFE_AREA.simulated_insets = Vector4(0, 0, 0, 0)
	await frames(4)
	check(main.menu_layout.region != region_before and main.menu_layout.region == main.menu_region(), "Removing the insets alone rebuilds the menu for the larger room")
	SAFE_AREA.simulated_insets = Vector4.ZERO
	main.profile.data.settings.ui_text_scale = 1.0
	main.ui.theme = main.build_theme()
	root.content_scale_size = Vector2i(1280, 720)
	root.size = Vector2i(1280, 720)
	await frames(3)

func run() -> void:
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await frames(3)
	main.open_economy("inventory")
	await frames(2)
	var panel = main.economy_panel
	main.show_menu()
	await frames(3)
	await record_card(main, panel)
	await resized_menu(main, panel)
	panel.api.token = ""
	panel.account = {}
	main.queue_free()
	await frames(3)
	if failures.is_empty():
		print("PASS: Menu account lines and resize handling (%d checks)" % checks)
		quit(0)
	else:
		print("FAIL: %d of %d menu-state checks" % [failures.size(), checks])
		for failure in failures.slice(0, 40):
			print("  - " + failure)
		quit(1)
