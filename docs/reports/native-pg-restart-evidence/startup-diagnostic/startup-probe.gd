extends SceneTree
func _initialize() -> void:
	print("STARTUP_PROBE initialize pid=", OS.get_process_id())
	call_deferred("run")
func run() -> void:
	print("STARTUP_PROBE loading ui")
	var scene = load("res://scripts/ui/economy_ui.gd")
	print("STARTUP_PROBE loaded ui")
	var ui = scene.new()
	root.add_child(ui)
	print("STARTUP_PROBE ready")
	ui.queue_free()
	await process_frame
	await process_frame
	quit(0)
