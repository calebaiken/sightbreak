extends SceneTree
## Area-weighted statistics of the baked albedo and ORM under each named paint part of the Relay AR (headless; no rendering): what
## the first-person shader is actually fed. Presentation only.
const Actor = preload("res://scripts/gameplay/actor.gd")

func _initialize() -> void:
	_run.call_deferred()

func _sample(image: Image, uv: Vector2) -> Color:
	var x := clampi(int(fposmod(uv.x, 1.0) * image.get_width()), 0, image.get_width() - 1)
	var y := clampi(int(fposmod(uv.y, 1.0) * image.get_height()), 0, image.get_height() - 1)
	return image.get_pixel(x, y)

func _run() -> void:
	var albedo: Image = (load(SBWeaponModel.RELAY_AR_ALBEDO) as Texture2D).get_image()
	var orm: Image = (load(SBWeaponModel.RELAY_AR_ORM) as Texture2D).get_image()
	albedo.decompress() if albedo.is_compressed() else null
	orm.decompress() if orm.is_compressed() else null
	var model := SBWeaponModel.new()
	var scene := SBWeaponModel._pack("rifle", true).instantiate()
	for name in ["paint_receiver", "paint_handguard", "body"]:
		var node := scene.find_child(name, true, false) as MeshInstance3D
		if node == null:
			print("TEXEL missing ", name)
			continue
		var mesh := node.mesh
		var rows := []
		var total := 0.0
		for surface in mesh.get_surface_count():
			var arrays := mesh.surface_get_arrays(surface)
			var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			var uvs: PackedVector2Array = arrays[Mesh.ARRAY_TEX_UV]
			var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
			if indices.is_empty():
				indices = PackedInt32Array(range(vertices.size()))
			for t in range(0, indices.size(), 3):
				var a := indices[t]
				var b := indices[t + 1]
				var c := indices[t + 2]
				var area := (vertices[b] - vertices[a]).cross(vertices[c] - vertices[a]).length() * 0.5
				var uv := (uvs[a] + uvs[b] + uvs[c]) / 3.0
				var al := _sample(albedo, uv)
				var o := _sample(orm, uv)
				rows.append([area, al.r, al.g, al.b, o.r, o.g, o.b])
				total += area
		# area-weighted percentiles
		var out := "TEXEL %s tris=%d area=%.4f" % [name, rows.size(), total]
		for column in 6:
			var sorted := rows.duplicate()
			sorted.sort_custom(func(p, q): return p[column + 1] < q[column + 1])
			var acc := 0.0
			var marks := [0.1, 0.5, 0.9]
			var values := []
			for row in sorted:
				acc += row[0]
				while not marks.is_empty() and acc >= marks[0] * total:
					values.append(row[column + 1])
					marks.pop_front()
			out += " | %s p10/50/90 = %.3f %.3f %.3f" % [["albR", "albG", "albB", "AO", "rough", "metal"][column], values[0], values[1], values[2] if values.size() > 2 else values[1]]
		print(out)
	quit()
