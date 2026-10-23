extends Node
## Isolated exported diagnostic. This file is copied into a temporary project;
## it is never included in the shipping game or used as an acceptance substitute.
const Main = preload("res://scripts/main.gd")
const CASES := ["full", "shadows-off", "surface-detail-off", "sky-off", "materials-untextured"]
var render_case := "full"
var capture := ""
var main
var changed := 0

func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--render-case="): render_case = arg.trim_prefix("--render-case=")
		if arg.begins_with("--capture="): capture = arg.trim_prefix("--capture=")
	if render_case not in CASES or capture.is_empty() or DisplayServer.get_name() == "headless":
		push_error("Render diagnostic needs a valid case, capture path and native display")
		get_tree().quit(2)
		return
	print("RENDER_DIAG phase=begin case=", render_case, " msec=", Time.get_ticks_msec())
	main = Main.new()
	add_child(main)
	# Freeze one shipping menu view so wall time cannot move different cases
	# to different camera positions. UI, world geometry and rendering stay active.
	main._process(0.0)
	main.set_process(false)
	match render_case:
		"shadows-off":
			for light in main.find_children("*", "DirectionalLight3D", true, false):
				if light.shadow_enabled:
					light.shadow_enabled = false
					changed += 1
		"surface-detail-off":
			for node in main.find_children("*", "Node3D", true, false):
				if node.has_method("apply_detail_quality"):
					node.apply_detail_quality(false)
					changed += 1
		"sky-off":
			for world in main.find_children("*", "WorldEnvironment", true, false):
				world.environment.background_mode = Environment.BG_COLOR
				world.environment.background_color = Color("a3b2b9")
				world.environment.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED
				world.environment.sky = null
				changed += 1
		"materials-untextured":
			for material in main.menu_world.get_child(0)._surface_materials.keys():
				if material.albedo_texture != null:
					material.albedo_texture = null
					material.normal_enabled = false
					material.normal_texture = null
					material.roughness_texture = null
					changed += 1
	if render_case != "full" and changed == 0:
		push_error("Render diagnostic did not change its named feature")
		get_tree().quit(3)
		return
	print("RENDER_DIAG phase=constructed case=", render_case, " changed=", changed, " msec=", Time.get_ticks_msec())
	observe.call_deferred()

func observe() -> void:
	for frame in range(1, 16):
		await RenderingServer.frame_post_draw
		print("RENDER_DIAG phase=drawn frame=", frame, " case=", render_case,
			" msec=", Time.get_ticks_msec(),
			" draws=", Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
			" primitives=", Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME))
	var error := get_viewport().get_texture().get_image().save_png(capture)
	print("RENDER_DIAG_EXIT capture_error=", error, " case=", render_case, " msec=", Time.get_ticks_msec())
	get_tree().quit(0 if error == OK else 1)
