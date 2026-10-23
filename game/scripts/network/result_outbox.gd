class_name SBResultOutbox
extends RefCounted
## Server-only process-crash handoff. Python worker imports into SQLite FULL/WAL.
## flush+atomic rename protects completed handoffs against process termination;
## power-loss/storage guarantees require the worker's committed SQLite import.
const MAX_BYTES := 16384
const MAX_FILES := 512
static func stage(payload: Dictionary, directory: String) -> Dictionary:
	if not _allowed(payload):
		return {"ok": false, "error": "Unexpected result fields or types."}
	var id := str(payload.get("match_id", ""))
	var pattern := RegEx.new()
	pattern.compile("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
	if pattern.search(id) == null or not directory.is_absolute_path():
		return {"ok": false, "error": "Invalid server outbox identity or path."}
	var encoded := JSON.stringify(payload)
	if encoded.to_utf8_buffer().size() > MAX_BYTES:
		return {"ok": false, "error": "Result exceeds the outbox record limit."}
	if DirAccess.make_dir_recursive_absolute(directory) != OK:
		return {"ok": false, "error": "Cannot create the server result outbox."}
	var files := DirAccess.get_files_at(directory)
	for name: String in files:
		if name.begins_with(id + ".") and name.ends_with(".json"):
			return {"ok": true, "queued": true} if FileAccess.get_file_as_string(directory.path_join(name)) == encoded else {"ok": false, "error": "Match identity already has a different result."}
	if files.size() >= MAX_FILES:
		return {"ok": false, "error": "Result outbox is full; operator recovery required."}
	var stem := directory.path_join(id + "." + Crypto.new().generate_random_bytes(16).hex_encode())
	var temporary := stem + ".tmp"
	# Unique destinations preserve concurrent handoffs; SQLite arbitrates identity.
	var path := stem + ".json"
	var file := FileAccess.open(temporary, FileAccess.WRITE)
	if file == null:
		return {"ok": false, "error": "Cannot persist the match result."}
	file.store_string(encoded)
	file.flush()
	var error := file.get_error()
	file.close()
	if error != OK or DirAccess.rename_absolute(temporary, path) != OK:
		return {"ok": false, "error": "Match result handoff could not be completed."}
	return {"ok": true, "queued": true}

static func _allowed(payload: Dictionary) -> bool:
	var fields := ["match_id", "mode", "started_at", "ended_at", "participants"]
	if payload.size() != fields.size(): return false
	for key in fields:
		if not payload.has(key): return false
	for key in ["match_id", "mode", "started_at", "ended_at"]:
		if not payload[key] is String or payload[key].length() > 64: return false
	if payload.mode != "ranked_5v5" or not payload.participants is Array or payload.participants.size() != 10: return false
	var player_fields := ["player_id", "won", "active_seconds", "objective_contributions", "abandoned"]
	for player in payload.participants:
		if not player is Dictionary or player.size() != player_fields.size(): return false
		for key in player_fields:
			if not player.has(key): return false
		if not player.player_id is String or player.player_id.length() > 36: return false
		if not player.won is bool or not player.abandoned is bool: return false
		if not player.active_seconds is int or not player.objective_contributions is int: return false
	return true
