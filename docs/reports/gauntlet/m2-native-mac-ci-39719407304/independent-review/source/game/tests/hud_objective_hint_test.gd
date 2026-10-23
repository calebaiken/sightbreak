extends SceneTree
## Frozen source UI fixture only: no exported gameplay or rendered-layout pass.
## Exercise the actual _process status Label, never objective_hint directly.
var checks := 0
var failures := 0

func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures += 1
		push_error(message)

func _initialize() -> void:
	# Environment-only state roots do not redirect Godot's native macOS user://.
	# Use a private native directory before constructing any controller/profile.
	var original_user_dir := OS.get_user_data_dir()
	var fixture_name := "SIGHTBREAK_QA/hud-objective-hint-%d-%d" % [OS.get_process_id(), Time.get_ticks_usec()]
	ProjectSettings.set_setting("application/config/use_custom_user_dir", true)
	ProjectSettings.set_setting("application/config/custom_user_dir_name", fixture_name)
	var fixture_user_dir := OS.get_user_data_dir()
	if fixture_user_dir == original_user_dir or not fixture_user_dir.replace("\\", "/").ends_with("/" + fixture_name) or DirAccess.dir_exists_absolute(fixture_user_dir):
		push_error("HUD fixture requires a new, distinct native user-data directory: " + fixture_user_dir)
		quit(2)
		return
	if DirAccess.make_dir_recursive_absolute(fixture_user_dir) != OK:
		push_error("Cannot create private HUD fixture directory: " + fixture_user_dir)
		quit(2)
		return
	var marker_path := fixture_user_dir.path_join("hud-fixture-owner.txt")
	var marker := FileAccess.open(marker_path, FileAccess.WRITE)
	if marker == null:
		push_error("Cannot create private HUD fixture ownership marker: " + marker_path)
		quit(2)
		return
	marker.store_string(fixture_name)
	marker.close()
	if FileAccess.get_file_as_string("user://hud-fixture-owner.txt") != fixture_name:
		push_error("HUD fixture user:// does not resolve to its private native directory")
		quit(2)
		return
	print("HUD_OBJECTIVE_HINT_TEST_STATE native_user_dir=%s original_user_dir=%s owner=%s" % [fixture_user_dir, original_user_dir, fixture_name])
	run.call_deferred()

func expect_status(main: Node, game: Node, actor: Node, item: Dictionary, context: String) -> void:
	# These are declared HUD-only state inputs. Physics is disabled before its
	# first tick; none of this establishes objective or match completion evidence.
	game.phase = item.get("phase", "live")
	game.objective_state = item.get("objective", "carried")
	game.objective_carrier = actor.actor_id if item.get("carrier", true) else 2
	actor.team = item.get("team", 0)
	actor.alive = item.get("alive", true)
	actor.health = 100 if actor.alive else 0
	main.elapsed = 1000.0
	main.status_label.set_meta("until", 0.0)
	main.status_label.text = "STALE HUD TEXT"
	main._process(0.0)
	var actual: String = main.status_label.text
	check(actual == item.expected, "%s %s: expected '%s', actual '%s'" % [context, item.name, item.expected, actual])

func run() -> void:
	if FileAccess.file_exists("user://offline_training.json"):
		push_error("Use fresh isolated SIGHTBREAK_STATE_DIR; player saves are never overwritten")
		quit(2)
		return
	var source := "res://scripts/main.gd"
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--baseline-source="):
			source = argument.trim_prefix("--baseline-source=")
	var script: Script = load(source)
	if script == null or not script.can_instantiate():
		push_error("HUD main source did not compile: " + source)
		quit(2)
		return
	var main = script.new()
	main.set_process(false)
	main.set_physics_process(false)
	root.add_child(main)
	main.set_process(false)
	main.set_physics_process(false)
	main.start_match({"mode": "offline", "difficulty": "easy", "name": "Frozen HUD fixture"})
	var game = main.match_game
	game.set_process(false)
	game.set_physics_process(false)
	game.process_mode = Node.PROCESS_MODE_DISABLED
	var actor = game.local_actor()
	check(game._simulation_tick == 0 and game._elapsed == 0.0, "HUD fixture freezes before the first match tick")
	for touch_enabled in [false, true]:
		main.profile.data.settings.touch_visible = touch_enabled
		main.build_hud()
		var control := "USE" if touch_enabled else "E"
		var context := "touch=%s" % touch_enabled
		var cases := [
			{"name": "living attacker carrier", "expected": "HOLD %s AT A SITE TO PLANT" % control},
			{"name": "other living attacker", "carrier": false, "expected": "ESCORT THE DEVICE CARRIER"},
			{"name": "attacker dropped device", "objective": "dropped", "expected": "RECOVER THE RELAY DEVICE"},
			{"name": "attacker planted device", "objective": "planted", "expected": "DEFEND THE DEVICE"},
			{"name": "defender planted device", "team": 1, "objective": "planted", "expected": "HOLD %s NEAR THE DEVICE TO DEFUSE" % control},
			{"name": "defender carried device", "team": 1, "expected": "DEFEND THE TWO OBJECTIVE SITES"},
			{"name": "defender dropped device", "team": 1, "objective": "dropped", "expected": "DEFEND THE TWO OBJECTIVE SITES"},
			{"name": "post round", "phase": "post", "objective": "planted", "expected": "ROUND COMPLETE"},
			{"name": "completed operation", "phase": "match_over", "objective": "planted", "expected": "OPERATION COMPLETE"},
			{"name": "eliminated player", "alive": false, "objective": "planted", "expected": "SPECTATING YOUR SQUAD"},
			{"name": "authenticated waiting room", "phase": "waiting", "expected": "WAITING FOR AUTHENTICATED PLAYERS   1 / 10"},
			{"name": "buy phase", "phase": "buy", "expected": "BUY PHASE   /   %s TO EQUIP" % ("TAP BUY" if touch_enabled else "PRESS B")},
		]
		for item in cases:
			expect_status(main, game, actor, item, context)
		expect_status(main, game, actor, cases[0], context)
		main.show_notification("QA: live notification remains visible")
		main._process(0.0)
		check(main.status_label.text == "QA: live notification remains visible", context + ": unexpired live notification is preserved")
		main.elapsed = 1006.0
		main._process(0.0)
		check(main.status_label.text == cases[0].expected, context + ": expired live notification returns to the correct hint")
	check(game._simulation_tick == 0 and game._elapsed == 0.0, "Status rendering never advances the frozen gameplay fixture")
	check(main.profile.data.matches == 0 and not FileAccess.file_exists("user://offline_training.json"), "HUD fixture never awards or saves training progression")
	main.queue_free()
	await process_frame
	print("HUD_OBJECTIVE_HINT_TEST source=%s scope=frozen_source_ui checks=%d failures=%d" % [source, checks, failures])
	quit(1 if failures else 0)
