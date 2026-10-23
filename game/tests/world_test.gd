extends SceneTree
## World geometry changes must preserve the competitive route graph and ownership.
const Arena = preload("res://scripts/gameplay/arena.gd")
var checks := 0
var failures: Array[String] = []

func _initialize() -> void: run.call_deferred()
func check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

func run() -> void:
	var arena := Arena.new()
	root.add_child(arena)
	await process_frame
	check(arena._obstacles.size() == 25, "presentation preserves all 25 navigation obstacles")
	check(arena.sites == [Vector3(-15, 0, 10), Vector3(15, 0, 10)], "objective coordinates remain unchanged")
	check(arena.attack_spawns.size() == 5 and arena.defend_spawns.size() == 5, "ten unchanged spawn locations")
	check(arena.waypoints.size() > 100, "walkable route graph remains populated")
	for site in arena.sites:
		for spawn in [arena.attack_spawns[0], arena.defend_spawns[4]]:
			var next: Vector3 = arena.bot_navigation(spawn, site)
			check(next != spawn and next.is_finite(), "spawn can route toward objective")
	check(arena.presentation_stats.box_instances > 1000, "layered architecture and service hardware constructed")
	check(arena.presentation_stats.static_batches < 130, "repeated geometry shares bounded material batches")
	check(arena.get_child_count() < 250, "temporary box parents released after batching")
	var bodies := arena.find_children("*", "StaticBody3D", true, false)
	check(bodies.size() == 26, "decorative improvements add no walkable collision obstacles")
	var roof_supported := arena.roof_equipment_bounds.size() == 6
	for equipment: AABB in arena.roof_equipment_bounds:
		var west := equipment.get_center().x < 0
		var roof := AABB(Vector3(-37.5, 12.0, -22) if west else Vector3(24.5, 9.65, -16), Vector3(13, 0.3, 30 if west else 38))
		var footprint := Rect2(Vector2(roof.position.x, roof.position.z), Vector2(roof.size.x, roof.size.z))
		var unit := Rect2(Vector2(equipment.position.x, equipment.position.z), Vector2(equipment.size.x, equipment.size.z))
		roof_supported = roof_supported and footprint.encloses(unit) and equipment.position.y <= roof.end.y and equipment.end.y >= roof.end.y
	check(roof_supported, "all six air handling units rest on their building roof, with no floating off-edge units")
	var signs_clear := true
	var brand_signs := 0
	var wall_labels_inward := true
	for label: Node in arena.find_children("*", "Label3D", true, false):
		if absf(label.position.x) > 23.0:
			wall_labels_inward = wall_labels_inward and label.basis.z.x * label.position.x < 0
		if label.text.begins_with("SIGHTBREAK"):
			brand_signs += 1
			signs_clear = signs_clear and label.position.y >= 6.0 and label.position.z < 23.22
	check(brand_signs == 1 and signs_clear, "brand header clears loading-door occlusion")
	check(wall_labels_inward, "wall fascia and staff labels face the playable yard instead of mirrored back faces")
	var lights := arena.find_children("*", "Light3D", true, false)
	check(lights.size() == 1, "one directional light with no additive dynamic lighting")
	var world_env: WorldEnvironment = arena.find_children("*", "WorldEnvironment", true, false)[0]
	check(world_env.environment.sky == Arena.RELAY_SKY, "world uses shared retained sky resource")
	var material: StandardMaterial3D = arena._material(Color.WHITE, .85, false, "asphalt")
	check(material.normal_texture.get_width() == 128 and material.roughness_texture.get_width() == 128, "bounded 128px PBR companions")
	check(material.normal_texture.get_image().has_mipmaps() and material.roughness_texture.get_image().has_mipmaps(), "surface companions retain mipmaps against distant aliasing")
	check(material.normal_enabled, "high preset enables shallow surface response")
	arena.apply_detail_quality(false)
	check(not material.normal_enabled and material.roughness_texture == null, "low preset removes optional texture lookups")
	var later: StandardMaterial3D = arena._material(Color("c3d2e1"), .85, false, "metal")
	check(not later.normal_enabled and later.roughness_texture == null, "later created material respects low preset")
	arena.apply_detail_quality(true)
	check(material.normal_enabled and later.normal_enabled and later.roughness_texture != null, "high preset restores map references")
	var transforms_valid := true
	var all_unit_mesh := true
	for child in arena.get_children():
		if child is MultiMeshInstance3D:
			all_unit_mesh = all_unit_mesh and child.multimesh.mesh is BoxMesh and child.multimesh.mesh.size == Vector3.ONE
			for i in range(child.multimesh.instance_count):
				var transform: Transform3D = child.multimesh.get_instance_transform(i)
				transforms_valid = transforms_valid and transform.is_finite() and absf(transform.basis.determinant()) > 0.00000001
	check(transforms_valid, "all fitted and diagonal beam instance transforms finite and nonsingular")
	check(all_unit_mesh, "every box batch shares unit mesh geometry")
	print("WORLD_PRESENTATION_STATS ", JSON.stringify(arena.presentation_stats))
	arena.queue_free()
	await process_frame
	await process_frame
	print("WORLD_TEST ", checks, " checks; ", failures.size(), " failures")
	quit(0 if failures.is_empty() else 1)
