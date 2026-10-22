## The same external probe runs on the frozen baseline and adapted candidate.
extends SceneTree
const UI = preload("res://scripts/ui/economy_ui.gd")
var fixture_path := ""

class FixtureAPI extends EconomyAPI:
	var calls: Array[Dictionary] = []
	var reply := {"_error": "Fixture response lost after commit", "_outcome": "unknown", "_uncertain": true}
	func request(path: String, method: int = HTTPClient.METHOD_GET, payload: Dictionary = {}) -> Dictionary:
		if path == "/auth/logout":
			return {}
		if method == HTTPClient.METHOD_GET:
			match path:
				"/me": return {"credits": 0, "xp": 0}
				"/inventory": return {"items": [{"id": "fixture-server-confirmed-item"}]}
				_: return {"slots": {}}
		calls.append({"path": path, "method": method, "payload": payload.duplicate(true)})
		return reply.duplicate(true)

func _initialize() -> void:
	call_deferred("run")

func make_ui(suffix: String) -> EconomyUI:
	var ui := UI.new()
	for property in ui.get_property_list():
		if property.name == "transaction_journal":
			ui.get("transaction_journal").path = fixture_path + suffix
	root.add_child(ui)
	ui.api.free()
	var api := FixtureAPI.new()
	api.player_id = "fixture-original-account"
	api.token = "synthetic-memory-only-lifecycle-token"
	ui.api = api
	ui.add_child(api)
	return ui

func run() -> void:
	fixture_path = OS.get_environment("SIGHTBREAK_LIFECYCLE_JOURNAL")
	if fixture_path.is_empty():
		quit(2)
		return
	var body := {"idempotency_key": "d53cbec2-9551-458a-973c-538442a3209f", "definition_id": "key"}
	var ui := make_ui(".retry")
	var api := ui.api as FixtureAPI
	await ui._perform("/store/buy", body)
	var retry := {"pending_after_lost_response": not ui.pending_transaction.is_empty()}
	body.idempotency_key = "caller-change-must-not-replace-original"
	api.reply = {"_error": "Fixture retry rejected while an earlier request may still commit", "_outcome": "rejected", "_status": 409, "_uncertain": false}
	var rejected: Dictionary = await ui._retry_pending()
	retry["retry_status"] = rejected.get("_status", 0)
	retry["pending_after_rejected_retry"] = not ui.pending_transaction.is_empty()
	retry["journal_after_rejected_retry"] = FileAccess.file_exists(fixture_path + ".retry")
	retry["calls"] = api.calls.duplicate(true)
	ui.free()

	body.idempotency_key = "112a501d-3ca0-4811-9783-385cdecb073e"
	ui = make_ui(".logout")
	await ui._perform("/store/buy", body)
	await ui._logout()
	var logout := {"pending_after_logout": not ui.pending_transaction.is_empty(), "token_cleared": ui.api.token.is_empty(), "account_cleared": ui.account.is_empty()}
	ui.free()
	ui = make_ui(".logout")
	api = ui.api as FixtureAPI
	logout["pending_after_recreation"] = not ui.pending_transaction.is_empty()
	api.reply = {"item": {"id": "fixture-server-confirmed-item"}, "credits": 0}
	var replay: Dictionary = await ui._retry_pending()
	logout["result"] = replay
	logout["calls"] = api.calls.duplicate(true)
	logout["pending_after_confirmation"] = not ui.pending_transaction.is_empty()
	logout["account"] = ui.account.duplicate(true)
	print("RECEIPT_LIFECYCLE " + JSON.stringify({"retry": retry, "logout": logout}))
	ui.queue_free()
	await process_frame
	quit(0)
