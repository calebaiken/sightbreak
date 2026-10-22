extends SceneTree
## Eye-level views of Relay Yard from fixed positions, for layout review. Fixture cameras at the
## standing eye height with the game's 82 degree field of view; no weapon, HUD or actors.
## --capture-dir=<dir> --size=WxH (default 1280x720) --prefix=<file prefix> (default view)
const Arena = preload("res://scripts/gameplay/arena.gd")
const EYE := 1.62
## [file stem, position (x, z), look-at (x, z), side that would stand there]
const VIEWS := [
	["01-attacker-pocket-looking-south", Vector2(0, -21), Vector2(0, -8), "attack"],
	["02-mid-pocket-looking-south", Vector2(0, -13), Vector2(0, 14), "attack"],
	["03-west-exit-looking-south", Vector2(-16.5, -16), Vector2(-15, 12), "attack"],
	["04-east-exit-looking-south", Vector2(16.5, -16), Vector2(15, 12), "attack"],
	["05-west-lane-to-site-a", Vector2(-11, -8), Vector2(-15, 10), "attack"],
	["06-mid-chicane-looking-south", Vector2(-4, -8), Vector2(0, 14), "attack"],
	["07-site-a-from-north-approach", Vector2(-12, 2), Vector2(-15, 10), "attack"],
	["08-site-a-defender-looking-north", Vector2(-15, 17), Vector2(-15, -14), "defend"],
	["09-defender-spawn-looking-north", Vector2(0, 20.5), Vector2(0, -18), "defend"],
	["10-site-b-defender-looking-north", Vector2(15, 17), Vector2(15, -14), "defend"],
	["11-yard-centre-looking-south", Vector2(0, -3), Vector2(0, 14), "attack"],
	["12-yard-centre-looking-north", Vector2(0, 6), Vector2(0, -16), "defend"],
]
var output := "res://../builds/qa/map-viewpoints"
var prefix := "view"

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var size := Vector2i(1280, 720)
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture-dir="):
			output = argument.trim_prefix("--capture-dir=")
		elif argument.begins_with("--prefix="):
			prefix = argument.trim_prefix("--prefix=")
		elif argument.begins_with("--size="):
			var parts := argument.trim_prefix("--size=").split("x")
			if parts.size() == 2:
				size = Vector2i(int(parts[0]), int(parts[1]))
	root.content_scale_size = size
	root.size = size
	DirAccess.make_dir_recursive_absolute(output)
	var world := Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	var camera := Camera3D.new()
	camera.fov = 82.0
	camera.near = 0.05
	camera.far = 200.0
	world.add_child(camera)
	camera.current = true
	for view in VIEWS:
		var at: Vector2 = view[1]
		var target: Vector2 = view[2]
		camera.look_at_from_position(Vector3(at.x, EYE, at.y), Vector3(target.x, EYE - 0.15, target.y), Vector3.UP)
		for _i in 3:
			await process_frame
		await RenderingServer.frame_post_draw
		var image := root.get_texture().get_image()
		var path := output.path_join("%s-%s.png" % [prefix, view[0]])
		if image.save_png(path) != OK:
			push_error("Capture failed: " + path)
		print("VIEWPOINT %s %dx%d" % [view[0], image.get_width(), image.get_height()])
	world.queue_free()
	await process_frame
	quit()
