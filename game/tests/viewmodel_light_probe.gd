extends SceneTree
## Measures what the first-person weapon looks like under different lighting, from real
## rendered frames. For each scenario and pose it renders the scene, hides each part in
## turn and counts the pixels that change: those are the part's visible pixels, whatever
## covers it. It reports their luma (0-255, sRGB-encoded) as median, 10th and 90th
## percentile and local detail, so "the magazine is near black" and "the fill kept
## the receiver's value" are numbers. Needs a native display. Presentation only.
##   --out=<dir>   also saves the base frame of every case
##   --tag=<name>  label printed on every line (before / after)
##   --assert  a test: separation bounds over the lightings and poses measured (see _assert_separation); exit 1 on a failure
##   --arms-specular=x  set the arms' dielectric specular (viewmodel_specular) for the run   --arms-rim=x  likewise the rim
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
const POSES := {"ready": -1.0, "grab": 0.15, "hip": 0.47, "mid reload": 0.5, "seat": 0.84}
## The "hip" pose is the hip retrieval: the support arm is below the rifle and its forearm's underside is what is in the frame.
const HIP_SLEEVE_MIN := {"sun": 55.0, "backlight": 45.0, "shade": 38.0, "dark interior": 38.0}
const PARTS := ["magazine", "receiver", "handguard", "furniture", "grip", "gloves", "sleeves"]
var output := ""
var tag := "probe"
var only_scenarios: PackedStringArray = []
var arms_specular := -1.0
var arms_rim := -1.0
var arms_lift := -1.0
var arms_floor := -1.0
var finish_floor := -1.0
var assert_mode := false
var medians := {}
var finish_lift := -1.0
var grip_rim := -1.0
var grip_lift := -1.0
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
		elif argument.begins_with("--arms-specular="):
			arms_specular = float(argument.trim_prefix("--arms-specular="))
		elif argument.begins_with("--arms-rim="):
			arms_rim = float(argument.trim_prefix("--arms-rim="))
		elif argument == "--assert":
			assert_mode = true
		elif argument.begins_with("--finish-floor="):
			finish_floor = float(argument.trim_prefix("--finish-floor="))
		elif argument.begins_with("--finish-lift="):
			finish_lift = float(argument.trim_prefix("--finish-lift="))
		elif argument.begins_with("--arms-floor="):
			arms_floor = float(argument.trim_prefix("--arms-floor="))
		elif argument.begins_with("--arms-lift="):
			arms_lift = float(argument.trim_prefix("--arms-lift="))
		elif argument.begins_with("--grip-rim="):
			grip_rim = float(argument.trim_prefix("--grip-rim="))
		elif argument.begins_with("--grip-lift="):
			grip_lift = float(argument.trim_prefix("--grip-lift="))
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
	if arms_specular >= 0.0:
		(arms_mesh.material_override as ShaderMaterial).set_shader_parameter("viewmodel_specular", arms_specular)
	if arms_rim >= 0.0:
		(arms_mesh.material_override as ShaderMaterial).set_shader_parameter("viewmodel_rim", arms_rim)
	if finish_floor >= 0.0:
		actor._finish.set_shader_parameter("viewmodel_floor", finish_floor)
	if finish_lift >= 0.0:
		actor._finish.set_shader_parameter("viewmodel_lift", finish_lift)
	if arms_floor >= 0.0:
		(arms_mesh.material_override as ShaderMaterial).set_shader_parameter("viewmodel_floor", arms_floor)
	if arms_lift >= 0.0:
		(arms_mesh.material_override as ShaderMaterial).set_shader_parameter("viewmodel_lift", arms_lift)
	var grip_node: MeshInstance3D = actor._gun.get_node_or_null("grip")
	if grip_node != null and grip_node.material_override is ShaderMaterial:
		if grip_rim >= 0.0:
			(grip_node.material_override as ShaderMaterial).set_shader_parameter("viewmodel_rim", grip_rim)
		if grip_lift >= 0.0:
			(grip_node.material_override as ShaderMaterial).set_shader_parameter("viewmodel_lift", grip_lift)
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
				if s.n >= 48:
					if not medians.has(scenario + "|" + pose):
						medians[scenario + "|" + pose] = {}
					medians[scenario + "|" + pose][part] = s.median
				if s.n < 48:
					print("LIGHT %s | %s | %s | %s | n=%d (not visible)" % [tag, scenario, pose, part, s.n])
				else:
					print("LIGHT %s | %s | %s | %s | n=%d median=%.1f p10=%.1f p90=%.1f detail=%.2f" % [tag, scenario, pose, part, s.n, s.median, s.p10, s.p90, s.detail])
	sun.light_energy = sun_energy
	environment.ambient_light_energy = ambient_energy
	if assert_mode:
		quit(_assert_separation())
		return
	quit()

## Bounds on how the parts separate (median luma, 0 to 255). They are set from the measurements of this round (the values before it
## are in docs/reports/media/art-v8/reload-hip-retrieval/logs/light-probe-after.txt, the values after in art-v9/materials/logs),
## so each is a regression guard around a measured state, not a visual standard:
##   grip / receiver <= 0.85   the grip is distinctly darker than the receiver in every lighting and pose (before: 1.00 in sun at ready,
##                             0.94 in shade at ready; after: 0.56 to 0.76)
##   gloves / sleeves <= 0.78 in sun   the gloves are not a pale veil beside the sleeve (before: 0.79 to 0.81; after: 0.73 to 0.76)
##   sleeves at the hip retrieval pose >= 55 sun, 45 backlight, 38 shade and dark interior   the support forearm's underside is not a black wedge
##   receiver and handguard >= 22 in the dark interior   the rifle does not dissolve into it (before the fill: 17 and 18; after: 25 and 28)
func _assert_separation() -> int:
	var checks := 0
	var failures := 0
	for key in medians:
		var v: Dictionary = medians[key]
		var parts := str(key).split("|")
		if v.has("grip") and v.has("receiver"):
			var ratio: float = v.grip / v.receiver
			checks += 1
			var ok := ratio <= 0.85
			failures += 0 if ok else 1
			print("%s %s: grip %.1f / receiver %.1f = %.2f (at most 0.85)" % ["ok  " if ok else "FAIL", key, v.grip, v.receiver, ratio])
		if parts[1] == "hip" and v.has("sleeves"):
			# The support forearm's underside in the hip retrieval was a near-black wedge. Empirical bounds, set after seeing the
			# measurements, midway between the values without and with the ground bounce (art-v10/materials): sun 48.0 / 61.9,
			# backlight 37.2 / 52.6, shade and dark interior 33.9 / 42.2.
			var least: float = HIP_SLEEVE_MIN[parts[0]]
			checks += 1
			var ok_hip: bool = v.sleeves >= least
			failures += 0 if ok_hip else 1
			print("%s %s: sleeves %.1f at the hip retrieval (at least %.0f)" % ["ok  " if ok_hip else "FAIL", key, v.sleeves, least])
		if parts[0] == "sun" and parts[1] != "hip" and parts[1] != "mid reload" and v.has("gloves") and v.has("sleeves"):
			var ratio: float = v.gloves / v.sleeves
			checks += 1
			var ok := ratio <= 0.78
			failures += 0 if ok else 1
			print("%s %s: gloves %.1f / sleeves %.1f = %.2f (at most 0.78)" % ["ok  " if ok else "FAIL", key, v.gloves, v.sleeves, ratio])
		if parts[0] == "dark interior" and v.has("receiver") and v.has("handguard"):
			checks += 1
			var ok: bool = v.receiver >= 22.0 and v.handguard >= 22.0
			failures += 0 if ok else 1
			print("%s %s: receiver %.1f and handguard %.1f in the dark interior (at least 22)" % ["ok  " if ok else "FAIL", key, v.receiver, v.handguard])
	print("VIEWMODEL_LIGHT_TEST checks=%d failures=%d" % [checks, failures])
	for key in medians:
		pass
	if failures > 0:
		push_error("%d separation checks failed" % failures)
	return 1 if failures > 0 else 0
