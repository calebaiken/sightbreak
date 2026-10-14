extends SceneTree
## Measures how legible the reload is in the first-person frame, from real rendered
## frames and from the model's own geometry. For each reload progress it reports:
##   onscreen  share of the magazine's projected silhouette inside the frame
##   free      pixels of the magazine with the arms hidden (what it would show if nothing
##             covered it, inside the frame)
##   seen      pixels of the magazine with the arms drawn
##   covered   1 - seen / free: the share of the magazine the arms hide
##   hand      pixels the support hand and forearm cover in the frame
## and, at the ready pose, where the bore points against the crosshair. Needs a native
## display. Presentation only.
##   --out=<dir>    also saves the base frame of every pose
##   --tag=<name>   label printed on every line (before / after)
##   --view=sunlit|backlit|shade
##   --size=WxH     viewport (default 1280x720)
##   --ps=a,b,c     only these reload progresses (default: every 0.02)
##   --gun-offset=x,y,z and --gun-turn=x,y,z (radians)  added to the weapon node after the
##                  pose, to explore reload placements without editing the actor
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const ViewmodelShading = preload("res://scripts/gameplay/viewmodel_shading.gd")
const RELOAD_SECONDS := 2.25
const VIEWS := {
	"sunlit": [Vector3(3, 0.05, -12), 0.35],
	"backlight": [Vector3(0, 0.05, -19), PI - 0.08],
	"shade": [Vector3(0, 0.05, 20.5), 0.1],
}
var output := ""
var tag := "probe"
var view := "sunlit"
var size := Vector2i(1280, 720)
var progresses: Array[float] = []
var extra_offset := Vector3.ZERO
var extra_turn := Vector3.ZERO
var actor: SBActor
var debug_material: ShaderMaterial

func _initialize() -> void:
	_run.call_deferred()

func _frame() -> Image:
	for i in 3:
		await process_frame
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image()

func _changed(a: Image, b: Image) -> PackedInt32Array:
	var mask := PackedInt32Array()
	var width := a.get_width()
	for y in range(0, a.get_height(), 2):
		for x in range(0, width, 2):
			var p := a.get_pixel(x, y)
			var q := b.get_pixel(x, y)
			if absf(p.r - q.r) + absf(p.g - q.g) + absf(p.b - q.b) > 0.03:
				mask.append(y * width + x)
	return mask

func _screen(point: Vector3) -> Vector2:
	var q := actor.camera.global_transform.affine_inverse() * point
	var t := tan(deg_to_rad(ViewmodelShading.FOV) * 0.5)
	var aspect := float(size.x) / float(size.y)
	return Vector2(0.5 + 0.5 * (q.x / -q.z) / (t * aspect), 0.5 - 0.5 * (q.y / -q.z) / t)

## Share of the magazine's projected hull that lies inside the frame.
func _onscreen_share() -> float:
	var vertices: PackedVector3Array = actor._magazine.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
	var points := PackedVector2Array()
	for vertex in vertices:
		points.append(_screen(actor._magazine.global_transform * vertex))
	var hull := Geometry2D.convex_hull(points)
	var area := _area(hull)
	if area <= 0.0:
		return 0.0
	var inside := 0.0
	for clipped in Geometry2D.intersect_polygons(hull, PackedVector2Array([Vector2.ZERO, Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)])):
		inside += _area(clipped)
	return inside / area

func _area(polygon: PackedVector2Array) -> float:
	var sum := 0.0
	for i in polygon.size():
		var a := polygon[i]
		var b := polygon[(i + 1) % polygon.size()]
		sum += a.x * b.y - b.x * a.y
	return absf(sum) * 0.5

## The arms' authored albedo with no lighting, drawn through the viewmodel projection, so a
## covered pixel can be attributed to the glove or to the sleeve (the sleeve is the lighter).
func _debug_arms(arms_mesh: MeshInstance3D) -> void:
	var shader := Shader.new()
	shader.code = "shader_type spatial;\nrender_mode unshaded;\n" + ViewmodelShading.UNIFORMS + "uniform sampler2D albedo_texture : source_color;\nvoid vertex() {\n" + ViewmodelShading.PROJECT + "}\nvoid fragment() { ALBEDO = texture(albedo_texture, UV).rgb; }\n"
	debug_material = ShaderMaterial.new()
	debug_material.shader = shader
	debug_material.set_shader_parameter("albedo_texture", load(SBWeaponModel.RELAY_AR_ARMS_TEXTURES + "_albedo.png"))
	ViewmodelShading.enable(debug_material)

func _luma(c: Color) -> float:
	return (0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b) * 255.0

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
	actor._gun.position += extra_offset
	actor._gun.rotation += extra_turn

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
		elif argument.begins_with("--view="):
			view = argument.trim_prefix("--view=")
		elif argument.begins_with("--gun-offset="):
			var v := argument.trim_prefix("--gun-offset=").split(",")
			extra_offset = Vector3(float(v[0]), float(v[1]), float(v[2]))
		elif argument.begins_with("--gun-turn="):
			var v := argument.trim_prefix("--gun-turn=").split(",")
			extra_turn = Vector3(float(v[0]), float(v[1]), float(v[2]))
		elif argument.begins_with("--ps="):
			for part in argument.trim_prefix("--ps=").split(","):
				progresses.append(float(part))
		elif argument.begins_with("--size="):
			var parts := argument.trim_prefix("--size=").split("x")
			size = Vector2i(int(parts[0]), int(parts[1]))
	root.content_scale_size = size
	root.size = size
	var world := Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	actor = Actor.new()
	actor.configure(1, 0, "Legibility probe", true)
	world.add_child(actor)
	var place: Array = VIEWS[view]
	actor.reset_for_round(place[0])
	actor.credits = 5000
	actor.buy_weapon("rifle")
	actor._equip_blend = 0
	actor.apply_cosmetic({})
	actor.global_position = place[0]
	actor.yaw = place[1]
	actor.rotation.y = place[1]
	actor.camera.rotation.x = -0.025
	var arms_node: Node3D = actor._gun.get_node("arms")
	var hide_arms := func(on: bool): arms_node.visible = not on
	var arms_mesh: MeshInstance3D = arms_node.find_children("*", "MeshInstance3D", true, false).front()
	_debug_arms(arms_mesh)
	# Bore against the crosshair at the ready pose.
	_set_pose(-1.0)
	await _frame()
	var muzzle := _screen(actor._gun.global_transform * (actor._gun.get_node("body") as Node3D).transform * Vector3(0, 0.025, -0.676))
	var behind := _screen(actor._gun.global_transform * (actor._gun.get_node("body") as Node3D).transform * Vector3(0, 0.025, -0.376))
	var direction := (muzzle - behind)
	var at_centre := muzzle.y + (0.5 - muzzle.x) * direction.y / direction.x if absf(direction.x) > 0.0001 else muzzle.y
	var pixels := float(size.y)
	# Where the barrel's direction converges on screen (its vanishing point), against the crosshair.
	var bore: Vector3 = actor.camera.global_transform.basis.inverse() * (actor._gun.global_transform.basis * (actor._gun.get_node("body") as Node3D).transform.basis * Vector3(0, 0, -1))
	var tangent := tan(deg_to_rad(ViewmodelShading.FOV) * 0.5)
	var vanish := Vector2((bore.x / -bore.z) / (tangent * float(size.x) / float(size.y)) * 0.5 * size.x, -(bore.y / -bore.z) / tangent * 0.5 * size.y)
	print("BORE %s | muzzle=(%.0f, %.0f) px from the crosshair | bore line passes %+.0f px below the crosshair at its x | vanishing point (%.0f, %.0f) px from the crosshair (%.1f degrees off)" % [tag, (muzzle.x - 0.5) * size.x, (muzzle.y - 0.5) * size.y, (at_centre - 0.5) * pixels, vanish.x, vanish.y, rad_to_deg(acos(clampf(bore.normalized().dot(Vector3(0, 0, -1)), -1, 1)))])
	if progresses.is_empty():
		for step in range(0, 51):
			progresses.append(step / 50.0)
	for progress in progresses:
		_set_pose(progress)
		var base := await _frame()
		if not output.is_empty():
			base.save_png(output.path_join("%s-%03d.png" % [view, roundi(progress * 100.0)]))
		var onscreen := _onscreen_share()
		hide_arms.call(true)
		var without_arms := await _frame()
		var magazine_node: Node3D = actor._magazine
		magazine_node.visible = false
		var nothing := await _frame()
		magazine_node.visible = true
		hide_arms.call(false)
		magazine_node.visible = false
		var without_magazine := await _frame()
		magazine_node.visible = true
		var free_mask := _changed(without_arms, nothing)
		var seen_mask := _changed(base, without_magazine)
		var free := free_mask.size() * 4
		var seen := seen_mask.size() * 4
		var hand := _changed(base, without_arms).size() * 4
		var covered := 1.0 - float(seen) / float(maxi(free, 1)) if free > 0 else 0.0
		# Attribute the covered pixels (free but not seen) to glove or sleeve by albedo.
		var seen_set := {}
		for index in seen_mask:
			seen_set[index] = true
		var lit_material: Material = arms_mesh.material_override
		arms_mesh.material_override = debug_material
		var albedo := await _frame()
		if not output.is_empty():
			albedo.save_png(output.path_join("%s-albedo-%03d.png" % [view, roundi(progress * 100.0)]))
		arms_mesh.material_override = lit_material
		var width := base.get_width()
		var by_glove := 0
		var by_sleeve := 0
		for index in free_mask:
			if seen_set.has(index):
				continue
			if _luma(albedo.get_pixel(index % width, index / width)) > 62.0:
				by_sleeve += 1
			else:
				by_glove += 1
		print("RELOAD %s | %s | p=%.2f onscreen=%.2f free=%d seen=%d covered=%.2f (glove %.2f, sleeve %.2f) hand=%d" % [tag, view, progress, onscreen, free, seen, covered, float(by_glove) / maxf(free_mask.size(), 1), float(by_sleeve) / maxf(free_mask.size(), 1), hand])
	quit()
