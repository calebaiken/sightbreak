extends SceneTree
const Actor = preload("res://scripts/gameplay/actor.gd")
func _initialize() -> void: run.call_deferred()
func run() -> void:
	var actor := Actor.new()
	actor.configure(1,0,"Replicated reload clock",true)
	root.add_child(actor)
	actor.reset_for_round(Vector3.ZERO)
	actor.credits = 5000
	actor.buy_weapon("rifle")
	actor._equip_blend = 0
	var last := -1.0
	var changes := 0
	var unchanged := 0
	for tick in 120:
		# Match client receives server reload time each third60Hz tick.
		# Presentation ticks run every physics step, without authority countdown.
		if tick % 3 == 0: actor.reload_remaining = 2.25 - float(tick) / 60.0
		actor.tick_visual(1.0/60.0)
		if actor._arms_time != last: changes += 1
		else: unchanged += 1
		last = actor._arms_time
	print("REPLICATED_RELOAD_CLOCK visual_ticks=120 pose_time_changes=%d unchanged_ticks=%d source_interval_hz=20" % [changes,unchanged])
	actor.queue_free()
	await process_frame
	await create_timer(0.2).timeout
	quit()
