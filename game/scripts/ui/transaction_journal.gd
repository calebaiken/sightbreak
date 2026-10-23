class_name TransactionJournal
extends RefCounted
## One outstanding keyed mutation. Authentication and offline balances never belong here.
## Flush + same-directory rename precede dispatch; this covers app-process termination.
const PATH := "user://pending_transaction.json"
const MAX_BYTES := 8192
var error := ""
## An OS-owned loopback listener serializes journal owners across processes. No peer
## is accepted and no protocol/data is exposed. Process exit releases the claim.
## A port collision fails closed; it never permits another writer. Godot 4.7.2
## disables Winsock SO_REUSEADDR (which would otherwise permit duplicate listeners).
var owner_guard: TCPServer
var path := PATH:
	set(value):
		if owner_guard != null and owner_guard.is_listening() and value != path:
			error = "Receipt storage cannot be moved while it is in use."
			return
		path = value

func acquire() -> Error:
	if owner_guard != null and owner_guard.is_listening():
		return OK
	var address := ProjectSettings.globalize_path(path).simplify_path().replace("\\", "/").to_lower()
	var port := 49152 + int(address.sha256_text().substr(0, 7).hex_to_int() % 16384)
	var guard := TCPServer.new()
	var result := guard.listen(port, "127.0.0.1")
	if result != OK:
		guard.stop()
		error = "Another instance or local service is using receipt storage. Close the other instance and retry. Nothing was sent."
		return result
	owner_guard = guard
	return OK

func claim(pending: Dictionary) -> Error:
	var already_owned := owner_guard != null and owner_guard.is_listening()
	if acquire() != OK:
		return ERR_ALREADY_IN_USE
	var existing := load_pending()
	if not error.is_empty() or existing != pending:
		if not already_owned:
			_release()
		error = "The saved receipt changed or could not be read. Nothing was sent; reload its current state."
		return ERR_INVALID_DATA
	return OK

func _release() -> void:
	if owner_guard != null:
		owner_guard.stop()
	owner_guard = null

func load_pending() -> Dictionary:
	error = ""
	if not FileAccess.file_exists(path):
		return {}
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		error = "The pending receipt could not be read. New transactions are blocked."
		return {}
	var size := file.get_length()
	var text := file.get_as_text() if size <= MAX_BYTES else ""
	file.close()
	var parser := JSON.new()
	if parser.parse(text) != OK or not parser.data is Dictionary:
		error = "The pending receipt is damaged. It has been kept; new transactions are blocked."
		return {}
	var record: Dictionary = parser.data
	if record.get("schema") != 1 or not record.get("transaction") is Dictionary or not valid(record.transaction):
		error = "The pending receipt format is unsupported. It has been kept; new transactions are blocked."
		return {}
	# JSON parses numbers as floats; restore the API's strict integer price contract.
	record.transaction.method = int(record.transaction.method)
	if record.transaction.payload.get("expected_price") != null:
		record.transaction.payload.expected_price = int(record.transaction.payload.expected_price)
	return record.transaction

func stage(pending: Dictionary) -> Error:
	if acquire() != OK:
		return ERR_ALREADY_IN_USE
	var existing := load_pending()
	if not error.is_empty() or not existing.is_empty():
		return ERR_ALREADY_IN_USE
	if not valid(pending):
		error = "The receipt could not be saved safely. Nothing was sent."
		return ERR_INVALID_DATA
	var text := JSON.stringify({"schema": 1, "transaction": pending})
	if text.to_utf8_buffer().size() > MAX_BYTES:
		return ERR_INVALID_DATA
	var file := FileAccess.open(path + ".tmp", FileAccess.WRITE)
	if file == null:
		return FileAccess.get_open_error()
	var stored := file.store_string(text)
	file.flush()
	var result := file.get_error()
	file.close()
	# Godot's Windows flush ignores fflush's return value. Reopen after close and
	# verify actual bytes, both before and after publishing, rather than trusting it.
	if not stored or result != OK or not _matches_bytes(path + ".tmp", text):
		return ERR_FILE_CANT_WRITE
	result = DirAccess.rename_absolute(path + ".tmp", path)
	if result != OK:
		return result
	return OK if _matches_bytes(path, text) else ERR_FILE_CANT_WRITE

func _matches_bytes(file_path: String, expected: String) -> bool:
	var file := FileAccess.open(file_path, FileAccess.READ)
	if file == null:
		return false
	var bytes := expected.to_utf8_buffer()
	var matches := file.get_length() == bytes.size() and file.get_buffer(bytes.size()) == bytes
	file.close()
	return matches

func clear(pending: Dictionary) -> Error:
	var result := claim(pending)
	if result != OK:
		return result
	result = DirAccess.remove_absolute(path)
	if result == OK:
		_release()
	return result

static func valid(pending: Dictionary) -> bool:
	if pending.size() != 6:
		return false
	for field in ["path", "owner", "server", "message"]:
		if not pending.get(field) is String or str(pending[field]).is_empty():
			return false
	if pending.get("method") != HTTPClient.METHOD_POST or not pending.get("payload") is Dictionary:
		return false
	var server: String = pending.server
	if not (server.begins_with("https://") or server.begins_with("http://")) or "@" in server or "?" in server or "#" in server:
		return false
	var payload: Dictionary = pending.payload
	var fields: Array = ["idempotency_key"]
	match str(pending.path):
		"/store/buy": fields.append("definition_id")
		"/cases/open": fields.append_array(["case_id", "key_id"])
		_:
			var parts := str(pending.path).split("/")
			if parts.size() != 4 or parts[1] != "market" or parts[2].is_empty() or parts[3] != "buy":
				return false
			if payload.has("expected_price"):
				var price: Variant = payload.expected_price
				if price != null and (not (price is int or price is float) or not is_finite(float(price)) or float(price) != floor(float(price)) or float(price) < 1 or float(price) > 10000000):
					return false
				fields.append("expected_price")
	if payload.size() != fields.size():
		return false
	for field in fields:
		if field != "expected_price" and (not payload.get(field) is String or str(payload[field]).is_empty()):
			return false
	return true
