class_name SBCombatEffects
extends Node3D
## Fixed-capacity cosmetic pools. No physics bodies, damage, lights, scene-owner
## references or timers. The owning match frees all pools with its scene.
const CASING_CAP := 24
const SPARK_CAP := 40
const DUST_CAP := 12
var _pools: Dictionary = {}
var _next: Dictionary = {}
var _random := RandomNumberGenerator.new()

static func for_world(world: Node) -> SBCombatEffects:
	var effects := world.get_node_or_null("CombatEffects") as SBCombatEffects
	if effects == null:
		effects = SBCombatEffects.new()
		effects.name = "CombatEffects"
		world.add_child(effects)
	return effects

func _ready() -> void:
	_random.randomize() # Entirely separate from the authoritative shot RNG.
	var shell := CylinderMesh.new()
	shell.top_radius = 0.008
	shell.bottom_radius = 0.008
	shell.height = 0.029
	shell.radial_segments = 6
	_make_pool("casings", CASING_CAP, shell, Color("b99b5d"), false)
	var spark := BoxMesh.new()
	spark.size = Vector3(0.012, 0.012, 0.045)
	_make_pool("sparks", SPARK_CAP, spark, Color("ffe0a1"), true)
	var dust := SphereMesh.new()
	dust.radius = 0.085
	dust.height = 0.17
	dust.radial_segments = 8
	dust.rings = 4
	_make_pool("dust", DUST_CAP, dust, Color("9f9a8d"), false)

func _make_pool(key: String, capacity: int, mesh: Mesh, tint: Color, unshaded: bool) -> void:
	var instance := MultiMeshInstance3D.new()
	var multi := MultiMesh.new()
	multi.transform_format = MultiMesh.TRANSFORM_3D
	multi.instance_count = capacity
	multi.mesh = mesh
	instance.multimesh = multi
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var material := StandardMaterial3D.new()
	material.albedo_color = tint
	material.roughness = 0.42 if key == "casings" else 0.95
	material.metallic = 0.7 if key == "casings" else 0.0
	if unshaded:
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	instance.material_override = material
	add_child(instance)
	var slots: Array[Dictionary] = []
	for i in range(capacity):
		slots.append({"life": 0.0})
		multi.set_instance_transform(i, Transform3D(Basis.IDENTITY.scaled(Vector3.ZERO), Vector3.ZERO))
	_pools[key] = {"mesh": multi, "slots": slots}
	_next[key] = 0

func _emit(key: String, at: Vector3, velocity: Vector3, life: float) -> void:
	var pool: Dictionary = _pools[key]
	var slot: int = _next[key]
	_next[key] = (slot + 1) % pool.slots.size()
	pool.slots[slot] = {"life": life, "total": life, "at": at, "velocity": velocity, "spin": _random.randf_range(-5, 5)}

func casing(at: Vector3, right: Vector3) -> void:
	_emit("casings", at, right * _random.randf_range(1.1, 1.7) + Vector3.UP * 1.15, 0.65)

func impact(at: Vector3, normal: Vector3, actor: bool) -> void:
	for i in range(2 if actor else 4):
		var scatter := Vector3(_random.randf_range(-0.5, 0.5), _random.randf_range(-0.3, 0.5), _random.randf_range(-0.5, 0.5))
		_emit("sparks", at + normal * 0.025, (normal + scatter) * _random.randf_range(0.7, 1.8), 0.10 if actor else 0.19)
	if not actor:
		_emit("dust", at + normal * 0.03, normal * 0.35 + Vector3.UP * 0.12, 0.34)

func _process(delta: float) -> void:
	for key in _pools:
		var pool: Dictionary = _pools[key]
		for i in range(pool.slots.size()):
			var slot: Dictionary = pool.slots[i]
			if slot.life <= 0:
				continue
			slot.life = maxf(0, slot.life - delta)
			if slot.life == 0:
				pool.mesh.set_instance_transform(i, Transform3D(Basis.IDENTITY.scaled(Vector3.ZERO), Vector3.ZERO))
				continue
			var velocity: Vector3 = slot.velocity
			velocity.y -= delta * (7.0 if key == "casings" else 0.65)
			slot.velocity = velocity
			slot.at += velocity * delta
			var remaining: float = slot.life / slot.total
			var scale_factor := minf(1, remaining * 4)
			if key == "dust":
				scale_factor *= 0.4 + (1.0 - remaining) * 1.8
			var basis := Basis(Vector3(0.7, 0.3, 0.2).normalized(), slot.spin * (slot.total - slot.life))
			pool.mesh.set_instance_transform(i, Transform3D(basis.scaled(Vector3.ONE * scale_factor), slot.at))
