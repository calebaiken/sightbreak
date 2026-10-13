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
		return {"_error": "Unable to start the connection. Check the server address."}
	var completed: Array = await http.request_completed
	http.queue_free()
	if int(completed[0]) != HTTPRequest.RESULT_SUCCESS:
		return {"_error": "Server unavailable or connection timed out. Check your network and server address. If a purchase was pending, refresh inventory before retrying."}
	var code := int(completed[1])
	var data: Variant = JSON.parse_string((completed[3] as PackedByteArray).get_string_from_utf8())
	if not data is Dictionary:
		return {"_error": "Server returned an unreadable response (%d)." % code}
	if code < 200 or code >= 300:
		var detail: Variant = data.get("detail", data.get("error", "Request rejected"))
		if code == 401:
			logout()
		return {"_error": "%s (%d)" % [str(detail), code], "_status": code}
	return data
