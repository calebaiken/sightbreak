extends SceneTree
## Native first-person gallery for every weapon, plus the operator body at three distances.
## Fixture poses, not played matches; it asserts nothing about quality or frame rate. It exists so
## a reviewer sees all four weapons and both teams in identical cameras and lighting, which
## weapon_art_capture.gd (Relay AR only) does not provide.
## --capture-dir=<dir> output folder; --size=WxH viewport (default 1280x720);
## --weapons=sidearm,smg,rifle,marksman subset; --procedural uses the procedural weapon models.
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const WeaponModel = preload("res://scripts/gameplay/weapon_model.gd")
const Weapons = preload("res://scripts/gameplay/weapons.gd")
const VIEWS := {
	"backlit": [Vector3(0, 0.05, -19), PI - 0.08],
	"sunlit": [Vector3(3, 0.05, -12), 0.35],
	"shade": [Vector3(0, 0.05, 20.5), 0.1],
}
var output := "res://../builds/qa/presentation-gallery"
var wanted := ["sidearm", "smg", "rifle", "marksman"]
var world: Node3D
var actor: SBActor

func _initialize() -> void:
	_run.call_deferred()

func shot(name: String) -> void:
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	if image.save_png(output.path_join(name + ".png")) != OK:
		push_error("Capture failed: " + name)
	print("GALLERY CAPTURE: %s %dx%d" % [name, image.get_width(), image.get_height()])

func pose(view: String) -> void:
	var entry: Array = VIEWS[view]
	actor.global_position = entry[0]
	actor.yaw = entry[1]
	actor.rotation.y = entry[1]
	actor.camera.rotation.x = -0.025
	actor.tick_visual(0.016)

func settle(seconds: float = 0.0) -> void:
	# Advance the presentation clock in 60 Hz steps so equip and recoil blends reach the state under test.
	var remaining := seconds
	while remaining > 0.0:
		actor.tick_visual(1.0 / 60.0)
		remaining -= 1.0 / 60.0

func _run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture-dir="):
			output = argument.trim_prefix("--capture-dir=")
		elif argument.begins_with("--weapons="):
			wanted = Array(argument.trim_prefix("--weapons=").split(","))
		elif argument == "--procedural":
			WeaponModel.use_authored = false
		elif argument.begins_with("--size="):
			var parts := argument.trim_prefix("--size=").split("x")
			if parts.size() == 2:
				root.content_scale_size = Vector2i(int(parts[0]), int(parts[1]))
				root.size = root.content_scale_size
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
		var spec := Weapons.get_weapon(id)
		var reload_seconds := float(spec["reload"])
		actor._equip_blend = 0
		actor._kick = 0
		actor._flash = 0
		actor.reload_remaining = 0
		for view in VIEWS:
			pose(view)
			settle(0.4)
			await shot("%s-%s-ready" % [id, view])
		pose("backlit")
		actor._equip_blend = 0.6
		actor.tick_visual(0.016)
		await shot("%s-backlit-draw" % id)
		actor._equip_blend = 0
		settle(0.4)
		actor.play_shot_effect()
		actor.tick_visual(0.016)
		await shot("%s-backlit-fire" % id)
		actor._kick = 0
		actor._flash = 0
		settle(0.3)
		for fraction in [0.25, 0.5, 0.75]:
			actor.reload_remaining = reload_seconds * (1.0 - fraction)
			actor.tick_visual(0.016)
			await shot("%s-backlit-reload-%d" % [id, int(fraction * 100)])
		actor.reload_remaining = 0
		settle(0.5)
	# Operator bodies, both teams, three distances, as the local player sees them.
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
	pose("backlit")
	for bot in bots:
		bot.tick_visual(0.016)
	settle(0.3)
	await shot("operators-backlit-8-22-40m")
	pose("sunlit")
	actor.global_position = Vector3(0, 0.05, -19)
	actor.yaw = PI
	actor.rotation.y = PI
	settle(0.1)
	await shot("operators-sunlit-8-22-40m")
	world.queue_free()
	await process_frame
	quit()
