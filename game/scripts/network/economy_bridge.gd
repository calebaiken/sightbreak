class_name SBEconomyBridge
extends Node
## Dedicated-server-only HTTP client. The privileged key never enters game snapshots.
var base_url: String = "http://127.0.0.1:8080"
var server_id: String = "local-relay"
var _server_key: String = ""

func configure(url: String, identity: String) -> void:
	base_url = url.trim_suffix("/")
	server_id = identity
	_server_key = OS.get_environment("SIGHTBREAK_SERVER_KEY")

func configured() -> bool:
	return _server_key.length() >= 32 and valid_origin(base_url)

static func valid_origin(url: String) -> bool:
	var pattern := RegEx.new()
	pattern.compile("^(https?)://([A-Za-z0-9.-]+)(?::([0-9]{1,5}))?$")
	var matched: RegExMatch = pattern.search(url)
	if matched == null:
		return false
	var port: String = matched.get_string(3)
	if not port.is_empty() and (int(port) < 1 or int(port) > 65535):
		return false
	return matched.get_string(1) == "https" or matched.get_string(2) in ["127.0.0.1", "localhost"]

func inspect_ticket(ticket: String) -> Dictionary:
	if ticket.length() < 32 or ticket.length() > 128:
		return {"ok": false, "error": "A valid account join ticket is required."}
	return await _post("/server/tickets/inspect", {"ticket": ticket, "server_id": server_id})

func consume_ticket(ticket: String) -> Dictionary:
	if ticket.length() < 20 or ticket.length() > 512:
		return {"ok": false, "error": "A valid account join ticket is required."}
	return await _post("/server/tickets/consume", {"ticket": ticket, "server_id": server_id})

func submit_result(result: Dictionary) -> Dictionary:
	var response: Dictionary = {}
	# The immutable UUID and payload are reused: a lost response cannot mint twice.
	for attempt in range(3):
		response = await _post("/server/matches", result)
		if bool(response.get("ok", false)):
			return response
		var status: int = int(response.get("status", 0))
		if status < 500 and not bool(response.get("transport_error", false)):
			return response
		if attempt < 2:
			await get_tree().create_timer(float(1 << attempt)).timeout
	return response

func make_request() -> HTTPRequest:
	var request := HTTPRequest.new()
	request.timeout = 10
	request.max_redirects = 0
	request.body_size_limit = 65536
	return request

func _post(path: String, payload: Dictionary) -> Dictionary:
	if not configured():
		return {"ok": false, "error": "The server economy bridge is not configured."}
	var request: HTTPRequest = make_request()
	add_child(request)
	var headers := PackedStringArray(["Content-Type: application/json", "X-Server-Key: " + _server_key])
	var error: Error = request.request(base_url + path, headers, HTTPClient.METHOD_POST, JSON.stringify(payload))
	if error != OK:
		request.queue_free()
		return {"ok": false, "transport_error": true, "error": "The account service could not be reached."}
	var reply: Array = await request.request_completed
	request.queue_free()
	var status: int = int(reply[1])
	var result_code: int = int(reply[0])
	var transient_transport: bool = result_code in [HTTPRequest.RESULT_CHUNKED_BODY_SIZE_MISMATCH, HTTPRequest.RESULT_CANT_CONNECT, HTTPRequest.RESULT_CANT_RESOLVE, HTTPRequest.RESULT_CONNECTION_ERROR, HTTPRequest.RESULT_NO_RESPONSE, HTTPRequest.RESULT_REQUEST_FAILED, HTTPRequest.RESULT_TIMEOUT]
	# Redirect refusal is a security decision, never a transient transport failure.
	# Keep the HTTP code even when Godot reports RESULT_REDIRECT_LIMIT_REACHED.
	if status >= 300 and status < 500:
		transient_transport = false
	if result_code != HTTPRequest.RESULT_SUCCESS or status < 200 or status >= 300:
		return {"ok": false, "status": status, "transport_error": transient_transport, "error": "The account service rejected the operation (%d)." % status}
	var decoder := JSON.new()
	if decoder.parse((reply[3] as PackedByteArray).get_string_from_utf8()) != OK or not decoder.data is Dictionary:
		return {"ok": false, "status": status, "error": "The account service returned an invalid response."}
	return {"ok": true, "data": decoder.data}
