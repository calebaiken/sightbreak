extends SceneTree
## Isolated native math primitives. No game, scenes, autoloads or LOS queries.
const PREFIX := "FOV_MATH "
const MAX_CASES := 1024
const INPUT_CODEC := "ieee754-binary64-little-endian-v1"
const CANONICAL_SHA := "d3e3cbc53b89cd0f872d333262524e43a84155c2b8ae0aaab06850e1337dcbae"
const INPUT_SCALARS := ["yaw", "threshold", "vision_range", "elapsed", "damaged_at", "enemy_id", "attacker_id"]
const INPUT_VECTORS := ["actor_position", "enemy_position"]

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

func valid_hex(value: Variant, count: int) -> bool:
	if not value is String or value.length() != count: return false
	var text: String = value
	for index in range(count):
		var character := text.unicode_at(index)
		if not ((character >= 48 and character <= 57) or (character >= 97 and character <= 102)): return false
	return true

func decode_binary64(value: Variant) -> Variant:
	# Reject before APIs that would print an engine error on malformed input.
	if not valid_hex(value, 16): return null
	var bytes: PackedByteArray = value.hex_decode()
	if bytes.size() != 8: return null
	var decoded: float = bytes.decode_double(0)
	if not is_finite(decoded) or bits64(decoded) != value: return null
	return decoded

func decode_inputs(encoded: Variant) -> Variant:
	if not encoded is Dictionary or encoded.size() != INPUT_SCALARS.size() + INPUT_VECTORS.size(): return null
	var decoded := {}
	for name in INPUT_SCALARS:
		var scalar: Variant = decode_binary64(encoded.get(name))
		if typeof(scalar) != TYPE_FLOAT: return null
		decoded[name] = scalar
	for name in INPUT_VECTORS:
		var vector: Variant = encoded.get(name)
		if not vector is Array or vector.size() != 3: return null
		var values := []
		for component in vector:
			var component_value: Variant = decode_binary64(component)
			if typeof(component_value) != TYPE_FLOAT or abs(component_value) > 1000000.0: return null
			values.append(component_value)
		decoded[name] = values
	if abs(decoded["yaw"]) > 100.0 or decoded["threshold"] < -1.0 or decoded["threshold"] > 1.0: return null
	if decoded["vision_range"] <= 0.0 or decoded["vision_range"] > 1000.0: return null
	if abs(decoded["elapsed"]) > 1000000.0 or abs(decoded["damaged_at"]) > 1000000.0: return null
	if decoded["enemy_id"] < 1.0 or decoded["enemy_id"] > 10.0 or decoded["attacker_id"] < 0.0 or decoded["attacker_id"] > 10.0: return null
	if decoded["enemy_id"] != floor(decoded["enemy_id"]) or decoded["attacker_id"] != floor(decoded["attacker_id"]): return null
	return decoded

func input_bits(decoded: Dictionary) -> Dictionary:
	var result := {}
	for name in INPUT_SCALARS: result[name] = bits64(decoded[name])
	for name in INPUT_VECTORS:
		result[name] = [bits64(decoded[name][0]), bits64(decoded[name][1]), bits64(decoded[name][2])]
	return result

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
	if not parsed is Dictionary or parsed.size() != 7 or parsed.get("schema") != 2 or not parsed.get("cases") is Array:
		fail("Input schema")
		return
	var payload: Dictionary = parsed
	for key in ["schema", "engine", "source_fixture_sha256", "seed", "cases", "input_codec", "canonical_cases_sha256"]:
		if not payload.has(key):
			fail("Input schema key")
			return
	if payload["input_codec"] != INPUT_CODEC or payload["canonical_cases_sha256"] != CANONICAL_SHA or payload["engine"] != "4.7.2.stable.official.ed1daf0bf" or not valid_hex(payload["source_fixture_sha256"], 64) or not finite_number(payload["seed"]):
		fail("Input identity")
		return
	var cases: Array = payload["cases"]
	if cases.size() != 588 or cases.size() > MAX_CASES:
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
	emit({"kind": "header", "schema": 2, "engine": Engine.get_version_info(),
		"cases_sha256": actual_sha, "program_sha256": FileAccess.get_sha256(get_script().resource_path),
		"precision": precision, "input_codec": INPUT_CODEC, "canonical_cases_sha256": CANONICAL_SHA})
	var ids := {}
	var ordinal := 0
	for raw_case in cases:
		if not raw_case is Dictionary:
			fail("Case is not an object")
			return
		var entry: Dictionary = raw_case
		var keys := ["id", "group", "actor_position", "enemy_position", "yaw", "threshold", "vision_range", "elapsed", "damaged_at", "enemy_id", "attacker_id", "meta", "input_sha256", "ordinal", "input64_le", "transport_sha256"]
		if entry.size() != keys.size():
			fail("Case schema")
			return
		for key in keys:
			if not entry.has(key):
				fail("Case schema key")
				return
		if not finite_number(entry["ordinal"]) or entry["ordinal"] != ordinal or not valid_hex(entry["input_sha256"], 64) or not valid_hex(entry["transport_sha256"], 64) or not entry["group"] is String or not entry["meta"] is Dictionary:
			fail("Case order/metadata")
			return
		if not entry.get("id") is String or ids.has(entry["id"]) or not finite_vector(entry.get("actor_position")) or not finite_vector(entry.get("enemy_position")):
			fail("Case identity/vector")
			return
		ids[entry["id"]] = true
		for name in ["yaw", "threshold", "vision_range", "elapsed", "damaged_at", "enemy_id", "attacker_id"]:
			if not finite_number(entry.get(name)):
				fail("Case scalar")
				return
		var exact: Variant = decode_inputs(entry["input64_le"])
		if not exact is Dictionary:
			fail("Exact binary input")
			return
		# Decimal entry values above are presentation only. Every operative value
		# comes from PackedByteArray.decode_double, never JSON decimal conversion.
		var actor := vector_from(exact["actor_position"])
		var enemy := vector_from(exact["enemy_position"])
		var yaw: float = exact["yaw"]
		var threshold: float = exact["threshold"]
		var vision_range: float = exact["vision_range"]
		var elapsed: float = exact["elapsed"]
		var damaged_at: float = exact["damaged_at"]
		var age: float = elapsed - damaged_at
		var facing := Vector3(-sin(yaw), 0.0, -cos(yaw))
		var delta := enemy - actor
		var toward := delta.normalized()
		var dot: float = facing.dot(toward)
		var distance: float = actor.distance_to(enemy)
		var geometric: bool = dot > threshold
		var specific: bool = exact["enemy_id"] == exact["attacker_id"]
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
			"values": values, "bits64": binary, "predicates": predicates, "ordinal": ordinal,
			"transport_sha256": entry["transport_sha256"], "decoded_input64_le": input_bits(exact)})
		ordinal += 1
	emit({"kind": "done", "count": cases.size(), "cases_sha256": actual_sha})
	quit(0)
