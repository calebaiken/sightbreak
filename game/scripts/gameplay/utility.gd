class_name SBUtility
extends Node3D

var kind: String = "grenade"
var visual_only: bool = false
var owner_id: int = 0
var owner_team: int = 0
var velocity := Vector3.ZERO
var _fuse := 1.6
var _lifetime := 0.0
var _detonated := false
var _mesh: MeshInstance3D
var _cloud_puffs: Array[MeshInstance3D] = []
var _cloud_elapsed := 0.0
static var high_quality_smoke := true
static var _smoke_texture: ImageTexture
static var _smoke_core_shader: Shader
static var _smoke_core_mesh: ArrayMesh
const CONCEALMENT_RADIUS := 3.2
## Edge puffs as [offset from cloud center, quad size]: four upper layers and two
## small low layers whose lower edge ends at ground level, so no quad is cut by
## the floor. Low quality keeps the first, third and fifth.
const PUFF_LAYOUT := [
	[Vector3(0.0, 0.75, -1.1), Vector2(4.4, 3.8)],
	[Vector3(1.3, 0.45, 0.3), Vector2(4.2, 3.6)],
	[Vector3(-1.25, 0.55, 0.2), Vector2(4.2, 3.6)],
	[Vector3(0.2, 0.9, 1.2), Vector2(4.4, 3.8)],
	[Vector3(1.35, -0.55, -0.9), Vector2(3.0, 2.2)],
	[Vector3(-1.3, -0.55, 1.0), Vector2(3.0, 2.2)]
]
const LOW_PUFFS := [0, 2, 4]
const DISSIPATE_SECONDS := 1.5
var _puff_material: StandardMaterial3D
var _core_material: ShaderMaterial

static func smoke_texture() -> ImageTexture:
	# One original deterministic 64² RGBA texture, about 22 KiB including mipmaps.
	# Shared by all clouds; never allocates a texture per particle or per frame.
	if _smoke_texture == null:
		var texture_image := Image.create(64, 64, false, Image.FORMAT_RGBA8)
		var noise := FastNoiseLite.new()
		noise.seed = 3817
		noise.frequency = 0.083
		noise.fractal_octaves = 4
		for y in range(64):
			for x in range(64):
				var n := noise.get_noise_2d(x, y)
				var radius := (Vector2(x, y) - Vector2(31.5, 31.5)).length() / 31.5
				var density := smoothstep(1.0, 0.42, radius + n * 0.09)
				var shade := 0.46 + n * 0.15
				texture_image.set_pixel(x, y, Color(shade * 0.94, shade, shade * 1.035, density))
		texture_image.generate_mipmaps()
		_smoke_texture = ImageTexture.create_from_image(texture_image)
	return _smoke_texture

static func smoke_core_shader() -> Shader:
	if _smoke_core_shader == null:
		_smoke_core_shader = Shader.new()
		# Unshaded and opaque: a top-lit gradient toward the sun, drifting triplanar
		# noise and a soft bright rim that blends into the translucent edge quads.
		# Culling stays disabled so the cloud remains opaque from inside.
		_smoke_core_shader.code = """shader_type spatial;
render_mode unshaded, cull_disabled, blend_mix, depth_draw_opaque;
uniform sampler2D cloud_noise : source_color, filter_linear_mipmap, repeat_enable;
uniform vec3 light_direction = vec3(-0.41, 0.64, 0.65);
uniform float core_radius = 2.15;
uniform float opacity = 1.0;
varying vec3 cloud_position;
varying vec3 world_normal;
void vertex() {
 float t = TIME * 0.11;
 float billow = sin(VERTEX.x*1.7+0.5+t)*sin(VERTEX.y*1.5-t*0.7)*sin(VERTEX.z*1.4+1.0+t*0.5);
 VERTEX += NORMAL * billow * 0.15;
 cloud_position = VERTEX;
 world_normal = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}
void fragment() {
 float scale = length(MODEL_MATRIX[0].xyz);
 bool inside = distance(CAMERA_POSITION_WORLD, NODE_POSITION_WORLD) < core_radius * scale * 0.97;
 // Outside, only the near surface draws; inside, the surrounding shell is dense fog.
 if (!FRONT_FACING && !inside) {
  discard;
 }
 vec3 n = normalize(world_normal);
 vec3 weights = abs(n);
 weights /= max(weights.x + weights.y + weights.z, 0.001);
 vec3 p = cloud_position * 0.19 + vec3(0.5) + vec3(TIME * 0.004, TIME * 0.007, 0.0);
 float density = texture(cloud_noise, p.yz).r * weights.x + texture(cloud_noise, p.xz).r * weights.y + texture(cloud_noise, p.xy).r * weights.z;
 // Smoke scatters light: only a gentle sun/sky gradient, never a dark terminator.
 float sun = clamp(dot(n, normalize(light_direction)) * 0.5 + 0.5, 0.0, 1.0);
 float sky = clamp(n.y * 0.5 + 0.5, 0.0, 1.0);
 vec3 tone = vec3(0.29, 0.295, 0.305) * mix(0.9, 1.03, sun * 0.6 + sky * 0.4) * (0.52 + density * 1.45);
 // Only the grazing rim thins out, broken up by the noise; the body stays opaque.
 float facing = clamp(abs(dot(normalize(NORMAL), normalize(VIEW))), 0.0, 1.0);
 float body = smoothstep(0.05, 0.4, facing + (density - 0.45) * 0.3);
 if (!FRONT_FACING) {
  tone = vec3(0.275, 0.28, 0.29) * (0.95 + density * 0.08);
  body = 1.0;
 }
 ALBEDO = tone;
 ALPHA = body * opacity;
}
"""
	return _smoke_core_shader

## One shared cumulus-like core: the original concealment sphere plus overlapping
## lobes merged into a single draw. Every lobe stays inside CONCEALMENT_RADIUS so
## bots and players lose sight together; the textured puffs layer over its seams.
static func smoke_core_mesh() -> ArrayMesh:
	if _smoke_core_mesh == null:
		var lobes := [
			[Vector3.ZERO, Vector3(2.15, 2.05, 2.15)],
			[Vector3(0.25, 1.1, -0.2), Vector3(1.25, 1.1, 1.25)],
			[Vector3(1.3, 0.25, 0.55), Vector3(1.2, 1.1, 1.15)],
			[Vector3(-1.25, 0.4, -0.45), Vector3(1.2, 1.1, 1.15)],
			[Vector3(1.25, -0.95, -0.85), Vector3(1.15, 0.75, 1.1)],
			[Vector3(-1.15, -0.95, 1.0), Vector3(1.15, 0.75, 1.1)]
		]
		var builder := SurfaceTool.new()
		builder.begin(Mesh.PRIMITIVE_TRIANGLES)
		for index in range(lobes.size()):
			var sphere := SphereMesh.new()
			sphere.radius = 1.0
			sphere.height = 2.0
			sphere.radial_segments = 28 if index == 0 else 22
			sphere.rings = 14 if index == 0 else 11
			builder.append_from(sphere, 0, Transform3D(Basis.from_scale(lobes[index][1]), lobes[index][0]))
		_smoke_core_mesh = builder.commit()
	return _smoke_core_mesh

## Cloud center height above the surface beneath the detonation point. The same
## position drives replicated visuals and bot concealment.
const CLOUD_HEIGHT := 1.6

func cloud_rest_height() -> float:
	if is_inside_tree():
		var from := global_position + Vector3.UP * 0.25
		var query := PhysicsRayQueryParameters3D.create(from, from + Vector3.DOWN * 40.0, 1)
		var hit := get_world_3d().direct_space_state.intersect_ray(query)
		if not hit.is_empty():
			return float(hit.position.y) + CLOUD_HEIGHT
	return CLOUD_HEIGHT

## Remaining fraction of the cloud: 1 until the final DISSIPATE_SECONDS, then 0.
func dissipation() -> float:
	if not _detonated or kind != "smoke":
		return 1.0
	return clampf(_lifetime / DISSIPATE_SECONDS, 0.0, 1.0)

## Line-of-sight blocking radius used by bots; it shrinks with the visible cloud.
func concealment_radius() -> float:
	return CONCEALMENT_RADIUS * dissipation()

func _apply_dissipation() -> void:
	var remaining := dissipation()
	if remaining >= 1.0:
		return
	var scale_factor := lerpf(0.15, 1.0, remaining)
	for puff in _cloud_puffs:
		puff.scale = Vector3.ONE * scale_factor
	if _puff_material != null:
		_puff_material.albedo_color.a = remaining
	if _core_material != null:
		_core_material.set_shader_parameter("opacity", remaining)

func _ready() -> void:
	_mesh = MeshInstance3D.new()
	var shape := SphereMesh.new()
	shape.radius = 0.09
	shape.height = 0.18
	_mesh.mesh = shape
	var material := StandardMaterial3D.new()
	material.albedo_color = Color("77afbd") if kind == "smoke" else Color("90a06c")
	_mesh.material_override = material
	add_child(_mesh)

func _physics_process(delta: float) -> void:
	if _detonated:
		_lifetime -= delta
		_cloud_elapsed += delta
		for i in range(_cloud_puffs.size()):
			_cloud_puffs[i].rotation.y += delta * (0.025 if i % 2 == 0 else -0.025)
		if kind == "smoke":
			_apply_dissipation()
		if _lifetime <= 0:
			queue_free()
		return
	_fuse -= delta
	velocity.y -= 16 * delta
	var next := global_position + velocity * delta
	var query := PhysicsRayQueryParameters3D.create(global_position, next, 1)
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	if hit.is_empty():
		global_position = next
	else:
		global_position = hit["position"] + hit["normal"] * 0.1
		velocity = velocity.bounce(hit["normal"]) * 0.42
	if _fuse <= 0:
		_detonate()

func _detonate() -> void:
	_detonated = true
	_mesh.visible = false
	if kind == "smoke":
		_lifetime = 12
		global_position.y = cloud_rest_height()
		add_to_group("smoke_clouds")
		# A closed opaque core preserves concealment even inside the cloud. Only
		# the boundary uses alpha: at most six quads (three in Low), no lights.
		var core := MeshInstance3D.new()
		core.mesh = smoke_core_mesh()
		var core_material := ShaderMaterial.new()
		_core_material = core_material
		core_material.shader = smoke_core_shader()
		# Drawn before the textured edge puffs, which layer softly over it.
		core_material.render_priority = 0
		core_material.set_shader_parameter("cloud_noise", smoke_texture())
		core.material_override = core_material
		core.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(core)
		_cloud_puffs.append(core)
		var puff_count := 6 if high_quality_smoke else 3
		var material := StandardMaterial3D.new()
		_puff_material = material
		material.albedo_texture = smoke_texture()
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		material.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
		material.cull_mode = BaseMaterial3D.CULL_DISABLED
		material.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
		material.render_priority = 1
		for i in range(puff_count):
			var layout: Array = PUFF_LAYOUT[i if high_quality_smoke else LOW_PUFFS[i]]
			var puff := MeshInstance3D.new()
			var quad := QuadMesh.new()
			quad.size = layout[1]
			puff.mesh = quad
			puff.material_override = material
			puff.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			add_child(puff)
			puff.position = layout[0]
			_cloud_puffs.append(puff)
		for puff in _cloud_puffs:
			puff.scale = Vector3.ONE * 0.2
			var grow := puff.create_tween()
			grow.tween_property(puff, "scale", Vector3.ONE, 0.8)

	else:
		_lifetime = 0.45
		for actor in ([] if visual_only else get_tree().get_nodes_in_group("combatants")):
			if not actor.alive or actor.team == owner_team:
				continue
			var to: Vector3 = actor.global_position + Vector3.UP * 0.9
			var distance := global_position.distance_to(to)
			if distance > 6:
				continue
			var query := PhysicsRayQueryParameters3D.create(global_position, to, 1)
			if get_world_3d().direct_space_state.intersect_ray(query).is_empty():
				actor.apply_damage(90.0 * (1.0 - distance / 6.0), owner_id, false)
		_mesh.visible = true
		var mat := _mesh.material_override as StandardMaterial3D
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.albedo_color = Color("ffd588")
		var burst := create_tween()
		burst.tween_property(_mesh, "scale", Vector3.ONE * 24, 0.09)
		burst.parallel().tween_property(mat, "albedo_color", Color("c98455"), 0.12)
		burst.tween_property(_mesh, "scale", Vector3.ONE * 0.01, 0.3)
		var audio := AudioStreamPlayer3D.new()
		audio.stream = SBActor._synthesize_sound(0.38, 42, 0.70)
		audio.volume_db = -5
		audio.max_distance = 65
		audio.unit_size = 12
		add_child(audio)
		audio.play()
