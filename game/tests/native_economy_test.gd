## Real isolated HTTP/PostgreSQL transaction review; trusted fictional seed balances only.
extends SceneTree
var count := 0
var failures := 0
func _initialize(): call_deferred("run")
func check(ok: bool, message: String):
	count += 1
	if not ok:
		failures += 1
		push_error(message)
func run():
	root.size = Vector2i(1280,720)
	var fixtures: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(OS.get_environment("SIGHTBREAK_NATIVE_FIXTURE")))
	var scene = load("res://scripts/ui/economy_ui.gd")
	var a = scene.new()
	var b = scene.new()
	a.transaction_journal.path = "user://native_economy_a_%d.json" % OS.get_process_id()
	b.transaction_journal.path = "user://native_economy_b_%d.json" % OS.get_process_id()
	root.add_child(a)
	root.add_child(b)
	for pair in [[a,"a"],[b,"b"]]:
		pair[0].api.base_url = fixtures.api_url
		pair[0].api.token = fixtures["token_"+pair[1]]
		pair[0].api.player_id = fixtures[pair[1]]
		pair[0].reduced_motion = true
		await pair[0]._refresh()
	check(a.inventory.size()==3 and b.inventory.is_empty(), "real fixture inventory fetched")
	var equipment: Dictionary = await a._perform("/loadout", {"slot":"rifle", "item_id":fixtures.skin}, "equip", HTTPClient.METHOD_PUT)
	check(equipment.get("slots", {}).get("rifle", {}).get("id")==fixtures.skin and a.equipped_loadout.get("rifle", {}).get("id")==fixtures.skin, "native equip persists and refreshes cosmetic loadout")
	a.active_tab = "cases"
	var case_item: Dictionary
	var key_item: Dictionary
	for owned in a.inventory:
		if owned.id == fixtures.case: case_item=owned
		if owned.id == fixtures.key: key_item=owned
	await a._open_case(case_item,key_item)
	check(a.inventory.size()==2,"case consumes case+key and adds one result")
	check(a.selected.get("kind")=="weapon_skin" and a.selected.has("id"),"case reveal displays actual minted instance")
	var reward_id: String = a.selected.id
	var listing: Dictionary = await a._perform("/market/list", {"item_id": reward_id, "price": 400})
	check(listing.has("id"),"real native listing confirms")
	if not listing.has("id"): quit(1); return
	b.active_tab = "market"
	await b._refresh()
	check(b.listings.any(func(l): return l.id==listing.id),"buyer sees committed listing")
	var purchase: Dictionary = await b._perform("/market/%s/buy" % listing.id, {"idempotency_key": b.api.key(), "expected_price": int(listing.price)})
	check(not purchase.has("_error") and int(b.account.credits)==1600,"buyer native wallet refresh reflects debit")
	await a._refresh()
	check(int(a.account.credits)==2388,"seller wallet receives400minus12fee")
	check(a.inventory.size()==1 and b.inventory.size()==1,"ownership refresh shows unique buyer item")
	a.active_tab = "trades"
	b.active_tab = "trades"
	var trade: Dictionary = await a._perform("/trades", {"partner_id": fixtures.b})
	check(trade.has("id"),"native trade created")
	if not trade.has("id"): quit(1); return
	var path := "/trades/%s" % trade.id
	var first: Dictionary = await a._perform(path+"/offer", {"revision":0,"item_ids":[fixtures.skin]}, "offer", HTTPClient.METHOD_PUT)
	var second: Dictionary = await b._perform(path+"/offer", {"revision":1,"item_ids":[reward_id]}, "offer", HTTPClient.METHOD_PUT)
	check(int(first.get("revision",-1))==1 and int(second.get("revision",-1))==2,"native offer revisions verified")
	# Player A confirms through the real CONFIRM DISPLAYED REVISION button and the bounded sheet.
	var one: Dictionary = await confirm_through_the_sheet(a, trade.id, fixtures.skin, reward_id)
	var two: Dictionary = await b._perform(path+"/confirm", {"revision":2})
	check(one.get("state")=="open" and two.get("state")=="completed","native two-sided confirmation settles")
	await a._refresh()
	check(a.inventory.size()==1 and a.inventory[0].id==reward_id and b.inventory.size()==1 and b.inventory[0].id==fixtures.skin,"native inventory refresh reflects both atomic ownership swaps")
	check(a.equipped_loadout.is_empty(), "native loadout automatically clears transferred item")
	await account_states_against_the_real_server(a, b, fixtures)
	print("NATIVE_REAL_ECONOMY_QA %d/%d passed (real case reveal, marketplace, trade, account states, rejection, 401, replay, sheet; fictional isolated balances)" % [count-failures,count])
	a.queue_free(); b.queue_free()
	await process_frame
	await process_frame
	quit(0 if failures==0 else 1)

func frames(n: int) -> void:
	for i in n:
		await process_frame

func words(node: Node) -> String:
	var parts: Array[String] = []
	for label in node.find_children("*", "Label", true, false):
		parts.append((label as Label).text)
	for button in node.find_children("*", "Button", true, false):
		parts.append((button as Button).text)
	return "  ".join(parts)

## The round-2 account, failure and confirmation behaviour, on responses the real API sends.
func account_states_against_the_real_server(a, b, fixtures: Dictionary) -> void:
	var UI = load("res://scripts/ui/economy_ui.gd")
	var pattern := RegEx.create_from_string("(^|[^0-9.])[0-9]+\\.0([^0-9]|$)")
	# The account as the server states it.
	await a._refresh()
	var me: Dictionary = await a.api.request("/me")
	var summary: Dictionary = a.account_summary()
	check(summary.state == "ready" and summary.balance_verified and summary.credits == UI.credits_text(int(me.credits)), "the header's balance is the server's /me balance (%s)" % summary.credits)
	check(a.wallet.text.contains(summary.credits + " EARNED CREDITS"), "the wallet line shows it: " + a.wallet.text)
	# Real catalog shapes: odds in rarity order, no stray .0 anywhere on any tab.
	var probabilities: Dictionary = a.catalog.case_tables.probabilities
	check(a.rarities_in_order(probabilities) == ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic"], "the real odds sort commonest first: " + str(a.rarities_in_order(probabilities)))
	check(a.catalog.definitions.filter(func(d): return d.kind == "weapon_skin").size() == 24, "the real catalog lists 24 finishes")
	for tab in ["inventory", "cases", "market", "trades", "profile"]:
		a.active_tab = tab
		a.selected = a.inventory[0] if not a.inventory.is_empty() else {}
		a._render()
		await frames(3)
		var match := pattern.search(words(a))
		check(match == null, "%s: nothing the real server sent prints with a trailing .0" % tab)
	a.selected = {}
	# A real rejection: opening a case with items the player does not own.
	a.pending_transaction = {}
	var refused: Dictionary = await a._perform("/cases/open", {"case_id": fixtures.skin, "key_id": fixtures.skin, "idempotency_key": a.api.key()}, "x")
	check(refused.has("_error") and refused.get("_outcome") == "rejected" and int(refused.get("_status", 0)) in [404, 409, 422], "a real refusal is classified as rejected (%s)" % str(refused.get("_status")))
	check(a.pending_transaction.is_empty() and not a.retry_button.visible and "refused it; nothing changed" in a.status.text, "...keeps no receipt and says nothing changed: " + a.status.text)
	# The real server's replay of one receipt id charges once.
	var before: Dictionary = await a.api.request("/me")
	var key: String = a.api.key()
	var first: Dictionary = await a.api.request("/store/buy", HTTPClient.METHOD_POST, {"definition_id": "key", "idempotency_key": key})
	var second: Dictionary = await a.api.request("/store/buy", HTTPClient.METHOD_POST, {"definition_id": "key", "idempotency_key": key})
	var after: Dictionary = await a.api.request("/me")
	check(not first.has("_error") and not second.has("_error") and int(before.credits) - int(after.credits) == 150, "the same receipt id sent twice is charged once (%d -> %d)" % [int(before.credits), int(after.credits)])
	# A real, unreachable server: the held account is stale, the balance unconfirmed, nothing invented.
	var good_url: String = a.api.base_url
	a.api.base_url = "http://127.0.0.1:9"
	var ok: bool = await a._refresh()
	check(not ok and a.load_outcome == "not_reached" and a.account_summary().state == "stale" and not a.account_summary().balance_verified, "an unreachable server leaves the held balance marked unconfirmed")
	check(a.wallet.text.contains("LAST CONFIRMED"), "...and the header says so: " + a.wallet.text)
	a.api.base_url = good_url
	ok = await a._refresh()
	check(ok and a.account_summary().state == "ready", "the next successful refresh confirms it again")
	# A real 401: a session the server does not know ends the session on screen.
	var token: String = a.api.token
	var player: String = a.api.player_id
	a.api.token = "not-a-session"
	ok = await a._refresh()
	check(not ok and a.session_expired and a.account_summary().state == "expired" and a.account.is_empty(), "a session the server rejects (401) ends the session on screen")
	check(a.wallet.text.begins_with("SESSION ENDED"), "...and the header says: " + a.wallet.text)
	a.api.token = token
	a.api.player_id = player
	a.session_expired = false
	await a._refresh()

## Player `ui` confirms the real trade through the real button: the sheet opens inside the screen
## with both real items in its terms and the real revision, its pinned summary states the counts,
## and accepting it records the confirmation on the real server. Returns the server's trade.
func confirm_through_the_sheet(ui, trade_id: String, own_item: String, partner_item: String) -> Dictionary:
	var pattern := RegEx.create_from_string("(^|[^0-9.])[0-9]+\\.0([^0-9]|$)")
	ui.active_tab = "trades"
	await ui._refresh()
	ui._render()
	await frames(3)
	var button: Button
	for candidate in ui.content.find_children("*", "Button", true, false):
		if (candidate as Button).text == "CONFIRM DISPLAYED REVISION":
			button = candidate
	check(button != null, "the real trade shows the real CONFIRM DISPLAYED REVISION button")
	if button == null:
		return {}
	button.pressed.emit()
	await frames(5)
	var sheet = ui.dialog
	var screen := Rect2(Vector2.ZERO, Vector2(root.size))
	check(sheet.visible and screen.encloses(sheet.panel.get_global_rect()) and screen.encloses(sheet.accept_button.get_global_rect()) and screen.encloses(sheet.cancel_button.get_global_rect()), "the sheet opens inside the screen with both buttons reachable")
	var names := []
	for item in ui.inventory:
		if item.id == own_item:
			names.append(item.name)
	check(names.size() == 1 and str(names[0]) in sheet.dialog_text and "revision 2" in sheet.dialog_text and "YOU GIVE:" in sheet.dialog_text and "YOU RECEIVE:" in sheet.dialog_text, "its terms name the real item given and the real revision")
	check("YOU GIVE 1 item" in sheet.summary_label.text and "YOU RECEIVE 1 item" in sheet.summary_label.text, "its pinned summary states the real counts: " + sheet.summary_label.text)
	check(pattern.search(sheet.dialog_text) == null, "its terms print the real pattern seeds whole")
	sheet.accept_button.pressed.emit()
	await frames(10)
	var listed: Dictionary = await ui.api.request("/trades")
	var traded: Dictionary = (listed.trades as Array).filter(func(t): return t.id == trade_id)[0]
	check(ui.api.player_id in traded.confirmations and int(traded.revision) == 2, "accepting the sheet recorded the confirmation on the real server for revision 2")
	return traded
