extends SceneTree
const UI = preload("res://scripts/ui/economy_ui.gd")
const FINISH = preload("res://scripts/ui/cosmetic_material.gd")
var failures: Array[String] = []
var checks := 0

class RecoveryAPI extends EconomyAPI:
	var calls: Array[Dictionary] = []
	var fail_next := true
	func request(path: String, method: int = HTTPClient.METHOD_GET, payload: Dictionary = {}) -> Dictionary:
		if method != HTTPClient.METHOD_GET:
			calls.append({"path": path, "payload": payload.duplicate(true), "method": method})
			if fail_next:
				fail_next = false
				return {"_error": "Simulated lost response after commit", "_uncertain": true}
			return {"item": {"id": "already-committed-instance"}, "credits": 0}
		match path:
			"/me": return {"credits": 0}
			"/inventory": return {"items": [{"id": "already-committed-instance"}]}
			"/catalog": return {}
			"/loadout": return {"slots": {}}
		return {}

func _initialize() -> void:
	call_deferred("run")

func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures.append(message)
		push_error(message)

func run() -> void:
	var ui := UI.new()
	ui.transaction_journal.path = "user://economy_recovery_test_%d.json" % OS.get_process_id()
	root.add_child(ui)
	await process_frame
	ui.api.free()
	var fake := RecoveryAPI.new()
	fake.player_id = "original-account"
	fake.token = "memory-only-test"
	ui.api = fake
	ui.add_child(fake)
	var body := {"definition_id": "key", "idempotency_key": "unchanged-receipt"}
	var lost: Dictionary = await ui._perform("/store/buy", body)
	check(lost.has("_error") and not ui.pending_transaction.is_empty(), "Lost keyed response retains exact transaction")
	check(ui.retry_button.visible, "Recovery action is visible")
	body.idempotency_key = "caller-mutated-body"
	var blocked: Dictionary = await ui._perform("/store/buy", body)
	check(blocked.has("_error") and fake.calls.size() == 1, "Unresolved purchase blocks another mutation")
	fake.player_id = "different-account"
	var wrong: Dictionary = await ui._retry_pending()
	check(wrong.has("_error") and fake.calls.size() == 1, "Recovery cannot cross accounts")
	fake.player_id = "original-account"
	var recovered: Dictionary = await ui._retry_pending()
	check(recovered.item.id == "already-committed-instance", "Recovery uses server's previously committed instance")
	check(fake.calls.size() == 2 and fake.calls[0] == fake.calls[1], "Retry sends identical endpoint, method and original receipt payload")
	check(ui.pending_transaction.is_empty() and not ui.retry_button.visible, "Confirmed recovery clears pending state")
	check(ui.inventory.size() == 1, "Recovered ownership is refreshed from server")
	var first := FINISH.finish({"collection": "Obsidian", "pattern_seed": 123, "wear": 0.4})
	var second := FINISH.finish({"collection": "Crimson Archive", "pattern_seed": 123, "wear": 0.4})
	check(first.get_shader_parameter("base_paint") != second.get_shader_parameter("base_paint"), "Collection materials have distinct authored palettes")
	check(first.get_shader_parameter("pattern_seed") == 123.0 and is_equal_approx(first.get_shader_parameter("wear"), 0.4), "Inspection preserves server pattern and wear metadata")
	check(FINISH.finish({"wear": 10}).get_shader_parameter("wear") == 1.0, "Visual wear values clamp defensively")
	check(FINISH.finish({}).get_shader_parameter("patterned") == 0.0, "Standard equipment keeps an unpatterned training finish")
	ui.queue_free()
	await process_frame
	if failures.is_empty():
		print("PASS: %d economy recovery and cosmetic material assertions" % checks)
	quit(0 if failures.is_empty() else 1)
