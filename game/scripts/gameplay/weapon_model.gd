class_name SBWeaponModel
extends RefCounted
## Original, reusable in-engine geometry. All dimensions are meters; barrel faces -Z.
## No collision, gameplay state, textures, lights or animation ownership.
var _gun: Node3D
var _paint_parts: Array[MeshInstance3D] = []
var _magazine: MeshInstance3D
var _magazine_rest := Vector3.ZERO
var _muzzle: MeshInstance3D
var _gun_color := Color("59616a")
var weapon_id := "rifle"
var _hands := false
var _materials: Dictionary = {}
var _authored: Array[MeshInstance3D] = []
var _ejection := Vector3.INF
var _pivot := Vector3.ZERO
var _arms_placement := Transform3D()
var _rigged := false

## Authored first-person rifle built by tools/art (Blender, original geometry). Units
## are meters: receiver rear at the origin, bore at +Y 0.025, barrel along -Z. The
## procedural rifle remains the fallback when the asset is missing.
const RELAY_AR := "res://assets/weapons/relay_ar/relay_ar.glb"
const RELAY_AR_MATERIAL := "res://assets/weapons/relay_ar/relay_ar_body.tres"
const RELAY_AR_ORM := "res://assets/weapons/relay_ar/relay_ar_orm.png"
const RELAY_AR_NORMAL := "res://assets/weapons/relay_ar/relay_ar_normal.png"
const RELAY_AR_ALBEDO := "res://assets/weapons/relay_ar/relay_ar_albedo.png"
## Gloved hands and sleeves posed on this rifle (tools/art/relay_ar_hands.py); static,
## the fallback when the rigged arms are absent.
const RELAY_AR_HANDS := "res://assets/weapons/relay_ar/relay_ar_hands.glb"
const RELAY_AR_HANDS_MATERIAL := "res://assets/weapons/relay_ar/relay_ar_hands.tres"
## Rigged arms (tools/art/arms_build.py): both arms in one skinned mesh on a 34-bone
## skeleton, posed on this rifle in their bind pose, with a one-second "reload" clip
## that the actor seeks by reload progress. Same space as the rifle GLB.
const RELAY_AR_ARMS := "res://assets/weapons/relay_ar/relay_ar_arms.glb"
const RELAY_AR_TEXTURES := "res://assets/weapons/relay_ar/relay_ar"
const RELAY_AR_ARMS_TEXTURES := "res://assets/weapons/relay_ar/relay_ar_arms"
const ViewmodelShading = preload("res://scripts/gameplay/viewmodel_shading.gd")
## Viewmodel placement inside the camera-attached weapon node (presentation only).
## The weapon node rests 0.235 m right, 0.235 m down and 0.42 m ahead of the eye.
## These values come from tools/art/viewmodel_fit.py: the muzzle near the crosshair,
## the reflex sight right of centre, the pistol grip at the lower right and the stock
## behind the camera, with about 6 degrees of roll so the left receiver face reads.
static var relay_ar_scale := 1.0
static var relay_ar_rotation := Vector3(-0.020, 0.174, -0.04)
static var relay_ar_offset := Vector3(0.065, 0.074, -0.005)
## Inspection and other hand-less builds keep the rifle upright, centred in the
## existing studio framing (the studio's yaw brings the muzzle end nearer the camera).
const RELAY_AR_UPRIGHT_OFFSET := Vector3(0, -0.015, -0.07)
## Balance point between the two hands, in the GLB's axes (barrel along -Z). First-person
## builds move the weapon node's origin here, so reload and equip tilts turn the rifle
## about its middle instead of sweeping the stock through the view. The rest pose is
## unchanged: the actor adds the pivot to the node's rest position and the models are
## offset by the same amount.
const RELAY_AR_PIVOT := Vector3(0.0, 0.0, -0.19)
## Captures switch these off for before/after comparisons; gameplay never reads them.
static var use_authored := true
static var use_rigged_arms := true

# One packed model per weapon/hands variant. Instances share every mesh and
# material, so an equip costs node instantiation instead of geometry building.
static var _packed: Dictionary = {}

static func build(parent: Node3D, id: String, hands: bool = false) -> Dictionary:
	for child in parent.get_children():
		parent.remove_child(child)
		child.queue_free()
	var key := "%s|%s|%s|%s|%s|%s|%s" % [id, hands, use_authored, use_rigged_arms, relay_ar_scale, relay_ar_offset, relay_ar_rotation]
	if not _packed.has(key):
		_packed[key] = _pack(id, hands)
	var instance: Node = (_packed[key] as PackedScene).instantiate()
	var result := {"paint": [] as Array[MeshInstance3D], "magazine": null, "muzzle": null, "ejection": instance.get_meta("ejection", Vector3.INF), "pivot": instance.get_meta("pivot", Vector3.ZERO),
		"viewmodel": instance.get_meta("viewmodel", false), "arms": null, "arms_player": null, "arms_skeleton": null}
	for child in instance.get_children():
		instance.remove_child(child)
		release_owner(child)
		parent.add_child(child)
		if child.get_meta("weapon_paint", false):
			result.paint.append(child)
		match str(child.get_meta("weapon_role", "")):
			"magazine": result.magazine = child
			"muzzle": result.muzzle = child
	if instance.has_meta("arms_placement"):
		_add_arms(parent, instance.get_meta("arms_placement"), result)
	instance.free()
	return result

## The rigged arms are instanced per build rather than packed, so their skeleton and
## animation player stay intact; the GLB's packed scene is cached by the loader.
static func _add_arms(parent: Node3D, placement: Transform3D, result: Dictionary) -> void:
	var arms: Node3D = (load(RELAY_AR_ARMS) as PackedScene).instantiate()
	arms.name = "arms"
	arms.transform = placement
	arms.set_meta("weapon_role", "arms")
	var material := ViewmodelShading.surface(RELAY_AR_ARMS_TEXTURES)
	for mesh: MeshInstance3D in arms.find_children("*", "MeshInstance3D", true, false):
		mesh.material_override = material
		mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(arms)
	result.arms = arms
	result.arms_skeleton = arms.find_children("*", "Skeleton3D", true, false).front()
	var players := arms.find_children("*", "AnimationPlayer", true, false)
	if not players.is_empty():
		var player: AnimationPlayer = players.front()
		player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
		player.assigned_animation = "reload"
		player.seek(0.0, true)
		result.arms_player = player

static func _pack(id: String, hands: bool) -> PackedScene:
	var root := Node3D.new()
	var model := SBWeaponModel.new()
	model._gun = root
	model.weapon_id = id
	model._hands = hands
	model._build_gun()
	model._batch_magazine()
	model._batch_static_parts()
	for part in model._paint_parts:
		part.set_meta("weapon_paint", true)
	if model._magazine != null:
		model._magazine.set_meta("weapon_role", "magazine")
	if not model._authored.is_empty():
		# Baked occlusion and surface normals survive any cosmetic finish.
		for part in model._paint_parts:
			part.set_meta("detail_orm", load(RELAY_AR_ORM))
			part.set_meta("detail_normal", load(RELAY_AR_NORMAL))
			part.set_meta("detail_albedo", load(RELAY_AR_ALBEDO))
	model._muzzle.set_meta("weapon_role", "muzzle")
	if model._ejection != Vector3.INF:
		root.set_meta("ejection", model._ejection)
	if model._pivot != Vector3.ZERO:
		root.set_meta("pivot", model._pivot)
	if model._rigged:
		root.set_meta("arms_placement", model._arms_placement)
	if model._hands and not model._authored.is_empty():
		root.set_meta("viewmodel", true)
	return pack_children(root)

## Packs a procedurally built hierarchy, then frees the source nodes.
static func pack_children(root: Node) -> PackedScene:
	_own(root, root)
	var packed := PackedScene.new()
	packed.pack(root)
	root.free()
	return packed

static func _own(node: Node, owner: Node) -> void:
	for child in node.get_children():
		child.owner = owner
		_own(child, owner)

static func release_owner(node: Node) -> void:
	node.owner = null
	for child in node.get_children():
		release_owner(child)

func _part(parent: Node3D, at: Vector3, dimensions: Vector3, color: Color) -> MeshInstance3D:
	var visual := MeshInstance3D.new()
	var shape := BoxMesh.new()
	shape.size = dimensions
	visual.mesh = shape
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = 0.65
	visual.material_override = material
	parent.add_child(visual)
	visual.position = at
	return visual

func _chamfer(at: Vector3, size: Vector3, tint: Color, painted: bool = false) -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	mesh.mesh = bevel_mesh(size)
	var material := _material(tint, 0.48, 0.65)
	mesh.material_override = material
	_gun.add_child(mesh)
	mesh.position = at
	if painted:
		_paint_parts.append(mesh)
	return mesh

static func bevel_mesh(size: Vector3) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.set_smooth_group(-1)
	var x := size.x * 0.5
	var y := size.y * 0.5
	var z := size.z * 0.5
	var b := minf(x, y) * 0.32
	var ring := [Vector2(-x + b, -y), Vector2(x - b, -y), Vector2(x, -y + b), Vector2(x, y - b), Vector2(x - b, y), Vector2(-x + b, y), Vector2(-x, y - b), Vector2(-x, -y + b)]
	for i in range(8):
		var a: Vector2 = ring[i]
		var c: Vector2 = ring[(i + 1) % 8]
		var front_a := Vector3(a.x, a.y, -z)
		var front_b := Vector3(c.x, c.y, -z)
		var back_a := Vector3(a.x, a.y, z)
		var back_b := Vector3(c.x, c.y, z)
		var vertices := [front_a, front_b, back_b, front_a, back_b, back_a, Vector3(0, 0, -z), front_b, front_a, Vector3(0, 0, z), back_a, back_b]
		# Godot front faces use clockwise winding.
		for triangle in range(0, vertices.size(), 3):
			st.add_vertex(vertices[triangle])
			st.add_vertex(vertices[triangle + 2])
			st.add_vertex(vertices[triangle + 1])
	st.generate_normals()
	st.index()
	return st.commit()

func _material(tint: Color, roughness: float, metallic: float) -> StandardMaterial3D:
	var key := "%s/%.2f/%.2f" % [tint.to_html(), roughness, metallic]
	if not _materials.has(key):
		var material := StandardMaterial3D.new()
		material.albedo_color = tint
		material.roughness = roughness
		material.metallic = metallic
		_materials[key] = material
	return _materials[key]

func _sleeve(from: Vector3, to: Vector3, tint: Color) -> void:
	# Tapered twelve-sided forearm and a distinct cuff avoid the slab-arm silhouette.
	var sleeve := MeshInstance3D.new()
	var mesh := CylinderMesh.new()
	mesh.top_radius = 0.048
	mesh.bottom_radius = 0.069
	mesh.height = from.distance_to(to)
	mesh.radial_segments = 12
	sleeve.mesh = mesh
	sleeve.material_override = _material(tint, 0.93, 0.0)
	_gun.add_child(sleeve)
	sleeve.position = (from + to) * 0.5
	sleeve.quaternion = Quaternion(Vector3.UP, (to - from).normalized())
	var cuff := _chamfer(to, Vector3(0.10, 0.045, 0.10), Color("19272d"))
	cuff.quaternion = sleeve.quaternion
	cuff.material_override = _material(Color("19272d"), 0.95, 0)
	var seam_at := from.lerp(to, 0.42) + Vector3(-0.034, 0.038, 0)
	var seam := _chamfer(seam_at, Vector3(0.008, 0.008, from.distance_to(to) * 0.48), tint.lightened(0.06))
	seam.quaternion = Quaternion(Vector3.FORWARD, (to - from).normalized())
	seam.material_override = _material(tint.lightened(0.06), 0.95, 0)
	var panel := _chamfer(from.lerp(to, 0.65) + Vector3(0, 0.035, 0), Vector3(0.063, 0.02, 0.11), tint.darkened(0.18))
	panel.quaternion = seam.quaternion
	panel.material_override = _material(tint.darkened(0.18), 0.96, 0)

func _glove(at: Vector3, support: bool = false) -> void:
	var tint := Color("3c463f")
	var palm := _chamfer(at, Vector3(0.088, 0.08, 0.115), tint)
	palm.material_override = _material(tint, 0.89, 0)
	for i in range(4):
		var finger := _chamfer(at + Vector3(0.036, 0.023 - i * 0.016, -0.035), Vector3(0.029, 0.014, 0.072), tint.lightened(0.035))
		finger.material_override = _material(tint.lightened(0.035), 0.9, 0)
		finger.rotation.y = -0.14 if support else 0.1
	var thumb := _chamfer(at + Vector3(-0.039, 0.025, -0.022), Vector3(0.025, 0.036, 0.075), tint)
	thumb.rotation.x = -0.35
	thumb.material_override = _material(tint, 0.89, 0)
	var knuckle := _chamfer(at + Vector3(0, 0.018, 0.048), Vector3(0.069, 0.033, 0.018), Color("24312e"))
	knuckle.material_override = _material(Color("24312e"), 0.85, 0)

func _batch_magazine() -> void:
	if _magazine == null or _magazine.get_child_count() == 0 or _authored.has(_magazine):
		return
	var builder := SurfaceTool.new()
	builder.begin(Mesh.PRIMITIVE_TRIANGLES)
	var material: Material
	for rib in _magazine.get_children():
		builder.append_from(rib.mesh, 0, rib.transform)
		material = rib.material_override
		_magazine.remove_child(rib)
		rib.free()
	var detail := MeshInstance3D.new()
	detail.mesh = builder.commit()
	detail.material_override = material
	detail.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_magazine.add_child(detail)

func _batch_static_parts() -> void:
	# One mesh per shared material/paint role. Magazine and flash retain their own
	# transforms; fixed attachments do not each consume a mobile draw call.
	var groups: Dictionary = {}
	for node in _gun.get_children():
		if not node is MeshInstance3D or node == _magazine or node == _muzzle or _authored.has(node):
			continue
		var painted := _paint_parts.has(node)
		var key := "paint" if painted else ("fabric" if node.material_override.roughness > 0.8 else "metal")
		if not groups.has(key):
			var builder := SurfaceTool.new()
			builder.begin(Mesh.PRIMITIVE_TRIANGLES)
			var material: Material = node.material_override
			if not painted:
				var merged_material := StandardMaterial3D.new()
				merged_material.vertex_color_use_as_albedo = true
				merged_material.vertex_color_is_srgb = true
				merged_material.roughness = 0.94 if key == "fabric" else 0.48
				merged_material.metallic = 0.0 if key == "fabric" else 0.65
				material = merged_material
			groups[key] = {"surface": builder, "material": material, "painted": painted}
		if painted:
			groups[key].surface.append_from(node.mesh, 0, node.transform)
		else:
			var source := MeshDataTool.new()
			var arrays := ArrayMesh.new()
			arrays.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, node.mesh.surface_get_arrays(0))
			source.create_from_surface(arrays, 0)
			for face in range(source.get_face_count()):
				for corner in range(3):
					var index := source.get_face_vertex(face, corner)
					groups[key].surface.set_color(node.material_override.albedo_color)
					groups[key].surface.set_normal((node.transform.basis.inverse().transposed() * source.get_vertex_normal(index)).normalized())
					groups[key].surface.add_vertex(node.transform * source.get_vertex(index))
		_paint_parts.erase(node)
		_gun.remove_child(node)
		node.free()
	for group in groups.values():
		var merged := MeshInstance3D.new()
		merged.mesh = group.surface.commit()
		merged.material_override = group.material
		merged.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_gun.add_child(merged)
		if group.painted:
			_paint_parts.append(merged)

func _barrel(at: Vector3, length: float, radius: float, tint: Color) -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	var shape := CylinderMesh.new()
	shape.top_radius = radius
	shape.bottom_radius = radius
	shape.height = length
	shape.radial_segments = 12
	mesh.mesh = shape
	var material := _material(tint, 0.38, 0.8)
	mesh.material_override = material
	_gun.add_child(mesh)
	mesh.position = at
	mesh.rotation.x = PI * 0.5
	return mesh

func _build_gun() -> void:
	for child in _gun.get_children():
		_gun.remove_child(child)
		child.queue_free()
	_paint_parts.clear()
	_magazine = null

	var metal := Color("10161c")
	var edge := Color("25303a")
	var glove := Color("343c39")
	var muzzle_z := -0.35
	var muzzle_at := Vector3.INF
	if weapon_id == "rifle" and use_authored and ResourceLoader.exists(RELAY_AR):
		muzzle_at = _build_authored_rifle()
	elif weapon_id == "sidearm":
		_chamfer(Vector3(0, 0.022, -0.16), Vector3(0.085, 0.075, 0.31), edge, true)
		_chamfer(Vector3(0, -0.023, -0.12), Vector3(0.074, 0.052, 0.26), metal)
		var grip := _chamfer(Vector3(0, -0.105, -0.017), Vector3(0.066, 0.16, 0.09), metal)
		grip.rotation.x = -0.23
		_barrel(Vector3(0, 0.019, -0.32), 0.07, 0.022, metal)
		_barrel(Vector3(0, 0.019, -0.357), 0.005, 0.014, Color("03070b"))
		# A real open rear notch, fine front sight, ejection port, slide serrations.
		for x in [-0.026, 0.026]:
			_chamfer(Vector3(x, 0.074, -0.025), Vector3(0.018, 0.029, 0.025), metal)
		_chamfer(Vector3(0, 0.072, -0.279), Vector3(0.014, 0.020, 0.021), Color("96b2a0"))
		_chamfer(Vector3(0.043, 0.03, -0.13), Vector3(0.003, 0.028, 0.061), Color("060c10"))
		for i in range(5):
			_chamfer(Vector3(0.044, 0.017, 0.0 - i * 0.012), Vector3(0.006, 0.057, 0.004), metal)
		# Trigger guard encloses open air rather than a solid rectangular block.
		_chamfer(Vector3(0, -0.073, -0.107), Vector3(0.046, 0.009, 0.080), metal)
		_chamfer(Vector3(0, -0.046, -0.147), Vector3(0.046, 0.060, 0.009), metal)
		_chamfer(Vector3(0, -0.049, -0.102), Vector3(0.009, 0.031, 0.008), edge)
		if _hands:
			_glove(Vector3(0.015, -0.132, 0.037))
			_sleeve(Vector3(0.11, -0.37, 0.43), Vector3(0.022, -0.16, 0.085), Color("28353c"))
			var support := _chamfer(Vector3(-0.055, -0.143, 0.065), Vector3(0.09, 0.09, 0.13), glove)
			support.rotation.z = 0.24
			for i in range(3):
				_chamfer(Vector3(0.059, -0.12 + i * 0.018, -0.005), Vector3(0.016, 0.014, 0.076), glove.lightened(0.045))
	else:
		_chamfer(Vector3(0, 0, -0.15), Vector3(0.088, 0.104, 0.30), edge, true)
		_chamfer(Vector3(0, 0.007, -0.405), Vector3(0.082, 0.088, 0.23), edge, true)
		_barrel(Vector3(0, 0.025, -0.59), 0.22, 0.023, metal)
		_barrel(Vector3(0, 0.025, -0.72), 0.07, 0.031, edge)
		_barrel(Vector3(0, 0.025, -0.758), 0.005, 0.021, Color("03070b"))
		muzzle_z = -0.77
		_chamfer(Vector3(0, 0.071, -0.26), Vector3(0.052, 0.018, 0.39), metal)
		for i in range(13):
			_chamfer(Vector3(0, 0.083, -0.06 - i * 0.029), Vector3(0.058, 0.009, 0.008), edge)
		for i in range(5):
			_chamfer(Vector3(0.048, 0.016, -0.32 - i * 0.033), Vector3(0.004, 0.020, 0.018), metal)
		var magazine := _chamfer(Vector3(0, -0.15, -0.245), Vector3(0.064, 0.23, 0.10), metal, true)
		magazine.rotation.x = 0.10
		_magazine = magazine
		_magazine_rest = magazine.position
		var grip := _chamfer(Vector3(0, -0.12, -0.034), Vector3(0.07, 0.15, 0.085), metal)
		grip.rotation.x = -0.23
		_chamfer(Vector3(0, -0.032, 0.085), Vector3(0.05, 0.068, 0.15), metal)
		_chamfer(Vector3(0.052, 0.015, -0.105), Vector3(0.005, 0.041, 0.065), metal)
		# Machined receiver controls, bolts, split handguard and magazine ribs.
		_chamfer(Vector3(0.055, 0.02, -0.205), Vector3(0.011, 0.015, 0.052), Color("919a9a"))
		_chamfer(Vector3(-0.057, -0.032, -0.098), Vector3(0.013, 0.035, 0.012), edge)
		_chamfer(Vector3(0, -0.074, -0.098), Vector3(0.059, 0.009, 0.105), metal)
		_chamfer(Vector3(0, -0.053, -0.15), Vector3(0.059, 0.048, 0.009), metal)
		_chamfer(Vector3(0, -0.051, -0.104), Vector3(0.009, 0.032, 0.009), edge)
		for side in [-1.0, 1.0]:
			for i in range(3):
				_chamfer(Vector3(side * 0.054, -0.03, -0.12 - i * 0.048), Vector3(0.003, 0.012, 0.012), Color("798183"))
			_chamfer(Vector3(side * 0.046, 0.045, -0.415), Vector3(0.006, 0.016, 0.174), metal)
			for i in range(5):
				var rib := _chamfer(Vector3(side * 0.034, -0.205 + i * 0.026, -0.244), Vector3(0.008, 0.006, 0.082), edge)
				# Ribs belong to the magazine animation; parent without changing local pose.
				var magazine_local := magazine.transform.affine_inverse() * rib.transform
				_gun.remove_child(rib)
				magazine.add_child(rib)
				rib.transform = magazine_local
		_chamfer(Vector3(0, -0.008, -0.527), Vector3(0.104, 0.105, 0.015), metal)
		if weapon_id == "smg":
			# Short suppressed PDW silhouette, flatter rail and straight box magazine.
			_barrel(Vector3(0, 0.025, -0.62), 0.23, 0.040, metal)
			magazine.scale = Vector3(0.8, 0.9, 0.75)
		elif weapon_id == "marksman":
			_barrel(Vector3(0, 0.025, -0.77), 0.34, 0.025, metal)
			_barrel(Vector3(0, 0.158, -0.23), 0.30, 0.049, metal)
			_barrel(Vector3(0, 0.158, -0.386), 0.012, 0.039, Color("263d43"))
			for z in [-0.12, -0.32]:
				_chamfer(Vector3(0, 0.11, z), Vector3(0.08, 0.048, 0.022), edge)
			muzzle_z = -0.955

		# Compact bridge sight preserves center-screen target readability.
		for x in [-0.026, 0.026]:
			_chamfer(Vector3(x, 0.12, -0.16), Vector3(0.010, 0.071, 0.048), metal)
		_chamfer(Vector3(0, 0.16, -0.16), Vector3(0.062, 0.010, 0.048), metal)
		if _hands:
			_glove(Vector3(0.035, -0.136, 0.017))
			_sleeve(Vector3(0.16, -0.36, 0.43), Vector3(0.035, -0.16, 0.07), Color("28353c"))
			_glove(Vector3(-0.055, -0.075, -0.40), true)
			_sleeve(Vector3(-0.26, -0.33, 0.12), Vector3(-0.055, -0.10, -0.33), Color("28353c"))
	_muzzle = MeshInstance3D.new()
	var flash_mesh := SurfaceTool.new()
	flash_mesh.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(6):
		var angle := i * TAU / 6.0
		var radial := Vector3(cos(angle), sin(angle), 0)
		flash_mesh.add_vertex(radial * 0.014 + Vector3(0, 0, 0.025))
		flash_mesh.add_vertex(radial * 0.045 + Vector3(0, 0, -0.035))
		flash_mesh.add_vertex(Vector3(0, 0, -0.19 if i % 2 == 0 else -0.105))
	flash_mesh.generate_normals()
	_muzzle.mesh = flash_mesh.commit()
	if _hands and not _authored.is_empty():
		_muzzle.material_override = ViewmodelShading.flash(Color("ffde9c"))
	else:
		_muzzle.material_override = _material(Color("ffde9c"), 1, 0).duplicate()
		var mat := _muzzle.material_override as StandardMaterial3D
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_gun.add_child(_muzzle)
	_muzzle.position = Vector3(0, 0.025, muzzle_z) if muzzle_at == Vector3.INF else muzzle_at
	_muzzle.visible = false

	for child in _gun.get_children():
		if child is MeshInstance3D:
			child.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

## Reads an authored GLB: every node's transform in the viewmodel node (markers),
## its untransformed position in the rifle's own space (anchors) and its meshes.
static func _authored_nodes(path: String, placement: Transform3D) -> Dictionary:
	var source: Node = (load(path) as PackedScene).instantiate()
	var result := {"markers": {}, "anchors": {}, "meshes": {}}
	for node in source.find_children("*", "Node3D", true, false):
		var local := Transform3D.IDENTITY
		var walk: Node = node
		while walk != source:
			local = (walk as Node3D).transform * local
			walk = walk.get_parent()
		result.markers[str(node.name)] = placement * local
		result.anchors[str(node.name)] = local.origin
		if node is MeshInstance3D:
			result.meshes[str(node.name)] = (node as MeshInstance3D).mesh
	source.free()
	return result

func _add_authored(part_name: String, mesh: Mesh, at: Transform3D, material: Material) -> MeshInstance3D:
	var part := MeshInstance3D.new()
	part.name = part_name
	part.mesh = mesh
	part.material_override = material
	part.transform = at
	_gun.add_child(part)
	_authored.append(part)
	return part

## Adds the authored rifle's meshes and hands; returns the muzzle position.
func _build_authored_rifle() -> Vector3:
	var placement := Transform3D(Basis.from_euler(relay_ar_rotation).scaled(Vector3.ONE * relay_ar_scale), relay_ar_offset) if _hands else Transform3D(Basis.IDENTITY, RELAY_AR_UPRIGHT_OFFSET)
	if _hands:
		_pivot = placement * RELAY_AR_PIVOT
		placement.origin -= _pivot
	var rifle := _authored_nodes(RELAY_AR, placement)
	# First person draws with the viewmodel projection; inspection keeps the plain material.
	var material: Material = ViewmodelShading.surface(RELAY_AR_TEXTURES, 0.86) if _hands else load(RELAY_AR_MATERIAL)
	var part_names := ["body", "paint_receiver", "paint_handguard", "magazine"]
	if not _hands and rifle.meshes.has("stock"):
		part_names.append("stock")
	for part_name in part_names:
		var part := _add_authored(part_name, rifle.meshes[part_name], rifle.markers[part_name], material)
		if part_name.begins_with("paint_"):
			_paint_parts.append(part)
	_magazine = _gun.get_node("magazine")
	_magazine_rest = _magazine.position
	var rounds := MeshInstance3D.new()
	rounds.name = "magazine_rounds"
	rounds.mesh = rifle.meshes["magazine_rounds"]
	rounds.material_override = material
	rounds.transform = _magazine.transform.affine_inverse() * rifle.markers["magazine_rounds"]
	_magazine.add_child(rounds)
	if _hands and use_rigged_arms and ResourceLoader.exists(RELAY_AR_ARMS):
		_rigged = true
		_arms_placement = placement
	elif _hands and ResourceLoader.exists(RELAY_AR_HANDS):
		var hands := _authored_nodes(RELAY_AR_HANDS, placement)
		_add_authored("hands", hands.meshes["hands"], hands.markers["hands"], load(RELAY_AR_HANDS_MATERIAL))
	elif _hands:
		# Procedural gloves when the hand asset is absent; offsets are in rifle space.
		var grip: Vector3 = rifle.anchors["grip_hand"]
		var support: Vector3 = rifle.anchors["support_hand"]
		_glove(placement * (grip + Vector3(0.012, -0.004, 0.010)))
		_sleeve(Vector3(0.16, -0.36, 0.43), placement * (grip + Vector3(0.020, -0.040, 0.075)), Color("28353c"))
		_glove(placement * (support + Vector3(-0.012, -0.022, 0.0)), true)
		_sleeve(Vector3(-0.26, -0.33, 0.12), placement * (support + Vector3(-0.030, -0.070, 0.070)), Color("28353c"))
	_ejection = rifle.markers["ejection"].origin
	return rifle.markers["muzzle"].origin
