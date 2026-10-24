class_name SBCombatEffects
extends Node3D
## Fixed-capacity cosmetic pools. No physics bodies, damage, lights, scene-owner
## references or timers. The owning match frees all pools with its scene.
const CASING_CAP := 24
const SPARK_CAP := 40
const DUST_CAP := 12
## Bullet holes are one more fixed pool, kept apart from the timed pools because they stay until the round changes.
## The allocation is the ULTRA ceiling; `apply_graphics` lowers the ring that is used.
const HOLE_MAX := 64
const HOLE_LIFT := 0.006
const HOLE_TEXTURE_SIZE := 64
## What a hit does to each surface family (`surface` meta on the arena's solids; anything else is "generic").
## sparks and dust are particle counts, `spark`/`dust` tints (the lit puffs come out about three times brighter than
## their tint, so they are dark here: measured, not guessed), `speed` a multiplier on spark speed, `*_size`
## multipliers on the pooled particle's scale, `hole` the hole's width in metres, `hole_tint` the colour the shared
## hole texture is multiplied by.
const SURFACES := {
	"metal": {"sparks": 5, "spark": Color("ffd08a"), "speed": 1.45, "spark_size": 2.2, "spark_life": 0.22, "dust": 1, "dust_tint": Color("5e6266"), "dust_size": 0.7, "hole": 0.15, "hole_tint": Color(0.16, 0.17, 0.19, 1.0)},
	"concrete": {"sparks": 2, "spark": Color("e4e0d2"), "speed": 0.9, "spark_size": 1.3, "spark_life": 0.17, "dust": 1, "dust_tint": Color("706e66"), "dust_size": 1.0, "hole": 0.20, "hole_tint": Color(0.22, 0.22, 0.21, 1.0)},
	"asphalt": {"sparks": 1, "spark": Color("a4a9ac"), "speed": 0.8, "spark_size": 1.3, "spark_life": 0.15, "dust": 1, "dust_tint": Color("4a4e50"), "dust_size": 0.8, "hole": 0.16, "hole_tint": Color(0.10, 0.11, 0.12, 1.0)},
	"generic": {"sparks": 4, "spark": Color("ffe0a1"), "speed": 1.0, "spark_size": 1.0, "spark_life": 0.19, "dust": 1, "dust_tint": Color("7a7258"), "dust_size": 1.0, "hole": 0.17, "hole_tint": Color(0.17, 0.16, 0.14, 1.0)},
}
var _pools: Dictionary = {}
var _next: Dictionary = {}
var _random := RandomNumberGenerator.new()
var _holes: MultiMesh
var _hole_ring := 0
var _hole_cap := 32
var _hole_total := 0
var _round_seen := -1
## The surface family of the last world impact: for tests and for the capture tooling.
var last_surface := ""

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
	_hole_cap = clampi(int(SBGraphicsQuality.config(SBGraphicsQuality.current).impact_holes), 0, HOLE_MAX)
	var parent_round = get_parent().get("round_number") if get_parent() != null else null
	_round_seen = int(parent_round) if parent_round != null else -1
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
	_make_hole_pool()

func _make_pool(key: String, capacity: int, mesh: Mesh, tint: Color, unshaded: bool) -> void:
	var instance := MultiMeshInstance3D.new()
	var multi := MultiMesh.new()
	multi.transform_format = MultiMesh.TRANSFORM_3D
	multi.use_colors = true # must precede the instance count
	multi.instance_count = capacity
	multi.mesh = mesh
	instance.multimesh = multi
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var material := StandardMaterial3D.new()
	# The instance colour carries each particle's tint (a metal spark and a concrete chip differ), so the
	# material itself stays white.
	material.vertex_color_use_as_albedo = true
	material.roughness = 0.34 if key == "casings" else 0.95
	material.metallic = 0.85 if key == "casings" else 0.0
	if key == "casings":
		material.cull_mode = BaseMaterial3D.CULL_DISABLED
	if unshaded:
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	instance.material_override = material
	add_child(instance)
	var slots: Array[Dictionary] = []
	for i in range(capacity):
		slots.append({"life": 0.0})
		multi.set_instance_transform(i, Transform3D(Basis.IDENTITY.scaled(Vector3.ZERO), Vector3.ZERO))
	_pools[key] = {"mesh": multi, "slots": slots, "tint": tint}
	_next[key] = 0

func _emit(key: String, at: Vector3, velocity: Vector3, life: float, ground := -INF, tint := Color(0, 0, 0, 0), size := 1.0) -> void:
	var pool: Dictionary = _pools[key]
	var slot: int = _next[key]
	_next[key] = (slot + 1) % pool.slots.size()
	pool.mesh.set_instance_color(slot, tint if tint.a > 0.0 else pool.tint)
	# Every particle tumbles about its own axis, from its own starting orientation.
	var axis := Vector3(_random.randf_range(-1, 1), _random.randf_range(-1, 1), _random.randf_range(-1, 1))
	axis = axis.normalized() if axis.length() > 0.01 else Vector3.UP
	var start := Vector3(_random.randf_range(-1, 1), _random.randf_range(-1, 1) + 0.01, _random.randf_range(-1, 1)).normalized()
	pool.slots[slot] = {"life": life, "total": life, "at": at, "velocity": velocity, "spin": _random.randf_range(-5, 5), "axis": axis,
		"basis": Basis(start, _random.randf_range(0, TAU)), "ground": ground, "bounces": 0, "resting": false, "size": size}

## A spent case thrown from the ejection port: out to the right and up, with a little scatter
## fore and aft, tumbling, and bouncing off the floor (`ground` is the floor's height) before
## it fades. Cosmetic only.
func casing(at: Vector3, right: Vector3, ground := -INF) -> void:
	var back := right.cross(Vector3.UP).normalized()
	var throw := right * _random.randf_range(1.1, 1.8) + Vector3.UP * _random.randf_range(0.9, 1.5) + back * _random.randf_range(-0.35, 0.35)
	_emit("casings", at, throw, 1.8 if is_finite(ground) else 0.65, ground)

func impact(at: Vector3, normal: Vector3, actor: bool) -> void:
	if not at.is_finite() or not normal.is_finite() or normal.length_squared() < 0.25:
		return
	if actor:
		for i in range(2):
			var scatter := Vector3(_random.randf_range(-0.5, 0.5), _random.randf_range(-0.3, 0.5), _random.randf_range(-0.5, 0.5))
			_emit("sparks", at + normal * 0.025, (normal + scatter) * _random.randf_range(0.7, 1.8), 0.10)
		return
	var family := surface_at(at, normal)
	last_surface = family
	var fx: Dictionary = SURFACES[family]
	for i in range(int(fx.sparks)):
		var scatter := Vector3(_random.randf_range(-0.5, 0.5), _random.randf_range(-0.3, 0.5), _random.randf_range(-0.5, 0.5))
		_emit("sparks", at + normal * 0.025, (normal + scatter) * _random.randf_range(0.7, 1.8) * float(fx.speed), float(fx.spark_life), -INF, fx.spark, float(fx.spark_size))
	for i in range(int(fx.dust)):
		_emit("dust", at + normal * 0.03, normal * 0.35 + Vector3.UP * 0.12, 0.34, -INF, fx.dust_tint, float(fx.dust_size))
	_place_hole(at, normal.normalized(), fx)

## The surface family at a world hit, from the `surface` meta of the solid under the point. Local physics only, so
## the network carries nothing new: a client finds the same answer from the same arena.
func surface_at(at: Vector3, normal: Vector3) -> String:
	if not is_inside_tree():
		return "generic"
	var query := PhysicsRayQueryParameters3D.create(at + normal * 0.06, at - normal * 0.06, 1)
	var found := get_world_3d().direct_space_state.intersect_ray(query)
	var body := found.get("collider") as Node
	if body != null and body.has_meta("surface"):
		var family := String(body.get_meta("surface"))
		if SURFACES.has(family):
			return family
	return "generic"

## A bullet hole: one textured quad lying on the surface, oldest replaced when the ring is full.
func _place_hole(at: Vector3, normal: Vector3, fx: Dictionary) -> void:
	if _holes == null or _hole_cap <= 0:
		return
	var reference := Vector3.UP if absf(normal.y) < 0.95 else Vector3.RIGHT
	var x := reference.cross(normal).normalized()
	var basis := Basis(x, normal.cross(x), normal).rotated(normal, _random.randf_range(0.0, TAU))
	var width := float(fx.hole) * _random.randf_range(0.85, 1.15)
	_holes.set_instance_transform(_hole_ring, Transform3D(basis.scaled_local(Vector3(width, width, 1.0)), at + normal * HOLE_LIFT))
	_holes.set_instance_color(_hole_ring, fx.hole_tint)
	_hole_ring = (_hole_ring + 1) % _hole_cap
	_hole_total = mini(_hole_total + 1, _hole_cap)

func hole_count() -> int:
	return _hole_total

func clear_holes() -> void:
	if _holes == null:
		return
	for i in range(HOLE_MAX):
		_holes.set_instance_transform(i, Transform3D(Basis.IDENTITY.scaled(Vector3.ZERO), Vector3.ZERO))
	_hole_ring = 0
	_hole_total = 0

## Called by SBGraphicsQuality for the tier's ring size; holes beyond a smaller ring disappear.
func apply_graphics(settings: Dictionary) -> void:
	var cap := clampi(int(settings.get("impact_holes", 32)), 0, HOLE_MAX)
	if cap < _hole_cap:
		clear_holes()
	_hole_cap = cap

## One shared texture for every hole: a dark irregular core, a scorched ring, and a faint soot halo with radial
## streaks. Alpha carries the shape; the instance colour carries how dark the surface makes it.
static func hole_texture() -> ImageTexture:
	var size := HOLE_TEXTURE_SIZE
	var image := Image.create(size, size, false, Image.FORMAT_RGBA8)
	for py in range(size):
		for px in range(size):
			var u := (px + 0.5) / size * 2.0 - 1.0
			var v := (py + 0.5) / size * 2.0 - 1.0
			var r := sqrt(u * u + v * v)
			var theta := atan2(v, u)
			var wobble := 1.0 + 0.22 * sin(3.0 * theta + 0.7) + 0.14 * sin(7.0 * theta + 2.1) + 0.08 * sin(13.0 * theta + 4.3)
			var core := 0.15 * wobble
			var ring := 0.34 * wobble
			var halo := 0.96
			var shade := 1.0
			var alpha := 0.0
			if r < core:
				shade = 0.0
				alpha = 1.0
			elif r < ring:
				var t := (r - core) / (ring - core)
				shade = 0.25 + 0.35 * t
				alpha = 0.92 * (1.0 - t * t) + 0.1
			elif r < halo:
				var streak := 0.5 + 0.5 * sin(11.0 * theta + 1.3) * sin(5.0 * theta + 0.4)
				var t := (r - ring) / (halo - ring)
				shade = 1.9
				alpha = 0.42 * (0.35 + 0.65 * streak) * (1.0 - t) * (1.0 - t)
			image.set_pixel(px, py, Color(shade * 0.5, shade * 0.5, shade * 0.5, clampf(alpha, 0.0, 1.0)))
	return ImageTexture.create_from_image(image)

func _make_hole_pool() -> void:
	var instance := MultiMeshInstance3D.new()
	_holes = MultiMesh.new()
	_holes.transform_format = MultiMesh.TRANSFORM_3D
	_holes.use_colors = true
	_holes.instance_count = HOLE_MAX
	var quad := QuadMesh.new()
	quad.size = Vector2.ONE
	_holes.mesh = quad
	instance.multimesh = _holes
	instance.name = "BulletHoles"
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var material := StandardMaterial3D.new()
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.albedo_texture = hole_texture()
	material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	material.vertex_color_use_as_albedo = true
	material.roughness = 1.0
	material.cull_mode = BaseMaterial3D.CULL_BACK
	material.render_priority = 1
	instance.material_override = material
	add_child(instance)
	clear_holes()

func _process(delta: float) -> void:
	# Holes belong to one round: the match is the parent, and its round counter is the one signal that needs no wiring.
	var parent_round = get_parent().get("round_number") if get_parent() != null else null
	if parent_round != null and int(parent_round) != _round_seen:
		_round_seen = int(parent_round)
		clear_holes()
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
			var scale_factor := minf(1, remaining * 4) * float(slot.get("size", 1.0))
			if key == "dust":
				scale_factor *= 0.4 + (1.0 - remaining) * 1.8
			var basis: Basis = slot.basis if key == "casings" else Basis(Vector3(0.7, 0.3, 0.2).normalized(), slot.spin * (slot.total - slot.life))
			pool.mesh.set_instance_transform(i, Transform3D(basis.scaled(Vector3.ONE * scale_factor), slot.at))
