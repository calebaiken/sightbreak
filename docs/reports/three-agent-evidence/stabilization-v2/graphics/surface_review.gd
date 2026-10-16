extends SceneTree
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const Inspector = preload("res://scripts/ui/item_inspector.gd")
var output := "/workspace/reviews/stabilization-v2-20261016/graphics/surface-review"
var world: Node3D
var actor: SBActor
var report := {"source":"5357329fa06136ac0d81b58ace97f872f37bebfa", "cases":[]}
func _initialize() -> void: run.call_deferred()
func shot(label: String, extra: Dictionary = {}) -> void:
	for i in 4: await process_frame
	await RenderingServer.frame_post_draw
	var image := root.get_texture().get_image()
	image.save_png(output.path_join(label+".png"))
	var row := {"label":label,"dimensions":image.get_size(),"metadata":extra}
	report.cases.append(row)
	print("INDEPENDENT_SURFACE_CAPTURE "+JSON.stringify(row))
func pose(progress: float) -> void:
	actor.reload_remaining = 0
	actor.tick_visual(1.0/60.0)
	actor._equip_blend = 0
	actor._kick = 0
	if progress >= 0:
		actor.reload_remaining = 2.25 * (1-progress)
	actor.tick_visual(1.0/60.0)
func audit() -> Dictionary:
	var r := actor._gun.get_node("paint_receiver").material_override as ShaderMaterial
	var h := actor._gun.get_node("paint_handguard").material_override as ShaderMaterial
	return {"same_material":r==h,"receiver_rough_floor":r.get_shader_parameter("viewmodel_roughness"),"handguard_rough_floor":h.get_shader_parameter("viewmodel_roughness"),"receiver_metal_scale":r.get_shader_parameter("viewmodel_metal_scale"),"handguard_metal_scale":h.get_shader_parameter("viewmodel_metal_scale"),"ambient_disabled":r.shader.code.contains("ambient_light_disabled"),"ammo":actor.ammo,"reserve":actor.reserve}
func run() -> void:
	root.content_scale_size=Vector2i(1280,720)
	root.size=Vector2i(1280,720)
	DirAccess.make_dir_recursive_absolute(output)
	world=Node3D.new();root.add_child(world);world.add_child(Arena.new())
	actor=Actor.new();actor.configure(1,0,"Independent cosmetic fixture",true);world.add_child(actor)
	actor.reset_for_round(Vector3(3,0.05,-12));actor.credits=5000;actor.buy_weapon("rifle")
	actor.yaw=0.35;actor.rotation.y=0.35;actor.camera.rotation.x=-0.025
	var finishes=[{}, {"kind":"weapon_skin","collection":"Obsidian","rarity":"Rare","pattern_seed":7,"wear":0.1},{"kind":"weapon_skin","collection":"Crimson Archive","rarity":"Legendary","pattern_seed":897,"wear":0.05},{"kind":"weapon_skin","collection":"Spectral Circuit","rarity":"Epic","pattern_seed":315,"wear":0.45},{"kind":"weapon_skin","collection":"Blacksite","rarity":"Mythic","pattern_seed":12,"wear":0.8}]
	for f in finishes:
		actor.apply_cosmetic(f)
		var name:=str(f.get("collection","default")).to_snake_case()
		pose(-1);await shot(name+"-ready",audit())
		pose(0.67);await shot(name+"-insert",audit())
		pose(0.88);await shot(name+"-return",audit())
	# Real remote-actor proxy: regular world material rather than first-person studio.
	actor.queue_free();await process_frame;await process_frame
	var remote:=Actor.new();remote.configure(2,1,"Remote operator",false);world.add_child(remote);remote.reset_for_round(Vector3(3,0.05,-12))
	var cam:=Camera3D.new();world.add_child(cam);cam.position=remote.position+Vector3(1.0,1.5,-2.0);cam.current=true;cam.look_at(remote.position+Vector3(0,1.1,0))
	await shot("thirdperson-proxy-lit",{"scope":"actual remote actor proxy; does not display a detailed authored skin"})
	for n in world.find_children("*","DirectionalLight3D",true,false):n.light_energy=0
	for n in world.find_children("*","WorldEnvironment",true,false):n.environment.ambient_light_energy=0;n.environment.reflected_light_source=Environment.REFLECTION_SOURCE_DISABLED
	await shot("thirdperson-proxy-unlit",{"scope":"same remote world object with direct, ambient and sky reflection disabled"})
	world.queue_free();await process_frame;await process_frame
	var inspector:=Inspector.new();root.add_child(inspector);inspector.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);await process_frame
	for f in [finishes[1],finishes[2],finishes[3]]:
		inspector.show_item(f)
		await shot("inspection-"+str(f.collection).to_snake_case(),{"world_shader":not inspector.finish_material.shader.code.contains("ambient_light_disabled"),"first_person_projection":inspector.finish_material.shader.code.contains("POSITION")})
	inspector.queue_free();await process_frame;await process_frame
	FileAccess.open(output.path_join("results.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	await create_timer(0.2).timeout
	quit()
