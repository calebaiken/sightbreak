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
static var _smoke_shader: Shader

static func smoke_shader() -> Shader:
	if _smoke_shader == null:
		_smoke_shader = Shader.new()
		_smoke_shader.code = """shader_type spatial;
render_mode diffuse_burley;
uniform vec4 smoke_tint : source_color;
varying float billow;
void vertex() {
 billow = sin(VERTEX.x*3.8 + VERTEX.y*2.9) * sin(VERTEX.z*4.2-VERTEX.y*2.1);
 VERTEX += NORMAL * billow * 0.12;
}
void fragment() {
 ALBEDO = smoke_tint.rgb * (0.94 + billow*0.055);
 ROUGHNESS = 1.0;
}
"""
	return _smoke_shader

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
		for i in range(11):
			var puff := MeshInstance3D.new()
			var sphere := SphereMesh.new()
			sphere.radius = 1.7
			sphere.height = 3.4
			sphere.radial_segments = 16
			sphere.rings = 8
			puff.mesh = sphere
			var material := ShaderMaterial.new()
			material.shader = smoke_shader()
			material.set_shader_parameter("smoke_tint", Color("7c898e").lightened(float(i % 3) * 0.04))
			puff.material_override = material
			puff.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			add_child(puff)
			puff.position = Vector3(sin(i * 2.4) * 1.35, cos(i * 1.9) * 0.48, cos(i * 2.4) * 1.35)
			_cloud_puffs.append(puff)
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
