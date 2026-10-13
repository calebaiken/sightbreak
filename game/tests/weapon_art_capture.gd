extends SceneTree
## Real-engine review captures of the first-person rifle. Fixture poses, not played
## matches; asserts nothing about visual quality or frame rate.
## --capture-dir=<dir> output folder; --procedural captures the procedural rifle
## (the "before" model) instead of the authored one; --size=WxH sets the viewport
## (default 1280x720). The window's --resolution does not change the captured
## viewport under this project's canvas_items stretch, so this sets root.size, as the
## landscape tests do, and prints the real image size.
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const WeaponModel = preload("res://scripts/gameplay/weapon_model.gd")
const INSPECTOR = preload("res://scripts/ui/item_inspector.gd")
const SKIN := {"kind": "weapon_skin", "collection": "Crimson Archive", "rarity": "Legendary", "pattern_seed": 897, "wear": 0.2}
var output := "res://../builds/qa/weapon-art"
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
	print("WEAPON CAPTURE: %s %dx%d" % [name, image.get_width(), image.get_height()])

func pose(at: Vector3, yaw: float, pitch: float = -0.025) -> void:
	actor.global_position = at
	actor.yaw = yaw
	actor.rotation.y = yaw
	actor.camera.rotation.x = pitch
	actor.tick_visual(0.016)

func _run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture-dir="):
			output = argument.trim_prefix("--capture-dir=")
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
	actor.credits = 5000
	actor.buy_weapon("rifle")
	actor._equip_blend = 0
	actor.apply_cosmetic({})
	# Sun from behind the target (the spawn view), sun on the weapon, and full shade.
	pose(Vector3(0, 0.05, -19), PI - 0.08)
	await shot("01-yard-backlit-ready")
	actor.play_shot_effect()
	actor.tick_visual(0.016)
	await shot("02-yard-backlit-fire")
	actor._kick = 0
	actor._flash = 0
	actor.reload_remaining = 1.25
	actor.tick_visual(0.016)
	await shot("03-yard-backlit-reload")
	actor.reload_remaining = 0
	pose(Vector3(3, 0.05, -12), 0.35)
	await shot("04-yard-sunlit-ready")
	pose(Vector3(0, 0.05, 20.5), 0.1)
	await shot("05-hall-shade-ready")
	actor.apply_cosmetic(SKIN)
	pose(Vector3(3, 0.05, -12), 0.35)
	await shot("06-yard-sunlit-skin")
	world.queue_free()
	await process_frame
	var inspector := INSPECTOR.new()
	inspector.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(inspector)
	await process_frame
	inspector.show_item(SKIN.merged({"name": "Relay AR / Crimson Archive"}))
	await process_frame
	await shot("07-inspection-skin")
	inspector.queue_free()
	await process_frame
	quit()
