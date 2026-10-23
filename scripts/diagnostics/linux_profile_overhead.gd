extends Node
## Unshipped static diagnostic overlay. No match, authority or visual ticks.
const WARM := 32
const SAMPLES := 64
var output := ""
var token := ""
var callbacks := 0
var world: Node3D
var ledger: Dictionary
var ledger_hash := ""
var canonical_seen: Dictionary = {}
var report: Dictionary = {}
var failure := ""

func _ready() -> void:
	RenderingServer.frame_post_draw.connect(_post_draw)
	_run.call_deferred()

func _post_draw() -> void:
	callbacks += 1

func _fail(message: String) -> void:
	failure = message
	push_error("LINUX_PROFILE_OVERHEAD " + message)
	get_tree().quit(2)

func _endpoint() -> Dictionary:
	return {"clock_usec": Time.get_ticks_usec(), "counter": Engine.get_frames_drawn(), "callback": callbacks}

func _await_ack(name: String) -> bool:
	# Hold the main thread before the cold anchor / after readback. This creates
	# no intervening draws and keeps controller I/O outside sampled intervals.
	var deadline := Time.get_ticks_msec() + 15000
	while not FileAccess.file_exists(output.path_join(name)):
		if Time.get_ticks_msec() >= deadline:
			_fail("Controller handshake timed out: " + name)
			return false
		OS.delay_msec(10)
	if FileAccess.get_file_as_string(output.path_join(name)) != token:
		_fail("Controller handshake token differs")
		return false
	return true

func _write(name: String, value: Dictionary) -> void:
	var temporary := output.path_join(name + ".pending")
	if FileAccess.file_exists(temporary):
		_fail("Preserve incomplete publication " + temporary)
		return
	var file := FileAccess.open(temporary, FileAccess.WRITE)
	if file == null:
		_fail("Cannot write " + name)
		return
	file.store_string(JSON.stringify(value, "\t", true, true))
	file.close()
	if DirAccess.rename_absolute(temporary, output.path_join(name)) != OK:
		_fail("Cannot publish " + name)

func _settings() -> Dictionary:
	var viewport := get_window()
	var texture_size := viewport.get_texture().get_size()
	return {"viewport": [viewport.size.x, viewport.size.y], "texture_size": [int(texture_size.x), int(texture_size.y)],
		"msaa_3d": viewport.msaa_3d, "render_scale": viewport.scaling_3d_scale, "scaling_3d_mode": viewport.scaling_3d_mode,
		"max_fps": Engine.max_fps, "physics_hz": Engine.physics_ticks_per_second,
		"physics_limit": Engine.max_physics_steps_per_frame, "jitter_fix": Engine.physics_jitter_fix,
		"time_scale": Engine.time_scale, "vsync_mode": DisplayServer.window_get_vsync_mode(),
		"thread_model_project": ProjectSettings.get_setting("rendering/driver/threads/thread_model", 1),
		"caller_is_main_thread": OS.get_thread_caller_id() == OS.get_main_thread_id(),
		"caller_is_render_thread": RenderingServer.is_on_render_thread(),
		"print_profile_setting": ProjectSettings.get_setting("debug/settings/stdout/print_gpu_profile", false)}

func _canonical(value):
	# No RID, runtime instance ID or unused actor RNG state enters the result.
	match typeof(value):
		TYPE_NIL, TYPE_BOOL, TYPE_INT, TYPE_FLOAT, TYPE_STRING, TYPE_STRING_NAME, TYPE_NODE_PATH:
			return str(value) if typeof(value) in [TYPE_STRING_NAME, TYPE_NODE_PATH] else value
		TYPE_COLOR:
			return [value.r, value.g, value.b, value.a]
		TYPE_VECTOR2, TYPE_VECTOR2I:
			return [value.x, value.y]
		TYPE_VECTOR3, TYPE_VECTOR3I:
			return [value.x, value.y, value.z]
		TYPE_VECTOR4, TYPE_VECTOR4I, TYPE_QUATERNION:
			return [value.x, value.y, value.z, value.w]
		TYPE_BASIS:
			return [_canonical(value.x), _canonical(value.y), _canonical(value.z)]
		TYPE_TRANSFORM3D:
			return {"basis": _canonical(value.basis), "origin": _canonical(value.origin)}
		TYPE_TRANSFORM2D:
			return [_canonical(value.x), _canonical(value.y), _canonical(value.origin)]
		TYPE_AABB:
			return [_canonical(value.position), _canonical(value.size)]
		TYPE_RECT2, TYPE_RECT2I:
			return [_canonical(value.position), _canonical(value.size)]
		TYPE_PLANE:
			return [_canonical(value.normal), value.d]
		TYPE_PROJECTION:
			return [_canonical(value.x), _canonical(value.y), _canonical(value.z), _canonical(value.w)]
		TYPE_PACKED_BYTE_ARRAY, TYPE_PACKED_INT32_ARRAY, TYPE_PACKED_INT64_ARRAY, TYPE_PACKED_FLOAT32_ARRAY, TYPE_PACKED_FLOAT64_ARRAY, TYPE_PACKED_STRING_ARRAY, TYPE_PACKED_VECTOR2_ARRAY, TYPE_PACKED_VECTOR3_ARRAY, TYPE_PACKED_VECTOR4_ARRAY, TYPE_PACKED_COLOR_ARRAY:
			var hashing := HashingContext.new()
			hashing.start(HashingContext.HASH_SHA256)
			hashing.update(var_to_bytes(value))
			return {"packed_type": typeof(value), "count": value.size(), "sha256": hashing.finish().hex_encode()}
		TYPE_ARRAY:
			var result := []
			for item in value: result.append(_canonical(item))
			return result
		TYPE_DICTIONARY:
			var result := {}
			var keys: Array = value.keys()
			keys.sort_custom(func(a, b): return str(typeof(a)) + JSON.stringify(a, "", true, true) < str(typeof(b)) + JSON.stringify(b, "", true, true))
			for key in keys:
				if typeof(key) not in [TYPE_STRING, TYPE_STRING_NAME, TYPE_INT, TYPE_FLOAT]:
					_fail("Unsupported canonical dictionary key")
					return null
				result[str(typeof(key)) + ":" + JSON.stringify(_canonical(key), "", true, true)] = _canonical(value[key])
			return result
		TYPE_OBJECT:
			if value is Resource:
				return _resource(value)
			_fail("Unsupported canonical object")
			return null
		_:
			_fail("Unsupported canonical variant: " + str(typeof(value)))
			return null

func _resource(value: Resource) -> Dictionary:
	# IDs are used only for in-memory cycle detection; deterministic traversal
	# assigns stable reference labels that contain no process identity.
	var identity := value.get_instance_id()
	if canonical_seen.has(identity): return {"reference": canonical_seen[identity]}
	var label := "resource-" + str(canonical_seen.size())
	canonical_seen[identity] = label
	var result := {"reference_label": label, "class": value.get_class(), "path": value.resource_path}
	var base_path := value.resource_path.trim_prefix("res://").split("::")[0]
	if not base_path.is_empty():
		if not ledger.content.has(base_path):
			_fail("Resource lacks a frozen content identity: " + base_path)
			return result
		result["content_sha256"] = ledger.content[base_path]
	# Texture image readback is excluded from fingerprinting. Its immutable
	# source identity plus the material's actual sampler parameters are retained.
	if value is Texture2D or value is Texture3D or value is TextureLayered:
		if base_path.is_empty(): _fail("Generated texture lacks an immutable source identity")
		return result
	if value is Script:
		return result
	var properties := {}
	var names := []
	for property in value.get_property_list():
		if int(property.usage) & PROPERTY_USAGE_STORAGE and property.name not in ["resource_path", "resource_scene_unique_id"]:
			names.append(str(property.name))
	names.sort()
	for name in names: properties[name] = _canonical(value.get(name))
	result["properties"] = properties
	return result

func _node_key(node: Node) -> String:
	var parts := []
	var cursor := node
	while cursor != world:
		parts.push_front(str(cursor.get_index()))
		cursor = cursor.get_parent()
	return "world/" + "/".join(parts)

func _node(node: Node) -> Dictionary:
	var state := {"path": _node_key(node), "class": node.get_class(),
		"process_mode": node.process_mode, "process": node.is_processing(), "physics_process": node.is_physics_processing()}
	if node is Node3D:
		state["transform"] = _canonical(node.transform)
		state["global_transform"] = _canonical(node.global_transform)
		state["top_level"] = node.is_set_as_top_level()
		state["visible"] = node.visible
		state["visible_in_tree"] = node.is_visible_in_tree()
	if node is GeometryInstance3D:
		state["geometry"] = {"layers": node.layers, "cast_shadow": node.cast_shadow, "transparency": node.transparency,
			"material_override": _canonical(node.material_override), "material_overlay": _canonical(node.material_overlay),
			"extra_cull_margin": node.extra_cull_margin, "sorting_offset": node.sorting_offset,
			"visibility_range_begin": node.visibility_range_begin, "visibility_range_end": node.visibility_range_end,
			"visibility_range_begin_margin": node.visibility_range_begin_margin, "visibility_range_end_margin": node.visibility_range_end_margin,
			"visibility_range_fade_mode": node.visibility_range_fade_mode, "lod_bias": node.lod_bias,
			"ignore_occlusion_culling": node.ignore_occlusion_culling}
		var instance_parameters := {}
		for property in node.get_property_list():
			var name := str(property.name)
			if name.begins_with("instance_shader_parameters/"):
				instance_parameters[name] = _canonical(node.get(name))
		state["instance_shader_parameters"] = instance_parameters
	if node is MeshInstance3D:
		state["mesh"] = _canonical(node.mesh)
		state["skin"] = _canonical(node.skin)
		var overrides := []
		for index in node.get_surface_override_material_count(): overrides.append(_canonical(node.get_surface_override_material(index)))
		state["surface_overrides"] = overrides
	if node is MultiMeshInstance3D:
		state["multimesh"] = _canonical(node.multimesh)
		var instances := []
		for index in node.multimesh.instance_count:
			instances.append({"transform": _canonical(node.multimesh.get_instance_transform(index)),
				"color": _canonical(node.multimesh.get_instance_color(index)) if node.multimesh.use_colors else null,
				"custom": _canonical(node.multimesh.get_instance_custom_data(index)) if node.multimesh.use_custom_data else null})
		state["instance_data"] = {"instances": instances, "visible_count": node.multimesh.visible_instance_count,
			"transform_format": node.multimesh.transform_format}
	if node is Camera3D:
		state["camera"] = {"current": node.current, "fov": node.fov, "near": node.near, "far": node.far,
			"projection": node.projection, "keep_aspect": node.keep_aspect, "cull_mask": node.cull_mask,
			"h_offset": node.h_offset, "v_offset": node.v_offset, "frustum_offset": _canonical(node.frustum_offset),
			"environment": _canonical(node.environment), "attributes": _canonical(node.attributes)}
	if node is Light3D:
		var properties := {}
		for property in node.get_property_list():
			var name := str(property.name)
			if int(property.usage) & PROPERTY_USAGE_STORAGE and (name.begins_with("light_") or name.begins_with("shadow_") or name.begins_with("directional_") or name.begins_with("omni_") or name.begins_with("spot_")):
				properties[name] = _canonical(node.get(name))
		state["light"] = properties
	if node is WorldEnvironment:
		state["environment"] = _canonical(node.environment)
		state["camera_attributes"] = _canonical(node.camera_attributes)
	if node is Label3D:
		state["label"] = {"text": node.text, "font": _canonical(node.font), "font_size": node.font_size,
			"modulate": _canonical(node.modulate), "pixel_size": node.pixel_size,
			"outline_size": node.outline_size, "billboard": node.billboard, "alpha_cut": node.alpha_cut}
	if node is Skeleton3D:
		var bones := []
		for index in node.get_bone_count():
			bones.append({"name": node.get_bone_name(index), "parent": node.get_bone_parent(index),
				"rest": _canonical(node.get_bone_rest(index)), "pose": _canonical(node.get_bone_pose(index))})
		state["bones"] = bones
	if node is AnimationPlayer:
		state["animation"] = {"mode": node.callback_mode_process, "assigned": node.assigned_animation,
			"position": node.current_animation_position, "playing": node.is_playing()}
	return state

func _fingerprint() -> Dictionary:
	canonical_seen.clear()
	var nodes := [world]
	nodes.append_array(world.find_children("*", "", true, false))
	nodes.sort_custom(func(a, b): return _node_key(a) < _node_key(b))
	var entries := []
	for node in nodes: entries.append(_node(node))
	var value := {"source_ledger_sha256": ledger_hash, "settings": _settings(), "nodes": entries}
	var serialized := JSON.stringify(value, "", true, true)
	return {"serialized": serialized, "sha256": serialized.sha256_text()}

func _intervals(count: int, previous: Dictionary) -> Array:
	var rows := []
	for index in count:
		await get_tree().process_frame
		await RenderingServer.frame_post_draw
		var current := _endpoint()
		if current.counter != previous.counter + 1 or current.callback != previous.callback + 1 or current.clock_usec <= previous.clock_usec:
			_fail("Skipped/duplicate/nonpositive post-draw interval")
			return []
		rows.append({"begin": previous, "end": current,
			"draw_calls": int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)),
			"primitives": int(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME))})
		previous = current
	return rows

func _run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg.begins_with("--token="): token = arg.trim_prefix("--token=")
	if output.is_empty() or token.is_empty() or DisplayServer.get_name() == "headless":
		_fail("Native display, fresh output and token required")
		return
	if ProjectSettings.get_setting("debug/settings/stdout/print_gpu_profile", false) != false:
		_fail("Project profile printing must be off")
		return
	# Godot consumes --render-thread before exposing its filtered argument list.
	# The controller verifies exact full argv separately; verify effective state
	# here on the main thread, including a rejection of a separate render thread.
	if OS.get_thread_caller_id() != OS.get_main_thread_id() or not RenderingServer.is_on_render_thread():
		_fail("Pinned synchronous safe main/render thread identity required")
		return
	ledger_hash = FileAccess.get_sha256("res://diagnostics/source_ledger.json")
	ledger = JSON.parse_string(FileAccess.get_file_as_string("res://diagnostics/source_ledger.json"))
	get_window().size = Vector2i(1280, 720)
	get_window().content_scale_size = Vector2i(1280, 720)
	get_viewport().msaa_3d = Viewport.MSAA_2X
	get_viewport().scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	get_viewport().scaling_3d_scale = 1.0
	Engine.max_fps = 60
	world = Node3D.new()
	world.name = "FixedWorld"
	add_child(world)
	var arena = load("res://scripts/gameplay/arena.gd").new()
	world.add_child(arena)
	var actor_script = load("res://scripts/gameplay/actor.gd")
	for index in 5:
		var actor = actor_script.new()
		actor.name = "FixedActor" + str(index)
		actor.configure(index + 1, 0 if index == 0 else (index - 1) % 2, "Static profile fixture", index == 0)
		world.add_child(actor)
		if index == 0:
			actor.credits = 5000
			actor.buy_weapon("rifle")
			actor.reset_for_round(Vector3(-14, 0, -18))
			actor.yaw = PI
			actor.pitch = -0.12
			actor.rotation.y = PI
			actor.camera.rotation.x = -0.12
		else:
			var other := index - 1
			actor.reset_for_round(Vector3(-16 + other * 1.3, 0, -7 + other % 2))
			actor.yaw = 0.18 * other
			actor.rotation.y = actor.yaw
	# Actor weapon arms already use manual AnimationPlayer processing. Disable
	# automatic world callbacks, preserving static rendering and authored state.
	world.process_mode = Node.PROCESS_MODE_DISABLED
	# Let construction-only queue_free calls retire before the initial stable
	# fingerprint. This endpoint is outside cold/anchor and sampled intervals.
	await get_tree().process_frame
	report = {"schema": 1, "token": token, "settings": _settings(), "engine": Engine.get_version_info(),
		"engine_arguments_filtered": OS.get_cmdline_args(),
		"adapter": {"name": RenderingServer.get_video_adapter_name(), "vendor": RenderingServer.get_video_adapter_vendor(),
			"api": RenderingServer.get_video_adapter_api_version()}, "source_ledger_sha256": ledger_hash,
		"workload": {"actors": 5, "view": "approach", "static": true, "authority_ticks": 0, "visual_ticks": 0},
		"construction_settled": _endpoint(),
		"fingerprint_initial": _fingerprint()}
	if not failure.is_empty(): return
	_write("ready.json", report)
	if not _await_ack("begin.ack"): return
	report["cold_before"] = _endpoint()
	await RenderingServer.frame_post_draw
	report["anchor"] = _endpoint()
	report["warm"] = await _intervals(WARM, report.anchor)
	if not failure.is_empty(): return
	report["measured"] = await _intervals(SAMPLES, report.warm[-1].end)
	if not failure.is_empty(): return
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	report["readback"] = _endpoint()
	report["fingerprint_terminal"] = _fingerprint()
	if not failure.is_empty(): return
	if get_viewport().get_texture().get_image().save_png(output.path_join("proof.png")) != OK:
		_fail("Image save failed")
		return
	report["png_sha256"] = FileAccess.get_sha256(output.path_join("proof.png"))
	report["readback_after"] = _endpoint()
	_write("metrics.json", report)
	if not _await_ack("finish.ack"): return
	RenderingServer.frame_post_draw.disconnect(_post_draw)
	print("LINUX_PROFILE_OVERHEAD intervals=32+64 anchor=separate readback=later")
	get_tree().quit(0)
