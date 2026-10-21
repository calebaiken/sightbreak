extends SceneTree
## Source-level initialization/observer boundaries only, never exported gameplay.
const Diagnostics = preload("res://scripts/offline_diagnostics.gd")
const Match = preload("res://scripts/gameplay/match.gd")
const Profile = preload("res://scripts/profile.gd")
var checks := 0
var failures := 0

func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures += 1
		push_error(message)

func _initialize() -> void:
	run.call_deferred()

func run() -> void:
	var diagnostics_script: Script = load("res://scripts/offline_diagnostics.gd")
	var match_script: Script = load("res://scripts/gameplay/match.gd")
	if not diagnostics_script.can_instantiate() or not match_script.can_instantiate():
		push_error("Offline diagnostics dependencies did not compile")
		quit(1)
		return
	var output := ProjectSettings.globalize_path("user://offline-diagnostics-unit")
	if DirAccess.dir_exists_absolute(output):
		push_error("Use fresh isolated test state; earlier evidence is never overwritten")
		quit(2)
		return
	var profile: Dictionary = Profile.DEFAULTS.duplicate(true)
	check(Diagnostics.create([], profile) == null, "Ordinary launches do not activate diagnostics")
	check(Diagnostics.create(["--offline-validation", "--offline-trace-dir=relative"], profile) == null, "Relative diagnostic output is rejected")
	check(Diagnostics.create(["--offline-validation", "--offline-trace-dir=" + output, "--server"], profile) == null, "Network server arguments reject offline diagnostics")
	check(Diagnostics.create(["--offline-validation", "--offline-trace-dir=" + output, "--offline-scenario=winner"], profile) == null, "Unknown scenarios cannot inject results")
	check(Diagnostics.create(["--offline-validation", "--offline-trace-dir=" + output, "--offline-seed=-1"], profile) == null, "Invalid deterministic seed is rejected")
	var existing := profile.duplicate(true)
	existing.matches = 1
	existing.history = [{"rounds": 12}]
	check(Diagnostics.create(["--offline-validation", "--offline-trace-dir=" + output, "--offline-scenario=plant"], existing) == null, "Objective fixtures cannot replace existing earned training history")
	var observer = Diagnostics.create(["--offline-validation", "--offline-trace-dir=" + output], profile)
	check(observer != null, "Explicit debug observer accepts isolated offline profile")
	if observer == null: quit(1); return
	for mode in ["server", "client"]:
		var network: Dictionary = observer.configure_match({"mode": mode, "port": 27020})
		check(not network.has(Diagnostics.FIXTURE_KEY) and not observer.active, "Observer cannot authorize network mode " + mode)
		check(not DirAccess.dir_exists_absolute(output), "Network configuration creates no trace output")
	var ordinary_options: Dictionary = observer.configure_match({"mode": "offline", "difficulty": "easy"})
	var ordinary = Match.new()
	ordinary.configure(ordinary_options)
	root.add_child(ordinary)
	ordinary.process_mode = Node.PROCESS_MODE_DISABLED
	check(Diagnostics.fixture_for(ordinary.options, ordinary.arena).is_empty(), "Trace-only run has no seed, side or spawn fixture")
	check(ordinary.local_actor().team == 0 and ordinary.local_actor().position == Vector3(-4.4,0.05,-21), "Trace-only run keeps ordinary local team/spawn")
	var position: Vector3 = ordinary.local_actor().position
	var random_state: int = ordinary._rng.state
	observer.begin_match(ordinary)
	observer.observe(ordinary, 1.0)
	check(ordinary.phase == "buy" and ordinary.round_number == 1 and ordinary.time_left == Match.BUY_SECONDS, "Observation does not advance rounds or timers")
	check(ordinary.local_actor().position == position and ordinary._rng.state == random_state, "Observation does not move actors or consume gameplay randomness")
	observer.completed(ordinary, {"won":true}, profile)
	var ordinary_state: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(output.path_join("status.json")))
	check(int(ordinary_state.completion_calls) == 0 and not ordinary_state.has("summary"), "Observer rejects a completion call before a real match result")
	observer.finish()
	root.remove_child(ordinary)
	ordinary.queue_free()
	await process_frame
	var stale = Diagnostics.create(["--offline-validation", "--offline-trace-dir=" + output, "--offline-scenario=plant"], profile)
	var stale_options: Dictionary = stale.configure_match({"mode":"offline"})
	check(not stale.active and not stale_options.has(Diagnostics.FIXTURE_KEY), "Existing trace is rejected before fixture authorization")
	var stale_game = Match.new()
	stale_game.configure(stale_options)
	root.add_child(stale_game)
	stale_game.process_mode = Node.PROCESS_MODE_DISABLED
	check(stale_game.local_actor().position == Vector3(-4.4,0.05,-21) and stale_game.local_actor().team == 0, "Rejected stale observer cannot alter initial positions or teams")
	root.remove_child(stale_game)
	stale_game.queue_free()
	await process_frame
	for scenario in ["plant", "defuse"]:
		var destination := output.path_join(scenario)
		var diagnostic = Diagnostics.create(["--offline-validation", "--offline-trace-dir=" + destination, "--offline-scenario=" + scenario, "--offline-seed=42"], profile)
		var game = Match.new()
		game.configure(diagnostic.configure_match({"mode":"offline", "difficulty":"easy"}))
		root.add_child(game)
		game.process_mode = Node.PROCESS_MODE_DISABLED
		check(game.actors.size() == 10, scenario + ": all ten actors remain present")
		var attack_count := 0
		var defense_count := 0
		var seeded := true
		for actor in game.actors.values():
			attack_count += int(actor.team == 0)
			defense_count += int(actor.team == 1)
			seeded = seeded and actor._rng.seed == 42 * 97 + actor.actor_id
			check(actor.alive and actor.health == 100, scenario + ": actor starts with ordinary living health")
		check(attack_count == 5 and defense_count == 5, scenario + ": original 5v5 team counts retained")
		check(seeded and game._rng.seed == 42, scenario + ": declared match/spread seeds established before physics")
		check(game.objective_state == "carried" and game.objective_timer == 0 and game.interaction_progress == 0, scenario + ": no objective state or progress is injected")
		check(game.phase == "buy" and game.time_left == Match.BUY_SECONDS and game.attack_score == 0 and game.defend_score == 0, scenario + ": normal round timers and scores retained")
		check(game.arena.attack_spawns[0] == Vector3(-4.4,0.05,-21) and game.arena.defend_spawns[0] == Vector3(-4.4,0.05,20.5), scenario + ": stock spawn definitions restored before physics")
		if scenario == "plant":
			check(game.local_actor().team == 0 and game.objective_carrier == game.local_id and game.arena.is_at_site(game.local_actor().position) == -1, "Plant fixture requires actual approach from outside site")
		else:
			check(game.local_actor().team == 1 and game.objective_carrier != game.local_id, "Defuse fixture requires ordinary attacker carrier")
			var carrier = game.actors[game.objective_carrier]
			check(carrier.team == 0 and game.arena.is_at_site(carrier.position) == 0 and game.local_actor().position.distance_to(carrier.position) > 2.8, "Defuse fixture starts outside range with an unplanted normal bot carrier at A")
		diagnostic.begin_match(game)
		var initial: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(destination.path_join("status.json")))
		check(initial.initial_conditions == "declared_initial_spawns_side_and_seeds_only" and initial.actor_spread_seeds.size() == 10, scenario + ": full declared initial layout and seeds are recorded")
		check(initial.actors.size() == 10 and initial.protocol == 6 and not initial.prediction_enabled and initial.rules.plant_seconds == 3 and initial.rules.defuse_seconds == 5, scenario + ": trace records actors and unchanged rules/contracts")
		diagnostic.finish()
		root.remove_child(game)
		game.queue_free()
		await process_frame
	await process_frame
	print("OFFLINE_DIAGNOSTICS_TEST checks=%d failures=%d scope=source_initialization_and_read_only_observer_not_exported_gameplay" % [checks,failures])
	quit(1 if failures else 0)
