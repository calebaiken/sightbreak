extends SceneTree

const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const Weapons = preload("res://scripts/gameplay/weapons.gd")
const Utility = preload("res://scripts/gameplay/utility.gd")
var failures: Array[String] = []
var checks := 0

func _initialize() -> void:
	_run.call_deferred()

func check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

func _run() -> void:
	var world := Node3D.new()
	root.add_child(world)
	var arena := Arena.new()
	world.add_child(arena)
	var player := Actor.new()
	player.configure(1, 0, "Test attacker", true)
	world.add_child(player)
	var enemy := Actor.new()
	enemy.configure(2, 1, "Test defender")
	world.add_child(enemy)
	player.reset_for_round(Vector3(0, 0.05, -15))
	enemy.reset_for_round(Vector3(0, 0.05, -9))
	await physics_frame
	await physics_frame
	check(arena.sites.size() == 2, "two objective sites")
	check(arena.attack_spawns.size() == 5 and arena.defend_spawns.size() == 5, "five spawns per team")
	check(arena.is_at_site(Vector3(-15, 0, 10)) == 0, "site A detection")
	check(arena.is_at_site(Vector3(15, 0, 10)) == 1, "site B detection")
	check(arena.is_at_site(Vector3.ZERO) == -1, "center not objective")
	check(arena.waypoints.size() > 100, "walkable navigation graph")
	check(arena._obstacles.size() == 25, "surface polish preserves all 25 navigation obstacles")
	var rough: StandardMaterial3D = arena._material(Color.WHITE, 0.94)
	var smooth: StandardMaterial3D = arena._material(Color.WHITE, 0.24)
	check(rough != smooth and is_equal_approx(smooth.roughness, 0.24), "material cache distinguishes roughness")
	var asphalt: StandardMaterial3D = arena._material(Color.WHITE, 0.85, false, "asphalt")
	check(asphalt.albedo_texture.get_width() == 128 and asphalt.uv1_world_triplanar, "surface texture remains small and world-scaled")
	var waypoint: Vector3 = arena.bot_navigation(Vector3(-14, 0, -18), Vector3(14, 0, 10))
	check(waypoint != Vector3(-14, 0, -18), "bot routes around freight containers")
	check(player.can_see(enemy), "open lane visible")
	check(not player.buy_weapon("rifle"), "insufficient match credits rejected")
	check(not player.buy_weapon("invented"), "unknown weapon rejected")
	player.credits = 3000
	check(player.buy_weapon("rifle"), "rifle purchase succeeds")
	check(player.credits == 600, "purchase debits match currency")
	check(not player.buy_weapon("rifle"), "duplicate purchase rejected")
	check(player.ammo == 30 and player.reserve == 90, "rifle magazine and reserve")
	# A floor-stationary accurate head hit at six meters must be lethal.
	for i in range(30):
		player.input_state = {"look": Vector2(PI, 0), "move": Vector2.ZERO}
		player.tick_authority(1.0 / 60.0)
		enemy.tick_authority(1.0 / 60.0)
		await physics_frame
	player.input_state = {"look": Vector2(PI, 0), "fire": true}
	player.tick_authority(1.0 / 60.0)
	check(player.ammo == 29, "shot consumes one bullet")
	check(not enemy.alive and enemy.health == 0, "authoritative ray headshot eliminates enemy")
	check(enemy.last_hit_headshot, "headshot identified by hit location")
	player.input_state = {"fire": true}
	player.tick_authority(1.0 / 60.0)
	check(player.ammo == 29, "fire interval rejects rapid duplicate shot")
	player.input_state = {"reload": true}
	player.tick_authority(0.01)
	check(player.reload_remaining > 0, "reload begins")
	player.input_state = {}
	player.tick_authority(3.0)
	check(player.ammo == 30 and player.reserve == 89, "reload transfers only missing rounds")
	enemy.reset_for_round(Vector3(0, 0.05, -9))
	player.reset_for_round(Vector3(0, 0.05, -15))
	await physics_frame
	await physics_frame
	var smoke := Utility.new()
	smoke.kind = "smoke"
	world.add_child(smoke)
	smoke.global_position = Vector3(0, 1, -12)
	smoke._detonate()
	check(not player.can_see(enemy), "smoke blocks bot line of sight")
	smoke.queue_free()
	await process_frame
	var before := player.global_position
	player.input_state = {"move": Vector2(0, 1), "look": Vector2(PI, 0)}
	for i in range(30):
		player.tick_authority(1.0 / 60.0)
		await physics_frame
	check(player.global_position.z > before.z + 1, "forward movement follows yaw")
	player.input_state = {"crouch": true}
	player.tick_authority(0.01)
	check(player.head_height == 1.13, "crouch lowers camera and collision")
	var saved: Dictionary = player.snapshot()
	check(saved["weapon"] == "rifle" and saved["grenades"] == 1, "snapshot includes equipment")
	var original_position := player.global_position
	player.global_position += Vector3(2, 0, 0)
	player.apply_snapshot(saved, 0.016)
	check(player.global_position.is_equal_approx(original_position), "local authoritative snapshot corrects position")
	check(Weapons.get_weapon("invalid")["name"] == "Kestrel 9", "unknown spec safely falls back")
	# Cosmetic network replicas must never apply client-side blast damage.
	player.reset_for_round(Vector3(0, 0.05, -15))
	enemy.reset_for_round(Vector3(0, 0.05, -12))
	await physics_frame
	await physics_frame
	var replica := Utility.new()
	replica.visual_only = true
	replica.owner_team = 0
	world.add_child(replica)
	replica.global_position = Vector3(0, 0.5, -12)
	replica._detonate()
	check(enemy.health == 100, "network utility replica cannot damage actors")
	var blast := Utility.new()
	blast.owner_team = 0
	blast.owner_id = 1
	world.add_child(blast)
	blast.global_position = Vector3(0, 0.5, -12)
	blast._detonate()
	check(enemy.health < 30 and enemy.health > 0, "authority grenade applies radial damage")
	check(player.health == 100, "grenade excludes friendly actors")
	enemy.reset_for_round(Vector3(-4.6, 0.05, -11))
	await physics_frame
	await physics_frame
	var blocked_blast := Utility.new()
	blocked_blast.owner_team = 0
	world.add_child(blocked_blast)
	blocked_blast.global_position = Vector3(-9.2, 1, -11)
	blocked_blast._detonate()
	check(enemy.health == 100, "solid freight container blocks blast damage")
	player.team = 1
	player.reset_for_round(Vector3(0, 0.05, 20))
	check(player._body_team == 1 and player.yaw == 0, "side switch updates model and spawn facing")
	player.inventory.append("smg")
	player.reset_for_round(Vector3(0, 0.05, 20))
	player._equip("smg")
	check(player.ammo == 30 and player.reserve == 120, "round refill covers holstered weapons")
	var stats_before: Dictionary = player.snapshot()
	player.apply_cosmetic({"rarity": "mythic", "pattern_seed": 985, "wear": 0.75})
	check(player.snapshot() == stats_before, "cosmetic application never changes competitive state")
	check(player._finish.get_shader_parameter("pattern_seed") == 985.0, "cosmetic seed controls only paint material")
	# Recoil affects both authoritative shot rays and replicated camera presentation.
	player.recoil = Vector2(0.02, 0.08)
	var aiming: Dictionary = player.snapshot()
	check(aiming["recoil"] == player.recoil, "snapshot includes authoritative recoil")
	enemy.apply_snapshot(aiming, 0.016)
	check(is_equal_approx(enemy.camera.rotation.x, enemy.pitch + player.recoil.y) and is_equal_approx(enemy.camera.rotation.y, player.recoil.x), "replica camera follows authoritative recoil")
	player.input_state = {"crouch": true}
	player.tick_authority(0.01)
	player.play_shot_effect()
	player.reset_for_round(Vector3(0, 0.05, 20))
	check(is_equal_approx(player.head_height, 1.62) and is_equal_approx(player.camera.position.y, 1.62) and is_equal_approx(player._body.scale.y, 1.0), "round reset immediately restores crouched head and body")
	check(player._kick == 0 and player._flash == 0 and player.recoil == Vector2.ZERO, "round reset clears previous shot presentation")
	# Cosmetic animation must not alter ammunition, look, hitboxes or recoil.
	var visual_state: Dictionary = player.snapshot()
	player.play_shot_effect()
	player.tick_visual(1.0 / 30.0)
	var kick_30: float = player._kick
	player.play_shot_effect()
	for i in range(4):
		player.tick_visual(1.0 / 120.0)
	check(is_equal_approx(player._kick, kick_30), "kick return is frame-rate independent at 30 and 120 Hz")
	check(player.snapshot() == visual_state, "viewmodel animation cannot mutate competitive state")
	player.reload_remaining = float(Weapons.get_weapon(player.weapon_id)["reload"]) * 0.5
	player.tick_visual(0.016)
	check(player._magazine.position.y < player._magazine_rest.y - 0.1, "reload extracts magazine visually")
	player.reload_remaining = 0
	player.tick_visual(0.016)
	check(player._magazine.position == player._magazine_rest, "reload completion seats magazine")
	player.yaw = PI - 0.001
	player._visual_initialized = false
	player.tick_visual(0.016)
	player.yaw = -PI + 0.001
	player.tick_visual(0.016)
	check(player._sway.length() < 0.002, "look sway wraps yaw without full-turn jerk")
	check(Actor._shot_streams.size() == 4, "all four weapons use original distinct sounds")
	var previous := PackedByteArray()
	for id in Weapons.DATA:
		var sound: AudioStreamWAV = Actor._shot_streams[id]
		check(sound.format == AudioStreamWAV.FORMAT_16_BITS and sound.data.size() > 5000 and sound.data != previous, "%s has distinct nonempty 16-bit audio" % id)
		previous = sound.data
	# v0.3 presentation contracts: same gameplay snapshots, bounded visuals and
	# real reload/equip transforms; these do not assert aesthetic quality.
	check(player._knees.size() == 2 and player._arms.size() == 2, "operator has two articulated knees and weapon-support arms")
	check(player._head.mesh is SphereMesh, "helmet silhouette uses curved geometry")
	check(player._gun.get_child_count() <= 16, "static first-person attachments batch into at most sixteen draw nodes")
	check(player._paint_parts.size() == 2, "shared model retains separately animated magazine and batched finish")
	check(player._magazine.get_child_count() == 1, "magazine ribs batch into one draw node following reload transform")
	player.show_hit_feedback(true, true)
	check(player.hit_feedback_remaining == 0.18 and player.hit_feedback_headshot and player.hit_feedback_lethal, "confirmed headshot kill exposes feedback independently of HUD")
	var feedback_state: Dictionary = player.snapshot()
	player.tick_visual(0.2)
	check(player.hit_feedback_remaining == 0 and player.snapshot() == feedback_state, "feedback expires without changing authoritative state")
	player._equip("rifle")
	check(player._equip_blend == 1.0, "equip starts a visual ready transition")
	player.tick_visual(0.016)
	var full_equip_tilt: float = absf(player._gun.rotation.x)
	player._equip_blend = 1.0
	player.reduced_motion = true
	player.tick_visual(0.016)
	check(absf(player._gun.rotation.x) < full_equip_tilt * 0.5 and player._sway == Vector2.ZERO, "reduced motion attenuates equip and removes cosmetic sway")
	player.reduced_motion = false
	var effects: Node3D = world.get_node("CombatEffects")
	for i in range(100):
		effects.casing(Vector3.ZERO, Vector3.RIGHT)
		effects.impact(Vector3.ZERO, Vector3.UP, false)
	check(effects.get_child_count() == 3, "rapid effects reuse exactly three mesh pools")
	check(effects._pools.casings.slots.size() == 24 and effects._pools.sparks.slots.size() == 40 and effects._pools.dust.slots.size() == 12, "effects cannot grow beyond fixed 76-instance budget")
	effects._process(1.0)
	var live := 0
	for pool in effects._pools.values():
		for slot in pool.slots:
			if slot.life > 0: live += 1
	check(live == 0, "all pooled effects expire after bounded lifetime")
	var model_root := Node3D.new()
	var inspection: Dictionary = Actor.WeaponModel.build(model_root, "rifle", false)
	check(inspection.paint.size() == 2 and model_root.get_child_count() < player._gun.get_child_count(), "inspection shares exact weapon geometry without hand meshes")
	model_root.free()
	player.reset_for_round(Vector3(0, 0.05, 20))
	check(player.hit_feedback_remaining == 0 and player._equip_blend == 0, "round reset clears hit and equip presentation")
	await create_timer(0.6).timeout
	world.queue_free()
	await process_frame
	print("ACTOR TESTS: %d checks, %d failures" % [checks, failures.size()])
	quit(0 if failures.is_empty() else 1)
