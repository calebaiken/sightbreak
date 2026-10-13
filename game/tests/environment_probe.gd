extends SceneTree
## Fixed native views for surface/lighting comparisons; no gameplay simulation.
const Arena = preload("res://scripts/gameplay/arena.gd")
const Actor = preload("res://scripts/gameplay/actor.gd")
var output_dir := "res://../builds/qa/environment"
func _initialize() -> void:
	run.call_deferred()
func run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("Environment probe needs a graphical display")
		quit(2)
		return
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):
			output_dir = arg.trim_prefix("--output=")
	DirAccess.make_dir_recursive_absolute(output_dir)
	var world := Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	var actor := Actor.new()
	actor.configure(1, 0, "Surface review", true)
	world.add_child(actor)
	actor.credits = 5000
	actor.buy_weapon("rifle")
	var views := [
		{"name": "approach", "at": Vector3(-14, 0, -18), "yaw": PI, "pitch": -0.12},
		{"name": "site", "at": Vector3(-16, 0, 3), "yaw": PI + 0.13, "pitch": -0.10},
		{"name": "overview", "at": Vector3(18, 8, -18), "yaw": PI * 0.76, "pitch": -0.42}
	]
	var metrics := []
	for view in views:
		actor.reset_for_round(view.at)
		actor.rotation.y = view.yaw
		actor.camera.rotation.x = view.pitch
		actor._gun.visible = view.name != "overview"
		for i in range(5):
			await process_frame
			await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(output_dir.path_join(view.name + ".png"))
		metrics.append({"view": view.name, "draw_calls": Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), "primitives": Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)})
	var report := {"context": "Native Godot Linux Xvfb, Mesa llvmpipe software rendering; not physical-device measurements", "views": metrics}
	var file := FileAccess.open(output_dir.path_join("metrics.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t"))
	file.close()
	print("ENVIRONMENT_PROBE ", JSON.stringify(report))
	world.queue_free()
	for i in range(5):
		await process_frame
		await RenderingServer.frame_post_draw
	quit(0)
