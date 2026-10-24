extends SceneTree
## Surface-aware impacts and persistent bullet holes: each surface family gets its own sparks and hole, the pool is
## fixed, holes follow the graphics tier, a new round clears them, and nothing here touches gameplay state.
var checks := 0
var failures := 0
func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures += 1
		push_error(message)
func _initialize() -> void:
	call_deferred("run")
func frames(count: int) -> void:
	for i in count: await physics_frame
func shoot(world: Node3D, from: Vector3, direction: Vector3) -> Dictionary:
	var query := PhysicsRayQueryParameters3D.create(from, from + direction * 80.0, 1)
	return world.get_world_3d().direct_space_state.intersect_ray(query)
func run() -> void:
	# A holder that owns a round counter, as the match does.
	var holder_script := GDScript.new()
	holder_script.source_code = "extends Node3D\nvar round_number := 1\n"
	holder_script.reload()
	var world := Node3D.new()
	world.set_script(holder_script)
	root.add_child(world)
	world.add_child(RelayYard.new())
	await frames(2)
	var effects := SBCombatEffects.for_world(world)
	await frames(1)
	var expectations := {
		"asphalt": shoot(world, Vector3(11, 1.6, -5), Vector3.DOWN),
		"concrete": shoot(world, Vector3(-12, 1.6, -3.5), Vector3.LEFT),
		"metal": shoot(world, Vector3(-1.0, 1.55, -11), Vector3.LEFT),
		"generic": shoot(world, Vector3(0, 0.8, 5), Vector3.BACK),
	}
	for family in expectations:
		var hit: Dictionary = expectations[family]
		check(not hit.is_empty(), "A test ray finds the %s fixture" % family)
		if hit.is_empty():
			continue
		var before := effects.hole_count()
		effects.impact(hit.position, hit.normal, false)
		check(effects.last_surface == family, "A hit on %s is classified as %s (got %s)" % [family, family, effects.last_surface])
		check(effects.hole_count() == before + 1, "A %s hit leaves one bullet hole" % family)
	# Surfaces differ in what they throw.
	check(SBCombatEffects.SURFACES.metal.sparks > SBCombatEffects.SURFACES.concrete.sparks and SBCombatEffects.SURFACES.metal.dust_size < SBCombatEffects.SURFACES.concrete.dust_size, "Metal throws more sparks and a smaller puff than concrete")
	check(SBCombatEffects.SURFACES.concrete.hole > SBCombatEffects.SURFACES.metal.hole, "Concrete takes a wider hole than steel")
	# A hit on an operator leaves no hole and no surface lookup.
	var holes_before := effects.hole_count()
	effects.impact(Vector3(0, 1, 0), Vector3.UP, true)
	check(effects.hole_count() == holes_before, "A hit on an operator leaves no hole")
	# Malformed events change nothing.
	effects.impact(Vector3.INF, Vector3.UP, false)
	effects.impact(Vector3.ZERO, Vector3.ZERO, false)
	check(effects.hole_count() == holes_before, "Non-finite or zero-normal impacts leave no hole")
	# Fixed pool.
	for i in range(300):
		effects.impact(Vector3(randf_range(-10, 10), 0.0, randf_range(-10, 10)), Vector3.UP, false)
	check(effects.hole_count() == 32 and effects._holes.instance_count == SBCombatEffects.HOLE_MAX, "The default ring keeps 32 holes inside a fixed 64-instance pool")
	# Tier ring.
	effects.apply_graphics(SBGraphicsQuality.config(SBGraphicsQuality.LOW))
	check(effects.hole_count() == 0, "Dropping to LOW clears the holes that no longer fit")
	for i in range(100):
		effects.impact(Vector3(0, 0, i * 0.1), Vector3.UP, false)
	check(effects.hole_count() == 12, "LOW keeps 12 holes")
	effects.apply_graphics(SBGraphicsQuality.config(SBGraphicsQuality.ULTRA))
	for i in range(200):
		effects.impact(Vector3(0, 0, i * 0.05), Vector3.UP, false)
	check(effects.hole_count() == 64, "ULTRA keeps 64 holes")
	# Holes stay while their particles expire, and a new round removes them.
	effects._process(5.0)
	check(effects.hole_count() == 64, "Holes outlive the timed particles")
	world.round_number = 2
	await process_frame
	await process_frame
	check(effects.hole_count() == 0, "A new round clears every hole")
	# A freshly made pool starts from the current tier.
	SBGraphicsQuality.current = SBGraphicsQuality.HIGH
	var other := Node3D.new()
	root.add_child(other)
	var fresh := SBCombatEffects.for_world(other)
	await frames(1)
	check(fresh._hole_cap == 48, "Effects created after a tier change use that tier's hole ring")
	SBGraphicsQuality.current = SBGraphicsQuality.MEDIUM
	# The hole texture is a real shape: opaque dark centre, transparent corners.
	var image := SBCombatEffects.hole_texture().get_image()
	var mid := image.get_width() / 2
	check(image.get_pixel(mid, mid).a > 0.95 and image.get_pixel(mid, mid).r < 0.05, "The hole centre is opaque and dark")
	check(image.get_pixel(0, 0).a == 0.0 and image.get_pixel(image.get_width() - 1, image.get_height() - 1).a == 0.0, "The hole texture is clear at its corners")
	print("combat_impact_test: %d checks, %d failures" % [checks, failures])
	quit(1 if failures > 0 else 0)
