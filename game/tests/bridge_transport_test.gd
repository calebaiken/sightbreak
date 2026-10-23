extends SceneTree
var api_url: String = ""
var expectation: String = "retry"
func _initialize() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--api="): api_url = arg.trim_prefix("--api=")
		if arg.begins_with("--expect="): expectation = arg.trim_prefix("--expect=")
	call_deferred("_run")
func _run() -> void:
	var bridge := SBEconomyBridge.new()
	bridge.configure(api_url, "test-server")
	root.add_child(bridge)
	var result: Dictionary = await bridge.submit_result({"match_id": "fixed-test-id", "participants": []})
	var okay: bool = bool(result.get("ok", false)) if expectation == "retry" else not bool(result.get("ok", false)) and int(result.get("status", 0)) == 302
	print("BRIDGE_TRANSPORT_PASS " + expectation if okay else "BRIDGE_TRANSPORT_FAIL " + expectation)
	bridge.queue_free()
	await process_frame
	quit(0 if okay else 1)
