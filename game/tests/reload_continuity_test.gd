extends SceneTree
## Temporal continuity of the replacement magazine, from real rendered pixels (needs a native display). Every 60 Hz tick of the reload is
## drawn twice: as the player sees it, and as an identification pass in which the replacement magazine, the old magazine, the support
## hand and forearm, the right arm and the rifle each have a flat colour. From the identification pass it measures, per tick, how much of
## the replacement is in the frame, how much of the support hand is, and how many pixels of the replacement are touched by the hand
## (the replacement's pixels with a hand pixel within CONTACT_RADIUS pixels of them). It asserts what a viewer needs to see, written before
## the data and not fitted to it:
##   - the replacement is not in the picture on its own for long: from the first tick it shows at all, the hand touches it, except for a
##     run of at most GRACE_TICKS ticks (0.1 s: shorter than that an object coming in through the frame's edge reads as an entrance,
##     longer it reads as a floating magazine). The magazine's top comes up first and the hand cups its base, so some run is
##     geometry; it is the length of the run that is measured;
##   - the replacement does not appear abruptly: its first visible tick shows under FIRST_MAX_PX pixels (a tenth of it) and it
##     grows by at most GROWTH_MAX_PX pixels from one tick to the next on the way up;
##   - once the hand grips it and until it is seated the hand keeps touching it (HOLD_MIN_PX pixels of contact every tick);
##   - the replacement is never drawn while the hand is not (hand pixels at least ENTER_HAND_MIN at its first visible tick, or two later).
## It is independent of reload_visibility_test.gd (a different question: frame-to-frame continuity), and has its own negative controls
## in scripts/reload_negative_controls.py.
##   --out=<dir>      save the lit frame and the identification frame of every tick
##   --csv=<path>     write the per-tick numbers (an absolute path)
##   --view=<name>    sunlit (default), backlight, shade
##   --reduced        reduced motion on, --variant=<name> with it (current, calm, still)
##   --from=<tick> --to=<tick>   only these ticks (for trying a path quickly; the pass criteria need ticks from 56 to 110 at least)
##   --report         print every check
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const ViewmodelShading = preload("res://scripts/gameplay/viewmodel_shading.gd")
const RELOAD_SECONDS := 2.25
const TICK := 1.0 / 60.0
const CONTACT_RADIUS := 6
## The thresholds are about time and the magazine's size (about 15,000 px when fully in view), written before the clip was tuned; the
## first draft (2 ticks, a sliver of 120 px) was stricter than the geometry allows and was loosened to the 0.1 s perception scale after
## the data showed the best achievable lead is 5 ticks (docs/reports/media/art-v10/continuity). Disclosed there.
const GRACE_TICKS := 6
const FIRST_MAX_PX := 1500
const GROWTH_MAX_PX := 3500
const HOLD_MIN_PX := 150
const ENTER_HAND_MIN := 800
const KEYS := ["new", "old", "hand", "right", "rifle"]
## What each flat ALBEDO comes out as in the capture (the output is not a plain copy of the albedo: 0.5 comes out as 0.635, so 0.6 as 0.76).
const PALETTE := {
	"new": Color(0.76, 0.76, 0.0), "old": Color(1, 1, 1), "hand": Color(0, 1, 1), "right": Color(1, 0.5, 0), "rifle": Color(0.635, 0.31, 0.0),
}
const VIEWS := {
	"sunlit": [Vector3(3, 0.05, -12), 0.35],
	"backlight": [Vector3(0, 0.05, -19), PI - 0.08],
	"shade": [Vector3(0, 0.05, 20.5), 0.1],
}
var checks := 0
var failures: Array[String] = []
var report := false
var output := ""
var csv_path := ""
var view := "sunlit"
var reduced := false
var variant := "current"
var first_tick := 0
var last_tick := -1
var actor: SBActor
var arena: Node3D
var arms_mesh: MeshInstance3D
var lit_mesh: Mesh
var id_mesh: Mesh
var lit_material: Material
var id_material: ShaderMaterial
var flat_materials: Dictionary = {}
var others: Array[MeshInstance3D] = []
var others_material: Dictionary = {}

func _initialize() -> void:
	_run.call_deferred()

func check(condition: bool, message: String) -> void:
	checks += 1
	if report:
		print("%s %s" % ["ok  " if condition else "FAIL", message])
	if not condition:
		failures.append(message)
		push_error(message)

func _frame() -> Image:
	for i in 3:
		await process_frame
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image()

func _flat_shader(body: String) -> ShaderMaterial:
	var shader := Shader.new()
	shader.code = "shader_type spatial;\nrender_mode unshaded;\n" + ViewmodelShading.UNIFORMS + "void vertex() {\n" + ViewmodelShading.PROJECT + "}\n" + body
	var material := ShaderMaterial.new()
	material.shader = shader
	ViewmodelShading.enable(material)
	return material

## A copy of the arms' mesh with one flat colour per triangle: the support arm (every L_ bone) or the right arm.
func _identification_mesh(source: ArrayMesh, skin: Skin, skeleton: Skeleton3D) -> ArrayMesh:
	var made := ArrayMesh.new()
	for surface in source.get_surface_count():
		var arrays := source.surface_get_arrays(surface)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var bones: PackedInt32Array = arrays[Mesh.ARRAY_BONES]
		var weights: PackedFloat32Array = arrays[Mesh.ARRAY_WEIGHTS]
		var per_vertex := bones.size() / vertices.size()
		var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
		var colour_of := func(vertex: int) -> Color:
			var best := 0
			var best_weight := -1.0
			for k in per_vertex:
				if weights[vertex * per_vertex + k] > best_weight:
					best_weight = weights[vertex * per_vertex + k]
					best = bones[vertex * per_vertex + k]
			var bone_name := String(skin.get_bind_name(best))
			if bone_name.is_empty():
				bone_name = String(skeleton.get_bone_name(skin.get_bind_bone(best)))
			return PALETTE["hand"] if bone_name.begins_with("L_") else PALETTE["right"]
		var out_vertices := PackedVector3Array()
		var out_bones := PackedInt32Array()
		var out_weights := PackedFloat32Array()
		var out_colours := PackedColorArray()
		for t in range(0, indices.size(), 3):
			var colour: Color = colour_of.call(indices[t])
			for c in 3:
				var vertex := indices[t + c]
				out_vertices.append(vertices[vertex])
				for k in per_vertex:
					out_bones.append(bones[vertex * per_vertex + k])
					out_weights.append(weights[vertex * per_vertex + k])
				out_colours.append(colour)
		var flat := []
		flat.resize(Mesh.ARRAY_MAX)
		flat[Mesh.ARRAY_VERTEX] = out_vertices
		flat[Mesh.ARRAY_BONES] = out_bones
		flat[Mesh.ARRAY_WEIGHTS] = out_weights
		flat[Mesh.ARRAY_COLOR] = out_colours
		made.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, flat, [], {}, Mesh.ARRAY_FLAG_USE_8_BONE_WEIGHTS if per_vertex == 8 else 0)
	return made

## The reload at a 60 Hz tick, the way tick_visual plays it.
func _set_tick(tick: int) -> void:
	actor._magazine_swap_pending = false
	actor._equip_blend = 0.0
	actor._kick = 0.0
	actor._flash = 0.0
	actor.reload_remaining = 0.0
	actor._reload_clock = 0.0
	actor.tick_visual(TICK)
	actor.reload_remaining = maxf(RELOAD_SECONDS - float(tick) * TICK, 0.001)
	actor._reload_clock = float(tick) * TICK
	actor.tick_visual(0.0005)

func _set_identification(on: bool) -> void:
	arms_mesh.mesh = id_mesh if on else lit_mesh
	arms_mesh.material_override = id_material if on else lit_material
	arena.visible = not on
	for node in others:
		if on:
			node.material_override = flat_materials["new"] if node.name == "magazine_spare" else (flat_materials["old"] if node.name.begins_with("magazine") else flat_materials["rifle"])
		else:
			node.material_override = others_material.get(node)

## Pixel counts by colour, and the replacement's pixels with a hand pixel within CONTACT_RADIUS of them.
func _measure(image: Image) -> Dictionary:
	var counts := {"new": 0, "old": 0, "hand": 0, "right": 0, "rifle": 0}
	var width := image.get_width()
	var height := image.get_height()
	var kind := PackedByteArray()
	kind.resize(width * height)
	for y in height:
		for x in width:
			var pixel := image.get_pixel(x, y)
			if pixel.r + pixel.g + pixel.b < 0.2:
				continue
			for k in KEYS.size():
				var target: Color = PALETTE[KEYS[k]]
				if absf(pixel.r - target.r) + absf(pixel.g - target.g) + absf(pixel.b - target.b) < 0.18:
					counts[KEYS[k]] += 1
					kind[y * width + x] = k + 1
					break
	var contact := 0
	if counts.new > 0 and counts.hand > 0:
		for y in height:
			for x in width:
				if kind[y * width + x] != 1:
					continue
				var touched := false
				for dy in range(-CONTACT_RADIUS, CONTACT_RADIUS + 1, 2):
					for dx in range(-CONTACT_RADIUS, CONTACT_RADIUS + 1, 2):
						var nx := x + dx
						var ny := y + dy
						if nx >= 0 and ny >= 0 and nx < width and ny < height and kind[ny * width + nx] == 3:
							touched = true
							break
					if touched:
						break
				if touched:
					contact += 1
	counts["contact"] = contact
	return counts

func _run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("A native rendering display is required")
		quit(2)
		return
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--out="):
			output = argument.trim_prefix("--out=")
			DirAccess.make_dir_recursive_absolute(output)
		elif argument.begins_with("--csv="):
			csv_path = argument.trim_prefix("--csv=")
		elif argument.begins_with("--view="):
			view = argument.trim_prefix("--view=")
		elif argument.begins_with("--variant="):
			variant = argument.trim_prefix("--variant=")
		elif argument.begins_with("--from="):
			first_tick = int(argument.trim_prefix("--from="))
		elif argument.begins_with("--to="):
			last_tick = int(argument.trim_prefix("--to="))
		elif argument == "--reduced":
			reduced = true
		elif argument == "--report":
			report = true
	var size := Vector2i(1280, 720)
	root.content_scale_size = size
	root.size = size
	var world := Node3D.new()
	root.add_child(world)
	arena = Arena.new()
	world.add_child(arena)
	actor = Actor.new()
	actor.configure(1, 0, "Continuity test", true)
	world.add_child(actor)
	var place: Array = VIEWS[view]
	actor.reset_for_round(place[0])
	actor.credits = 5000
	actor.buy_weapon("rifle")
	actor._equip_blend = 0
	actor.apply_cosmetic({})
	actor.reduced_motion = reduced
	actor.reduced_variant = variant
	actor.global_position = place[0]
	actor.yaw = place[1]
	actor.rotation.y = place[1]
	actor.camera.rotation.x = -0.025
	var arms_node: Node3D = actor._gun.get_node("arms")
	arms_mesh = arms_node.find_children("*", "MeshInstance3D", true, false).front()
	lit_mesh = arms_mesh.mesh
	lit_material = arms_mesh.material_override
	id_mesh = _identification_mesh(arms_mesh.mesh, arms_mesh.skin, actor._arms_skeleton)
	id_material = _flat_shader("void fragment() { ALBEDO = COLOR.rgb; }\n")
	flat_materials["new"] = _flat_shader("void fragment() { ALBEDO = vec3(0.6, 0.6, 0.0); }\n")
	flat_materials["old"] = _flat_shader("void fragment() { ALBEDO = vec3(1.0); }\n")
	flat_materials["rifle"] = _flat_shader("void fragment() { ALBEDO = vec3(0.5, 0.25, 0.0); }\n")
	for node: MeshInstance3D in actor._gun.find_children("*", "MeshInstance3D", true, false):
		if node != arms_mesh:
			others.append(node)
			others_material[node] = node.material_override
	var rows: Array[String] = ["tick,progress,new_px,old_px,hand_px,right_px,contact_px"]
	var results: Array[Dictionary] = []
	var ticks := int(ceil(RELOAD_SECONDS / TICK)) if last_tick < 0 else last_tick
	for tick in range(first_tick, ticks + 1):
		_set_tick(tick)
		var progress := clampf(float(tick) * TICK / RELOAD_SECONDS, 0.0, 1.0)
		if not output.is_empty():
			(await _frame()).save_png(output.path_join("%s-%03d.png" % [view, tick]))
		_set_identification(true)
		var ids := await _frame()
		_set_identification(false)
		if not output.is_empty():
			ids.save_png(output.path_join("%s-id-%03d.png" % [view, tick]))
		var counts := _measure(ids)
		counts["tick"] = tick
		counts["progress"] = progress
		results.append(counts)
		rows.append("%d,%.4f,%d,%d,%d,%d,%d" % [tick, progress, counts.new, counts.old, counts.hand, counts.right, counts.contact])
	if not csv_path.is_empty():
		var file := FileAccess.open(csv_path, FileAccess.WRITE)
		if file == null:
			push_error("cannot write %s (use an absolute path)" % csv_path)
		else:
			file.store_string("\n".join(rows) + "\n")
	_evaluate(results)
	print("RELOAD_CONTINUITY_TEST view=%s reduced=%s ticks=%d checks=%d failures=%d" % [view, reduced, results.size(), checks, failures.size()])
	quit(1 if not failures.is_empty() else 0)

func _evaluate(results: Array[Dictionary]) -> void:
	var first := -1
	for i in results.size():
		if results[i].progress >= SBReloadPhases.ACQUIRE and results[i].new > 0:
			first = i
			break
	check(first >= 0, "the replacement magazine is drawn at some tick after the acquisition")
	if first < 0:
		return
	# up to the tick before the seat (the hand lets go as the replacement seats)
	var seat_tick := results.size() - 1
	for i in results.size():
		if results[i].progress >= SBReloadPhases.SEAT:
			seat_tick = i - 1
			break
	# 1. never without the hand that holds it
	var unsupported := 0
	var worst_run := 0
	var run := 0
	var worst_unsupported_px := 0
	var worst_at := 0
	for i in range(first, seat_tick + 1):
		var r: Dictionary = results[i]
		if r.new >= 25 and r.contact == 0:
			unsupported += 1
			run += 1
			if run > worst_run:
				worst_run = run
				worst_at = r.tick
			worst_unsupported_px = maxi(worst_unsupported_px, int(r.new))
		else:
			run = 0
	check(worst_run <= GRACE_TICKS, "the replacement is not in the frame without the hand touching it for more than %d ticks (%d unsupported ticks, longest run %d ending at tick %d, up to %d px)" % [GRACE_TICKS, unsupported, worst_run, worst_at, worst_unsupported_px])
	# 2. no abrupt appearance
	var first_px: int = results[first].new
	check(first_px < FIRST_MAX_PX, "the replacement's first visible tick (%d) shows %d px (under %d: it enters through the edge)" % [results[first].tick, first_px, FIRST_MAX_PX])
	var worst_growth := 0
	var worst_growth_at := 0
	for i in range(first + 1, seat_tick + 1):
		var growth: int = int(results[i].new) - int(results[i - 1].new)
		if results[i].progress < SBReloadPhases.ALIGN and growth > worst_growth:
			worst_growth = growth
			worst_growth_at = results[i].tick
	check(worst_growth < GROWTH_MAX_PX, "it grows by at most %d px per tick on the way up (worst %d at tick %d)" % [GROWTH_MAX_PX, worst_growth, worst_growth_at])
	# 3. the hand is in the frame when the replacement is
	var later := mini(first + 2, results.size() - 1)
	check(int(results[first].hand) >= ENTER_HAND_MIN or int(results[later].hand) >= ENTER_HAND_MIN, "the hand enters with it: %d px of hand at its first tick, %d two ticks later (at least %d)" % [results[first].hand, results[later].hand, ENTER_HAND_MIN])
	# 4. held until seated
	var settled := first
	while settled < seat_tick and int(results[settled].contact) < HOLD_MIN_PX:
		settled += 1
	var weakest := 1 << 30
	var weakest_at := 0
	for i in range(settled, seat_tick + 1):
		if int(results[i].contact) < weakest:
			weakest = int(results[i].contact)
			weakest_at = results[i].tick
	check(weakest >= HOLD_MIN_PX, "from the tick the hand grips it (%d) until the seat it touches at least %d px of the replacement every tick (weakest %d at tick %d)" % [results[settled].tick, HOLD_MIN_PX, weakest, weakest_at])
