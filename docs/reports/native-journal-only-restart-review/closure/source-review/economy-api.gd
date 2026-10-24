class_name EconomyAPI
extends Node
## Each request gets a dedicated HTTPRequest. Credentials remain in memory only.
var base_url := "http://127.0.0.1:8080"
var token := ""
var player_id := ""

func configure_url(value: String) -> String:
	var url := value.strip_edges().trim_suffix("/")
	if not url.begins_with("https://") and not url.begins_with("http://"):
		return "Use an HTTPS URL, or HTTP on a trusted local development network."
	if "@" in url or "?" in url or "#" in url:
		return "The server address cannot contain credentials, a query, or a fragment."
	if url.begins_with("http://"):
		var host := url.trim_prefix("http://").split("/")[0].split(":")[0]
		var numeric_host := host.is_valid_ip_address()
		var private_host := host == "localhost" or (numeric_host and (host == "127.0.0.1" or host.begins_with("192.168.") or host.begins_with("10.")))
		var parts := host.split(".")
		if numeric_host and parts.size() == 4 and parts[0] == "172" and int(parts[1]) >= 16 and int(parts[1]) <= 31:
			private_host = true
		if not private_host:
			return "Public servers require HTTPS. Plain HTTP is permitted only for loopback or a trusted LAN during development."
	logout()
	base_url = url
	return ""

func logout() -> void:
	token = ""
	player_id = ""

func key() -> String:
	var bytes := Crypto.new().generate_random_bytes(16)
	bytes[6] = (bytes[6] & 15) | 64
	bytes[8] = (bytes[8] & 63) | 128
	var value := bytes.hex_encode()
	return "%s-%s-%s-%s-%s" % [value.substr(0, 8), value.substr(8, 4), value.substr(12, 4), value.substr(16, 4), value.substr(20, 12)]

## What a failed request tells the player, in order of how much is known. "outcome" is one of:
##   not_sent      nothing left this device (the request could not be started)
##   not_reached   a connection to the server was never made, so the server cannot have acted
##   unknown       the request may have reached the server and the answer was lost or unreadable,
##                 or the server failed (5xx); whether it acted is NOT known
##   rejected      the server answered with a refusal (4xx); it did not act
## Successful responses carry no "_outcome". "_uncertain" is true exactly for "unknown".
const NOT_REACHED_RESULTS := [HTTPRequest.RESULT_CANT_CONNECT, HTTPRequest.RESULT_CANT_RESOLVE, HTTPRequest.RESULT_TLS_HANDSHAKE_ERROR]

func request(path: String, method: int = HTTPClient.METHOD_GET, payload: Dictionary = {}) -> Dictionary:
	var http := HTTPRequest.new()
	http.timeout = 12.0
	http.max_redirects = 0
	http.body_size_limit = 4194304
	add_child(http)
	var headers := PackedStringArray(["Content-Type: application/json", "Accept: application/json"])
	if not token.is_empty():
		headers.append("Authorization: Bearer " + token)
	var body := "" if method == HTTPClient.METHOD_GET else JSON.stringify(payload)
	var started := http.request(base_url + path, headers, method, body)
	if started != OK:
		http.queue_free()
		return {"_error": "The request could not be started, so nothing was sent. Check the server address.", "_outcome": "not_sent", "_uncertain": false}
	var completed: Array = await http.request_completed
	http.queue_free()
	if int(completed[0]) != HTTPRequest.RESULT_SUCCESS:
		if int(completed[0]) in NOT_REACHED_RESULTS:
			return {"_error": "Could not connect to the server, so nothing was sent. Check your network and the server address.", "_outcome": "not_reached", "_uncertain": false}
		return {"_error": "The connection dropped or timed out after the request may have reached the server. Whether it was carried out is not known.", "_outcome": "unknown", "_uncertain": true}
	var code := int(completed[1])
	# JSON.new().parse reports a bad body as an error code; parse_string would also log an engine error.
	var parser := JSON.new()
	var data: Variant = parser.data if parser.parse((completed[3] as PackedByteArray).get_string_from_utf8()) == OK else null
	if not data is Dictionary:
		return {"_error": "The server's answer (%d) could not be read. Whether the request was carried out is not known." % code, "_outcome": "unknown", "_uncertain": true, "_status": code}
	if code < 200 or code >= 300:
		var detail: Variant = data.get("detail", data.get("error", "Request rejected"))
		if code == 401:
			logout()
		var server_failed := code >= 500
		return {"_error": "%s (%d)" % [str(detail), code], "_status": code, "_outcome": "unknown" if server_failed else "rejected", "_uncertain": server_failed}
	return data
