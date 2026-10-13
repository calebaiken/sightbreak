extends SceneTree
## Smoke presentation must never change who can see whom (CLAUDE_AUDIT_0.3 visual
## work on the 0.3 "spherical smoke" defect). Appearance is reviewed in captures.
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const Utility = preload("res://scripts/gameplay/utility.gd")
var failures: Array[String] = []
var checks := 0

func _initialize() -> void:
	_run.call_deferred()

func check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

func _run() -> void:
	var world := Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	await physics_frame
	# Geometry: every lobe (plus shader billow) stays inside bot concealment.
	var farthest := 0.0
	var vertices: PackedVector3Array = Utility.smoke_core_mesh().surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
	for vertex in vertices:
		farthest = maxf(farthest, vertex.length())
	check(farthest + 0.15 <= Utility.CONCEALMENT_RADIUS, "visible core stays inside the bot concealment radius (%.2f m)" % (farthest + 0.15))
	check(Utility.smoke_core_mesh() == Utility.smoke_core_mesh(), "all clouds share one core mesh")
	for layout: Array in Utility.PUFF_LAYOUT:
		var bottom: float = Utility.CLOUD_HEIGHT + layout[0].y - layout[1].y * 0.5
		check(bottom >= -0.06, "edge puff ends at or above the ground (%.2f m)" % bottom)
	var shooter := Actor.new()
	shooter.configure(1, 0, "smoke-shooter")
	world.add_child(shooter)
	shooter.reset_for_round(Vector3(0, 0.05, -15))
	var target := Actor.new()
	target.configure(2, 1, "smoke-target")
	world.add_child(target)
	target.reset_for_round(Vector3(0, 0.05, -9))
	await physics_frame
	await physics_frame
	for high in [true, false]:
		Utility.high_quality_smoke = high
		var smoke := Utility.new()
		smoke.kind = "smoke"
		world.add_child(smoke)
		smoke.global_position = Vector3(0, 0.3, -12)
		smoke._detonate()
		var core: MeshInstance3D = smoke._cloud_puffs[0]
		check(core.mesh == Utility.smoke_core_mesh(), "%s preset keeps the identical concealment core" % ("standard" if high else "low"))
		check(smoke._cloud_puffs.size() == (7 if high else 4), "%s preset puff budget unchanged" % ("standard" if high else "low"))
		var puff: MeshInstance3D = smoke._cloud_puffs[1]
		check(smoke._core_material.render_priority < (puff.material_override as StandardMaterial3D).render_priority, "textured edge puffs draw over the core")
		check(not shooter.can_see(target) and is_equal_approx(smoke.concealment_radius(), Utility.CONCEALMENT_RADIUS), "fresh cloud blocks line of sight at full radius")
		# Dissipation: concealment shrinks with the visible cloud, not after it vanishes.
		smoke._lifetime = Utility.DISSIPATE_SECONDS * 0.5
		smoke._physics_process(0.0)
		check(is_equal_approx(smoke.concealment_radius(), Utility.CONCEALMENT_RADIUS * 0.5) and puff.scale.x < 0.7 and is_equal_approx(float(smoke._core_material.get_shader_parameter("opacity")), 0.5), "dissipating cloud thins visuals and concealment together")
		smoke._lifetime = 0.0
		smoke._apply_dissipation()
		check(shooter.can_see(target), "a fully dissipated cloud no longer blinds bots")
		smoke.queue_free()
		await physics_frame
	Utility.high_quality_smoke = true
	world.queue_free()
	await process_frame
	print("SMOKE_PRESENTATION_TEST checks=%d failures=%d" % [checks, failures.size()])
	quit(0 if failures.is_empty() else 1)
