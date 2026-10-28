extends SceneTree
## Where the native plant scenario's smoke lands: thrown from a start position along a yaw and pitch, with every other bot idle.
const STEP := 1.0 / 60.0
const SPEED_UP := 5.0
var game: TacticalMatch

func _initialize() -> void:
	_run.call_deferred()

func _throw(start: Vector3, yaw: float, pitch: float) -> String:
	game = TacticalMatch.new()
	game.configure({"mode": "offline", "difficulty": "normal"})
	root.add_child(game)
	game._bot_clock = 1.0e12
	game.phase = "live"
	game.time_left = TacticalMatch.ROUND_SECONDS
	var human := game.local_actor()
	human.global_position = start
	await physics_frame
	for tick in 12:
		game.set_local_input({"move": Vector2.ZERO, "look": Vector2(yaw, pitch)})
		await physics_frame
	game.set_local_input({"move": Vector2.ZERO, "look": Vector2(yaw, pitch), "smoke": true})
	await physics_frame
	game.set_local_input({"move": Vector2.ZERO, "look": Vector2(yaw, pitch), "smoke": false})
	var t := 0.0
	var where := "none"
	while t < 3.0:
		await physics_frame
		t += STEP
		for child in game.get_children():
			if child is SBUtility and child.kind == "smoke":
				where = "%s detonated=%s" % [str(child.position.snapped(Vector3.ONE * 0.1)), str(child._detonated)]
	game.queue_free()
	await process_frame
	await process_frame
	return where

func _run() -> void:
	Engine.max_physics_steps_per_frame = 64
	Engine.physics_ticks_per_second = int(60.0 * SPEED_UP)
	Engine.time_scale = SPEED_UP
	var start := Vector3(-15, 0.05, 2)
	for yaw in [PI, PI + 0.25, PI + 0.5]:
		for pitch in [-0.8, -0.4, -0.2, 0.0, 0.2]:
			print("SMOKE_LANDING start=%s yaw=%.2f pitch=%.2f -> %s" % [str(start), yaw, pitch, await _throw(start, yaw, pitch)])
	Engine.time_scale = 1.0
	Engine.physics_ticks_per_second = 60
	await create_timer(0.6).timeout
	quit(0)
