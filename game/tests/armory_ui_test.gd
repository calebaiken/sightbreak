extends SceneTree
## The armory's states and money terms, checked on the real screens: empty, loading and
## error cards with working actions, the listing price/fee/receipt arithmetic against the
## server's own rule, exact buy and trade confirmation terms, YOU GIVE / YOU RECEIVE, the
## collection browser's order, and that no screen overflows sideways at the supported
## sizes and text scales. Fixtures are explicitly local; nothing here talks to a real server
## except the failed-connection check, which targets a port nothing listens on.
const UI = preload("res://scripts/ui/economy_ui.gd")
const DESIGN = preload("res://scripts/ui/design_tokens.gd")
const SIZES := [Vector2i(960, 720), Vector2i(1024, 768), Vector2i(1280, 720), Vector2i(1560, 720), Vector2i(1600, 720)]
const SCALES := [0.85, 1.0, 1.15, 1.3]
const TABS := ["inventory", "cases", "market", "trades"]
var failures: Array[String] = []
var checks := 0
var ui: EconomyUI
var capture_dir := OS.get_environment("ECONOMY_CAPTURE_DIR")

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

## Scrolls the shell so a node sits at the top of the visible area, to capture what is
## below the first screen.
func scroll_to(node: Control) -> void:
	var scroll := ui.content.get_parent() as ScrollContainer
	scroll.scroll_vertical = int(node.get_global_rect().position.y - ui.content.get_global_rect().position.y) - 4
	for i in 2:
		await process_frame

## Every label's text under a node, joined: what a player can read there.
func words(node: Node) -> String:
	var parts: Array[String] = []
	for label in node.find_children("*", "Label", true, false):
		parts.append((label as Label).text)
	for button in node.find_children("*", "Button", true, false):
		parts.append((button as Button).text)
	return "  ".join(parts)

func named(node_name: String) -> Node:
	return ui.content.find_child(node_name, true, false)

func skin(id: String, name: String, collection: String, rarity: String, wear: float, extra := {}) -> Dictionary:
	var item := {"id": id, "name": name, "definition_id": id + "_def", "rarity": rarity, "kind": "weapon_skin", "collection": collection, "pattern_seed": 100 + id.length(), "wear": wear, "reserved": false}
	item.merge(extra, true)
	return item

## The catalog exactly as the backend serves it (scripts/export_catalog_fixture.py calls the
## backend's own catalog(), so definitions, prices, odds and the fee rate are the server's).
func world() -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/backend_world.json"))
	return (parsed as Dictionary).world

func fixture_catalog() -> Dictionary:
	return (world().catalog as Dictionary).duplicate(true)

## An owned item of a real definition: name, rarity and collection are the catalog's; only the
## instance's id, wear and state are chosen here.
func real_skin(id: String, definition_id: String, wear: float, extra := {}) -> Dictionary:
	var definition: Dictionary = {}
	for raw in fixture_catalog().definitions:
		if raw.id == definition_id:
			definition = raw
	var item := skin(id, definition.name, definition.collection, definition.rarity, wear, {"definition_id": definition_id})
	item.merge(extra, true)
	return item

func make_ui(size: Vector2i, scale: float, credits: int) -> void:
	if is_instance_valid(ui):
		ui.queue_free()
		await process_frame
	root.content_scale_size = size
	root.size = size
	ui = UI.new()
	ui.configure({"xp": 430, "credits": 900000, "settings": {"reduced_motion": true, "ui_text_scale": scale}})
	root.add_child(ui)
	await process_frame
	ui.api.token = "fixture-render-only"
	ui.api.player_id = "self-0000-0000"
	ui.api.base_url = "http://127.0.0.1:9"
	ui.account = {"display_name": "QA render fixture", "credits": credits, "xp": 200, "level": 1}
	ui.catalog = fixture_catalog()
	ui.equipped_loadout = {}
	ui.busy = false

func fill() -> Dictionary:
	var graphite := real_skin("s-graphite", "obsidian_common", 0.12)
	var slate := real_skin("s-slate", "obsidian_rare", 0.331, {"reserved": true})
	var iris := real_skin("s-iris", "crimson_archive_legendary", 0.015)
	ui.inventory = [graphite, slate, iris, {"id": "c-1", "kind": "case", "name": "Obsidian case", "definition_id": "obsidian_case", "collection": "Obsidian"}, {"id": "k-1", "kind": "key", "name": "Collection key", "definition_id": "key"}]
	ui.equipped_loadout = {"rifle": iris}
	ui.listings = [
		{"id": "L-theirs", "seller_id": "other-9999", "price": 100, "item": real_skin("l-1", "obsidian_mythic", 0.004)},
		{"id": "L-mine", "seller_id": "self-0000-0000", "price": 1250, "item": slate},
		{"id": "L-dear", "seller_id": "other-9999", "price": 5000, "item": real_skin("l-2", "crimson_archive_uncommon", 0.4)},
	]
	var gift_trade := {"id": "T-gift", "revision": 3, "state": "open", "a": "self-0000-0000", "b": "other-9999", "names": {"other-9999": "Ash\nFORGED  CONFIRM"}, "offers": {"self-0000-0000": ["s-graphite"], "other-9999": []}, "offer_items": {"self-0000-0000": [graphite], "other-9999": []}, "confirmations": []}
	var swap_trade := {"id": "T-swap", "revision": 1, "state": "open", "a": "other-9999", "b": "self-0000-0000", "names": {"other-9999": "Rook"}, "offers": {"self-0000-0000": ["s-iris"], "other-9999": ["l-1"]}, "offer_items": {"self-0000-0000": [iris], "other-9999": [real_skin("l-1", "obsidian_mythic", 0.004)]}, "confirmations": ["other-9999"]}
	ui.trades = [gift_trade, swap_trade]
	return {"graphite": graphite, "slate": slate, "iris": iris}

func show_tab(tab: String) -> void:
	ui.active_tab = tab
	ui._render()
	(ui.content.get_parent() as ScrollContainer).scroll_vertical = 0
	for i in 3:
		await process_frame

## No control under the content is wider than the screen, and nothing needs sideways
## scrolling: the shell's scroll never scrolls horizontally.
func check_fits(context: String, size: Vector2i) -> void:
	var scroll := ui.content.get_parent() as ScrollContainer
	check(scroll.horizontal_scroll_mode == ScrollContainer.SCROLL_MODE_DISABLED, context + ": no horizontal scroll mode")
	var widest := 0.0
	var offender := ""
	for control in ui.content.find_children("*", "Control", true, false):
		var c := control as Control
		if not c.is_visible_in_tree():
			continue
		var right := c.get_global_rect().end.x
		if right > widest:
			widest = right
			offender = c.name
	check(widest <= size.x + 1.0, "%s: content ends at x=%.0f of %d (%s)" % [context, widest, size.x, offender])
	check(ui.content.get_combined_minimum_size().x <= scroll.size.x + 1.0, "%s: content minimum width %.0f fits the scroll area %.0f" % [context, ui.content.get_combined_minimum_size().x, scroll.size.x])

## Every text label inside a card is no wider than the card that holds it (unless it
## clips with an ellipsis): nothing reads as cut off.
func check_text_in_cards(context: String) -> void:
	for card in ui.content.find_children("*", "PanelContainer", true, false):
		var panel := card as PanelContainer
		if not panel.is_visible_in_tree() or panel.size.x <= 0.0:
			continue
		for label in panel.find_children("*", "Label", true, false):
			var l := label as Label
			if not l.is_visible_in_tree() or l.text.is_empty():
				continue
			if l.autowrap_mode != TextServer.AUTOWRAP_OFF or l.clip_text or l.text_overrun_behavior != TextServer.OVERRUN_NO_TRIMMING:
				continue
			var font := l.get_theme_font("font")
			var wide := font.get_string_size(l.text, HORIZONTAL_ALIGNMENT_LEFT, -1, l.get_theme_font_size("font_size")).x
			check(wide <= panel.size.x + 1.0, "%s: \"%s\" (%.0f px) fits its %.0f px card" % [context, l.text.left(30), wide, panel.size.x])

func money() -> void:
	check(UI.credits_text(0) == "0" and UI.credits_text(7) == "7" and UI.credits_text(999) == "999", "Credits under 1,000 have no separator")
	check(UI.credits_text(1000) == "1,000" and UI.credits_text(1250) == "1,250" and UI.credits_text(1250000) == "1,250,000", "Credits use thousands separators")
	check(UI.credits_text(-1250) == "-1,250", "A negative amount keeps its sign once")
	ui.catalog = {"market_fee_basis_points": 300}
	check(ui.market_fee(100) == 3 and ui.market_fee(1000) == 30 and ui.market_fee(1) == 0, "A 3 % fee on 100 is 3, on 1,000 is 30, and rounds down to 0 on 1")
	check(ui.market_fee(33) == 0 and ui.market_fee(34) == 1, "The fee rounds down: 33 -> 0, 34 -> 1")
	var matches_server := true
	for basis_points in [0, 100, 250, 300, 999, 10000]:
		ui.catalog = {"market_fee_basis_points": basis_points}
		for price in range(1, 4001):
			if ui.market_fee(price) != price * basis_points / 10000:
				matches_server = false
	check(matches_server, "The displayed fee equals price x basis points // 10000 for 24,000 price/rate pairs")
	ui.catalog = {}
	check(ui.market_fee(500) == 0, "With no published fee rate, no fee is claimed")
	ui.catalog = {"market_fee_basis_points": 300}
	check(ui.fee_percent_text() == "3%", "A 300 basis point fee reads 3%")
	ui.catalog = {"market_fee_basis_points": 250}
	check(ui.fee_percent_text() == "2.5%", "A 250 basis point fee reads 2.5%")
	ui.catalog = {}
	check(ui.fee_percent_text() == "0%", "No published fee reads 0%")

func wallet_line() -> void:
	await make_ui(Vector2i(1280, 720), 1.0, 1250000)
	ui.account.display_name = "Ash\nKnight\u200b  Forged"
	ui._render()
	check(ui.wallet.text == "ONLINE  •  Ash Knight Forged  •  LEVEL 1  •  1,250,000 EARNED CREDITS", "The header flattens the name and separates thousands: " + ui.wallet.text)
	ui.account.display_name = ""
	ui._render()
	check(ui.wallet.text == "ONLINE  •  LEVEL 1  •  1,250,000 EARNED CREDITS", "An empty name leaves no empty segment: " + ui.wallet.text)
	ui.api.logout()
	ui._render()
	check(ui.wallet.text == "OFFLINE TRAINING  •  LOCAL PROGRESS ONLY", "Signed out, the header says training only")

func states() -> void:
	# Empty inventory: a card with a real action that opens the cases screen.
	await make_ui(Vector2i(1280, 720), 1.0, 500)
	ui.inventory = []
	await show_tab("inventory")
	var empty := named("State_empty")
	check(empty != null, "An empty inventory shows an empty-state card")
	check(empty != null and "Your collection starts here" in words(empty), "The empty inventory card says what to do")
	var action := named("StateAction") as Button
	check(action != null and action.text == "BROWSE CASES" and not action.disabled, "The empty inventory action is enabled and named")
	await capture("inventory-empty")
	ui.busy = true  # open_tab refreshes online; hold the refresh so only navigation is observed
	if action:
		action.pressed.emit()
	ui.busy = false
	check(ui.active_tab == "cases", "BROWSE CASES opens the cases screen")
	# Empty market and trades.
	ui.listings = []
	await show_tab("market")
	var market_empty := named("State_empty")
	check(market_empty != null and named("StateAction") != null and (named("StateAction") as Button).text == "REFRESH LISTINGS", "An empty market offers a real refresh")
	await capture("market-empty")
	ui.trades = []
	await show_tab("trades")
	var trades_empty := named("State_empty")
	check(trades_empty != null and (named("StateAction") as Button).text == "SHOW MY PLAYER ID", "No trades offers the way to share your player ID")
	ui.busy = true
	(named("StateAction") as Button).pressed.emit()
	ui.busy = false
	check(ui.active_tab == "profile", "SHOW MY PLAYER ID opens the profile")
	await show_tab("cases")
	ui.inventory = []
	await show_tab("cases")
	check(named("State_empty") != null, "Cases with none owned shows an empty-state card")
	# Loading: no account yet, a refresh in flight. The card says so and offers no action.
	ui.account = {}
	ui.is_loading = true
	await show_tab("inventory")
	var loading := named("State_loading")
	check(loading != null and named("StateAction") == null, "Loading shows a card with no action to take")
	check(named("State_empty") == null, "Loading is not mistaken for an empty inventory")
	check("EARNED CREDITS" not in ui.wallet.text, "While loading, no balance is shown")
	await capture("inventory-loading")
	# Error: a real failed connection, then the recovery action.
	ui.is_loading = false
	ui.busy = false
	var refreshed: bool = await ui._refresh()
	check(not refreshed, "A refresh against a closed port reports failure")
	check(not ui.load_error.is_empty() and not ui.busy and not ui.is_loading, "The failure is recorded and the screen is released")
	var error_card := named("State_error")
	check(error_card != null, "A failed refresh shows an error card")
	check(ui.wallet.text == "ONLINE  •  ACCOUNT NOT LOADED  •  BALANCE UNAVAILABLE", "With no account loaded the header claims no name or balance: " + ui.wallet.text)
	check(error_card != null and ui.load_error in words(error_card), "The error card states the actual failure")
	check(error_card != null and "Nothing on this screen was changed" in words(error_card), "The error card says nothing was changed")
	var retry := named("StateAction") as Button
	check(retry != null and retry.text == "TRY AGAIN" and not retry.disabled, "The error card offers TRY AGAIN")
	check(retry != null and retry.pressed.get_connections().size() > 0, "TRY AGAIN is wired to a refresh")
	await capture("inventory-error")
	# A later success clears the error.
	ui.load_error = ""
	ui.account = {"display_name": "QA render fixture", "credits": 500, "xp": 200, "level": 1}
	await show_tab("inventory")
	check(named("State_error") == null, "Clearing the error removes the card")
	# 401 clears the account instead of leaving a signed-in-looking screen.
	check(ui._failed({"_error": "Session expired (401)", "_status": 401}), "A 401 is a failure")
	check(ui.account.is_empty() and ui.inventory.is_empty() and ui.selected.is_empty(), "A 401 clears the cached account, inventory and selection")
	check(not ui._refresh_failed({"ok": true}), "A successful response is not a refresh failure")

func inventory_screen(items: Dictionary) -> void:
	await make_ui(Vector2i(1280, 720), 1.0, 500)
	fill()
	await show_tab("inventory")
	for item in ui.inventory:
		check(named("Item_" + item.id) != null, "Inventory card for %s" % item.id)
	var reserved_card := named("Item_s-slate")
	check(reserved_card != null and "RESERVED" in words(reserved_card), "A reserved instance says RESERVED")
	check(reserved_card != null and "WEAR 0.331" in words(reserved_card), "A card shows the instance's real wear")
	check(reserved_card != null and "RARE" in words(reserved_card), "A card shows the instance's rarity")
	var equipped_card := named("Item_s-iris")
	check(equipped_card != null and "EQUIPPED" in words(equipped_card), "The equipped finish is marked EQUIPPED")
	check(named("Item_s-graphite") != null and "EQUIPPED" not in words(named("Item_s-graphite")), "An unequipped finish is not marked")
	(named("Item_s-graphite") as Button).pressed.emit()
	await process_frame
	check(ui.selected.get("id", "") == "s-graphite", "Selecting a card selects that instance")
	check("Instance: s-graphite" in words(ui.content) and "Available in inventory" in words(ui.content), "The inspector names the selected owned instance")
	check(("EQUIP RIFLE FINISH" in words(ui.content)), "An owned unreserved finish offers EQUIP")
	(named("Item_s-slate") as Button).pressed.emit()
	await process_frame
	check("Reserved for exchange" in words(ui.content), "A reserved instance explains why it cannot be equipped")
	var equip := ui.content.find_children("*", "Button", true, false).filter(func(b): return (b as Button).text == "EQUIP RIFLE FINISH")
	check(equip.size() == 1 and (equip[0] as Button).disabled, "A reserved finish cannot be equipped")
	await capture("inventory-selected")
	var inspector_panel := ui.content.find_children("*", "SubViewportContainer", true, false)
	if not inspector_panel.is_empty() and not capture_dir.is_empty():
		await scroll_to(inspector_panel[0].get_parent().get_parent() as Control)
		await capture("inventory-inspector")
	ui.selected = {}

func cases_screen() -> void:
	await make_ui(Vector2i(1280, 720), 1.0, 100)
	fill()
	await show_tab("cases")
	var key_buy := named("BuySupply_key") as Button
	check(key_buy != null and key_buy.disabled and key_buy.text == "NEED 50 MORE", "A key costing 150 with 100 Credits says NEED 50 MORE and is disabled")
	check(int(ui.catalog.prices.key) == 150 and int(ui.catalog.prices.case) == 350, "The shop prices are the backend's own (key 150, case 350)")
	var case_buy := named("BuySupply_obsidian_case") as Button
	check(case_buy != null and case_buy.disabled and case_buy.text == "NEED 250 MORE", "A case costing 350 with 100 Credits says NEED 250 MORE")
	ui.account.credits = 1250
	await show_tab("cases")
	key_buy = named("BuySupply_key") as Button
	check(key_buy != null and not key_buy.disabled and key_buy.text == "BUY", "With enough Credits the key can be bought")
	key_buy.pressed.emit()
	check("150" in ui.dialog.dialog_text and "1,250" in ui.dialog.dialog_text, "The purchase confirmation states the price and the balance: " + ui.dialog.dialog_text.replace("\n", " "))
	check(ui.pending_action.is_valid(), "The confirmation holds the purchase until accepted")
	ui.dialog.hide()
	ui.pending_action = Callable()
	# The player's case: openable with a key, not otherwise.
	var open_button := named("Open_c-1") as Button
	check(open_button != null and not open_button.disabled, "A held case with a key can be opened")
	open_button.pressed.emit()
	check("Obsidian case" in ui.dialog.dialog_text and "Common  58%" in ui.dialog.dialog_text and "Mythic  0.1%" in ui.dialog.dialog_text and "Legendary  0.9%" in ui.dialog.dialog_text, "Opening a case confirms with the real published probabilities, printed without a stray .0: " + ui.dialog.dialog_text.replace("\n", " "))
	ui.dialog.hide()
	ui.pending_action = Callable()
	var keyless: Array = ui.inventory.filter(func(i): return i.kind != "key")
	ui.inventory = keyless
	await show_tab("cases")
	check((named("Open_c-1") as Button).disabled and "collection key is required" in words(ui.content), "Without a key the case cannot be opened, and the screen says why")
	check("Holds 6 finishes" in words(named("Open_c-1").get_parent()), "A held Obsidian case says it holds 6 finishes")
	check("Holds 6 finishes" in words(named("BuySupply_crimson_archive_case").get_parent()), "A Crimson Archive case on sale says it holds 6 finishes")
	check("Holds" not in words(named("BuySupply_key").get_parent()), "A key is not described as holding finishes")
	check(ui.case_holds_text("No such collection").is_empty(), "A collection with no listed finishes claims no contents")
	if not capture_dir.is_empty():
		await scroll_to(named("Collection_Obsidian").get_parent() as Control)
		await capture("cases-collection-browser")
	# Collection browser: grouped, ordered by rarity, each finish inspectable.
	for collection in ["Obsidian", "Crimson_Archive", "Spectral_Circuit", "Blacksite"]:
		check(named("Collection_" + collection) != null, "Collection section " + collection)
	var obsidian := named("Collection_Obsidian")
	var order: Array[String] = []
	for button in obsidian.find_children("Finish_*", "Button", true, false):
		order.append(button.name)
	check(order == ["Finish_obsidian_common", "Finish_obsidian_uncommon", "Finish_obsidian_rare", "Finish_obsidian_epic", "Finish_obsidian_legendary", "Finish_obsidian_mythic"], "Obsidian finishes run common -> mythic: " + str(order))
	var crimson := named("Collection_Crimson_Archive")
	order = []
	for button in crimson.find_children("Finish_*", "Button", true, false):
		order.append(button.name)
	check(order[0] == "Finish_crimson_archive_common" and order[-1] == "Finish_crimson_archive_mythic" and order.size() == 6, "Crimson Archive finishes run common -> mythic: " + str(order))
	check("6 FINISHES" in words(obsidian) and "6 FINISHES" in words(crimson), "Each collection states how many finishes it holds")
	check(ui.content.find_children("Finish_*", "Button", true, false).size() == 24, "Every catalog finish appears exactly once (4 collections x 6 rarities)")
	check("MYTHIC  ·  0.1%" in words(named("Finish_obsidian_mythic")) and "COMMON  ·  58%" in words(named("Finish_obsidian_common")), "Each finish states the published chance of its rarity")
	var popups_before := ui.find_children("*", "PopupPanel", false, false).size()
	(named("Finish_obsidian_mythic") as Button).pressed.emit()
	for i in 4:
		await process_frame
	check(ui.find_children("*", "PopupPanel", false, false).size() == popups_before + 1, "A catalog finish opens the 3D inspector")
	check(ui.selected.get("rarity", "") == "Mythic", "The inspected catalog finish is the one pressed")
	check(ui.inventory.filter(func(i): return i.get("id", "") == ui.selected.get("id", "x")).is_empty(), "A catalog finish is never added to the inventory by inspecting it")
	for popup in ui.find_children("*", "PopupPanel", false, false):
		popup.hide()
	await process_frame
	ui.catalog.definitions = ui.catalog.definitions.filter(func(d): return d.kind != "weapon_skin")
	await show_tab("cases")
	check(named("State_empty") != null, "A catalog with no finishes shows an empty-state card")
	ui.catalog = fixture_catalog()
	await show_tab("cases")
	await capture("cases-collections")

func market_screen() -> void:
	await make_ui(Vector2i(1280, 720), 1.0, 99)
	fill()
	await show_tab("market")
	var theirs := named("Listing_L-theirs")
	check(theirs != null, "A listing from another player shows")
	var price := theirs.find_child("Price", true, false) as Label
	check(price != null and price.text == "100 EARNED CREDITS", "The price is stated in earned Credits: " + (price.text if price else "-"))
	var terms := theirs.find_child("Terms", true, false) as Label
	check(terms != null and "seller receives 97" in terms.text and "fee of 3 (3%)" in terms.text, "A 100 listing at 3 % tells the buyer the seller gets 97 after a fee of 3: " + (terms.text if terms else "-"))
	var buy := theirs.find_child("Buy", true, false) as Button
	check(buy != null and buy.disabled and buy.text == "NEED 1 MORE", "With 99 Credits a 100 listing is not buyable and says NEED 1 MORE")
	check(theirs.find_child("Cancel", true, false) == null, "Someone else's listing cannot be cancelled by you")
	ui.account.credits = 100
	await show_tab("market")
	theirs = named("Listing_L-theirs")
	buy = theirs.find_child("Buy", true, false) as Button
	check(buy != null and not buy.disabled and buy.text == "BUY FOR 100", "With exactly 100 Credits the listing is buyable")
	buy.pressed.emit()
	var text := ui.dialog.dialog_text
	for term in ["100 earned Credits", "Obsidian / Gilded Fracture", "MYTHIC", "Wear 0.0040", "You pay 100", "seller receives 97", "market fee of 3", "You have 100 earned Credits"]:
		check(term in text, "The buy confirmation states \"%s\"" % term)
	check(ui.pending_action.is_valid(), "The buy confirmation holds the purchase until accepted")
	ui.dialog.hide()
	ui.pending_action = Callable()
	var mine := named("Listing_L-mine")
	check(mine != null and mine.find_child("Buy", true, false) == null, "Your own listing has no BUY")
	check(mine != null and mine.find_child("Cancel", true, false) != null, "Your own listing can be cancelled")
	check(mine != null and "YOUR LISTING" in words(mine), "Your own listing is labelled")
	var mine_terms := mine.find_child("Terms", true, false) as Label
	check(mine_terms != null and "You receive 1,213 after a fee of 37" in mine_terms.text, "A 1,250 listing pays the seller 1,213 after a fee of 37: " + (mine_terms.text if mine_terms else "-"))
	check((mine.find_child("Price", true, false) as Label).text == "1,250 EARNED CREDITS", "Prices use thousands separators")
	var dear := named("Listing_L-dear")
	check(dear != null and (dear.find_child("Buy", true, false) as Button).text == "NEED 4,900 MORE", "An unaffordable listing states the exact shortfall")
	var inspect := theirs.find_child("Inspect", true, false) as Button
	check(inspect != null and not inspect.disabled, "A listing can be inspected before buying")
	# Browsing comes first: the listings sit above the sell form.
	var first_listing := named("Listing_L-theirs")
	var form_heading := ui.content.find_children("*", "Label", true, false).filter(func(l): return (l as Label).text == "SELL AN OWNED COSMETIC")
	check(form_heading.size() == 1 and first_listing.get_global_rect().position.y < (form_heading[0] as Label).get_global_rect().position.y, "Listings come before the sell form")
	var create := named("CreateListing") as Button
	check(create != null and not create.disabled, "An owned unreserved finish can be listed")
	create.pressed.emit()
	check("Obsidian / Graphite" in ui.dialog.dialog_text and "100 earned Credits" in ui.dialog.dialog_text and "fee is 3 (3%)" in ui.dialog.dialog_text and "you receive 97" in ui.dialog.dialog_text, "The listing confirmation states the price, the fee and the proceeds: " + ui.dialog.dialog_text.replace("\n", " "))
	ui.dialog.hide()
	ui.pending_action = Callable()
	# Sorting and the "mine" filter change only what is shown.
	var ids := func() -> Array:
		var out := []
		for card in ui.content.find_children("Listing_*", "PanelContainer", true, false):
			out.append(String(card.name))
		return out
	check(ids.call() == ["Listing_L-theirs", "Listing_L-mine", "Listing_L-dear"], "Default order is by price, low to high: " + str(ids.call()))
	ui.market_sort = 1
	await show_tab("market")
	check(ids.call() == ["Listing_L-dear", "Listing_L-mine", "Listing_L-theirs"], "High to low reverses the order")
	ui.market_sort = 0
	ui.market_mine_only = true
	await show_tab("market")
	check(ids.call() == ["Listing_L-mine"], "MY LISTINGS shows only yours")
	check(ui.listings.size() == 3, "Sorting and filtering never change the underlying listings")
	ui.market_mine_only = false
	ui.market_filter = "no such finish"
	await show_tab("market")
	check(named("State_empty") != null and ids.call().is_empty(), "A filter with no matches shows an empty-state card")
	ui.market_filter = ""
	await show_tab("market")
	await capture("market-listings")
	if not capture_dir.is_empty():
		await scroll_to(ui.content.find_children("*", "Label", true, false).filter(func(l): return (l as Label).text == "SELL AN OWNED COSMETIC")[0].get_parent().get_parent() as Control)
		await capture("market-sell-form")

func trades_screen() -> void:
	await make_ui(Vector2i(1280, 720), 1.0, 500)
	var items := fill()
	await show_tab("trades")
	var gift := ui.content.find_children("TradeGive", "PanelContainer", true, false)
	var receive := ui.content.find_children("TradeReceive", "PanelContainer", true, false)
	check(gift.size() == 2 and receive.size() == 2, "Each trade shows a YOU GIVE and a YOU RECEIVE column")
	check(gift[0].get_global_rect().size.x >= 340 and receive[0].get_global_rect().size.x >= 340, "The two columns are at least 340 px wide")
	var side_by_side: bool = absf(gift[0].get_global_rect().position.y - receive[0].get_global_rect().position.y) < 1.0
	check(side_by_side, "At 1280 px the two columns sit side by side")
	check("YOU GIVE" in words(gift[0]) and "Graphite" in words(gift[0]) and "OBSIDIAN" in words(gift[0]), "The gift trade lists what you give, finish first")
	check(receive[0].find_child("Nothing", true, false) != null, "The gift trade says you receive nothing")
	var warnings := ui.content.find_children("GiftWarning", "PanelContainer", true, false)
	check(warnings.size() == 1, "Only the one-sided trade carries the gift warning")
	check(not warnings.is_empty() and "YOU RECEIVE NOTHING FOR THIS OFFER" in words(warnings[0]), "The gift warning is explicit")
	check("Gilded Fracture" in words(receive[1]) and "OBSIDIAN" in words(receive[1]) and "Iridescence" in words(gift[1]) and "CRIMSON ARCHIVE" in words(gift[1]), "The swap trade lists the right item on each side")
	var titles := ui.content.find_children("TradeTitle", "Label", true, false)
	check(titles.size() == 2 and "Ash FORGED CONFIRM" in (titles[0] as Label).text, "A partner name with a newline is flattened to one line: " + (titles[0] as Label).text)
	check("(other-99)" in (titles[0] as Label).text, "The partner's player ID prefix is shown next to the name")
	check(not "\n" in (titles[0] as Label).text, "The trade title is a single line")
	var you := ui.content.find_children("ConfirmYou", "PanelContainer", true, false)
	var them := ui.content.find_children("ConfirmPartner", "PanelContainer", true, false)
	check("HAVE NOT CONFIRMED" in words(you[0]) and "HAVE NOT CONFIRMED" in words(them[0]), "A fresh revision shows neither player confirmed")
	check("HAVE NOT CONFIRMED" in words(you[1]) and "THEY CONFIRMED" in words(them[1]), "The second trade shows the partner has confirmed and you have not")
	# The confirmation text keeps YOU GIVE / YOU RECEIVE and the gift sentence.
	var text: String = ui.trade_confirmation_text(ui.trades[0])
	check("YOU GIVE:" in text and "YOU RECEIVE:" in text and "    nothing" in text and "This is a gift" in text, "The commit dialog repeats the gift terms")
	check("revision 3" in text and "other-99" in text, "The commit dialog names the revision and the partner")
	var swap_text: String = ui.trade_confirmation_text(ui.trades[1])
	check("Obsidian / Gilded Fracture" in swap_text and "MYTHIC" in swap_text and "This is a gift" not in swap_text, "A two-sided swap is not called a gift")
	# Unsaved edits cannot be confirmed.
	var confirm_buttons := ui.content.find_children("*", "Button", true, false).filter(func(b): return (b as Button).text == "CONFIRM DISPLAYED REVISION")
	check(confirm_buttons.size() == 2, "Each open trade has a confirm button")
	var toggles := ui.content.find_children("*", "CheckButton", true, false).filter(func(b): return (b as CheckButton).text == "Crimson Archive / Iridescence")
	check(not toggles.is_empty(), "The offer editor lists an inventory item")
	if not toggles.is_empty():
		(toggles[0] as CheckButton).button_pressed = true
		(confirm_buttons[0] as Button).pressed.emit()
		check("unsaved edits" in ui.status.text, "Confirming with unsaved edits is refused with a reason")
		check(not ui.dialog.visible, "No confirmation dialog opens over unsaved edits")
	await capture("trades-give-receive")
	if not capture_dir.is_empty():
		await scroll_to(ui.content.find_children("TradeTitle", "Label", true, false)[1].get_parent().get_parent() as Control)
		await capture("trades-swap")
	ui.dialog.hide()
	(confirm_buttons[1] as Button).pressed.emit()
	check("YOU GIVE:" in ui.dialog.dialog_text and "Rook" in ui.dialog.dialog_text, "Confirming a saved revision shows the exact terms")
	ui.dialog.hide()
	ui.pending_action = Callable()
	check(items.size() == 3, "fixture")

func layouts() -> void:
	var tally := 0
	for size in SIZES:
		for scale in SCALES:
			await make_ui(size, scale, 500)
			fill()
			for tab in TABS:
				await show_tab(tab)
				var context := "%s @%dx%d x%.2f" % [tab, size.x, size.y, scale]
				check_fits(context, size)
				check_text_in_cards(context)
				tally += 1
				if (size == Vector2i(960, 720) and scale == 1.3) or (size == Vector2i(1600, 720) and scale == 1.0):
					await capture("layout-%s-%dx%d-%d" % [tab, size.x, size.y, int(scale * 100)])
	print("LAYOUT %d screens (4 tabs x %d sizes x %d text scales)" % [tally, SIZES.size(), SCALES.size()])
	# A long, hostile name and CJK text in a trade and a listing.
	await make_ui(Vector2i(960, 720), 1.3, 500)
	fill()
	var long_name := "Δ".repeat(80) + " 非常に長い名前 " + "W".repeat(60)
	ui.trades[0].names = {"other-9999": long_name}
	ui.listings[0].item.name = "Obsidian / " + "Extraordinarily".repeat(6)
	await show_tab("trades")
	check_fits("long partner name", Vector2i(960, 720))
	check((ui.content.find_children("TradeTitle", "Label", true, false)[0] as Label).text.length() < 120, "A very long partner name is capped in the title")
	await show_tab("market")
	check_fits("long item name", Vector2i(960, 720))

func run() -> void:
	await make_ui(Vector2i(1280, 720), 1.0, 500)
	money()
	await wallet_line()
	await states()
	await inventory_screen({})
	await cases_screen()
	await market_screen()
	await trades_screen()
	await layouts()
	if is_instance_valid(ui):
		ui.queue_free()
	await process_frame
	if failures.is_empty():
		print("PASS: Armory states, money terms, trade sides and collection order (%d checks)" % checks)
		quit(0)
	else:
		print("FAIL: %d of %d armory checks" % [failures.size(), checks])
		for failure in failures.slice(0, 40):
			print("  - " + failure)
		quit(1)
