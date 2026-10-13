class_name RelayYard
extends Node3D

# Shared immutable lighting avoids sky allocation churn across menu/match transitions.
# Godot 4.7.2 GLES3 can leak a dirty sky retired before its first rendered frame.
const RELAY_SKY = preload("res://assets/environments/relay_sky.tres")
const SURFACES := {
	"asphalt": preload("res://assets/materials/asphalt.png"),
	"concrete": preload("res://assets/materials/concrete.png"),
	"metal": preload("res://assets/materials/painted_metal.png")
}

const SURFACE_NORMALS := {
	"asphalt": preload("res://assets/materials/asphalt_normal.png"),
	"concrete": preload("res://assets/materials/concrete_normal.png"),
	"metal": preload("res://assets/materials/painted_metal_normal.png")
}
const SURFACE_ROUGHNESS := {
	"asphalt": preload("res://assets/materials/asphalt_roughness.png"),
	"concrete": preload("res://assets/materials/concrete_roughness.png"),
	"metal": preload("res://assets/materials/painted_metal_roughness.png")
}
var _detail_quality := true
var _surface_materials: Dictionary = {}

var sites: Array[Vector3] = [Vector3(-15, 0, 10), Vector3(15, 0, 10)]
var attack_spawns: Array[Vector3] = []
var defend_spawns: Array[Vector3] = []
var waypoints: Array[Vector3] = []
var _obstacles: Array[AABB] = []
var _navigation := AStar3D.new()
var _materials: Dictionary = {}
var _box_visuals: Array[MeshInstance3D] = []
var presentation_stats: Dictionary = {}
const INDUSTRIAL_STEEL := Color("344148")
const WEATHERED_GOLD := Color("ae935c")
const SAFETY_CRIMSON := Color("9c4344")
const PANEL_PAINT := Color("6f7b7c")

func _ready() -> void:
	name = "RelayYard"
	_build()
	_batch_static_boxes()
	_build_navigation()

func _material(color: Color, roughness: float = 0.85, emission: bool = false, surface: String = "") -> StandardMaterial3D:
	var key := str(color) + str(roughness) + str(emission) + surface
	if _materials.has(key):
		return _materials[key]
	var result := StandardMaterial3D.new()
	result.albedo_color = color
	result.roughness = roughness
	if SURFACES.has(surface):
		result.albedo_texture = SURFACES[surface]
		result.uv1_triplanar = true
		result.uv1_world_triplanar = true
		result.uv1_scale = Vector3.ONE * 0.5
		result.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		result.roughness = 0.65 if surface == "metal" else 0.94
		result.metallic = 0.38 if surface == "metal" else 0.0
		result.normal_texture = SURFACE_NORMALS[surface]
		result.normal_enabled = _detail_quality
		result.normal_scale = 0.55 if surface == "metal" else 0.35
		result.roughness_texture = SURFACE_ROUGHNESS[surface] if _detail_quality else null
		result.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
		_surface_materials[result] = surface
	if emission:
		result.emission_enabled = true
		result.emission = color
		result.emission_energy_multiplier = 1.5
	_materials[key] = result
	return result

func _box(at: Vector3, size: Vector3, color: Color, solid: bool = true, nav_block: bool = true, surface: String = "") -> Node3D:
	var node: Node3D = StaticBody3D.new() if solid else Node3D.new()
	add_child(node)
	node.position = at
	var mesh := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = size
	mesh.mesh = box
	mesh.material_override = _material(color, 0.85, false, surface)
	node.add_child(mesh)
	_box_visuals.append(mesh)
	if solid:
		var collision := CollisionShape3D.new()
		var shape := BoxShape3D.new()
		shape.size = size
		collision.shape = shape
		node.add_child(collision)
		if nav_block:
			_obstacles.append(AABB(at - size * 0.5, size).grow(0.55))
	return node

func _label(text: String, at: Vector3, color: Color, size: int = 110, turn: float = 0.0) -> void:
	var label := Label3D.new()
	label.text = text
	label.font_size = size
	label.pixel_size = 0.008
	label.modulate = color
	label.outline_size = 1
	label.outline_modulate = Color("1b262c")
	label.shaded = true
	label.no_depth_test = false
	add_child(label)
	label.position = at
	label.rotation.y = turn

func _container(at: Vector3, color: Color, length: float = 7.0) -> void:
	_box(at + Vector3(0, 1.55, 0), Vector3(3.0, 3.1, length), color, true, true, "metal")
	for z in range(int(length / 0.65)):
		_box(at + Vector3(-1.53, 1.55, -length * 0.5 + z * 0.65 + 0.25), Vector3(0.08, 2.85, 0.10), color.lightened(0.13), false)
		_box(at + Vector3(1.53, 1.55, -length * 0.5 + z * 0.65 + 0.25), Vector3(0.08, 2.85, 0.10), color.lightened(0.13), false)
	_box(at + Vector3(0, 3.12, 0), Vector3(3.12, 0.14, length + 0.12), color.darkened(0.2), false)
	for end in [-1, 1]:
		var z := float(end) * (length * 0.5 + 0.025)
		_box(at + Vector3(0, 1.55, z), Vector3(0.035, 2.75, 0.04), color.darkened(0.5), false)
		for x in [-0.95, -0.38, 0.38, 0.95]:
			_box(at + Vector3(x, 1.55, z + end * 0.023), Vector3(0.045, 2.75, 0.06), Color("545e60"), false)
			_box(at + Vector3(x, 1.1, z + end * 0.064), Vector3(0.18, 0.06, 0.035), Color("8b938d"), false)
		_box(at + Vector3(0, 0.13, z), Vector3(2.9, 0.12, 0.08), Color("283339"), false)
		_box(at + Vector3(0, 2.97, z), Vector3(2.9, 0.12, 0.08), color.darkened(0.35), false)
	_label("RY / 07\nFREIGHT SYSTEMS", at + Vector3(-1.57, 2.1, 0), Color("c2c4af"), 39, -PI * 0.5)
	_label("RY / 07\nFREIGHT SYSTEMS", at + Vector3(1.57, 2.1, 0), Color("c2c4af"), 39, PI * 0.5)


func _build() -> void:
	var environment := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = RELAY_SKY
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("c9dfe8")
	env.ambient_light_energy = 0.49
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.environment = env
	add_child(environment)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-40, -32, 0)
	sun.light_color = Color("fff0d5")
	sun.light_energy = 1.12
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 70
	add_child(sun)
	_box(Vector3(0, -0.3, 0), Vector3(48, 0.6, 48), Color("3c464d"), true, false, "asphalt")
	_box(Vector3(-24, 3, 0), Vector3(1, 6, 49), Color("5a6a73"), true, true, "concrete")
	_box(Vector3(24, 3, 0), Vector3(1, 6, 49), Color("5a6a73"), true, true, "concrete")
	_box(Vector3(0, 3, 24), Vector3(48, 6, 1), Color("65757b"), true, true, "concrete")
	_box(Vector3(0, 3, -24), Vector3(48, 6, 1), Color("65757b"), true, true, "concrete")
	# Three readable routes: west freight, exposed relay center, east service lane.
	_container(Vector3(-7, 0, -11), Color("703d3e"), 9)
	_container(Vector3(7, 0, -11), Color("36535c"), 9)
	_container(Vector3(-7, 0, 4), Color("703d3e"), 8)
	_container(Vector3(7, 0, 4), Color("36535c"), 8)
	_container(Vector3(-20, 0, 0), Color("7f8988"), 5)
	_container(Vector3(20, 0, 0), Color("7f8988"), 5)
	for at in [Vector3(-14, 0.65, -5), Vector3(14, 0.65, -5), Vector3(-18, 0.65, 13), Vector3(18, 0.65, 13), Vector3(0, 0.65, 8), Vector3(-3, 0.65, -1), Vector3(3, 0.65, -1)]:
		_box(at, Vector3(2.5, 1.3, 2.5), Color("7f7560"))
		_box(at + Vector3(0, 0.67, 0), Vector3(2.55, 0.10, 2.55), Color("b5a889"), false)
	for site_index in range(2):
		var at: Vector3 = sites[site_index]
		var tint := Color("bb955c") if site_index == 0 else Color("6ca5a5")
		for offset in [-3.5, 3.5]:
			_box(at + Vector3(offset, 0.018, 0), Vector3(0.14, 0.025, 7.1), tint, false)
			_box(at + Vector3(0, 0.018, offset), Vector3(7.1, 0.025, 0.14), tint, false)
		_box(at + Vector3(0, 0.45, 2.4), Vector3(1.0, 0.9, 1.0), Color("26343c"))
		_box(at + Vector3(0, 0.92, 2.4), Vector3(0.85, 0.05, 0.85), tint, false)
		_label("A / FREIGHT" if site_index == 0 else "B / RELAY", Vector3(at.x, 3.2, 23.4), tint, 110, PI)
	for x in [-22, 22]:
		for z in [-18, 16]:
			_box(Vector3(x, 4, z), Vector3(0.18, 8, 0.18), Color("2b3941"))
			_box(Vector3(x, 7.8, z), Vector3(1.7, 0.2, 0.7), Color("e2dfbe"), false)
	# Original gantry silhouette; overhead elements leave all walkways clear.
	_box(Vector3(0, 6.8, 16), Vector3(43, 0.55, 0.55), Color("dbb36b"), false)
	for x in [-21, 21]:
		_box(Vector3(x, 3.4, 16), Vector3(0.5, 6.8, 0.5), Color("dbb36b"))
	for x in range(-20, 21, 4):
		_box(Vector3(x, 0.012, -20), Vector3(2, 0.018, 0.14), Color("b6a273"), false)
	_label("SIGHTBREAK  //  RELAY YARD", Vector3(0, 4.1, 23.4), Color("dce7e9"), 120, PI)
	_label("01  FREIGHT   ←      →   RELAY  02", Vector3(0, 3.8, -23.4), Color("c9d6dc"), 85, 0)
	_add_environment_detail()
	_add_transfer_architecture()
	_add_service_infrastructure()
	_add_cargo_fittings()
	for i in range(5):
		attack_spawns.append(Vector3((i - 2) * 2.2, 0.05, -21))
		defend_spawns.append(Vector3((i - 2) * 2.2, 0.05, 20.5))

func is_at_site(at: Vector3) -> int:
	for i in range(sites.size()):
		if Vector2(at.x - sites[i].x, at.z - sites[i].z).length() < 3.8:
			return i
	return -1

func _clear_path(from: Vector3, to: Vector3) -> bool:
	var a := Vector3(from.x, 0.7, from.z)
	var b := Vector3(to.x, 0.7, to.z)
	for obstacle in _obstacles:
		if obstacle.intersects_segment(a, b) != null:
			return false
	return true

func _build_navigation() -> void:
	for x in range(-21, 22, 3):
		for z in range(-21, 22, 3):
			var at := Vector3(x, 0, z)
			if _clear_path(at, at + Vector3(0.01, 0, 0.01)):
				_navigation.add_point(waypoints.size(), at)
				waypoints.append(at)
	for i in range(waypoints.size()):
		for j in range(i + 1, waypoints.size()):
			if waypoints[i].distance_to(waypoints[j]) <= 4.3 and _clear_path(waypoints[i], waypoints[j]):
				_navigation.connect_points(i, j)

func bot_navigation(from: Vector3, to: Vector3) -> Vector3:
	if _clear_path(from, to):
		return to
	var start := -1
	var finish := -1
	var start_distance := INF
	var finish_distance := INF
	for i in range(waypoints.size()):
		var d := from.distance_squared_to(waypoints[i])
		if d < start_distance and _clear_path(from, waypoints[i]):
			start = i
			start_distance = d
		var e := to.distance_squared_to(waypoints[i])
		if e < finish_distance and _clear_path(to, waypoints[i]):
			finish = i
			finish_distance = e
	if start < 0 or finish < 0:
		return from
	var path := _navigation.get_point_path(start, finish)
	if path.is_empty():
		return from
	for i in range(path.size() - 1, -1, -1):
		if _clear_path(from, path[i]):
			return path[i]
	return path[0]

func _pipe(at: Vector3, length: float, radius: float, tint: Color, horizontal: bool = false) -> void:
	var visual := MeshInstance3D.new()
	var cylinder := CylinderMesh.new()
	cylinder.top_radius = radius
	cylinder.bottom_radius = radius
	cylinder.height = length
	cylinder.radial_segments = 12
	visual.mesh = cylinder
	visual.material_override = _material(tint)
	add_child(visual)
	visual.position = at
	if horizontal:
		visual.rotation.z = PI * 0.5

func _floor_text(text: String, at: Vector3, tint: Color, size: int = 90) -> void:
	var visual := Label3D.new()
	visual.text = text
	visual.font_size = size
	visual.pixel_size = 0.012
	visual.modulate = tint
	visual.outline_size = 0
	add_child(visual)
	visual.position = at
	visual.rotation.x = -PI * 0.5

func _add_environment_detail() -> void:
	# Decorative pieces never change collision or navigation: routes remain tested.
	var steel := Color("35434b")
	var concrete := Color("5b6464")
	var paint := Color("998859")
	# Paved-panel seams complement the fine baked asphalt grain.
	for z in range(-21, 22, 7):
		_box(Vector3(0, 0.006, z), Vector3(46, 0.006, 0.028), Color("263139"), false)
	for x in [-21, -10, 10, 21]:
		_box(Vector3(x, 0.007, 0), Vector3(0.026, 0.006, 46), Color("263139"), false)
	for x in [-12, 12]:
		for z in range(-20, 19, 4):
			_box(Vector3(x, 0.011, z), Vector3(0.095, 0.008, 1.65), paint.darkened(0.18), false)
	_floor_text("01 / FREIGHT", Vector3(-15, 0.03, -18), Color("b4a077"), 85)
	_floor_text("02 / RELAY", Vector3(15, 0.03, -18), Color("79a4aa"), 85)
	_floor_text("KEEP CLEAR", Vector3(0, 0.03, -6), Color("8c9490"), 60)
	# Wall base, upright concrete panel seams, and raised utility conduit.
	for side in [-1, 1]:
		_box(Vector3(side * 23.43, 0.4, 0), Vector3(0.06, 0.78, 46), Color("34434a"), false)
		_box(Vector3(0, 0.4, side * 23.43), Vector3(46, 0.78, 0.06), Color("34434a"), false)
		for z in range(-20, 21, 5):
			_box(Vector3(side * 23.43, 3.1, z), Vector3(0.08, 5.8, 0.08), Color("3c4a50"), false)
		_box(Vector3(side * 23.30, 4.8, 0), Vector3(0.08, 0.10, 45), Color("2c3c43"), false)
	# Far transfer warehouse: dark glazing, structural mullions, roof monitors.
	_box(Vector3(0, 5.9, 32), Vector3(49, 11.8, 15), Color("657274"), false)
	_box(Vector3(0, 11.85, 31.5), Vector3(51, 0.30, 16.5), Color("384a54"), false)
	_box(Vector3(0, 8.1, 24.46), Vector3(46, 2.8, 0.08), Color("273b46"), false, true, "metal")
	for x in range(-22, 23, 4):
		_box(Vector3(x, 8.1, 24.35), Vector3(0.17, 3.1, 0.12), Color("738081"), false)
		_box(Vector3(x, 5.95, 24.33), Vector3(0.25, 11.7, 0.20), Color("4a5b62"), false)
	_box(Vector3(0, 8.1, 24.32), Vector3(46, 0.11, 0.12), Color("738081"), false)
	for x in [-17, -6, 6, 17]:
		_box(Vector3(x, 12.35, 32), Vector3(7.5, 0.8, 7), Color("788383"), false)
		var roof := _box(Vector3(x, 12.9, 32), Vector3(8.1, 0.22, 7.5), Color("35454e"), false)
		roof.rotation.z = -0.08
	_label("R Y   /   TRANSFER STATION", Vector3(0, 10.55, 24.2), Color("bac5ba"), 135, PI)
	# Side buildings and a water tower create an original industrial skyline.
	_box(Vector3(-31, 6, -7), Vector3(12, 12, 29), Color("4b5b62"), false)
	_box(Vector3(-31, 12.15, -7), Vector3(13, 0.3, 30), steel, false)
	for z in [-18, -10, -2, 6]:
		_box(Vector3(-24.9, 8.8, z), Vector3(0.1, 2.0, 4.8), Color("253c48"), false)
		_box(Vector3(-24.82, 8.8, z), Vector3(0.08, 2.1, 0.12), Color("7b8789"), false)
	_box(Vector3(31, 4.8, 3), Vector3(12, 9.6, 37), Color("716e60"), false)
	_box(Vector3(31, 9.8, 3), Vector3(13, 0.3, 38), steel, false)
	_pipe(Vector3(32, 14, 16), 8, 2.8, Color("637579"))
	_pipe(Vector3(32, 18.1, 16), 0.20, 3.1, steel)
	for z in [13.8, 18.2]:
		for x in [29.8, 34.2]:
			_box(Vector3(x, 7, z), Vector3(0.20, 14, 0.20), steel, false)
	_pipe(Vector3(-28, 15, -10), 7, 0.45, Color("7d817a"))
	_pipe(Vector3(-30, 14, -12), 5, 0.35, Color("7d817a"))
	# Gantry cross bracing and hanging cable add a recognizable relay landmark.
	for x in range(-20, 21, 4):
		var brace := _box(Vector3(x, 7.25, 16), Vector3(2.0, 0.11, 0.12), paint.darkened(0.2), false)
		brace.rotation.z = 0.45 if x % 8 == 0 else -0.45
	_box(Vector3(0, 7.7, 16), Vector3(43, 0.17, 0.25), paint, false)
	_box(Vector3(12, 5.65, 16), Vector3(0.04, 2.1, 0.04), steel, false)
	# Low-cover crates retain original bounds; slats/straps visually explain cover.
	for at in [Vector3(-14, 0.65, -5), Vector3(14, 0.65, -5), Vector3(-18, 0.65, 13), Vector3(18, 0.65, 13), Vector3(0, 0.65, 8), Vector3(-3, 0.65, -1), Vector3(3, 0.65, -1)]:
		for dx in [-0.86, 0.86]:
			_box(at + Vector3(dx, 0, 0), Vector3(0.10, 1.34, 2.56), Color("3e4949"), false)
		for height in [-0.29, 0.18]:
			_box(at + Vector3(0, height, -1.255), Vector3(2.4, 0.035, 0.015), Color("58584a"), false)
			_box(at + Vector3(0, height, 1.255), Vector3(2.4, 0.035, 0.015), Color("58584a"), false)
	# Site letters on actual ground plus emissive terminal screens.
	for i in range(sites.size()):
		var tint := Color("d0a460") if i == 0 else Color("69b6bd")
		_floor_text("A" if i == 0 else "B", sites[i] + Vector3(-2.2, 0.032, 0), tint, 170)
		var screen := _box(sites[i] + Vector3(0, 0.96, 2.4), Vector3(0.65, 0.035, 0.48), tint.darkened(0.3), false)
		var screen_mesh := screen.get_child(0) as MeshInstance3D
		screen_mesh.material_override = _material(tint.darkened(0.4), 0.7, true)
		_label("LINK / 01" if i == 0 else "LINK / 02", sites[i] + Vector3(0, 0.70, 1.886), tint, 24, PI)

func _batch_static_boxes() -> void:
	# Shared unit-cube mesh and one instanced draw per material. Hundreds of repeated
	# hardware pieces do not each submit a draw or retain an empty scene node.
	presentation_stats["box_instances"] = _box_visuals.size()
	presentation_stats["static_batches"] = 0
	# Physics bodies and route geometry stay intact.
	var batches: Dictionary = {}
	for visual in _box_visuals:
		var material: Material = visual.material_override
		if not batches.has(material):
			batches[material] = []
		batches[material].append(visual)
	var cube := BoxMesh.new()
	cube.size = Vector3.ONE
	for material: Material in batches:
		var visuals: Array = batches[material]
		var batch := MultiMeshInstance3D.new()
		var instances := MultiMesh.new()
		instances.transform_format = MultiMesh.TRANSFORM_3D
		instances.mesh = cube
		instances.instance_count = visuals.size()
		for i in range(visuals.size()):
			var visual: MeshInstance3D = visuals[i]
			var shape := visual.mesh as BoxMesh
			var local := global_transform.affine_inverse() * visual.global_transform
			local.basis = local.basis.scaled_local(shape.size)
			instances.set_instance_transform(i, local)
			if visual.get_parent() is StaticBody3D:
				visual.queue_free()
			else:
				visual.get_parent().queue_free()
		batch.multimesh = instances
		batch.material_override = material
		add_child(batch)
		presentation_stats["static_batches"] += 1
	_box_visuals.clear()

func _beam_between(start: Vector3, finish: Vector3, width: float, depth: float, tint: Color) -> Node3D:
	var beam := _box((start + finish) * 0.5, Vector3(width, start.distance_to(finish), depth), tint, false)
	# Orthonormal basis for a cuboid whose long local Y axis follows the strut.
	var axis := (finish - start).normalized()
	var reference := Vector3.FORWARD if absf(axis.dot(Vector3.FORWARD)) < 0.95 else Vector3.RIGHT
	var right := axis.cross(reference).normalized()
	beam.basis = Basis(right, axis, right.cross(axis))
	return beam

func _add_transfer_architecture() -> void:
	# All additions are fitted to existing collision shells or above player clearance.
	# The transfer hall is an engineered building, with docking doors and service bays.
	for x in [-16.0, 0.0, 16.0]:
		_box(Vector3(x, 2.6, 23.40), Vector3(7.7, 5.1, 0.13), INDUSTRIAL_STEEL, false)
		_box(Vector3(x, 2.45, 23.30), Vector3(6.8, 4.7, 0.10), Color("4e5c61"), false, true, "metal")
		for y in range(1, 12):
			_box(Vector3(x, y * 0.4, 23.22), Vector3(6.75, 0.028, 0.07), INDUSTRIAL_STEEL, false)
		for dx in [-3.55, 3.55]:
			_box(Vector3(x + dx, 2.5, 23.22), Vector3(0.25, 5.05, 0.28), PANEL_PAINT, false)
			_box(Vector3(x + dx, 0.60, 23.08), Vector3(0.32, 1.2, 0.08), WEATHERED_GOLD, false)
			for y in [0.25, 0.70, 1.10]:
				_box(Vector3(x + dx, y, 23.025), Vector3(0.33, 0.13, 0.035), INDUSTRIAL_STEEL, false)
		_box(Vector3(x, 5.15, 23.10), Vector3(8.1, 0.18, 0.70), INDUSTRIAL_STEEL, false)
		_box(Vector3(x, 4.94, 22.95), Vector3(2.0, 0.09, 0.20), Color("c1baa2"), false)
		_label("01 / FREIGHT" if x < 0 else ("02 / RELAY" if x > 0 else "TRANSFER CONTROL"), Vector3(x, 5.7, 23.25), Color("d1c6aa"), 50, PI)
	# Recessed ribbed fascia and vertical columns extend above the old perimeter.
	for x in range(-22, 23, 2):
		_box(Vector3(x, 10.8, 24.17), Vector3(0.06, 1.25, 0.11), INDUSTRIAL_STEEL, false)
	for x in range(-24, 25, 8):
		_box(Vector3(x, 7.5, 24.10), Vector3(0.45, 8.75, 0.48), INDUSTRIAL_STEEL, false)
		_box(Vector3(x, 11.75, 23.9), Vector3(0.8, 0.22, 0.8), PANEL_PAINT, false)
	# I-section crane structure: paired rails, diagonal web, column feet, trolley.
	for z in [15.5, 16.5]:
		_box(Vector3(0, 6.53, z), Vector3(43.8, 0.16, 0.38), WEATHERED_GOLD, false)
		_box(Vector3(0, 7.82, z), Vector3(43.8, 0.16, 0.38), WEATHERED_GOLD, false)
		for x in range(-20, 21, 4):
			_beam_between(Vector3(x - 1.9, 6.65, z), Vector3(x + 1.9, 7.71, z), 0.12, 0.13, INDUSTRIAL_STEEL)
	for x in [-21.0, 21.0]:
		_box(Vector3(x, 0.1, 16), Vector3(0.82, 0.16, 0.82), INDUSTRIAL_STEEL, false)
		for z in [15.75, 16.25]:
			_box(Vector3(x, 3.45, z), Vector3(0.62, 6.75, 0.09), WEATHERED_GOLD, false)
		_beam_between(Vector3(x, 5.1, 16), Vector3(x - signf(x) * 2.5, 6.65, 16), 0.19, 0.3, WEATHERED_GOLD)
		for height in [0.35, 0.70, 1.05]:
			_box(Vector3(x, height, 15.70), Vector3(0.63, 0.15, 0.06), INDUSTRIAL_STEEL, false)
	_box(Vector3(0, 7.0, 16), Vector3(3.3, 0.65, 1.8), SAFETY_CRIMSON, false, true, "metal")
	_box(Vector3(0, 6.5, 16), Vector3(1.3, 0.35, 1.1), INDUSTRIAL_STEEL, false)
	for x in [-0.43, 0.43]:
		_box(Vector3(x, 5.74, 16), Vector3(0.035, 1.35, 0.035), INDUSTRIAL_STEEL, false)
	_box(Vector3(0, 5.05, 16), Vector3(1.05, 0.28, 0.45), WEATHERED_GOLD, false)
	_label("RY • 08 T", Vector3(0, 7.03, 15.085), Color("e1d3b4"), 37, PI)
	# Service walkway is beyond collision perimeter: railings/cable trays create scale.
	for side in [-1, 1]:
		_box(Vector3(side * 24.8, 6.30, 0), Vector3(2.4, 0.22, 44), INDUSTRIAL_STEEL, false)
		for z in range(-20, 23, 4):
			_box(Vector3(side * 23.65, 6.95, z), Vector3(0.075, 1.2, 0.075), PANEL_PAINT, false)
			_beam_between(Vector3(side * 23.8, 6.10, z), Vector3(side * 25.1, 4.9, z), 0.12, 0.12, INDUSTRIAL_STEEL)
		for y in [6.65, 7.45]:
			_box(Vector3(side * 23.65, y, 0), Vector3(0.08, 0.08, 44), PANEL_PAINT, false)
		_box(Vector3(side * 23.63, 6.38, 0), Vector3(0.08, 0.15, 44), WEATHERED_GOLD, false)

func _add_service_infrastructure() -> void:
	# Architectural service layer at human scale: wall-mounted electrical cabinets,
	# conduit, air handling units and drainage. Detail stays out of firing lanes.
	for side in [-1, 1]:
		for z in [-16.0, 6.0, 19.0]:
			_box(Vector3(side * 23.38, 1.80, z), Vector3(0.22, 2.20, 2.00), INDUSTRIAL_STEEL, false)
			_box(Vector3(side * 23.22, 1.80, z), Vector3(0.12, 1.97, 1.78), PANEL_PAINT, false, true, "metal")
			_box(Vector3(side * 23.13, 1.65, z + 0.60), Vector3(0.08, 0.28, 0.05), INDUSTRIAL_STEEL, false)
			for vent in range(5):
				_box(Vector3(side * 23.13, 1.09 + vent * 0.075, z), Vector3(0.035, 0.026, 1.10), INDUSTRIAL_STEEL, false)
			_box(Vector3(side * 23.11, 2.30, z), Vector3(0.036, 0.26, 0.36), WEATHERED_GOLD, false)
			_label("!", Vector3(side * 23.07, 2.30, z), INDUSTRIAL_STEEL, 28, side * PI * 0.5)
			_box(Vector3(side * 23.26, 3.7, z - 0.6), Vector3(0.07, 1.55, 0.075), PANEL_PAINT, false)
			_box(Vector3(side * 23.26, 3.7, z - 0.4), Vector3(0.07, 1.55, 0.075), PANEL_PAINT, false)
		# Flat slotted drains are geometry, so no alpha, decal or shader dependency.
		_box(Vector3(side * 22.8, 0.013, 0), Vector3(0.38, 0.018, 45), INDUSTRIAL_STEEL, false)
		for z in range(-22, 23):
			_box(Vector3(side * 22.8, 0.025, z), Vector3(0.33, 0.008, 0.08), PANEL_PAINT, false)
		# Roof ventilation banks give the side halls an industrial silhouette.
		for z in [-15.0, 0.0, 15.0]:
			var roof_y := 12.8 if side < 0 else 10.5
			_box(Vector3(side * 28.8, roof_y, z), Vector3(4.0, 1.3, 2.4), PANEL_PAINT, false, true, "metal")
			for y in range(5):
				_box(Vector3(side * 26.78, roof_y - 0.45 + y * 0.20, z), Vector3(0.05, 0.08, 2.05), INDUSTRIAL_STEEL, false)
			_box(Vector3(side * 28.8, roof_y + 0.72, z), Vector3(4.2, 0.16, 2.6), INDUSTRIAL_STEEL, false)
		# Cable ladder over the wall, elevated sufficiently to preserve shooting lanes.
		for z in range(-21, 22, 3):
			_box(Vector3(side * 23.30, 4.55, z), Vector3(0.2, 0.08, 0.55), INDUSTRIAL_STEEL, false)
		for y in [4.50, 4.65]:
			_box(Vector3(side * 23.20, y, 0), Vector3(0.08, 0.05, 44), SAFETY_CRIMSON if y > 4.6 else PANEL_PAINT, false)
	# Buried power routing explains each relay zone's industrial purpose.
	for site in sites:
		for dx in [-0.16, 0.16]:
			_box(Vector3(site.x + dx, 0.024, 17.8), Vector3(0.07, 0.01, 10.0), WEATHERED_GOLD.darkened(0.3), false)
		for x in [-0.38, 0.38]:
			_box(site + Vector3(x, 0.46, 1.89), Vector3(0.08, 0.77, 0.03), INDUSTRIAL_STEEL, false)
			for y in [0.2, 0.8]:
				_box(site + Vector3(x, y, 1.865), Vector3(0.04, 0.035, 0.035), PANEL_PAINT, false)
		_box(site + Vector3(0, 0.35, 1.87), Vector3(0.51, 0.33, 0.03), Color("151f27"), false)
		for x in [-0.16, 0.0, 0.16]:
			_box(site + Vector3(x, 0.36, 1.85), Vector3(0.06, 0.18, 0.015), PANEL_PAINT, false)

func _add_cargo_fittings() -> void:
	var cargo: Array = [
		[Vector3(-7, 0, -11), 9.0], [Vector3(7, 0, -11), 9.0],
		[Vector3(-7, 0, 4), 8.0], [Vector3(7, 0, 4), 8.0],
		[Vector3(-20, 0, 0), 5.0], [Vector3(20, 0, 0), 5.0]
	]
	for entry in cargo:
		var at: Vector3 = entry[0]
		var length: float = entry[1]
		for side in [-1, 1]:
			# Heavy corner castings, bottom rails, door hinges and small data plates.
			_box(at + Vector3(side * 1.49, 0.14, 0), Vector3(0.12, 0.23, length), INDUSTRIAL_STEEL, false)
			for end in [-1, 1]:
				for y in [0.14, 2.97]:
					_box(at + Vector3(side * 1.49, y, end * (length * 0.5 - 0.09)), Vector3(0.20, 0.27, 0.24), INDUSTRIAL_STEEL, false)
					_box(at + Vector3(side * 1.59, y, end * (length * 0.5 - 0.09)), Vector3(0.014, 0.095, 0.10), Color("101b23"), false)
				for y in [0.52, 1.55, 2.55]:
					_box(at + Vector3(side * 1.34, y, end * (length * 0.5 + 0.06)), Vector3(0.20, 0.10, 0.08), PANEL_PAINT, false)
			_box(at + Vector3(side * 1.588, 0.86, -length * 0.30), Vector3(0.026, 0.35, 0.75), INDUSTRIAL_STEEL, false)
			_box(at + Vector3(side * 1.605, 0.86, -length * 0.30), Vector3(0.014, 0.17, 0.47), Color("b0b7aa"), false)
			for z in [-length * 0.40, length * 0.40]:
				_box(at + Vector3(side * 1.582, 0.25, z), Vector3(0.025, 0.12, 0.44), WEATHERED_GOLD, false)
	# Reinforced transit cases with handles, latches and raised corner guards.
	for at in [Vector3(-14, 0.65, -5), Vector3(14, 0.65, -5), Vector3(-18, 0.65, 13), Vector3(18, 0.65, 13), Vector3(0, 0.65, 8), Vector3(-3, 0.65, -1), Vector3(3, 0.65, -1)]:
		for end in [-1, 1]:
			for x in [-0.86, 0.86]:
				_box(at + Vector3(x, 0.32, end * 1.289), Vector3(0.17, 0.25, 0.07), PANEL_PAINT, false)
				_box(at + Vector3(x, 0.32, end * 1.335), Vector3(0.06, 0.15, 0.03), INDUSTRIAL_STEEL, false)
			_box(at + Vector3(0, 0.15, end * 1.283), Vector3(0.52, 0.18, 0.035), INDUSTRIAL_STEEL, false)
			_box(at + Vector3(0, 0.17, end * 1.328), Vector3(0.37, 0.055, 0.065), PANEL_PAINT, false)
			_box(at + Vector3(0.43, -0.26, end * 1.273), Vector3(0.40, 0.21, 0.022), Color("c5c3aa"), false)
		for x in [-1.16, 1.16]:
			for z in [-1.16, 1.16]:
				_box(at + Vector3(x, 0.60, z), Vector3(0.21, 0.22, 0.21), INDUSTRIAL_STEEL, false)

func apply_detail_quality(high_quality: bool) -> void:
	_detail_quality = high_quality
	for material: StandardMaterial3D in _surface_materials:
		material.normal_enabled = high_quality
		material.roughness_texture = SURFACE_ROUGHNESS[_surface_materials[material]] if high_quality else null
