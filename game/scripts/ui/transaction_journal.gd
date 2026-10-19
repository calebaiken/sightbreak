class_name TransactionJournal
extends RefCounted
## One outstanding keyed mutation. Authentication and offline balances never belong here.
## Flush + same-directory rename precede dispatch; this covers app-process termination.
const PATH := "user://pending_transaction.json"
const MAX_BYTES := 8192
var path := PATH
var error := ""

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
	file.store_string(text)
	file.flush()
	var result := file.get_error()
	file.close()
	if result != OK:
		return result
	return DirAccess.rename_absolute(path + ".tmp", path)

func clear(pending: Dictionary) -> Error:
	var existing := load_pending()
	if not error.is_empty() or existing != pending:
		return ERR_INVALID_DATA
	return DirAccess.remove_absolute(path)

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
