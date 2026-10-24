extends SceneTree
## Isolated native math primitives. No game, scenes, autoloads or LOS queries.
const PREFIX := "FOV_MATH "
const MAX_CASES := 1024

func bits64(value: float) -> String:
	var bytes := PackedByteArray()
	bytes.resize(8)
	bytes.encode_double(0, value)
	return bytes.hex_encode()

func bits32(value: float) -> String:
	var bytes := PackedByteArray()
	bytes.resize(4)
	bytes.encode_float(0, value)
	return bytes.hex_encode()

func vector_values(value: Vector3) -> Array:
	return [value.x, value.y, value.z]

func vector_from(value: Array) -> Vector3:
	return Vector3(float(value[0]), float(value[1]), float(value[2]))

func finite_number(value: Variant) -> bool:
	return (typeof(value) == TYPE_INT or typeof(value) == TYPE_FLOAT) and is_finite(float(value))

func finite_vector(value: Variant) -> bool:
	return value is Array and value.size() == 3 and finite_number(value[0]) and finite_number(value[1]) and finite_number(value[2])

func emit(value: Dictionary) -> void:
	print(PREFIX + JSON.stringify(value, "", true, true))

func fail(message: String) -> void:
	emit({"kind": "error", "message": message})
	quit(1)

func _initialize() -> void:
	var cases_path := ""
	var expected_sha := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--cases="): cases_path = arg.trim_prefix("--cases=")
		elif arg.begins_with("--expected-cases-sha256="): expected_sha = arg.trim_prefix("--expected-cases-sha256=")
		else:
			fail("Unexpected user argument")
			return
	if not cases_path.is_absolute_path() or expected_sha.length() != 64:
		fail("Absolute fixed cases and digest required")
		return
	var actual_sha := FileAccess.get_sha256(cases_path)
	if actual_sha != expected_sha:
		fail("Case payload digest mismatch")
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(cases_path))
	if not parsed is Dictionary or parsed.get("schema") != 1 or not parsed.get("cases") is Array:
		fail("Input schema")
		return
	var payload: Dictionary = parsed
	var cases: Array = payload["cases"]
	if cases.is_empty() or cases.size() > MAX_CASES:
		fail("Input count")
		return
	var scalar: float = 16777217.0
	var vector_scalar: float = Vector3(scalar, 0.0, 0.0).x
	var packed32: float = PackedFloat32Array([scalar])[0]
	var packed64: float = PackedFloat64Array([scalar])[0]
	var precision := {"single": OS.has_feature("single"), "double": OS.has_feature("double"),
		"scalar64": scalar, "vector_component": vector_scalar, "packed32": packed32, "packed64": packed64,
		"scalar64_le": bits64(scalar), "vector64_le": bits64(vector_scalar),
		"packed32_le": bits32(packed32), "packed64_le": bits64(packed64)}
	emit({"kind": "header", "schema": 1, "engine": Engine.get_version_info(),
		"cases_sha256": actual_sha, "program_sha256": FileAccess.get_sha256(get_script().resource_path),
		"precision": precision})
	var ids := {}
	for raw_case in cases:
		if not raw_case is Dictionary:
			fail("Case is not an object")
			return
		var entry: Dictionary = raw_case
		if not entry.get("id") is String or ids.has(entry["id"]) or not finite_vector(entry.get("actor_position")) or not finite_vector(entry.get("enemy_position")):
			fail("Case identity/vector")
			return
		ids[entry["id"]] = true
		for name in ["yaw", "threshold", "vision_range", "elapsed", "damaged_at", "enemy_id", "attacker_id"]:
			if not finite_number(entry.get(name)):
				fail("Case scalar")
				return
		var actor := vector_from(entry["actor_position"])
		var enemy := vector_from(entry["enemy_position"])
		var yaw: float = entry["yaw"]
		var threshold: float = entry["threshold"]
		var vision_range: float = entry["vision_range"]
		var elapsed: float = entry["elapsed"]
		var damaged_at: float = entry["damaged_at"]
		var age: float = elapsed - damaged_at
		var facing := Vector3(-sin(yaw), 0.0, -cos(yaw))
		var delta := enemy - actor
		var toward := delta.normalized()
		var dot: float = facing.dot(toward)
		var distance: float = actor.distance_to(enemy)
		var geometric: bool = dot > threshold
		var specific: bool = entry["enemy_id"] == entry["attacker_id"]
		var recent: bool = age < 1.2 and specific
		var in_fov: bool = geometric or recent
		var rejected_range: bool = distance > vision_range
		var values := {"actor_position": vector_values(actor), "enemy_position": vector_values(enemy),
			"yaw": yaw, "threshold": threshold, "vision_range": vision_range, "elapsed": elapsed,
			"damaged_at": damaged_at, "age": age, "facing": vector_values(facing), "delta": vector_values(delta),
			"toward": vector_values(toward), "distance": distance, "dot": dot}
		var binary := {}
		for key in values:
			if values[key] is Array:
				if not finite_vector(values[key]):
					fail("Nonfinite native vector")
					return
				binary[key] = [bits64(values[key][0]), bits64(values[key][1]), bits64(values[key][2])]
			else:
				if not finite_number(values[key]):
					fail("Nonfinite native scalar")
					return
				binary[key] = bits64(values[key])
		var predicates := {"range_reject": rejected_range, "geometric": geometric, "specific_attacker": specific,
			"recent_attacker": recent, "in_fov": in_fov,
			"stage": "range" if rejected_range else ("requires_visibility" if in_fov else "fov")}
		emit({"kind": "case", "id": entry["id"], "input_sha256": entry["input_sha256"],
			"values": values, "bits64": binary, "predicates": predicates})
	emit({"kind": "done", "count": cases.size(), "cases_sha256": actual_sha})
	quit(0)
