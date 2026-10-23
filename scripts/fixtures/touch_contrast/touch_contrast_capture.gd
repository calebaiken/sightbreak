extends SceneTree
## Native only. --mode=backgrounds first; then --mode=controls --background-dir=...
const OriginalTouch = preload("res://scripts/ui/touch_controls.gd")
const ProbeTouch = preload("res://tests/touch_contrast_instrumented.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const Utility = preload("res://scripts/gameplay/utility.gd")
const GROUPS := ["active_label", "inactive_label", "active_icon", "inactive_icon", "empty_count", "ready_count", "border", "held_border", "joystick_ring", "joystick_knob"]
const LAYOUTS := [
	{"id": "mobile-min", "size": Vector2i(960, 720), "scale": 0.7, "inset": 32},
	{"id": "mobile-max", "size": Vector2i(960, 720), "scale": 1.5, "inset": 32},
	{"id": "desktop-min", "size": Vector2i(1280, 720), "scale": 0.7, "inset": 0},
	{"id": "desktop-max", "size": Vector2i(1280, 720), "scale": 1.5, "inset": 0}]
var options: Dictionary = {}
var records: Array = []
var written_images: Dictionary = {}

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		var pair := arg.trim_prefix("--").split("=", true, 1)
		if pair.size() == 2: options[pair[0]] = pair[1]
	call_deferred("run")

func settle() -> void:
	await process_frame
	await RenderingServer.frame_post_draw

func image_at(path: String) -> void:
	await settle()
	var image := root.get_texture().get_image()
	assert(image.save_png(path) == OK, "cannot save " + path)
	written_images[path] = FileAccess.get_sha256(path)

func layout(config: Dictionary) -> void:
	root.content_scale_size = config.size
	root.size = config.size
	await settle()

func backgrounds(out: String) -> void:
	var arena = Arena.new()
	root.add_child(arena)
	var camera := Camera3D.new()
	root.add_child(camera)
	camera.position = Vector3(0, 1.65, -18)
	camera.look_at(Vector3(0, 1.5, 8))
	camera.current = true
	var smoke = Utility.new()
	smoke.kind = "smoke"
	smoke.visual_only = true
	root.add_child(smoke)
	smoke.position = Vector3(0, 1.6, -15)
	smoke.set_physics_process(false)
	for config in LAYOUTS:
		await layout(config)
		if is_instance_valid(smoke): smoke.hide()
		await image_at(out.path_join(config.id + "-arena.png"))
		if not smoke._detonated:
			smoke._detonate()
			smoke.set_replica_lifetime(10.0)
		smoke.show()
		await image_at(out.path_join(config.id + "-smoke.png"))
		for back in ["white", "gray"]:
			var flat := ColorRect.new()
			flat.size = config.size
			flat.color = Color.WHITE if back == "white" else Color(0.5, 0.5, 0.5)
			root.add_child(flat)
			await image_at(out.path_join(config.id + "-" + back + ".png"))
			flat.queue_free()
			await settle()
		records.append({"layout": config.id, "size": [config.size.x, config.size.y], "camera": [0, 1.65, -18], "look_at": [0, 1.5, 8], "smoke_position": [0, 1.6, -15], "smoke_remaining": 10.0})
	smoke.queue_free()
	camera.queue_free()
	arena.queue_free()
	await settle()

func setup_touch(touch, config: Dictionary, held: bool) -> void:
	touch.enabled = true
	touch.size = config.size
	touch.safe_rect = Rect2(config.inset, 0, config.size.x - config.inset * 2, config.size.y)
	touch.hud_scale = config.scale
	touch.counts = {"grenade": 0, "smoke": 1}
	if held:
		touch.actions = {"fire": true, "reload": true, "interact": true}
		touch.fingers = {0: "move"}
		touch.move_origin = touch.control_point("move")
		touch.movement = Vector2(0.65, 0.45)
	touch.queue_redraw()

func controls(out: String, background_dir: String) -> void:
	var back := TextureRect.new()
	back.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	root.add_child(back)
	for config in LAYOUTS:
		await layout(config)
		back.size = config.size
		for background in ["white", "gray", "arena", "smoke"]:
			var background_path: String = background_dir.path_join(config.id + "-" + background + ".png")
			var bg := Image.load_from_file(background_path)
			assert(bg != null and bg.get_size() == config.size, "missing native frozen background")
			back.texture = ImageTexture.create_from_image(bg)
			for held in [false, true]:
				var scene_id: String = config.id + "-" + background + ("-held" if held else "-idle")
				var folder := out.path_join(scene_id)
				DirAccess.make_dir_recursive_absolute(folder)
				var original = OriginalTouch.new()
				root.add_child(original)
				await settle()
				setup_touch(original, config, held)
				await image_at(folder.path_join("original.png"))
				original.queue_free()
				await settle()
				var probe = ProbeTouch.new()
				root.add_child(probe)
				await settle()
				setup_touch(probe, config, held)
				await image_at(folder.path_join("normal.png"))
				var geometry: Dictionary = {}
				for key in probe.positions:
					var point: Vector2 = probe.control_point(key)
					geometry[key] = {"point": [point.x, point.y], "radius": probe.radius(key)}
				for group in GROUPS:
					if group == "held_border" and not held: continue
					probe.probe_group = group
					for pass_name in ["underlay", "black", "white", "footprint"]:
						back.modulate = Color.BLACK if pass_name == "footprint" else Color.WHITE
						probe.probe_pass = pass_name
						probe.queue_redraw()
						await image_at(folder.path_join(group + "-" + pass_name + ".png"))
				back.modulate = Color.WHITE
				var scene_images: Dictionary = {}
				for path in written_images:
					if path.get_base_dir() == folder: scene_images[path.get_file()] = written_images[path]
				var record := {"id": scene_id, "layout": config.id, "size": [config.size.x, config.size.y], "scale": config.scale, "inset": config.inset, "held": held, "counts": {"grenade": 0, "smoke": 1}, "movement": [0.65, 0.45] if held else [0.0, 0.0], "actions": ["fire", "reload", "interact"] if held else [], "geometry": geometry, "alphas": probe.probe_alphas.duplicate(), "background": background_path, "background_sha256": FileAccess.get_sha256(background_path), "images": scene_images}
				records.append(record)
				var file := FileAccess.open(folder.path_join("scene.json"), FileAccess.WRITE)
				file.store_string(JSON.stringify(record, "\t"))
				file.close()
				probe.queue_free()
				await settle()
	back.queue_free()
	await settle()

func verify_source() -> Dictionary:
	var source_root := ProjectSettings.globalize_path("res://").path_join("..").simplify_path()
	var file := FileAccess.open(source_root.path_join("SOURCE.json"), FileAccess.READ)
	var receipt: Dictionary = JSON.parse_string(file.get_as_text())
	file.close()
	for entry in receipt.files + receipt.fixture:
		assert(FileAccess.get_sha256(source_root.path_join(entry.path)) == entry.sha256, "source/UID changed: " + entry.path)
	assert(FileAccess.get_sha256("res://tests/touch_contrast_instrumented.gd") == receipt.instrumented_sha256, "instrumented source changed")
	assert(FileAccess.get_sha256("res://tests/touch_contrast_instrumented.gd.uid") == receipt.instrumented_uid_sha256, "instrumented UID changed")
	return receipt

func run() -> void:
	var source_receipt := verify_source()
	var out: String = options.get("out", "")
	assert(not out.is_empty(), "--out is required")
	DirAccess.make_dir_recursive_absolute(out)
	if options.get("mode", "") == "backgrounds": await backgrounds(out)
	elif options.get("mode", "") == "controls": await controls(out, options.get("background-dir", ""))
	else: assert(false, "--mode must be backgrounds or controls")
	var file := FileAccess.open(out.path_join("capture.json"), FileAccess.WRITE)
	var source_path := ProjectSettings.globalize_path("res://").path_join("../SOURCE.json").simplify_path()
	assert(verify_source() == source_receipt, "source receipt changed during capture")
	var background_manifest: String = options.get("background-dir", "").path_join("capture.json")
	file.store_string(JSON.stringify({"engine": Engine.get_version_info(), "renderer": RenderingServer.get_video_adapter_name(), "mode": options.get("mode"), "source": source_receipt.source, "source_verified_before_after": true, "source_manifest_sha256": FileAccess.get_sha256(source_path), "background_manifest_sha256": FileAccess.get_sha256(background_manifest) if options.get("mode") == "controls" else "", "images": written_images, "records": records}, "\t"))
	file.close()
	print("TOUCH_CONTRAST_CAPTURE records=", records.size())
	quit(0)
