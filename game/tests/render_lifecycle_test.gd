extends SceneTree
# Native regression: rapid and rendered menu/match transitions must release worlds.
var checks := 0
var failures := 0
var texture_samples: Array[int] = []
func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures += 1
		push_error(message)
func _initialize() -> void: call_deferred("run")
func drawn_frames(count: int) -> void:
	for i in count:
		await process_frame
		await RenderingServer.frame_post_draw
func run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("Native lifecycle test requires a rendered display")
		quit(2)
		return
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	# This immediate transition reproduced QA-012 before the shared sky fix.
	main.start_match({"mode": "offline", "name": "Renderer QA", "difficulty": "normal"})
	await drawn_frames(3)
	main.leave_match()
	await drawn_frames(3)
	for cycle in 5:
		var old_menu: WeakRef = weakref(main.menu_world)
		main.start_match({"mode": "offline", "name": "Renderer QA", "difficulty": "normal"})
		await drawn_frames(3)
		check(old_menu.get_ref() == null, "Previous menu world released")
		var old_match: WeakRef = weakref(main.match_game)
		main.leave_match()
		await drawn_frames(3)
		check(old_match.get_ref() == null, "Previous match world released")
		var textures := RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED)
		texture_samples.append(textures)
		print("NATIVE_LIFECYCLE cycle=", cycle, " texture_bytes=", textures)
	# Warmed caches should plateau; one leaked 256px sky pair is 699,048 tracked bytes.
	check(texture_samples[-1] <= texture_samples[1] + 65536, "Texture allocations plateau across repeated sessions")
	main.queue_free()
	main = null
	await drawn_frames(4)
	print("NATIVE_LIFECYCLE_TEST checks=%d failures=%d texture_bytes=%s" % [checks, failures, texture_samples])
	quit(1 if failures else 0)
