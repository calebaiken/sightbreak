extends SceneTree
## Reproducible smoke fill-cost diagnostic. Native renderer required.
## This is a fixed-work software-rendering comparison, never mobile FPS evidence.
const ARENA = preload("res://scripts/gameplay/arena.gd")
const ACTOR = preload("res://scripts/gameplay/actor.gd")
const UTILITY = preload("res://scripts/gameplay/utility.gd")
const WARMUP_FRAMES := 8
const SAMPLE_FRAMES := 24
const CAMERA_POSITION := Vector3(-14, 1.7, -12)
const CAMERA_TARGET := Vector3(-14, 1.5, -1)
const CLOUD_POSITION := Vector3(-14, 0, -6)
var output_dir := ""
var failures: Array[String] = []

func _initialize() -> void:
	call_deferred("run")

func check(value: bool, message: String) -> void:
	if not value:
		failures.append(message)
		push_error(message)

func frame() -> void:
	await process_frame
	await RenderingServer.frame_post_draw

func summary(values: Array) -> Dictionary:
	var ordered := values.duplicate()
	ordered.sort()
	var count := ordered.size()
	var middle := count / 2
	var median := float(ordered[middle])
	if count % 2 == 0:
		median = (float(ordered[middle - 1]) + float(ordered[middle])) * 0.5
	var total := 0.0
	for value in ordered:
		total += float(value)
	return {"median": median, "p95": ordered[mini(count - 1, int(ceil(count * 0.95)) - 1)], "mean": total / count, "minimum": ordered[0], "maximum": ordered[-1]}

func measure(name: String, quads: int) -> Dictionary:
	for index in WARMUP_FRAMES:
		await frame()
	var times: Array[float] = []
	var calls: Array[int] = []
	var triangles: Array[int] = []
	var textures: Array[int] = []
	for index in SAMPLE_FRAMES:
		var before := Time.get_ticks_usec()
		await frame()
		times.append((Time.get_ticks_usec() - before) / 1000.0)
		calls.append(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME))
		triangles.append(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME))
		textures.append(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED))
	var capture := name + ".png"
	check(root.get_texture().get_image().save_png(output_dir.path_join(capture)) == OK, "Save native capture: " + name)
	return {"case": name, "alpha_quads": quads, "opaque_cores": 0 if quads == 0 else 1, "samples": SAMPLE_FRAMES, "frame_ms": summary(times), "draw_calls": summary(calls), "primitives": summary(triangles), "texture_bytes": summary(textures), "raw_frame_ms": times, "raw_draw_calls": calls, "raw_primitives": triangles, "raw_texture_bytes": textures, "capture": capture}

func run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("Smoke rendering probe requires an actual graphical renderer")
		quit(2)
		return
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="):
			output_dir = argument.trim_prefix("--output=")
	if output_dir.is_empty():
		push_error("Use -- --output=/absolute/report/directory")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(output_dir)
	root.size = Vector2i(1280, 720)
	root.content_scale_size = Vector2i(1280, 720)
	root.msaa_3d = Viewport.MSAA_2X
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	var world := Node3D.new()
	root.add_child(world)
	var arena := ARENA.new()
	world.add_child(arena)
	arena.apply_detail_quality(true)
	for light in arena.find_children("*", "DirectionalLight3D", true, false):
		light.shadow_enabled = true
	for index in 10:
		var actor := ACTOR.new()
		actor.configure(index + 1, index % 2, "Fixed smoke fixture", false)
		world.add_child(actor)
		actor.reset_for_round(Vector3(-19 + (index % 5) * 2.5, 0, -3 + (index / 5) * 4.0))
		actor.yaw = 0.10 * (index % 3)
		actor.rotation.y = actor.yaw
		actor.set_physics_process(false)
		actor.set_process(false)
	var camera := Camera3D.new()
	world.add_child(camera)
	camera.position = CAMERA_POSITION
	camera.fov = 75
	camera.look_at(CAMERA_TARGET)
	camera.make_current()
	# Cache the one shared cloud texture before clear measurement so all cases
	# include the same allocation; it remains cached after the cloud is removed.
	UTILITY.smoke_texture()
	var original_quality: bool = UTILITY.high_quality_smoke
	var results := []
	results.append(await measure("clear", 0))
	for high in [true, false]:
		UTILITY.high_quality_smoke = high
		var smoke := UTILITY.new()
		smoke.kind = "smoke"
		smoke.visual_only = true
		world.add_child(smoke)
		smoke.position = CLOUD_POSITION
		# Stop the twelve-second physics lifetime and rotation, while allowing the
		# normal 0.8-second idle growth tweens to finish before any measurements.
		smoke.set_physics_process(false)
		smoke._detonate()
		var started := Time.get_ticks_usec()
		var mature := false
		while Time.get_ticks_usec() - started < 10_000_000:
			await frame()
			mature = true
			for puff in smoke._cloud_puffs:
				mature = mature and puff.scale.is_equal_approx(Vector3.ONE)
			if mature:
				break
		check(mature, "Smoke growth must finish before sampling")
		var quads := 6 if high else 3
		check(smoke._cloud_puffs.size() == quads + 1, "Cloud matches expected alpha-quad count plus opaque core")
		check(is_equal_approx(smoke._lifetime, 12.0), "Disabled smoke physics preserves the same mature fixture throughout measurement")
		results.append(await measure("standard_cloud" if high else "low_cloud", quads))
		var retired: WeakRef = weakref(smoke)
		smoke.queue_free()
		smoke = null
		for index in 3:
			await frame()
		check(retired.get_ref() == null, "Retired cloud releases its scene nodes")
	UTILITY.high_quality_smoke = original_quality
	var clear_median := float(results[0].frame_ms.median)
	for index in range(1, results.size()):
		results[index]["median_ms_delta_vs_clear"] = float(results[index].frame_ms.median) - clear_median
		results[index]["median_ms_ratio_vs_clear"] = float(results[index].frame_ms.median) / clear_median
	var report := {
		"context": "Native Linux graphical renderer with fixed arena/camera/ten operators; wall-clock rendered frame cost. NOT physical-device FPS, GPU timings, thermal, battery or network evidence.",
		"engine": Engine.get_version_info().string,
		"renderer": RenderingServer.get_video_adapter_name(),
		"viewport": [1280, 720], "camera_position": [CAMERA_POSITION.x, CAMERA_POSITION.y, CAMERA_POSITION.z],
		"camera_target": [CAMERA_TARGET.x, CAMERA_TARGET.y, CAMERA_TARGET.z], "camera_fov": 75,
		"cloud_position": [CLOUD_POSITION.x, 1.6, CLOUD_POSITION.z],
		"fixed_operators": 10, "warmup_frames_per_case": WARMUP_FRAMES, "samples_per_case": SAMPLE_FRAMES,
		"scene_quality": "Standard scene details/shadows and 2xMSAA held constant. Low changes only smoke alpha quads from six to three.",
		"limitations": "A mature cloud replaces visible geometry with an opaque core and transparent boundary. Costs include that scene occlusion change, not an isolated fragment-shader microbenchmark. Shared smoke texture preallocated in all cases. No animation, camera movement, combat, physics, lifetime expiry or ten-human match load.",
		"percentiles": "Median averages the middle two of24; p95 uses nearest rank.", "results": results, "failures": failures
	}
	var file := FileAccess.open(output_dir.path_join("metrics.json"), FileAccess.WRITE)
	if file == null:
		check(false, "Open smoke metrics output")
	else:
		file.store_string(JSON.stringify(report, "\t"))
		file.close()
	world.queue_free()
	for index in 4:
		await frame()
	print("SMOKE_RENDER_PROBE ", JSON.stringify(report))
	quit(0 if failures.is_empty() else 1)
