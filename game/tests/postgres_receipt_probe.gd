## Real EconomyUI/API over the owned production HTTP/PG fixture; no stub API.
extends SceneTree
const UI = preload("res://scripts/ui/economy_ui.gd")

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var config: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(OS.get_environment("SIGHTBREAK_PG_RECEIPT_CONFIG")))
	# Bootstrap is deliberately memory-only. Configuration, argv and output contain
	# no plaintext password or bearer token; every process gets a fresh real login.
	var auth: Dictionary = JSON.parse_string(OS.get_environment("SIGHTBREAK_PG_RECEIPT_AUTH"))
	var ui := UI.new()
	ui.transaction_journal.path = config.journal
	ui.reduced_motion = true
	root.add_child(ui)
	await ui._authenticate(config.url, auth.username, auth.password, "", false, null)
	auth.clear()
	if ui.api.token.is_empty() or ui.api.player_id != config.expected_account:
		print("PG_RECEIPT_AUTH_FAILED")
		ui.queue_free()
		await process_frame
		quit(2)
		return
	print("PG_RECEIPT_AUTH_READY " + JSON.stringify({"player_id": ui.api.player_id, "mode": config.mode}))
	var result: Dictionary = {}
	var pending_before := not ui.pending_transaction.is_empty()
	match str(config.mode):
		"send":
			var payload: Dictionary = config.payload.duplicate(true)
			payload.expected_price = int(payload.expected_price)
			result = await ui._perform(config.path, payload)
		"retry", "guard":
			result = await ui._retry_pending()
		"post_clear":
			result = await ui._retry_pending()
			await ui._refresh()
		_:
			quit(2)
			return
	var observation := {"mode": config.mode, "result": result,
		"pending_before": pending_before, "pending_after": not ui.pending_transaction.is_empty(),
		"account": ui.account.duplicate(true), "inventory": ui.inventory.duplicate(true),
		"player_id": ui.api.player_id, "journal_exists": FileAccess.file_exists(config.journal)}
	# _perform/_retry_pending return only after their actual account refresh finishes.
	print("PG_RECEIPT_RESULT " + JSON.stringify(observation))
	await ui._logout()
	print("PG_RECEIPT_LOGOUT " + JSON.stringify({"token_cleared": ui.api.token.is_empty(),
		"account_cleared": ui.account.is_empty(), "pending_after": not ui.pending_transaction.is_empty()}))
	ui.queue_free()
	await process_frame
	await process_frame
	quit(0)
