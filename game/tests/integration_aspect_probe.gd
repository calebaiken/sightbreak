extends SceneTree
## Diagnostic only: compares actual keep/expand window policies without changing
## project settings. Synthetic touch bounds are not physical notch/device evidence.
var output := ""
var rows: Array = []
var failures := 0

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
	_run.call_deferred()

func _settle() -> void:
	for i in 8: await process_frame
	if DisplayServer.get_name() != "headless": await RenderingServer.frame_post_draw

func _run() -> void:
	if output.is_empty():
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(output)
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	main.profile.data.settings.touch_visible = true
	main.profile.data.settings.hud_positions = {}
	main.profile.data.settings.fov = 82
	main.start_match({"mode": "offline", "name": "Aspect fixture"})
	main.match_game.set_physics_process(false)
	var actor: SBActor = main.match_game.local_actor()
	actor.credits = 5000
	actor.buy_weapon("rifle")
	actor.reset_for_round(Vector3(3, 0.05, -12))
	actor.yaw = 0.35
	actor.rotation.y = 0.35
	actor.pitch = -0.025
	actor.tick_visual(0.016)
	for policy in ["keep", "expand"]:
		root.content_scale_aspect = Window.CONTENT_SCALE_ASPECT_KEEP if policy == "keep" else Window.CONTENT_SCALE_ASPECT_EXPAND
		root.content_scale_size = Vector2i(1280, 720)
		for dimensions in [Vector2i(1280,720), Vector2i(1440,720), Vector2i(1560,720), Vector2i(1600,720), Vector2i(960,720)]:
			root.size = dimensions
			await _settle()
			var logical := root.get_visible_rect().size
			var xform := root.get_screen_transform()
			var left := actor.camera.project_local_ray_normal(Vector2(0,logical.y * 0.5))
			var right := actor.camera.project_local_ray_normal(Vector2(logical.x,logical.y * 0.5))
			var top := actor.camera.project_local_ray_normal(Vector2(logical.x * 0.5,0))
			var bottom := actor.camera.project_local_ray_normal(Vector2(logical.x * 0.5,logical.y))
			var bounds_ok := true
			for control_name in main.touch.positions:
				var point: Vector2 = main.touch.control_point(control_name)
				var radius: float = main.touch.radius(control_name)
				bounds_ok = bounds_ok and point.x-radius >= 0 and point.y-radius >= 0 and point.x+radius <= logical.x and point.y+radius <= logical.y
			var centered: bool = main.crosshair.get_global_rect().get_center().distance_to(logical * 0.5) < 1.0
			var hud_bounds := {}
			for pair in [["radar",main.radar],["ammo",main.ammo_label],["health",main.health_label],["funds",main.funds_label]]:
				hud_bounds[pair[0]] = Rect2(Vector2.ZERO,logical).encloses(pair[1].get_global_rect())
				if not hud_bounds[pair[0]]: failures += 1
			var row := {"policy":policy, "window":[dimensions.x,dimensions.y], "logical":[logical.x,logical.y], "screen_origin":[xform.origin.x,xform.origin.y], "screen_scale":[xform.x.x,xform.y.y], "world_horizontal_fov_deg":rad_to_deg(left.angle_to(right)), "world_vertical_fov_deg":rad_to_deg(top.angle_to(bottom)), "camera_keep_aspect":actor.camera.keep_aspect, "crosshair_centered":centered, "touch_bounds":bounds_ok, "viewmodel_vertical_fov_deg":54, "safe_area_device":"UNVERIFIED"}
			if not centered or not bounds_ok: failures += 1
			row["hud_bounds"] = hud_bounds
			if DisplayServer.get_name() != "headless":
				var picture := root.get_texture().get_image()
				row["capture_dimensions"] = [picture.get_width(),picture.get_height()]
				if picture.save_png(output.path_join("%s-%dx%d.png" % [policy,dimensions.x,dimensions.y])) != OK: failures += 1
			rows.append(row)
	main.queue_free()
	await _settle()
	var file := FileAccess.open(output.path_join("metrics.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify({"scope":"native window policy fixture; shipping setting unchanged; no physical safe-area claim", "rows":rows, "failures":failures}, "\t"))
	file.close()
	print("INTEGRATION_ASPECT rows=%d failures=%d" % [rows.size(),failures])
	quit(1 if failures else 0)
