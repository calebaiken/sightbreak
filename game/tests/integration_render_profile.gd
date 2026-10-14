extends SceneTree
## Fixed native diagnostic. UI data is a synthetic fixture, never a backend result.
## Wall frame time includes scheduling and software rasterization, not GPU timing.
var output := ""
var samples := 24
var rows: Array = []
var actor: SBActor
var animate := false
var animate_usec: Array[float] = []
var redraw := Callable()
const ITEM := {"name":"Relay AR / Crimson Archive", "kind":"weapon_skin", "collection":"Crimson Archive", "rarity":"Legendary", "pattern_seed":897, "wear":0.2}

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		if arg.begins_with("--samples="): samples = maxi(12,int(arg.trim_prefix("--samples=")))
	_run.call_deferred()

func _frame() -> void:
	if redraw.is_valid(): redraw.call()
	if animate and is_instance_valid(actor):
		var start := Time.get_ticks_usec()
		actor.tick_visual(1.0/60.0)
		animate_usec.append(Time.get_ticks_usec()-start)
	await process_frame
	await RenderingServer.frame_post_draw

func _measure(label: String, construction_ms: float) -> void:
	var first := Time.get_ticks_usec()
	await _frame()
	var first_ms := (Time.get_ticks_usec()-first)/1000.0
	for i in 8: await _frame()
	animate_usec.clear()
	var times: Array[float] = []
	for i in samples:
		var start := Time.get_ticks_usec()
		await _frame()
		times.append((Time.get_ticks_usec()-start)/1000.0)
	times.sort()
	animate_usec.sort()
	rows.append({"scenario":label,"construction_ms":construction_ms,"first_present_ms":first_ms,"samples":samples,"frame_p50_ms":times[times.size()/2],"frame_p95_ms":times[mini(times.size()-1,int(times.size()*0.95))],"visual_tick_p50_usec":animate_usec[animate_usec.size()/2] if not animate_usec.is_empty() else null,"draw_calls":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),"primitives":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME),"texture_bytes":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED),"buffer_bytes":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_BUFFER_MEM_USED),"static_bytes":Performance.get_monitor(Performance.MEMORY_STATIC),"node_count":Performance.get_monitor(Performance.OBJECT_NODE_COUNT)})
	if root.get_texture().get_image().save_png(output.path_join(label+".png")) != OK: push_error("Capture failed: "+label)

func _clear(node: Node) -> void:
	animate = false
	actor = null
	redraw = Callable()
	node.queue_free()
	for i in 5: await _frame()

func _run() -> void:
	if output.is_empty() or DisplayServer.get_name() == "headless":
		push_error("Native display and --output required")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(output)
	root.size = Vector2i(1280,720)
	root.content_scale_size = root.size
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	var start := Time.get_ticks_usec()
	var world := Node3D.new()
	root.add_child(world)
	world.add_child(load("res://scripts/gameplay/arena.gd").new())
	var camera := Camera3D.new()
	world.add_child(camera)
	camera.position = Vector3(3,1.67,-12)
	camera.rotation = Vector3(-0.025,0.35,0)
	camera.fov = 82
	camera.current = true
	await _measure("empty-yard",(Time.get_ticks_usec()-start)/1000.0)
	start = Time.get_ticks_usec()
	actor = SBActor.new()
	actor.configure(1,0,"Profile fixture",true)
	world.add_child(actor)
	actor.reset_for_round(Vector3(3,0.05,-12))
	actor.credits = 5000
	actor.buy_weapon("rifle")
	actor._equip_blend = 0
	actor.yaw = 0.35
	actor.rotation.y = 0.35
	actor.pitch = -0.025
	animate = true
	await _measure("authored-idle",(Time.get_ticks_usec()-start)/1000.0)
	actor.ammo -= 5
	actor.start_reload()
	# Progress the visual clip without advancing authority/ammunition in this cost fixture.
	actor.reload_remaining *= 0.5
	await _measure("reload-pose",0)
	actor.reload_remaining = 0
	start = Time.get_ticks_usec()
	for i in 6:
		var smoke := SBUtility.new()
		smoke.kind = "smoke"
		smoke.visual_only = true
		world.add_child(smoke)
		smoke.position = Vector3(3+(i%3-1)*3,0,-16-(i/3)*3)
		smoke._detonate()
		smoke.set_replica_lifetime(9)
		smoke.set_physics_process(false)
	await _measure("six-smoke-clouds",(Time.get_ticks_usec()-start)/1000.0)
	await _clear(world)
	start = Time.get_ticks_usec()
	var game := TacticalMatch.new()
	game.configure({"mode":"offline","name":"Bot profile fixture"})
	root.add_child(game)
	game.phase = "live"
	game.time_left = 100
	await _measure("live-ten-actor-bots",(Time.get_ticks_usec()-start)/1000.0)
	await _clear(game)
	start = Time.get_ticks_usec()
	var inspector = load("res://scripts/ui/item_inspector.gd").new()
	root.add_child(inspector)
	inspector.show_item(ITEM)
	redraw = func():
		inspector.pivot.rotation.y += 0.01
		inspector._request_render()
	await _measure("interactive-inspection",(Time.get_ticks_usec()-start)/1000.0)
	await _clear(inspector)
	start = Time.get_ticks_usec()
	var reveal = load("res://scripts/ui/case_reveal.gd").new()
	reveal.committed_item = ITEM.duplicate()
	root.add_child(reveal)
	reveal.progress = 0.8
	# Repeat opening progress to measure active reveal frames, not the idle cache
	# after the short real-time tween has ended on a slow software renderer.
	if reveal.tween: reveal.tween.kill()
	redraw = func(): reveal.progress = fmod(reveal.progress + 0.025,1.0)
	await _measure("case-reveal-fixture",(Time.get_ticks_usec()-start)/1000.0)
	await _clear(reveal)
	start = Time.get_ticks_usec()
	var economy = load("res://scripts/ui/economy_ui.gd").new()
	root.add_child(economy)
	# No network request: populate presentation only; no reward/ownership claim.
	economy.api.token = "synthetic-presentation-fixture"
	economy.account = {"display_name":"Profile fixture","credits":100,"level":1}
	for i in 20: economy.listings.append({"id":str(i),"seller_id":"fixture","price":i+1,"item":ITEM.duplicate()})
	economy.active_tab = "market"
	economy._render()
	await _measure("market-20-fixture-listings",(Time.get_ticks_usec()-start)/1000.0)
	await _clear(economy)
	var file := FileAccess.open(output.path_join("metrics.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify({"scope":"Native Linux software render diagnostic; no GPU/device/thermal/battery claim. Market/case data synthetic, no transactions.","renderer":RenderingServer.get_video_adapter_name(),"engine":Engine.get_version_info().string,"size":[1280,720],"rows":rows},"\t"))
	file.close()
	print("INTEGRATION_RENDER_PROFILE scenarios=",rows.size())
	quit()
