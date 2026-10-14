extends SceneTree
## Pixel check that the cosmetic paint parts are actually drawn: renders a frame,
## hides the paint parts, renders again and counts the pixels that changed. Covers the
## inspection studio (skin and default finish), a procedural first-person weapon (world
## finish) and the authored first-person rifle (viewmodel finish). A shader that
## overrides the vertex position wrongly draws nothing, which a parameter check cannot
## see. Needs a native display (not part of the headless validate.sh).
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const INSPECTOR = preload("res://scripts/ui/item_inspector.gd")
const SKIN := {"kind": "weapon_skin", "collection": "Crimson Archive", "rarity": "Legendary", "pattern_seed": 897, "wear": 0.2}
## Changed pixels required at 1280x720; the measured values are several times larger.
const MINIMUM := {"inspection skin": 20000, "inspection default": 20000, "first-person sidearm": 1500, "first-person rifle": 8000}
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	_run.call_deferred()

func check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

func _frame() -> Image:
	for i in 3:
		await process_frame
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image()

func _changed(a: Image, b: Image) -> int:
	var count := 0
	for y in range(0, a.get_height(), 2):
		for x in range(0, a.get_width(), 2):
			var p := a.get_pixel(x, y)
			var q := b.get_pixel(x, y)
			if absf(p.r - q.r) + absf(p.g - q.g) + absf(p.b - q.b) > 0.06:
				count += 4
	return count

func _measure(label: String, parts: Array, redraw: Callable) -> void:
	redraw.call()
	var shown := await _frame()
	for part: Node3D in parts:
		part.visible = false
	redraw.call()
	var hidden := await _frame()
	for part: Node3D in parts:
		part.visible = true
	var changed := _changed(shown, hidden)
	print("PAINT_VISIBILITY %s parts=%d changed_pixels=%d" % [label, parts.size(), changed])
	check(parts.size() > 0 and changed >= int(MINIMUM[label]), "%s: paint parts change %d pixels (need %d)" % [label, changed, MINIMUM[label]])

func _paint_of(node: Node, material: Material) -> Array:
	return node.find_children("*", "MeshInstance3D", true, false).filter(func(m): return m.material_override == material)

func _run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("A native rendering display is required")
		quit(2)
		return
	root.content_scale_size = Vector2i(1280, 720)
	root.size = Vector2i(1280, 720)
	var inspector := INSPECTOR.new()
	inspector.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(inspector)
	await process_frame
	for label in ["inspection skin", "inspection default"]:
		var item: Dictionary = SKIN.merged({"name": "Relay AR"}) if label == "inspection skin" else {"kind": "weapon_skin", "name": "Relay AR"}
		inspector.show_item(item)
		await process_frame
		await _measure(label, _paint_of(inspector, inspector.finish_material), inspector._request_render)
	inspector.queue_free()
	await process_frame
	var world := Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	var actor := Actor.new()
	actor.configure(1, 0, "Paint fixture", true)
	world.add_child(actor)
	actor.reset_for_round(Vector3(3, 0.05, -12))
	actor.yaw = 0.35
	actor.rotation.y = 0.35
	actor._equip_blend = 0
	actor.apply_cosmetic(SKIN)
	actor.tick_visual(0.016)
	await _measure("first-person sidearm", actor._paint_parts, func(): pass)
	actor.credits = 5000
	actor.buy_weapon("rifle")
	actor._equip_blend = 0
	actor.apply_cosmetic(SKIN)
	actor.tick_visual(0.016)
	await _measure("first-person rifle", actor._paint_parts, func(): pass)
	world.queue_free()
	await process_frame
	print("PAINT_VISIBILITY_TEST checks=%d failures=%d" % [checks, failures.size()])
	quit(0 if failures.is_empty() else 1)
