extends Node3D
class_name SBArena

const TEAM_ATTACK := 0
const TEAM_DEFEND := 1
const ROUND_TIME := 100.0
const BUY_TIME := 12.0
const PLANT_TIME := 3.2
const DEFUSE_TIME := 4.5
const BOMB_TIMER := 40.0
const PLANT_RADIUS := 4.0
const DEFUSE_RADIUS := 2.8

var sites: Array[Vector3] = [
	Vector3(-15.0, 0.0, 10.0),
	Vector3(15.0, 0.0, 10.0),
]

var attack_spawns: Array[Vector3] = [
	Vector3(-8.0, 0.0, -18.0),
	Vector3(-5.0, 0.0, -18.0),
	Vector3(-2.0, 0.0, -18.0),
	Vector3(2.0, 0.0, -18.0),
	Vector3(5.0, 0.0, -18.0),
]

var defend_spawns: Array[Vector3] = [
	Vector3(-12.0, 0.0, 17.0),
	Vector3(-4.0, 0.0, 17.0),
	Vector3(0.0, 0.0, 17.0),
	Vector3(4.0, 0.0, 17.0),
	Vector3(12.0, 0.0, 17.0),
]

var waypoints: PackedVector3Array = PackedVector3Array()
var _navigation := AStar3D.new()
var _obstacles: Array[AABB] = []
var _smokes: Array[Dictionary] = []

var _mat_cache: Dictionary = {}

func _ready() -> void:
	_build_geometry()
	_build_navigation()

func _process(delta: float) -> void:
	for index in range(_smokes.size() - 1, -1, -1):
		var item := _smokes[index]
		item.ttl = float(item.ttl) - delta
		var node: Node3D = item.node
		if is_instance_valid(node):
			var mesh := node.get_node_or_null("Cloud") as MeshInstance3D
			if mesh and mesh.material_override is StandardMaterial3D:
				var mat := mesh.material_override as StandardMaterial3D
				mat.albedo_color.a = clampf(float(item.ttl) / 14.0, 0.0, 1.0) * 0.62
		if float(item.ttl) <= 0.0:
			if is_instance_valid(node):
				node.queue_free()
			_smokes.remove_at(index)

func spawn_for(team: int, slot: int) -> Vector3:
	var list := attack_spawns if team == TEAM_ATTACK else defend_spawns
	return list[posmod(slot, list.size())] + Vector3(0.0, 0.05, 0.0)

func nearest_site(at: Vector3) -> int:
	return 0 if at.distance_to(sites[0]) <= at.distance_to(sites[1]) else 1

func can_plant(at: Vector3) -> int:
	for idx in range(sites.size()):
		if at.distance_to(sites[idx]) <= PLANT_RADIUS:
			return idx
	return -1

func add_smoke(at: Vector3, radius: float = 4.6, ttl: float = 14.0) -> void:
	var holder := Node3D.new()
	holder.position = Vector3(at.x, 0.0, at.z)
	var cloud := MeshInstance3D.new()
	cloud.name = "Cloud"
	var sphere := SphereMesh.new()
	sphere.radius = radius
	sphere.height = radius * 1.35
	cloud.mesh = sphere
	cloud.position.y = radius * 0.45
	var material := StandardMaterial3D.new()
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color = Color(0.76, 0.81, 0.86, 0.62)
	cloud.material_override = material
	holder.add_child(cloud)
	add_child(holder)
	_smokes.append({"position": Vector3(at.x, 1.2, at.z), "radius": radius, "ttl": ttl, "node": holder})

func clear_smokes() -> void:
	for item in _smokes:
		var node: Node3D = item.node
		if is_instance_valid(node):
			node.queue_free()
	_smokes.clear()

func smoke_obscures(from: Vector3, to: Vector3) -> bool:
	for item in _smokes:
		var center: Vector3 = item.position
		var radius: float = item.radius
		var closest := Geometry3D.get_closest_point_to_segment(center, from, to)
		if closest.distance_to(center) <= radius:
			return true
	return false

func _get_material(color: Color, rough: float, metal: float) -> StandardMaterial3D:
	var key := "%s_%.2f_%.2f" % [color.to_html(), rough, metal]
	if _mat_cache.has(key):
		return _mat_cache[key]
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.roughness = rough
	mat.metallic = metal
	_mat_cache[key] = mat
	return mat

func _box(at: Vector3, size: Vector3, color: Color, record_obstacle: bool = true, rough: float = 0.85, metal: float = 0.08) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.position = at
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = size
	shape.shape = box
	body.add_child(shape)
	var mesh := MeshInstance3D.new()
	var box_mesh := BoxMesh.new()
	box_mesh.size = size
	mesh.mesh = box_mesh
	mesh.material_override = _get_material(color, rough, metal)
	body.add_child(mesh)
	add_child(body)
	if record_obstacle and size.y > 0.6 and at.y < 3.0:
		_obstacles.append(AABB(at - size * 0.5, size).grow(0.55))
	return body

func _shipping_container(at: Vector3, length: float, is_horizontal: bool, base_color: Color) -> void:
	var w := length if is_horizontal else 3.0
	var d := 3.0 if is_horizontal else length
	var h := 3.1
	_box(at + Vector3(0, h * 0.5, 0), Vector3(w, h, d), base_color, true, 0.65, 0.35)
	var trim_c := base_color.darkened(0.25)
	_box(at + Vector3(0, h + 0.05, 0), Vector3(w + 0.1, 0.1, d + 0.1), trim_c, false, 0.5, 0.5)
	var count := int(length / 1.5)
	for i in range(-count / 2, count / 2 + 1):
		if is_horizontal:
			_box(at + Vector3(i * 1.4, h * 0.5, 0), Vector3(0.15, h - 0.2, d + 0.08), base_color.lightened(0.08), false, 0.7, 0.3)
		else:
			_box(at + Vector3(0, h * 0.5, i * 1.4), Vector3(w + 0.08, h - 0.2, 0.15), base_color.lightened(0.08), false, 0.7, 0.3)

func _build_geometry() -> void:
	_obstacles.clear()
	_box(Vector3(0.0, -0.25, 0.0), Vector3(64.0, 0.5, 64.0), Color(0.16, 0.18, 0.20), false, 0.9, 0.05)
	for i in range(-28, 30, 8):
		_box(Vector3(i, 0.01, 0.0), Vector3(0.15, 0.02, 56.0), Color(0.22, 0.24, 0.27), false, 0.95, 0.0)
		_box(Vector3(0.0, 0.01, i), Vector3(56.0, 0.02, 0.15), Color(0.22, 0.24, 0.27), false, 0.95, 0.0)

	var wall_c := Color(0.25, 0.28, 0.32)
	var wall_trim := Color(0.18, 0.20, 0.24)
	_box(Vector3(0.0, 2.5, -24.5), Vector3(50.0, 5.0, 1.0), wall_c, false)
	_box(Vector3(0.0, 5.2, -24.5), Vector3(50.4, 0.4, 1.4), wall_trim, false)
	_box(Vector3(0.0, 2.5, 24.5), Vector3(50.0, 5.0, 1.0), wall_c, false)
	_box(Vector3(0.0, 5.2, 24.5), Vector3(50.4, 0.4, 1.4), wall_trim, false)
	_box(Vector3(-24.5, 2.5, 0.0), Vector3(1.0, 5.0, 48.0), wall_c, false)
	_box(Vector3(-24.5, 5.2, 0.0), Vector3(1.4, 0.4, 48.4), wall_trim, false)
	_box(Vector3(24.5, 2.5, 0.0), Vector3(1.0, 5.0, 48.0), wall_c, false)
	_box(Vector3(24.5, 5.2, 0.0), Vector3(1.4, 0.4, 48.4), wall_trim, false)

	_shipping_container(Vector3(-7.0, 0.0, -11.0), 9.0, false, Color(0.18, 0.32, 0.45))
	_shipping_container(Vector3(7.0, 0.0, -11.0), 9.0, false, Color(0.48, 0.24, 0.18))
	_shipping_container(Vector3(-7.0, 0.0, 4.0), 8.0, false, Color(0.22, 0.38, 0.28))
	_shipping_container(Vector3(7.0, 0.0, 4.0), 8.0, false, Color(0.45, 0.36, 0.18))

	var crate_c := Color(0.46, 0.38, 0.26)
	_box(Vector3(-14.0, 0.65, -5.0), Vector3(2.5, 1.3, 2.5), crate_c)
	_box(Vector3(14.0, 0.65, -5.0), Vector3(2.5, 1.3, 2.5), crate_c)
	_box(Vector3(-18.0, 0.65, 13.0), Vector3(2.5, 1.3, 2.5), crate_c)
	_box(Vector3(18.0, 0.65, 13.0), Vector3(2.5, 1.3, 2.5), crate_c)
	_box(Vector3(0.0, 0.65, 8.0), Vector3(2.5, 1.3, 2.5), crate_c.darkened(0.15))
	_box(Vector3(-3.0, 0.65, -1.0), Vector3(2.5, 1.3, 2.5), crate_c)
	_box(Vector3(3.0, 0.65, -1.0), Vector3(2.5, 1.3, 2.5), crate_c)

	_shipping_container(Vector3(-20.0, 0.0, 0.0), 5.0, false, Color(0.30, 0.33, 0.38))
	_shipping_container(Vector3(20.0, 0.0, 0.0), 5.0, false, Color(0.30, 0.33, 0.38))

	_build_site_marker(sites[0], Color(0.95, 0.48, 0.14), "A")
	_build_site_marker(sites[1], Color(0.20, 0.72, 0.95), "B")

func _build_site_marker(at: Vector3, color: Color, _label: String) -> void:
	_box(at + Vector3(0.0, 0.02, 0.0), Vector3(6.5, 0.04, 6.5), color * Color(1, 1, 1, 0.4), false, 0.4, 0.2)
	_box(at + Vector3(0.0, 0.03, 0.0), Vector3(5.8, 0.04, 5.8), Color(0.14, 0.16, 0.18), false, 0.8, 0.1)
	_box(at + Vector3(0.0, 0.45, 2.4), Vector3(1.0, 0.9, 1.0), Color(0.2, 0.22, 0.25), true, 0.4, 0.6)
	_box(at + Vector3(0.0, 1.1, 2.4), Vector3(0.8, 0.4, 0.8), color, false, 0.2, 0.8)

func _build_navigation() -> void:
	waypoints.clear()
	_navigation.clear()
	var id := 0
	for x in range(-21, 22, 3):
		for z in range(-21, 22, 3):
			var candidate := Vector3(float(x), 0.0, float(z))
			if _clear_path(candidate, candidate + Vector3(0.01, 0.0, 0.01)):
				waypoints.append(candidate)
				_navigation.add_point(id, candidate)
				id += 1
	for a in range(waypoints.size()):
		for b in range(a + 1, waypoints.size()):
			if waypoints[a].distance_to(waypoints[b]) <= 4.5 and _clear_path(waypoints[a], waypoints[b]):
				_navigation.connect_points(a, b)

func is_blocked(point: Vector3, margin: float = 0.35) -> bool:
	if absf(point.x) > 23.2 or absf(point.z) > 23.2:
		return true
	var check := Vector3(point.x, 0.7, point.z)
	for box: AABB in _obstacles:
		var shrunk := box.grow(margin - 0.55)
		if shrunk.has_point(check):
			return true
	return false

func can_traverse(from: Vector3, to: Vector3) -> bool:
	return _clear_path(from, to)

func next_waypoint(from: Vector3, to: Vector3) -> Vector3:
	return bot_navigation(from, to)

func _snap_navigation_target(from: Vector3, to: Vector3) -> Vector3:
	var flat_to := Vector3(to.x, 0.0, to.z)
	if not is_blocked(flat_to, 0.58):
		return flat_to
	var flat_from := Vector3(from.x, 0.0, from.z)
	var best := flat_to
	var best_score := INF
	var to_from := flat_from - flat_to
	var base_angle := atan2(to_from.z, to_from.x) if to_from.length_squared() > 0.001 else 0.0
	for radius in [0.9, 1.5, 2.2, 3.0, 3.8]:
		for step_idx in range(12):
			var angle := base_angle + float(step_idx) * (TAU / 12.0)
			var candidate := Vector3(
				clampf(flat_to.x + cos(angle) * float(radius), -22.5, 22.5),
				0.0,
				clampf(flat_to.z + sin(angle) * float(radius), -22.5, 22.5)
			)
			if is_blocked(candidate, 0.58):
				continue
			var score := candidate.distance_to(flat_to) + candidate.distance_to(flat_from) * 0.25
			if _clear_path(flat_from, candidate):
				score -= 3.0
			if score < best_score:
				best_score = score
				best = candidate
	return best

func bot_navigation(from: Vector3, to: Vector3) -> Vector3:
	var target := _snap_navigation_target(from, to)
	if waypoints.is_empty() or _clear_path(from, target):
		return target
	var start := -1
	var finish := -1
	var start_dist := INF
	var finish_dist := INF
	var fallback_start := 0
	var fallback_finish := 0
	var fallback_start_dist := INF
	var fallback_finish_dist := INF
	var alt_finish := -1
	var alt_finish_dist := INF
	for i in range(waypoints.size()):
		var d_from := from.distance_squared_to(waypoints[i])
		var d_to := target.distance_squared_to(waypoints[i])
		if d_from < fallback_start_dist:
			fallback_start_dist = d_from
			fallback_start = i
		if d_to < fallback_finish_dist:
			fallback_finish_dist = d_to
			fallback_finish = i
		if d_from < start_dist and _clear_path(from, waypoints[i]):
			start_dist = d_from
			start = i
		if d_to < finish_dist and _clear_path(target, waypoints[i]):
			finish_dist = d_to
			finish = i
	if start == -1:
		start = fallback_start
	if finish == -1:
		finish = fallback_finish
	if start == finish and from.distance_to(target) > 1.2:
		for i in range(waypoints.size()):
			if i == start:
				continue
			var d_to := target.distance_squared_to(waypoints[i])
			if d_to < alt_finish_dist and (_clear_path(from, waypoints[i]) or _clear_path(target, waypoints[i])):
				alt_finish_dist = d_to
				alt_finish = i
		if alt_finish != -1:
			finish = alt_finish
	var path := _navigation.get_point_path(start, finish)
	if path.size() > 1:
		for idx in range(1, path.size()):
			if from.distance_to(path[idx]) > 0.35:
				return path[idx]
		return path[1]
	if path.size() == 1 and from.distance_to(path[0]) > 0.35:
		return path[0]
	return target

func _clear_path(from: Vector3, to: Vector3) -> bool:
	var a := Vector3(from.x, 0.7, from.z)
	var b := Vector3(to.x, 0.7, to.z)
	for box: AABB in _obstacles:
		if box.intersects_segment(a, b):
			return false
	return true
