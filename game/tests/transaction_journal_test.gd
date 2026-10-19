extends SceneTree
const UI = preload("res://scripts/ui/economy_ui.gd")
const JOURNAL = preload("res://scripts/ui/transaction_journal.gd")
var checks := 0
var failures: Array[String] = []
var receipt_path := "user://journal_test_%d.json" % OS.get_process_id()

class StubAPI extends EconomyAPI:
	var reply: Dictionary = {"_error": "lost", "_outcome": "unknown", "_uncertain": true}
	var calls: Array[Dictionary] = []
	var receipt_path := ""
	var staged_before_send := false
	func request(path: String, method: int = HTTPClient.METHOD_GET, payload: Dictionary = {}) -> Dictionary:
		if path == "/auth/logout":
			return {}
		if method != HTTPClient.METHOD_GET:
			staged_before_send = FileAccess.file_exists(receipt_path)
			calls.append({"path": path, "method": method, "payload": payload.duplicate(true)})
			return reply.duplicate(true)
		return {"items": [], "slots": {}}

func _initialize() -> void:
	call_deferred("run")

func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures.append(message)
		push_error(message)

func make_ui() -> EconomyUI:
	var ui := UI.new()
	ui.transaction_journal.path = receipt_path
	root.add_child(ui)
	ui.api.free()
	var api := StubAPI.new()
	api.player_id = "original-owner"
	api.token = "never-persist-this-token"
	api.receipt_path = receipt_path
	ui.api = api
	ui.add_child(api)
	return ui

func run() -> void:
	var ui := make_ui()
	var api := ui.api as StubAPI
	var payload := {"idempotency_key": "same-receipt", "expected_price": 10000000}
	await ui._perform("/market/listing-id/buy", payload)
	check(api.staged_before_send, "Receipt exists before the mutation is dispatched")
	check(not FileAccess.get_file_as_string(receipt_path).contains(api.token), "Bearer credential is absent from the durable record")
	payload.expected_price = 1
	await ui._logout()
	check(not ui.pending_transaction.is_empty(), "Sign-out retains the unresolved receipt")
	ui.free()
	ui = make_ui()
	api = ui.api as StubAPI
	check(ui.retry_button.visible and ui.pending_transaction.payload.expected_price is int, "Recreated UI discovers receipt and restores strict integer price")
	check(ui.pending_transaction.payload.expected_price == 10000000, "Recovery preserves maximum consent price despite caller mutation")
	api.player_id = "different-owner"
	await ui._retry_pending()
	api.player_id = "original-owner"
	api.base_url = "http://127.0.0.1:9999"
	await ui._retry_pending()
	check(api.calls.is_empty(), "Neither account nor server mismatch dispatches a recovery")
	api.base_url = "http://127.0.0.1:8080"
	for response in [
		{"_error": "offline", "_outcome": "not_reached"},
		{"_error": "expired", "_outcome": "rejected", "_status": 401},
		{"_error": "limited", "_outcome": "rejected", "_status": 429},
		{"_error": "invalid", "_outcome": "rejected", "_status": 422},
		{"_error": "lost", "_outcome": "unknown", "_uncertain": true}]:
		api.reply = response
		api.player_id = "original-owner"
		api.token = "memory-only-again"
		await ui._retry_pending()
		check(not ui.pending_transaction.is_empty() and FileAccess.file_exists(receipt_path), "Retry failure %s preserves earlier uncertainty" % str(response))
	api.reply = {"item": {"id": "committed-once"}}
	await ui._retry_pending()
	check(ui.pending_transaction.is_empty() and not FileAccess.file_exists(receipt_path), "Authoritative confirmation clears both memory and disk")
	for call in api.calls:
		check(call.payload == {"idempotency_key": "same-receipt", "expected_price": 10000000}, "Every recovery uses the identical receipt and price")
	ui.transaction_journal.path = receipt_path + "/missing-parent"
	var call_count := api.calls.size()
	await ui._perform("/store/buy", {"idempotency_key": "another", "definition_id": "key"})
	check(api.calls.size() == call_count, "Unwritable receipt storage prevents dispatch")
	ui.free()
	var file := FileAccess.open(receipt_path, FileAccess.WRITE)
	file.store_string("{truncated")
	file.close()
	ui = make_ui()
	api = ui.api as StubAPI
	await ui._perform("/store/buy", {"idempotency_key": "another", "definition_id": "key"})
	check(not ui.transaction_storage_error.is_empty() and api.calls.is_empty(), "Damaged journal blocks new mutations instead of forgetting an unknown purchase")
	check(FileAccess.get_file_as_string(receipt_path) == "{truncated", "Damaged evidence is preserved")
	ui.free()
	DirAccess.remove_absolute(receipt_path)
	var journal := JOURNAL.new()
	journal.path = receipt_path
	var record := {"path": "/store/buy", "payload": {"idempotency_key": "receipt", "definition_id": "key", "token": "secret"}, "owner": "account", "server": "http://127.0.0.1:8080", "method": HTTPClient.METHOD_POST, "message": "done"}
	check(journal.stage(record) != OK and not FileAccess.file_exists(receipt_path), "Unrecognized payload fields cannot persist credentials")
	await process_frame
	print("TRANSACTION_JOURNAL %d/%d passed" % [checks - failures.size(), checks])
	quit(0 if failures.is_empty() else 1)
