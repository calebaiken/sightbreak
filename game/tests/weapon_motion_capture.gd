extends SceneTree
## Frame sequence of the first-person rifle in motion: a held-trigger burst, then a
## reload, driven through the actor's own authority and visual ticks (the same calls
## the match makes) at a fixed 60 Hz simulation step, one captured frame per two steps
## (30 fps of simulated time). Fixture input, not a played match; it asserts nothing
## about visual quality or frame rate. Run with --fixed-fps 30 so every other node also
## advances 1/30 s per captured frame. Needs a native display.
## --capture-dir=<dir> output folder (frames are NNN.png plus frames.csv);
## --view=sunlit|backlit|shade picks the fixture view (default sunlit);
## --size=WxH sets the viewport (default 1280x720); --shots=N trigger ticks (default 40).
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const STEP := 1.0 / 60.0
const VIEWS := {
	"sunlit": [Vector3(3, 0.05, -12), 0.35],
	"backlit": [Vector3(0, 0.05, -19), PI - 0.08],
	"shade": [Vector3(0, 0.05, 20.5), 0.1],
}
var output := "res://../builds/qa/weapon-motion"
var view := "sunlit"
var trigger_ticks := 40
var actor: SBActor
var frame := 0
var rows: PackedStringArray = ["frame,time_s,phase,ammo,reload_remaining_s,clip_time_s,magazine_y_m,kick"]

func _initialize() -> void:
	_run.call_deferred()

func _step(input: Dictionary) -> void:
	for i in 2:
		actor.input_state = input.merged({"look": Vector2(actor.yaw, actor.pitch)})
		actor.tick_authority(STEP)
		# A reload request is a single press.
		input.erase("reload")
	actor.tick_visual(STEP * 2.0)
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	if image.save_png(output.path_join("%03d.png" % frame)) != OK:
		push_error("Capture failed: frame %d" % frame)
	var magazine_y: float = actor._magazine.position.y if actor._magazine != null else 0.0
	rows.append("%d,%.4f,%s,%d,%.4f,%.4f,%.4f,%.4f" % [frame, frame * STEP * 2.0, input.get("phase", ""), actor.ammo, actor.reload_remaining, actor._arms_time, magazine_y, actor._kick])
	frame += 1

func _run() -> void:
	var size := Vector2i(1280, 720)
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture-dir="):
			output = argument.trim_prefix("--capture-dir=")
		elif argument.begins_with("--view="):
			view = argument.trim_prefix("--view=")
		elif argument.begins_with("--shots="):
			trigger_ticks = maxi(2, int(argument.trim_prefix("--shots=")))
		elif argument.begins_with("--size="):
			var parts := argument.trim_prefix("--size=").split("x")
			if parts.size() == 2:
				size = Vector2i(int(parts[0]), int(parts[1]))
	root.content_scale_size = size
	root.size = size
	DirAccess.make_dir_recursive_absolute(output)
	var world := Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	actor = Actor.new()
	actor.configure(1, 0, "Motion fixture", true)
	world.add_child(actor)
	var place: Array = VIEWS.get(view, VIEWS["sunlit"])
	actor.reset_for_round(place[0])
	actor.credits = 5000
	actor.buy_weapon("rifle")
	actor.apply_cosmetic({})
	actor.yaw = place[1]
	actor.rotation.y = place[1]
	actor.pitch = -0.025
	# Settle the deploy and the landing before recording.
	for i in 90:
		actor.input_state = {"look": Vector2(actor.yaw, actor.pitch)}
		actor.tick_authority(STEP)
		actor.tick_visual(STEP)
	await process_frame
	for i in 6:
		await _step({"phase": "ready"})
	for i in trigger_ticks / 2:
		await _step({"phase": "fire", "fire": true})
	for i in 10:
		await _step({"phase": "recover"})
	await _step({"phase": "reload", "reload": true})
	while actor.reload_remaining > 0:
		await _step({"phase": "reload"})
	for i in 10:
		await _step({"phase": "settle"})
	var file := FileAccess.open(output.path_join("frames.csv"), FileAccess.WRITE)
	file.store_string("\n".join(rows) + "\n")
	file.close()
	print("WEAPON MOTION: %d frames at %dx%d, view %s, %s" % [frame, size.x, size.y, view, output])
	quit()
