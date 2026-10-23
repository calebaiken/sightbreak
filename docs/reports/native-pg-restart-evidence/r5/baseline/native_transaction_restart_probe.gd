## External, identical probe for both revisions. Production UI/API code is unmodified.
extends SceneTree
const UI = preload("res://scripts/ui/economy_ui.gd")

func _initialize() -> void:
	call_deferred("run")

func record(event: String, fields := {}) -> void:
	fields["event"] = event
	fields["pid"] = OS.get_process_id()
	fields["unix_seconds"] = Time.get_unix_time_from_system()
	print("NATIVE_RECEIPT_EVENT " + JSON.stringify(fields))

func run() -> void:
	var config: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(OS.get_environment("SIGHTBREAK_RECEIPT_FIXTURE")))
	# Exactly the integer captured by the market buy button; JSON.parse makes floats.
	config.payload.expected_price = int(config.payload.expected_price)
	var ui := UI.new()
	for property in ui.get_property_list():
		if property.name == "transaction_journal":
			ui.get("transaction_journal").path = config.journal
	root.add_child(ui)
	var pending_on_start: Dictionary = ui.pending_transaction.duplicate(true)
	record("ui_ready", {"mode": config.mode, "pending": pending_on_start})
	var password_field := LineEdit.new()
	root.add_child(password_field)
	# This is the normal sign-in path, including /me, /inventory, /catalog, /loadout.
	await ui._authenticate(config.url, config.username, config.password, "", false, password_field)
	var authenticated: bool = ui.api.player_id == config.owner and not ui.api.token.is_empty() and ui.account.get("player_id") == config.owner
	record("authenticated", {"ok": authenticated, "owner": ui.api.player_id, "token_sha256": ui.api.token.sha256_text()})
	if not authenticated:
		record("authentication_failed", {"status": ui.status.text})
		quit(1)
		return
	var result: Dictionary
	if config.mode == "send":
		record("perform_entered", {"path": config.path, "payload": config.payload, "expected_price_is_int": config.payload.expected_price is int})
		result = await ui._perform(config.path, config.payload)
	else:
		# An empty journal must cause an empty result and no HTTP mutation request.
		result = await ui._retry_pending()
	record("completed", {"mode": config.mode, "result": result, "pending_on_start": pending_on_start, "pending_after": ui.pending_transaction, "account": ui.account, "inventory": ui.inventory})
	ui.queue_free()
	password_field.queue_free()
	await process_frame
	await process_frame
	quit(0)
