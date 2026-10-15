class_name SBActor
extends CharacterBody3D

signal eliminated(victim_id: int, killer_id: int)
signal damage_taken(victim_id: int, attacker_id: int, amount: float)
signal shot_fired(actor_id: int, origin: Vector3, direction: Vector3)
signal impact_created(at: Vector3, normal: Vector3, hit_actor: bool)
signal hit_confirmed(attacker_id: int, headshot: bool, lethal: bool)
signal utility_deployed(actor_id: int, at: Vector3, kind: String)

const Weapons = preload("res://scripts/gameplay/weapons.gd")
const CombatEffects = preload("res://scripts/gameplay/combat_effects.gd")
const WeaponModel = preload("res://scripts/gameplay/weapon_model.gd")
const Utility = preload("res://scripts/gameplay/utility.gd")
const CosmeticMaterial = preload("res://scripts/ui/cosmetic_material.gd")
const ViewmodelShading = preload("res://scripts/gameplay/viewmodel_shading.gd")
const WALK_SPEED := 5.1
const CROUCH_SPEED := 2.5
const GRAVITY := 22.0
const DEPLOY_SECONDS := 0.3
const READY_EPSILON := 0.000001
## Shot volumes. Head: the rendered head and helmet ellipsoids (body space, before
## the crouch squash). Body: exactly the 0.3 movement capsule (same radius, height
## and placement as the collision shape) cut off where the drawn torso ends, so a
## body hit is only ever registered where 0.3 registered one.
const HEAD_VOLUMES := [
	[Vector3(0, 1.56, 0), Vector3(0.16, 0.195, 0.165)],
	[Vector3(0, 1.68, 0.005), Vector3(0.175, 0.1175, 0.18)]
]
const BODY_TOP := 1.38
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
var reduced_motion := false
var _world_muzzle: MeshInstance3D
var hit_feedback_remaining := 0.0
var hit_feedback_headshot := false
var hit_feedback_lethal := false
var _equip_blend := 0.0
var _knees: Array[Node3D] = []
var _arms: Array[Node3D] = []
var _body_materials: Dictionary = {}
var inventory: Array[String] = ["sidearm"]
var _ammo_store: Dictionary = {}
var _body: Node3D
var _body_team: int = -1
var _head: MeshInstance3D
var _gun: Node3D
var _muzzle: MeshInstance3D
var _collision: CollisionShape3D
# Seconds until the equipped weapon is drawn, and until each weapon may cycle
# again. Intervals are tracked per weapon so swapping cannot clear them.
var _deploy_remaining: float = 0.0
var _weapon_cooldowns: Dictionary = {}
var _shot_index: int = 0
var _fire_previous: bool = false
var _grenade_previous: bool = false
var _smoke_previous: bool = false
var _jump_previous: bool = false
var _bob: float = 0.0
var _kick: float = 0.0
var _sway := Vector2.ZERO
var _visual_look := Vector2.ZERO
var _visual_initialized := false
var _magazine: MeshInstance3D
var _magazine_rest := Vector3.ZERO
## Where the first-person weapon node rests, relative to the eye. Authored models move
## it to their own balance point so tilts turn about the middle of the weapon.
const GUN_REST := Vector3(0.235, -0.235, -0.42)
var _gun_rest := GUN_REST
## Ejection port in weapon-node space when the model provides one (authored models).
var _ejection_point := Vector3.INF
# Authored first person: drawn with the viewmodel projection, with rigged arms whose
# reload clip is seeked by reload progress and whose index finger follows the kick.
var _viewmodel := false
var _arms_player: AnimationPlayer
var _arms_skeleton: Skeleton3D
var _arms_time := 0.0
var _trigger_bones: Array[int] = []
var _trigger_rest: Array[Quaternion] = []
## Magazine drop down its own well, in the rifle's space (metres at full extraction), for
## builds without the rigged arms.
const MAGAZINE_DROP := 0.23
## The authored reload's timing lives in SBReloadPhases (reload_phases.gd), the single
## definition tools/art/arms_build.py keys the arms' clip to and the tests measure the imported
## clip against. While a hand holds a magazine (the old one from SBReloadPhases.GRASP to DROP,
## the replacement from ACQUIRE to LETGO) that magazine is posed from the hand bone, so the two
## cannot drift apart; between, the old one falls and the replacement is not yet in view.
var _magazine_rest_transform := Transform3D.IDENTITY
## The magazine's transform in the hand bone's frame while it is held (measured once, at the
## grasp, when the magazine is still in the well). The replacement is held the same way.
var _grip_offset := Transform3D.IDENTITY
var _grip_measured := false
## The replacement magazine: a second instance of the same mesh, a separate visual identity that
## enters the picture at SBReloadPhases.ACQUIRE and is the one in the well after the seat. At the
## end of the reload the first one is shown again in the well (the two are identical, so nothing
## pops). Presentation only: ammunition is Actor.ammo and never reads either.
var _magazine_spare: MeshInstance3D
## Where, and how fast, the old magazine is when the hand lets it go (gun space, measured once from
## the clip) and what it does after: a ballistic fall, a pure function of the reload's progress.
var _drop_origin := Transform3D.IDENTITY
var _drop_velocity := Vector3.ZERO
const DROP_SPIN := 5.5
const DROP_VISIBLE_SECONDS := 0.5
const DROP_GRAVITY := 9.8
var _hand_bone := -1
## How much of the reload's whole-weapon staging a player with reduced motion gets, by variant: the roll (about 26
## degrees in "current") and the lift/shift of the weapon that keeps the hands and the magazine in the frame. "current"
## is what shipped before and stays the default: the choice between the variants is a policy for the project (and ideally
## for players with vestibular sensitivity) to make, not something this build decides; the variants exist so it can be
## made from comparative sequences (docs/reports/media/art-v8/reduced-motion). The hand's own motion in the clip is
## unaffected by all of them (it is part of the reload), and so are the timing, the sounds and the ammunition.
## Each variant sets the components of the reload's presentation separately: `roll` and `lift` scale the rifle's whole-weapon
## staging (ARMS_RELOAD_ROTATION and ARMS_RELOAD_OFFSET), `recoil` the muzzle climb of a shot, and `clip` is the support hand's
## animation: "reload" is the default clip and "reload_calm" the same phases with a shallower reach to the pouch (14 cm down, not
## 22), so that with less staging of the rifle the hand and the forearm are still in the frame at the pickup. Presentation only:
## the timing, the sounds, the ammunition and the authoritative reload are the same in all of them.
const REDUCED_RELOAD_VARIANTS := {
	"current": {"roll": 1.0, "lift": 1.0, "recoil": 1.0, "clip": "reload"},
	"calm": {"roll": 0.4, "lift": 1.3, "recoil": 0.6, "clip": "reload_calm"},
	"still": {"roll": 0.0, "lift": 1.8, "recoil": 0.4, "clip": "reload_calm"},
}
var reduced_variant := "current"
## With rigged arms the support hand performs the reload, so the weapon lifts, moves
## toward the centre and rolls clockwise to keep the magazine and the hand in frame at the
## grab and the seat (fitted through the viewmodel projection; weapon_art_test pins it).
const ARMS_RELOAD_OFFSET := Vector3(-0.05, 0.14, 0.0)
const ARMS_RELOAD_ROTATION := Vector3(0.05, 0.0, -0.45)
var _legs: Array[Node3D] = []
var _flash: float = 0.0
## The muzzle smoke: age in seconds since the last shot (past SMOKE_SECONDS it is hidden), its node and material.
var _smoke_age := 9.0
var _smoke_node: MeshInstance3D
var _smoke_material: ShaderMaterial
const SMOKE_SECONDS := 0.45
const FLASH_SECONDS := 0.040
var _flash_variation := Vector3.ONE
var _crouching: bool = false
var _gun_color := Color("9aabb5")
var _paint_parts: Array[MeshInstance3D] = []
var _cosmetic: Dictionary = {}
var _finish: ShaderMaterial
var _rng := RandomNumberGenerator.new()
var _shot_audio: AudioStreamPlayer3D
var _hurt_audio: AudioStreamPlayer3D
var _reload_audio: SBReloadAudio
var _reload_visual_active := false
## The reload events (SBReloadPhases.EVENTS) this reload has already played: each plays once however the presentation
## clock is corrected, and the next reload starts empty.
var _reload_fired: Dictionary = {}
## A reload that has reached the seat swaps the two magazine nodes when it ends, so the replacement
## really is the magazine in the well afterwards and the next reload takes THAT one out.
var _magazine_swap_pending := false
## The shudder the rifle gives when the magazine is driven home: 1 at the seat click, falling away (presentation
## only; the weight of the action, not part of any aim).
var _seat_kick := 0.0
const SEAT_KICK_OFFSET := Vector3(0.0, -0.007, 0.010)
const SEAT_KICK_TURN := Vector3(0.020, 0.0, 0.010)
const SEAT_KICK_DECAY := 11.0
## The magazine node a hand is holding right now (null when neither is), for the tests and probes.
var _magazine_in_hand: MeshInstance3D
## Emitted when the presentation clock crosses a reload event (SBReloadPhases.EVENTS: unlatch, extract, pouch, land,
## enter, seat; the procedural weapons have only unlatch and seat), on the tick the sound plays and the visible part
## moves. Presentation only.
signal reload_cue(event: String, progress: float)
## The presentation clock's progress at the previous tick, to find the events it crossed.
var _reload_visual_previous := 0.0
## Presentation-only reload clock. Online clients receive reload_remaining at the
## snapshot rate, so posing the weapon from it directly steps the reload clip. This
## clock counts down every visual tick and stays within RELOAD_VISUAL_SLACK seconds below
## the authoritative value. Nothing reads it but the viewmodel pose; it never writes
## reload_remaining, ammunition or any other gameplay state.
const RELOAD_VISUAL_SLACK := 0.1
var _reload_clock := 0.0
static var _shot_streams: Dictionary = {}
static var _hurt_stream: AudioStreamWAV

func configure(id: int, side: int, label: String, local: bool = false) -> void:
	actor_id = id
	team = side
	display_name = label
	is_local = local
	# Authoritative spread must not be predictable from the public actor id.
	_rng.seed = Crypto.new().generate_random_bytes(8).decode_u64(0)

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
	_shot_audio.max_polyphony = 4
	_shot_audio.position.y = head_height
	add_child(_shot_audio)
	_hurt_audio = AudioStreamPlayer3D.new()
	_hurt_audio.max_distance = 18
	_hurt_audio.volume_db = -13
	add_child(_hurt_audio)
	_reload_audio = SBReloadAudio.new()
	add_child(_reload_audio)
	if _shot_streams.is_empty():
		for id in Weapons.DATA:
			_shot_streams[id] = _synthesize_shot(id)
		_hurt_stream = _synthesize_sound(0.08, 65, 0.25)
	_shot_audio.stream = _shot_streams[weapon_id]
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

static func _synthesize_shot(id: String) -> AudioStreamWAV:
	# Original layered transients: a short crack, low body and filtered noise tail.
	# No samples/assets or timing/gameplay rules depend on this presentation.
	var profiles := {
		"sidearm": Vector3(0.18, 155.0, 0.72),
		"smg": Vector3(0.13, 190.0, 0.56),
		"rifle": Vector3(0.23, 105.0, 0.84),
		"marksman": Vector3(0.34, 72.0, 1.0)
	}
	var profile: Vector3 = profiles.get(id, profiles["sidearm"])
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = 22050
	var count := int(profile.x * stream.mix_rate)
	var data := PackedByteArray()
	data.resize(count * 2)
	var rng := RandomNumberGenerator.new()
	rng.seed = 711 + int(profile.y)
	var low_noise := 0.0
	for i in range(count):
		var t := float(i) / stream.mix_rate
		var noise := rng.randf_range(-1.0, 1.0)
		low_noise = lerpf(low_noise, noise, 0.2)
		var crack := noise * exp(-t * 160.0) * 0.62
		var body := sin(TAU * profile.y * t + 0.9 * (1.0 - exp(-t * 35.0))) * exp(-t * 32.0) * 0.4
		var tail := low_noise * exp(-t * 17.0) * profile.z
		var fade := clampf((profile.x - t) / 0.012, 0.0, 1.0)
		var wave := clampf((crack + body + tail) * fade, -0.95, 0.95)
		data.encode_s16(i * 2, int(wave * 32767))
	stream.data = data
	return stream

func _part(parent: Node3D, at: Vector3, dimensions: Vector3, color: Color) -> MeshInstance3D:
	var visual := MeshInstance3D.new()
	visual.mesh = WeaponModel.bevel_mesh(dimensions)
	var material := _body_material(color)
	visual.material_override = material
	parent.add_child(visual)
	visual.position = at
	return visual

func _body_material(color: Color, roughness: float = 0.85, metal: float = 0.0) -> StandardMaterial3D:
	var key := "%s/%.2f/%.2f" % [color.to_html(), roughness, metal]
	if not _body_materials.has(key):
		var material := StandardMaterial3D.new()
		material.albedo_color = color
		material.roughness = roughness
		material.metallic = metal
		_body_materials[key] = material
	return _body_materials[key]

func _rounded(parent: Node3D, at: Vector3, size: Vector3, color: Color) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 0.5
	sphere.height = 1.0
	sphere.radial_segments = 12
	sphere.rings = 6
	node.mesh = sphere
	node.material_override = _body_material(color)
	parent.add_child(node)
	node.position = at
	node.scale = size
	return node

func _limb(parent: Node3D, from: Vector3, to: Vector3, radius: float, color: Color) -> void:
	var node := MeshInstance3D.new()
	var mesh := CapsuleMesh.new()
	mesh.radius = radius
	mesh.height = from.distance_to(to) + radius
	mesh.radial_segments = 10
	mesh.rings = 3
	node.mesh = mesh
	node.material_override = _body_material(color)
	parent.add_child(node)
	node.position = (from + to) * 0.5
	node.quaternion = Quaternion(Vector3.UP, (to - from).normalized())

# One packed operator per side: spawning or switching sides instantiates shared
# meshes instead of rebuilding and re-batching geometry for every actor.
static var _packed_bodies: Dictionary = {}

func _build_body() -> void:
	for child in _body.get_children():
		_body.remove_child(child)
		child.queue_free()
	_legs.clear()
	_knees.clear()
	_arms.clear()
	_body_team = team
	if not _packed_bodies.has(team):
		var template := Node3D.new()
		_construct_body(template, team)
		_packed_bodies[team] = WeaponModel.pack_children(template)
	var instance: Node = (_packed_bodies[team] as PackedScene).instantiate()
	for child in instance.get_children():
		instance.remove_child(child)
		WeaponModel.release_owner(child)
		_body.add_child(child)
	instance.free()
	_collect_body_parts(_body)
	_legs.sort_custom(_by_body_index)
	_knees.sort_custom(_by_body_index)
	_arms.sort_custom(_by_body_index)

static func _by_body_index(a: Node3D, b: Node3D) -> bool:
	return int(a.get_meta("body_index")) < int(b.get_meta("body_index"))

func _collect_body_parts(node: Node) -> void:
	for child in node.get_children():
		match str(child.get_meta("body_role", "")):
			"leg": _legs.append(child)
			"knee": _knees.append(child)
			"arm": _arms.append(child)
			"head": _head = child
			"world_muzzle": _world_muzzle = child
		_collect_body_parts(child)

func _construct_body(root: Node3D, side: int) -> void:
	# Broad muted team fields retain target recognition at distance. Body volume
	# remains entirely within the unchanged competitive capsule/headshot regions.
	var accent := Color("73513b") if side == 0 else Color("335969")
	var uniform := Color("303531") if side == 0 else Color("29343b")
	var dark := Color("182329")
	_rounded(root, Vector3(0, 1.08, 0), Vector3(0.59, 0.68, 0.34), uniform)
	_rounded(root, Vector3(0, 0.82, 0), Vector3(0.44, 0.27, 0.32), uniform.darkened(0.2))
	var vest := _part(root, Vector3(0, 1.10, -0.15), Vector3(0.42, 0.42, 0.16), dark)
	vest.material_override = _body_material(dark)
	for x in [-0.13, 0.0, 0.13]:
		var pouch := _part(root, Vector3(x, 0.99, -0.254), Vector3(0.104, 0.18, 0.065), dark.lightened(0.1))
		pouch.material_override = _body_material(dark.lightened(0.1))
	# Distinct shoulder/arm silhouettes and two-joint legs, not rigid blocks.
	for x in [-0.16, 0.16]:
		var index := 0 if x < 0 else 1
		var leg := Node3D.new()
		root.add_child(leg)
		leg.position = Vector3(x, 0.87, 0)
		leg.set_meta("body_role", "leg")
		leg.set_meta("body_index", index)
		_limb(leg, Vector3.ZERO, Vector3(0, -0.35, 0), 0.105, uniform.darkened(0.14))
		var knee := Node3D.new()
		leg.add_child(knee)
		knee.position.y = -0.35
		knee.set_meta("body_role", "knee")
		knee.set_meta("body_index", index)
		_limb(knee, Vector3.ZERO, Vector3(0, -0.34, 0), 0.088, uniform.darkened(0.22))
		_rounded(knee, Vector3(0, -0.02, -0.084), Vector3(0.15, 0.17, 0.065), dark)
		_rounded(knee, Vector3(0, -0.38, -0.065), Vector3(0.19, 0.17, 0.31), Color("192229"))
		var arm := Node3D.new()
		root.add_child(arm)
		arm.position = Vector3(x * 1.85, 1.31, 0)
		arm.set_meta("body_role", "arm")
		arm.set_meta("body_index", index)
		var elbow := Vector3(x * 0.16, -0.23, 0.015)
		var grip_at := Vector3(-x * 1.5 + 0.07, -0.08, -0.38 if x < 0 else -0.23)
		_limb(arm, Vector3.ZERO, elbow, 0.093, uniform)
		_limb(arm, elbow, grip_at, 0.078, uniform)
		_rounded(arm, grip_at, Vector3(0.12, 0.115, 0.15), dark)
		_rounded(arm, Vector3(x * 0.15, -0.04, 0), Vector3(0.17, 0.20, 0.21), accent)
	var head := _rounded(root, HEAD_VOLUMES[0][0], HEAD_VOLUMES[0][1] * 2.0, dark)
	head.set_meta("body_role", "head")
	# Helmet rim and smoke-tinted visor sit at root scale, not scaled head-local.
	_rounded(root, HEAD_VOLUMES[1][0], HEAD_VOLUMES[1][1] * 2.0, dark.lightened(0.03))
	var visor := _rounded(root, Vector3(0, 1.585, -0.158), Vector3(0.26, 0.065, 0.05), Color("14232a"))
	visor.material_override = _body_material(Color("14232a"), 0.48, 0.1)
	visor.set_meta("separate_material", true)
	_part(root, Vector3(0, 1.705, -0.173), Vector3(0.19, 0.035, 0.018), accent)
	_part(root, Vector3(0, 1.18, -0.244), Vector3(0.21, 0.032, 0.01), accent)
	for x in [-0.20, 0.20]:
		_part(root, Vector3(x, 1.20, -0.172), Vector3(0.052, 0.34, 0.035), dark.lightened(0.055))
	for y in [1.06, 1.13]:
		_part(root, Vector3(0, y, -0.238), Vector3(0.34, 0.016, 0.012), Color("101a20"))
	_part(root, Vector3(0, 1.08, 0.19), Vector3(0.32, 0.35, 0.13), dark)
	# A lightweight world proxy: first-person attachments need no tenfold overhead.
	var rifle := _part(root, Vector3(0.07, 1.26, -0.37), Vector3(0.075, 0.11, 0.44), Color("1b242b"))
	rifle.material_override = _body_material(Color("1b242b"), 0.48, 0.55)
	_part(root, Vector3(0.07, 1.27, -0.65), Vector3(0.029, 0.029, 0.16), dark)
	_part(root, Vector3(0.07, 1.14, -0.38), Vector3(0.054, 0.15, 0.08), dark)
	var muzzle := MeshInstance3D.new()
	var flash := PrismMesh.new()
	flash.size = Vector3(0.085, 0.085, 0.16)
	muzzle.mesh = flash
	var flash_material := StandardMaterial3D.new()
	flash_material.albedo_color = Color("ffda8a")
	flash_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	muzzle.material_override = flash_material
	muzzle.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	muzzle.set_meta("body_role", "world_muzzle")
	root.add_child(muzzle)
	muzzle.position = Vector3(0.07, 1.27, -0.765)
	muzzle.visible = false
	_batch_body_visuals(root)

func _batch_body_visuals(parent: Node3D) -> void:
	# Color-vertex batching keeps articulated operators at one draw per joint;
	# static clothing/gear details do not multiply draw calls for ten players.
	var builder := SurfaceTool.new()
	builder.begin(Mesh.PRIMITIVE_TRIANGLES)
	var added := false
	for child in parent.get_children():
		if child is Node3D and not child is MeshInstance3D:
			_batch_body_visuals(child)
		if not child is MeshInstance3D or child.has_meta("body_role") or child.has_meta("separate_material"):
			continue
		var source := MeshDataTool.new()
		var arrays := ArrayMesh.new()
		arrays.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, child.mesh.surface_get_arrays(0))
		source.create_from_surface(arrays, 0)
		var tint: Color = child.material_override.albedo_color
		for face in range(source.get_face_count()):
			for corner in range(3):
				var index := source.get_face_vertex(face, corner)
				builder.set_color(tint)
				builder.set_normal((child.transform.basis.inverse().transposed() * source.get_vertex_normal(index)).normalized())
				builder.add_vertex(child.transform * source.get_vertex(index))
		parent.remove_child(child)
		child.free()
		added = true
	if added:
		var merged := MeshInstance3D.new()
		merged.mesh = builder.commit()
		var material := StandardMaterial3D.new()
		material.vertex_color_use_as_albedo = true
		material.vertex_color_is_srgb = true
		material.roughness = 0.87
		merged.material_override = material
		parent.add_child(merged)

func _build_gun() -> void:
	for child in _gun.get_children():
		_gun.remove_child(child)
		child.queue_free()
	var model: Dictionary = WeaponModel.build(_gun, weapon_id, true)
	_paint_parts.assign(model.paint)
	_magazine = model.magazine
	_viewmodel = model.get("viewmodel", false)
	_magazine_spare = null
	if is_instance_valid(_magazine):
		_magazine_rest = _magazine.position
		_magazine_rest_transform = _magazine.transform
		if _viewmodel and _magazine.get_parent() != null:
			# The replacement: its own instance of the same mesh, hidden until the hand takes it.
			_magazine_spare = _magazine.duplicate() as MeshInstance3D
			_magazine_spare.name = "magazine_spare"
			_magazine_spare.visible = false
			_magazine.get_parent().add_child(_magazine_spare)
			_magazine_spare.transform = _magazine_rest_transform
	_muzzle = model.muzzle
	_smoke_node = null
	if _viewmodel and is_local and is_instance_valid(_muzzle) and _muzzle.get_parent() != null:
		# A grey puff that leaves the muzzle after a shot and thins out over SMOKE_SECONDS (presentation only).
		_smoke_material = SBViewmodelShading.smoke()
		_smoke_node = MeshInstance3D.new()
		_smoke_node.name = "muzzle_smoke"
		_smoke_node.mesh = SBWeaponModel.smoke_mesh()
		_smoke_node.material_override = _smoke_material
		_smoke_node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_smoke_node.visible = false
		_muzzle.get_parent().add_child(_smoke_node)
		_smoke_node.position = _muzzle.position
		_smoke_age = 9.0
	_ejection_point = model.get("ejection", Vector3.INF)
	_arms_player = model.get("arms_player")
	_arms_skeleton = model.get("arms_skeleton")
	_arms_time = 0.0
	_grip_measured = false
	_hand_bone = -1
	_drop_velocity = Vector3.ZERO
	_magazine_swap_pending = false
	_seat_kick = 0.0
	_reload_fired.clear()
	if is_instance_valid(_reload_audio):
		_reload_audio.stop_all() # a weapon change cancels a reload: nothing of it keeps sounding
	_magazine_in_hand = null
	_trigger_bones.clear()
	_trigger_rest.clear()
	if is_instance_valid(_arms_skeleton):
		for bone_name in ["R_index_2", "R_index_3"]:
			var bone := _arms_skeleton.find_bone(bone_name)
			if bone >= 0:
				_trigger_bones.append(bone)
				_trigger_rest.append(_arms_skeleton.get_bone_rest(bone).basis.get_rotation_quaternion())
	_gun_color = Weapons.get_weapon(weapon_id)["color"]
	_gun_rest = GUN_REST + (model.get("pivot", Vector3.ZERO) as Vector3)
	_gun.position = _gun_rest
	apply_cosmetic(_cosmetic)

func apply_cosmetic(metadata: Dictionary) -> void:
	# Shared inspection/in-match material. Appearance never changes match state.
	_cosmetic = metadata.duplicate(true)
	_finish = CosmeticMaterial.finish(metadata, _viewmodel)
	if metadata.is_empty():
		var paint := Color("26323b")
		_finish.set_shader_parameter("base_paint", paint)
	CosmeticMaterial.apply(_finish, _paint_parts)

func _exit_tree() -> void:
	if is_instance_valid(_shot_audio):
		_shot_audio.stop()
	if is_instance_valid(_hurt_audio):
		_hurt_audio.stop()
	if is_instance_valid(_reload_audio):
		_reload_audio.stop_all()

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
	_deploy_remaining = 0
	_weapon_cooldowns.clear()
	_shot_index = 0
	recoil = Vector2.ZERO
	head_height = 1.62
	camera.position.y = head_height
	_body.scale.y = 1.0
	_kick = 0.0
	_equip_blend = 0.0
	_reload_visual_active = false
	_reload_fired.clear()
	if is_instance_valid(_reload_audio):
		_reload_audio.stop_all()
	_reload_visual_previous = 0.0
	_magazine_swap_pending = false
	_reload_clock = 0.0
	hit_feedback_remaining = 0.0
	_flash = 0.0
	_bob = 0.0
	_sway = Vector2.ZERO
	_visual_initialized = false
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
	_deploy_remaining = maxf(0, _deploy_remaining - delta)
	for id in _weapon_cooldowns:
		_weapon_cooldowns[id] = float(_weapon_cooldowns[id]) - delta
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
	var fired_weapon := ""
	if firing and (automatic or not _fire_previous) and weapon_ready() and reload_remaining <= 0:
		if ammo > 0:
			fired_weapon = weapon_id
			_fire()
		else:
			start_reload()
	# A held trigger carries at most this tick's remainder into the next interval,
	# so sustained fire matches the weapon data at 60 Hz; idle time never banks shots.
	for id in _weapon_cooldowns:
		if id != fired_weapon:
			_weapon_cooldowns[id] = maxf(0.0, float(_weapon_cooldowns[id]))
	if not firing and recoil == Vector2.ZERO:
		_shot_index = 0
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

func weapon_ready() -> bool:
	return _deploy_remaining <= READY_EPSILON and float(_weapon_cooldowns.get(weapon_id, 0.0)) <= READY_EPSILON

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
	# Drawing costs a fixed delay; the drawn weapon's own cycle time keeps running
	# while holstered, and accumulated recoil keeps recovering normally.
	_deploy_remaining = DEPLOY_SECONDS
	_shot_index = 0
	_build_gun()
	_equip_blend = 1.0

## Pistol-round equipment: purchases do not survive the halftime reset.
func reset_loadout() -> void:
	inventory.assign(["sidearm"])
	_ammo_store.clear()
	_weapon_cooldowns.clear()
	if weapon_id != "sidearm":
		weapon_id = "sidearm"
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
	# Only a continuously held trigger carries the sub-tick remainder; every burst
	# starts from the same phase so its recoil pattern is repeatable. A cooldown a
	# whole tick or more overdue means firing was blocked (reload, deploy), so
	# nothing carries and the interruption cannot bank part of a shot.
	var physics_step := 1.0 / float(Engine.physics_ticks_per_second)
	var cooldown := float(_weapon_cooldowns.get(weapon_id, 0.0))
	var carry := cooldown if _fire_previous and cooldown <= 0.0 and cooldown > -physics_step * 0.999 else 0.0
	_weapon_cooldowns[weapon_id] = carry + float(spec["interval"])
	var spread := current_spread(not is_on_floor())
	var shot_yaw := yaw + recoil.x + _rng.randf_range(-spread, spread)
	var shot_pitch := pitch + recoil.y + _rng.randf_range(-spread, spread)
	var direction := Vector3(-sin(shot_yaw) * cos(shot_pitch), sin(shot_pitch), -cos(shot_yaw) * cos(shot_pitch)).normalized()
	var origin := global_position + Vector3.UP * head_height
	var trace := trace_shot(origin, direction, float(spec["range"]))
	if trace.hit:
		var target: SBActor = trace.actor
		if target != null and target.team != team and target.alive:
			var headshot: bool = trace.headshot
			var distance_ratio := clampf(float(trace.distance) / float(spec["range"]), 0, 1)
			var amount := float(spec["damage"]) * lerpf(1, float(spec["falloff"]), distance_ratio)
			if headshot:
				amount *= float(spec["head"])
			target.apply_damage(amount, actor_id, headshot)
			show_hit_feedback(headshot, not target.alive)
			hit_confirmed.emit(actor_id, headshot, not target.alive)
		_impact(trace.position, trace.normal, target != null)
		impact_created.emit(trace.position, trace.normal, target != null)
	shot_fired.emit(actor_id, origin, direction)
	play_shot_effect()
	_shot_index += 1
	recoil.y = minf(recoil.y + float(spec["recoil"]), 0.16)
	recoil.x += sin(_shot_index * 1.7) * float(spec["recoil"]) * 0.55

## Authoritative shot trace. World geometry uses the physics ray; operators use
## their drawn head/body volumes, so a ray through the empty corners of another
## operator's movement capsule continues to whatever is actually behind it.
func trace_shot(origin: Vector3, direction: Vector3, max_distance: float) -> Dictionary:
	var result := {"hit": false, "distance": max_distance, "position": origin + direction * max_distance, "normal": -direction, "actor": null, "headshot": false}
	var query := PhysicsRayQueryParameters3D.create(origin, origin + direction * max_distance, 1, [get_rid()])
	var world_hit := get_world_3d().direct_space_state.intersect_ray(query)
	if not world_hit.is_empty():
		result.hit = true
		result.distance = origin.distance_to(world_hit.position)
		result.position = world_hit.position
		result.normal = world_hit.normal
	for node in get_tree().get_nodes_in_group("combatants"):
		var other := node as SBActor
		if other == null or other == self or not other.alive:
			continue
		var contact := other.volume_intersection(origin, direction, float(result.distance))
		if contact.is_empty():
			continue
		result.hit = true
		result.distance = contact.distance
		result.position = contact.position
		result.normal = contact.normal
		result.actor = other
		result.headshot = contact.headshot
	return result

## Nearest entry of a world-space ray into this operator's drawn head or body,
## closer than max_distance; empty when the ray misses both.
func volume_intersection(origin: Vector3, direction: Vector3, max_distance: float) -> Dictionary:
	var inverse := global_transform.affine_inverse()
	var local_origin := inverse * origin
	var local_direction := inverse.basis * direction
	var squash := maxf(0.05, _body.scale.y) if _body != null else 1.0
	# Body: the movement capsule at the current stance, in unsquashed local space.
	var capsule := _collision.shape as CapsuleShape3D
	var body_t := _capsule_entry(local_origin - Vector3(0, _collision.position.y, 0), local_direction, capsule.radius, capsule.height, BODY_TOP * squash - _collision.position.y)
	# Head: undo the drawn crouch squash; the ray parameter remains a world distance.
	var head_origin := Vector3(local_origin.x, local_origin.y / squash, local_origin.z)
	var head_direction := Vector3(local_direction.x, local_direction.y / squash, local_direction.z)
	var nearest := max_distance
	var headshot := false
	var found := false
	for volume: Array in HEAD_VOLUMES:
		var t := _ellipsoid_entry(head_origin, head_direction, volume[0], volume[1])
		if t >= 0.0 and t < nearest:
			nearest = t
			headshot = true
			found = true
	if body_t >= 0.0 and body_t < nearest:
		nearest = body_t
		headshot = false
		found = true
	if not found:
		return {}
	var at := origin + direction * nearest
	var outward := at - Vector3(global_position.x, at.y, global_position.z)
	return {"distance": nearest, "position": at, "normal": outward.normalized() if outward.length_squared() > 0.000001 else -direction, "headshot": headshot}

static func _ellipsoid_entry(origin: Vector3, direction: Vector3, center: Vector3, radii: Vector3) -> float:
	var o := (origin - center) / radii
	var d := direction / radii
	var c := o.dot(o) - 1.0
	if c <= 0.0:
		return 0.0
	var a := d.dot(d)
	var b := o.dot(d)
	var disc := b * b - a * c
	if a <= 0.0 or disc < 0.0:
		return -1.0
	var t := (-b - sqrt(disc)) / a
	return t if t >= 0.0 else -1.0

## Entry distance of a ray into a y-axis capsule centred on the origin (height
## includes both caps, as CapsuleShape3D) intersected with the half-space y <= top;
## -1 on a miss, 0 from inside. Both pieces are convex, so each meets the ray in one
## interval and the solid's interval is their overlap. Grazing rays miss, as they do
## against the physics capsule.
static func _capsule_entry(origin: Vector3, direction: Vector3, radius: float, height: float, top: float) -> float:
	var half := maxf(0.0, height * 0.5 - radius)
	var cylinder := _overlap(_radial_span(origin, direction, radius), _slab_span(origin.y, direction.y, -half, half))
	var capsule := cylinder
	for cap_y in [-half, half]:
		var cap := _sphere_span(origin - Vector3(0, cap_y, 0), direction, radius)
		if cap.x < cap.y:
			capsule = cap if capsule.x >= capsule.y else Vector2(minf(capsule.x, cap.x), maxf(capsule.y, cap.y))
	var span := _overlap(capsule, _slab_span(origin.y, direction.y, -INF, top))
	if span.x >= span.y or span.y < 0.0:
		return -1.0
	return maxf(span.x, 0.0)

const _EMPTY_SPAN := Vector2(INF, -INF)
## A ray that passes within this of the surface (squared-distance margin, m^2; about
## 1.6 micrometres at the 0.31 m radius) is tangent and misses, as against the
## physics capsule.
const GRAZE := 0.000001

static func _overlap(a: Vector2, b: Vector2) -> Vector2:
	return Vector2(maxf(a.x, b.x), minf(a.y, b.y))

# The spans below work in 64-bit floats on Vector3 components. Vector3 maths is
# 32-bit, which at 100 m moves the surface by millimetres; the closest-approach form
# also keeps the tangent margin independent of range and of the ray's pitch.

## Ray parameters inside the infinite vertical cylinder of the given radius.
static func _radial_span(origin: Vector3, direction: Vector3, radius: float) -> Vector2:
	var a := direction.x * direction.x + direction.z * direction.z
	if a < 0.000000000001:
		var inside := radius * radius - (origin.x * origin.x + origin.z * origin.z)
		return Vector2(-INF, INF) if inside > GRAZE else _EMPTY_SPAN
	var t := -(origin.x * direction.x + origin.z * direction.z) / a
	var px := origin.x + direction.x * t
	var pz := origin.z + direction.z * t
	var h := radius * radius - (px * px + pz * pz)
	if h <= GRAZE:
		return _EMPTY_SPAN
	var half := sqrt(h / a)
	return Vector2(t - half, t + half)

## Ray parameters where low <= origin_y + direction_y * t <= high.
static func _slab_span(origin_y: float, direction_y: float, low: float, high: float) -> Vector2:
	if absf(direction_y) < 0.000000000001:
		return Vector2(-INF, INF) if origin_y >= low and origin_y <= high else _EMPTY_SPAN
	var t1 := (low - origin_y) / direction_y
	var t2 := (high - origin_y) / direction_y
	return Vector2(minf(t1, t2), maxf(t1, t2))

## Ray parameters inside a sphere of the given radius centred on the origin.
static func _sphere_span(origin: Vector3, direction: Vector3, radius: float) -> Vector2:
	var a := direction.x * direction.x + direction.y * direction.y + direction.z * direction.z
	if a <= 0.0:
		return _EMPTY_SPAN
	var t := -(origin.x * direction.x + origin.y * direction.y + origin.z * direction.z) / a
	var px := origin.x + direction.x * t
	var py := origin.y + direction.y * t
	var pz := origin.z + direction.z * t
	var h := radius * radius - (px * px + py * py + pz * pz)
	if h <= GRAZE:
		return _EMPTY_SPAN
	var half := sqrt(h / a)
	return Vector2(t - half, t + half)

## Half-angle of the random cone for the next shot, in radians. The authority
## passes its floor contact; the HUD estimates airborne state from velocity.
func current_spread(airborne: bool) -> float:
	var spec := Weapons.get_weapon(weapon_id)
	var moving := Vector2(velocity.x, velocity.z).length() / WALK_SPEED
	var spread := float(spec["spread"]) + moving * 0.026 + (0.045 if airborne else 0.0)
	return spread * 0.6 if _crouching else spread

func show_hit_feedback(headshot: bool, lethal: bool) -> void:
	# Presentation called only by an authority-confirmed hit (or its server RPC).
	hit_feedback_remaining = 0.18
	hit_feedback_headshot = headshot
	hit_feedback_lethal = lethal

func play_shot_effect() -> void:
	_kick = 1
	_flash = FLASH_SECONDS
	# Each shot's flash differs a little in turn, length and width; the cosmetic variation
	# comes from the clock, apart from the authoritative RNG.
	var ticks := Time.get_ticks_msec()
	_muzzle.rotation.z = float(ticks % 29) * 0.22
	_flash_variation = Vector3(0.85 + float(ticks % 17) * 0.015, 0.85 + float(ticks % 13) * 0.02, 0.78 + float(ticks % 23) * 0.02)
	_muzzle.scale = _flash_variation
	_smoke_age = 0.0
	if is_local:
		var port: Vector3 = _gun.global_transform * _ejection_point if _ejection_point != Vector3.INF else _gun.global_position + global_basis * Vector3(0.065, 0.02, -0.11)
		if _viewmodel:
			port = _viewmodel_to_world(port)
		CombatEffects.for_world(get_parent()).casing(port, global_basis.x, _cosmetic_floor(port))
	if _shot_audio != null:
		if _shot_audio.stream != _shot_streams[weapon_id]:
			_shot_audio.stream = _shot_streams[weapon_id]
		# Separate cosmetic RNG: audio variation cannot alter authoritative spread.
		_shot_audio.pitch_scale = 0.98 + fmod(float(Time.get_ticks_msec()), 41.0) * 0.001
		_shot_audio.play()

## The height of the floor under a point, for the brass to bounce on: a downward ray against the
## world only (never an actor), up to FLOOR_PROBE metres. -INF when there is no floor in reach,
## and then the casing does not bounce at all. The actor's own feet are NOT a floor: in the air
## they are above it, and brass that "landed" at the feet's height hung in mid-air. Cosmetic only.
const FLOOR_PROBE := 4.0
func _cosmetic_floor(from: Vector3) -> float:
	if not is_inside_tree():
		return -INF
	var query := PhysicsRayQueryParameters3D.create(from, from + Vector3.DOWN * FLOOR_PROBE, 1, [get_rid()])
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	return float((hit.get("position", Vector3.ZERO) as Vector3).y) if not hit.is_empty() else -INF

func _impact(at: Vector3, normal: Vector3, hit_actor: bool) -> void:
	CombatEffects.for_world(get_parent()).impact(at, normal, hit_actor)

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
		if nearest.distance_to(cloud.global_position) < cloud.concealment_radius():
			return false
	var query := PhysicsRayQueryParameters3D.create(from, to, 3, [get_rid()])
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	return hit.is_empty() or hit.get("collider") == other

func tick_visual(delta: float) -> void:
	if camera == null or delta <= 0:
		return
	var reloading := reload_remaining > 0
	var reload_duration := float(Weapons.get_weapon(weapon_id)["reload"])
	# The presentation clock first (see RELOAD_VISUAL_SLACK), then everything the player sees and
	# hears of the reload follows IT, not the authoritative fraction: the click lands on the frame
	# the part moves, whatever the snapshot jitter.
	if reloading and _reload_visual_active and reload_remaining - _reload_clock > reload_duration * 0.5:
		# The timer went up by more than half a reload: this is a NEW reload that never showed an idle
		# frame in between (a reload restarted at once). Close the old one the way an idle frame would.
		_swap_magazines_if_seated()
		if not _reload_fired.has("seat"):
			_reload_audio.stop_all()
		_reload_visual_active = false
	if not reloading:
		_reload_clock = 0.0
	elif not _reload_visual_active or _reload_clock <= 0.0 or reload_remaining - _reload_clock > RELOAD_VISUAL_SLACK:
		# A new reload, or an authoritative correction upward: follow it at once.
		_reload_clock = reload_remaining
	else:
		_reload_clock = clampf(_reload_clock - delta, reload_remaining - RELOAD_VISUAL_SLACK, reload_remaining)
	var visual_progress := SBReloadPhases.progress(_reload_clock, reload_duration) if reloading else 0.0
	if reloading and not _reload_visual_active:
		_reload_fired.clear()
		_reload_audio.begin_reload()
		_reload_visual_previous = visual_progress
		if not is_instance_valid(_arms_player):
			# Procedural magazines start to drop at once, so their release click is the start (as it always was).
			_fire_reload_cue("unlatch", visual_progress)
	if reloading:
		var rigged_events := is_instance_valid(_arms_player)
		for event in SBReloadPhases.crossed(_reload_visual_previous, visual_progress):
			# The rigged hand has the whole set; a procedural magazine has a release (fired at the start, above) and a seat.
			if not rigged_events and (event == "unlatch" or not SBReloadPhases.PROCEDURAL_EVENTS.has(event)):
				continue
			_fire_reload_cue(event, visual_progress)
		_reload_visual_previous = visual_progress
	elif _reload_visual_active and not _reload_fired.has("seat"):
		_reload_audio.stop_all() # cancelled before the seat: the sounds that were playing stop with it
	_reload_visual_active = reloading
	_seat_kick = _seat_kick * exp(-delta * SEAT_KICK_DECAY) if _seat_kick > 0.002 else 0.0
	var speed := Vector2(velocity.x, velocity.z).length()
	_bob += delta * speed * 1.8
	# Exponential return has the same response at 30, 60 and 120 Hz.
	_kick *= exp(-delta * 20.0)
	_flash = maxf(0, _flash - delta)
	if _flash > 0.0:
		# A flash is brightest and widest at the start and shrinks fast over its 40 ms.
		_muzzle.scale = _flash_variation * (0.5 + 0.5 * _flash / FLASH_SECONDS)
	hit_feedback_remaining = maxf(0, hit_feedback_remaining - delta)
	_equip_blend *= exp(-delta * 14.0)
	_muzzle.visible = _flash > 0 and alive
	if is_instance_valid(_smoke_node):
		_smoke_age += delta
		var life := _smoke_age / SMOKE_SECONDS
		_smoke_node.visible = life < 1.0 and alive
		if _smoke_node.visible:
			var grow := 0.55 + 1.25 * life
			_smoke_node.scale = Vector3(grow, grow, 1.0 + 1.5 * life)
			_smoke_node.position = _muzzle.position + Vector3(0.0, 0.012 * life, -0.14 * life)
			_smoke_material.set_shader_parameter("fade", pow(1.0 - life, 1.6) * (0.5 if reduced_motion else 0.85))
	_world_muzzle.visible = _flash > 0 and alive and not is_local
	var gait := minf(speed / WALK_SPEED, 1.0) * (0.15 if _crouching else 0.35)
	for i in range(_legs.size()):
		_legs[i].rotation.x = sin(_bob + i * PI) * gait
		_knees[i].rotation.x = maxf(0, -sin(_bob + i * PI)) * gait * 1.35
	for i in range(_arms.size()):
		_arms[i].rotation.x = -0.16 + sin(_bob + i * PI) * gait * 0.15 - _kick * 0.04
	if is_local:
		var look := Vector2(yaw, pitch)
		if not _visual_initialized:
			_visual_look = look
			_visual_initialized = true
		var look_delta := Vector2(angle_difference(_visual_look.x, look.x), look.y - _visual_look.y)
		_visual_look = look
		_sway += look_delta.limit_length(0.15) * 0.20
		_sway *= exp(-delta * 12.0)
		_sway = _sway.limit_length(0.04)
		if reduced_motion:
			_sway = Vector2.ZERO
		var reload_progress := 1.0 - clampf(_reload_clock / maxf(0.1, float(Weapons.get_weapon(weapon_id)["reload"])), 0, 1)
		var rigged := is_instance_valid(_arms_player)
		var reload_tilt := sin(reload_progress * PI) if reload_remaining > 0 else 0.0
		if rigged and reload_remaining > 0:
			# Into the reload pose before the hand reaches the magazine, held through the
			# swap, and back after the seat.
			reload_tilt = smoothstep(0.0, 0.16, reload_progress) * (1.0 - smoothstep(SBReloadPhases.LETGO, 1.0, reload_progress))
		if reduced_motion and not rigged:
			reload_tilt *= 0.2 # the procedural weapons' dip is plain motion: still calmed
		# Reduced motion calms sway, bob and the equip swing; it does NOT shrink the rigged reload's staging
		# lift, which is what keeps the hand and the magazine on screen for the swap (at 20 % of the
		# lift the support hand fell below the frame). The pose is reached by the same smooth ramp.
		var bob_weight := 0.0 if reduced_motion else minf(speed / WALK_SPEED, 1.0)
		var equip_motion := _equip_blend * (0.25 if reduced_motion else 1.0)
		var reload_offset := ARMS_RELOAD_OFFSET if rigged else Vector3(0, -0.13, 0)
		var reload_rotation := ARMS_RELOAD_ROTATION if rigged else Vector3(-0.38, 0, 0.38)
		var profile: Dictionary = REDUCED_RELOAD_VARIANTS["current"]
		if reduced_motion and rigged:
			profile = REDUCED_RELOAD_VARIANTS.get(reduced_variant, REDUCED_RELOAD_VARIANTS["current"])
			reload_rotation *= float(profile.roll)
			reload_offset *= float(profile.lift)
		var kick := _kick * (float(profile.recoil) if reduced_motion and rigged else 1.0)
		_gun.position = Vector3(_gun_rest.x + sin(_bob) * 0.006 * bob_weight - _sway.x, _gun_rest.y + absf(cos(_bob)) * 0.006 * bob_weight - _sway.y - equip_motion * 0.19, _gun_rest.z + kick * (0.075 if weapon_id == "marksman" else 0.046) + equip_motion * 0.08) + reload_offset * reload_tilt + SEAT_KICK_OFFSET * _seat_kick * (0.25 if reduced_motion else 1.0)
		_gun.rotation = Vector3(kick * (0.13 if weapon_id == "sidearm" else 0.065) - equip_motion * 0.48, -_sway.x * 1.8, -_sway.x) + reload_rotation * reload_tilt + SEAT_KICK_TURN * _seat_kick * (0.25 if reduced_motion else 1.0)
		if is_instance_valid(_arms_player):
			# The clip's first frame is the hold, so 0 returns the hands to the rifle.
			var clip_time := reload_progress if reload_remaining > 0 else 0.0
			var clip_name := str(profile.clip) if _arms_player.has_animation(str(profile.clip)) else "reload"
			if _arms_player.assigned_animation != clip_name:
				_arms_player.assigned_animation = clip_name
				_arms_time = -1.0
			if clip_time != _arms_time:
				_arms_time = clip_time
				_arms_player.seek(clip_time, true)
		if is_instance_valid(_magazine):
			_pose_magazines(reload_progress if reload_remaining > 0 else 0.0)
		if is_instance_valid(_arms_skeleton):
			var pull := clampf(_kick * 1.5, 0.0, 1.0) * 0.32
			for i in range(_trigger_bones.size()):
				_arms_skeleton.set_bone_pose_rotation(_trigger_bones[i], _trigger_rest[i] * Quaternion(Vector3.RIGHT, -pull * (1.0 if i == 0 else 0.6)))

## Plays and announces a reload click, once per reload (a correction that takes the clock back over it
## does not click it again).
func _fire_reload_cue(event: String, progress: float) -> void:
	if _reload_fired.has(event):
		return
	_reload_fired[event] = true
	if event == "seat":
		_magazine_swap_pending = true
		_seat_kick = 1.0
	_reload_audio.play(event, progress, head_height)
	reload_cue.emit(event, progress)

## The reload reached the seat: the replacement is the magazine in the well from now on, and the one that
## fell is the spare for the next reload (two real nodes, alternating).
func _swap_magazines_if_seated() -> void:
	if _magazine_swap_pending and is_instance_valid(_magazine_spare) and is_instance_valid(_magazine):
		var seated := _magazine_spare
		_magazine_spare = _magazine
		_magazine = seated
	_magazine_swap_pending = false

## Where the magazines are for a reload progress. With the rigged arms the old magazine rides the
## support hand from the grasp to the drop (the clip took it out of the well and swung it out), then
## falls; the replacement, a second mesh, appears in the hand at the acquisition, is carried to the
## well and rides the hand until the let-go; after it the replacement stays in the well. Outside a
## reload the first magazine sits in the well. Without the rigged arms the one magazine follows the
## older drop curve.
func _pose_magazines(progress: float) -> void:
	if not is_instance_valid(_arms_skeleton) or not is_instance_valid(_arms_player):
		var extraction := sin(clampf((progress - 0.12) / 0.72, 0, 1) * PI) if reload_remaining > 0 else 0.0
		_magazine.position = _magazine_rest + _magazine.basis * Vector3(0, -extraction * MAGAZINE_DROP, 0)
		return
	if _hand_bone < 0:
		_hand_bone = _arms_skeleton.find_bone("L_hand")
	if not _grip_measured:
		_measure_hold()
	var reloading := reload_remaining > 0
	if not reloading:
		_swap_magazines_if_seated()
		_magazine.visible = true
		_magazine.transform = _magazine_rest_transform
		if is_instance_valid(_magazine_spare):
			_magazine_spare.visible = false
		_magazine_in_hand = null
		return
	var in_hand := _hand_in_gun() * _grip_offset
	_magazine_in_hand = null
	# The old magazine.
	if progress < SBReloadPhases.GRASP:
		_magazine.visible = true
		_magazine.transform = _magazine_rest_transform
	elif progress <= SBReloadPhases.DROP:
		_magazine.visible = true
		_magazine.transform = in_hand
		_magazine_in_hand = _magazine
	else:
		var fall := (progress - SBReloadPhases.DROP) * float(Weapons.get_weapon(weapon_id)["reload"])
		_magazine.visible = fall <= DROP_VISIBLE_SECONDS
		_magazine.transform = _dropped_transform(fall)
	# The replacement.
	if is_instance_valid(_magazine_spare):
		# The replacement is drawn from the acquisition: the hand has it at the pouch, below the frame, and
		# brings it up into view (arms_build.py: the hip pouch). Before that it is not drawn.
		_magazine_spare.visible = progress >= SBReloadPhases.ACQUIRE
		_magazine_spare.transform = _magazine_rest_transform if progress > SBReloadPhases.LETGO else in_hand
		if progress >= SBReloadPhases.ACQUIRE and progress <= SBReloadPhases.LETGO:
			_magazine_in_hand = _magazine_spare # held from the acquisition, at the pouch

## The old magazine `fall` seconds after the hand lets go: it leaves with a share of the hand's
## speed and falls under gravity (pointing down in the world, whatever the rifle's roll), tumbling
## about the rifle's own X (unless reduced motion is on). A pure function of time, so the pose can be
## sought and replayed.
func _dropped_transform(fall: float) -> Transform3D:
	var down := (_gun.global_basis.inverse() * Vector3.DOWN).normalized() * DROP_GRAVITY
	var at := _drop_origin.origin + _drop_velocity * fall + down * (0.5 * fall * fall)
	# Reduced motion keeps the fall (the discard has to be seen) but not the tumble.
	var spin := 0.0 if reduced_motion else DROP_SPIN * fall
	return Transform3D(Basis(Vector3.RIGHT, spin) * _drop_origin.basis, at)

## Measures, once per built gun, from the clip itself: how the held magazine sits in the hand (at
## the grasp, with the magazine still in the well) and where, and how fast, the hand is at the drop.
func _measure_hold() -> void:
	var was := _arms_time
	var duration := float(Weapons.get_weapon(weapon_id)["reload"])
	_arms_player.seek(SBReloadPhases.GRASP, true)
	_grip_offset = _hand_in_gun().affine_inverse() * _magazine_rest_transform
	var step := 1.0 / 60.0
	_arms_player.seek(SBReloadPhases.DROP - step, true)
	var before := (_hand_in_gun() * _grip_offset).origin
	_arms_player.seek(SBReloadPhases.DROP, true)
	_drop_origin = _hand_in_gun() * _grip_offset
	_drop_velocity = (_drop_origin.origin - before) / (step * duration) * 0.6
	_arms_player.seek(was, true)
	_grip_measured = true

## The support hand's transform in the weapon node's space, from the skeleton's current pose.
func _hand_in_gun() -> Transform3D:
	var chain := Transform3D.IDENTITY
	var node: Node = _arms_skeleton
	while node != null and node != _gun:
		chain = (node as Node3D).transform * chain
		node = node.get_parent()
	return chain * _arms_skeleton.get_bone_global_pose(_hand_bone)

## A point of the viewmodel moved to where it appears on screen under the world
## camera's projection (the viewmodel draws with a narrower one), at the same depth.
func _viewmodel_to_world(point: Vector3) -> Vector3:
	var local := camera.global_transform.affine_inverse() * point
	var spread := tan(deg_to_rad(camera.fov) * 0.5) / tan(deg_to_rad(ViewmodelShading.FOV) * 0.5)
	return camera.global_transform * Vector3(local.x * spread, local.y * spread, local.z)

func snapshot() -> Dictionary:
	return {"id": actor_id, "team": team, "name": display_name, "position": global_position, "velocity": velocity, "yaw": yaw, "pitch": pitch, "recoil": recoil, "health": health, "alive": alive, "kills": kills, "deaths": deaths, "assists": assists, "credits": credits, "weapon": weapon_id, "ammo": ammo, "reserve": reserve, "reload": reload_remaining, "grenades": grenades, "smokes": smokes, "crouch": _crouching, "inventory": inventory.duplicate()}

func apply_snapshot(data: Dictionary, delta: float) -> void:
	team = int(data.get("team", team))
	if _body_team != team:
		_build_body()
	var at: Vector3 = data.get("position", global_position)
	global_position = at if is_local else global_position.lerp(at, clampf(delta * 18, 0, 1))
	velocity = data.get("velocity", Vector3.ZERO)
	yaw = float(data.get("yaw", yaw))
	pitch = float(data.get("pitch", pitch))
	var snapshot_recoil: Vector2 = data.get("recoil", Vector2.ZERO)
	if is_finite(snapshot_recoil.x) and is_finite(snapshot_recoil.y):
		recoil = snapshot_recoil.clamp(Vector2(-0.16, 0), Vector2(0.16, 0.16))
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
	camera.rotation.x = pitch + recoil.y
	camera.rotation.y = recoil.x
	var next_weapon: String = data.get("weapon", weapon_id)
	if next_weapon != weapon_id and Weapons.DATA.has(next_weapon):
		weapon_id = next_weapon
		_build_gun()
	if data.has("inventory"):
		inventory.assign(data["inventory"])
