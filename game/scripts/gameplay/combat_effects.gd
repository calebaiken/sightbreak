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

## A spent rifle case lathed from its profile, axis +Y and centred on its middle: a rim, an
## extractor groove, a tapered body, a shoulder, a neck and an open mouth whose inside is dark.
## Ten sides are enough for something about 4 cm long; the whole pool is one draw.
static func casing_mesh() -> ArrayMesh:
	var profile: Array[Vector2] = [Vector2(0.0, 0.0), Vector2(0.0034, 0.0), Vector2(0.0053, 0.0004), Vector2(0.0053, 0.0014), Vector2(0.0045, 0.0018), Vector2(0.0048, 0.0028), Vector2(0.0047, 0.0235), Vector2(0.0033, 0.0305), Vector2(0.0033, 0.0400), Vector2(0.0029, 0.0400), Vector2(0.0029, 0.0330)]
	var inside_from := 9 # Points from here on are the inside of the mouth.
	var sides := 10
	var centre := 0.020
	var normals: Array[Vector2] = []
	for i in profile.size():
		var before := profile[maxi(i - 1, 0)]
		var after := profile[mini(i + 1, profile.size() - 1)]
		var tangent := (after - before).normalized()
		normals.append(Vector2(tangent.y, -tangent.x))
	var tool := SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	for j in range(profile.size() - 1):
		var dark := j >= inside_from - 1
		for k in range(sides):
			var corner: Array[Vector3] = []
			var corner_normal: Array[Vector3] = []
			for step in [[j, k], [j + 1, k], [j + 1, k + 1], [j, k + 1]]:
				var angle: float = TAU * step[1] / sides
				var point: Vector2 = profile[step[0]]
				corner.append(Vector3(point.x * cos(angle), point.y - centre, point.x * sin(angle)))
				var n: Vector2 = normals[step[0]]
				corner_normal.append(Vector3(n.x * cos(angle), n.y, n.x * sin(angle)))
			var shade := Color(0.16, 0.12, 0.07) if dark else Color.WHITE
			for index in [0, 1, 2, 0, 2, 3]:
				tool.set_color(shade)
				tool.set_normal(corner_normal[index])
				tool.add_vertex(corner[index])
	return tool.commit()

func _ready() -> void:
	_random.randomize() # Entirely separate from the authoritative shot RNG.
	_make_pool("casings", CASING_CAP, casing_mesh(), Color("c8a45a"), false)
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
	material.roughness = 0.34 if key == "casings" else 0.95
	material.metallic = 0.85 if key == "casings" else 0.0
	if key == "casings":
		material.vertex_color_use_as_albedo = true
		material.cull_mode = BaseMaterial3D.CULL_DISABLED
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

func _emit(key: String, at: Vector3, velocity: Vector3, life: float, ground := -INF) -> void:
	var pool: Dictionary = _pools[key]
	var slot: int = _next[key]
	_next[key] = (slot + 1) % pool.slots.size()
	# Every particle tumbles about its own axis, from its own starting orientation.
	var axis := Vector3(_random.randf_range(-1, 1), _random.randf_range(-1, 1), _random.randf_range(-1, 1))
	axis = axis.normalized() if axis.length() > 0.01 else Vector3.UP
	var start := Vector3(_random.randf_range(-1, 1), _random.randf_range(-1, 1) + 0.01, _random.randf_range(-1, 1)).normalized()
	pool.slots[slot] = {"life": life, "total": life, "at": at, "velocity": velocity, "spin": _random.randf_range(-5, 5), "axis": axis,
		"basis": Basis(start, _random.randf_range(0, TAU)), "ground": ground, "bounces": 0, "resting": false}

## A spent case thrown from the ejection port: out to the right and up, with a little scatter
## fore and aft, tumbling, and bouncing off the floor (`ground` is the floor's height) before
## it fades. Cosmetic only.
func casing(at: Vector3, right: Vector3, ground := -INF) -> void:
	var back := right.cross(Vector3.UP).normalized()
	var throw := right * _random.randf_range(1.1, 1.8) + Vector3.UP * _random.randf_range(0.9, 1.5) + back * _random.randf_range(-0.35, 0.35)
	_emit("casings", at, throw, 1.8 if is_finite(ground) else 0.65, ground)

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
			if not slot.resting:
				velocity.y -= delta * (7.0 if key == "casings" else 0.65)
				slot.velocity = velocity
				slot.at += velocity * delta
			if key == "casings" and not slot.resting:
				var ground: float = slot.ground
				if slot.at.y < ground + 0.005 and velocity.y < 0.0:
					# Bounce: keep a third of the vertical speed and half of the horizontal, and half
					# the spin; after three bounces, or once it is too slow to leave the floor, it lies still.
					slot.bounces += 1
					slot.at.y = ground + 0.005
					velocity = Vector3(velocity.x * 0.5, -velocity.y * 0.32, velocity.z * 0.5)
					slot.spin = float(slot.spin) * 0.5
					if slot.bounces > 3 or absf(velocity.y) < 0.25:
						velocity = Vector3.ZERO
						slot.spin = 0.0
						slot.resting = true
					slot.velocity = velocity
				slot.basis = Basis(slot.axis, float(slot.spin) * 3.0 * delta) * slot.basis
			var remaining: float = slot.life / slot.total
			var scale_factor := minf(1, remaining * 4)
			if key == "dust":
				scale_factor *= 0.4 + (1.0 - remaining) * 1.8
			var basis: Basis = slot.basis if key == "casings" else Basis(Vector3(0.7, 0.3, 0.2).normalized(), slot.spin * (slot.total - slot.life))
			pool.mesh.set_instance_transform(i, Transform3D(basis.scaled(Vector3.ONE * scale_factor), slot.at))
