extends SceneTree
## Authored rifle asset contract: nodes the game reads, orientation, budgets and the
## procedural fallback. Presentation only; no gameplay value is read or changed.
const Actor = preload("res://scripts/gameplay/actor.gd")
const WeaponModel = preload("res://scripts/gameplay/weapon_model.gd")
const CosmeticMaterial = preload("res://scripts/ui/cosmetic_material.gd")
const ViewmodelShading = preload("res://scripts/gameplay/viewmodel_shading.gd")
const INSPECTOR = preload("res://scripts/ui/item_inspector.gd")
const REVEAL = preload("res://scripts/ui/case_reveal.gd")
const SKIN := {"id": "art-fixture", "kind": "weapon_skin", "collection": "Crimson Archive", "rarity": "Legendary", "pattern_seed": 897, "wear": 0.2}
const RIFLE_TRIANGLES := 32000
const HAND_TRIANGLES := 10000
const ARMS_TRIANGLES := 10000
const ARMS_BONES := 34
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	_run.call_deferred()

func check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

func _triangles(mesh: Mesh) -> int:
	var total := 0
	for surface in range(mesh.get_surface_count()):
		var indices: PackedInt32Array = mesh.surface_get_arrays(surface)[Mesh.ARRAY_INDEX]
		total += indices.size() / 3 if not indices.is_empty() else mesh.surface_get_array_len(surface) / 3
	return total

func _texture_ok(path: String, limit: int) -> bool:
	var texture: Texture2D = load(path)
	return texture != null and texture.get_width() <= limit and texture.get_width() == texture.get_height() and is_equal_approx(log(texture.get_width()) / log(2.0), roundf(log(texture.get_width()) / log(2.0)))

## Meshes under node whose shader writes POSITION without the viewmodel projection set.
## Writing POSITION makes the engine skip its own vertex transform, so such a mesh is
## drawn wrongly or not at all; only first-person materials may do it.
func _vertex_overrides(node: Node) -> Array[String]:
	var found: Array[String] = []
	for mesh: MeshInstance3D in node.find_children("*", "MeshInstance3D", true, false):
		var materials: Array[Material] = [mesh.material_override]
		for surface in range(mesh.get_surface_override_material_count()):
			materials.append(mesh.get_surface_override_material(surface))
			if mesh.mesh != null:
				materials.append(mesh.mesh.surface_get_material(surface))
		for material in materials:
			if material is ShaderMaterial and (material as ShaderMaterial).shader != null and (material as ShaderMaterial).shader.code.contains("POSITION"):
				var fov = (material as ShaderMaterial).get_shader_parameter("viewmodel_fov")
				if fov == null or float(fov) <= 0.0:
					found.append(String(mesh.name))
	return found

## Names of the meshes under node, split by the projection their material draws with.
func _projections(node: Node) -> Dictionary:
	var split := {"viewmodel": [] as Array[String], "camera": [] as Array[String]}
	for mesh: MeshInstance3D in node.find_children("*", "MeshInstance3D", true, false):
		var material := mesh.material_override
		var fov = (material as ShaderMaterial).get_shader_parameter("viewmodel_fov") if material is ShaderMaterial else null
		split["viewmodel" if fov != null and float(fov) > 0.0 else "camera"].append(String(mesh.name))
	return split

## Whether node holds the merged glove-and-sleeve mesh of the procedural hands.
func _has_fabric(node: Node) -> bool:
	for mesh: MeshInstance3D in node.find_children("*", "MeshInstance3D", true, false):
		var material := mesh.material_override
		if material is StandardMaterial3D and (material as StandardMaterial3D).vertex_color_use_as_albedo and (material as StandardMaterial3D).roughness > 0.9:
			return true
		if material is ShaderMaterial and float((material as ShaderMaterial).get_shader_parameter("roughness") if (material as ShaderMaterial).get_shader_parameter("roughness") != null else 0.0) > 0.9:
			return true
	return false

## A point as a fraction of a 16:9 frame through the viewmodel projection (the shipped
## "keep" aspect), independent of the test's window size.
func _viewmodel_screen(camera: Camera3D, point: Vector3) -> Vector2:
	var q := camera.global_transform.affine_inverse() * point
	var t := tan(deg_to_rad(ViewmodelShading.FOV) * 0.5)
	return Vector2(0.5 + 0.5 * (q.x / -q.z) / (t * 16.0 / 9.0), 0.5 - 0.5 * (q.y / -q.z) / t)

func _run() -> void:
	for path in [WeaponModel.RELAY_AR, WeaponModel.RELAY_AR_HANDS, WeaponModel.RELAY_AR_MATERIAL, WeaponModel.RELAY_AR_HANDS_MATERIAL]:
		check(ResourceLoader.exists(path), "authored asset present: " + path)
	var rifle := WeaponModel._authored_nodes(WeaponModel.RELAY_AR, Transform3D.IDENTITY)
	for node in ["body", "paint_receiver", "paint_handguard", "magazine", "magazine_rounds", "stock", "muzzle", "ejection", "grip_hand", "support_hand"]:
		check(rifle.markers.has(node), "rifle exports node " + node)
	var muzzle: Vector3 = rifle.anchors["muzzle"]
	check(muzzle.z < -0.6 and absf(muzzle.x) < 0.001 and absf(muzzle.y - 0.025) < 0.002, "barrel runs along -Z with the bore at 0.025 m")
	var body_box: AABB = (rifle.meshes["body"] as Mesh).get_aabb()
	check(muzzle.z <= body_box.position.z + 0.002, "muzzle marker sits at the front of the model")
	check(rifle.anchors["ejection"].x > 0.015, "ejection port is on the right side")
	var magazine_top: Vector3 = rifle.anchors["magazine"]
	check((rifle.meshes["magazine"] as Mesh).get_aabb().end.y <= 0.02 and magazine_top.y > -0.01, "magazine pivot is at its seated top")
	var rifle_triangles := 0
	for mesh_name in rifle.meshes:
		rifle_triangles += _triangles(rifle.meshes[mesh_name])
	check(rifle_triangles > 5000 and rifle_triangles <= RIFLE_TRIANGLES, "rifle within %d triangles (%d)" % [RIFLE_TRIANGLES, rifle_triangles])
	var hands := WeaponModel._authored_nodes(WeaponModel.RELAY_AR_HANDS, Transform3D.IDENTITY)
	check(hands.meshes.has("hands") and _triangles(hands.meshes["hands"]) <= HAND_TRIANGLES, "hands are one mesh within %d triangles" % HAND_TRIANGLES)
	for prefix in ["relay_ar", "relay_ar_hands"]:
		for map in ["albedo", "orm", "normal"]:
			check(_texture_ok("res://assets/weapons/relay_ar/%s_%s.png" % [prefix, map], 1024), "%s %s is square, power of two, at most 1024" % [prefix, map])
	# The magazine is pulled out of the magwell by reload, so the occlusion on its faces must be
	# its own: baked with it seated, the faces that were inside the well were fully occluded and
	# were black as soon as it came out (23 % of its vertices had occlusion below 0.1).
	var orm_image: Image = (load(WeaponModel.RELAY_AR_ORM) as Texture2D).get_image()
	if orm_image.is_compressed():
		orm_image.decompress()
	var magazine_arrays: Array = (rifle.meshes["magazine"] as Mesh).surface_get_arrays(0)
	var magazine_uvs: PackedVector2Array = magazine_arrays[Mesh.ARRAY_TEX_UV]
	var occluded := 0
	var occlusion_total := 0.0
	for uv in magazine_uvs:
		var texel := orm_image.get_pixelv(Vector2i(clampi(int(uv.x * orm_image.get_width()), 0, orm_image.get_width() - 1), clampi(int(uv.y * orm_image.get_height()), 0, orm_image.get_height() - 1)))
		occlusion_total += texel.r
		if texel.r < 0.1:
			occluded += 1
	check(float(occluded) / magazine_uvs.size() <= 0.10, "the magazine's baked occlusion is its own: %.1f %% of its vertices are almost fully occluded (limit 10 %%)" % (100.0 * occluded / magazine_uvs.size()))
	check(occlusion_total / magazine_uvs.size() >= 0.70, "the magazine's mean baked occlusion is at least 0.70 (%.3f)" % (occlusion_total / magazine_uvs.size()))
	var material: ORMMaterial3D = load(WeaponModel.RELAY_AR_MATERIAL)
	check(material.albedo_texture != null and material.orm_texture != null and material.normal_enabled and material.normal_texture != null, "rifle material binds albedo, ORM and normal maps")

	# Built through the same path as the game: roles, batching budget, finish detail.
	var holder := Node3D.new()
	root.add_child(holder)
	var parts: Dictionary = WeaponModel.build(holder, "rifle", true)
	check(parts.paint.size() == 2 and parts.magazine != null and parts.muzzle != null, "authored rifle exposes paint, magazine and muzzle roles")
	check(holder.get_child_count() <= 6, "first-person rifle with hands is at most six draw nodes (%d)" % holder.get_child_count())
	check(parts.magazine.get_child_count() == 1, "cartridge follows the magazine")
	check(parts.muzzle.position.distance_to(parts.magazine.position) > 0.3, "muzzle flash sits at the authored muzzle")
	var base := Transform3D(Basis.from_euler(WeaponModel.relay_ar_rotation).scaled(Vector3.ONE * WeaponModel.relay_ar_scale), WeaponModel.relay_ar_offset)
	var pivot: Vector3 = base * WeaponModel.RELAY_AR_PIVOT
	check(parts.pivot is Vector3 and parts.pivot.distance_to(pivot) < 0.001, "the model reports its balance point as the weapon node's pivot")
	var expected_port: Vector3 = base * (rifle.anchors["ejection"] as Vector3) - pivot
	check(parts.ejection is Vector3 and parts.ejection.distance_to(expected_port) < 0.001, "casings leave from the authored ejection port")
	for part: MeshInstance3D in parts.paint:
		check(part.has_meta("detail_orm") and part.has_meta("detail_normal"), "paint part carries baked detail: " + part.name)
	var finish := CosmeticMaterial.finish({"collection": "Obsidian", "pattern_seed": 12, "wear": 0.3})
	CosmeticMaterial.apply(finish, parts.paint)
	check(finish.get_shader_parameter("detail") == 1.0 and finish.get_shader_parameter("detail_orm") != null, "cosmetic finish keeps baked occlusion and normals")
	check(parts.paint[0].material_override == finish and parts.paint[1].material_override == finish, "one finish material covers both paint parts")
	var plain := CosmeticMaterial.finish({})
	CosmeticMaterial.apply(plain, [])
	check(plain.get_shader_parameter("detail") == null or plain.get_shader_parameter("detail") == 0.0, "finishes without authored parts leave detail at its 0 default")
	var unskinned := CosmeticMaterial.finish({})
	CosmeticMaterial.apply(unskinned, parts.paint)
	check(unskinned.get_shader_parameter("patterned") == 0.0 and unskinned.get_shader_parameter("detail_albedo") != null, "without a skin the authored receiver shows its baked surface")

	var upright := Node3D.new()
	root.add_child(upright)
	var inspection: Dictionary = WeaponModel.build(upright, "rifle", false)
	var body_node: MeshInstance3D = upright.get_node("body")
	check(body_node.transform.basis.is_equal_approx(Basis.IDENTITY) and absf(inspection.muzzle.position.x) < 0.001, "inspection rifle is upright and on axis, without the viewmodel cant")
	check(upright.has_node("stock") and not upright.has_node("hands"), "inspection keeps the buttstock and has no hands")
	check(_projections(upright).viewmodel.is_empty(), "inspection draws every mesh with the camera's projection")
	upright.queue_free()

	# The procedural rifle remains a complete fallback.
	WeaponModel.use_authored = false
	var fallback := Node3D.new()
	root.add_child(fallback)
	var procedural: Dictionary = WeaponModel.build(fallback, "rifle", true)
	check(procedural.paint.size() == 2 and procedural.magazine != null and procedural.muzzle != null and _triangles(procedural.paint[0].mesh) < 2000, "procedural rifle still builds when authored assets are off")
	WeaponModel.use_authored = true

	# In an actor: reload still extracts and reseats the authored magazine.
	var actor := Actor.new()
	actor.configure(7, 0, "Art fixture", true)
	root.add_child(actor)
	actor.reset_for_round(Vector3.ZERO)
	actor.credits = 5000
	actor.buy_weapon("rifle")
	check(actor._magazine != null and actor._magazine.name == "magazine", "actor holds the authored magazine")
	check(actor._ejection_point != Vector3.INF, "actor ejects casings from the model's port")
	actor.reload_remaining = 1.25
	actor.tick_visual(0.016)
	check(actor._magazine.position.y < actor._magazine_rest.y - 0.05, "reload extracts the authored magazine")
	actor.reload_remaining = 0
	actor.tick_visual(0.016)
	check(actor._magazine.position == actor._magazine_rest, "reload completion reseats it")

	# Rest pose is independent of the pivot: a model point lands where the placement alone puts it.
	actor._equip_blend = 0.0
	actor._kick = 0.0
	actor.reload_remaining = 0
	actor.tick_visual(0.016)
	var rest_point: Vector3 = actor._gun.global_transform * (actor._gun.get_node("body") as Node3D).transform * Vector3(0, 0, 0.1)
	var camera_point: Vector3 = actor.camera.global_transform.affine_inverse() * rest_point
	var expected_camera_point: Vector3 = Actor.GUN_REST + base * Vector3(0, 0, 0.1)
	check(camera_point.distance_to(expected_camera_point) < 0.002, "moving the pivot leaves the rest pose where the fitted placement put it")

	# The buttstock is behind the camera in first person, so the viewmodel leaves it out
	# (it would sweep into the frame during reload and equip, and at wider aspects).
	check(not actor._gun.has_node("stock") and actor._gun.get_node("body").mesh.get_aabb().end.z < 0.22, "first person omits the buttstock")

	# Rigged arms: one skinned mesh, the skeleton and the reload clip the actor seeks.
	check(actor._gun.has_node("arms") and not actor._gun.has_node("hands"), "first person uses the rigged arms")
	var skeleton: Skeleton3D = actor._arms_skeleton
	var player: AnimationPlayer = actor._arms_player
	check(skeleton != null and skeleton.get_bone_count() == ARMS_BONES and skeleton.find_bone("L_hand") >= 0 and skeleton.find_bone("R_index_3") >= 0, "arms skeleton has both arms' %d bones" % ARMS_BONES)
	var arms_mesh: MeshInstance3D = actor._gun.get_node("arms").find_children("*", "MeshInstance3D", true, false).front()
	check(arms_mesh.skin != null and _triangles(arms_mesh.mesh) <= ARMS_TRIANGLES, "arms are one skinned mesh within %d triangles (%d)" % [ARMS_TRIANGLES, _triangles(arms_mesh.mesh)])
	for map in ["albedo", "orm", "normal"]:
		check(_texture_ok("res://assets/weapons/relay_ar/relay_ar_arms_%s.png" % map, 1024), "arms %s is square, power of two, at most 1024" % map)
	check(player != null and player.has_animation("reload") and is_equal_approx(player.get_animation("reload").length, 1.0), "the reload clip is one second long, seeked by reload progress")
	# Viewmodel drawing: first person uses the narrower projection, inspection does not.
	check(arms_mesh.material_override is ShaderMaterial and arms_mesh.material_override.get_shader_parameter("viewmodel_fov") == ViewmodelShading.FOV, "arms draw with the viewmodel projection")
	check((actor._gun.get_node("body") as MeshInstance3D).material_override.get_shader_parameter("viewmodel_fov") == ViewmodelShading.FOV and actor._finish.get_shader_parameter("viewmodel_fov") == ViewmodelShading.FOV, "rifle body and finish draw with the viewmodel projection in first person")
	var inspected := Node3D.new()
	root.add_child(inspected)
	WeaponModel.build(inspected, "rifle", false)
	check((inspected.get_node("body") as MeshInstance3D).material_override is ORMMaterial3D, "inspection keeps the plain material and the world projection")
	inspected.queue_free()
	# The shared cosmetic finish: inspection, the case reveal and procedural first-person
	# weapons use the world variant, which leaves the vertex transform to the engine.
	check(not CosmeticMaterial.shader().code.contains("POSITION") and CosmeticMaterial.shader(true).code.contains("POSITION"), "only the first-person cosmetic variant overrides the vertex position")
	check(actor._finish.shader == CosmeticMaterial.shader(true) and _vertex_overrides(actor._gun).is_empty(), "first-person rifle: every position override has the viewmodel projection")
	var inspector := INSPECTOR.new()
	root.add_child(inspector)
	inspector.show_item(SKIN)
	var inspector_paint: Array[String] = _vertex_overrides(inspector)
	check(inspector.finish_material.shader == CosmeticMaterial.shader() and inspector_paint.is_empty(), "inspection draws its paint parts with the engine's transform %s" % [inspector_paint])
	inspector.queue_free()
	var reveal := REVEAL.new()
	reveal.committed_item = SKIN.duplicate(true)
	root.add_child(reveal)
	await process_frame
	reveal.skip()
	var reveal_paint: Array[String] = _vertex_overrides(reveal)
	check(reveal_paint.is_empty(), "the case reveal draws its reward with the engine's transform %s" % [reveal_paint])
	reveal.queue_free()
	var sidearm := Actor.new()
	sidearm.configure(8, 0, "Procedural fixture", true)
	root.add_child(sidearm)
	sidearm.reset_for_round(Vector3(4, 0, 0))
	sidearm.apply_cosmetic(SKIN)
	var sidearm_paint: Array[String] = _vertex_overrides(sidearm._gun)
	check(sidearm.weapon_id == "sidearm" and not sidearm._viewmodel and sidearm._paint_parts.size() > 0 and sidearm._finish.shader == CosmeticMaterial.shader() and sidearm_paint.is_empty(), "procedural first-person sidearm keeps the world finish %s" % [sidearm_paint])
	sidearm.queue_free()
	# The clip: the support hand leaves the handguard for the magazine, follows it down
	# its well and returns exactly to the hold. Positions are in the skeleton's space.
	var hand := skeleton.find_bone("L_hand")
	var hold: Vector3 = skeleton.get_bone_global_pose(hand).origin
	var reload_time: float = 2.25
	actor.reload_remaining = reload_time * (1.0 - 0.45)
	actor.tick_visual(0.016)
	var low: Vector3 = skeleton.get_bone_global_pose(hand).origin
	check(low.y < hold.y - 0.15, "mid-reload the support hand is down with the magazine (%.2f m below the hold)" % (hold.y - low.y))
	var magazine_drop: Vector3 = actor._magazine.position - actor._magazine_rest
	check(magazine_drop.length() > 0.15 and absf((actor._magazine.basis.inverse() * magazine_drop).normalized().y + 1.0) < 0.001, "the magazine drops straight down its own well")
	# Staging: the support hand and the whole magazine are in frame when the hand takes
	# the magazine and when it seats it (they leave the frame only mid-swap).
	var magazine_box: AABB = actor._magazine.mesh.get_aabb()
	for progress in [0.14, 0.84]:
		actor.reload_remaining = reload_time * (1.0 - progress)
		actor.tick_visual(0.016)
		var wrist := _viewmodel_screen(actor.camera, skeleton.global_transform * skeleton.get_bone_global_pose(hand).origin)
		var bottom := _viewmodel_screen(actor.camera, actor._magazine.global_transform * Vector3(magazine_box.get_center().x, magazine_box.position.y, magazine_box.get_center().z))
		check(wrist.x > 0.02 and wrist.x < 0.98 and wrist.y < 0.95 and bottom.x > 0.02 and bottom.x < 0.98 and bottom.y < 0.98, "at %d %% of the reload the support hand and magazine are in frame (wrist %s, magazine bottom %s)" % [roundi(progress * 100), wrist, bottom])
		var tube_end := _viewmodel_screen(actor.camera, (actor._gun.get_node("body") as Node3D).global_transform * Vector3(0, 0.025, 0.205))
		check(tube_end.x > 1.0 or tube_end.y > 1.0, "the buffer tube's end face stays out of frame at %d %% (%s)" % [roundi(progress * 100), tube_end])
	# Every vertex of the magazine, not just its bottom centre, stays in frame through the
	# grab and the seat, with a margin of 1 % of the frame (the review of 64ec598 measured
	# 36 vertices 2.8 px below a 720 px frame at 15 %).
	var magazine_vertices: PackedVector3Array = actor._magazine.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
	for progress in [0.12, 0.13, 0.14, 0.15, 0.82, 0.84, 0.86, 0.88]:
		actor.reload_remaining = 0
		actor.tick_visual(0.016)
		actor.reload_remaining = reload_time * (1.0 - progress)
		actor.tick_visual(0.016)
		var extent := Rect2(_viewmodel_screen(actor.camera, actor._magazine.global_transform * magazine_vertices[0]), Vector2.ZERO)
		for vertex in magazine_vertices:
			extent = extent.expand(_viewmodel_screen(actor.camera, actor._magazine.global_transform * vertex))
		check(extent.position.x > 0.01 and extent.end.x < 0.99 and extent.end.y < 0.99, "at %d %% of the reload every magazine vertex is in frame (%s)" % [roundi(progress * 100), extent])
	# The held reload pose rises toward the centre but leaves the crosshair clear.
	actor.reload_remaining = reload_time * 0.5
	actor.tick_visual(0.016)
	var held_muzzle := _viewmodel_screen(actor.camera, (actor._gun.get_node("body") as Node3D).global_transform * Vector3(0, 0.025, -0.676))
	check(held_muzzle.x > 0.55, "mid-reload the muzzle stays right of the crosshair (%s)" % held_muzzle)
	actor.reload_remaining = 0
	actor.tick_visual(0.016)
	check(skeleton.get_bone_global_pose(hand).origin.distance_to(hold) < 0.001, "after the reload the support hand is back on the handguard")
	# Online clients receive the reload timer at the snapshot rate (20 Hz). The pose follows
	# a presentation clock that moves every visual tick and stays within one slack of the
	# authoritative timer, which it never writes.
	var clip_times: Array[float] = []
	var authoritative := reload_time
	var worst_gap := 0.0
	for tick in 120:
		if tick % 3 == 0:
			authoritative = maxf(0.0, reload_time - tick / 60.0)
		actor.reload_remaining = authoritative
		actor.tick_visual(1.0 / 60.0)
		if tick == 60:
			check(actor.reload_remaining == authoritative, "the reload pose never writes the authoritative timer")
		clip_times.append(actor._arms_time)
		worst_gap = maxf(worst_gap, absf(actor._reload_clock - authoritative))
	var changes := 0
	var backwards := 0
	for i in range(1, clip_times.size()):
		if clip_times[i] != clip_times[i - 1]: changes += 1
		if clip_times[i] < clip_times[i - 1]: backwards += 1
	check(changes >= 115 and backwards == 0, "at a 20 Hz snapshot rate the reload pose advances every visual tick (%d changes in 119 ticks, %d backwards)" % [changes, backwards])
	check(worst_gap <= actor.RELOAD_VISUAL_SLACK + 0.0001, "the pose clock stays within %.2f s of the authoritative timer (worst %.3f s)" % [actor.RELOAD_VISUAL_SLACK, worst_gap])
	actor.reload_remaining = 0
	actor.tick_visual(1.0 / 60.0)
	check(actor._arms_time == 0.0, "a cancelled reload returns the hands to the hold at once")
	check(ResourceLoader.has_cached(WeaponModel.RELAY_AR_ARMS), "the rigged arms scene stays loaded between equips")
	# Trigger: the index finger curls with the kick and relaxes after it.
	var index := skeleton.find_bone("R_index_2")
	var rest_pose: Quaternion = skeleton.get_bone_pose_rotation(index)
	actor._kick = 1.0
	actor.tick_visual(0.001)
	var pulled: Quaternion = skeleton.get_bone_pose_rotation(index)
	check(rest_pose.angle_to(pulled) > 0.2, "firing curls the trigger finger (%.2f rad)" % rest_pose.angle_to(pulled))
	actor._kick = 0.0
	actor.tick_visual(0.016)
	check(rest_pose.angle_to(skeleton.get_bone_pose_rotation(index)) < 0.01, "the trigger finger returns to rest")
	actor.queue_free()
	# Without the rigged arms the static hands remain the fallback.
	WeaponModel.use_rigged_arms = false
	var static_hands := Node3D.new()
	root.add_child(static_hands)
	var fallback_hands: Dictionary = WeaponModel.build(static_hands, "rifle", true)
	check(static_hands.has_node("hands") and not static_hands.has_node("arms") and fallback_hands.arms_player == null, "static hands remain the fallback without the rigged arms")
	static_hands.queue_free()
	WeaponModel.use_rigged_arms = true
	# One projection per first-person build. The authored rifle and whichever hands it has
	# (rigged arms, the static hands, or procedural gloves when no hand asset is used) draw
	# with the viewmodel projection; procedural weapons and their gloves keep the camera's.
	# The static hands once kept the camera's 82 degrees beside the rifle's 54 and drew
	# detached from it (review of 64ec598).
	for variant in [["rifle", true, true, true], ["rifle", true, false, true], ["rifle", true, true, false], ["rifle", false, true, true], ["sidearm", true, true, true], ["smg", true, true, true], ["marksman", true, true, true]]:
		WeaponModel.use_authored = variant[1]
		WeaponModel.use_rigged_arms = variant[2]
		WeaponModel.use_hand_assets = variant[3]
		var build_holder := Node3D.new()
		root.add_child(build_holder)
		var built: Dictionary = WeaponModel.build(build_holder, variant[0], true)
		var split := _projections(build_holder)
		var context := "first-person %s (authored %s, rigged arms %s, hand assets %s)" % variant
		var authored_rifle: bool = variant[0] == "rifle" and variant[1]
		check(built.viewmodel == authored_rifle, context + " reports its projection")
		if authored_rifle:
			check(split.camera.is_empty(), context + ": every mesh draws with the viewmodel projection (camera projection: %s)" % [split.camera])
		else:
			check(split.viewmodel.is_empty(), context + ": every mesh draws with the camera's projection (viewmodel: %s)" % [split.viewmodel])
		var hands_drawn := _has_fabric(build_holder)
		if authored_rifle and variant[3]:
			hands_drawn = build_holder.has_node("arms") if variant[2] else build_holder.has_node("hands")
		check(hands_drawn, context + " draws its hands")
		build_holder.queue_free()
	WeaponModel.use_authored = true
	WeaponModel.use_rigged_arms = true
	WeaponModel.use_hand_assets = true
	holder.queue_free()
	fallback.queue_free()
	await process_frame
	print("WEAPON_ART_TEST checks=%d failures=%d" % [checks, failures.size()])
	quit(0 if failures.is_empty() else 1)
