class_name SBTracerEffects
extends Node3D
## Bullet streaks: a short bright segment that runs from the muzzle to where a shot ended. Presentation only, in the
## same spirit as SBCombatEffects: no physics, no damage, no lights, no timers, a fixed capacity (one multimesh, one
## draw call), and it is told about a shot, never asked. A tracer is made where a shot is traced (the authority or an
## offline match), from the muzzle to the point the trace ended, so a client that is only sent a flash learns nothing
## new from it. The local player's own shots draw none: a streak leaving the muzzle toward the crosshair is seen end-on,
## a sliver a few pixels long, so it would only be a smear in the middle of the view. One shot in EVERY carries one, like a belt with tracer rounds, so a spray does not draw a curtain.
const CAP := 16
const EVERY := 3
## Metres per second the streak travels at; the streak is STREAK metres long, and shrinks into the end point.
const SPEED := 190.0
const STREAK := 7.0
## A path shorter than this is not drawn: the streak would sit in the muzzle flash or on the target.
const MIN_PATH := 2.5
## Beyond this a shot that hit nothing is drawn only this far.
const MAX_PATH := 90.0
const WIDTH := 0.05
var _multi: MultiMesh
var _slots: Array[Dictionary] = []
var _next := 0

static func for_world(world: Node) -> SBTracerEffects:
	var effects := world.get_node_or_null("TracerEffects") as SBTracerEffects
	if effects == null:
		effects = SBTracerEffects.new()
		effects.name = "TracerEffects"
		world.add_child(effects)
	return effects

## True when shot number `index` of a shooter carries a tracer.
static func carries(index: int) -> bool:
	return index % EVERY == 0

static var _mesh: ArrayMesh
static var _shader: Shader

## One quad along +Z, 0 at the muzzle end to 1 at the far end, 1 unit wide: the shader turns it to face the camera.
static func quad() -> ArrayMesh:
	if _mesh == null:
		var arrays := []
		arrays.resize(Mesh.ARRAY_MAX)
		arrays[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3(-0.5, 0, 0), Vector3(0.5, 0, 0), Vector3(0.5, 0, 1), Vector3(-0.5, 0, 1)])
		arrays[Mesh.ARRAY_TEX_UV] = PackedVector2Array([Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)])
		arrays[Mesh.ARRAY_INDEX] = PackedInt32Array([0, 1, 2, 0, 2, 3])
		_mesh = ArrayMesh.new()
		_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return _mesh

static func shader() -> Shader:
	if _shader == null:
		_shader = Shader.new()
		_shader.code = """
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, fog_disabled;
uniform vec3 tint : source_color = vec3(1.0, 0.70, 0.28);
// Per instance: x head, y tail (0 to 1 along the path), z strength, w width in metres.
varying vec4 streak;
varying float near_fade;
void vertex() {
	vec3 start = MODEL_MATRIX[3].xyz;
	vec3 axis = MODEL_MATRIX[2].xyz;
	vec3 centre = start + axis * VERTEX.z;
	vec3 to_point = centre - CAMERA_POSITION_WORLD;
	float distance_to_camera = max(length(to_point), 0.01);
	vec3 side = cross(axis, to_point / distance_to_camera);
	side = side / max(length(side), 0.0001);
	// A little wider with distance so a streak 40 m away is still a couple of pixels.
	float width = INSTANCE_CUSTOM.w + distance_to_camera * 0.0032;
	vec3 world_position = centre + side * VERTEX.x * width;
	POSITION = PROJECTION_MATRIX * VIEW_MATRIX * vec4(world_position, 1.0);
	streak = INSTANCE_CUSTOM;
	// Nothing smears across the lens or stands up like a beam over the floor: a streak is gone by the time it is within
	// 2 m of the camera, and fades in over the next six.
	near_fade = smoothstep(2.0, 8.0, distance_to_camera);
	// A streak seen almost end-on (a shot fired at the camera) is a pillar standing on the floor or a smear, not a bullet
	// path, so it fades as the angle between it and the line of sight closes.
	float broadside = length(cross(normalize(axis), to_point / distance_to_camera));
	near_fade *= smoothstep(0.12, 0.40, broadside);
}
void fragment() {
	float across = 1.0 - abs(UV.x * 2.0 - 1.0);
	float body = pow(across, 1.4);
	float core = pow(across, 5.0);
	float along = UV.y;
	float length_fraction = max(streak.x - streak.y, 0.0001);
	float ramp = clamp((along - streak.y) / length_fraction, 0.0, 1.0);
	float inside = step(along, streak.x) * step(streak.y, along);
	float head_glow = smoothstep(0.75, 1.0, ramp);
	// A comet: nothing at the tail end, so the streak never ends in a hard dash, and a bright head.
	float weight = inside * (pow(ramp, 1.8) * 0.8 + head_glow * 0.6) * body;
	ALBEDO = mix(tint, vec3(1.0, 0.93, 0.74), core * 0.4) * (1.1 + core * 0.7);
	ALPHA = clamp(weight * streak.z * near_fade, 0.0, 1.0);
}
"""
	return _shader

func _ready() -> void:
	_multi = MultiMesh.new()
	_multi.transform_format = MultiMesh.TRANSFORM_3D
	# Per-instance data has to be switched on before the count is set.
	_multi.use_custom_data = true
	_multi.instance_count = CAP
	_multi.mesh = quad()
	var instance := MultiMeshInstance3D.new()
	instance.multimesh = _multi
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# The segments are placed by the shader, so the bounds the engine would cull by say nothing true about them.
	instance.custom_aabb = AABB(Vector3(-300, -50, -300), Vector3(600, 150, 600))
	var material := ShaderMaterial.new()
	material.shader = shader()
	instance.material_override = material
	add_child(instance)
	for i in range(CAP):
		_slots.append({"age": 0.0, "path": 1.0, "live": false})
		_hide(i)

## A tracer from `from` to `to`; `strength` scales its brightness. Returns whether one was drawn.
func trace(from: Vector3, to: Vector3, strength := 1.0) -> bool:
	if not from.is_finite() or not to.is_finite():
		return false
	var span := to - from
	var path := span.length()
	if path < MIN_PATH:
		return false
	if path > MAX_PATH:
		span = span / path * MAX_PATH
		path = MAX_PATH
	var slot := _next
	_next = (_next + 1) % CAP
	_slots[slot] = {"age": 0.0, "path": path, "live": true, "from": from, "span": span, "strength": strength}
	_place(slot)
	return true

## How many streaks are in flight.
func active() -> int:
	var count := 0
	for slot in _slots:
		if slot.live:
			count += 1
	return count

func _process(delta: float) -> void:
	for i in range(CAP):
		var slot: Dictionary = _slots[i]
		if not slot.live:
			continue
		slot.age += delta
		var tail: float = slot.age * SPEED / slot.path - STREAK / slot.path
		if tail >= 1.0:
			slot.live = false
			_hide(i)
		else:
			_place(i)

func _place(index: int) -> void:
	var slot: Dictionary = _slots[index]
	var path: float = slot.path
	var age: float = slot.age
	var head := minf(age * SPEED / path, 1.0)
	var tail := age * SPEED / path - STREAK / path
	# X and Y are unit vectors perpendicular to the path and Z is the path itself, so the transform is never singular.
	var along: Vector3 = slot.span
	var across := along.cross(Vector3.UP)
	across = across.normalized() if across.length_squared() > 0.0001 else Vector3.RIGHT
	var basis := Basis(across, along.cross(across).normalized(), along)
	_multi.set_instance_transform(index, Transform3D(basis, slot.from))
	# The tail is left below zero while the streak is still lengthening out of the muzzle, so a young one is lit right
	# down to the muzzle instead of floating clear of it.
	_multi.set_instance_custom_data(index, Color(head, tail, slot.strength, WIDTH))

func _hide(index: int) -> void:
	_multi.set_instance_transform(index, Transform3D(Basis.IDENTITY.scaled(Vector3.ZERO), Vector3.ZERO))
