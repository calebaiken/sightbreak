extends SceneTree
## Deterministic, real-engine review fixtures, not naturally played match results.
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
var output := "res://../builds/qa/v03-combat"
var world: Node3D
var actor: SBActor

func _initialize() -> void:
	_run.call_deferred()

func shot(name: String) -> void:
	# MultiMesh uploads can be one frame behind the scene mutation.
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	var result := root.get_texture().get_image().save_png(output.path_join(name + ".png"))
	if result != OK:
		push_error("Capture failed: " + name)
	print("COMBAT CAPTURE: " + name)

func _run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture-dir="):
			output = argument.trim_prefix("--capture-dir=")
	DirAccess.make_dir_recursive_absolute(output)
	world = Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	actor = Actor.new()
	actor.configure(1, 0, "Capture fixture", true)
	world.add_child(actor)
	actor.reset_for_round(Vector3(0, 0.05, -19))
	actor.yaw = PI - 0.08
	actor.rotation.y = actor.yaw
	actor.camera.rotation.x = -0.025
	await shot("01-sidearm-ready")
	actor.credits = 5000
	actor.buy_weapon("rifle")
	actor._equip_blend = 0
	actor.apply_cosmetic({})
	await shot("02-rifle-ready")
	actor.play_shot_effect()
	actor.tick_visual(0.016)
	await shot("03-rifle-fire")
	actor._kick = 0
	actor._flash = 0
	actor.reload_remaining = 1.25
	actor.tick_visual(0.016)
	await shot("04-rifle-reload")
	actor.reload_remaining = 0
	actor.tick_visual(0.016)
	await shot("05-rifle-reseated")
	var effects := SBCombatEffects.for_world(world)
	effects.impact(actor.global_position + Vector3(-0.25, 1.3, 1.7), Vector3(0, 0, -1), false)
	effects.set_process(false)
	effects._process(0.05)
	await shot("05b-bullet-impact")
	effects.set_process(true)
	effects._process(1.0)
	actor._gun.visible = false
	actor.camera.current = false
	var camera := Camera3D.new()
	world.add_child(camera)
	camera.fov = 55
	camera.position = Vector3(0, 1.45, -14)
	camera.look_at(Vector3(0, 1.05, -18))
	camera.current = true
	for i in range(2):
		var operator := Actor.new()
		operator.configure(3 + i, i, "Model fixture")
		world.add_child(operator)
		operator.reset_for_round(Vector3(-0.6 + i * 1.2, 0.05, -18))
		operator.rotation.y = PI - 0.25
		operator.velocity = Vector3(0, 0, 3)
		operator.tick_visual(0.19)
	await shot("06-operator-silhouettes")
	var smoke := SBUtility.new()
	smoke.kind = "smoke"
	world.add_child(smoke)
	smoke.position = Vector3(0, 0, -22)
	smoke._detonate()
	await create_timer(0.85).timeout
	await shot("07-smoke")
	world.queue_free()
	await process_frame
	await process_frame
	quit()
