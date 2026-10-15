extends SceneTree
## Measures what the first-person weapon looks like under different lighting, from real
## rendered frames. For each scenario and pose it renders the scene, hides each part in
## turn and counts the pixels that change: those are the part's visible pixels, whatever
## covers it. It reports their luma (0-255, sRGB-encoded) as median, 10th and 90th
## percentile and local detail, so "the magazine is near black" and "the fill kept
## the receiver's value" are numbers. Needs a native display. Presentation only.
##   --out=<dir>   also saves the base frame of every case
##   --tag=<name>  label printed on every line (before / after)
##   --scenarios=a,b  only these scenarios (sun, backlight, shade, dark interior)   --poses=a,b  only these poses
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const ViewmodelShading = preload("res://scripts/gameplay/viewmodel_shading.gd")
const RELOAD_SECONDS := 2.25
## Where the camera stands and looks: the three yard views the art captures use, and the
## shade view again with the sun and sky scaled down, standing in for a dark interior.
const SCENARIOS := {
	"sun": {"at": Vector3(3, 0.05, -12), "yaw": 0.35, "sun": 1.0, "ambient": 1.0},
	"backlight": {"at": Vector3(0, 0.05, -19), "yaw": PI - 0.08, "sun": 1.0, "ambient": 1.0},
	"shade": {"at": Vector3(0, 0.05, 20.5), "yaw": 0.1, "sun": 1.0, "ambient": 1.0},
	"dark interior": {"at": Vector3(0, 0.05, 20.5), "yaw": 0.1, "sun": 0.08, "ambient": 0.3},
}
## Reload progress per pose; -1 is the ready pose.
const POSES := {"ready": -1.0, "grab": 0.15, "mid reload": 0.5, "seat": 0.84}
const PARTS := ["magazine", "receiver", "handguard", "furniture", "grip", "gloves", "sleeves"]
var output := ""
var tag := "probe"
var only_scenarios: PackedStringArray = []
var only_poses: PackedStringArray = []
var world: Node3D
var actor: SBActor
var sun: DirectionalLight3D
var environment: Environment
var debug_material: ShaderMaterial

func _initialize() -> void:
	_run.call_deferred()

func _frame() -> Image:
	for i in 3:
		await process_frame
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image()

func _luma(c: Color) -> float:
	return (0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b) * 255.0

## Visible pixels of a part: those that differ between the frame with it and without it.
func _mask(shown: Image, hidden: Image) -> PackedInt32Array:
	var mask := PackedInt32Array()
	var width := shown.get_width()
	for y in range(0, shown.get_height(), 2):
		for x in range(0, width, 2):
			var p := shown.get_pixel(x, y)
			var q := hidden.get_pixel(x, y)
			if absf(p.r - q.r) + absf(p.g - q.g) + absf(p.b - q.b) > 0.03:
				mask.append(y * width + x)
	return mask

func _stats(image: Image, mask: PackedInt32Array) -> Dictionary:
	if mask.size() < 12:
		return {"n": mask.size()}
	var width := image.get_width()
	var values: Array[float] = []
	var detail := 0.0
	for index in mask:
		var x := index % width
		var y := index / width
		var here := _luma(image.get_pixel(x, y))
		values.append(here)
		var around := (_luma(image.get_pixel(maxi(x - 3, 0), y)) + _luma(image.get_pixel(mini(x + 3, width - 1), y)) + _luma(image.get_pixel(x, maxi(y - 3, 0))) + _luma(image.get_pixel(x, mini(y + 3, image.get_height() - 1)))) * 0.25
		detail += absf(here - around)
	values.sort()
	return {"n": values.size() * 4, "median": values[values.size() / 2], "p10": values[int(values.size() * 0.1)], "p90": values[int(values.size() * 0.9)], "detail": detail / values.size()}

func _part_node(part: String) -> Node3D:
	match part:
		"magazine": return actor._magazine
		"receiver": return actor._gun.get_node("paint_receiver")
		"handguard": return actor._gun.get_node("paint_handguard")
		"furniture": return actor._gun.get_node("body")
		"grip": return actor._gun.get_node_or_null("grip")
		_: return actor._gun.get_node("arms")

func _set_pose(progress: float) -> void:
	actor._equip_blend = 0.0
	actor._kick = 0.0
	actor._flash = 0.0
	actor.reload_remaining = 0.0
	actor._reload_clock = 0.0
	actor.tick_visual(0.016)
	if progress >= 0.0:
		actor.reload_remaining = RELOAD_SECONDS * (1.0 - progress)
		actor.tick_visual(0.016)

func _debug_arms() -> void:
	# The arms' albedo with no lighting, drawn through the viewmodel projection, so the
	# glove and the sleeve can be told apart by the colour they were authored with.
	var arms: MeshInstance3D = actor._gun.get_node("arms").find_children("*", "MeshInstance3D", true, false).front()
	var shader := Shader.new()
	shader.code = "shader_type spatial;\nrender_mode unshaded;\n" + ViewmodelShading.UNIFORMS + "uniform sampler2D albedo_texture : source_color;\nvoid vertex() {\n" + ViewmodelShading.PROJECT + "}\nvoid fragment() { ALBEDO = texture(albedo_texture, UV).rgb; }\n"
	debug_material = ShaderMaterial.new()
	debug_material.shader = shader
	debug_material.set_shader_parameter("albedo_texture", load(SBWeaponModel.RELAY_AR_ARMS_TEXTURES + "_albedo.png"))
	ViewmodelShading.enable(debug_material)
	arms.set_meta("lit_material", arms.material_override)

func _run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("A native rendering display is required")
		quit(2)
		return
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--out="):
			output = argument.trim_prefix("--out=")
			DirAccess.make_dir_recursive_absolute(output)
		elif argument.begins_with("--tag="):
			tag = argument.trim_prefix("--tag=")
		elif argument.begins_with("--scenarios="):
			only_scenarios = argument.trim_prefix("--scenarios=").split(",")
		elif argument.begins_with("--poses="):
			only_poses = argument.trim_prefix("--poses=").split(",")
	root.content_scale_size = Vector2i(1280, 720)
	root.size = Vector2i(1280, 720)
	world = Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	for node in world.find_children("*", "DirectionalLight3D", true, false):
		sun = node
	for node in world.find_children("*", "WorldEnvironment", true, false):
		environment = (node as WorldEnvironment).environment
	var sun_energy := sun.light_energy
	var ambient_energy := environment.ambient_light_energy
	actor = Actor.new()
	actor.configure(1, 0, "Light probe", true)
	world.add_child(actor)
	actor.reset_for_round(Vector3(0, 0.05, -19))
	actor.credits = 5000
	actor.buy_weapon("rifle")
	actor._equip_blend = 0
	actor.apply_cosmetic({})
	_debug_arms()
	var arms_mesh: MeshInstance3D = actor._gun.get_node("arms").find_children("*", "MeshInstance3D", true, false).front()
	for scenario in SCENARIOS:
		if not only_scenarios.is_empty() and not only_scenarios.has(scenario):
			continue
		var setup: Dictionary = SCENARIOS[scenario]
		sun.light_energy = sun_energy * float(setup.sun)
		environment.ambient_light_energy = ambient_energy * float(setup.ambient)
		actor.global_position = setup.at
		actor.yaw = setup.yaw
		actor.rotation.y = setup.yaw
		actor.camera.rotation.x = -0.025
		for pose in POSES:
			if not only_poses.is_empty() and not only_poses.has(pose):
				continue
			_set_pose(POSES[pose])
			var base := await _frame()
			if not output.is_empty():
				base.save_png(output.path_join("%s-%s.png" % [scenario.replace(" ", "-"), pose.replace(" ", "-")]))
			var masks := {}
			var lit_arms: Material = arms_mesh.material_override
			for part in PARTS:
				if part == "gloves" or part == "sleeves":
					continue
				var node := _part_node(part)
				if node == null:
					masks[part] = PackedInt32Array()
					continue
				node.visible = false
				var hidden := await _frame()
				node.visible = true
				masks[part] = _mask(base, hidden)
			# The arms: lit pixels from the base frame, split by authored albedo.
			var arms_node := _part_node("arms")
			arms_node.visible = false
			var without_arms := await _frame()
			arms_node.visible = true
			var arm_pixels := _mask(base, without_arms)
			arms_mesh.material_override = debug_material
			var albedo_frame := await _frame()
			arms_mesh.material_override = lit_arms
			var glove := PackedInt32Array()
			var sleeve := PackedInt32Array()
			var width := base.get_width()
			for index in arm_pixels:
				var albedo := _luma(albedo_frame.get_pixel(index % width, index / width))
				(sleeve if albedo > 62.0 else glove).append(index)
			masks["gloves"] = glove
			masks["sleeves"] = sleeve
			for part in PARTS:
				var s := _stats(base, masks[part])
				if s.n < 48:
					print("LIGHT %s | %s | %s | %s | n=%d (not visible)" % [tag, scenario, pose, part, s.n])
				else:
					print("LIGHT %s | %s | %s | %s | n=%d median=%.1f p10=%.1f p90=%.1f detail=%.2f" % [tag, scenario, pose, part, s.n, s.median, s.p10, s.p90, s.detail])
	sun.light_energy = sun_energy
	environment.ambient_light_energy = ambient_energy
	quit()
