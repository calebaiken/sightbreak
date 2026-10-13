class_name SBActor
extends CharacterBody3D

signal eliminated(victim_id: int, killer_id: int)
signal damage_taken(victim_id: int, attacker_id: int, amount: float)
signal shot_fired(actor_id: int, origin: Vector3, direction: Vector3)
signal utility_deployed(actor_id: int, at: Vector3, kind: String)

const Weapons = preload("res://scripts/gameplay/weapons.gd")
const Utility = preload("res://scripts/gameplay/utility.gd")
const WALK_SPEED := 5.1
const CROUCH_SPEED := 2.5
const GRAVITY := 22.0
var actor_id: int = 0
var team: int = 0
var display_name: String = "Operator"
var is_local: bool = false
var alive: bool = true
var health: float = 100.0
var kills: int = 0
var assists: int = 0
var deaths: int = 0
var credits: int = 800
var weapon_id: String = "sidearm"
var ammo: int = 15
var reserve: int = 60
var input_state: Dictionary = {}
var yaw: float = 0.0
var pitch: float = 0.0
var camera: Camera3D
var head_height: float = 1.62
var grenades: int = 1
var smokes: int = 1
var reload_remaining: float = 0.0
var recoil := Vector2.ZERO
var last_hit_headshot: bool = false
var inventory: Array[String] = ["sidearm"]
var _ammo_store: Dictionary = {}
var _body: Node3D
var _body_team: int = -1
var _head: MeshInstance3D
var _gun: Node3D
var _muzzle: MeshInstance3D
var _collision: CollisionShape3D
var _cooldown: float = 0.0
var _shot_index: int = 0
var _fire_previous: bool = false
var _grenade_previous: bool = false
var _smoke_previous: bool = false
var _jump_previous: bool = false
var _bob: float = 0.0
var _kick: float = 0.0
var _flash: float = 0.0
var _crouching: bool = false
var _gun_color := Color("9aabb5")
var _paint_parts: Array[MeshInstance3D] = []
var _cosmetic: Dictionary = {}
var _finish: ShaderMaterial
var _rng := RandomNumberGenerator.new()
var _shot_audio: AudioStreamPlayer3D
var _hurt_audio: AudioStreamPlayer3D
static var _shot_stream: AudioStreamWAV
static var _hurt_stream: AudioStreamWAV

func configure(id: int, side: int, label: String, local: bool = false) -> void:
	actor_id = id
	team = side
	display_name = label
	is_local = local
	_rng.seed = id * 7919 + 103

func _ready() -> void:
	add_to_group("combatants")
	collision_layer = 2
	collision_mask = 3
	floor_snap_length = 0.3
	_collision = CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.31
	capsule.height = 1.8
	_collision.shape = capsule
	_collision.position.y = 0.9
	add_child(_collision)
	_body = Node3D.new()
	add_child(_body)
	_build_body()
	camera = Camera3D.new()
	camera.position.y = head_height
	camera.fov = 82
	camera.near = 0.045
	camera.far = 120
	camera.current = is_local
	add_child(camera)
	_gun = Node3D.new()
	camera.add_child(_gun)
	_build_gun()
	_body.visible = not is_local
	_gun.visible = is_local
	_shot_audio = AudioStreamPlayer3D.new()
	_shot_audio.max_distance = 65
	_shot_audio.unit_size = 9
	_shot_audio.volume_db = -10
	_shot_audio.position.y = head_height
	add_child(_shot_audio)
	_hurt_audio = AudioStreamPlayer3D.new()
	_hurt_audio.max_distance = 18
	_hurt_audio.volume_db = -13
	add_child(_hurt_audio)
	if _shot_stream == null:
		_shot_stream = _synthesize_sound(0.12, 145, 0.85)
		_hurt_stream = _synthesize_sound(0.08, 65, 0.25)
	_shot_audio.stream = _shot_stream
	_hurt_audio.stream = _hurt_stream

static func _synthesize_sound(duration: float, frequency: float, noise: float) -> AudioStreamWAV:
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = 22050
	var count := int(duration * stream.mix_rate)
	var data := PackedByteArray()
	data.resize(count * 2)
	var rng := RandomNumberGenerator.new()
	rng.seed = 711
	for i in range(count):
		var t := float(i) / stream.mix_rate
		var envelope := pow(1.0 - float(i) / count, 3.0)
		var wave := (sin(t * TAU * frequency * (1.0 - t * 3.0)) * (1.0 - noise) + rng.randf_range(-1.0, 1.0) * noise) * envelope * 0.75
		data.encode_s16(i * 2, int(wave * 32767))
	stream.data = data
	return stream

func _part(parent: Node3D, at: Vector3, dimensions: Vector3, color: Color) -> MeshInstance3D:
	var visual := MeshInstance3D.new()
	var shape := BoxMesh.new()
	shape.size = dimensions
	visual.mesh = shape
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = 0.65
	visual.material_override = material
	parent.add_child(visual)
	visual.position = at
	return visual

func _build_body() -> void:
	for child in _body.get_children():
		_body.remove_child(child)
		child.queue_free()
	_body_team = team
	var uniform := Color("bb8153") if team == 0 else Color("518caa")
	_part(_body, Vector3(0, 1.03, 0), Vector3(0.57, 0.63, 0.31), uniform)
	_part(_body, Vector3(0, 1.08, -0.18), Vector3(0.46, 0.45, 0.13), Color("29333a"))
	for x in [-0.16, 0.16]:
		_part(_body, Vector3(x, 0.45, 0), Vector3(0.23, 0.83, 0.24), uniform.darkened(0.25))
		_part(_body, Vector3(x, 0.13, -0.07), Vector3(0.25, 0.23, 0.40), Color("263038"))
		_part(_body, Vector3(x * 2.1, 1.05, -0.12), Vector3(0.19, 0.40, 0.25), uniform)
	_head = _part(_body, Vector3(0, 1.58, 0), Vector3(0.37, 0.40, 0.36), Color("36434c"))
	_part(_head, Vector3(0, -0.03, -0.19), Vector3(0.32, 0.11, 0.035), Color("c4e4e3"))
	_part(_body, Vector3(0.20, 1.12, -0.40), Vector3(0.11, 0.13, 0.65), Color("1b242b"))

func _chamfer(at: Vector3, size: Vector3, tint: Color, painted: bool = false) -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var x := size.x * 0.5
	var y := size.y * 0.5
	var z := size.z * 0.5
	var b := minf(x, y) * 0.32
	var ring := [Vector2(-x + b, -y), Vector2(x - b, -y), Vector2(x, -y + b), Vector2(x, y - b), Vector2(x - b, y), Vector2(-x + b, y), Vector2(-x, y - b), Vector2(-x, -y + b)]
	for i in range(8):
		var a: Vector2 = ring[i]
		var c: Vector2 = ring[(i + 1) % 8]
		var front_a := Vector3(a.x, a.y, -z)
		var front_b := Vector3(c.x, c.y, -z)
		var back_a := Vector3(a.x, a.y, z)
		var back_b := Vector3(c.x, c.y, z)
		var vertices := [front_a, front_b, back_b, front_a, back_b, back_a, Vector3(0, 0, -z), front_b, front_a, Vector3(0, 0, z), back_a, back_b]
		# Godot front faces use clockwise winding.
		for triangle in range(0, vertices.size(), 3):
			st.add_vertex(vertices[triangle])
			st.add_vertex(vertices[triangle + 2])
			st.add_vertex(vertices[triangle + 1])
	st.generate_normals()
	mesh.mesh = st.commit()
	var material := StandardMaterial3D.new()
	material.albedo_color = tint
	material.roughness = 0.58
	material.metallic = 0.35
	mesh.material_override = material
	_gun.add_child(mesh)
	mesh.position = at
	if painted:
		_paint_parts.append(mesh)
	return mesh

func _sleeve(from: Vector3, to: Vector3, tint: Color) -> void:
	var sleeve := _chamfer((from + to) * 0.5, Vector3(0.11, 0.105, from.distance_to(to)), tint)
	sleeve.quaternion = Quaternion(Vector3.FORWARD, (to - from).normalized())

func _barrel(at: Vector3, length: float, radius: float, tint: Color) -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	var shape := CylinderMesh.new()
	shape.top_radius = radius
	shape.bottom_radius = radius
	shape.height = length
	shape.radial_segments = 12
	mesh.mesh = shape
	var material := StandardMaterial3D.new()
	material.albedo_color = tint
	material.metallic = 0.5
	material.roughness = 0.5
	mesh.material_override = material
	_gun.add_child(mesh)
	mesh.position = at
	mesh.rotation.x = PI * 0.5
	return mesh

func _build_gun() -> void:
	for child in _gun.get_children():
		_gun.remove_child(child)
		child.queue_free()
	_paint_parts.clear()
	_gun_color = Weapons.get_weapon(weapon_id)["color"]
	var metal := Color("151c23")
	var edge := Color("323e48")
	var glove := Color("343c39")
	var muzzle_z := -0.35
	if weapon_id == "sidearm":
		_chamfer(Vector3(0, 0.022, -0.16), Vector3(0.085, 0.075, 0.31), edge, true)
		_chamfer(Vector3(0, -0.023, -0.12), Vector3(0.074, 0.052, 0.26), metal)
		var grip := _chamfer(Vector3(0, -0.105, -0.017), Vector3(0.066, 0.16, 0.09), metal)
		grip.rotation.x = -0.23
		_barrel(Vector3(0, 0.019, -0.32), 0.07, 0.022, metal)
		_barrel(Vector3(0, 0.019, -0.357), 0.005, 0.014, Color("03070b"))
		# A real open rear notch, fine front sight, ejection port, slide serrations.
		for x in [-0.026, 0.026]:
			_chamfer(Vector3(x, 0.074, -0.025), Vector3(0.018, 0.029, 0.025), metal)
		_chamfer(Vector3(0, 0.072, -0.279), Vector3(0.014, 0.020, 0.021), Color("96b2a0"))
		_chamfer(Vector3(0.043, 0.03, -0.13), Vector3(0.003, 0.028, 0.061), Color("060c10"))
		for i in range(5):
			_chamfer(Vector3(0.044, 0.017, 0.0 - i * 0.012), Vector3(0.006, 0.057, 0.004), metal)
		# Trigger guard encloses open air rather than a solid rectangular block.
		_chamfer(Vector3(0, -0.073, -0.107), Vector3(0.046, 0.009, 0.080), metal)
		_chamfer(Vector3(0, -0.046, -0.147), Vector3(0.046, 0.060, 0.009), metal)
		_chamfer(Vector3(0, -0.049, -0.102), Vector3(0.009, 0.031, 0.008), edge)
		_chamfer(Vector3(0.015, -0.132, 0.037), Vector3(0.11, 0.10, 0.105), glove)
		_sleeve(Vector3(0.11, -0.37, 0.43), Vector3(0.022, -0.16, 0.085), Color("28353c"))
		var support := _chamfer(Vector3(-0.055, -0.143, 0.065), Vector3(0.09, 0.09, 0.13), glove)
		support.rotation.z = 0.24
		for i in range(3):
			_chamfer(Vector3(0.059, -0.12 + i * 0.018, -0.005), Vector3(0.016, 0.014, 0.076), glove.lightened(0.045))
	else:
		_chamfer(Vector3(0, 0, -0.15), Vector3(0.104, 0.113, 0.30), edge, true)
		_chamfer(Vector3(0, 0.007, -0.405), Vector3(0.092, 0.10, 0.23), edge, true)
		_barrel(Vector3(0, 0.025, -0.59), 0.22, 0.023, metal)
		_barrel(Vector3(0, 0.025, -0.72), 0.07, 0.031, edge)
		_barrel(Vector3(0, 0.025, -0.758), 0.005, 0.021, Color("03070b"))
		muzzle_z = -0.77
		_chamfer(Vector3(0, 0.071, -0.26), Vector3(0.052, 0.018, 0.39), metal)
		for i in range(13):
			_chamfer(Vector3(0, 0.083, -0.06 - i * 0.029), Vector3(0.058, 0.009, 0.008), edge)
		for i in range(5):
			_chamfer(Vector3(0.048, 0.016, -0.32 - i * 0.033), Vector3(0.004, 0.020, 0.018), metal)
		var magazine := _chamfer(Vector3(0, -0.15, -0.245), Vector3(0.064, 0.23, 0.10), metal, true)
		magazine.rotation.x = 0.10
		var grip := _chamfer(Vector3(0, -0.12, -0.034), Vector3(0.07, 0.15, 0.085), metal)
		grip.rotation.x = -0.23
		_chamfer(Vector3(0, -0.032, 0.085), Vector3(0.085, 0.11, 0.18), metal)
		_chamfer(Vector3(0.052, 0.015, -0.105), Vector3(0.005, 0.041, 0.065), metal)
		# Compact bridge sight preserves center-screen target readability.
		for x in [-0.026, 0.026]:
			_chamfer(Vector3(x, 0.12, -0.16), Vector3(0.010, 0.071, 0.048), metal)
		_chamfer(Vector3(0, 0.16, -0.16), Vector3(0.062, 0.010, 0.048), metal)
		_chamfer(Vector3(0.035, -0.136, 0.017), Vector3(0.105, 0.10, 0.105), glove)
		_sleeve(Vector3(0.16, -0.36, 0.43), Vector3(0.035, -0.16, 0.07), Color("28353c"))
		var support := _chamfer(Vector3(-0.08, -0.10, -0.40), Vector3(0.14, 0.085, 0.13), glove)
		support.rotation.z = 0.4
		_sleeve(Vector3(-0.31, -0.35, 0.04), Vector3(-0.09, -0.11, -0.35), Color("28353c"))
	_muzzle = _part(_gun, Vector3(0, 0.025, muzzle_z), Vector3(0.11, 0.075, 0.15), Color("ffda8c"))
	var mat := _muzzle.material_override as StandardMaterial3D
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_muzzle.visible = false
	for child in _gun.get_children():
		if child is MeshInstance3D:
			child.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_gun.position = Vector3(0.23, -0.22, -0.36)
	apply_cosmetic(_cosmetic)

func apply_cosmetic(metadata: Dictionary) -> void:
	# Appearance alone: no match state, prices, damage, ammo, or timing changes.
	_cosmetic = metadata.duplicate(true)
	if _finish == null:
		_finish = ShaderMaterial.new()
		var shader := Shader.new()
		shader.code = """shader_type spatial;
uniform vec4 base_paint : source_color = vec4(0.2,0.25,0.3,1.0);
uniform vec4 accent_paint : source_color = vec4(0.35,0.42,0.40,1.0);
uniform float pattern_seed = 1.0;
uniform float wear = 0.0;
uniform float patterned = 0.0;
varying vec3 local_position;
void vertex() { local_position = VERTEX; }
void fragment() {
 float band = step(0.45, sin(local_position.z * 95.0 + local_position.x * 55.0 + pattern_seed));
 float grain = fract(sin(dot(floor(local_position * 580.0),vec3(12.98,78.23,31.18)) + pattern_seed) * 43758.54);
 vec3 paint = mix(base_paint.rgb, accent_paint.rgb, band * patterned * 0.55);
 ALBEDO = mix(paint, vec3(0.23,0.25,0.26), step(1.0-wear*0.24,grain));
 ROUGHNESS = 0.6 + wear * 0.2;
 METALLIC = 0.28;
}"""
		_finish.shader = shader
	var rarity := str(metadata.get("rarity", "common")).to_lower()
	var palette := {"common": Color("526774"), "uncommon": Color("3f7566"), "rare": Color("365988"), "epic": Color("755694"), "legendary": Color("9f7d46"), "mythic": Color("922c44")}
	var paint: Color = palette.get(rarity, Color("526774"))
	if metadata.is_empty():
		paint = Color("35414a") if weapon_id == "sidearm" else _gun_color.darkened(0.48)
	_finish.set_shader_parameter("base_paint", paint)
	_finish.set_shader_parameter("accent_paint", paint.lightened(0.3))
	_finish.set_shader_parameter("pattern_seed", float(int(metadata.get("pattern_seed", metadata.get("seed", 1))) % 10000))
	_finish.set_shader_parameter("wear", clampf(float(metadata.get("wear", 0.05)), 0, 1))
	_finish.set_shader_parameter("patterned", 0.0 if metadata.is_empty() else 1.0)
	for part in _paint_parts:
		part.material_override = _finish

func _exit_tree() -> void:
	if is_instance_valid(_shot_audio):
		_shot_audio.stop()
	if is_instance_valid(_hurt_audio):
		_hurt_audio.stop()

func reset_for_round(spawn: Vector3) -> void:
	if _body_team != team:
		_build_body()
	for id in inventory:
		var definition := Weapons.get_weapon(id)
		_ammo_store[id] = Vector2i(int(definition["magazine"]), int(definition["reserve"]))
	global_position = spawn
	velocity = Vector3.ZERO
	alive = true
	health = 100
	_crouching = false
	_collision.disabled = false
	_body.visible = not is_local
	_gun.visible = is_local
	_collision.shape.height = 1.8
	_collision.position.y = 0.9
	yaw = PI if team == 0 else 0.0
	pitch = 0
	rotation.y = yaw
	camera.rotation = Vector3.ZERO
	reload_remaining = 0
	_cooldown = 0
	recoil = Vector2.ZERO
	grenades = 1
	smokes = 1
	_fire_previous = false
	_grenade_previous = false
	_smoke_previous = false
	_jump_previous = false
	input_state.clear()
	var spec := Weapons.get_weapon(weapon_id)
	ammo = int(spec["magazine"])
	reserve = int(spec["reserve"])

func tick_authority(delta: float) -> void:
	if not alive:
		return
	var look: Vector2 = input_state.get("look", Vector2(yaw, pitch))
	if is_finite(look.x) and is_finite(look.y):
		yaw = wrapf(look.x, -PI, PI)
		pitch = clampf(look.y, -1.42, 1.42)
	rotation.y = yaw
	var requested_crouch: bool = input_state.get("crouch", false)
	# Standing requires room overhead; never expand the capsule into a solid ceiling.
	if requested_crouch or not _crouching or _can_stand():
		_crouching = requested_crouch
	_collision.shape.height = 1.25 if _crouching else 1.8
	_collision.position.y = 0.625 if _crouching else 0.9
	head_height = 1.13 if _crouching else 1.62
	_body.scale.y = 0.72 if _crouching else 1.0
	var move: Vector2 = input_state.get("move", Vector2.ZERO)
	if not is_finite(move.x) or not is_finite(move.y):
		move = Vector2.ZERO
	move = move.limit_length(1.0)
	var direction := global_basis * Vector3(move.x, 0, -move.y)
	var speed := CROUCH_SPEED if _crouching else WALK_SPEED
	var acceleration := 28.0 if is_on_floor() else 7.0
	velocity.x = move_toward(velocity.x, direction.x * speed, acceleration * delta)
	velocity.z = move_toward(velocity.z, direction.z * speed, acceleration * delta)
	if not is_on_floor():
		velocity.y -= GRAVITY * delta
	var jump: bool = input_state.get("jump", false)
	if jump and not _jump_previous and is_on_floor() and not _crouching:
		velocity.y = 6.4
	_jump_previous = jump
	move_and_slide()
	_cooldown = maxf(0, _cooldown - delta)
	recoil = recoil.move_toward(Vector2.ZERO, delta * 0.11)
	if reload_remaining > 0:
		reload_remaining = maxf(0, reload_remaining - delta)
		if reload_remaining == 0:
			var amount := mini(int(Weapons.get_weapon(weapon_id)["magazine"]) - ammo, reserve)
			ammo += amount
			reserve -= amount
	var requested_weapon: String = input_state.get("weapon", "")
	if not requested_weapon.is_empty() and requested_weapon != weapon_id and inventory.has(requested_weapon):
		_equip(requested_weapon)
	if input_state.get("reload", false):
		start_reload()
	var firing: bool = input_state.get("fire", false)
	var automatic: bool = Weapons.get_weapon(weapon_id)["automatic"]
	if firing and (automatic or not _fire_previous) and _cooldown <= 0 and reload_remaining <= 0:
		if ammo > 0:
			_fire()
		else:
			start_reload()
	_fire_previous = firing
	var grenade: bool = input_state.get("grenade", false)
	var smoke: bool = input_state.get("smoke", false)
	if grenade and not _grenade_previous and grenades > 0:
		_deploy_utility("grenade")
	if smoke and not _smoke_previous and smokes > 0:
		_deploy_utility("smoke")
	_grenade_previous = grenade
	_smoke_previous = smoke
	camera.position.y = head_height
	camera.rotation.x = pitch + recoil.y
	camera.rotation.y = recoil.x

func _can_stand() -> bool:
	var query := PhysicsRayQueryParameters3D.create(global_position + Vector3.UP * 1.1, global_position + Vector3.UP * 1.85, 1, [get_rid()])
	return get_world_3d().direct_space_state.intersect_ray(query).is_empty()

func start_reload() -> void:
	var spec := Weapons.get_weapon(weapon_id)
	if reload_remaining <= 0 and ammo < int(spec["magazine"]) and reserve > 0:
		reload_remaining = float(spec["reload"])
		_shot_index = 0

func _equip(id: String) -> void:
	_ammo_store[weapon_id] = Vector2i(ammo, reserve)
	weapon_id = id
	var spec := Weapons.get_weapon(id)
	var stored: Vector2i = _ammo_store.get(id, Vector2i(int(spec["magazine"]), int(spec["reserve"])))
	ammo = stored.x
	reserve = stored.y
	reload_remaining = 0
	_cooldown = 0.3
	recoil = Vector2.ZERO
	_shot_index = 0
	_build_gun()

func buy_weapon(id: String) -> bool:
	if not alive or not Weapons.DATA.has(id):
		return false
	var spec := Weapons.get_weapon(id)
	var cost := int(spec["cost"])
	if credits < cost or inventory.has(id):
		return false
	credits -= cost
	inventory.append(id)
	_equip(id)
	return true

func _fire() -> void:
	var spec := Weapons.get_weapon(weapon_id)
	ammo -= 1
	_cooldown = float(spec["interval"])
	var moving := Vector2(velocity.x, velocity.z).length() / WALK_SPEED
	var spread := float(spec["spread"]) + moving * 0.026 + (0.045 if not is_on_floor() else 0.0)
	if _crouching:
		spread *= 0.6
	var shot_yaw := yaw + recoil.x + _rng.randf_range(-spread, spread)
	var shot_pitch := pitch + recoil.y + _rng.randf_range(-spread, spread)
	var direction := Vector3(-sin(shot_yaw) * cos(shot_pitch), sin(shot_pitch), -cos(shot_yaw) * cos(shot_pitch)).normalized()
	var origin := global_position + Vector3.UP * head_height
	var endpoint := origin + direction * float(spec["range"])
	var query := PhysicsRayQueryParameters3D.create(origin, endpoint, 3, [get_rid()])
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	if not hit.is_empty():
		endpoint = hit["position"]
		var target: Object = hit["collider"]
		if target is SBActor and target.team != team and target.alive:
			var headshot: bool = endpoint.y > target.global_position.y + target.head_height - 0.25
			var distance_ratio := clampf(origin.distance_to(endpoint) / float(spec["range"]), 0, 1)
			var amount := float(spec["damage"]) * lerpf(1, float(spec["falloff"]), distance_ratio)
			if headshot:
				amount *= float(spec["head"])
			target.apply_damage(amount, actor_id, headshot)
		_impact(endpoint, hit["normal"], target is SBActor)
	shot_fired.emit(actor_id, origin, direction)
	play_shot_effect()
	_shot_index += 1
	recoil.y = minf(recoil.y + float(spec["recoil"]), 0.16)
	recoil.x += sin(_shot_index * 1.7) * float(spec["recoil"]) * 0.55

func play_shot_effect() -> void:
	_kick = 1
	_flash = 0.055
	if _shot_audio != null:
		_shot_audio.pitch_scale = 1.2 if weapon_id == "smg" else (0.7 if weapon_id == "marksman" else 1.0)
		_shot_audio.play()

func _impact(at: Vector3, normal: Vector3, hit_actor: bool) -> void:
	var spark := MeshInstance3D.new()
	var mesh := SphereMesh.new()
	mesh.radius = 0.055
	mesh.height = 0.11
	spark.mesh = mesh
	var material := StandardMaterial3D.new()
	material.albedo_color = Color("e5b574") if hit_actor else Color("e8dfb1")
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	spark.material_override = material
	get_parent().add_child(spark)
	spark.global_position = at + normal * 0.025
	var tween := spark.create_tween()
	tween.tween_property(spark, "scale", Vector3.ONE * 0.05, 0.13)
	tween.tween_callback(spark.queue_free)

func _deploy_utility(kind: String) -> void:
	if kind == "grenade":
		grenades -= 1
	else:
		smokes -= 1
	var utility := Utility.new()
	utility.kind = kind
	utility.owner_id = actor_id
	utility.owner_team = team
	utility.velocity = Vector3(-sin(yaw) * cos(pitch), sin(pitch) + 0.28, -cos(yaw) * cos(pitch)).normalized() * 13
	get_parent().add_child(utility)
	utility.global_position = global_position + Vector3.UP * head_height
	utility_deployed.emit(actor_id, utility.global_position, kind)

func apply_damage(amount: float, attacker_id: int, headshot: bool = false) -> void:
	if not alive or not is_finite(amount) or amount <= 0:
		return
	var actual := minf(health, amount)
	health = maxf(0, health - amount)
	last_hit_headshot = headshot
	damage_taken.emit(actor_id, attacker_id, actual)
	_hurt_audio.play()
	if health <= 0:
		alive = false
		velocity = Vector3.ZERO
		_collision.set_deferred("disabled", true)
		_body.visible = false
		_gun.visible = false
		eliminated.emit(actor_id, attacker_id)

func can_see(other: SBActor) -> bool:
	if not other.alive:
		return false
	var from := global_position + Vector3.UP * head_height
	var to := other.global_position + Vector3.UP * other.head_height
	for cloud in get_tree().get_nodes_in_group("smoke_clouds"):
		var nearest := Geometry3D.get_closest_point_to_segment(cloud.global_position, from, to)
		if nearest.distance_to(cloud.global_position) < 3.2:
			return false
	var query := PhysicsRayQueryParameters3D.create(from, to, 3, [get_rid()])
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	return hit.is_empty() or hit.get("collider") == other

func tick_visual(delta: float) -> void:
	if camera == null:
		return
	_bob += delta * Vector2(velocity.x, velocity.z).length() * 1.8
	_kick = move_toward(_kick, 0, delta * 9)
	_flash = maxf(0, _flash - delta)
	_muzzle.visible = _flash > 0 and alive
	if is_local:
		var reload_tilt := sin(clampf(reload_remaining / maxf(0.1, float(Weapons.get_weapon(weapon_id)["reload"])), 0, 1) * PI)
		_gun.position = Vector3(0.23 + sin(_bob) * 0.006, -0.22 + absf(cos(_bob)) * 0.006 - reload_tilt * 0.20, -0.36 + _kick * 0.045)
		_gun.rotation = Vector3(_kick * 0.07 - reload_tilt * 0.5, 0, reload_tilt * 0.5)

func snapshot() -> Dictionary:
	return {"id": actor_id, "team": team, "name": display_name, "position": global_position, "velocity": velocity, "yaw": yaw, "pitch": pitch, "health": health, "alive": alive, "kills": kills, "deaths": deaths, "assists": assists, "credits": credits, "weapon": weapon_id, "ammo": ammo, "reserve": reserve, "reload": reload_remaining, "grenades": grenades, "smokes": smokes, "crouch": _crouching, "inventory": inventory.duplicate()}

func apply_snapshot(data: Dictionary, delta: float) -> void:
	team = int(data.get("team", team))
	if _body_team != team:
		_build_body()
	var at: Vector3 = data.get("position", global_position)
	global_position = at if is_local else global_position.lerp(at, clampf(delta * 18, 0, 1))
	velocity = data.get("velocity", Vector3.ZERO)
	yaw = float(data.get("yaw", yaw))
	pitch = float(data.get("pitch", pitch))
	rotation.y = yaw
	health = float(data.get("health", health))
	alive = bool(data.get("alive", alive))
	kills = int(data.get("kills", kills))
	deaths = int(data.get("deaths", deaths))
	assists = int(data.get("assists", assists))
	credits = int(data.get("credits", credits))
	ammo = int(data.get("ammo", ammo))
	reserve = int(data.get("reserve", reserve))
	grenades = int(data.get("grenades", grenades))
	smokes = int(data.get("smokes", smokes))
	reload_remaining = float(data.get("reload", 0))
	_crouching = bool(data.get("crouch", false))
	head_height = 1.13 if _crouching else 1.62
	_body.scale.y = 0.72 if _crouching else 1.0
	_collision.shape.height = 1.25 if _crouching else 1.8
	_collision.position.y = 0.625 if _crouching else 0.9
	_collision.disabled = not alive
	_body.visible = alive and not is_local
	_gun.visible = alive and is_local
	camera.position.y = head_height
	camera.rotation.x = pitch
	var next_weapon: String = data.get("weapon", weapon_id)
	if next_weapon != weapon_id and Weapons.DATA.has(next_weapon):
		weapon_id = next_weapon
		_build_gun()
	if data.has("inventory"):
		inventory.assign(data["inventory"])
