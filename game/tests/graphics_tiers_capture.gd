extends SceneTree
## Renders the twelve Relay Yard review viewpoints (the layout review set) at one graphics tier, for before/after and
## tier comparison, and records relative frame cost per view. Run it once per tier under a real display:
##   --tier=0..3 --capture-dir=<dir> --size=WxH (default 1280x720) --prefix=<file prefix> (default tier)
## Isolation overrides, applied after the tier, to attribute a difference to one setting:
##   --ssao=0|1
##   --msaa=<Viewport.MSAA int>  --aniso=<0..16>  --scale=<3D render scale, above 1 supersamples>
##   --env=<property>:<value>,...  --light=<property>:<value>,...  --sky=<property>:<value>,... (the procedural sky material)
##   --only=<view numbers, comma separated> renders just those views.
## Timings come from whatever renderer the host has (software rasteriser in CI); compare tiers on the same host
## only, never read them as device frame rates.
const VIEWS := [
	["01-attacker-pocket-looking-south", Vector2(0, -21), Vector2(0, -8)],
	["02-mid-pocket-looking-south", Vector2(0, -13), Vector2(0, 14)],
	["03-west-exit-looking-south", Vector2(-16.5, -16), Vector2(-15, 12)],
	["04-east-exit-looking-south", Vector2(16.5, -16), Vector2(15, 12)],
	["05-west-lane-to-site-a", Vector2(-11, -8), Vector2(-15, 10)],
	["06-mid-chicane-looking-south", Vector2(-4, -8), Vector2(0, 14)],
	["07-site-a-from-north-approach", Vector2(-12, 2), Vector2(-15, 10)],
	["08-site-a-defender-looking-north", Vector2(-15, 17), Vector2(-15, -14)],
	["09-defender-spawn-looking-north", Vector2(0, 20.5), Vector2(0, -18)],
	["10-site-b-defender-looking-north", Vector2(15, 17), Vector2(15, -14)],
	["11-yard-centre-looking-south", Vector2(0, -3), Vector2(0, 14)],
	["12-yard-centre-looking-north", Vector2(0, 6), Vector2(0, -16)],
]
const EYE := 1.62
const TIMED_FRAMES := 40
var output := "res://../builds/qa/graphics-tiers"
var prefix := "tier"
var tier := SBGraphicsQuality.MEDIUM
var overrides := {}
var only := PackedStringArray()

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var size := Vector2i(1280, 720)
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture-dir="):
			output = argument.trim_prefix("--capture-dir=")
		elif argument.begins_with("--prefix="):
			prefix = argument.trim_prefix("--prefix=")
		elif argument.begins_with("--tier="):
			tier = int(argument.trim_prefix("--tier="))
		elif argument.begins_with("--only="):
			only = argument.trim_prefix("--only=").split(",")
		elif argument.begins_with("--ssao=") or argument.begins_with("--msaa=") or argument.begins_with("--aniso=") or argument.begins_with("--scale=") or argument.begins_with("--env=") or argument.begins_with("--light=") or argument.begins_with("--sky="):
			overrides[argument.get_slice("=", 0).trim_prefix("--")] = argument.get_slice("=", 1)
		elif argument.begins_with("--size="):
			var parts := argument.trim_prefix("--size=").split("x")
			if parts.size() == 2:
				size = Vector2i(int(parts[0]), int(parts[1]))
	root.content_scale_size = size
	root.size = size
	DirAccess.make_dir_recursive_absolute(output)
	SBGraphicsQuality.current = tier
	var world := Node3D.new()
	root.add_child(world)
	world.add_child(RelayYard.new())
	var camera := Camera3D.new()
	camera.fov = 82.0
	camera.near = 0.05
	camera.far = 200.0
	world.add_child(camera)
	camera.current = true
	SBGraphicsQuality.apply(world, root, tier, 1.0, false)
	for key in overrides:
		match key:
			"ssao":
				world.find_children("*", "WorldEnvironment", true, false)[0].environment.ssao_enabled = overrides[key] == "1"
			"msaa":
				root.msaa_3d = int(overrides[key])
			"aniso":
				root.anisotropic_filtering_level = int(overrides[key])
			"scale":
				root.scaling_3d_scale = float(overrides[key])
			"env":
				for pair in String(overrides[key]).split(","):
					world.find_children("*", "WorldEnvironment", true, false)[0].environment.set(pair.get_slice(":", 0), float(pair.get_slice(":", 1)))
			"sky":
				var sky_material = world.find_children("*", "WorldEnvironment", true, false)[0].environment.sky.sky_material
				for pair in String(overrides[key]).split(","):
					sky_material.set(pair.get_slice(":", 0), float(pair.get_slice(":", 1)))
			"light":
				for pair in String(overrides[key]).split(","):
					world.find_children("*", "DirectionalLight3D", true, false)[0].set(pair.get_slice(":", 0), float(pair.get_slice(":", 1)))
	var timings := {}
	for view in VIEWS:
		if not only.is_empty() and not only.has(String(view[0]).left(2)):
			continue
		var at: Vector2 = view[1]
		var target: Vector2 = view[2]
		camera.look_at_from_position(Vector3(at.x, EYE, at.y), Vector3(target.x, EYE - 0.15, target.y), Vector3.UP)
		for _i in 3:
			await process_frame
		await RenderingServer.frame_post_draw
		var image := root.get_texture().get_image()
		var path := output.path_join("%s%d-%s.png" % [prefix, tier, view[0]])
		if image.save_png(path) != OK:
			push_error("Capture failed: " + path)
		var samples := PackedFloat64Array()
		for _i in TIMED_FRAMES:
			var started := Time.get_ticks_usec()
			await RenderingServer.frame_post_draw
			samples.append((Time.get_ticks_usec() - started) / 1000.0)
		samples.sort()
		timings[view[0]] = {"median_ms": samples[samples.size() / 2], "p95_ms": samples[int(samples.size() * 0.95)]}
		print("TIER_VIEW tier=%d %s median_ms=%.2f p95_ms=%.2f" % [tier, view[0], timings[view[0]].median_ms, timings[view[0]].p95_ms])
	var report := FileAccess.open(output.path_join("%s%d-timings.json" % [prefix, tier]), FileAccess.WRITE)
	report.store_string(JSON.stringify({"tier": tier, "size": [size.x, size.y], "renderer": RenderingServer.get_current_rendering_method(), "adapter": RenderingServer.get_video_adapter_name(), "views": timings}, "\t"))
	report.close()
	world.queue_free()
	await process_frame
	quit()
