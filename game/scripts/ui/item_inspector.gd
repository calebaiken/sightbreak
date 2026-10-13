class_name ItemInspector
extends SubViewportContainer
## Original procedural display model. Its appearance derives from instance metadata.
var pivot: Node3D
var camera: Camera3D
var dragging := false
var distance := 3.5
var item: Dictionary = {}
var world: SubViewport

func _ready() -> void:
	custom_minimum_size = Vector2(250, 240)
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	stretch = true
	mouse_filter = Control.MOUSE_FILTER_STOP
	world = SubViewport.new()
	world.size = Vector2i(640, 360)
	world.own_world_3d = true
	world.render_target_update_mode = SubViewport.UPDATE_WHEN_VISIBLE
	add_child(world)
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_COLOR
	env.environment.background_color = Color("11161d")
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color("8896ae")
	env.environment.ambient_light_energy = 0.8
	world.add_child(env)
	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-38, -28, 0)
	light.light_energy = 1.9
	world.add_child(light)
	var fill := OmniLight3D.new()
	fill.position = Vector3(-2, 1, 2)
	fill.light_color = Color("c58e67")
	fill.light_energy = 3.0
	world.add_child(fill)
	camera = Camera3D.new()
	camera.position = Vector3(0, 0.35, distance)
	camera.fov = 40
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
	var rarity := str(item.get("rarity", "Common")).to_lower()
	var colors := {"common": Color("82909a"), "uncommon": Color("76a896"), "rare": Color("597eb9"), "epic": Color("8d69b7"), "legendary": Color("bba26e"), "mythic": Color("b6314c")}
	var paint: Color = colors.get(rarity, Color("9b293c"))
	var wear := clampf(float(item.get("wear", 0.1)), 0, 1)
	paint = paint.lerp(Color("747779"), wear * 0.55)
	var metal := Color("303840")
	var kind := str(item.get("kind", "skin"))
	if kind == "case":
		_box(Vector3(1.5, 0.9, 0.5), Vector3.ZERO, Color("222930"))
		_box(Vector3(1.55, 0.09, 0.52), Vector3(0, 0.12, 0), paint)
		_box(Vector3(0.35, 0.15, 0.07), Vector3(0, -0.05, 0.29), Color("bea36a"))
	elif kind == "key":
		_box(Vector3(1.0, 0.12, 0.12), Vector3(0.1, 0, 0), Color("bea36a"))
		_box(Vector3(0.4, 0.5, 0.15), Vector3(-0.5, 0, 0), paint)
		_box(Vector3(0.13, 0.22, 0.12), Vector3(0.48, -0.1, 0), Color("bea36a"))
	else:
		_box(Vector3(0.96, 0.26, 0.19), Vector3(0.03, 0.08, 0), paint)
		_box(Vector3(0.64, 0.18, 0.16), Vector3(0.74, 0.08, 0), metal)
		_box(Vector3(0.45, 0.065, 0.065), Vector3(1.18, 0.1, 0), Color("79818a"))
		_box(Vector3(0.43, 0.23, 0.16), Vector3(-0.66, 0.02, 0), metal)
		_box(Vector3(0.11, 0.34, 0.19), Vector3(-0.91, -0.04, 0), metal)
		_box(Vector3(0.15, 0.34, 0.14), Vector3(-0.22, -0.23, 0), metal, -0.24)
		_box(Vector3(0.23, 0.4, 0.15), Vector3(0.19, -0.22, 0), paint, 0.18)
		_box(Vector3(0.75, 0.04, 0.09), Vector3(0.1, 0.25, 0), Color("727b86"))
		_box(Vector3(0.15, 0.14, 0.07), Vector3(-0.14, 0.3, 0), metal)
		var seed_value := int(item.get("pattern_seed", 1))
		for i in 6:
			var stripe := Color("b59d69") if (seed_value + i) % 3 == 0 else paint.darkened(0.35)
			_box(Vector3(0.036, 0.22, 0.198), Vector3(-0.36 + i * 0.135, 0.08, 0), stripe, -0.2)

func _box(dimensions: Vector3, location: Vector3, color: Color, tilt := 0.0) -> void:
	var mesh := MeshInstance3D.new()
	var shape := BoxMesh.new()
	shape.size = dimensions
	mesh.mesh = shape
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.metallic = 0.65
	material.roughness = 0.38
	mesh.material_override = material
	mesh.position = location
	mesh.rotation.z = tilt
	pivot.add_child(mesh)

func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT:
			dragging = event.pressed
		elif event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_UP:
			zoom(-0.2)
		elif event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			zoom(0.2)
	if event is InputEventMouseMotion and dragging:
		_rotate_model(event.relative)
	if event is InputEventScreenDrag:
		_rotate_model(event.relative)
	accept_event()

func _rotate_model(delta: Vector2) -> void:
	pivot.rotation.y += delta.x * 0.009
	pivot.rotation.x = clampf(pivot.rotation.x + delta.y * 0.009, -1.0, 1.0)

func zoom(amount: float) -> void:
	distance = clampf(distance + amount, 2.3, 5.0)
	if camera:
		camera.position = Vector3(0, 0.35, distance)
		camera.look_at(Vector3.ZERO)
