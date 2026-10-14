extends SceneTree
const Actor = preload("res://scripts/gameplay/actor.gd")
var failures: Array[String] = []
var checks := 0
func check(ok: bool, note: String) -> void:
	checks += 1
	if not ok: failures.append(note)
func _initialize() -> void: run.call_deferred()
func frame() -> Image:
	for i in 3: await process_frame
	await RenderingServer.frame_post_draw
	return root.get_texture().get_image()
func changed(a: Image, b: Image) -> int:
	var count := 0
	for y in range(0,a.get_height(),2):
		for x in range(0,a.get_width(),2):
			var p := a.get_pixel(x,y)
			var q := b.get_pixel(x,y)
			if absf(p.r-q.r)+absf(p.g-q.g)+absf(p.b-q.b)>0.06: count += 4
	return count
func run() -> void:
	root.size = Vector2i(1280,720)
	root.content_scale_size = root.size
	var world := Node3D.new()
	root.add_child(world)
	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-30,-20,0)
	world.add_child(light)
	var actor := Actor.new()
	actor.configure(1,0,"Independent depth projection",true)
	world.add_child(actor)
	actor.reset_for_round(Vector3.ZERO)
	actor.credits = 5000
	actor.buy_weapon("rifle")
	actor._equip_blend = 0
	actor.tick_visual(0.016)
	var wall := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = Vector3(10,10,0.005)
	wall.mesh = box
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color = Color(0.1,0.8,0.2)
	wall.material_override = material
	actor.camera.add_child(wall)
	var reference: Image
	for fov in [42.0,82.0,110.0]:
		actor.camera.fov = fov
		for depth in [0.3,0.1,0.055]:
			wall.position = Vector3(0,0,-depth)
			actor._gun.visible = false
			var hidden := await frame()
			actor._gun.visible = true
			var shown := await frame()
			var pixels := changed(hidden,shown)
			print("PROJECTION_RENDER world_fov=%.0f wall_depth=%.3f weapon_pixels=%d" % [fov,depth,pixels])
			check(pixels>40000, "first-person weapon remains visible at fov%s depth%s" % [fov,depth])
			if reference == null: reference = shown
			var difference := changed(reference,shown)
			print("PROJECTION_RENDER compared_to_first_frame changed_pixels=%d" % difference)
			check(difference < 4000, "separate projection stable across world FOV and wall depth")
	world.queue_free()
	await process_frame
	await create_timer(0.2).timeout
	print("PROJECTION_RENDER_TEST checks=%d failures=%s" % [checks,failures])
	quit(0 if failures.is_empty() else 1)
