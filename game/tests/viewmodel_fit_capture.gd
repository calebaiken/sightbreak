extends SceneTree
## One first-person frame of a weapon with the viewmodel placement overridden from the command line, for fitting a new
## authored model: --weapon=sidearm|smg --scale=1.3 --offset=x,y,z --rotation=x,y,z (radians) --view=sunlit|backlit|shade
## --out=<png path>. Presentation only.
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const WeaponModel = preload("res://scripts/gameplay/weapon_model.gd")
const VIEWS := {
	"backlit": [Vector3(0, 0.05, -19), PI - 0.08],
	"sunlit": [Vector3(3, 0.05, -12), 0.35],
	"shade": [Vector3(0, 0.05, 20.5), 0.1],
}

func _initialize() -> void:
	_run.call_deferred()

func _vec(text: String) -> Vector3:
	var p := text.split(",")
	return Vector3(float(p[0]), float(p[1]), float(p[2]))

func _run() -> void:
	var weapon := "sidearm"
	var view := "sunlit"
	var out := "res://../builds/qa/viewmodel-fit.png"
	var fire := false
	# The placement the command line overrides is the weapon's own (sidearm: the Kestrel 9, smg: the Vectorline); it is
	# written to the model's statics once the weapon is known.
	var placement := {"scale": -1.0, "offset": Vector3.INF, "rotation": Vector3.INF}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--weapon="): weapon = argument.trim_prefix("--weapon=")
		elif argument.begins_with("--view="): view = argument.trim_prefix("--view=")
		elif argument.begins_with("--out="): out = argument.trim_prefix("--out=")
		elif argument.begins_with("--scale="): placement.scale = float(argument.trim_prefix("--scale="))
		elif argument.begins_with("--offset="): placement.offset = _vec(argument.trim_prefix("--offset="))
		elif argument.begins_with("--rotation="): placement.rotation = _vec(argument.trim_prefix("--rotation="))
		elif argument == "--fire": fire = true
	if weapon == "smg":
		if placement.scale > 0.0: WeaponModel.vectorline_scale = placement.scale
		if placement.offset != Vector3.INF: WeaponModel.vectorline_offset = placement.offset
		if placement.rotation != Vector3.INF: WeaponModel.vectorline_rotation = placement.rotation
	else:
		if placement.scale > 0.0: WeaponModel.kestrel_9_scale = placement.scale
		if placement.offset != Vector3.INF: WeaponModel.kestrel_9_offset = placement.offset
		if placement.rotation != Vector3.INF: WeaponModel.kestrel_9_rotation = placement.rotation
	root.content_scale_size = Vector2i(1280, 720)
	root.size = Vector2i(1280, 720)
	var world := Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	var actor := Actor.new()
	actor.configure(1, 0, "Fit fixture", true)
	world.add_child(actor)
	actor.reset_for_round(VIEWS[view][0])
	actor.credits = 20000
	actor.apply_cosmetic({})
	if weapon != "sidearm":
		actor.buy_weapon(weapon)
	else:
		actor._equip("sidearm")
	actor._equip_blend = 0
	actor._kick = 0
	actor._flash = 0
	actor.global_position = VIEWS[view][0]
	actor.yaw = VIEWS[view][1]
	actor.rotation.y = VIEWS[view][1]
	actor.camera.rotation.x = -0.025
	for _i in 30:
		actor.tick_visual(1.0 / 60.0)
	if fire:
		actor.play_shot_effect()
		actor.tick_visual(0.016)
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(out)
	print("FIT_CAPTURE ", out)
	world.queue_free()
	await process_frame
	quit()
