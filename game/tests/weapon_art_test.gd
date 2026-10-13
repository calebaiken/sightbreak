extends SceneTree
## Authored rifle asset contract: nodes the game reads, orientation, budgets and the
## procedural fallback. Presentation only; no gameplay value is read or changed.
const Actor = preload("res://scripts/gameplay/actor.gd")
const WeaponModel = preload("res://scripts/gameplay/weapon_model.gd")
const CosmeticMaterial = preload("res://scripts/ui/cosmetic_material.gd")
const RIFLE_TRIANGLES := 32000
const HAND_TRIANGLES := 10000
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

func _run() -> void:
	for path in [WeaponModel.RELAY_AR, WeaponModel.RELAY_AR_HANDS, WeaponModel.RELAY_AR_MATERIAL, WeaponModel.RELAY_AR_HANDS_MATERIAL]:
		check(ResourceLoader.exists(path), "authored asset present: " + path)
	var rifle := WeaponModel._authored_nodes(WeaponModel.RELAY_AR, Transform3D.IDENTITY)
	for node in ["body", "paint_receiver", "paint_handguard", "magazine", "magazine_rounds", "muzzle", "ejection", "grip_hand", "support_hand"]:
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
	var expected_port: Vector3 = (Transform3D(Basis.from_euler(WeaponModel.relay_ar_rotation), WeaponModel.relay_ar_offset) * Transform3D(Basis.IDENTITY, rifle.anchors["ejection"])).origin
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

	var upright := Node3D.new()
	root.add_child(upright)
	var inspection: Dictionary = WeaponModel.build(upright, "rifle", false)
	var body_node: MeshInstance3D = upright.get_node("body")
	check(body_node.transform.basis.is_equal_approx(Basis.IDENTITY) and absf(inspection.muzzle.position.x) < 0.001, "inspection rifle is upright and on axis, without the viewmodel cant")
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
	actor.queue_free()
	holder.queue_free()
	fallback.queue_free()
	await process_frame
	print("WEAPON_ART_TEST checks=%d failures=%d" % [checks, failures.size()])
	quit(0 if failures.is_empty() else 1)
