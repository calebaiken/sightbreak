extends SceneTree
const Actor = preload("res://scripts/gameplay/actor.gd")
const Model = preload("res://scripts/gameplay/weapon_model.gd")
var checks := 0
var failures: Array[String] = []
func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok: failures.append(message)
func authority(actor: SBActor) -> Array:
	return [actor.ammo, actor.reserve, actor.reload_remaining, actor.weapon_id, actor.credits, actor.inventory.duplicate(), actor.alive, actor.health, actor.global_position, actor.velocity, actor._deploy_remaining, actor._weapon_cooldowns.duplicate(true)]
func _initialize() -> void: run.call_deferred()
func run() -> void:
	var actor := Actor.new()
	actor.configure(3, 0, "Independent art lifecycle", true)
	root.add_child(actor)
	actor.reset_for_round(Vector3.ZERO)
	actor.credits = 5000
	check(actor.buy_weapon("rifle"), "rifle purchase fixture")
	var hand := actor._arms_skeleton.find_bone("L_hand")
	var hold: Vector3 = actor._arms_skeleton.get_bone_global_pose(hand).origin
	for iteration in 30:
		actor.reload_remaining = 2.25 * 0.55
		var before := authority(actor)
		for rate in [30.0,60.0,120.0]: actor.tick_visual(1.0/rate)
		check(authority(actor) == before, "visual tick preserves authority values iteration%d" % iteration)
		check(actor._arms_time > 0.4 and actor._arms_time < 0.5, "reload seeks authority timer")
		var old: WeakRef = weakref(actor._arms_player)
		actor._equip("sidearm")
		check(actor._arms_player == null and actor._arms_skeleton == null and not actor._viewmodel, "sidearm clears arms/first-person-shader contract")
		actor.tick_visual(1.0/60.0)
		await process_frame
		await process_frame
		check(old.get_ref() == null, "removed arms animation player freed")
		actor._equip("rifle")
		actor.tick_visual(1.0/60.0)
		check(actor._arms_time == 0.0 and actor._arms_skeleton.get_bone_global_pose(hand).origin.distance_to(hold) < 0.001, "re-equipped arms at hold")
		actor.reload_remaining = 2.25 * 0.45
		actor.tick_visual(1.0/60.0)
		actor.reset_for_round(Vector3.ZERO)
		actor.tick_visual(1.0/60.0)
		check(actor._arms_time == 0.0 and actor._magazine.position == actor._magazine_rest, "round reset returns arms and magazine")
	actor.apply_damage(200, 9)
	check(not actor._gun.visible and not actor.alive, "death hides gun")
	actor.reset_for_round(Vector3.ZERO)
	actor.tick_visual(1.0/60.0)
	check(actor._gun.visible and actor.alive and actor._arms_time == 0.0, "respawn resets arms")
	Model.use_rigged_arms = false
	actor._build_gun()
	var body: Material = actor._gun.get_node("body").material_override
	var hands: Material = actor._gun.get_node("hands").material_override
	print("FALLBACK_PROJECTION body_class=%s body_fov=%s hands_class=%s world_fov=%s" % [body.get_class(), body.get_shader_parameter("viewmodel_fov"), hands.get_class(), actor.camera.fov])
	Model.use_rigged_arms = true
	actor.queue_free()
	await process_frame
	await process_frame
	await create_timer(0.2).timeout
	print("INDEPENDENT_ART_LIFECYCLE checks=%d failures=%s" % [checks, failures])
	quit(0 if failures.is_empty() else 1)
