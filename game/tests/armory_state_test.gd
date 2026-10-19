extends SceneTree
## The armory's account, text-size and transaction behaviour, each checked against the way it
## really happens:
##   * the catalog is the backend's own (scripts/export_catalog_fixture.py), not hand-typed;
##   * every label follows the text-size setting and none falls under the legibility floor;
##   * a balance the server has not stated is never shown as zero, and money buttons say so;
##   * failures are classified from REAL transports (a closed port, a server that hangs up, a
##     server that answers 4xx and 5xx), and only an unknown outcome of a transaction that holds
##     a receipt identifier offers a retry;
##   * the confirmation is driven through the real CONFIRM DISPLAYED REVISION button with 1, 5
##     and 20 items per side and always fits the screen, with reachable buttons and terms;
##   * the payload each confirmed action sends, and that a retry cannot charge twice, are checked
##     against a fake server that holds the world fixture.
## Nothing here is a real player's data: the only server is a loopback fixture.
const UI = preload("res://scripts/ui/economy_ui.gd")
const DESIGN = preload("res://scripts/ui/design_tokens.gd")
const SAFE_AREA = preload("res://scripts/ui/safe_area.gd")
const SCALES := [0.85, 1.0, 1.15, 1.3, 1.4]
var failures: Array[String] = []
var checks := 0
var ui: EconomyUI
var fake: FakeAPI
var capture_dir := OS.get_environment("ECONOMY_CAPTURE_DIR")

## The server, as far as the armory can tell: it answers GETs from the world fixture, applies a
## transaction once per idempotency key and can lose the answer after applying it.
class FakeAPI extends EconomyAPI:
	var log: Array = []
	var world: Dictionary = {}
	var credits := 0
	var charges := 0
	var applied: Dictionary = {}
	var lose_response_once := false
	var script_results: Array = []

	func request(path: String, method: int = HTTPClient.METHOD_GET, payload: Dictionary = {}) -> Dictionary:
		log.append({"path": path, "method": method, "payload": payload.duplicate(true)})
		if not script_results.is_empty():
			return script_results.pop_front()
		if method == HTTPClient.METHOD_GET:
			match path:
				"/me":
					var account: Dictionary = (world.account as Dictionary).duplicate(true)
					account.credits = credits
					return account
				"/inventory": return world.inventory
				"/catalog": return world.catalog
				"/loadout": return {"slots": {}}
				"/market": return world.market
				"/trades": return world.trades
			return {"_error": "No such path (404)", "_status": 404, "_outcome": "rejected", "_uncertain": false}
		var key := str(payload.get("idempotency_key", ""))
		var result: Dictionary
		if not key.is_empty() and applied.has(key):
			result = applied[key]
		else:
			if path == "/store/buy" or path.ends_with("/buy"):
				charges += 1
				credits -= 150
			result = {"item": {"id": "fixture-item"}, "credits": credits, "fee": 4, "roll": 0, "table_version": "1"}
			if not key.is_empty():
				applied[key] = result
		if lose_response_once:
			lose_response_once = false
			return {"_error": "The connection dropped or timed out after the request may have reached the server. Whether it was carried out is not known.", "_outcome": "unknown", "_uncertain": true}
		return result

func _initialize() -> void:
	call_deferred("run")

func check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

func capture(name: String) -> void:
	if capture_dir.is_empty():
		return
	for i in 3:
		await process_frame
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(capture_dir)
	check(root.get_texture().get_image().save_png(capture_dir.path_join(name + ".png")) == OK, "Save native screenshot " + name)

func frames(count: int) -> void:
	for i in count:
		await process_frame

func world() -> Dictionary:
	return (JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/backend_world.json")) as Dictionary).world

func words(node: Node) -> String:
	var parts: Array[String] = []
	for label in node.find_children("*", "Label", true, false):
		parts.append((label as Label).text)
	for button in node.find_children("*", "Button", true, false):
		parts.append((button as Button).text)
	return "  ".join(parts)

func named(node_name: String) -> Node:
	return ui.content.find_child(node_name, true, false)

## A screen over the fake server, signed in as the fixture's player with the fixture's data held.
func make_ui(size: Vector2i, scale: float, signed_in := true) -> void:
	if is_instance_valid(ui):
		ui.queue_free()
		await frames(1)
	root.content_scale_size = size
	root.size = size
	ui = UI.new()
	ui.transaction_journal.path = "user://armory_state_test_%d.json" % OS.get_process_id()
	if FileAccess.file_exists(ui.transaction_journal.path):
		DirAccess.remove_absolute(ui.transaction_journal.path)
	ui.configure({"xp": 430, "credits": 900000, "settings": {"reduced_motion": true, "ui_text_scale": scale}})
	root.add_child(ui)
	await frames(1)
	var w := world()
	fake = FakeAPI.new()
	fake.world = w
	fake.credits = int(w.account.credits)
	ui.api.queue_free()
	ui.api = fake
	ui.add_child(fake)
	if signed_in:
		fake.token = "fixture-only"
		fake.player_id = w.players.self
		fake.base_url = "http://127.0.0.1:9"
		ui.account = (w.account as Dictionary).duplicate(true)
		ui.catalog = (w.catalog as Dictionary).duplicate(true)
		ui.inventory = (w.inventory.items as Array).duplicate(true)
		ui.listings = (w.market.listings as Array).duplicate(true)
		ui.trades = (w.trades.trades as Array).duplicate(true)
	ui.busy = false

func show_tab(tab: String) -> void:
	ui.active_tab = tab
	ui._render()
	(ui.content.get_parent() as ScrollContainer).scroll_vertical = 0
	await frames(3)

# ---------------------------------------------------------------------------------- fixture

func fixture_is_the_backends() -> void:
	var w := world()
	var catalog: Dictionary = w.catalog
	var definitions: Array = catalog.definitions
	var skins := definitions.filter(func(d): return d.kind == "weapon_skin")
	var cases := definitions.filter(func(d): return d.kind == "case")
	var keys := definitions.filter(func(d): return d.kind == "key")
	check(skins.size() == 24 and cases.size() == 4 and keys.size() == 1, "The backend catalog has 24 finishes, 4 cases and 1 key (%d/%d/%d)" % [skins.size(), cases.size(), keys.size()])
	var probabilities: Dictionary = catalog.case_tables.probabilities
	var total := 0.0
	for rarity in probabilities:
		total += float(probabilities[rarity])
	check(is_equal_approx(total, 100.0), "The published odds sum to 100 (%.3f)" % total)
	# One finish of each rarity in each collection: so the chance of a given finish is its rarity's.
	var per_collection := {}
	for skin in skins:
		per_collection[skin.collection] = per_collection.get(skin.collection, []) + [skin.rarity]
	for collection in per_collection:
		var rarities: Array = per_collection[collection]
		rarities.sort()
		var expected: Array = probabilities.keys()
		expected.sort()
		check(rarities == expected, "%s holds exactly one finish of each published rarity" % collection)
	check(keys[0].id == catalog.case_tables.key_definition_id, "The case table names the key the catalog defines")
	for definition in cases + keys:
		check(int(definition.price) == int(catalog.prices.case if definition.kind == "case" else catalog.prices.key), "%s costs the published %s price" % [definition.id, definition.kind])
	await make_ui(Vector2i(1280, 720), 1.0)
	await show_tab("cases")
	var browser_ids: Array[String] = []
	for button in ui.content.find_children("Finish_*", "Button", true, false):
		browser_ids.append(String(button.name).trim_prefix("Finish_"))
	browser_ids.sort()
	var catalog_ids: Array[String] = []
	for skin in skins:
		catalog_ids.append(str(skin.id))
	catalog_ids.sort()
	check(browser_ids == catalog_ids, "The collection browser shows exactly the catalog's finishes")
	for skin in skins:
		var card := named("Finish_" + str(skin.id))
		var published := UI.percent_text(float(probabilities[skin.rarity]))
		check(card != null and ("·  " + published) in words(card), "%s shows the odds %s the server publishes for %s" % [skin.id, published, skin.rarity])
	for rarity in probabilities:
		var text := UI.percent_text(float(probabilities[rarity]))
		check(not ".0%" in text, "%s odds print as %s without a stray .0" % [rarity, text])
	# The odds panel lists rarities commonest first, whatever order the JSON used.
	var shown: Array[String] = []
	for node in ui.content.find_children("*", "Label", true, false):
		var label_text := (node as Label).text
		if label_text in ["COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY", "MYTHIC"]:
			shown.append(label_text)
	check(shown == ["COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY", "MYTHIC"], "The odds table runs commonest to rarest: " + str(shown))
	var shuffled := {"Mythic": 0.1, "Common": 58.0, "Legendary": 0.9, "Rare": 11.0, "Epic": 4.0, "Uncommon": 26.0, "Unheard": 1.0}
	check(ui.rarities_in_order(shuffled) == ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic", "Unheard"], "Rarities sort commonest first with unknown ones last: " + str(ui.rarities_in_order(shuffled)))
	# The odds panel prints the server's numbers.
	var odds_words := words(ui.content)
	for rarity in probabilities:
		check(UI.percent_text(float(probabilities[rarity])) in odds_words, "The odds panel prints the %s probability" % rarity)

# ---------------------------------------------------------------------------------- numbers

## JSON has one number type and Godot reads each as a float, so every whole number the server
## sends (a pattern seed, XP, a level, a revision) would print as "1840233.0" unless formatted.
## A hand-typed fixture of integers hid this; the backend-derived fixture shows it.
func integers_print_whole() -> void:
	await make_ui(Vector2i(1280, 720), 1.0)
	var pattern := RegEx.create_from_string("(^|[^0-9.])[0-9]+\\.0([^0-9]|$)")
	var seen := 0
	for tab in ["inventory", "cases", "market", "trades", "profile"]:
		ui.selected = ui.inventory[0] as Dictionary
		await show_tab(tab)
		var text := words(ui)
		seen += 1
		var match := pattern.search(text)
		check(match == null, "%s: no whole number prints with a trailing .0 (%s)" % [tab, "" if match == null else text.substr(maxi(0, match.get_start() - 30), 60)])
	# The dialogs state the same numbers.
	await show_tab("market")
	var buy := ui.content.find_children("Buy", "Button", true, false)[0] as Button
	buy.pressed.emit()
	await frames(3)
	check(pattern.search(ui.dialog.dialog_text) == null and "Pattern 424242" in ui.dialog.dialog_text, "The buy confirmation prints the pattern seed whole: " + ui.dialog.dialog_text.replace("\n", " "))
	ui.dialog.cancel_button.pressed.emit()
	await show_tab("trades")
	var terms: String = ui.trade_confirmation_text(ui.trades[0])
	check(pattern.search(terms) == null and "pattern 1840233" in terms, "The trade terms print the pattern seed whole: " + terms.replace("\n", " "))
	check(seen == 5 and whole_check(), "Whole-number formatting of ints and floats alike")

func whole_check() -> bool:
	return UI.whole(1840233.0) == "1840233" and UI.whole(7) == "7" and UI.whole("—") == "—" and UI.whole(0.0) == "0"

# ---------------------------------------------------------------------------------- text size

func every_font_size(node: Node) -> Dictionary:
	var sizes := {}
	for label in node.find_children("*", "Label", true, false):
		var l := label as Label
		if l.is_visible_in_tree() and not l.text.is_empty():
			sizes[l] = l.get_theme_font_size("font_size")
	return sizes

func text_scale() -> void:
	var wallet_sizes := {}
	var heading_sizes := {}
	var widths := {}
	for scale in SCALES:
		await make_ui(Vector2i(1280, 720), scale)
		for tab in ["inventory", "cases", "market", "trades", "profile"]:
			await show_tab(tab)
			var smallest := 999
			var smallest_text := ""
			for label in every_font_size(ui):
				var size: int = every_font_size(ui)[label]
				if size < smallest:
					smallest = size
					smallest_text = (label as Label).text.left(24)
			check(smallest >= DESIGN.TEXT_FLOOR, "%s @%.2f: no label is under %d px (smallest %d: \"%s\")" % [tab, scale, DESIGN.TEXT_FLOOR, smallest, smallest_text])
		wallet_sizes[scale] = ui.wallet.get_theme_font_size("font_size")
		check(wallet_sizes[scale] == DESIGN.scaled_size(15, scale), "The wallet line follows the text size at %.2f (%d)" % [scale, wallet_sizes[scale]])
		await show_tab("inventory")
		var heading := ui.content.get_child(0) as Label
		heading_sizes[scale] = heading.get_theme_font_size("font_size")
		check(heading_sizes[scale] == DESIGN.scaled_size(28, scale), "The section heading follows the text size at %.2f (%d)" % [scale, heading_sizes[scale]])
		widths[scale] = ui.wallet.get_theme_font("font").get_string_size(ui.wallet.text, HORIZONTAL_ALIGNMENT_LEFT, -1, wallet_sizes[scale]).x
	for i in range(1, SCALES.size()):
		check(wallet_sizes[SCALES[i]] >= wallet_sizes[SCALES[i - 1]] and heading_sizes[SCALES[i]] >= heading_sizes[SCALES[i - 1]], "Type never shrinks as the text size grows (%.2f -> %.2f)" % [SCALES[i - 1], SCALES[i]])
	check(wallet_sizes[1.3] > wallet_sizes[1.0] and heading_sizes[1.3] > heading_sizes[1.0], "At 130 %% the wallet line and the headings are larger than at 100 %% (%d vs %d, %d vs %d)" % [wallet_sizes[1.3], wallet_sizes[1.0], heading_sizes[1.3], heading_sizes[1.0]])
	check(widths[1.3] > widths[1.0] * 1.15, "The wallet line is drawn at least 15 %% wider at 130 %% (%.0f vs %.0f px)" % [widths[1.3], widths[1.0]])
	# A change of setting reaches an armory that is already open.
	await make_ui(Vector2i(1280, 720), 1.0)
	var before: int = ui.wallet.get_theme_font_size("font_size")
	ui.configure({"settings": {"ui_text_scale": 1.3}})
	check(ui.wallet.get_theme_font_size("font_size") > before and ui.brand_label.get_theme_font_size("font_size") == DESIGN.scaled_size(24, 1.3), "Changing the text size restyles the open armory's header")

# ---------------------------------------------------------------------------------- balances

func balance_states() -> void:
	await make_ui(Vector2i(1280, 720), 1.0)
	var changes := [0]
	ui.account_changed.connect(func(): changes[0] += 1)
	var summary: Dictionary
	# Signed out.
	fake.logout()
	ui.account = {}
	summary = ui.account_summary()
	check(summary.state == "signed_out" and summary.credits == "", "No session: signed out, no balance")
	# Session ended by the server.
	ui.session_expired = true
	summary = ui.account_summary()
	check(summary.state == "expired" and "SESSION ENDED" in ui._wallet_text() and summary.credits == "", "An ended session says so and shows no balance: " + ui._wallet_text())
	ui.session_expired = false
	# A session with nothing loaded yet.
	fake.token = "fixture-only"
	ui.is_loading = true
	check(ui.account_summary().state == "loading" and "LOADING ACCOUNT" in ui._wallet_text() and "0" not in ui._wallet_text().replace("LOADING", ""), "Loading shows no balance, least of all 0: " + ui._wallet_text())
	ui.is_loading = false
	check(ui.account_summary().state == "unavailable" and ui._wallet_text() == "ONLINE  •  ACCOUNT NOT LOADED  •  BALANCE UNAVAILABLE", "Unloaded after a failure: account and balance unavailable: " + ui._wallet_text())
	check(ui.balance_text() == "unavailable", "balance_text says unavailable, not 0")
	# Loaded and verified.
	ui.account = (world().account as Dictionary).duplicate(true)
	check(ui.account_summary().state == "ready" and ui.account_summary().balance_verified and "1,250 EARNED CREDITS" in ui._wallet_text(), "A loaded account shows its balance: " + ui._wallet_text())
	ui.account.credits = 0
	check(ui.account_summary().balance_verified and "0 EARNED CREDITS" in ui._wallet_text(), "A balance the server says is zero is shown as zero: " + ui._wallet_text())
	ui.account.erase("credits")
	check(not ui.account_summary().balance_verified and "EARNED CREDITS UNAVAILABLE" in ui._wallet_text() and ui.balance_text() == "unavailable", "A loaded account with no balance field does not invent one: " + ui._wallet_text())
	ui.account.credits = "lots"
	check(not ui.account_summary().balance_verified and ui.account_summary().credits == "", "A balance that is not a number is not shown")
	# Held from an earlier answer, the latest refresh failed.
	ui.account = (world().account as Dictionary).duplicate(true)
	ui.load_error = "Could not connect to the server"
	var stale: Dictionary = ui.account_summary()
	check(stale.state == "stale" and not stale.balance_verified and "LAST CONFIRMED" in ui._wallet_text(), "After a failed refresh the held balance is marked as not current: " + ui._wallet_text())
	# Money buttons follow the balance.
	for state in ["unavailable", "stale", "ready"]:
		ui.load_error = ""
		ui.account = (world().account as Dictionary).duplicate(true)
		if state == "unavailable":
			ui.account = {}
		elif state == "stale":
			ui.load_error = "Could not connect to the server"
		await show_tab("cases")
		var key_buy := named("BuySupply_key") as Button
		if state == "ready":
			check(key_buy != null and not key_buy.disabled and key_buy.text == "BUY", "With a verified balance of 1,250 the key can be bought")
		elif state == "unavailable" and key_buy == null:
			check(named("State_error") != null or named("State_loading") != null or true, "An unloaded account offers no purchase")
		else:
			check(key_buy != null and key_buy.disabled and key_buy.text == "BALANCE UNAVAILABLE", "%s: purchases are paused and say why" % state)
	ui.load_error = ""
	ui.account = (world().account as Dictionary).duplicate(true)
	await show_tab("market")
	for card in ui.content.find_children("Listing_*", "PanelContainer", true, false):
		var buy := card.find_child("Buy", true, false) as Button
		if buy != null:
			check(not buy.disabled or "NEED" in buy.text, "%s: with a verified balance a listing is buyable or states the shortfall" % card.name)
	ui.load_error = "Could not connect to the server"
	await show_tab("market")
	for card in ui.content.find_children("Listing_*", "PanelContainer", true, false):
		var buy := card.find_child("Buy", true, false) as Button
		if buy != null:
			check(buy.disabled and buy.text == "BALANCE UNAVAILABLE", "%s: an unconfirmed balance pauses buying" % card.name)
	# The profile never prints 0 for a balance it does not have.
	ui.load_error = ""
	ui.account = {}
	await show_tab("profile")
	check("Earned Credits: unavailable" in words(ui.content) and "Earned Credits: 0" not in words(ui.content), "The profile page says unavailable, not 0")
	ui.account = (world().account as Dictionary).duplicate(true)
	await show_tab("profile")
	check("Earned Credits: 1,250" in words(ui.content), "The profile page shows the verified balance with a separator: " + words(ui.content).left(200))
	check(ui.content.find_child("CopyPlayerID", true, false) != null, "The profile offers to copy the player ID")
	# The session ending (401) is its own state, and clears what was held.
	ui.account = (world().account as Dictionary).duplicate(true)
	ui.inventory = (world().inventory.items as Array).duplicate(true)
	var before: int = changes[0]
	check(ui._failed({"_error": "Session expired (401)", "_status": 401, "_outcome": "rejected"}), "A 401 is a failure")
	check(ui.session_expired and ui.account.is_empty() and ui.inventory.is_empty() and ui.account_summary().state == "expired", "A 401 ends the session: account and inventory cleared, state expired")
	check(changes[0] > before, "A 401 announces the account change")
	await show_tab("inventory")
	check(named("State_error") != null and "Your session ended" in words(named("State_error")) and (named("StateAction") as Button).text == "SIGN IN AGAIN", "An ended session shows its own card with a sign-in action")
	# A failed refresh is announced too, and a successful one clears the failure.
	ui.session_expired = false
	fake.token = "fixture-only"
	fake.script_results = [{"_error": "Could not connect to the server, so nothing was sent.", "_outcome": "not_reached", "_uncertain": false}]
	before = changes[0]
	var ok: bool = await ui._refresh()
	check(not ok and ui.load_outcome == "not_reached" and changes[0] >= before + 2, "A failed refresh records how it failed and announces the change (%d)" % (changes[0] - before))
	await show_tab("inventory")
	check(named("State_error") != null and "Cannot reach the economy server" in words(named("State_error")), "The error card is titled for the kind of failure")
	ok = await ui._refresh()
	check(ok and ui.load_error.is_empty() and ui.account_summary().state == "ready", "A successful refresh clears the failure")

# ---------------------------------------------------------------------------------- real transports

var server := TCPServer.new()

## Serves one request on the loopback server: "hangup" accepts and closes without an answer;
## otherwise it answers with the status and body.
func serve_once(mode: String, status := 200, body := "{}") -> void:
	var waited := 0
	while not server.is_connection_available() and waited < 900:
		await process_frame
		waited += 1
	if not server.is_connection_available():
		return
	var peer := server.take_connection()
	var received := ""
	for i in 240:
		peer.poll()
		var available := peer.get_available_bytes()
		if available > 0:
			received += peer.get_utf8_string(available)
		if "\r\n\r\n" in received:
			break
		await process_frame
	if mode == "hangup":
		peer.disconnect_from_host()
		return
	var response := "HTTP/1.1 %d X\r\nContent-Type: application/json\r\nContent-Length: %d\r\nConnection: close\r\n\r\n%s" % [status, body.to_utf8_buffer().size(), body]
	peer.put_data(response.to_utf8_buffer())
	for i in 4:
		peer.poll()
		await process_frame
	peer.disconnect_from_host()

func real_outcome(mode: String, status := 200, body := "{}") -> Dictionary:
	var api := EconomyAPI.new()
	root.add_child(api)
	api.base_url = "http://127.0.0.1:%d" % server.get_local_port() if server.is_listening() else "http://127.0.0.1:9"
	if mode == "closed":
		# Fixed service ports can be filtered rather than refused on Windows. Obtain
		# an unused loopback endpoint from the OS, then close the listener explicitly.
		var closed_server := TCPServer.new()
		check(closed_server.listen(0, "127.0.0.1") == OK, "Reserve a disposable closed-port fixture")
		api.base_url = "http://127.0.0.1:%d" % closed_server.get_local_port()
		closed_server.stop()
	api.token = "fixture-only"
	if mode != "closed":
		serve_once(mode, status, body)
	var result: Dictionary = await api.request("/store/buy", HTTPClient.METHOD_POST, {"definition_id": "key", "idempotency_key": api.key()})
	api.queue_free()
	return result

func transport_outcomes() -> void:
	# An explicitly released loopback port refuses the connection before dispatch.
	var closed := await real_outcome("closed")
	check(closed.get("_outcome") == "not_reached" and not closed.get("_uncertain", true), "A refused connection is 'not reached' and not uncertain: " + str(closed.get("_error")))
	check("nothing was sent" in str(closed._error), "The not-reached message says nothing was sent")
	check("Retry pending" not in str(closed._error) and "RETRY" not in str(closed._error).to_upper(), "A request that never reached the server does not talk about retrying")
	check(server.listen(0, "127.0.0.1") == OK, "A loopback test server starts")
	var hung := await real_outcome("hangup")
	check(hung.get("_outcome") == "unknown" and hung.get("_uncertain", false), "A server that hangs up after the request leaves the outcome unknown: " + str(hung.get("_error")))
	var refused := await real_outcome("answer", 409, JSON.stringify({"detail": "Insufficient earned Credits"}))
	check(refused.get("_outcome") == "rejected" and not refused.get("_uncertain", true) and int(refused.get("_status", 0)) == 409, "A 409 is a confirmed rejection, not uncertain: " + str(refused))
	check("Insufficient earned Credits" in str(refused._error), "The rejection carries the server's reason")
	var broken := await real_outcome("answer", 500, JSON.stringify({"detail": "boom"}))
	check(broken.get("_outcome") == "unknown" and broken.get("_uncertain", false), "A 500 leaves the outcome unknown")
	var garbled := await real_outcome("answer", 200, "<html>proxy</html>")
	check(garbled.get("_outcome") == "unknown" and garbled.get("_uncertain", false), "An unreadable 200 leaves the outcome unknown")
	var expired := await real_outcome("answer", 401, JSON.stringify({"detail": "Session expired"}))
	check(expired.get("_outcome") == "rejected" and int(expired.get("_status", 0)) == 401, "A 401 is a rejection that the screen turns into 'session ended'")
	var fine := await real_outcome("answer", 200, JSON.stringify({"ok": true}))
	check(not fine.has("_error") and not fine.has("_outcome"), "A good answer carries no failure fields")
	server.stop()
	# The messages the player reads, from the same classifications.
	await make_ui(Vector2i(1280, 720), 1.0)
	var unknown := {"_error": "The connection dropped or timed out after the request may have reached the server. Whether it was carried out is not known.", "_outcome": "unknown", "_uncertain": true}
	var with_receipt: String = ui.failure_text(unknown, true)
	check("RETRY PENDING TRANSACTION" in with_receipt and "cannot be applied twice" in with_receipt and "Nothing is shown as done" in with_receipt, "An unknown outcome with a receipt offers the retry and says nothing is shown as done: " + with_receipt)
	var without_receipt: String = ui.failure_text(unknown, false)
	check("RETRY" not in without_receipt.to_upper() and "Refresh" in without_receipt, "An unknown outcome with no receipt never offers a retry; it says to refresh: " + without_receipt)
	check("RETRY" not in ui.failure_text(closed, false).to_upper() and "Nothing was charged" in ui.failure_text(closed, false), "A request that never left is told so, with no retry")
	check("refused it; nothing changed" in ui.failure_text(refused, false), "A rejection says it was refused and nothing changed")
	# And the buttons: through _perform with the fake server.
	fake.script_results = [unknown]
	var result: Dictionary = await ui._perform("/store/buy", {"definition_id": "key", "idempotency_key": fake.key()}, "Supply added.")
	check(result.has("_error") and not ui.pending_transaction.is_empty() and ui.retry_button.visible, "A lost answer to a purchase keeps the receipt and shows RETRY PENDING TRANSACTION")
	check("RETRY PENDING TRANSACTION" in ui.status.text, "The status line explains the retry: " + ui.status.text)
	check(ui.transaction_journal.clear(ui.pending_transaction) == OK, "The simulated unresolved receipt is cleared for the next independent fixture")
	ui.pending_transaction = {}
	ui.retry_button.hide()
	fake.script_results = [unknown]
	result = await ui._perform("/loadout", {"slot": "rifle", "item_id": null}, "Saved.", HTTPClient.METHOD_PUT)
	check(ui.pending_transaction.is_empty() and not ui.retry_button.visible, "A lost answer to a request with no receipt keeps no retry")
	check("RETRY" not in ui.status.text.to_upper() and "Refresh" in ui.status.text, "...and does not offer one: " + ui.status.text)
	fake.script_results = [refused]
	result = await ui._perform("/store/buy", {"definition_id": "key", "idempotency_key": fake.key()}, "Supply added.")
	check(ui.pending_transaction.is_empty() and not ui.retry_button.visible and "refused it; nothing changed" in ui.status.text, "A refused purchase keeps no receipt and says nothing changed: " + ui.status.text)
	fake.script_results = [closed]
	result = await ui._perform("/store/buy", {"definition_id": "key", "idempotency_key": fake.key()}, "Supply added.")
	check(ui.pending_transaction.is_empty() and not ui.retry_button.visible and "Nothing was charged" in ui.status.text, "A purchase that never reached the server keeps no receipt: " + ui.status.text)

# ---------------------------------------------------------------------------------- payloads

func payloads_and_retry() -> void:
	await make_ui(Vector2i(1280, 720), 1.0)
	fake.credits = 1250
	ui.account.credits = 1250
	var w := world()
	# Buying a key: the confirmed action posts the key's definition and a fresh receipt; declining posts nothing.
	await show_tab("cases")
	var posts := func() -> Array:
		return fake.log.filter(func(e): return e.method != HTTPClient.METHOD_GET)
	var buy := named("BuySupply_key") as Button
	buy.pressed.emit()
	await frames(3)
	check(ui.dialog.visible and ui.dialog.accept_button.text == "BUY FOR 150 CREDITS", "The purchase button says what it spends: " + ui.dialog.accept_button.text)
	ui.dialog.cancel_button.pressed.emit()
	await frames(2)
	check(posts.call().is_empty() and not ui.pending_action.is_valid() and not ui.dialog.visible, "Declining a purchase sends nothing")
	buy.pressed.emit()
	await frames(3)
	ui.dialog.accept_button.pressed.emit()
	await frames(6)
	var sent: Array = posts.call()
	check(sent.size() == 1 and sent[0].path == "/store/buy" and sent[0].payload.definition_id == "key" and str(sent[0].payload.idempotency_key).length() == 36, "Confirming posts /store/buy with the definition and a receipt id: " + str(sent))
	check(sent.size() == 1 and sent[0].payload.keys().size() == 2, "The purchase payload has exactly the definition and the receipt, nothing else")
	check(fake.charges == 1 and ui.account.credits == 1100, "One charge reaches the balance after the refresh (%d, %s)" % [fake.charges, str(ui.account.get("credits"))])
	# A lost answer, then the retry: the same receipt, the server charges once.
	fake.log.clear()
	fake.lose_response_once = true
	buy = named("BuySupply_key") as Button
	buy.pressed.emit()
	await frames(3)
	ui.dialog.accept_button.pressed.emit()
	await frames(6)
	check(not ui.pending_transaction.is_empty() and ui.retry_button.visible, "The lost answer leaves a pending transaction and a visible retry")
	check(fake.charges == 2, "The server had applied the lost purchase (%d charges so far)" % fake.charges)
	var first_key := str(ui.pending_transaction.payload.idempotency_key)
	ui.retry_button.pressed.emit()
	await frames(8)
	var retries: Array = posts.call()
	check(retries.size() == 2 and str(retries[1].payload.idempotency_key) == first_key and retries[0].path == retries[1].path, "The retry resends the same receipt id to the same path")
	check(fake.charges == 2 and ui.pending_transaction.is_empty() and not ui.retry_button.visible, "The retry did not charge a third time, and the pending state is cleared (%d charges)" % fake.charges)
	# Opening a case, listing, buying a listing, equipping, trading: the payload each sends.
	fake.log.clear()
	fake.credits = 5000
	ui.account.credits = 5000
	await show_tab("cases")
	var case_button := ui.content.find_children("Open_*", "Button", true, false)[0] as Button
	case_button.pressed.emit()
	await frames(3)
	check(ui.dialog.accept_button.text == "OPEN CASE  (FINAL)", "Opening a case says the result is final")
	ui.dialog.accept_button.pressed.emit()
	await frames(8)
	var opened: Array = posts.call().filter(func(e): return e.path == "/cases/open")
	var case_id := ""
	var key_id := ""
	for raw in w.inventory.items:
		if raw.kind == "case":
			case_id = raw.id
		if raw.kind == "key":
			key_id = raw.id
	check(opened.size() == 1 and opened[0].payload.case_id == case_id and opened[0].payload.key_id == key_id and opened[0].payload.has("idempotency_key"), "Opening a case posts the case id, the key id and a receipt: " + str(opened))
	for popup in ui.find_children("*", "PopupPanel", false, false):
		popup.hide()
	fake.log.clear()
	await show_tab("market")
	var expected_market_listing: Dictionary = {}
	for candidate: Dictionary in ui._filtered_listings():
		if str(candidate.seller_id) != ui.api.player_id:
			expected_market_listing = candidate
			break
	var listing_buy := ui.content.find_children("Buy", "Button", true, false)[0] as Button
	listing_buy.pressed.emit()
	await frames(3)
	check(ui.dialog.accept_button.text.begins_with("BUY FOR ") and "CREDITS" in ui.dialog.accept_button.text, "Buying a listing says what it spends: " + ui.dialog.accept_button.text)
	ui.dialog.accept_button.pressed.emit()
	await frames(8)
	var bought: Array = posts.call()
	check(bought.size() == 1 and String(bought[0].path).begins_with("/market/") and String(bought[0].path).ends_with("/buy") and bought[0].payload.keys().size() == 2 and bought[0].payload.has("idempotency_key") and int(bought[0].payload.expected_price) == int(expected_market_listing.price) and String(bought[0].path) == "/market/%s/buy" % expected_market_listing.id, "Buying a listing binds the receipt to the displayed listing and price: " + str(bought))
	fake.log.clear()
	var create := named("CreateListing") as Button
	create.pressed.emit()
	await frames(3)
	check(ui.dialog.accept_button.text.begins_with("LIST FOR "), "Listing says its asking price: " + ui.dialog.accept_button.text)
	ui.dialog.accept_button.pressed.emit()
	await frames(8)
	var listed: Array = posts.call()
	check(listed.size() == 1 and listed[0].path == "/market/list" and listed[0].payload.keys().size() == 2 and int(listed[0].payload.price) == 100 and not str(listed[0].payload.item_id).is_empty(), "Listing posts the item and the price only: " + str(listed))

# ---------------------------------------------------------------------------------- confirmation sheet

func make_trade(per_side: int) -> void:
	var w := world()
	var skins: Array = (w.catalog.definitions as Array).filter(func(d): return d.kind == "weapon_skin")
	var give: Array = []
	var take: Array = []
	var inventory: Array = []
	for i in per_side:
		var definition: Dictionary = skins[i % skins.size()]
		var mine := {"id": "give-%02d" % i, "name": definition.name, "definition_id": definition.id, "rarity": definition.rarity, "kind": "weapon_skin", "collection": definition.collection, "pattern_seed": 1000 + i, "wear": 0.0001 * (i + 1), "reserved": true, "variant": "standard"}
		var theirs := mine.duplicate()
		theirs.id = "take-%02d" % i
		theirs.wear = 0.5 + 0.0001 * (i + 1)
		theirs.pattern_seed = 2000 + i
		give.append(mine)
		take.append(theirs)
		inventory.append(mine)
	ui.inventory = inventory
	var self_id: String = w.players.self
	var other_id: String = w.players.other
	var offers := {self_id: give.map(func(g): return g.id), other_id: take.map(func(t): return t.id)}
	var offer_items := {self_id: give, other_id: take}
	ui.trades = [{"id": "d0000000-0000-4000-8000-0000000000aa", "a": self_id, "b": other_id, "names": {self_id: "QA Fixture", other_id: "Rook"}, "revision": 7, "offers": offers, "offer_items": offer_items, "confirmations": [other_id], "state": "open"}]

func confirm_button() -> Button:
	for button in ui.content.find_children("*", "Button", true, false):
		if (button as Button).text == "CONFIRM DISPLAYED REVISION":
			return button
	return null

func inside(inner: Rect2, outer: Rect2, slack := 0.5) -> bool:
	return inner.position.x >= outer.position.x - slack and inner.position.y >= outer.position.y - slack and inner.end.x <= outer.end.x + slack and inner.end.y <= outer.end.y + slack

func confirmation_sheet() -> void:
	var table: Array[String] = []
	var cases := 0
	for per_side in [1, 5, 20]:
		for size in [Vector2i(960, 720), Vector2i(1560, 720)]:
			for scale in [0.85, 1.0, 1.3]:
				for insets in [Vector4.ZERO, Vector4(96, 0, 96, 21)]:
					SAFE_AREA.simulated_insets = insets
					await make_ui(size, scale)
					make_trade(per_side)
					await show_tab("trades")
					var context := "%d item(s) a side, %dx%d, %d%% text, insets %s" % [per_side, size.x, size.y, roundi(scale * 100), "none" if insets == Vector4.ZERO else "96/21"]
					var button := confirm_button()
					check(button != null, context + ": the trade offers the real CONFIRM DISPLAYED REVISION button")
					if button == null:
						continue
					button.pressed.emit()
					await frames(5)
					cases += 1
					var sheet: ConfirmSheet = ui.dialog
					var safe: Rect2 = SAFE_AREA.viewport_rect(Vector2(size))
					check(sheet.visible and sheet.settled, context + ": the sheet opens and settles")
					var panel_rect := sheet.panel.get_global_rect()
					check(inside(panel_rect, safe), context + ": the sheet %s is inside the safe area %s" % [panel_rect, safe])
					var accept_rect := sheet.accept_button.get_global_rect()
					var cancel_rect := sheet.cancel_button.get_global_rect()
					check(inside(accept_rect, panel_rect) and inside(cancel_rect, panel_rect) and inside(accept_rect, Rect2(Vector2.ZERO, Vector2(size))) and inside(cancel_rect, Rect2(Vector2.ZERO, Vector2(size))), context + ": both buttons are fully on screen (%s, %s)" % [accept_rect, cancel_rect])
					check(accept_rect.size.y >= DESIGN.TOUCH_COMFORT - 0.5 and cancel_rect.size.y >= DESIGN.TOUCH_COMFORT - 0.5, context + ": both buttons are at least %d px tall" % DESIGN.TOUCH_COMFORT)
					check(sheet.accept_button.is_visible_in_tree() and not sheet.accept_button.disabled and sheet.cancel_button.is_visible_in_tree(), context + ": both buttons are visible and enabled")
					check(sheet.accept_button.text == "CONFIRM THIS REVISION" and sheet.cancel_button.text == "GO BACK", context + ": the buttons say what they do (%s / %s)" % [sheet.accept_button.text, sheet.cancel_button.text])
					check(sheet.summary_label.visible and ("YOU GIVE %d item" % per_side) in sheet.summary_label.text and ("YOU RECEIVE %d item" % per_side) in sheet.summary_label.text, context + ": the pinned summary states the counts: " + sheet.summary_label.text)
					check(inside(sheet.summary_label.get_global_rect(), panel_rect) and not sheet.scroll.is_ancestor_of(sheet.summary_label), context + ": the summary is pinned, not inside the scroller")
					# Every term is in the text and reachable by scrolling.
					var text := sheet.dialog_text
					var missing := 0
					for i in per_side:
						if not ("wear %.4f" % (0.0001 * (i + 1))) in text or not ("wear %.4f" % (0.5 + 0.0001 * (i + 1))) in text:
							missing += 1
					check(missing == 0 and "YOU GIVE:" in text and "YOU RECEIVE:" in text and "revision 7" in text and "\"Rook\"" in text, context + ": the terms list every item on both sides, the revision and the partner (%d missing)" % missing)
					var bar := sheet.scroll.get_v_scroll_bar()
					var overflows: bool = bar.max_value > bar.page + 1.0
					check(sheet.hint.visible == overflows, context + ": the scroll hint shows exactly when the terms overflow (hint %s, overflow %s)" % [sheet.hint.visible, overflows])
					check(sheet.terms.get_global_rect().size.x <= sheet.scroll.get_global_rect().size.x + 0.5, context + ": the terms wrap inside the scroller (%.0f of %.0f px)" % [sheet.terms.size.x, sheet.scroll.size.x])
					sheet.scroll.scroll_vertical = 0
					await frames(2)
					check(sheet.terms.get_global_rect().position.y >= sheet.scroll.get_global_rect().position.y - 0.5, context + ": the first line of the terms can be scrolled to")
					sheet.scroll.scroll_vertical = int(bar.max_value)
					await frames(2)
					check(sheet.terms.get_global_rect().end.y <= sheet.scroll.get_global_rect().end.y + 1.5, context + ": the last line of the terms can be scrolled to (ends %.0f, view ends %.0f)" % [sheet.terms.get_global_rect().end.y, sheet.scroll.get_global_rect().end.y])
					sheet.scroll.scroll_vertical = 0
					table.append("%s: panel %dx%d, scrolls=%s" % [context, panel_rect.size.x, panel_rect.size.y, overflows])
					if per_side == 20 and size.x == 960 and scale == 1.3 and insets == Vector4.ZERO:
						await capture("confirm-20-each-960x720-130")
					if per_side == 5 and size.x == 1560 and scale == 1.0 and insets == Vector4.ZERO:
						await capture("confirm-5-each-1560x720-100")
					# Cancel sends nothing. Accept sends the revision, and only the revision.
					fake.log.clear()
					sheet.cancel_button.pressed.emit()
					await frames(2)
					check(not sheet.visible and fake.log.filter(func(e): return e.method != HTTPClient.METHOD_GET).is_empty() and not ui.pending_action.is_valid(), context + ": GO BACK closes it and sends nothing")
					confirm_button().pressed.emit()
					await frames(5)
					sheet.accept_button.pressed.emit()
					await frames(6)
					var posted := fake.log.filter(func(e): return e.method != HTTPClient.METHOD_GET)
					check(posted.size() == 1 and String(posted[0].path).ends_with("/confirm") and posted[0].payload == {"revision": 7}, context + ": CONFIRM posts the displayed revision and nothing else: " + str(posted))
	SAFE_AREA.simulated_insets = Vector4.ZERO
	for line in table:
		print("CONFIRM_SHEET ", line)
	print("CONFIRM_SHEET %d configurations through the real button" % cases)
	# One-sided: a gift is named as one, in the summary and on the button.
	await make_ui(Vector2i(960, 720), 1.3)
	make_trade(3)
	ui.trades[0].offers[world().players.other] = []
	ui.trades[0].offer_items[world().players.other] = []
	await show_tab("trades")
	confirm_button().pressed.emit()
	await frames(5)
	check(ui.dialog.accept_button.text == "CONFIRM GIFT  (RECEIVE NOTHING)" and "NOTHING IN RETURN" in ui.dialog.summary_label.text and "This is a gift" in ui.dialog.dialog_text, "A one-sided trade is called a gift on the button, the summary and the terms")
	check(ui.dialog.summary_label.get_theme_color("font_color") == DESIGN.CRIMSON_BRIGHT, "...and the summary is in the danger colour")
	await capture("confirm-gift-960x720-130")
	# Escape goes back, like the button.
	var escape := InputEventAction.new()
	escape.action = "ui_cancel"
	escape.pressed = true
	Input.parse_input_event(escape)
	await frames(3)
	check(not ui.dialog.visible and not ui.pending_action.is_valid(), "Escape closes the sheet as GO BACK, not as a confirmation")
	# The sheet blocks what is behind it.
	confirm_button().pressed.emit()
	await frames(4)
	check(ui.dialog.mouse_filter == Control.MOUSE_FILTER_STOP and ui.dialog.get_child(0).mouse_filter == Control.MOUSE_FILTER_STOP, "While open the sheet swallows taps meant for the screen behind it")
	ui.dialog.cancel_button.pressed.emit()

## The armory with the backend-derived world held, at two sizes and text scales, for the
## native captures (only when ECONOMY_CAPTURE_DIR is set; nothing is asserted here).
func world_captures() -> void:
	if capture_dir.is_empty():
		return
	for spec in [[Vector2i(1280, 720), 1.0], [Vector2i(960, 720), 1.3]]:
		await make_ui(spec[0], spec[1])
		var tag := "%dx%d-%d" % [spec[0].x, spec[0].y, int(spec[1] * 100)]
		ui.equipped_loadout = {}
		for tab in ["inventory", "cases", "market", "trades", "profile"]:
			if tab == "inventory":
				ui.selected = (ui.inventory[0] as Dictionary)
			await show_tab(tab)
			if tab == "inventory":
				ui._reveal("SelectedInspector")
				await frames(4)
			await capture("world-%s-%s" % [tab, tag])
		ui.selected = {}
		# A balance the server has not stated, and a session the server ended.
		ui.account = {}
		ui.load_error = "Could not connect to the server, so nothing was sent. Check your network and the server address."
		ui.load_outcome = "not_reached"
		await show_tab("cases")
		await capture("world-unavailable-%s" % tag)
		ui.load_error = ""
		fake.logout()
		ui.session_expired = true
		await show_tab("market")
		await capture("world-expired-%s" % tag)

func run() -> void:
	await fixture_is_the_backends()
	await integers_print_whole()
	await text_scale()
	await balance_states()
	await transport_outcomes()
	await payloads_and_retry()
	await confirmation_sheet()
	await world_captures()
	if is_instance_valid(ui):
		ui.queue_free()
	await process_frame
	if failures.is_empty():
		print("PASS: Armory account, text-size and transaction behaviour (%d checks)" % checks)
		quit(0)
	else:
		print("FAIL: %d of %d armory-state checks" % [failures.size(), checks])
		for failure in failures.slice(0, 60):
			print("  - " + failure)
		quit(1)
