extends SceneTree
## Diagnoses the Relay AR turning pale during the late part of a reload. For every probed reload tick it measures the median colour
## of the rifle's own visible pixels (the receiver, the handguard and the furniture, found by hiding each part and counting the pixels
## that change) under controlled conditions, together with what the material and the pose were on that tick:
##   base      the scene as the game draws it
##   noreflect the sky's reflection removed (the Environment's reflected light source disabled)
##   nosun     the sun off (ambient and reflection stay)
##   noambient the ambient light off
##   nofill    the viewmodel's fill and rim terms off (viewmodel_floor and viewmodel_rim = 0)
##   matte     every rifle part drawn with one fixed matte grey ShaderMaterial in place of its own (the same projection and fill)
## and a material audit (the resource id of each part's material, the shader parameters that could change, the part's basis
## against the camera). A colour change that follows `noreflect` and the pose, with the material audit constant, is a lighting
## effect of the pose, not a change of the material. Needs a native display. Presentation only.
##   --ticks=a,b,c   reload ticks at 60 Hz (default: a set through 0..135)   --view=sunlit|shade   --csv=<absolute path>
##   --sweep         instead of reload ticks: the idle pose with the animation frozen (no reload, no arms clip) and only the gun node's
##                   roll swept 0 to 25.8 degrees (the reload's own ARMS_RELOAD_ROTATION), then the lift alone, then both
##   --skin          apply a cosmetic finish (patterned) instead of the default unskinned finish
##   --procedural    the procedural rifle (no authored model) instead of the authored Relay AR
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const ViewmodelShading = preload("res://scripts/gameplay/viewmodel_shading.gd")
const RELOAD_SECONDS := 2.25
const TICK := 1.0 / 60.0
const VIEWS := {"sunlit": [Vector3(3, 0.05, -12), 0.35], "shade": [Vector3(0, 0.05, 20.5), 0.1]}
const PARTS := ["receiver", "handguard", "furniture", "arms"]
var world: Node3D
var actor: SBActor
var sun: DirectionalLight3D
var environment: Environment
var matte: ShaderMaterial
var skin := false
var sweep := false
var extra_conditions: PackedStringArray = []
var frames_dir := ""
var assert_mode := false
var series := {}
var failed := false
## A finish that holds through the reload keeps each painted-metal part's median luma within this ratio (max over min) across the
## reload ticks and the roll/lift sweep. Before the fix the receiver ranged 1.52 and the handguard 1.42 (sun), 1.75 and 1.48 (shade); after it
## the worst measured is 1.22. The bound is set from those measurements, not from a visual standard.
const RATIO_MAX := 1.25
## The receiver's blue-to-red balance, (r - b) / luma, may move this far from its value at the first probed tick. The luma bound cannot
## see a hue shift: at 57f6464 the receiver went from (53, 55, 54) at the ready to (74, 82, 83) in the hold, a swing of 0.09 in this number
## (towards blue); the shipped finish moves it by at most 0.034 over the reload in sun (0.015 with a skin). 0.06 is between them, derived
## from that data, not from a visual standard. Only the sunlit view is asserted: in shade the receiver is lit by the sky and its balance
## moves by 0.08 to 0.09 after the fix as well as before it (it turns bluer as it faces the sky), so the number does not separate the
## defect from ordinary lighting there and a bound would be arbitrary.
const CHROMA_SHIFT_MAX := 0.06

func _initialize() -> void:
	_run.call_deferred()

func _frame() -> Image:
	for i in 3:
		await process_frame
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image()

func _node(part: String) -> Node3D:
	if not SBWeaponModel.use_authored:
		return actor._gun # the procedural rifle has no named paint parts: the whole viewmodel stands for all three
	match part:
		"receiver": return actor._gun.get_node("paint_receiver")
		"handguard": return actor._gun.get_node("paint_handguard")
		"arms": return actor._gun.get_node("arms")
		_: return actor._gun.get_node("body")

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

func _median(image: Image, mask: PackedInt32Array) -> Color:
	if mask.size() < 24:
		return Color(-1, -1, -1)
	var width := image.get_width()
	var reds: Array[float] = []
	var greens: Array[float] = []
	var blues: Array[float] = []
	for index in mask:
		var c := image.get_pixel(index % width, index / width)
		reds.append(c.r)
		greens.append(c.g)
		blues.append(c.b)
	reds.sort()
	greens.sort()
	blues.sort()
	var m := mask.size() / 2
	return Color(reds[m], greens[m], blues[m])

func _luma(c: Color) -> float:
	return (0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b) * 255.0

## Animation frozen: the idle pose with only the gun node's roll (radians about the view axis) and lift (metres) set by hand.
func _frozen_pose(roll: float, lift: Vector3) -> void:
	_pose(-1)
	actor._gun.rotation.z += roll
	actor._gun.position += lift

## A copy of the finish with one line of its fragment shader added (an experiment, never shipped): same parameters, same textures.
func _patched(finish: ShaderMaterial, extra_line: String) -> ShaderMaterial:
	var shader := Shader.new()
	if finish.shader.code.contains("AO = occlusion;"):
		shader.code = finish.shader.code.replace("AO = occlusion;", "AO = occlusion;\n " + extra_line)
	else:
		shader.code = finish.shader.code.replace("METALLIC = orm.b;", "METALLIC = orm.b;\n " + extra_line)
	var material := ShaderMaterial.new()
	material.shader = shader
	for uniform in finish.shader.get_shader_uniform_list():
		material.set_shader_parameter(uniform.name, finish.get_shader_parameter(uniform.name))
	return material

## Experiment: the world's ambient light and sky radiance removed from the finish (ambient_light_disabled) and replaced by a fixed
## viewmodel environment: the same ambient colour for the diffuse part, and a reflection with a gentle gradient in view space.
func _studio(finish: ShaderMaterial, strength: float, gradient: float) -> ShaderMaterial:
	var line := "vec3 vm_amb = vec3(0.165, 0.214, 0.256); EMISSION += ALBEDO * (1.0 - METALLIC) * vm_amb * AO;\n"
	line += " vec3 vm_r = reflect(-VIEW, NORMAL); float vm_up = clamp(vm_r.y * 0.5 + 0.5, 0.0, 1.0);\n"
	line += " EMISSION += mix(vec3(0.04), ALBEDO, METALLIC) * vec3(0.62, 0.70, 0.72) * %f * mix(%f, 1.0, vm_up) * (1.0 - 0.5 * ROUGHNESS) * AO;" % [strength, 1.0 - gradient]
	var material := _patched(finish, line)
	material.shader.code = material.shader.code.replace("shader_type spatial;", "shader_type spatial;\nrender_mode ambient_light_disabled;")
	return material

## Experiment: set shader uniforms on every first-person ShaderMaterial of the weapon for one measurement ("u:name=value;name=value"),
## returns what to put back as [material, name, old value].
func _set_uniforms(spec: String) -> Array:
	var restore := []
	var materials: Array[ShaderMaterial] = []
	for node in actor._gun.find_children("*", "MeshInstance3D", true, false):
		var material := (node as MeshInstance3D).material_override as ShaderMaterial
		if material != null and not materials.has(material):
			materials.append(material)
	for pair in spec.trim_prefix("u:").split(";"):
		var kv := pair.split("=")
		if kv.size() != 2:
			continue
		for material in materials:
			if material.shader.get_shader_uniform_list().any(func(u): return u.name == kv[0]):
				restore.append([material, kv[0], material.get_shader_parameter(kv[0])])
				material.set_shader_parameter(kv[0], float(kv[1]))
	return restore

## The rigged arms' shader material (null for the procedural rifle).
func _arms_material() -> ShaderMaterial:
	if not SBWeaponModel.use_authored:
		return null
	var meshes: Array[Node] = (_node("arms") as Node3D).find_children("*", "MeshInstance3D", true, false)
	return (meshes[0] as MeshInstance3D).material_override as ShaderMaterial if not meshes.is_empty() else null

func _pose(tick: int) -> void:
	actor._equip_blend = 0.0
	actor._kick = 0.0
	actor._flash = 0.0
	actor.reload_remaining = 0.0
	actor._reload_clock = 0.0
	actor.tick_visual(TICK)
	if tick >= 0:
		actor.reload_remaining = maxf(RELOAD_SECONDS - float(tick) * TICK, 0.001)
		actor._reload_clock = float(tick) * TICK
		actor.tick_visual(0.0005)

## Reports each part's median colour in the current condition (hide-and-diff per part), as "r g b" 0-255.
func _measure(tag: String = "") -> Dictionary:
	var base := await _frame()
	if not frames_dir.is_empty() and not tag.is_empty():
		base.save_png(frames_dir.path_join(tag + ".png"))
	var out := {}
	for part in PARTS:
		var node := _node(part)
		node.visible = false
		var hidden := await _frame()
		node.visible = true
		out[part] = _median(base, _mask(base, hidden))
	return out

func _material_audit() -> String:
	var bits: PackedStringArray = []
	for part in PARTS:
		var node := _node(part)
		var material: Material = (node as MeshInstance3D).material_override if node is MeshInstance3D else null
		var tag := "%s:%d" % [part, material.get_instance_id() if material != null else 0]
		if material is ShaderMaterial:
			var shader_material := material as ShaderMaterial
			var values: PackedStringArray = []
			for name in ["viewmodel_floor", "viewmodel_rim", "viewmodel_lift", "patterned", "wear", "detail", "albedo_gain"]:
				var value: Variant = shader_material.get_shader_parameter(name)
				values.append("%s=%s" % [name.trim_prefix("viewmodel_"), ("%.2f" % float(value)) if value != null else "-"])
			tag += ":" + "/".join(values)
		bits.append(tag)
	return " ".join(bits)

## Angle of the receiver's up axis from the camera's up, and the pitch of its forward axis, in degrees (how the pose turns the rifle).
func _pose_numbers() -> String:
	var receiver := _node("receiver")
	var camera: Camera3D = actor.camera
	var local := camera.global_transform.basis.inverse() * receiver.global_transform.basis
	var up := local * Vector3.UP
	var forward := local * Vector3.FORWARD
	var roll := rad_to_deg(atan2(up.x, up.y))
	var pitch := rad_to_deg(asin(clampf(forward.y, -1.0, 1.0)))
	return "roll=%.1f pitch=%.1f up_y=%.3f" % [roll, pitch, up.y]

func _run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("A native rendering display is required")
		quit(2)
		return
	var ticks: Array[int] = [0, 40, 80, 100, 110, 114, 116, 118, 120, 122, 124, 126, 128, 130, 132, 134]
	var view := "sunlit"
	var csv := ""
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--ticks="):
			ticks.clear()
			for part in argument.trim_prefix("--ticks=").split(","):
				ticks.append(int(part))
		elif argument.begins_with("--view="):
			view = argument.trim_prefix("--view=")
		elif argument.begins_with("--csv="):
			csv = argument.trim_prefix("--csv=")
		elif argument.begins_with("--frames="):
			frames_dir = argument.trim_prefix("--frames=")
			DirAccess.make_dir_recursive_absolute(frames_dir)
		elif argument == "--assert":
			assert_mode = true
		elif argument == "--skin":
			skin = true
		elif argument == "--sweep":
			sweep = true
		elif argument.begins_with("--conditions="):
			extra_conditions = argument.trim_prefix("--conditions=").split(",")
		elif argument == "--procedural":
			SBWeaponModel.use_authored = false
	root.content_scale_size = Vector2i(1280, 720)
	root.size = Vector2i(1280, 720)
	world = Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	for node in world.find_children("*", "DirectionalLight3D", true, false):
		sun = node
	for node in world.find_children("*", "WorldEnvironment", true, false):
		environment = (node as WorldEnvironment).environment
	actor = Actor.new()
	actor.configure(1, 0, "Discolour probe", true)
	world.add_child(actor)
	actor.reset_for_round(VIEWS[view][0])
	actor.credits = 5000
	actor.buy_weapon("rifle")
	actor._equip_blend = 0
	actor.apply_cosmetic({"collection": "Obsidian", "pattern_seed": 7, "wear": 0.1, "id": "obsidian_test"} if skin else {})
	actor.yaw = VIEWS[view][1]
	actor.rotation.y = VIEWS[view][1]
	actor.camera.rotation.x = -0.025
	var shader := Shader.new()
	shader.code = "shader_type spatial;\n" + ViewmodelShading.UNIFORMS + "void vertex() {\n" + ViewmodelShading.PROJECT + "}\nvoid fragment() { ALBEDO = vec3(0.25); ROUGHNESS = 0.9; METALLIC = 0.0;\n" + ViewmodelShading.FILL + "}\n"
	matte = ShaderMaterial.new()
	matte.shader = shader
	ViewmodelShading.enable(matte)
	var sun_energy := sun.light_energy
	var ambient_energy := environment.ambient_light_energy
	var reflected := environment.reflected_light_source
	var finish: ShaderMaterial = actor._finish
	var rows: PackedStringArray = ["tick,condition,receiver_r,receiver_g,receiver_b,receiver_luma,handguard_luma,furniture_luma,arms_luma,pose,audit"]
	var conditions := ["base", "noreflect", "nosun", "noambient", "nofill", "matte"]
	if not extra_conditions.is_empty():
		conditions = Array(extra_conditions)
	var flat_sky := Sky.new()
	var flat_material := ProceduralSkyMaterial.new()
	for colour_property in ["sky_top_color", "sky_horizon_color", "ground_bottom_color", "ground_horizon_color"]:
		flat_material.set(colour_property, Color(0.50, 0.55, 0.57))
	flat_sky.sky_material = flat_material
	var real_sky := environment.sky
	var ground_skies := {}
	for ground_case in [["groundA", Color(0.40, 0.45, 0.48), 0.15], ["groundB", Color(0.55, 0.60, 0.62), 0.15], ["groundflat", Color(0.764706, 0.8, 0.784314), 0.02], ["groundC", Color(0.30, 0.34, 0.37), 0.30]]:
		var ground_material := (real_sky.sky_material as ProceduralSkyMaterial).duplicate() as ProceduralSkyMaterial
		ground_material.ground_bottom_color = ground_case[1]
		ground_material.ground_curve = ground_case[2]
		var ground_sky := Sky.new()
		ground_sky.sky_material = ground_material
		ground_skies[ground_case[0]] = ground_sky
	var experiments := {
		"rough45": "ROUGHNESS = max(ROUGHNESS, 0.45);", "rough65": "ROUGHNESS = max(ROUGHNESS, 0.65);", "rough70": "ROUGHNESS = max(ROUGHNESS, 0.70);", "rough60": "ROUGHNESS = max(ROUGHNESS, 0.60);", "rough80": "ROUGHNESS = max(ROUGHNESS, 0.80);",
		"metal60": "METALLIC *= 0.60;", "metal30": "METALLIC *= 0.30;",
	}
	var body_original: Material = (_node("furniture") as MeshInstance3D).material_override if SBWeaponModel.use_authored else null
	# The shipped paint materials, kept so every case starts from them: the first-person handguard is its own polymer clone
	# (CosmeticMaterial.apply), and assigning `finish` to both parts would measure a handguard that does not ship.
	var paint_original := {}
	if SBWeaponModel.use_authored:
		for part in ["receiver", "handguard"]:
			paint_original[part] = (_node(part) as MeshInstance3D).material_override
	var cases: Array[Dictionary] = []
	if sweep:
		var full_roll := SBActor.ARMS_RELOAD_ROTATION.z
		for step in 7:
			cases.append({"label": "roll%.1f" % rad_to_deg(-full_roll * float(step) / 6.0), "roll": full_roll * float(step) / 6.0, "lift": Vector3.ZERO})
		cases.append({"label": "lift_only", "roll": 0.0, "lift": SBActor.ARMS_RELOAD_OFFSET})
		cases.append({"label": "roll_and_lift", "roll": full_roll, "lift": SBActor.ARMS_RELOAD_OFFSET})
	else:
		for tick in ticks:
			cases.append({"label": str(tick), "tick": tick})
	for case in cases:
		for condition in conditions:
			if sweep:
				_frozen_pose(case.roll, case.lift)
			else:
				_pose(case.tick)
			sun.light_energy = sun_energy
			environment.ambient_light_energy = ambient_energy
			environment.reflected_light_source = reflected
			finish.set_shader_parameter("viewmodel_floor", ViewmodelShading.METAL_FLOOR)
			finish.set_shader_parameter("viewmodel_rim", ViewmodelShading.RIM)
			if SBWeaponModel.use_authored:
				(_node("furniture") as MeshInstance3D).material_override = body_original
				for part in ["receiver", "handguard"]:
					_node(part).material_override = paint_original[part]
			environment.sky = real_sky
			if condition.begins_with("studio") and SBWeaponModel.use_authored:
				# studio<strength>g<gradient>r<roughness floor>, all in hundredths (the floor defaults to the shipped one)
				var spec: String = condition.trim_prefix("studio")
				var parts: PackedStringArray = spec.split("g")
				var tail: String = parts[1] if parts.size() > 1 else "35"
				var gradient := float(tail.get_slice("r", 0)) / 100.0
				for part in ["receiver", "handguard"]:
					var experiment := _studio(finish, float(parts[0]) / 100.0, gradient)
					if tail.contains("r"):
						experiment.set_shader_parameter("viewmodel_roughness", float(tail.get_slice("r", 1)) / 100.0)
					_node(part).material_override = experiment
			if (condition == "furn80" or condition == "all80") and SBWeaponModel.use_authored:
				var body_node := _node("furniture") as MeshInstance3D
				if body_node.material_override is ShaderMaterial:
					body_node.material_override = _patched(body_node.material_override, "ROUGHNESS = max(ROUGHNESS, 0.80);")
				else:
					print("DISCOLOUR note: furniture material is %s" % body_node.material_override)
				if condition == "all80":
					for part in ["receiver", "handguard"]:
						_node(part).material_override = _patched(finish, "ROUGHNESS = max(ROUGHNESS, 0.80);")
			if experiments.has(condition) and SBWeaponModel.use_authored:
				for part in ["receiver", "handguard"]:
					_node(part).material_override = _patched(finish, experiments[condition])
			if ground_skies.has(condition):
				environment.sky = ground_skies[condition]
			var arms_material := _arms_material()
			var arms_saved := []
			if arms_material != null:
				arms_saved = [arms_material.get_shader_parameter("viewmodel_rim"), arms_material.get_shader_parameter("viewmodel_floor"), arms_material.get_shader_parameter("viewmodel_lift")]
				if condition == "armsnorim" or condition == "armsnofill":
					arms_material.set_shader_parameter("viewmodel_rim", 0.0)
				if condition == "armsnofill":
					arms_material.set_shader_parameter("viewmodel_floor", 0.0)
			match condition:
				"flatsky": environment.sky = flat_sky
				"noreflect": environment.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED
				"nosun": sun.light_energy = 0.0
				"noambient": environment.ambient_light_energy = 0.0
				"nofill":
					finish.set_shader_parameter("viewmodel_floor", 0.0)
					finish.set_shader_parameter("viewmodel_rim", 0.0)
			var uniform_restore := []
			if condition.begins_with("u:"):
				uniform_restore = _set_uniforms(condition)
			var saved := {}
			if condition == "matte" and SBWeaponModel.use_authored:
				for part in PARTS:
					saved[part] = _node(part).material_override
					_node(part).material_override = matte
			var audit := _material_audit()
			var pose := _pose_numbers()
			var m := await _measure("%s_%s" % [case.label, condition])
			for part in saved:
				_node(part).material_override = saved[part]
			for entry in uniform_restore:
				(entry[0] as ShaderMaterial).set_shader_parameter(entry[1], entry[2])
			if arms_material != null:
				arms_material.set_shader_parameter("viewmodel_rim", arms_saved[0])
				arms_material.set_shader_parameter("viewmodel_floor", arms_saved[1])
				arms_material.set_shader_parameter("viewmodel_lift", arms_saved[2])
			var r: Color = m.receiver
			var line := "%s,%s,%.0f,%.0f,%.0f,%.1f,%.1f,%.1f,%.1f,%s,%s" % [case.label, condition, r.r * 255, r.g * 255, r.b * 255, _luma(r), _luma(m.handguard), _luma(m.furniture), _luma(m.arms), pose, audit]
			rows.append(line)
			print("DISCOLOUR ", line)
			if not series.has(condition):
				series[condition] = {"receiver": [], "handguard": [], "chroma": []}
			series[condition].receiver.append(_luma(r))
			series[condition].chroma.append((r.r - r.b) / maxf(_luma(r) / 255.0, 0.001))
			series[condition].handguard.append(_luma(m.handguard))
	sun.light_energy = sun_energy
	environment.ambient_light_energy = ambient_energy
	environment.reflected_light_source = reflected
	environment.sky = real_sky
	if assert_mode:
		var checks := 0
		var failures := 0
		for part in ["receiver", "handguard"]:
			var values: Array = series["base"][part]
			var low := 1e9
			var high := 0.0
			for value in values:
				low = minf(low, value)
				high = maxf(high, value)
			checks += 1
			var ok := high / low <= RATIO_MAX
			failures += 0 if ok else 1
			print("%s the %s median luma stays within %.2f of its lowest through the reload (%.1f to %.1f, ratio %.2f, %d cases)" % ["ok  " if ok else "FAIL", part, RATIO_MAX, low, high, high / low, values.size()])
			if not ok:
				push_error("%s luma ratio %.2f exceeds %.2f" % [part, high / low, RATIO_MAX])
		var chroma: Array = series["base"].chroma
		var shift := 0.0
		for value in chroma:
			shift = maxf(shift, absf(value - chroma[0]))
		var chroma_ok := shift <= CHROMA_SHIFT_MAX or view != "sunlit"
		if view == "sunlit":
			checks += 1
			failures += 0 if chroma_ok else 1
		if view == "sunlit":
			print("%s the receiver's (r - b) / luma stays within %.2f of its first value through the reload (largest shift %.3f, from %.3f, %d cases)" % ["ok  " if chroma_ok else "FAIL", CHROMA_SHIFT_MAX, shift, chroma[0], chroma.size()])
			if not chroma_ok:
				push_error("receiver chroma shift %.3f exceeds %.2f" % [shift, CHROMA_SHIFT_MAX])
		print("RELOAD_DISCOLOUR_TEST view=%s skin=%s authored=%s sweep=%s checks=%d failures=%d" % [view, skin, SBWeaponModel.use_authored, sweep, checks, failures])
		failed = failures > 0
	if not csv.is_empty():
		var file := FileAccess.open(csv, FileAccess.WRITE)
		if file == null:
			push_error("cannot write %s" % csv)
			quit(1)
			return
		file.store_string("\n".join(rows) + "\n")
		file.close()
	quit(1 if failed else 0)
