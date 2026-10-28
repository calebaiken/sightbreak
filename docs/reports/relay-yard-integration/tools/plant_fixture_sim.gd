extends SceneTree
## The native plant scenario in the real physics: the human at the fixture start (-15, 2), the five defenders at the fixture's
## east/back row, every bot live. The human waits `delay` simulated seconds (the verifier throws a smoke and waits for its fuse
## first), walks the given legs at walking pace, then holds the plant. Reports whether and when the device was armed, or when
## the human died and who was nearest.
const STEP := 1.0 / 60.0
const SPEED_UP := 5.0
var game: TacticalMatch
var legs: Array = []

func _initialize() -> void:
	_run.call_deferred()

func _walk_to(actor: SBActor, point: Vector3, budget: float) -> float:
	var t := 0.0
	while t < budget and actor.alive:
		var flat := Vector3(point.x - actor.global_position.x, 0.0, point.z - actor.global_position.z)
		if flat.length() < 0.45:
			break
		game.set_local_input({"move": Vector2(0, 1), "look": Vector2(atan2(-flat.x, -flat.z), 0.0)})
		await physics_frame
		t += STEP
	return t

func _run() -> void:
	Engine.max_physics_steps_per_frame = 64
	Engine.physics_ticks_per_second = int(60.0 * SPEED_UP)
	Engine.time_scale = SPEED_UP
	var args := OS.get_cmdline_user_args()
	var route_name := args[0] if args.size() > 0 else "detour"
	var smoke_turn := float(args[1]) if args.size() > 1 else 0.0
	var smoke_pitch := float(args[2]) if args.size() > 2 else -0.8
	var settle := float(args[3]) if args.size() > 3 else 0.0
	if route_name == "detour":
		legs = [Vector3(-13.4, 0, 2.6), Vector3(-13.4, 0, 7.0), Vector3(-15, 0, 8)]
	else:
		legs = [Vector3(-15, 0, 8)]
	for delay in [2.0]:
		var armed := 0
		var died := 0
		var times := []
		for trial in 4:
			game = TacticalMatch.new()
			game.configure({"mode": "offline", "difficulty": "normal"})
			root.add_child(game)
			game.phase = "live"
			game.time_left = TacticalMatch.ROUND_SECONDS
			var human := game.local_actor()
			human.global_position = Vector3(-15, 0.05, 2)
			var defenders: Array = []
			for actor: SBActor in game.actors.values():
				if actor.team == 1:
					defenders.append(actor)
			defenders.sort_custom(func(a: SBActor, b: SBActor) -> bool: return a.actor_id < b.actor_id)
			for index in defenders.size():
				defenders[index].global_position = Vector3(13.2 + index * 2.2, 0.05, 20.5)
			await physics_frame
			var t := 0.0
			var aim := Vector2(PI + smoke_turn, smoke_pitch)
			for tick in 12:
				game.set_local_input({"move": Vector2.ZERO, "look": aim})
				await physics_frame
			game.set_local_input({"move": Vector2.ZERO, "look": aim, "smoke": true})
			await physics_frame
			while t < delay and human.alive:
				game.set_local_input({"move": Vector2.ZERO, "look": aim, "smoke": false})
				await physics_frame
				t += STEP
			for point: Vector3 in legs:
				t += await _walk_to(human, point, 20.0)
				var rested := 0.0
				while rested < settle and human.alive:
					game.set_local_input({"move": Vector2.ZERO, "look": Vector2(human.yaw, 0.0)})
					await physics_frame
					rested += STEP
					t += STEP
			var held := 0.0
			while held < TacticalMatch.PLANT_SECONDS + 1.0 and human.alive and game.objective_state != "planted":
				game.set_local_input({"move": Vector2.ZERO, "look": Vector2(human.yaw, 0.0), "interact": true})
				await physics_frame
				held += STEP
				t += STEP
			if game.objective_state == "planted":
				armed += 1
				times.append("%.1f" % t)
			elif not human.alive:
				died += 1
				times.append("dead@%.1f" % t)
			else:
				times.append("none@%.1f" % t)
			game.queue_free()
			await process_frame
			await process_frame
		print("PLANT_FIXTURE smoke_turn=%+.2f pitch=%.1f settle=%.1f route=%s delay=%.0fs armed=%d/4 died=%d/4 times=%s" % [smoke_turn, smoke_pitch, settle, route_name, delay, armed, died, " ".join(times)])
	Engine.time_scale = 1.0
	Engine.physics_ticks_per_second = 60
	await create_timer(0.6).timeout
	quit(0)
