extends SceneTree
func _initialize(): call_deferred("run")
func make_world():
	var world := Node3D.new()
	var keep := WorldEnvironment.new()
	keep.environment = Environment.new()
	keep.environment.background_mode = Environment.BG_SKY
	keep.environment.sky = Sky.new()
	keep.environment.sky.sky_material = ProceduralSkyMaterial.new()
	world.add_child(keep)
	var light := DirectionalLight3D.new()
	world.add_child(light)
	var camera := Camera3D.new()
	world.add_child(camera)
	root.add_child(world)
	return world
func run():
	var victim = make_world()
	if "--wait-before-free" in OS.get_cmdline_user_args():
		await process_frame
		await RenderingServer.frame_post_draw
	root.remove_child(victim)
	victim.queue_free()
	victim = null
	var keep = make_world()
	for i in 8:
		await process_frame
		await RenderingServer.frame_post_draw
	keep.queue_free()
	for i in 4:
		await process_frame
		await RenderingServer.frame_post_draw
	print("SKY_REPRO_COMPLETE")
	quit()
