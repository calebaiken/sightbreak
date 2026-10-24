extends SceneTree
## Shots as a player sees them: the first-person flash of each weapon, and operators firing at 8, 22 and 40 m (the
## flash on their own bodies and, once it exists, the tracer). Fixture poses stepped by hand at 60 Hz, so the 40 ms
## flash is captured while it is lit even though the software rasteriser renders a frame in 0.3 s or more.
##   --capture-dir=<dir> --prefix=<name> --size=WxH (default 1280x720) --weapons=sidearm,smg,rifle,marksman --procedural (the procedural models)
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const Weapons = preload("res://scripts/gameplay/weapons.gd")
const WeaponModel = preload("res://scripts/gameplay/weapon_model.gd")
const VIEWS := {
	"backlit": [Vector3(0, 0.05, -19), PI - 0.08],
	"sunlit": [Vector3(3, 0.05, -12), 0.35],
}
var output := "res://../builds/qa/muzzle-presentation"
var prefix := "muzzle"
var wanted := ["sidearm", "smg", "rifle", "marksman"]
var world: Node3D
var actor: SBActor

func _initialize() -> void:
	_run.call_deferred()

func shot(name: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	if image.save_png(output.path_join("%s-%s.png" % [prefix, name])) != OK:
		push_error("Capture failed: " + name)
	print("MUZZLE CAPTURE: %s %dx%d" % [name, image.get_width(), image.get_height()])

func pose(view: String) -> void:
	var entry: Array = VIEWS[view]
	actor.global_position = entry[0]
	actor.yaw = entry[1]
	actor.rotation.y = entry[1]
	actor.camera.rotation.x = -0.025
	actor.tick_visual(0.016)

func settle(seconds: float) -> void:
	var remaining := seconds
	while remaining > 0.0:
		actor.tick_visual(1.0 / 60.0)
		remaining -= 1.0 / 60.0

func _run() -> void:
	var size := Vector2i(1280, 720)
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture-dir="):
			output = argument.trim_prefix("--capture-dir=")
		elif argument.begins_with("--prefix="):
			prefix = argument.trim_prefix("--prefix=")
		elif argument.begins_with("--weapons="):
			wanted = Array(argument.trim_prefix("--weapons=").split(","))
		elif argument == "--procedural":
			WeaponModel.use_authored = false
		elif argument.begins_with("--size="):
			var parts := argument.trim_prefix("--size=").split("x")
			if parts.size() == 2:
				size = Vector2i(int(parts[0]), int(parts[1]))
	root.content_scale_size = size
	root.size = size
	DirAccess.make_dir_recursive_absolute(output)
	world = Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	actor = Actor.new()
	actor.configure(1, 0, "Capture fixture", true)
	world.add_child(actor)
	actor.reset_for_round(Vector3(0, 0.05, -19))
	actor.credits = 20000
	actor.apply_cosmetic({})
	for id in wanted:
		if not Weapons.DATA.has(id):
			push_error("Unknown weapon " + id)
			continue
		if id != "sidearm":
			actor.buy_weapon(id)
		else:
			actor._equip("sidearm")
		actor._equip_blend = 0
		actor._kick = 0
		actor._flash = 0
		actor.reload_remaining = 0
		for view in VIEWS:
			pose(view)
			settle(0.4)
			await shot("%s-%s-ready" % [id, view])
			actor.play_shot_effect()
			actor.tick_visual(0.004)
			await shot("%s-%s-fire" % [id, view])
			settle(0.3)
	# Operators firing at the local player, in a row at three distances, both teams.
	actor._equip("sidearm")
	actor._equip_blend = 0
	var bots: Array[SBActor] = []
	for entry in [[0, 8.0, -1.2], [1, 8.0, 1.2], [0, 22.0, -2.0], [1, 22.0, 2.0], [0, 40.0, 0.0], [1, 40.0, 3.0]]:
		var bot := Actor.new()
		bot.configure(10 + bots.size(), entry[0], "Bot %d" % bots.size(), false)
		world.add_child(bot)
		bot.reset_for_round(Vector3(entry[2], 0.05, -19.0 + entry[1]))
		bot.yaw = 0.0
		bot.rotation.y = 0.0
		bots.append(bot)
	for view in VIEWS:
		pose(view)
		if view == "sunlit":
			actor.global_position = Vector3(0, 0.05, -19)
			actor.yaw = PI
			actor.rotation.y = PI
		settle(0.2)
		for bot in bots:
			bot.tick_visual(0.016)
			bot.play_shot_effect()
			bot.tick_visual(0.004)
		await shot("operators-%s-firing" % view)
		# The same six shots at three ages (seconds after the shot): flash and tracer together, then the tracer on its own.
		# Positive stop: fired at the local player, seen end-on; negative: fired across the lane, seen from the side.
		# A build without tracers (the baseline) simply has no streak in these frames.
		var tracer_script: GDScript = load("res://scripts/gameplay/tracer_effects.gd") if ResourceLoader.exists("res://scripts/gameplay/tracer_effects.gd") else null
		var tracers: Node = tracer_script.for_world(world) if tracer_script != null else null
		if tracers != null:
			tracers.set_process(false)
		var chest := actor.global_position + Vector3(0, 1.3, 0)
		for signed_stop in [0.015, 0.035, -0.015, -0.035]:
			var end_on: bool = signed_stop > 0.0
			var stop := absf(signed_stop)
			for bot in bots:
				bot.tick_visual(0.2)
			if tracers != null:
				for _step in 60:
					tracers._process(1.0 / 60.0)
			var space := world.get_world_3d().direct_space_state
			for bot in bots:
				bot.play_shot_effect()
				if bot.has_method("_tracer"):
					# Across: outward and away from the camera at about 33 degrees, ending where the shot would (the first surface, or 60 m).
					var origin: Vector3 = bot.global_position + Vector3(0, 1.3, 0)
					var heading := Vector3((1.0 if bot.global_position.x >= 1.0 else -1.0) * 0.55, 0.0, 0.83)
					var landing := space.intersect_ray(PhysicsRayQueryParameters3D.create(origin, origin + heading * 60.0, 1))
					var far_end: Vector3 = landing.position if not landing.is_empty() else origin + heading * 60.0
					bot._tracer(chest if end_on else far_end)
			var age := 0.0
			while age < stop - 0.0001:
				for bot in bots:
					bot.tick_visual(1.0 / 240.0)
				if tracers != null:
					tracers._process(1.0 / 240.0)
				age += 1.0 / 240.0
			await shot("operators-%s-%s-%03dms" % [view, "end-on" if end_on else "across", int(stop * 1000)])
		for bot in bots:
			bot.tick_visual(0.2)
	world.queue_free()
	await process_frame
	quit()
