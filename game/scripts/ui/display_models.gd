class_name DisplayModels
extends RefCounted
## Original armory geometry. Resource ownership remains with the viewport scene.

static func metal(color: Color, roughness := 0.38, metallic := 0.65) -> StandardMaterial3D:
	var result := StandardMaterial3D.new()
	result.albedo_color = color
	result.roughness = roughness
	result.metallic = metallic
	return result

static func box(parent: Node3D, dimensions: Vector3, location: Vector3, material: Material) -> MeshInstance3D:
	var instance := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = dimensions
	instance.mesh = mesh
	instance.material_override = material
	instance.position = location
	parent.add_child(instance)
	return instance

static func cylinder(parent: Node3D, radius: float, height: float, location: Vector3, material: Material) -> MeshInstance3D:
	var instance := MeshInstance3D.new()
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = 16
	instance.mesh = mesh
	instance.material_override = material
	instance.position = location
	parent.add_child(instance)
	return instance

static func build_case(parent: Node3D) -> Node3D:
	var shell := metal(Color("202830"), 0.55, 0.45)
	var rubber := metal(Color("10171b"), 0.88, 0.05)
	var frame := metal(Color("78828b"), 0.28, 0.85)
	var gold := metal(Color("b99a59"), 0.32, 0.7)
	var crimson := metal(Color("8b3040"), 0.46, 0.45)
	box(parent, Vector3(1.84, 0.32, 0.82), Vector3(0, -0.14, 0), shell)
	box(parent, Vector3(1.70, 0.045, 0.69), Vector3(0, 0.03, 0), rubber)
	for side in [-1.0, 1.0]:
		box(parent, Vector3(0.065, 0.37, 0.88), Vector3(side * 0.89, -0.12, 0), frame)
		for z in [-0.4, 0.4]:
			box(parent, Vector3(0.24, 0.15, 0.055), Vector3(side * 0.76, -0.24, z), rubber)
		box(parent, Vector3(0.17, 0.17, 0.055), Vector3(side * 0.58, -0.005, 0.438), gold)
		box(parent, Vector3(0.09, 0.06, 0.07), Vector3(side * 0.58, -0.015, 0.47), rubber)
	box(parent, Vector3(0.38, 0.055, 0.07), Vector3(0, -0.08, 0.49), frame)
	for x in [-0.21, 0.21]:
		box(parent, Vector3(0.04, 0.12, 0.06), Vector3(x, -0.08, 0.46), frame)
	var hinge := Node3D.new()
	hinge.name = "CaseLidHinge"
	hinge.position = Vector3(0, 0.05, -0.4)
	parent.add_child(hinge)
	box(hinge, Vector3(1.84, 0.13, 0.82), Vector3(0, 0.055, 0.4), shell)
	box(hinge, Vector3(1.67, 0.025, 0.66), Vector3(0, 0.131, 0.4), rubber)
	for x in [-0.70, -0.56, 0.56, 0.70]:
		box(hinge, Vector3(0.055, 0.025, 0.56), Vector3(x, 0.15, 0.4), shell)
	box(hinge, Vector3(0.60, 0.015, 0.38), Vector3(0, 0.151, 0.4), crimson)
	box(hinge, Vector3(0.45, 0.009, 0.025), Vector3(0, 0.163, 0.29), gold)
	box(hinge, Vector3(0.12, 0.012, 0.12), Vector3(0, 0.165, 0.40), gold).rotation.y = PI * 0.25
	box(hinge, Vector3(0.035, 0.016, 0.17), Vector3(0, 0.175, 0.40), rubber)
	batch_static(hinge)
	batch_static(parent)
	return hinge

static func build_knife(parent: Node3D) -> void:
	var steel := metal(Color("aab7c1"), 0.23, 0.85)
	var edge := metal(Color("d8e1e4"), 0.17, 0.95)
	var grip := metal(Color("273034"), 0.85, 0.12)
	var gold := metal(Color("a78d59"), 0.38, 0.65)
	# Forged spear tip with an actual center ridge and bevel planes.
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var points := [Vector3(-0.15, 0.10, 0), Vector3(0.95, 0, 0), Vector3(-0.15, -0.10, 0), Vector3(-0.15, 0, 0.055), Vector3(-0.15, 0, -0.055)]
	for triangle in [[0, 3, 1], [3, 2, 1], [4, 0, 1], [2, 4, 1], [0, 4, 3], [3, 4, 2]]:
		for index in triangle:
			surface.add_vertex(points[index])
	surface.generate_normals()
	var blade := MeshInstance3D.new()
	blade.mesh = surface.commit()
	blade.material_override = steel
	parent.add_child(blade)
	box(parent, Vector3(0.07, 0.32, 0.16), Vector3(-0.20, 0, 0), gold)
	box(parent, Vector3(0.61, 0.16, 0.14), Vector3(-0.54, 0, 0), grip)
	box(parent, Vector3(0.08, 0.21, 0.18), Vector3(-0.87, 0, 0), steel)
	var rib := metal(Color("12191c"), 0.92, 0.0)
	for x in [-0.76, -0.65, -0.54, -0.43, -0.32]:
		box(parent, Vector3(0.026, 0.172, 0.15), Vector3(x, 0, 0), rib)
	for x in [-0.71, -0.37]:
		var pin := cylinder(parent, 0.027, 0.155, Vector3(x, 0, 0), edge)
		pin.rotation.x = PI * 0.5
	batch_static(parent)

static func batch_static(parent: Node3D) -> void:
	# Moving lid remains separate. Static parts share one draw per material.
	var groups: Dictionary = {}
	for node in parent.get_children():
		if not node is MeshInstance3D:
			continue
		var key := str(node.material_override.get_instance_id())
		if not groups.has(key):
			var surface := SurfaceTool.new()
			surface.begin(Mesh.PRIMITIVE_TRIANGLES)
			groups[key] = {"surface": surface, "material": node.material_override}
		groups[key].surface.append_from(node.mesh, 0, node.transform)
		parent.remove_child(node)
		node.free()
	for group in groups.values():
		var merged := MeshInstance3D.new()
		merged.mesh = group.surface.commit()
		merged.material_override = group.material
		merged.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		parent.add_child(merged)
