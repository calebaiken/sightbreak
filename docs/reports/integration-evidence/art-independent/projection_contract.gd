extends SceneTree
const Actor = preload("res://scripts/gameplay/actor.gd")
const Model = preload("res://scripts/gameplay/weapon_model.gd")
const Shading = preload("res://scripts/gameplay/viewmodel_shading.gd")
func _initialize() -> void: run.call_deferred()
func screen(at: Vector3, size: Vector2) -> Vector2:
	var scale := 1.0 / tan(deg_to_rad(Shading.FOV) * 0.5)
	return Vector2(size.x * 0.5 + at.x / -at.z * scale * size.y * 0.5, size.y * 0.5 - at.y / -at.z * scale * size.y * 0.5)
func run() -> void:
	var actor := Actor.new()
	actor.configure(1,0,"Projection independent",true)
	root.add_child(actor)
	actor.reset_for_round(Vector3.ZERO)
	actor.credits = 5000
	actor.buy_weapon("rifle")
	actor._equip_blend = 0
	actor.tick_visual(0.016)
	var pose: Basis = actor.camera.global_basis.inverse() * actor._gun.global_basis * Basis.from_euler(Model.relay_ar_rotation)
	var bore: Vector3 = pose * Vector3.FORWARD
	print("PROJECTION bore_vanishing_point_1280x720=%s camera_fov=%s viewmodel_fov=%s arms_scene_cached_after_build=%s" % [screen(bore, Vector2(1280,720)), actor.camera.fov, Shading.FOV, ResourceLoader.has_cached(Model.RELAY_AR_ARMS)])
	for aspect in [Vector2(1280,720),Vector2(1600,720),Vector2(1024,768)]:
		for progress in [0.0,0.14,0.15,0.30,0.45,0.60,0.75,0.84,0.90,1.0]:
			actor.reload_remaining = 2.25 * (1.0-progress) if progress > 0 and progress < 1 else 0
			actor.tick_visual(0.016)
			var wrist: Vector3 = actor._arms_skeleton.global_transform * actor._arms_skeleton.get_bone_global_pose(actor._arms_skeleton.find_bone("L_hand")).origin
			wrist = actor.camera.global_transform.affine_inverse() * wrist
			var box: AABB = actor._magazine.mesh.get_aabb()
			var top := INF
			var bottom := -INF
			for corner in 8:
				var at: Vector3 = actor.camera.global_transform.affine_inverse() * actor._magazine.global_transform * box.get_endpoint(corner)
				var projected := screen(at,aspect)
				top = minf(top,projected.y)
				bottom = maxf(bottom,projected.y)
			var actual_bottom := -INF
			var offscreen_vertices := 0
			var vertex_count := 0
			for surface in actor._magazine.mesh.get_surface_count():
				var vertices: PackedVector3Array = actor._magazine.mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]
				for vertex in vertices:
					var at: Vector3 = actor.camera.global_transform.affine_inverse() * actor._magazine.global_transform * vertex
					var point := screen(at,aspect)
					actual_bottom = maxf(actual_bottom,point.y)
					vertex_count += 1
					if point.x < 0 or point.x > aspect.x or point.y < 0 or point.y > aspect.y: offscreen_vertices += 1
			print("MAGAZINE_VERTEX aspect=%s progress=%.2f actual_bottom=%.2f outside_vertices=%d/%d" % [aspect,progress,actual_bottom,offscreen_vertices,vertex_count])
			print("PROJECTION aspect=%s progress=%.2f wrist_screen=%s wrist_distance=%.4f magazine_y_bounds=%.1f..%.1f" % [aspect,progress,screen(wrist,aspect),wrist.length(),top,bottom])
	actor.queue_free()
	await process_frame
	await create_timer(0.2).timeout
	quit()
