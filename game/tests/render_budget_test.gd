extends SceneTree
## Rendering and construction budgets (CLAUDE_AUDIT_0.3 H-3, H-4, M-12). These are
## structural guarantees, not frame-rate claims; device performance is measured separately.
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const Match = preload("res://scripts/gameplay/match.gd")
const WeaponModel = preload("res://scripts/gameplay/weapon_model.gd")
const CosmeticMaterial = preload("res://scripts/ui/cosmetic_material.gd")
var failures: Array[String] = []
var checks := 0

func _initialize() -> void:
	_run.call_deferred()

func check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

func _meshes(node: Node) -> Array:
	var found: Array = []
	for child in node.find_children("*", "MeshInstance3D", true, false):
		found.append(child.mesh)
	return found

func _run() -> void:
	var world := Node3D.new()
	root.add_child(world)
	var arena := Arena.new()
	world.add_child(arena)
	await physics_frame

	# H-4: invisible detail never enters the shadow passes.
	var stats: Dictionary = arena.presentation_stats
	check(stats.static_batches <= 12, "box geometry shares at most a dozen batches (%d)" % stats.static_batches)
	check(stats.shadow_casting_instances < stats.box_instances * 0.6, "thin and ground-level detail skips shadow passes (%d of %d cast)" % [stats.shadow_casting_instances, stats.box_instances])
	check(not Arena.casts_visible_shadow(Vector3(0.035, 2.75, 0.06), Vector3(0, 1.5, 0)), "sub-6 cm hardware casts no shadow")
	check(not Arena.casts_visible_shadow(Vector3(4.7, 0.002, 36), Vector3(14, 0.014, -2)), "ground resurfacing casts no shadow")
	check(Arena.casts_visible_shadow(Vector3(3.0, 3.1, 9.0), Vector3(-7, 1.55, -11)), "freight container still casts its shadow")
	var label_shadows := 0
	for label in arena.find_children("*", "Label3D", true, false):
		if label.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF:
			label_shadows += 1
	check(label_shadows == 0, "signage text never renders into shadow maps")
	var sun: DirectionalLight3D = arena.find_children("*", "DirectionalLight3D", true, false)[0]
	check(sun.directional_shadow_mode == DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS and sun.directional_shadow_max_distance <= 60.0, "two shadow cascades cover the 48 m yard")
	var tinted := true
	for child in arena.get_children():
		if child is MultiMeshInstance3D:
			tinted = tinted and child.multimesh.use_colors
	check(tinted, "box batches carry albedo per instance")

	# H-3: equips and spawns instantiate shared geometry instead of rebuilding it.
	var first := Node3D.new()
	var second := Node3D.new()
	world.add_child(first)
	world.add_child(second)
	var first_parts: Dictionary = WeaponModel.build(first, "rifle", true)
	var second_parts: Dictionary = WeaponModel.build(second, "rifle", true)
	check(_meshes(first) == _meshes(second) and not _meshes(first).is_empty(), "first-person rifle meshes are shared between builds")
	check(first_parts.paint.size() == 2 and first_parts.magazine != null and first_parts.muzzle != null, "shared build still exposes paint, magazine and muzzle roles")
	check(first_parts.magazine != second_parts.magazine, "each build owns its own animated magazine node")
	check(CosmeticMaterial.finish({}).shader == CosmeticMaterial.finish({"collection": "Obsidian"}).shader, "every cosmetic finish uses one shader program")
	var a := Actor.new()
	a.configure(31, 1, "budget-a")
	world.add_child(a)
	var b := Actor.new()
	b.configure(32, 1, "budget-b")
	world.add_child(b)
	check(_meshes(a._body) == _meshes(b._body), "operators on one side share body meshes")
	check(a._legs.size() == 2 and a._knees.size() == 2 and a._arms.size() == 2 and a._legs[0].position.x < a._legs[1].position.x, "shared body keeps ordered articulated joints")
	check(a._head.mesh is SphereMesh and a._world_muzzle != null and a._head != b._head, "each operator owns its head and muzzle nodes")
	a.team = 0
	a.reset_for_round(Vector3(0, 0.05, 0))
	check(_meshes(a._body) != _meshes(b._body), "side switch swaps to the other side's shared body")
	a.queue_free()
	b.queue_free()
	first.queue_free()
	second.queue_free()
	await physics_frame

	var game := Match.new()
	game.configure({"mode": "offline", "difficulty": "easy"})
	world.add_child(game)
	await physics_frame
	for bot: SBActor in game.actors.values():
		bot.credits = 5000
		bot.inventory.assign(["sidearm"])
	game.round_number = 2
	var started := Time.get_ticks_usec()
	game._begin_round()
	var elapsed_ms := float(Time.get_ticks_usec() - started) / 1000.0
	# Host-dependent; the audited build took ~229 ms here, so a generous bound still
	# catches a return to per-equip geometry construction.
	check(elapsed_ms < 60.0, "round start with nine bot purchases stays under 60 ms (%.1f ms)" % elapsed_ms)
	game.queue_free()
	await physics_frame

	# M-12: the 3D render scale reaches the viewport while the HUD stays native.
	var main = load("res://scripts/main.gd").new()
	root.add_child(main)
	await process_frame
	main.profile.data.settings.render_scale = 0.7
	main.apply_settings()
	check(is_equal_approx(root.scaling_3d_scale, 0.7) and root.scaling_3d_mode == Viewport.SCALING_3D_MODE_BILINEAR, "render scale setting reaches the 3D viewport")
	main.profile.data.settings.render_scale = 1.0
	main.apply_settings()
	main.queue_free()
	world.queue_free()
	await process_frame
	await process_frame
	print("RENDER_BUDGET_TEST checks=%d failures=%d" % [checks, failures.size()])
	quit(0 if failures.is_empty() else 1)
