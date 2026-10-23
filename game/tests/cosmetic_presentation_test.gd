extends SceneTree
## Presentation-only regressions; transaction authority remains in backend tests.
const UI = preload("res://scripts/ui/economy_ui.gd")
const INSPECTOR = preload("res://scripts/ui/item_inspector.gd")
const REVEAL = preload("res://scripts/ui/case_reveal.gd")
const FINISH = preload("res://scripts/ui/cosmetic_material.gd")
var failures := 0
var assertions := 0

func _initialize() -> void:
	call_deferred("run")

func check(value: bool, description: String) -> void:
	assertions += 1
	if not value:
		failures += 1
		push_error(description)

func run() -> void:
	var metadata := {"id": "committed-instance", "kind": "weapon_skin", "collection": "Crimson Archive", "rarity": "Legendary", "pattern_seed": 897, "wear": 0.2}
	var reveal := REVEAL.new()
	reveal.committed_item = metadata.duplicate(true)
	root.add_child(reveal)
	await process_frame
	check(reveal.world.own_world_3d, "Studio has isolated 3D world")
	check(reveal.world.msaa_3d == Viewport.MSAA_2X and reveal.world.size.x <= 1024 and reveal.world.size.y <= 512, "Studio uses bounded mobile rendering scale")
	check(reveal.lid is Node3D and reveal.reward is Node3D, "Case hinge and committed reward are actual 3D nodes")
	check(reveal.world.find_children("*", "Light3D", true, false).size() == 3, "Studio lighting is bounded at three lights")
	var env: WorldEnvironment = reveal.world.find_children("*", "WorldEnvironment", true, false)[0]
	check(env.environment.sky == null, "Inspector allocates no sky resources")
	check(not reveal.reward.visible, "Committed weapon remains hidden before opening")
	reveal.progress = 0.8
	check(reveal.lid.rotation.x < -1 and reveal.reward.visible, "Opening animates physical lid and reward lift")
	var events := [0]
	reveal.finished.connect(func(): events[0] += 1)
	reveal.skip()
	reveal.skip()
	check(events[0] == 1 and reveal.revealed, "Skip reveals once")
	check(reveal.committed_item == metadata and reveal.item == metadata, "Presentation preserves exact server instance metadata")
	check(is_equal_approx(float(reveal.finish_material.get_shader_parameter("wear")), 0.2), "Wear derives from server metadata")
	check(reveal.finish_material.get_shader_parameter("pattern_seed") == 897.0, "Pattern derives from server metadata")
	check(reveal.rarity_light.light_color == FINISH.rarity_color("Legendary"), "Rarity illumination corresponds only to committed rarity")
	var reveal_ref: WeakRef = weakref(reveal)
	reveal.queue_free()
	await process_frame
	await process_frame
	check(reveal_ref.get_ref() == null, "Closing reveal frees viewport scene owner")
	var inspector := INSPECTOR.new()
	inspector.item = {"name": "K-4 / Field knife", "kind": "knife_reference"}
	root.add_child(inspector)
	await process_frame
	check(inspector.pivot.get_child_count() >= 4 and inspector.pivot.get_child_count() <= 8, "Knife reference is actual multi-part 3D mesh")
	check(not inspector.item.has("id"), "Knife reference cannot masquerade as owned instance")
	var indexed_blade_tip := false
	var outward_blade_face := false
	for mesh in inspector.pivot.get_children():
		if not mesh is MeshInstance3D:
			continue
		var arrays: Array = mesh.mesh.surface_get_arrays(0)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
		var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
		for offset in range(0, indices.size(), 3):
			var a: Vector3 = vertices[indices[offset]]
			var b: Vector3 = vertices[indices[offset + 1]]
			var c: Vector3 = vertices[indices[offset + 2]]
			if maxf(a.x, maxf(b.x, c.x)) > 0.9:
				indexed_blade_tip = true
				if (b - a).cross(c - a).z < 0 and normals[indices[offset]].z > 0:
					outward_blade_face = true
	check(indexed_blade_tip, "Batched blade tip remains referenced by triangle indices")
	check(outward_blade_face, "Blade front uses Godot clockwise winding and outward normal")
	var press := InputEventScreenTouch.new()
	press.pressed = true
	press.index = 0
	press.position = Vector2(100, 100)
	inspector._gui_input(press)
	press.index = 1
	press.position = Vector2(200, 100)
	inspector._gui_input(press)
	var drag := InputEventScreenDrag.new()
	drag.index = 1
	drag.position = Vector2(240, 100)
	drag.relative = Vector2(40, 0)
	var rotation_before := inspector.pivot.rotation
	inspector._gui_input(drag)
	check(inspector.distance < 3.5 and inspector.pivot.rotation == rotation_before, "Two-finger spread zooms without rotating the inspected item")
	inspector._notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	check(inspector.touch_points.is_empty() and not inspector.dragging, "Focus loss clears inspector touch ownership")
	inspector.queue_free()
	await process_frame
	var ui := UI.new()
	root.add_child(ui)
	await process_frame
	ui.api.player_id = "self"
	ui.listings = [{"id": "high", "seller_id": "self", "price": 90, "item": {"name": "Crimson", "rarity": "Epic"}}, {"id": "low", "seller_id": "other", "price": 40, "item": {"name": "Obsidian", "rarity": "Common"}}]
	var original := ui.listings.duplicate(true)
	check(ui._filtered_listings()[0].id == "low", "Marketplace defaults to ascending actual price")
	ui.market_sort = 1
	check(ui._filtered_listings()[0].id == "high", "Descending sort changes presentation")
	ui.market_mine_only = true
	check(ui._filtered_listings().size() == 1 and ui._filtered_listings()[0].seller_id == "self", "My listings filter preserves seller identity")
	ui.market_mine_only = false
	ui.market_filter = "epic"
	check(ui._filtered_listings().size() == 1, "Market filtering matches rarity without API mutation")
	check(ui.listings == original, "Filtering never mutates authoritative transaction objects")
	check(ui.inventory.is_empty(), "Reference display never creates inventory ownership")
	check(ui._matches_filter({"collection": "Obsidian"}, "obsidian"), "Inventory filtering is case insensitive")
	ui.queue_free()
	await process_frame
	print("Cosmetic presentation: %d assertions / %d failures" % [assertions, failures])
	quit(0 if failures == 0 else 1)
