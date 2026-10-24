## The same external probe exercises the actual UI/API/journal in each source tree.
extends SceneTree
const UI = preload("res://scripts/ui/economy_ui.gd")

func _initialize() -> void:
	call_deferred("run")

func disk(path: String) -> Dictionary:
	var exists := FileAccess.file_exists(path)
	var bytes := FileAccess.get_file_as_bytes(path) if exists else PackedByteArray()
	return {"exists": exists, "base64": Marshalls.raw_to_base64(bytes), "bytes": bytes.size()}

func run() -> void:
	var config: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(OS.get_environment("SIGHTBREAK_RESPONSE_FIXTURE")))
	for entry in config.cases:
		var ui := UI.new()
		ui.transaction_journal.path = entry.journal
		ui.configure({"settings": {"reduced_motion": true}})
		root.add_child(ui)
		ui.api.base_url = config.url
		ui.api.player_id = config.owner
		ui.api.token = "response-contract-fixture-only"
		ui.account = entry.account.duplicate(true)
		ui.inventory = entry.inventory.duplicate(true)
		ui.listings = entry.listings.duplicate(true)
		ui.catalog = entry.catalog.duplicate(true)
		var payload: Dictionary = entry.payload.duplicate(true)
		if payload.get("expected_price") != null:
			payload.expected_price = int(payload.expected_price)
		var seed_result: Dictionary = {}
		var before := disk(entry.journal)
		var result: Dictionary
		if entry.mode == "recovery":
			seed_result = await ui._perform(entry.path, payload)
			before = disk(entry.journal)
			result = await ui._retry_pending()
		else:
			result = await ui._perform(entry.path, payload)
		var observation := {"id": entry.id, "mode": entry.mode, "pid": OS.get_process_id(),
			"seed_result": seed_result, "before": before, "result": result,
			"pending": ui.pending_transaction.duplicate(true), "after": disk(entry.journal),
			"retry_visible": ui.retry_button.visible, "busy": ui.busy,
			"status": ui.status.text, "storage_error": ui.transaction_storage_error}
		var file := FileAccess.open(entry.output, FileAccess.WRITE)
		file.store_string(JSON.stringify(observation))
		file.close()
		print("RESPONSE_OBSERVATION " + JSON.stringify(observation))
		ui.queue_free()
		await process_frame
		await process_frame
	await create_timer(0.5).timeout
	quit(0)
