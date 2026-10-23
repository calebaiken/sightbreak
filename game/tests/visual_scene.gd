extends SceneTree
## Actual engine render capture for review; does not assert visual quality or FPS.
var world: Node3D
var actor: SBActor

func _initialize() -> void:
	_capture.call_deferred()

func _capture() -> void:
	world = Node3D.new()
	root.add_child(world)
	world.add_child(RelayYard.new())
	actor = SBActor.new()
	actor.configure(1, 0, "Visual review", true)
	world.add_child(actor)
	actor.reset_for_round(Vector3(0, 0.05, -19))
	actor.yaw = PI - 0.08
	actor.rotation.y = actor.yaw
	actor.camera.rotation.x = -0.025
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://../builds/qa/refined-sidearm.png")
	actor.credits = 5000
	actor.buy_weapon("rifle")
	actor.apply_cosmetic({"rarity": "rare", "pattern_seed": 471, "wear": 0.18})
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://../builds/qa/refined-rifle.png")
	actor.camera.current = false
	var camera := Camera3D.new()
	world.add_child(camera)
	camera.position = Vector3(-33, 32, -38)
	camera.look_at(Vector3(0, 0, 0))
	camera.current = true
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://../builds/qa/refined-overview.png")
	world.queue_free()
	await process_frame
	quit()
