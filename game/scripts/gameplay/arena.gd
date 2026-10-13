class_name RelayYard
extends Node3D

var sites: Array[Vector3] = [Vector3(-15, 0, 10), Vector3(15, 0, 10)]
var attack_spawns: Array[Vector3] = []
var defend_spawns: Array[Vector3] = []
var waypoints: Array[Vector3] = []
var _obstacles: Array[AABB] = []
var _navigation := AStar3D.new()
var _materials: Dictionary = {}
var _box_visuals: Array[MeshInstance3D] = []

func _ready() -> void:
	name = "RelayYard"
	_build()
	_batch_static_boxes()
	_build_navigation()

func _material(color: Color, roughness: float = 0.85, emission: bool = false) -> StandardMaterial3D:
	var key := str(color) + str(emission)
	if _materials.has(key):
		return _materials[key]
	var result := StandardMaterial3D.new()
	result.albedo_color = color
	result.roughness = roughness
	if emission:
		result.emission_enabled = true
		result.emission = color
		result.emission_energy_multiplier = 1.5
	_materials[key] = result
	return result

func _box(at: Vector3, size: Vector3, color: Color, solid: bool = true, nav_block: bool = true) -> Node3D:
	var node: Node3D = StaticBody3D.new() if solid else Node3D.new()
	add_child(node)
	node.position = at
	var mesh := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = size
	mesh.mesh = box
	mesh.material_override = _material(color)
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
	label.outline_size = 5
	label.no_depth_test = false
	add_child(label)
	label.position = at
	label.rotation.y = turn

func _container(at: Vector3, color: Color, length: float = 7.0) -> void:
	_box(at + Vector3(0, 1.55, 0), Vector3(3.0, 3.1, length), color)
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
	var sky := Sky.new()
	var atmosphere := ProceduralSkyMaterial.new()
	atmosphere.sky_top_color = Color("45647d")
	atmosphere.sky_horizon_color = Color("c3ccc8")
	atmosphere.ground_bottom_color = Color("333d46")
	atmosphere.ground_horizon_color = Color("c3ccc8")
	atmosphere.sky_curve = 0.2
	atmosphere.sun_angle_max = 12
	sky.sky_material = atmosphere
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("c9dfe8")
	env.ambient_light_energy = 0.38
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.environment = env
	add_child(environment)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48, -32, 0)
	sun.light_color = Color("fff0d5")
	sun.light_energy = 1.0
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 70
	add_child(sun)
	_box(Vector3(0, -0.3, 0), Vector3(48, 0.6, 48), Color("343e46"), true, false)
	_box(Vector3(-24, 3, 0), Vector3(1, 6, 49), Color("5a6a73"))
	_box(Vector3(24, 3, 0), Vector3(1, 6, 49), Color("5a6a73"))
	_box(Vector3(0, 3, 24), Vector3(48, 6, 1), Color("65757b"))
	_box(Vector3(0, 3, -24), Vector3(48, 6, 1), Color("65757b"))
	# Three readable routes: west freight, exposed relay center, east service lane.
	_container(Vector3(-7, 0, -11), Color("754436"), 9)
	_container(Vector3(7, 0, -11), Color("315963"), 9)
	_container(Vector3(-7, 0, 4), Color("754436"), 8)
	_container(Vector3(7, 0, 4), Color("315963"), 8)
	_container(Vector3(-20, 0, 0), Color("7f8988"), 5)
	_container(Vector3(20, 0, 0), Color("7f8988"), 5)
	for at in [Vector3(-14, 0.65, -5), Vector3(14, 0.65, -5), Vector3(-18, 0.65, 13), Vector3(18, 0.65, 13), Vector3(0, 0.65, 8), Vector3(-3, 0.65, -1), Vector3(3, 0.65, -1)]:
		_box(at, Vector3(2.5, 1.3, 2.5), Color("7f7560"))
		_box(at + Vector3(0, 0.67, 0), Vector3(2.55, 0.10, 2.55), Color("b5a889"), false)
	for site_index in range(2):
		var at: Vector3 = sites[site_index]
		var tint := Color("e3a153") if site_index == 0 else Color("51c5c9")
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
	# Continuous paved-panel seams break up the large flat ground without textures.
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
	_box(Vector3(0, 8.1, 24.46), Vector3(46, 2.8, 0.08), Color("2a414d"), false)
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
	# One instanced draw per material; physics bodies and route geometry stay intact.
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
			visual.queue_free()
		batch.multimesh = instances
		batch.material_override = material
		add_child(batch)
	_box_visuals.clear()
