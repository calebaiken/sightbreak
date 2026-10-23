extends SceneTree
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const Model = preload("res://scripts/gameplay/weapon_model.gd")
const Shading = preload("res://scripts/gameplay/viewmodel_shading.gd")
var output := "/workspace/reviews/integration-20261013/art-independent/fallback"
func _initialize() -> void: run.call_deferred()
func frame(label: String) -> void:
	for i in 3: await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	image.save_png(output.path_join(label + ".png"))
	print("FALLBACK_CAPTURE %s %dx%d" % [label, image.get_width(), image.get_height()])
func run() -> void:
	DirAccess.make_dir_recursive_absolute(output)
	root.content_scale_size = Vector2i(1280,720)
	root.size = root.content_scale_size
	var world := Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	var actor := Actor.new()
	actor.configure(1,0,"Independent fallback projection",true)
	world.add_child(actor)
	actor.reset_for_round(Vector3(3,0.05,-12))
	actor.yaw = 0.35
	actor.rotation.y = actor.yaw
	actor.credits = 5000
	actor.buy_weapon("rifle")
	actor._equip_blend = 0.0
	actor.tick_visual(0.016)
	await frame("01-default-rigged")
	Model.use_rigged_arms = false
	actor._build_gun()
	actor.tick_visual(0.016)
	await frame("02-current-static-fallback")
	# Diagnostic-only counterfactual: same geometry and texture set through the
	# first-person projection used by the rifle. Does not modify project files.
	actor._gun.get_node("hands").material_override = Shading.surface("res://assets/weapons/relay_ar/relay_ar_hands")
	await frame("03-static-matched-projection-counterfactual")
	world.queue_free()
	await process_frame
	await create_timer(0.2).timeout
	quit()
