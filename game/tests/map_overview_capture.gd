extends SceneTree
## Top-down orthographic render of Relay Yard for layout review, with optional overlays.
## Fixture camera, not gameplay. --capture-dir=<dir> --size=WxH (default 1400x1400)
## --name=<file stem> (default overview). North (+z) is at the top of the image.
const Arena = preload("res://scripts/gameplay/arena.gd")
const BotAI = preload("res://scripts/gameplay/bot_ai.gd")
var output := "res://../builds/qa/map-overview"
var stem := "overview"

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var size := Vector2i(1400, 1400)
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture-dir="):
			output = argument.trim_prefix("--capture-dir=")
		elif argument.begins_with("--name="):
			stem = argument.trim_prefix("--name=")
		elif argument.begins_with("--size="):
			var parts := argument.trim_prefix("--size=").split("x")
			if parts.size() == 2:
				size = Vector2i(int(parts[0]), int(parts[1]))
	root.content_scale_size = size
	root.size = size
	DirAccess.make_dir_recursive_absolute(output)
	var world := Node3D.new()
	root.add_child(world)
	var arena: RelayYard = Arena.new()
	world.add_child(arena)
	var camera := Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 54.0
	camera.position = Vector3(0, 80, 0)
	camera.rotation_degrees = Vector3(-90, 0, 0)
	camera.near = 1.0
	camera.far = 200.0
	world.add_child(camera)
	camera.current = true
	# Markers: attacker spawns (blue), defender spawns (red), defender anchors (yellow), sites (white rings).
	var marker_height := 7.5
	for spawn in arena.attack_spawns:
		_marker(world, spawn + Vector3(0, marker_height, 0), Color(0.2, 0.55, 1.0), 0.7)
	for spawn in arena.defend_spawns:
		_marker(world, spawn + Vector3(0, marker_height, 0), Color(1.0, 0.25, 0.2), 0.7)
	for anchor in BotAI.DEFENDER_ANCHORS:
		_marker(world, anchor + Vector3(0, marker_height, 0), Color(1.0, 0.9, 0.2), 0.5)
	for site in arena.sites:
		_marker(world, site + Vector3(0, marker_height, 0), Color(1, 1, 1), 1.4)
	for _i in 3:
		await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	var path := output.path_join(stem + ".png")
	if image.save_png(path) != OK:
		push_error("Capture failed")
	print("MAP OVERVIEW: %s %dx%d" % [path, image.get_width(), image.get_height()])
	world.queue_free()
	await process_frame
	quit()

func _marker(parent: Node3D, at: Vector3, color: Color, radius: float) -> void:
	var node := MeshInstance3D.new()
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = 0.2
	node.mesh = mesh
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	node.material_override = material
	node.position = at
	parent.add_child(node)
