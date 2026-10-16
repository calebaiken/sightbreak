extends SceneTree
## Frame source for the sunlit-metal work (gauntlet track T1). For each (view, reload tick) it saves the frame the game draws and, for
## each named part, the same frame with that part hidden, so tools/art/metal_probe_stats.py can find the part's visible pixels
## (those that differ) and take median colour, spread and highlight statistics with numpy instead of GDScript pixel loops. It poses the
## actor the way reload_discolour_probe.gd does (tick_visual with the reload clock set), so its poses match that probe's. Needs a native
## display. Presentation only.
##   --out=<dir>        where <view>_<tick>[_<part>].png go (required)
##   --views=a,b        sunlit, backlight, shade, dark (default sunlit)
##   --ticks=a,b        reload ticks at 60 Hz, -1 = idle (default 134)
##   --parts=a,b        parts hidden one at a time: receiver, handguard, body (furniture), arms, grip (default receiver,handguard)
##   --skin[=Name]      apply a patterned cosmetic finish (collection Name, default Obsidian) instead of the default unskinned finish
##   --set=n=v;n=v      experiment: shader uniforms set on the receiver, handguard and body materials (floats)
##   --debug=r|n|ndv    draw the receiver, handguard and body unshaded as the studio sees them: r = reflection vector, n = normal, ndv = n.v (colour = value * 0.5 + 0.5)
##   --sun=x            multiply the sun's energy by x (0 = no sun)
##   --size=WxH         viewport (default 1280x720)
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const RELOAD_SECONDS := 2.25
const TICK := 1.0 / 60.0
const VIEWS := {
	"sunlit": [Vector3(3, 0.05, -12), 0.35, 1.0, 1.0],
	"backlight": [Vector3(0, 0.05, -19), PI - 0.08, 1.0, 1.0],
	"shade": [Vector3(0, 0.05, 20.5), 0.1, 1.0, 1.0],
	"dark": [Vector3(0, 0.05, 20.5), 0.1, 0.08, 0.3],
}

func _initialize() -> void:
	_run.call_deferred()

func _frame() -> Image:
	for i in 3:
		await process_frame
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image()

func _pose(actor: SBActor, tick: int) -> void:
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

func _run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("A native rendering display is required")
		quit(2)
		return
	var output := ""
	var views: PackedStringArray = ["sunlit"]
	var ticks: Array[int] = [134]
	var parts: PackedStringArray = ["receiver", "handguard"]
	var skin := false
	var skin_collection := "Obsidian"
	var overrides := ""
	var sun_scale := 1.0
	var debug := ""
	var size := Vector2i(1280, 720)
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--out="):
			output = argument.trim_prefix("--out=")
		elif argument.begins_with("--views="):
			views = argument.trim_prefix("--views=").split(",")
		elif argument.begins_with("--ticks="):
			ticks.clear()
			for item in argument.trim_prefix("--ticks=").split(","):
				ticks.append(int(item))
		elif argument.begins_with("--parts="):
			parts = argument.trim_prefix("--parts=").split(",") if argument.length() > 8 else PackedStringArray()
		elif argument == "--skin" or argument.begins_with("--skin="):
			skin = true
			if argument.begins_with("--skin="):
				skin_collection = argument.trim_prefix("--skin=")
		elif argument.begins_with("--set="):
			overrides = argument.trim_prefix("--set=")
		elif argument.begins_with("--debug="):
			debug = argument.trim_prefix("--debug=")
		elif argument.begins_with("--sun="):
			sun_scale = float(argument.trim_prefix("--sun="))
		elif argument.begins_with("--size="):
			var wh := argument.trim_prefix("--size=").split("x")
			size = Vector2i(int(wh[0]), int(wh[1]))
	if output.is_empty():
		push_error("--out=<dir> is required")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(output)
	root.content_scale_size = size
	root.size = size
	var world := Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	var sun: DirectionalLight3D
	var environment: Environment
	for node in world.find_children("*", "DirectionalLight3D", true, false):
		sun = node
	for node in world.find_children("*", "WorldEnvironment", true, false):
		environment = (node as WorldEnvironment).environment
	var sun_energy := sun.light_energy
	var ambient_energy := environment.ambient_light_energy
	var actor := Actor.new()
	actor.configure(1, 0, "Metal probe", true)
	world.add_child(actor)
	actor.reset_for_round(Vector3(0, 0.05, -19))
	actor.credits = 5000
	actor.buy_weapon("rifle")
	actor._equip_blend = 0
	actor.apply_cosmetic({"collection": skin_collection, "pattern_seed": 7, "wear": 0.1, "id": skin_collection.to_snake_case() + "_test"} if skin else {})
	for i in 6:
		await process_frame
	if not overrides.is_empty():
		for part in ["paint_receiver", "paint_handguard", "body"]:
			var material := (actor._gun.get_node(part) as MeshInstance3D).material_override as ShaderMaterial
			for pair in overrides.split(";"):
				var kv := pair.split("=")
				if kv.size() == 2 and material.shader.get_shader_uniform_list().any(func(u): return u.name == kv[0]):
					material.set_shader_parameter(kv[0], float(kv[1]))
	if not debug.is_empty():
		var shader := Shader.new()
		var output_line: String = {"r": "vec3 r = reflect(-VIEW, n); ALBEDO = r * 0.5 + 0.5;", "n": "ALBEDO = n * 0.5 + 0.5;", "ndv": "ALBEDO = vec3(clamp(dot(n, VIEW), 0.0, 1.0));", "tz": "ALBEDO = vec3(t.z * 0.5 + 0.5, 0.0, 0.0);", "rx": "vec3 r = reflect(-VIEW, n); ALBEDO = vec3(clamp(r.x * 0.5 + 0.5, 0.0, 1.0));", "ry": "vec3 r = reflect(-VIEW, n); ALBEDO = vec3(clamp(r.y * 0.5 + 0.5, 0.0, 1.0));", "rz": "vec3 r = reflect(-VIEW, n); ALBEDO = vec3(clamp(r.z * 0.5 + 0.5, 0.0, 1.0));", "ndv0": "ALBEDO = vec3(clamp(dot(NORMAL, VIEW), 0.0, 1.0));", "view": "ALBEDO = VIEW * 0.5 + 0.5;", "nrm": "ALBEDO = NORMAL * 0.5 + 0.5;", "front": "ALBEDO = vec3(FRONT_FACING ? 1.0 : 0.0, 0.0, 0.0);"}[debug]
		shader.code = "shader_type spatial;\nrender_mode unshaded;\n" + SBViewmodelShading.UNIFORMS + "uniform sampler2D normal_texture : hint_normal;\nvoid vertex() {\n" + SBViewmodelShading.PROJECT + "}\nvoid fragment() {\n vec3 t = texture(normal_texture, UV).rgb * 2.0 - 1.0;\n t.z = sqrt(max(0.0, 1.0 - dot(t.xy, t.xy)));\n vec3 n = normalize(TANGENT * t.x + BINORMAL * t.y + NORMAL * t.z);\n " + output_line + "\n}\n"
		var debug_material := ShaderMaterial.new()
		debug_material.shader = shader
		debug_material.set_shader_parameter("normal_texture", load(SBWeaponModel.RELAY_AR_NORMAL))
		SBViewmodelShading.enable(debug_material)
		for part in ["paint_receiver", "paint_handguard", "body"]:
			(actor._gun.get_node(part) as MeshInstance3D).material_override = debug_material
	var nodes := {
		"receiver": actor._gun.get_node("paint_receiver"),
		"handguard": actor._gun.get_node("paint_handguard"),
		"body": actor._gun.get_node("body"),
		"arms": actor._gun.get_node("arms"),
		"grip": actor._gun.get_node_or_null("grip"),
	}
	for view in views:
		var place: Array = VIEWS[view]
		sun.light_energy = sun_energy * float(place[2]) * sun_scale
		environment.ambient_light_energy = ambient_energy * float(place[3])
		actor.global_position = place[0]
		actor.yaw = place[1]
		actor.rotation.y = place[1]
		actor.camera.rotation.x = -0.025
		for tick in ticks:
			_pose(actor, tick)
			var base := await _frame()
			base.save_png(output.path_join("%s_%03d.png" % [view, tick]))
			for part in parts:
				var node: Node3D = nodes.get(part)
				if node == null:
					continue
				node.visible = false
				var hidden := await _frame()
				node.visible = true
				hidden.save_png(output.path_join("%s_%03d_%s.png" % [view, tick, part]))
	print("VIEWMODEL_METAL_PROBE views=%s ticks=%s parts=%s skin=%s" % [views, ticks, parts, skin])
	quit()
