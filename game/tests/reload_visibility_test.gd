extends SceneTree
## What is DRAWN of the reload, frame by frame, measured from real rendered pixels. Needs a native
## display (it renders). For every reload progress it draws the frame as the player sees it and, from the
## same pose, an identification pass in which every part has its own flat colour (black for everything
## else), so the pixels of each fingertip, the thumb, the support hand and each magazine can be counted
## after the depth test: a fingertip hidden behind the magazine, or outside the frame, counts as zero.
##
##   --out=<dir>      save the lit frame and the identification frame of every progress
##   --step=<n>       progress step in hundredths (default 2: 51 frames)
##   --ps=a,b,c       only these progresses (for trying a grasp quickly; the pass criteria need the full run)
##   --view=<name>    sunlit (default), backlight, shade
##   --reduced        reduced motion on
##   --variant=<name> with --reduced: current (default), calm or still (Actor.REDUCED_RELOAD_VARIANTS)
##   --csv=<path>     write the per-frame numbers
##   --report         print every frame's numbers (no thresholds fail the run)
##
## Pass criteria are set by what a viewer needs to see, written before the data, and apply from the start
## to the end (the hand is on the handguard at both ends). They are engineering thresholds for a
## 1280 x 720 frame, not a claim that a person finds the reload legible:
##   - the support hand (glove and forearm) shows at least HAND_MIN pixels
##   - the thumb and at least three of the four fingertips show at least TIP_MIN pixels each
##     while the hand is on a magazine
##   - the magazine the hand holds shows at least MAGAZINE_MIN pixels and is at least 85 % inside the frame
##   - at the hip the arm is out of the picture for at most ARM_OUT_SHARE of the reload and no magazine is drawn without its arm; on the rise from it the hand shows at least RISE_HAND_MIN
##     pixels, with the thumb and RISE_FINGERS fingertips drawn and the magazine in full view
##   - no part of the action that matters (the old magazine leaving the well, the replacement entering it)
##     happens with its magazine out of the frame
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const ViewmodelShading = preload("res://scripts/gameplay/viewmodel_shading.gd")
const RELOAD_SECONDS := 2.25
const HAND_MIN := 10000
const TIP_MIN := 100
const MAGAZINE_MIN := 3000
## At the hip pouch (HIP_OUT to HIP_IN in reload_phases.gd) the hand is below the frame by design. Two rules keep that from reading as
## a hand that vanished: the whole left arm may be out of the picture (under ARM_OUT_PX pixels) for no more than ARM_OUT_SHARE of the
## reload, and a replacement magazine is never drawn (MAGAZINE_MIN pixels or more) with less than ARM_WITH_MAGAZINE pixels of the arm
## that holds it in the frame (no disembodied magazine). The first version asked for 8,000 px of arm at every pose of the hip; an
## independent review found that this kept a huge cut-ended sleeve across the corner of the frame (worse than a hand out of the picture).
const ARM_OUT_PX := 1000
const ARM_OUT_SHARE := 0.10
const ARM_WITH_MAGAZINE := 3000
## Rising from the hip to the lined-up position (HIP_IN to just after ALIGN) the wrist is still crossing the bottom edge: the hand
## shows less than on the handguard, the thumb and two fingertips are drawn, and the magazine it carries is in full view.
const RISE_HAND_MIN := 6000
const RISE_FINGERS := 2
## Half the side, in pixels at 1280 x 720, of the box round the crosshair that is measured for cover (the crosshair is about 24 px).
const CENTRE_BOX := 40
const TIPS := ["L_thumb_3", "L_index_3", "L_middle_3", "L_ring_3", "L_pinky_3"]
const PALETTE := {
	"thumb": Color(1, 0, 0), "index": Color(0, 1, 0), "middle": Color(0, 0, 1),
	"ring": Color(1, 1, 0), "pinky": Color(1, 0, 1),
	"left": Color(0, 1, 1), "right": Color(1, 0.5, 0), "magazine": Color(1, 1, 1), "rifle": Color(0.635, 0.31, 0.0), # what ALBEDO (0.5, 0.25, 0) comes out as in the capture (the output is not a plain copy)
}
const VIEWS := {
	"sunlit": [Vector3(3, 0.05, -12), 0.35],
	"backlight": [Vector3(0, 0.05, -19), PI - 0.08],
	"shade": [Vector3(0, 0.05, 20.5), 0.1],
}
var checks := 0
var failures: Array[String] = []
var output := ""
var csv_path := ""
var view := "sunlit"
var step := 2
var only: Array[float] = []
var reduced := false
var variant := "current"
var report := false
var actor: SBActor
var arena: Node3D
var arms_mesh: MeshInstance3D
var lit_mesh: Mesh
var id_mesh: Mesh
var lit_material: Material
var id_material: ShaderMaterial
var mask_material: ShaderMaterial
var white_material: ShaderMaterial
var rifle_material: ShaderMaterial
var others: Array[MeshInstance3D] = []
var others_material: Dictionary = {}
var rows: Array[String] = []

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

## A copy of the arms' mesh with one flat colour per triangle: the colour of the part its first vertex is
## weighted to most (fingertip bones, the rest of the left arm, the right arm), so nothing blends.
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
			for digit in ["thumb", "index", "middle", "ring", "pinky"]:
				if bone_name == "L_%s_3" % digit:
					return PALETTE[digit]
			return PALETTE["left"] if bone_name.begins_with("L_") else PALETTE["right"]
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

func _set_pose(progress: float) -> void:
	actor._magazine_swap_pending = false
	actor._equip_blend = 0.0
	actor._kick = 0.0
	actor._flash = 0.0
	actor.reload_remaining = 0.0
	actor._reload_clock = 0.0
	actor.tick_visual(0.016)
	if progress >= 0.0:
		actor.reload_remaining = RELOAD_SECONDS * (1.0 - progress)
		actor.tick_visual(0.016)

func _classify(image: Image) -> Dictionary:
	var counts := {"thumb": 0, "index": 0, "middle": 0, "ring": 0, "pinky": 0, "left": 0, "right": 0, "magazine": 0, "rifle": 0, "centre": 0}
	# Anything of the rifle, the arms or a magazine inside the box round the crosshair (the middle of the frame) is counted as it
	# is classified below.
	var cx := image.get_width() / 2
	var cy := image.get_height() / 2
	for y in range(0, image.get_height(), 1):
		for x in range(0, image.get_width(), 1):
			var pixel := image.get_pixel(x, y)
			if pixel.r + pixel.g + pixel.b < 0.2:
				continue
			for key in PALETTE:
				var target: Color = PALETTE[key]
				if absf(pixel.r - target.r) + absf(pixel.g - target.g) + absf(pixel.b - target.b) < 0.18:
					counts[key] += 1
					if absi(x - cx) < CENTRE_BOX and absi(y - cy) < CENTRE_BOX:
						counts["centre"] += 1
					break
	return counts

func _set_identification(on: bool) -> void:
	arms_mesh.mesh = id_mesh if on else lit_mesh
	arms_mesh.material_override = id_material if on else lit_material
	arena.visible = not on
	for node in others:
		if on:
			node.material_override = white_material if node.name.begins_with("magazine") else rifle_material
		else:
			node.material_override = others_material.get(node)

func _run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("A native rendering display is required")
		quit(2)
		return
	var size := Vector2i(1280, 720)
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--out="):
			output = argument.trim_prefix("--out=")
			DirAccess.make_dir_recursive_absolute(output)
		elif argument.begins_with("--csv="):
			csv_path = argument.trim_prefix("--csv=")
		elif argument.begins_with("--view="):
			view = argument.trim_prefix("--view=")
		elif argument.begins_with("--step="):
			step = int(argument.trim_prefix("--step="))
		elif argument.begins_with("--ps="):
			for part in argument.trim_prefix("--ps=").split(","):
				only.append(float(part))
		elif argument.begins_with("--variant="):
			variant = argument.trim_prefix("--variant=")
		elif argument == "--reduced":
			reduced = true
		elif argument == "--report":
			report = true
	root.content_scale_size = size
	root.size = size
	var world := Node3D.new()
	root.add_child(world)
	arena = Arena.new()
	world.add_child(arena)
	actor = Actor.new()
	actor.configure(1, 0, "Visibility test", true)
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
	mask_material = _flat_shader("void fragment() { ALBEDO = vec3(0.0); }\n")
	white_material = _flat_shader("void fragment() { ALBEDO = vec3(1.0); }\n")
	rifle_material = _flat_shader("void fragment() { ALBEDO = vec3(0.5, 0.25, 0.0); }\n")
	for node: MeshInstance3D in actor._gun.find_children("*", "MeshInstance3D", true, false):
		if node != arms_mesh:
			others.append(node)
			others_material[node] = node.material_override
	rows.append("progress,held,thumb_px,index_px,middle_px,ring_px,pinky_px,left_px,right_px,magazine_px,centre_px,rifle_px")
	var progresses: Array[float] = []
	for hundredth in range(0, 101, step):
		progresses.append(float(hundredth) / 100.0)
	if not only.is_empty():
		progresses = only
	var results: Array[Dictionary] = []
	for progress in progresses:
		_set_pose(progress)
		var in_hand: MeshInstance3D = actor._magazine_in_hand
		var held := "-" if in_hand == null else String(in_hand.name)
		var lit := await _frame()
		if not output.is_empty():
			lit.save_png(output.path_join("%s-%03d.png" % [view, roundi(progress * 100.0)]))
		_set_identification(true)
		var ids := await _frame()
		_set_identification(false)
		if not output.is_empty():
			ids.save_png(output.path_join("%s-id-%03d.png" % [view, roundi(progress * 100.0)]))
		var counts := _classify(ids)
		counts["progress"] = progress
		counts["held"] = held
		results.append(counts)
		rows.append("%.2f,%s,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d" % [progress, held, counts.thumb, counts.index, counts.middle, counts.ring, counts.pinky, counts.left, counts.right, counts.magazine, counts.centre, counts.rifle])
	if not csv_path.is_empty():
		var file := FileAccess.open(csv_path, FileAccess.WRITE)
		if file == null:
			push_error("cannot write %s (a relative path is relative to the game/ folder; use an absolute one)" % csv_path)
		else:
			file.store_string("\n".join(rows) + "\n")
	if only.is_empty():
		_evaluate(results)
	print("RELOAD_VISIBILITY_TEST view=%s reduced=%s frames=%d checks=%d failures=%d" % [view, reduced, results.size(), checks, failures.size()])
	quit(1 if not failures.is_empty() else 0)

func _in_hip(p: float) -> bool:
	return p >= SBReloadPhases.HIP_OUT and p <= SBReloadPhases.HIP_IN

func _in_rise(p: float) -> bool:
	return p > SBReloadPhases.HIP_IN and p < SBReloadPhases.ALIGN + 0.025 # the last digit swings round the base after the lined-up position

func _hand_px(r: Dictionary) -> int:
	return r.left + r.thumb + r.index + r.middle + r.ring + r.pinky

func _evaluate(results: Array[Dictionary]) -> void:
	# The hand is on the handguard (and behind the rifle) at 0 and 1; everything between must show it, except
	# at the hip pouch and on the way up from it (named and measured separately below).
	var window: Array[Dictionary] = []
	for r in results:
		if r.progress >= 0.02 and r.progress <= 0.98:
			window.append(r)
	check(window.size() >= 20, "%d frames from just after the start to just before the end" % window.size())
	var worst_hand := 1 << 30
	var worst_hand_at := 0.0
	var hip_frames := 0
	var arm_out_poses := 0
	var step_share := float(step) / 100.0
	var worst_rise_hand := 1 << 30
	var worst_rise_hand_at := 0.0
	var worst_rise_fingers := 4
	var worst_rise_thumb := 1 << 30
	var worst_rise_magazine := 1 << 30
	var rise_frames := 0
	for r in window:
		var p: float = r.progress
		var hand := _hand_px(r)
		if _in_hip(p):
			hip_frames += 1
			if hand < ARM_OUT_PX:
				arm_out_poses += 1
		elif _in_rise(p):
			rise_frames += 1
			if hand < worst_rise_hand:
				worst_rise_hand = hand
				worst_rise_hand_at = p
			var visible := 0
			for finger in ["index", "middle", "ring", "pinky"]:
				if int(r[finger]) >= TIP_MIN:
					visible += 1
			worst_rise_fingers = mini(worst_rise_fingers, visible)
			worst_rise_thumb = mini(worst_rise_thumb, r.thumb)
			worst_rise_magazine = mini(worst_rise_magazine, r.magazine)
		elif hand < worst_hand:
			worst_hand = hand
			worst_hand_at = p
	check(hip_frames >= 6 and rise_frames >= 2, "the hip window has %d frames and the rise from it %d in this run" % [hip_frames, rise_frames])
	check(worst_hand >= HAND_MIN, "the support hand shows at least %d pixels in every frame outside the hip and the rise from it (worst %d at %.2f)" % [HAND_MIN, worst_hand, worst_hand_at])
	check(float(arm_out_poses) * step_share <= ARM_OUT_SHARE, "at the hip the whole left arm is out of the picture (under %d px) for at most %.0f %% of the reload (%d of %d poses, %.0f %%)" % [ARM_OUT_PX, ARM_OUT_SHARE * 100.0, arm_out_poses, hip_frames, float(arm_out_poses) * step_share * 100.0])
	var disembodied := 0
	var disembodied_at := 0.0
	for r in window:
		if r.held == "magazine_spare" and r.magazine >= MAGAZINE_MIN and _hand_px(r) < ARM_WITH_MAGAZINE:
			disembodied += 1
			disembodied_at = r.progress
	check(disembodied == 0, "no replacement magazine is drawn (%d px or more) with less than %d px of its arm in the frame (%d poses; last at %.2f)" % [MAGAZINE_MIN, ARM_WITH_MAGAZINE, disembodied, disembodied_at])
	check(worst_rise_hand >= RISE_HAND_MIN, "on the rise from the hip the hand shows at least %d pixels (worst %d at %.2f)" % [RISE_HAND_MIN, worst_rise_hand, worst_rise_hand_at])
	check(worst_rise_thumb >= TIP_MIN and worst_rise_fingers >= RISE_FINGERS, "and the thumb (%d px) and at least %d fingertips (worst %d) show at least %d pixels" % [worst_rise_thumb, RISE_FINGERS, worst_rise_fingers, TIP_MIN])
	check(worst_rise_magazine >= MAGAZINE_MIN, "and the magazine it carries shows at least %d pixels (worst %d)" % [MAGAZINE_MIN, worst_rise_magazine])
	# While the hand is on a magazine outside the hip and the rise: the thumb and three of the four fingertips are
	# drawn, and so is the magazine.
	var worst_thumb := 1 << 30
	var worst_thumb_at := 0.0
	var worst_fingers := 4
	var worst_fingers_at := 0.0
	var worst_magazine := 1 << 30
	var worst_magazine_at := 0.0
	for r in window:
		if r.held == "-" or _in_hip(r.progress) or _in_rise(r.progress):
			continue
		if r.thumb < worst_thumb:
			worst_thumb = r.thumb
			worst_thumb_at = r.progress
		var visible := 0
		for finger in ["index", "middle", "ring", "pinky"]:
			if int(r[finger]) >= TIP_MIN:
				visible += 1
		if visible < worst_fingers:
			worst_fingers = visible
			worst_fingers_at = r.progress
		if r.magazine < worst_magazine:
			worst_magazine = r.magazine
			worst_magazine_at = r.progress
	var held_old := 0
	var held_new := 0
	for r in window:
		if r.held == "magazine_spare":
			held_new += 1
		elif r.held != "-":
			held_old += 1
	check(held_old >= 4 and held_new >= 4, "frames with a hand on a magazine: %d on the old one and %d on the replacement (each must be measured, or the checks below skip it)" % [held_old, held_new])
	check(worst_thumb >= TIP_MIN, "the thumb's tip shows at least %d pixels whenever the hand is on a magazine (worst %d at %.2f)" % [TIP_MIN, worst_thumb, worst_thumb_at])
	check(worst_fingers >= 3, "at least three of the four fingertips show at least %d pixels whenever the hand is on a magazine (worst %d at %.2f)" % [TIP_MIN, worst_fingers, worst_fingers_at])
	check(worst_magazine >= MAGAZINE_MIN, "the magazine in the hand shows at least %d pixels in every such frame (worst %d at %.2f)" % [MAGAZINE_MIN, worst_magazine, worst_magazine_at])
	# The empty hand's trip to the hip stays in the picture until it dips: the hand shows while no magazine is held.
	var worst_transit := 1 << 30
	var worst_transit_at := 0.0
	var transit_frames := 0
	for r in results:
		if r.progress > SBReloadPhases.DROP and r.progress < SBReloadPhases.HIP_OUT:
			transit_frames += 1
			var hand := _hand_px(r)
			if hand < worst_transit:
				worst_transit = hand
				worst_transit_at = r.progress
	check(transit_frames >= 1 and worst_transit >= HAND_MIN, "while the empty hand goes for the replacement, until it dips, it shows at least %d pixels (%d frames, worst %d at %.2f)" % [HAND_MIN, transit_frames, worst_transit, worst_transit_at])
	# The extraction and the insertion are in the frame: the magazine shows while it leaves and enters the well.
	var worst_action := 1 << 30
	var worst_action_at := 0.0
	for r in results:
		var p: float = r.progress
		if (p >= SBReloadPhases.UNLATCH and p <= SBReloadPhases.CLEAR) or (p >= SBReloadPhases.ALIGN and p <= SBReloadPhases.SEAT):
			if r.magazine < worst_action:
				worst_action = r.magazine
				worst_action_at = p
	check(worst_action >= MAGAZINE_MIN, "the magazine is drawn (at least %d pixels) throughout the extraction and the insertion (worst %d at %.2f)" % [MAGAZINE_MIN, worst_action, worst_action_at])
	# The crosshair is never covered: no pixel of the rifle, the arms or a magazine is inside the box round the middle of the frame
	# in any pose. A design requirement (a player has to see what is under the crosshair during a reload), not a number fitted to the clip.
	var worst_centre := 0
	var worst_centre_at := 0.0
	for r in results:
		if r.centre > worst_centre:
			worst_centre = r.centre
			worst_centre_at = r.progress
	check(worst_centre == 0, "the box round the crosshair (%d px square) is clear of the rifle, the arms and both magazines in every pose (worst %d px at %.2f)" % [CENTRE_BOX * 2, worst_centre, worst_centre_at])
