class_name ItemInspector
extends SubViewportContainer
## A bounded, sky-free studio displaying original native meshes and real metadata.
const FINISH = preload("res://scripts/ui/cosmetic_material.gd")
const DISPLAY = preload("res://scripts/ui/display_models.gd")
const WEAPONS = preload("res://scripts/gameplay/weapon_model.gd")
var finish_material: ShaderMaterial
var pivot: Node3D
var camera: Camera3D
var dragging := false
var touch_points: Dictionary = {}
var pinch_distance := 0.0
var distance := 3.5
var item: Dictionary = {}
var world: SubViewport
var rarity_light: OmniLight3D
var lid: Node3D
var reward: Node3D
var case_root: Node3D

func _ready() -> void:
	custom_minimum_size = Vector2(250, 240)
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	stretch = true
	# Only the selected item owns a viewport. Demand rendering allows crisp
	# studio detail; larger layouts scale to at most 1024 × 512 pixels.
	stretch_shrink = 1
	mouse_filter = Control.MOUSE_FILTER_STOP
	world = SubViewport.new()
	world.name = "ArmoryStudio"
	world.size = Vector2i(640, 360)
	world.msaa_3d = Viewport.MSAA_2X
	world.own_world_3d = true
	world.render_target_update_mode = SubViewport.UPDATE_ONCE
	add_child(world)
	resized.connect(_request_render)
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_COLOR
	env.environment.background_color = Color("10151b")
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color("97a3af")
	env.environment.ambient_light_energy = 0.85
	world.add_child(env)
	var key_light := DirectionalLight3D.new()
	key_light.rotation_degrees = Vector3(-42, -32, 0)
	key_light.light_color = Color("e3e9ed")
	key_light.light_energy = 2.0
	world.add_child(key_light)
	var fill := OmniLight3D.new()
	fill.position = Vector3(-2, 1, 2)
	fill.light_color = Color("c5af86")
	fill.light_energy = 4.3
	fill.omni_range = 5
	world.add_child(fill)
	rarity_light = OmniLight3D.new()
	rarity_light.position = Vector3(1.7, 1.2, -0.9)
	rarity_light.light_color = Color("8093aa")
	rarity_light.light_energy = 3.0
	rarity_light.omni_range = 4
	world.add_child(rarity_light)
	var stage := Node3D.new()
	world.add_child(stage)
	DISPLAY.cylinder(stage, 1.18, 0.045, Vector3(0, -0.84, 0), DISPLAY.metal(Color("27313a"), 0.65, 0.25))
	DISPLAY.cylinder(stage, 1.22, 0.018, Vector3(0, -0.87, 0), DISPLAY.metal(Color("9c844f"), 0.38, 0.65))
	camera = Camera3D.new()
	camera.position = Vector3(0, 0.35, distance)
	camera.fov = 32
	world.add_child(camera)
	camera.look_at(Vector3.ZERO)
	pivot = Node3D.new()
	pivot.rotation_degrees = Vector3(-8, -16, 0)
	world.add_child(pivot)
	show_item(item)

func show_item(value: Dictionary) -> void:
	item = value.duplicate(true)
	if not is_instance_valid(pivot):
		return
	for node in pivot.get_children():
		pivot.remove_child(node)
		node.queue_free()
	pivot.rotation_degrees = Vector3(-8, -16, 0)
	pivot.scale = Vector3.ONE
	finish_material = FINISH.finish(item)
	rarity_light.light_color = FINISH.rarity_color(str(item.get("rarity", "Common")))
	var kind := str(item.get("kind", "weapon_skin"))
	if kind == "case":
		lid = DISPLAY.build_case(pivot)
		pivot.rotation_degrees.x = 20
	elif kind == "key":
		var gold := DISPLAY.metal(Color("bea36a"))
		DISPLAY.box(pivot, Vector3(1.0, 0.12, 0.12), Vector3(0.1, 0, 0), gold)
		DISPLAY.box(pivot, Vector3(0.4, 0.5, 0.15), Vector3(-0.5, 0, 0), gold)
		DISPLAY.box(pivot, Vector3(0.13, 0.22, 0.12), Vector3(0.48, -0.1, 0), gold)
	elif kind == "knife_reference":
		DISPLAY.build_knife(pivot)
		pivot.scale = Vector3.ONE * 1.7
	else:
		_build_rifle(pivot)
	_request_render()

func _request_render() -> void:
	if is_instance_valid(world):
		stretch_shrink = maxi(1, ceili(maxf(size.x / 1024.0, size.y / 512.0)))
		world.render_target_update_mode = SubViewport.UPDATE_ONCE

func _build_rifle(parent: Node3D) -> Node3D:
	var rifle := Node3D.new()
	rifle.name = "CommittedRifle"
	parent.add_child(rifle)
	rifle.rotation.y = -PI * 0.5
	rifle.scale = Vector3.ONE * 3.4
	var model := Node3D.new()
	model.position = Vector3(0, 0.05, 0.3125)
	rifle.add_child(model)
	var pieces: Dictionary = WEAPONS.build(model, "rifle", false)
	FINISH.apply(finish_material, pieces.get("paint", []))
	return rifle

func prepare_reveal(value: Dictionary) -> void:
	show_item({"kind": "case"})
	item = value.duplicate(true)
	finish_material = FINISH.finish(item)
	case_root = Node3D.new()
	pivot.add_child(case_root)
	for child in pivot.get_children():
		if child != case_root:
			child.reparent(case_root)
	case_root.position.y = -0.20
	reward = _build_rifle(pivot)
	reward.visible = false
	pivot.rotation_degrees = Vector3(15, -16, 0)
	rarity_light.light_color = FINISH.rarity_color(str(value.get("rarity", "Common")))
	rarity_light.light_energy = 0

func set_reveal_progress(value: float) -> void:
	if not is_instance_valid(reward):
		return
	var opening := smoothstep(0.18, 0.65, value)
	lid.rotation.x = -opening * 1.65
	var lift := smoothstep(0.50, 1.0, value)
	reward.visible = lift > 0.01
	reward.position.y = lerpf(-0.20, 0.28, lift)
	reward.scale = Vector3.ONE * lerpf(1.35, 2.7, lift)
	reward.rotation.z = lerpf(-0.08, 0.0, lift)
	case_root.scale = Vector3.ONE * lerpf(1.0, 0.78, lift)
	case_root.position.y = lerpf(-0.20, -0.40, lift)
	rarity_light.light_energy = lift * 3.5
	_request_render()

func _gui_input(event: InputEvent) -> void:
	if (event is InputEventMouseButton or event is InputEventMouseMotion) and event.device == InputEvent.DEVICE_ID_EMULATION:
		accept_event()
		return
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT:
			dragging = event.pressed
		elif event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_UP:
			zoom(-0.2)
		elif event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			zoom(0.2)
	if event is InputEventMouseMotion and dragging:
		_rotate_model(event.relative)
	if event is InputEventScreenTouch:
		if event.pressed:
			touch_points[event.index] = event.position
		else:
			touch_points.erase(event.index)
		pinch_distance = _touch_distance()
	if event is InputEventScreenDrag:
		if touch_points.has(event.index):
			touch_points[event.index] = event.position
		if touch_points.size() >= 2:
			var next_distance := _touch_distance()
			if pinch_distance > 0:
				zoom((pinch_distance - next_distance) * 0.008)
			pinch_distance = next_distance
		else:
			_rotate_model(event.relative)
	accept_event()

func _touch_distance() -> float:
	if touch_points.size() < 2:
		return 0.0
	var points := touch_points.values()
	return Vector2(points[0]).distance_to(Vector2(points[1]))

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		touch_points.clear()
		pinch_distance = 0.0
		dragging = false

func _rotate_model(delta: Vector2) -> void:
	if not is_instance_valid(pivot):
		return
	pivot.rotation.y += delta.x * 0.009
	pivot.rotation.x = clampf(pivot.rotation.x + delta.y * 0.009, -1.0, 1.0)
	_request_render()

func zoom(amount: float) -> void:
	distance = clampf(distance + amount, 2.3, 5.0)
	if camera:
		camera.position = Vector3(0, 0.35, distance)
		camera.look_at(Vector3.ZERO)
	_request_render()

func reset_view() -> void:
	distance = 3.5
	zoom(0)
	if is_instance_valid(pivot):
		pivot.rotation_degrees = Vector3(-8, -16, 0)
