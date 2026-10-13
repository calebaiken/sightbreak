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
		_smoke_core_shader.code = """shader_type spatial;
render_mode unshaded, cull_disabled;
uniform sampler2D cloud_noise : source_color, filter_linear_mipmap, repeat_enable;
varying vec3 cloud_position;
varying vec3 cloud_normal;
void vertex() {
 float billow = sin(VERTEX.x*1.7+0.5)*sin(VERTEX.y*1.5)*sin(VERTEX.z*1.4+1.0);
 VERTEX += NORMAL * billow * 0.30;
 cloud_position = VERTEX; cloud_normal = NORMAL;
}
void fragment() {
 vec3 weights = abs(cloud_normal);
 weights /= max(weights.x + weights.y + weights.z, 0.001);
 ALBEDO = texture(cloud_noise, cloud_position.yz * 0.14 + 0.5).rgb * weights.x
        + texture(cloud_noise, cloud_position.xz * 0.14 + 0.5).rgb * weights.y
        + texture(cloud_noise, cloud_position.xy * 0.14 + 0.5).rgb * weights.z;
 ROUGHNESS = 1.0;
}
"""
	return _smoke_core_shader

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
		global_position.y = 1.6
		add_to_group("smoke_clouds")
		# A closed opaque core preserves concealment even inside the cloud. Only
		# the boundary uses alpha: at most six quads (three in Low), no lights.
		var core := MeshInstance3D.new()
		var sphere := SphereMesh.new()
		sphere.radius = 2.15
		sphere.height = 4.1
		sphere.radial_segments = 24
		sphere.rings = 12
		core.mesh = sphere
		var core_material := ShaderMaterial.new()
		core_material.shader = smoke_core_shader()
		core_material.set_shader_parameter("cloud_noise", smoke_texture())
		core.material_override = core_material
		core.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(core)
		_cloud_puffs.append(core)
		var puff_count := 6 if high_quality_smoke else 3
		var material := StandardMaterial3D.new()
		material.albedo_texture = smoke_texture()
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		material.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
		material.cull_mode = BaseMaterial3D.CULL_DISABLED
		material.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
		for i in range(puff_count):
			var puff := MeshInstance3D.new()
			var quad := QuadMesh.new()
			quad.size = Vector2(4.7, 4.7)
			puff.mesh = quad
			puff.material_override = material
			puff.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			add_child(puff)
			puff.position = Vector3(sin(i * TAU / puff_count) * 0.88, cos(i * 2.1) * 0.28, cos(i * TAU / puff_count) * 0.88)
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
