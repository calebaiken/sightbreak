## External harness runs this same probe against baseline and candidate projects.
extends SceneTree
const UI = preload("res://scripts/ui/economy_ui.gd")

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var config: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(OS.get_environment("SIGHTBREAK_RECEIPT_FIXTURE")))
	if config.payload.has("expected_price"):
		# The real buy button captures an integer; fixture JSON otherwise parses it as a float.
		config.payload.expected_price = int(config.payload.expected_price)
	var ui := UI.new()
	# Baseline has no journal; both use the same probe and isolated state location.
	for property in ui.get_property_list():
		if property.name == "transaction_journal":
			ui.get("transaction_journal").path = config.journal
	root.add_child(ui)
	ui.api.base_url = config.url
	ui.api.player_id = config.owner
	ui.api.token = config.token
	var result: Dictionary = {}
	var observation: Dictionary = {}
	if config.mode == "send":
		result = await ui._perform(config.path, config.payload)
	elif ui.pending_transaction.is_empty():
		observation = {"recovered": false, "reason": "no pending receipt after process restart"}
	else:
		result = await ui._retry_pending()
	if observation.is_empty():
		observation = {"recovered": not result.has("_error") and result.has("item"), "result": result, "pending": not ui.pending_transaction.is_empty()}
	print("RECEIPT_PROBE " + JSON.stringify(observation))
	if config.mode == "retry_hold":
		# The driver kills this process after the observation, before teardown can run.
		await create_timer(60.0).timeout
		quit(2)
		return
	ui.queue_free()
	await process_frame
	quit(0)
