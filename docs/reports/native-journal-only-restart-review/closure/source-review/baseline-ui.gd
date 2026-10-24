class_name EconomyUI
extends Control
## Authoritative account views. Offline progress never enters an API payload.
signal closed
signal loadout_changed(slots: Dictionary)
## The account, its balance or the way it is loading changed; the menu's record card follows.
signal account_changed

const API = preload("res://scripts/ui/economy_api.gd")
const INSPECTOR = preload("res://scripts/ui/item_inspector.gd")
const REVEAL = preload("res://scripts/ui/case_reveal.gd")
const SAFE_AREA = preload("res://scripts/ui/safe_area.gd")
const DESIGN = preload("res://scripts/ui/design_tokens.gd")
const CONFIRM = preload("res://scripts/ui/confirm_sheet.gd")
const GOLD := DESIGN.GOLD
const MUTED := DESIGN.STEEL
var api: EconomyAPI
var offline_profile: Dictionary = {}
var account: Dictionary = {}
var inventory: Array = []
var catalog: Dictionary = {}
var listings: Array = []
var trades: Array = []
var selected: Dictionary = {}
var equipped_loadout: Dictionary = {}
var active_tab := "inventory"
var busy := false
## True while a refresh is in flight, and the last refresh's failure (empty when it worked).
var is_loading := false
var load_error := ""
## How the last failed request failed (see EconomyAPI.request) and whether the server ended the session.
var load_outcome := ""
var session_expired := false
var reduced_motion := false
## The player's text-size setting (0.85 to 1.4): every label here follows it, as buttons do through the theme.
var text_scale := 1.0
var content: VBoxContainer
var status: Label
var wallet: Label
var dialog: ConfirmSheet
var pending_action := Callable()
var market_filter := ""
var inventory_filter := ""
var inventory_available_only := false
var market_sort := 0
var market_mine_only := false
var pending_transaction: Dictionary = {}
var retry_button: Button
var safe_margin: MarginContainer
var tab_buttons: Dictionary = {}
var brand_label: Label
## The finish to preselect in the sell form, set by "SELL THIS FINISH".
var sell_preselect := ""

func configure(profile: Dictionary) -> void:
	offline_profile = profile.duplicate(true)
	reduced_motion = bool(offline_profile.get("settings", {}).get("reduced_motion", false))
	text_scale = clampf(float(offline_profile.get("settings", {}).get("ui_text_scale", 1.0)), 0.85, 1.4)
	if is_node_ready():
		_restyle_shell()

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	api = API.new()
	add_child(api)
	_build_shell()
	_render()

func open_tab(tab: String) -> void:
	active_tab = tab if tab in ["inventory", "cases", "market", "trades", "profile"] else "inventory"
	if is_node_ready():
		_render()
		if not api.token.is_empty():
			_refresh()

func _build_shell() -> void:
	var background := ColorRect.new()
	background.color = DESIGN.OBSIDIAN
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(background)
	var margin := MarginContainer.new()
	safe_margin = margin
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 22)
	add_child(margin)
	resized.connect(_update_safe_margins)
	call_deferred("_update_safe_margins")
	var body := VBoxContainer.new()
	body.add_theme_constant_override("separation", 12)
	margin.add_child(body)
	var header := HBoxContainer.new()
	body.add_child(header)
	var brand := _label("SIGHTBREAK  /  ARMORY", 24, GOLD)
	brand_label = brand
	brand.add_theme_font_override("font", DESIGN.heading_font())
	brand.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(brand)
	DESIGN.apply_button(_button(header, "←  BACK", func(): closed.emit()), "ghost")
	brand.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	wallet = _label("OFFLINE TRAINING", 15, MUTED)
	wallet.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.add_child(wallet)
	var tabs := HFlowContainer.new()
	tabs.add_theme_constant_override("h_separation", 8)
	body.add_child(tabs)
	for tab in ["inventory", "cases", "market", "trades", "profile"]:
		var tab_button := _button(tabs, str(tab).to_upper(), open_tab.bind(tab))
		tab_button.toggle_mode = true
		tab_button.name = "Tab_" + tab
		tab_buttons[tab] = tab_button
	DESIGN.apply_button(_button(tabs, "REFRESH", _refresh), "ghost")
	status = _label("Offline progress and online ownership are separate.", 14, MUTED)
	status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.add_child(status)
	retry_button = _button(body, "RETRY PENDING TRANSACTION", _retry_pending)
	retry_button.hide()
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	body.add_child(scroll)
	content = VBoxContainer.new()
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", 14)
	scroll.add_child(content)
	dialog = CONFIRM.new()
	dialog.accepted.connect(func():
		var action := pending_action
		pending_action = Callable()
		if action.is_valid():
			action.call())
	dialog.cancelled.connect(func(): pending_action = Callable())
	add_child(dialog)
	theme = DESIGN.build_theme(text_scale)
	_restyle_shell()

## The header's labels are built once; they are resized when the text-size setting changes.
func _restyle_shell() -> void:
	for pair in [[brand_label, 24], [wallet, 15], [status, 14]]:
		var node: Label = pair[0]
		if is_instance_valid(node):
			node.add_theme_font_size_override("font_size", DESIGN.scaled_size(pair[1], text_scale))

func _update_safe_margins() -> void:
	if not is_instance_valid(safe_margin):
		return
	var insets := [22, 22, 22, 22]
	var safe: Rect2 = SAFE_AREA.viewport_rect(size)
	insets = [22 + int(safe.position.x), 22 + int(size.x - safe.end.x), 22 + int(safe.position.y), 22 + int(size.y - safe.end.y)]
	var sides := ["left", "right", "top", "bottom"]
	for index in 4:
		safe_margin.add_theme_constant_override("margin_" + sides[index], insets[index])

func _label(value: String, font_size := 16, color := DESIGN.TEXT) -> Label:
	var node := Label.new()
	node.text = value
	node.add_theme_font_size_override("font_size", DESIGN.scaled_size(font_size, text_scale))
	node.add_theme_color_override("font_color", color)
	return node

func _text(parent: Node, value: String, font_size := 16, color := DESIGN.TEXT) -> Label:
	var node := _label(value, font_size, color)
	node.size.x = minf(560, maxf(260, size.x - 80))
	node.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	parent.add_child(node)
	return node

func _button(parent: Node, title: String, action: Callable) -> Button:
	var node := Button.new()
	node.text = title
	node.custom_minimum_size.y = DESIGN.TOUCH_MIN
	node.pressed.connect(action)
	parent.add_child(node)
	return node

func _field(parent: Node, hint: String, value := "", secret := false) -> LineEdit:
	var node := LineEdit.new()
	node.placeholder_text = hint
	node.text = value
	node.secret = secret
	node.custom_minimum_size.y = DESIGN.TOUCH_MIN
	parent.add_child(node)
	return node

func _panel(parent: Node) -> VBoxContainer:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", DESIGN.panel())
	parent.add_child(panel)
	var stack := VBoxContainer.new()
	stack.add_theme_constant_override("separation", 10)
	panel.add_child(stack)
	return stack

func _render() -> void:
	if not content:
		return
	for node in content.get_children():
		content.remove_child(node)
		node.queue_free()
	wallet.text = _wallet_text()
	for tab in tab_buttons:
		var tab_button: Button = tab_buttons[tab]
		tab_button.set_pressed_no_signal(tab == active_tab)
		if tab == active_tab:
			tab_button.add_theme_stylebox_override("normal", DESIGN.tab_selected_style())
			tab_button.add_theme_stylebox_override("pressed", DESIGN.tab_selected_style())
			tab_button.add_theme_color_override("font_color", GOLD)
			tab_button.add_theme_color_override("font_pressed_color", GOLD)
		else:
			tab_button.remove_theme_stylebox_override("normal")
			tab_button.remove_theme_stylebox_override("pressed")
			tab_button.remove_theme_color_override("font_color")
			tab_button.remove_theme_color_override("font_pressed_color")
	var title := _text(content, active_tab.to_upper(), 28, GOLD)
	title.add_theme_font_override("font", DESIGN.heading_font())
	if active_tab != "profile" and api.token.is_empty() and session_expired:
		_state_card(content, "error", "Your session ended", "The server no longer accepts this session, so nothing here is confirmed any more: your inventory and Credits are held by the server, and are unchanged. Sign in again to see them.", "SIGN IN AGAIN", open_tab.bind("profile"), "SESSION ENDED")
	if active_tab != "profile" and not api.token.is_empty():
		if not load_error.is_empty():
			var titles := {"not_reached": "Cannot reach the economy server", "not_sent": "The request was not sent", "rejected": "The economy server refused the request", "unknown": "The economy server's answer was lost"}
			_state_card(content, "error", titles.get(load_outcome, "The economy server did not answer as expected"), load_error + "\nNothing on this screen was changed. Your inventory and Credits are held by the server.", "TRY AGAIN", func(): _refresh())
			if account.is_empty():
				return
		elif is_loading and account.is_empty():
			_state_card(content, "loading", "Loading your account", "Waiting for the economy server to confirm your inventory, Credits and the catalog. No action is available until it does.")
			return
	match active_tab:
		"profile": _profile()
		"inventory": _inventory()
		"cases": _cases()
		"market": _market()
		"trades": _trades()

## What is known about the online account, for every place that shows it (this screen's
## header, its profile and the menu's record card). "state" is one of:
##   signed_out  no session; only the local training record exists
##   expired     the server ended the session (401); sign in again
##   loading     a session exists and the server has not answered yet
##   unavailable a session exists and the last request failed before any account arrived
##   stale       an earlier answer is held, but the latest refresh failed
##   ready       the server's latest answer is in hand
## "credits" is the earned balance as text only when the server has stated one ("" otherwise):
## an unknown balance is never shown as zero.
func account_summary() -> Dictionary:
	var has_balance := account.has("credits") and (account.credits is int or account.credits is float)
	var state := "ready"
	if api.token.is_empty():
		state = "expired" if session_expired else "signed_out"
	elif is_loading:
		state = "loading"
	elif account.is_empty():
		state = "unavailable"
	elif not load_error.is_empty():
		state = "stale"
	return {
		"state": state,
		"name": DESIGN.plain_line(str(account.get("display_name", ""))),
		"level": int(account.get("level", 1)) if account.has("level") else -1,
		"credits": credits_text(int(account.credits)) if has_balance and state in ["ready", "stale"] else "",
		"balance_verified": has_balance and state == "ready",
	}

## The line under the title: the signed-in account's name, level and earned Credits, only once
## the server has said what they are; never a name or balance that was not received.
func _wallet_text() -> String:
	var summary := account_summary()
	match summary.state:
		"signed_out":
			return "OFFLINE TRAINING  •  LOCAL PROGRESS ONLY"
		"expired":
			return "SESSION ENDED  •  SIGN IN AGAIN UNDER PROFILE"
		"loading":
			return "ONLINE  •  LOADING ACCOUNT…"
		"unavailable":
			return "ONLINE  •  ACCOUNT NOT LOADED  •  BALANCE UNAVAILABLE"
	var identity: String = "%s  •  " % summary.name if not str(summary.name).is_empty() else ""
	var level_text: String = "LEVEL %d  •  " % summary.level if summary.level >= 0 else ""
	var credits: String = ("%s EARNED CREDITS" % summary.credits) if not str(summary.credits).is_empty() else "EARNED CREDITS UNAVAILABLE"
	return "ONLINE  •  %s%s%s%s" % [identity, level_text, credits, "  (LAST CONFIRMED  •  REFRESH FAILED)" if summary.state == "stale" else ""]

## A whole number from the server as text. JSON has one number type and Godot reads every one of
## them as a float, so a seed of 1840233 would print as "1840233.0"; anything else prints as is.
static func whole(value: Variant) -> String:
	return str(int(value)) if (value is float or value is int) else str(value)

## Earned Credits for a sentence: the balance with separators, or "unavailable". Never "0" for
## a balance the server has not stated.
func balance_text() -> String:
	var summary := account_summary()
	return summary.credits if not str(summary.credits).is_empty() else "unavailable"

func _announce_account() -> void:
	account_changed.emit()

func _needs_account() -> bool:
	if not api.token.is_empty():
		return false
	var panel := _panel(content)
	_text(panel, "Connect your online account", 22)
	_text(panel, "Authoritative inventory, earned Credits, cases and exchanges live on your economy server. Local training progress cannot be spent or traded online.", 16, MUTED)
	_button(panel, "SIGN IN / CREATE ACCOUNT", open_tab.bind("profile"))
	return true

func _profile() -> void:
	var local := _panel(content)
	_text(local, "LOCAL TRAINING", 18, GOLD)
	_text(local, "XP: %s  •  Training credits: %s\nThis device only. No conversion to online Credits." % [offline_profile.get("xp", 0), offline_profile.get("credits", 0)], 16, MUTED)
	if not api.token.is_empty():
		var online := _panel(content)
		_text(online, "ONLINE ACCOUNT  /  " + DESIGN.plain_line(str(account.get("display_name", ""))), 22)
		var identity_row := HFlowContainer.new()
		online.add_child(identity_row)
		var identity := _field(identity_row, "Player ID", api.player_id)
		identity.editable = false
		identity.custom_minimum_size.x = 320
		var copy_id := _button(identity_row, "COPY PLAYER ID", func():
			DisplayServer.clipboard_set(api.player_id)
			_message("Player ID copied. Send it to the player you want to trade with."))
		copy_id.name = "CopyPlayerID"
		var known := not account.is_empty()
		_text(online, "XP: %s  •  Level: %s  •  Earned Credits: %s" % [whole(account.get("xp", "—")) if known else "—", whole(account.get("level", "—")) if known else "—", balance_text()])
		_text(online, "New accounts start with zero. Only the trusted match service can award online rewards after a validated 5v5 match with ten human players. Small LAN sessions, bots and offline matches cannot grant online items or Credits.", 15, MUTED)
		_text(online, "Session held in memory. Closing the game clears it. Share your player ID to arrange a trade.", 14, MUTED)
		_button(online, "SIGN OUT", _logout)
	else:
		var login := _panel(content)
		_text(login, "ONLINE ACCOUNT", 22)
		var server := _field(login, "Economy server URL", api.base_url)
		_text(login, "Use HTTPS for public servers. HTTP exposes credentials and is for loopback or trusted LAN development only. A phone must use the host computer's LAN address.", 14, GOLD)
		var username := _field(login, "Username (3–32 characters)")
		var password := _field(login, "Password (12–128 characters)", "", true)
		var name_field := _field(login, "Display name (registration only)")
		var actions := HFlowContainer.new()
		login.add_child(actions)
		_button(actions, "SIGN IN", func(): _authenticate(server.text, username.text, password.text, name_field.text, false, password))
		_button(actions, "CREATE ACCOUNT", func(): _authenticate(server.text, username.text, password.text, name_field.text, true, password))
		_text(login, "No real money. No payments. No cash-out. All online Credits and collectibles come from validated gameplay or player exchanges.", 14, MUTED)
	var motion := CheckButton.new()
	motion.text = "Reduce case reveal motion"
	motion.button_pressed = reduced_motion
	motion.toggled.connect(func(value: bool): reduced_motion = value)
	content.add_child(motion)

func _authenticate(url: String, username: String, password: String, display_name: String, register: bool, password_field: LineEdit) -> void:
	if busy:
		return
	var problem := api.configure_url(url)
	if not problem.is_empty():
		_message(problem, true)
		return
	busy = true
	_message("Connecting securely to your selected server…")
	var payload := {"username": username.strip_edges(), "password": password}
	if register:
		payload["display_name"] = display_name.strip_edges()
	var result := await api.request("/auth/register" if register else "/auth/login", HTTPClient.METHOD_POST, payload)
	busy = false
	if is_instance_valid(password_field):
		password_field.clear()
	if _failed(result):
		return
	api.token = str(result.get("token", ""))
	api.player_id = str(result.get("player_id", ""))
	if api.token.is_empty():
		_message("The server did not issue a session.", true)
		return
	selected = {}
	session_expired = false
	load_error = ""
	load_outcome = ""
	await _refresh()

func _logout() -> void:
	if busy:
		return
	busy = true
	var result := await api.request("/auth/logout", HTTPClient.METHOD_POST)
	api.logout()
	pending_transaction = {}
	retry_button.hide()
	account = {}
	inventory = []
	selected = {}
	listings = []
	trades = []
	equipped_loadout = {}
	session_expired = false
	load_error = ""
	load_outcome = ""
	is_loading = false
	loadout_changed.emit(equipped_loadout)
	busy = false
	_render()
	_announce_account()
	_message("Signed out. Local session cleared." if not result.has("_error") else "Local session cleared. Server revocation could not be confirmed; the remote session will expire.")

func _refresh() -> bool:
	if busy:
		return false
	if api.token.is_empty():
		_message("Sign in under PROFILE to connect to the online economy.")
		return false
	busy = true
	is_loading = true
	load_error = ""
	load_outcome = ""
	if account.is_empty():
		_render()
	_announce_account()
	_message("Refreshing authoritative account data…")
	var me := await api.request("/me")
	if _refresh_failed(me):
		return false
	account = me
	var owned := await api.request("/inventory")
	if _refresh_failed(owned):
		return false
	inventory = owned.get("items", [])
	var definitions := await api.request("/catalog")
	if _refresh_failed(definitions):
		return false
	catalog = definitions
	var loadout := await api.request("/loadout")
	if _refresh_failed(loadout):
		return false
	equipped_loadout = loadout.get("slots", {})
	loadout_changed.emit(equipped_loadout.duplicate(true))
	if active_tab == "market":
		var market_data := await api.request("/market")
		if _refresh_failed(market_data):
			return false
		listings = market_data.get("listings", [])
	if active_tab == "trades":
		var trade_data := await api.request("/trades")
		if _refresh_failed(trade_data):
			return false
		trades = trade_data.get("trades", [])
	busy = false
	is_loading = false
	_render()
	_announce_account()
	_message("Connected. Data confirmed by your economy server.")
	return true

func _message(value: String, error := false) -> void:
	status.text = value
	status.add_theme_color_override("font_color", Color("f0a1aa") if error else MUTED)

## A refresh step that failed: records why, stops the loading state and shows the error.
func _refresh_failed(result: Dictionary) -> bool:
	if not _failed(result):
		return false
	busy = false
	is_loading = false
	if session_expired:
		return true
	load_error = str(result.get("_error", "Unknown error"))
	load_outcome = str(result.get("_outcome", ""))
	_render()
	_announce_account()
	return true

func _failed(result: Dictionary) -> bool:
	if result.has("_error"):
		if int(result.get("_status", 0)) == 401:
			# The server ended the session: what was held is no longer confirmed by anyone.
			session_expired = true
			api.logout()
			account = {}
			inventory = []
			selected = {}
			equipped_loadout = {}
			listings = []
			trades = []
			is_loading = false
			loadout_changed.emit({})
			_render()
			_announce_account()
			_message("Your session ended (the server did not accept it). Sign in again under PROFILE. Nothing was changed.", true)
			return true
		_message(str(result["_error"]), true)
		return true
	return false

## Opens the bounded confirmation. `accept_label` says what pressing it does ("BUY FOR 150
## CREDITS"), never just "OK"; `summary` is the pinned line of what is given and received;
## `danger` marks an act that gives something away for nothing.
func _confirm(message: String, action: Callable, accept_label := "CONFIRM", summary := "", danger := false, title := "CONFIRM TRANSACTION") -> void:
	if busy:
		return
	pending_action = action
	dialog.present(title, message, accept_label, summary, danger, text_scale)

func _retry_pending() -> Dictionary:
	if busy or pending_transaction.is_empty():
		return {}
	var pending := pending_transaction.duplicate(true)
	if pending.owner != api.player_id or pending.server != api.base_url:
		_message("Sign in to the original account and server to recover this transaction.", true)
		return {"_error": "Account mismatch"}
	pending_transaction = {}
	var result := await _perform(pending.path, pending.payload, pending.message, pending.method)
	if not result.has("_error") and pending.path == "/cases/open":
		selected = result.get("item", {})
		_show_committed_reveal(selected)
	return result

func _perform(path: String, payload := {}, message := "Transaction confirmed.", method := HTTPClient.METHOD_POST) -> Dictionary:
	if busy:
		return {"_error": "A request is already pending."}
	if not pending_transaction.is_empty():
		_message("Recover the pending transaction before starting another. Retry uses its original receipt identifier.", true)
		return {"_error": "An unresolved transaction is pending."}
	busy = true
	_message("Waiting for server confirmation…")
	var result := await api.request(path, method, payload)
	busy = false
	if result.get("_uncertain", false) and payload.has("idempotency_key"):
		pending_transaction = {"path": path, "payload": payload.duplicate(true), "message": message, "method": method, "owner": api.player_id, "server": api.base_url}
	retry_button.visible = not pending_transaction.is_empty()
	if _failed(result):
		if result.has("_error") and int(result.get("_status", 0)) != 401:
			_message(failure_text(result, not pending_transaction.is_empty()), true)
		return result
	var refreshed := await _refresh()
	if refreshed:
		_message(message)
	else:
		_message("Transaction confirmed, but account refresh failed. Refresh before making another transaction.", true)
	return result

## What a failed request means for the player, by what is known (EconomyAPI.request's
## "_outcome"). Only an unknown outcome of a transaction that holds a receipt identifier
## mentions retrying: a retry resends that identifier, so it can never charge twice.
func failure_text(result: Dictionary, retry_possible: bool) -> String:
	var error := str(result.get("_error", "The request failed."))
	match str(result.get("_outcome", "")):
		"not_sent", "not_reached":
			return error + " Nothing was charged and nothing changed. Try again when you are connected."
		"rejected":
			return error + " The server refused it; nothing changed."
		"unknown":
			if retry_possible:
				return error + " Nothing is shown as done. Press RETRY PENDING TRANSACTION to find out safely: it reuses this transaction's receipt identifier, so it cannot be applied twice."
			return error + " Refresh to see what the server holds before you try again."
	return error

## Credits with thousands separators: 1250 -> "1,250".
static func credits_text(value: int) -> String:
	var digits := str(absi(value))
	var out := ""
	for index in digits.length():
		if index > 0 and (digits.length() - index) % 3 == 0:
			out += ","
		out += digits[index]
	return ("-" if value < 0 else "") + out

## The fee the server keeps from a sale: price x basis points / 10,000, rounded down. This is
## backend/app.py's own rule, shown so a seller sees exactly what a sale pays; the server
## settles it.
@warning_ignore("integer_division")
func market_fee(price: int) -> int:
	return price * int(catalog.get("market_fee_basis_points", 0)) / 10000

## The market fee as a player reads it: "3%", or "2.5%" when the rate is not whole.
func fee_percent_text() -> String:
	var basis_points := int(catalog.get("market_fee_basis_points", 0))
	return "%d%%" % (basis_points / 100) if basis_points % 100 == 0 else "%s%%" % str(float(basis_points) / 100.0)

## How many finishes the catalog lists for a collection: what a case of it can hold.
func collection_finish_count(collection: String) -> int:
	var count := 0
	for raw in catalog.get("definitions", []):
		if raw is Dictionary and raw.get("kind") == "weapon_skin" and str(raw.get("collection", "")) == collection:
			count += 1
	return count

## "Holds 3 finishes" for a case's collection; empty when the catalog lists none.
func case_holds_text(collection: String) -> String:
	var count := collection_finish_count(collection)
	return "" if count == 0 else "Holds %d finish%s" % [count, "" if count == 1 else "es"]

## A small picture of an item's finish: its collection's two paint colours, framed in
## its rarity colour. Everything comes from the item's own metadata.
func _swatch(item: Dictionary, edge: float = 44.0) -> Control:
	var kind := str(item.get("kind", ""))
	var accent: Color = REVEAL.FINISH.rarity_color(str(item.get("rarity", "Common"))) if kind == "weapon_skin" else DESIGN.STEEL
	var palette: Array = REVEAL.FINISH.PALETTES.get(str(item.get("collection", "")), [DESIGN.GRAPHITE_HOVER, DESIGN.STEEL])
	var swatch := Control.new()
	swatch.mouse_filter = Control.MOUSE_FILTER_IGNORE
	swatch.custom_minimum_size = Vector2(edge, edge)
	swatch.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	swatch.draw.connect(func():
		var box := swatch.size
		swatch.draw_rect(Rect2(Vector2.ZERO, box), palette[0])
		if kind == "weapon_skin":
			swatch.draw_colored_polygon(PackedVector2Array([Vector2(box.x * 0.45, 0), box * Vector2(1, 0), box * Vector2(1, 0.55), Vector2(0, box.y), Vector2(0, box.y * 0.45)]), palette[1])
		else:
			swatch.draw_rect(Rect2(box * 0.3, box * 0.4), palette[1])
		swatch.draw_rect(Rect2(Vector2.ZERO, box), Color(accent, 0.9), false, 1.0)
	)
	return swatch

## A supply crate drawn from flat shapes: body, lid seam, latch. A case's colour is its
## collection's, so the crate matches the finishes it can hold.
func _case_glyph(collection: String, edge: float = 56.0) -> Control:
	var palette: Array = REVEAL.FINISH.PALETTES.get(collection, [DESIGN.GRAPHITE_HOVER, DESIGN.STEEL])
	var glyph := Control.new()
	glyph.mouse_filter = Control.MOUSE_FILTER_IGNORE
	glyph.custom_minimum_size = Vector2(edge, edge * 0.78)
	glyph.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	glyph.draw.connect(func():
		var box := glyph.size
		glyph.draw_rect(Rect2(0, box.y * 0.22, box.x, box.y * 0.78), Color(DESIGN.GRAPHITE_RAISED, 1.0))
		glyph.draw_rect(Rect2(0, box.y * 0.22, box.x, box.y * 0.78), DESIGN.LINE_STRONG, false, 1.0)
		glyph.draw_rect(Rect2(0, 0, box.x, box.y * 0.26), Color(palette[0], 1.0))
		glyph.draw_rect(Rect2(0, 0, box.x, box.y * 0.26), DESIGN.LINE_STRONG, false, 1.0)
		glyph.draw_rect(Rect2(box.x * 0.40, box.y * 0.18, box.x * 0.20, box.y * 0.22), DESIGN.GOLD)
		glyph.draw_rect(Rect2(box.x * 0.08, box.y * 0.50, box.x * 0.84, 2), Color(palette[1], 0.8))
	)
	return glyph

## What stands in for content: an empty list, a load in progress, or a failed refresh.
## The action, if any, does something real.
func _state_card(parent: Node, kind: String, title: String, body: String, action_label := "", action := Callable(), chip_text := "") -> PanelContainer:
	var tone: Color = {"empty": DESIGN.STEEL, "loading": DESIGN.GOLD, "error": DESIGN.CRIMSON_BRIGHT}[kind]
	var card := PanelContainer.new()
	card.name = "State_" + kind
	var style := DESIGN.box(Color(DESIGN.GRAPHITE, 0.9), Color(tone, 0.55), 1, Vector2(22, 18))
	style.border_width_left = 4
	style.border_color = tone
	card.add_theme_stylebox_override("panel", style)
	parent.add_child(card)
	var stack := VBoxContainer.new()
	stack.add_theme_constant_override("separation", 8)
	card.add_child(stack)
	var chip := _chip(chip_text if not chip_text.is_empty() else {"empty": "NOTHING HERE YET", "loading": "LOADING", "error": "CONNECTION PROBLEM"}[kind], tone)
	chip.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	stack.add_child(chip)
	_text(stack, title, 20)
	_text(stack, body, 15, MUTED)
	if kind == "loading" and not reduced_motion:
		var bar := ProgressBar.new()
		bar.name = "LoadingBar"
		bar.indeterminate = true
		bar.show_percentage = false
		bar.custom_minimum_size = Vector2(240, 6)
		stack.add_child(bar)
	if action.is_valid() and not action_label.is_empty():
		var button := _button(stack, action_label, action)
		button.name = "StateAction"
		DESIGN.apply_button(button, "primary" if kind == "error" else "secondary")
	return card

func _item_name(item: Dictionary) -> String:
	return str(item.get("name", item.get("definition_id", "Training rifle"))).replace("_", " ")

## The finish's own name ("Graphite" of "Obsidian / Graphite"): what tells two cards apart,
## so it leads a card and the collection sits beneath it instead of eating its width.
func _finish_name(item: Dictionary) -> String:
	var full := _item_name(item)
	return full.get_slice(" / ", 1) if " / " in full else full

## After choosing an item, the list re-renders and the inspector sits below all the cards;
## bring it to the top of the view so the choice visibly did something.
func _reveal_inspector() -> void:
	_reveal("SelectedInspector")

## Scrolls the tab so the named panel starts at the top of the view, once layout has settled.
func _reveal(node_name: String) -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	if not is_instance_valid(content):
		return
	var target := content.get_node_or_null(node_name) as Control
	var scroller := content.get_parent() as ScrollContainer
	if target != null and scroller != null:
		scroller.scroll_vertical = maxi(0, int(target.position.y) - 8)

func _inspect(parent: Node, item: Dictionary) -> void:
	var panel := _panel(parent)
	if parent == content:
		panel.get_parent().name = "SelectedInspector"
	_text(panel, _item_name(item), 23, GOLD)
	var inspector := INSPECTOR.new()
	inspector.item = item
	panel.add_child(inspector)
	_text(panel, "Drag to rotate  •  Pinch, scroll or use + / − to zoom", 13, MUTED)
	var zoom := HFlowContainer.new()
	panel.add_child(zoom)
	_button(zoom, "−", inspector.zoom.bind(0.3))
	_button(zoom, "+", inspector.zoom.bind(-0.3))
	_button(zoom, "RESET VIEW", inspector.reset_view)
	_text(panel, "%s  •  %s\nPattern %s  /  Wear %.4f  /  %s" % [item.get("rarity", "Standard"), item.get("collection", "Training"), whole(item.get("pattern_seed", 0)), float(item.get("wear", 0)), item.get("variant", "Standard")], 15, MUTED)
	var owned := false
	for instance in inventory:
		if item.has("id") and instance.get("id") == item.id:
			owned = true
	if owned:
		_text(panel, "Instance: " + str(item.id), 12, MUTED)
		_text(panel, "Reserved for exchange" if item.get("reserved", false) else "Available in inventory", 14)
	else:
		_text(panel, "PREVIEW ONLY  •  Not in your inventory", 14, GOLD)

func _inventory() -> void:
	if api.token.is_empty():
		_inspect(content, {"name": "AR-7 / Training graphite", "kind": "weapon_skin", "rarity": "Common", "pattern_seed": 44, "wear": 0.18})
		_text(content, "Standard training equipment is available to everyone. This preview is local and cannot be traded.", 15, MUTED)
		_knife_reference_button()
		_needs_account()
		return
	_text(content, "%d owned instances  •  Cosmetics never change weapon statistics" % inventory.size(), 15, MUTED)
	if inventory.is_empty():
		_state_card(content, "empty", "Your collection starts here", "Earn online Credits through validated matches, then open cases for finishes. Standard training equipment is always yours.", "BROWSE CASES", open_tab.bind("cases"))
	var filters := HFlowContainer.new()
	content.add_child(filters)
	var search := _field(filters, "Name, collection or rarity", inventory_filter)
	search.custom_minimum_size.x = 240
	_button(filters, "FILTER", func(): inventory_filter = search.text.strip_edges(); _render())
	var available := CheckButton.new()
	available.text = "AVAILABLE ONLY"
	available.button_pressed = inventory_available_only
	available.custom_minimum_size.y = 44
	available.toggled.connect(func(value): inventory_available_only = value; _render())
	filters.add_child(available)
	var cards := HFlowContainer.new()
	cards.add_theme_constant_override("h_separation", 10)
	cards.add_theme_constant_override("v_separation", 10)
	content.add_child(cards)
	var visible_count := 0
	for raw in inventory:
		var item: Dictionary = raw
		if not _matches_filter(item, inventory_filter) or (inventory_available_only and item.get("reserved", false)):
			continue
		visible_count += 1
		_item_card(cards, item)
	if visible_count == 0 and not inventory.is_empty():
		_text(content, "No owned instances match these filters.", 16, MUTED)
	if not selected.is_empty():
		_inspect(content, selected)
		var owned := false
		for item in inventory:
			if item.get("id", "") == selected.get("id", ""):
				owned = true
		if owned and selected.get("kind", "") == "weapon_skin":
			var equipped: Dictionary = equipped_loadout.get("rifle", {})
			var is_equipped: bool = equipped.get("id", "") == selected.get("id", "")
			_text(content, "EQUIPPED RIFLE FINISH  •  Visual only" if is_equipped else "Equip this owned rifle finish. Weapon damage, accuracy and handling remain identical.", 14, GOLD)
			var equip := _button(content, "UNEQUIP RIFLE FINISH" if is_equipped else "EQUIP RIFLE FINISH", func():
				_perform("/loadout", {"slot": "rifle", "item_id": null if is_equipped else selected.id}, "Rifle cosmetic loadout saved.", HTTPClient.METHOD_PUT))
			equip.disabled = selected.get("reserved", false) and not is_equipped
			if not selected.get("reserved", false) and selected.get("marketplace_eligible", true):
				var sell := _button(content, "SELL THIS FINISH", func():
					sell_preselect = str(selected.get("id", ""))
					open_tab("market"))
				sell.name = "SellSelected"

## One owned instance: a finish swatch from its collection's palette, name, rarity and
## state chips and, for finishes, its wear. Everything shown comes from the instance.
func _item_card(parent: Node, item: Dictionary) -> Button:
	var rarity := str(item.get("rarity", "Supply"))
	var kind := str(item.get("kind", ""))
	var reserved: bool = item.get("reserved", false)
	var is_selected: bool = not selected.is_empty() and selected.get("id", "") == item.get("id", "")
	var equipped := false
	for slot in equipped_loadout:
		if equipped_loadout[slot] is Dictionary and equipped_loadout[slot].get("id", "") == item.get("id", "") and item.has("id"):
			equipped = true
	var card := _button(parent, "", func(): selected = item; _render(); _reveal_inspector())
	card.name = "Item_" + str(item.get("id", _item_name(item)))
	card.tooltip_text = "%s\n%s  /  %s\n%s" % [_item_name(item), rarity.to_upper(), item.get("collection", "SUPPLY"), "RESERVED" if reserved else "INSPECT ITEM"]
	var accent: Color = REVEAL.FINISH.rarity_color(rarity) if kind == "weapon_skin" else DESIGN.STEEL
	for state in ["normal", "hover", "pressed", "focus"]:
		var style := DESIGN.box(DESIGN.GRAPHITE_HOVER if state == "hover" else DESIGN.GRAPHITE_RAISED, DESIGN.GOLD if is_selected or state == "focus" else DESIGN.LINE, 2 if is_selected else 1, Vector2(12, 10))
		style.border_width_left = 4
		style.border_color = DESIGN.GOLD if is_selected else accent
		card.add_theme_stylebox_override(state, style)
	var frame := MarginContainer.new()
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side in ["left", "right", "top", "bottom"]:
		frame.add_theme_constant_override("margin_" + side, 12)
	frame.add_theme_constant_override("margin_left", 16)
	card.add_child(frame)
	var row := HBoxContainer.new()
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_theme_constant_override("separation", 12)
	frame.add_child(row)
	var swatch: Control = _case_glyph(str(item.get("collection", "")), 44.0) if kind == "case" else (_key_glyph(44.0) if kind == "key" else _swatch(item, 44.0))
	row.add_child(swatch)
	var column := VBoxContainer.new()
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_theme_constant_override("separation", 4)
	column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(column)
	var title := _label(_finish_name(item) if kind == "weapon_skin" else _item_name(item), 16, DESIGN.TEXT)
	title.tooltip_text = _item_name(item)
	title.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	title.custom_minimum_size.x = 150
	column.add_child(title)
	column.add_child(_label(str(item.get("collection", "Collection supply")), 12, DESIGN.STEEL))
	var chips := HBoxContainer.new()
	chips.mouse_filter = Control.MOUSE_FILTER_IGNORE
	chips.add_theme_constant_override("separation", 6)
	column.add_child(chips)
	chips.add_child(_chip(rarity.to_upper() if kind == "weapon_skin" else kind.to_upper(), accent))
	if equipped:
		chips.add_child(_chip("EQUIPPED", DESIGN.GOLD))
	if reserved:
		chips.add_child(_chip("RESERVED", DESIGN.STEEL))
	if kind == "weapon_skin" and item.has("wear"):
		var wear_row := HBoxContainer.new()
		wear_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
		wear_row.add_theme_constant_override("separation", 6)
		column.add_child(wear_row)
		wear_row.add_child(_label("WEAR %.3f" % float(item.wear), 11, DESIGN.STEEL))
		var meter := ProgressBar.new()
		meter.mouse_filter = Control.MOUSE_FILTER_IGNORE
		meter.show_percentage = false
		meter.max_value = 1.0
		meter.value = clampf(float(item.wear), 0.0, 1.0)
		meter.custom_minimum_size = Vector2(60, 4)
		meter.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		meter.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		meter.add_theme_stylebox_override("background", DESIGN.box(DESIGN.OBSIDIAN, Color.TRANSPARENT, 0, Vector2.ZERO))
		meter.add_theme_stylebox_override("fill", DESIGN.box(Color(DESIGN.STEEL_BRIGHT, 0.7), Color.TRANSPARENT, 0, Vector2.ZERO))
		wear_row.add_child(meter)
	# A button ignores its children's size; the card is already in the tree (theme fonts
	# apply), so it takes its content's size now.
	var content_size := frame.get_combined_minimum_size()
	card.custom_minimum_size = Vector2(maxf(260, content_size.x), maxf(DESIGN.TOUCH_MIN, content_size.y))
	return card

func _chip(value: String, color: Color) -> PanelContainer:
	var chip := PanelContainer.new()
	chip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	chip.add_theme_stylebox_override("panel", DESIGN.box(Color(color, 0.16), Color(color, 0.5), 1, Vector2(6, 1)))
	chip.add_child(_label(value, 11, color.lightened(0.15)))
	return chip

## Published odds as a table: each rarity in its colour with a bar whose length is
## linearly proportional to its probability, so rare outcomes look as rare as they are.
func _odds_table(parent: Node, odds: Dictionary) -> void:
	var grid := GridContainer.new()
	grid.columns = 3
	grid.add_theme_constant_override("h_separation", 12)
	grid.add_theme_constant_override("v_separation", 6)
	parent.add_child(grid)
	var total := 0.0
	for rarity in odds:
		total += float(odds[rarity])
	for rarity in rarities_in_order(odds):
		var color: Color = REVEAL.FINISH.rarity_color(str(rarity))
		var name_label := _label(str(rarity).to_upper(), 13, color.lightened(0.1))
		name_label.custom_minimum_size.x = 110
		grid.add_child(name_label)
		var bar := ProgressBar.new()
		bar.show_percentage = false
		bar.max_value = maxf(total, 0.001)
		bar.value = float(odds[rarity])
		bar.custom_minimum_size = Vector2(220, 8)
		bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		bar.add_theme_stylebox_override("background", DESIGN.box(DESIGN.OBSIDIAN, Color.TRANSPARENT, 0, Vector2.ZERO))
		bar.add_theme_stylebox_override("fill", DESIGN.box(color, Color.TRANSPARENT, 0, Vector2.ZERO))
		grid.add_child(bar)
		var value := _label(percent_text(float(odds[rarity])), 13, DESIGN.TEXT)
		value.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		value.custom_minimum_size.x = 64
		grid.add_child(value)

func _knife_reference_button() -> void:
	var row := HFlowContainer.new()
	content.add_child(row)
	_button(row, "FIELD KNIFE REFERENCE", func(): _show_inspector_popup({"name": "K-4 / Field knife", "kind": "knife_reference", "collection": "Training reference"}, "REFERENCE MODEL • NOT OWNED"))

func _cases() -> void:
	if _needs_account():
		return
	var table: Dictionary = catalog.get("case_tables", {})
	var odds: Dictionary = table.get("probabilities", {})
	var probabilities: Array[String] = []
	for rarity in rarities_in_order(odds):
		probabilities.append("%s  %s" % [rarity, percent_text(float(odds[rarity]))])
	var key_item: Dictionary = {}
	for raw in inventory:
		if raw.get("kind") == "key" and not raw.get("reserved", false):
			key_item = raw
	# What the player can act on first: the cases they hold; then how the odds work; then the shop.
	var cases := _panel(content)
	_text(cases, "YOUR CASES", 20)
	var count := 0
	for raw in inventory:
		var item: Dictionary = raw
		if item.get("kind") != "case" or item.get("reserved", false):
			continue
		count += 1
		var row := HFlowContainer.new()
		row.add_theme_constant_override("h_separation", 14)
		row.add_theme_constant_override("v_separation", 6)
		cases.add_child(row)
		row.add_child(_case_glyph(str(item.get("collection", "")), 52.0))
		var holds := case_holds_text(str(item.get("collection", "")))
		var info := _label("%s\n%s%s" % [_item_name(item), "Ready: one key will be used" if not key_item.is_empty() else "Needs a collection key", "\n" + holds if not holds.is_empty() else ""], 16)
		info.custom_minimum_size.x = 230
		row.add_child(info)
		var button := _button(row, "OPEN", func():
			_confirm("Consume %s and one key?\n\n%s\n\nThese are the actual server probabilities. Results are final." % [_item_name(item), "  ·  ".join(probabilities)], _open_case.bind(item, key_item), "OPEN CASE  (FINAL)", "Uses 1 case and 1 key", false, "OPEN " + _item_name(item).to_upper()))
		button.name = "Open_" + str(item.get("id", ""))
		button.disabled = key_item.is_empty() or odds.is_empty()
		button.custom_minimum_size.y = DESIGN.TOUCH_COMFORT
		DESIGN.apply_button(button, "primary")
	if count == 0:
		_state_card(cases, "empty", "No cases to open", "Earn Credits in eligible online matches, then buy a case and a collection key below.")
	elif key_item.is_empty():
		_text(cases, "A collection key is required. Obtain one with earned Credits below.", 15, GOLD)
	var panel := _panel(content)
	_text(panel, "PUBLISHED PROBABILITIES  /  v" + str(table.get("version", "—")), 18, GOLD)
	_odds_table(panel, odds)
	_text(panel, "Each case rolls one rarity with these odds, and gives the finish of that rarity in its own collection. One case + one collection key are consumed. The server commits the reward before its reveal. Skipping has no effect on the outcome.", 15, MUTED)
	var store := _panel(content)
	_text(store, "COLLECTION SUPPLIES", 20)
	var verified: bool = account_summary().balance_verified
	var have := int(account.get("credits", 0)) if verified else 0
	if not verified:
		_text(store, "Your balance is not confirmed right now, so purchases are paused. Refresh to confirm it.", 15, GOLD)
	var supplies := 0
	for raw in catalog.get("definitions", []):
		var definition: Dictionary = raw
		if definition.get("kind") in ["case", "key"]:
			supplies += 1
			var price := int(definition.get("price", 0))
			var row := HFlowContainer.new()
			row.add_theme_constant_override("h_separation", 14)
			row.add_theme_constant_override("v_separation", 6)
			store.add_child(row)
			row.add_child(_case_glyph(str(definition.get("collection", "")), 52.0) if definition.get("kind") == "case" else _key_glyph(52.0))
			var holds := case_holds_text(str(definition.get("collection", ""))) if definition.get("kind") == "case" else ""
			var label := _label("%s\n%s earned Credits%s" % [definition.get("name", definition.id), credits_text(price), "\n" + holds if not holds.is_empty() else ""], 16)
			label.custom_minimum_size.x = 230
			row.add_child(label)
			var buy := _button(row, ("BUY" if have >= price else "NEED %s MORE" % credits_text(price - have)) if verified else "BALANCE UNAVAILABLE", func():
				_confirm("Buy %s for %s earned Credits? You have %s." % [definition.get("name", definition.id), credits_text(price), credits_text(have)], func(): _perform("/store/buy", {"definition_id": definition.id, "idempotency_key": api.key()}, "Supply added to inventory."), "BUY FOR %s CREDITS" % credits_text(price), "Cost: %s earned Credits" % credits_text(price), false, "BUY " + str(definition.get("name", definition.id)).to_upper()))
			buy.name = "BuySupply_" + str(definition.id)
			buy.disabled = not verified or have < price
			buy.custom_minimum_size.y = DESIGN.TOUCH_COMFORT
			DESIGN.apply_button(buy, "primary")
	if supplies == 0:
		_state_card(store, "empty", "No supplies are for sale", "The catalog lists no cases or keys right now.", "REFRESH", func(): _refresh())
	_collection_browser(content)

## A published probability as a player reads it: "58%", "0.1%". The server states them as
## percentages that are floats in JSON, so a whole number must not print as "58.0".
static func percent_text(value: float) -> String:
	return "%d%%" % int(round(value)) if is_equal_approx(value, round(value)) else "%s%%" % String.num(value, 2)

## The rarity order of the published odds, rarest last.
const RARITY_ORDER := ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic"]

## The rarities of a table of odds, commonest first, whatever order the server's JSON listed
## them in; a rarity this build does not know goes last.
func rarities_in_order(odds: Dictionary) -> Array:
	var keys: Array = odds.keys()
	keys.sort_custom(func(a, b):
		var ia := RARITY_ORDER.find(str(a))
		var ib := RARITY_ORDER.find(str(b))
		ia = RARITY_ORDER.size() if ia < 0 else ia
		ib = RARITY_ORDER.size() if ib < 0 else ib
		return ia < ib if ia != ib else str(a) < str(b))
	return keys

## What a case can hold, before it is opened: every finish in the catalog grouped by
## collection and ordered by rarity, each opening the 3D inspector. This only shows the
## catalog; the reward is committed by the server when a case is opened.
func _collection_browser(parent: Node) -> void:
	var panel := _panel(parent)
	_text(panel, "COLLECTIONS", 20)
	_text(panel, "Every finish a case can hold, by collection, with the chance a case of that collection gives it. Previews are not owned items.", 14, MUTED)
	var groups := {}
	for raw in catalog.get("definitions", []):
		var definition: Dictionary = raw
		if definition.get("kind") == "weapon_skin":
			var collection := str(definition.get("collection", "Training"))
			if not groups.has(collection):
				groups[collection] = []
			groups[collection].append(definition)
	if groups.is_empty():
		_state_card(panel, "empty", "No finishes are published", "The catalog lists no collections yet.", "REFRESH", func(): _refresh())
		return
	for collection in groups:
		var finishes: Array = groups[collection]
		finishes.sort_custom(func(a, b): return RARITY_ORDER.find(str(a.get("rarity", "Common"))) < RARITY_ORDER.find(str(b.get("rarity", "Common"))))
		var palette: Array = REVEAL.FINISH.PALETTES.get(collection, [DESIGN.GRAPHITE_HOVER, DESIGN.STEEL])
		var section := VBoxContainer.new()
		section.name = "Collection_" + str(collection).replace(" ", "_")
		section.add_theme_constant_override("separation", 8)
		panel.add_child(section)
		var heading := HBoxContainer.new()
		heading.add_theme_constant_override("separation", 10)
		section.add_child(heading)
		for tone: Color in palette:
			var chip := ColorRect.new()
			chip.color = tone
			chip.custom_minimum_size = Vector2(14, 28)
			heading.add_child(chip)
		var title := _label(str(collection).to_upper(), 16, GOLD)
		title.add_theme_font_override("font", DESIGN.heading_font())
		heading.add_child(title)
		heading.add_child(_label("%d FINISH%s" % [finishes.size(), "" if finishes.size() == 1 else "ES"], 12, MUTED))
		var flow := HFlowContainer.new()
		flow.add_theme_constant_override("h_separation", 8)
		flow.add_theme_constant_override("v_separation", 8)
		section.add_child(flow)
		for definition: Dictionary in finishes:
			var rarity := str(definition.get("rarity", "Common"))
			var accent: Color = REVEAL.FINISH.rarity_color(rarity)
			var card := _button(flow, "", func(): selected = definition; _show_inspector_popup(definition))
			card.name = "Finish_" + str(definition.get("id", ""))
			card.tooltip_text = "%s  /  %s  /  preview" % [definition.get("name", ""), rarity]
			for state in ["normal", "hover", "pressed", "focus"]:
				var style := DESIGN.box(DESIGN.GRAPHITE_HOVER if state == "hover" else DESIGN.GRAPHITE_RAISED, DESIGN.GOLD if state == "focus" else DESIGN.LINE, 1, Vector2(10, 8))
				style.border_width_left = 4
				style.border_color = accent
				card.add_theme_stylebox_override(state, style)
			var frame := HBoxContainer.new()
			frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
			frame.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
			frame.offset_left = 14
			frame.offset_right = -10
			frame.add_theme_constant_override("separation", 10)
			card.add_child(frame)
			frame.add_child(_swatch(definition, 32.0))
			var text := VBoxContainer.new()
			text.mouse_filter = Control.MOUSE_FILTER_IGNORE
			text.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			frame.add_child(text)
			var short_name := str(definition.get("name", "")).get_slice(" / ", 1) if " / " in str(definition.get("name", "")) else str(definition.get("name", ""))
			text.add_child(_label(short_name, 14))
			var chance := ""
			var published: Dictionary = catalog.get("case_tables", {}).get("probabilities", {})
			if published.has(rarity):
				chance = "  ·  " + percent_text(float(published[rarity]))
			text.add_child(_label(rarity.to_upper() + chance, 11, accent.lightened(0.15)))
			var content_size := frame.get_combined_minimum_size()
			card.custom_minimum_size = Vector2(maxf(190, content_size.x + 24), maxf(DESIGN.TOUCH_MIN, content_size.y + 16))

## A collection key: a bow and a toothed shaft, from flat shapes.
func _key_glyph(edge: float = 52.0) -> Control:
	var glyph := Control.new()
	glyph.mouse_filter = Control.MOUSE_FILTER_IGNORE
	glyph.custom_minimum_size = Vector2(edge, edge * 0.78)
	glyph.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	glyph.draw.connect(func():
		var box := glyph.size
		glyph.draw_arc(Vector2(box.x * 0.24, box.y * 0.5), box.y * 0.26, 0, TAU, 24, DESIGN.GOLD, 3.0)
		glyph.draw_rect(Rect2(box.x * 0.40, box.y * 0.44, box.x * 0.52, box.y * 0.12), DESIGN.GOLD)
		glyph.draw_rect(Rect2(box.x * 0.74, box.y * 0.52, box.x * 0.08, box.y * 0.22), DESIGN.GOLD)
		glyph.draw_rect(Rect2(box.x * 0.86, box.y * 0.52, box.x * 0.06, box.y * 0.16), DESIGN.GOLD)
	)
	return glyph

func _open_case(case_item: Dictionary, key_item: Dictionary) -> void:
	var result := await _perform("/cases/open", {"case_id": case_item.id, "key_id": key_item.id, "idempotency_key": api.key()}, "Reward committed to your inventory.")
	if result.has("_error"):
		return
	selected = result.get("item", {})
	_show_committed_reveal(selected)

func _show_committed_reveal(item: Dictionary) -> PopupPanel:
	var popup := PopupPanel.new()
	_style_popup(popup)
	add_child(popup)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 12)
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var scroll := _popup_scroll(popup)
	scroll.add_child(box)
	_text(box, "COLLECTION UNSEALED", 23, GOLD)
	_text(box, "Your reward is secured. Unsealing your collection finish…", 14, MUTED)
	var reel := REVEAL.new()
	reel.name = "CaseReel"
	reel.committed_item = item.duplicate(true)
	reel.reduced_motion = reduced_motion
	# Connect before entering the tree, including when reduced motion skips immediately.
	var result := _label("UNSEALING…", 19, GOLD)
	result.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var actions := HFlowContainer.new()
	var inspect := _button(actions, "INSPECT REWARD", func(): popup.hide(); _show_inspector_popup(item, "REWARD CONFIRMED"))
	inspect.disabled = true
	var skip := _button(actions, "SKIP", reel.skip)
	reel.finished.connect(func():
		result.text = "%s  /  %s" % [_item_name(item), item.get("rarity", "")]
		result.add_theme_color_override("font_color", REVEAL.FINISH.rarity_color(str(item.get("rarity", "Common"))))
		inspect.disabled = false
		skip.disabled = true)
	box.add_child(reel)
	box.add_child(result)
	box.add_child(actions)
	_button(actions, "CLOSE", popup.hide)
	popup.popup_hide.connect(popup.queue_free)
	_present_popup(popup, Vector2i(mini(760, int(size.x) - 44), 480))
	return popup

func _show_inspector_popup(item: Dictionary, title := "ITEM INSPECTOR") -> PopupPanel:
	var popup := PopupPanel.new()
	_style_popup(popup)
	add_child(popup)
	var box := VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var scroll := _popup_scroll(popup)
	scroll.add_child(box)
	_text(box, title, 20, GOLD)
	_inspect(box, item)
	_button(box, "CLOSE", popup.hide)
	popup.popup_hide.connect(popup.queue_free)
	_present_popup(popup, Vector2i(mini(640, int(size.x) - 40), mini(600, int(size.y) - 30)))
	return popup

func _popup_scroll(popup: PopupPanel) -> ScrollContainer:
	# Popups must scroll on short landscape screens; children cannot force them offscreen.
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	popup.add_child(scroll)
	return scroll

func _style_popup(popup: PopupPanel) -> void:
	var style := StyleBoxFlat.new()
	style.bg_color = Color("0e141e")
	style.border_color = Color("897851")
	style.set_border_width_all(1)
	style.set_corner_radius_all(6)
	style.content_margin_left = 12
	style.content_margin_right = 12
	style.content_margin_top = 12
	style.content_margin_bottom = 12
	popup.add_theme_stylebox_override("panel", style)

func _present_popup(popup: PopupPanel, desired: Vector2i) -> void:
	# Wrapped labels need their final width before Window computes its minimum
	# height. Lay out while hidden to avoid a full-screen transient popup.
	var safe: Rect2 = SAFE_AREA.viewport_rect(size)
	desired = Vector2i(mini(desired.x, int(safe.size.x) - 24), mini(desired.y, int(safe.size.y) - 24))
	popup.size = desired
	await get_tree().process_frame
	await get_tree().process_frame
	if is_instance_valid(popup) and not popup.is_queued_for_deletion():
		popup.popup(Rect2i(Vector2i(safe.position + (safe.size - Vector2(desired)) * 0.5), desired))

func _market() -> void:
	if _needs_account():
		return
	_text(content, "Community listings use earned Credits only. Ownership and payment settle together on the server.", 15, MUTED)
	var filter_row := HFlowContainer.new()
	content.add_child(filter_row)
	var search := _field(filter_row, "Filter name, rarity or collection", market_filter)
	search.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_button(filter_row, "FILTER", func(): market_filter = search.text.strip_edges(); _render())
	var sort_options := OptionButton.new()
	sort_options.custom_minimum_size.y = 44
	for label in ["PRICE: LOW TO HIGH", "PRICE: HIGH TO LOW", "ITEM NAME"]:
		sort_options.add_item(label)
	sort_options.selected = market_sort
	sort_options.item_selected.connect(func(index): market_sort = index; _render())
	filter_row.add_child(sort_options)
	var mine := CheckButton.new()
	mine.text = "MY LISTINGS"
	mine.custom_minimum_size.y = 44
	mine.button_pressed = market_mine_only
	mine.toggled.connect(func(value): market_mine_only = value; _render())
	filter_row.add_child(mine)
	var count := 0
	for listing in _filtered_listings():
		count += 1
		_listing_card(listing)
	if count == 0:
		_state_card(content, "empty", "No matching active listings", "Nothing is listed that matches these filters right now. New offers appear when other players list finishes.", "REFRESH LISTINGS", func(): _refresh())
	_listing_form()
	if not sell_preselect.is_empty():
		_reveal("SellForm")

## Selling: an owned, unreserved finish and an asking price, in one row. The fee is stated
## before the player commits, and again in the confirmation.
func _listing_form() -> void:
	var form := _panel(content)
	form.get_parent().name = "SellForm"
	_text(form, "SELL AN OWNED COSMETIC", 18, GOLD)
	var fee_percent := fee_percent_text()
	_text(form, "Transaction fee: %s of the asking price, deducted from seller proceeds on sale." % fee_percent, 14, MUTED)
	var row := HFlowContainer.new()
	row.add_theme_constant_override("h_separation", 10)
	row.add_theme_constant_override("v_separation", 8)
	form.add_child(row)
	var options := OptionButton.new()
	options.custom_minimum_size = Vector2(300, 44)
	row.add_child(options)
	var eligible: Array = []
	for item in inventory:
		if item.get("marketplace_eligible", not item.get("reserved", false)) and item.get("kind") == "weapon_skin":
			eligible.append(item)
			options.add_item(_item_name(item))
			if str(item.get("id", "")) == sell_preselect and not sell_preselect.is_empty():
				options.selected = options.item_count - 1
	var price := SpinBox.new()
	price.min_value = 1
	price.max_value = 1000000
	price.value = 100
	price.prefix = "Credits "
	price.custom_minimum_size = Vector2(200, 44)
	row.add_child(price)
	var list_button := _button(row, "CREATE LISTING", func():
		if options.selected >= 0:
			var item: Dictionary = eligible[options.selected]
			var asking := int(price.value)
			var fee := market_fee(asking)
			_confirm("List %s for %s earned Credits?\n\nIt will be reserved until sold or cancelled.\nOn a sale the market fee is %s (%s), so you receive %s." % [_item_name(item), credits_text(asking), credits_text(fee), fee_percent, credits_text(asking - fee)], func(): _perform("/market/list", {"item_id": item.id, "price": asking}, "Listing created."), "LIST FOR %s CREDITS" % credits_text(asking), "You will receive %s after the fee" % credits_text(asking - fee), false, "LIST " + _item_name(item).to_upper()))
	list_button.name = "CreateListing"
	list_button.disabled = eligible.is_empty()
	DESIGN.apply_button(list_button, "primary")
	if eligible.is_empty():
		_text(form, "You have no available weapon finishes to list.", 14, MUTED)

## One community listing: the finish, its price in earned Credits and exactly what a sale pays
## the seller, using the server's own fee rule. Buying and cancelling go through the same
## confirmation and server calls as before.
func _listing_card(listing: Dictionary) -> PanelContainer:
	var item: Dictionary = listing.get("item", {})
	var price := int(listing.get("price", 0))
	var fee := market_fee(price)
	var fee_percent := fee_percent_text()
	var mine := str(listing.get("seller_id")) == api.player_id
	var rarity := str(item.get("rarity", "Common"))
	var accent: Color = REVEAL.FINISH.rarity_color(rarity)
	var card := PanelContainer.new()
	card.name = "Listing_" + str(listing.get("id", ""))
	var style := DESIGN.box(DESIGN.GRAPHITE_RAISED, DESIGN.GOLD_DIM if mine else DESIGN.LINE, 1, Vector2(14, 12))
	style.border_width_left = 4
	style.border_color = accent
	card.add_theme_stylebox_override("panel", style)
	content.add_child(card)
	var flow := HFlowContainer.new()
	flow.add_theme_constant_override("h_separation", 18)
	flow.add_theme_constant_override("v_separation", 10)
	card.add_child(flow)
	flow.add_child(_swatch(item, 56.0))
	var identity := VBoxContainer.new()
	identity.custom_minimum_size.x = 230
	identity.add_theme_constant_override("separation", 4)
	flow.add_child(identity)
	var listing_title := DESIGN.ellipsize(_label(_finish_name(item), 18))
	listing_title.tooltip_text = _item_name(item)
	identity.add_child(listing_title)
	identity.add_child(DESIGN.ellipsize(_label(str(item.get("collection", "")), 13, MUTED)))
	var chips := HFlowContainer.new()
	chips.add_theme_constant_override("h_separation", 6)
	identity.add_child(chips)
	chips.add_child(_chip(rarity.to_upper(), accent))
	chips.add_child(_chip("WEAR %.3f" % float(item.get("wear", 0)), DESIGN.STEEL))
	if mine:
		chips.add_child(_chip("YOUR LISTING", DESIGN.GOLD))
	var money := VBoxContainer.new()
	money.custom_minimum_size.x = 210
	money.add_theme_constant_override("separation", 3)
	flow.add_child(money)
	var price_label := _label("%s EARNED CREDITS" % credits_text(price), 20, GOLD)
	price_label.name = "Price"
	price_label.add_theme_font_override("font", DESIGN.heading_font())
	money.add_child(price_label)
	var terms_text := ("You receive %s after a fee of %s (%s)." if mine else "The seller receives %s after a fee of %s (%s).") % [credits_text(price - fee), credits_text(fee), fee_percent]
	if fee == 0:
		terms_text = ("You receive all %s: at this price the %s fee rounds down to 0." if mine else "The seller receives all %s: at this price the %s fee rounds down to 0.") % [credits_text(price), fee_percent]
	var terms := _label(terms_text, 13, MUTED)
	terms.name = "Terms"
	terms.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	terms.custom_minimum_size.x = 210
	money.add_child(terms)
	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 8)
	flow.add_child(actions)
	var inspect := _button(actions, "INSPECT", _show_inspector_popup.bind(item))
	inspect.name = "Inspect"
	if mine:
		var cancel := _button(actions, "CANCEL MY LISTING", func(): _perform("/market/%s/cancel" % listing.id, {}, "Listing cancelled; item returned."))
		cancel.name = "Cancel"
	else:
		var verified: bool = account_summary().balance_verified
		var have := int(account.get("credits", 0)) if verified else 0
		var buy := _button(actions, ("BUY FOR %s" % credits_text(price) if have >= price else "NEED %s MORE" % credits_text(price - have)) if verified else "BALANCE UNAVAILABLE", func():
			_confirm("Buy this exact item for %s earned Credits?\n\n%s\n%s  ·  %s\nWear %.4f  ·  Pattern %s\n\nYou pay %s. The seller receives %s after a market fee of %s.\nYou have %s earned Credits." % [credits_text(price), _item_name(item), str(item.get("rarity", "")).to_upper(), item.get("collection", ""), float(item.get("wear", 0)), whole(item.get("pattern_seed", "—")), credits_text(price), credits_text(price - fee), credits_text(fee), credits_text(have)], func(): _perform("/market/%s/buy" % listing.id, {"idempotency_key": api.key(), "expected_price": price}, "Purchase confirmed."), "BUY FOR %s CREDITS" % credits_text(price), "You pay %s earned Credits" % credits_text(price), false, "BUY " + _item_name(item).to_upper()))
		buy.name = "Buy"
		buy.disabled = not verified or have < price
		buy.custom_minimum_size.y = DESIGN.TOUCH_COMFORT
		DESIGN.apply_button(buy, "primary")
	return card

func _matches_filter(item: Dictionary, query: String) -> bool:
	var terms := "%s %s %s" % [_item_name(item), item.get("rarity", ""), item.get("collection", "")]
	return query.is_empty() or query.to_lower() in terms.to_lower()

func _filtered_listings() -> Array:
	# Read-only presentation: never mutate canonical listing order or transaction IDs.
	var result: Array = listings.filter(func(listing):
		return _matches_filter(listing.get("item", {}), market_filter) and (not market_mine_only or str(listing.get("seller_id")) == api.player_id))
	result.sort_custom(func(a, b):
		if market_sort == 2:
			return _item_name(a.get("item", {})).naturalnocasecmp_to(_item_name(b.get("item", {}))) < 0
		return int(a.get("price", 0)) > int(b.get("price", 0)) if market_sort == 1 else int(a.get("price", 0)) < int(b.get("price", 0)))
	return result

func _trades() -> void:
	if _needs_account():
		return
	_text(content, "Both players confirm the same revision. Every offer change resets both confirmations. Items remain reserved until completion or cancellation.", 15, MUTED)
	var create := _panel(content)
	_text(create, "INVITE A PLAYER", 18, GOLD)
	var partner := _field(create, "Partner's player ID")
	_button(create, "SEND TRADE REQUEST", func(): _perform("/trades", {"partner_id": partner.text.strip_edges()}, "Trade request created."))
	if trades.is_empty():
		_state_card(content, "empty", "No trades yet", "Exchange player IDs with a friend, then send a request above. Both of you review the same revision before anything moves.", "SHOW MY PLAYER ID", open_tab.bind("profile"))
	for raw in trades:
		_trade_card(raw)

## Partner as "Display name" (id prefix): names are not unique, the id is. The name
## is flattened to one line and quoted so it can never read as part of the terms.
func partner_label(trade: Dictionary) -> String:
	var partner_id := _partner_id(trade)
	var names: Dictionary = trade.get("names", {})
	var display := DESIGN.plain_line(str(names.get(partner_id, "")))
	if display.is_empty():
		display = "Unknown player"
	return "\"%s\"" % display if partner_id.is_empty() else "\"%s\" (%s)" % [display, partner_id.left(8)]

func _partner_id(trade: Dictionary) -> String:
	var a: Variant = trade.get("a")
	var b: Variant = trade.get("b")
	var partner: Variant = b if str(a) == api.player_id else a
	return "" if partner == null else str(partner)

func _offer_lines(items: Variant) -> String:
	if not items is Array or (items as Array).is_empty():
		return "    nothing"
	var lines: Array[String] = []
	for item in items:
		if item is Dictionary:
			lines.append("    %s  ·  %s  ·  wear %.4f  ·  pattern %s" % [_item_name(item), str(item.get("rarity", "")).to_upper(), float(item.get("wear", 0)), whole(item.get("pattern_seed", "—"))])
		else:
			lines.append("    item " + str(item))
	return "\n".join(lines)

func _offer_count(items: Variant) -> int:
	return (items as Array).size() if items is Array else 0

func _plural(count: int, noun: String) -> String:
	return "%d %s%s" % [count, noun, "" if count == 1 else "s"]

## The exact terms of the displayed revision, stated at the moment of commitment.
func trade_confirmation_text(trade: Dictionary) -> String:
	var offers: Dictionary = trade.get("offers", {})
	var offer_items: Dictionary = trade.get("offer_items", offers)
	var partner_id := _partner_id(trade)
	var giving: Variant = offer_items.get(api.player_id, offers.get(api.player_id, []))
	var receiving: Variant = offer_items.get(partner_id, offers.get(partner_id, []))
	var text := "Trade with %s — revision %d\n\nYOU GIVE:\n%s\n\nYOU RECEIVE:\n%s" % [partner_label(trade), int(trade.get("revision", 0)), _offer_lines(giving), _offer_lines(receiving)]
	if not receiving is Array or (receiving as Array).is_empty():
		text += "\n\nYou receive nothing in return. This is a gift."
	text += "\n\nThe exchange completes atomically when both players confirm this revision. Any later edit cancels both confirmations."
	return text

## One side of a trade: what that player gives, item by item, with a way to inspect each.
func _trade_side(parent: Node, node_name: String, heading: String, items: Variant, tone: Color) -> PanelContainer:
	var box := PanelContainer.new()
	box.name = node_name
	box.custom_minimum_size.x = 400
	box.add_theme_stylebox_override("panel", DESIGN.box(DESIGN.OBSIDIAN, DESIGN.LINE, 1, Vector2(14, 10)))
	parent.add_child(box)
	var stack := VBoxContainer.new()
	stack.add_theme_constant_override("separation", 6)
	box.add_child(stack)
	var accent_bar := ColorRect.new()
	accent_bar.color = tone
	accent_bar.custom_minimum_size.y = 3
	stack.add_child(accent_bar)
	var title := _label(heading, 15, tone)
	title.add_theme_font_override("font", DESIGN.heading_font())
	stack.add_child(title)
	if not items is Array or (items as Array).is_empty():
		var none := _label("Nothing", 14, MUTED)
		none.name = "Nothing"
		stack.add_child(none)
		return box
	for item in items:
		if item is Dictionary:
			var row := HBoxContainer.new()
			row.add_theme_constant_override("separation", 10)
			stack.add_child(row)
			row.add_child(_swatch(item, 34.0))
			var text := VBoxContainer.new()
			text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			row.add_child(text)
			var side_title := DESIGN.ellipsize(_label(_finish_name(item), 15))
			side_title.tooltip_text = _item_name(item)
			text.add_child(side_title)
			text.add_child(DESIGN.ellipsize(_label("%s  ·  %s  ·  wear %.3f" % [str(item.get("collection", "")).to_upper(), str(item.get("rarity", "")).to_upper(), float(item.get("wear", 0))], 12, REVEAL.FINISH.rarity_color(str(item.get("rarity", "Common"))))))
			var look := _button(row, "INSPECT", _show_inspector_popup.bind(item))
			look.custom_minimum_size.x = 0
		else:
			stack.add_child(_label("item " + str(item), 13, MUTED))
	return box

func _trade_card(trade: Dictionary) -> void:
	var panel := _panel(content)
	var trade_id := str(trade.get("id", ""))
	var revision := int(trade.get("revision", 0))
	var offers: Dictionary = trade.get("offers", {})
	var offer_items: Dictionary = trade.get("offer_items", offers)
	var partner := partner_label(trade)
	var partner_id := _partner_id(trade)
	var header := HFlowContainer.new()
	header.add_theme_constant_override("h_separation", 8)
	panel.add_child(header)
	var title := _label("TRADE WITH " + partner, 18, GOLD)
	title.name = "TradeTitle"
	header.add_child(title)
	header.add_child(_chip(str(trade.get("state", "open")).to_upper(), DESIGN.GOLD))
	header.add_child(_chip("REVISION %d" % revision, DESIGN.STEEL))
	var sides := HFlowContainer.new()
	sides.add_theme_constant_override("h_separation", 14)
	sides.add_theme_constant_override("v_separation", 10)
	panel.add_child(sides)
	var giving: Variant = offer_items.get(api.player_id, offers.get(api.player_id, []))
	var receiving: Variant = offer_items.get(partner_id, offers.get(partner_id, []))
	_trade_side(sides, "TradeGive", "YOU GIVE", giving, DESIGN.GOLD)
	_trade_side(sides, "TradeReceive", "YOU RECEIVE", receiving, DESIGN.STEEL_BRIGHT)
	var gives_something: bool = giving is Array and not (giving as Array).is_empty()
	var gets_something: bool = receiving is Array and not (receiving as Array).is_empty()
	if gives_something and not gets_something:
		var gift := _chip("YOU RECEIVE NOTHING FOR THIS OFFER", DESIGN.CRIMSON_BRIGHT)
		gift.name = "GiftWarning"
		gift.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		panel.add_child(gift)
	var confirmations: Array = trade.get("confirmations", [])
	var confirmed := HFlowContainer.new()
	confirmed.add_theme_constant_override("h_separation", 8)
	panel.add_child(confirmed)
	var you_confirmed: bool = api.player_id in confirmations
	var they_confirmed: bool = not partner_id.is_empty() and partner_id in confirmations
	var you_chip := _chip("YOU CONFIRMED THIS REVISION" if you_confirmed else "YOU HAVE NOT CONFIRMED THIS REVISION", DESIGN.GOLD if you_confirmed else DESIGN.STEEL)
	you_chip.name = "ConfirmYou"
	confirmed.add_child(you_chip)
	var they_chip := _chip("THEY CONFIRMED" if they_confirmed else "THEY HAVE NOT CONFIRMED", DESIGN.GOLD if they_confirmed else DESIGN.STEEL)
	they_chip.name = "ConfirmPartner"
	confirmed.add_child(they_chip)
	if str(trade.get("state", "open")) not in ["open", "pending"]:
		return
	var offer_ids: Array[String] = []
	var current: Array = offers.get(api.player_id, [])
	for item in current:
		offer_ids.append(str(item.get("id")) if item is Dictionary else str(item))
	var original_ids := offer_ids.duplicate()
	original_ids.sort()
	_text(panel, "EDIT YOUR OFFER", 15)
	for raw in inventory:
		var item: Dictionary = raw
		var item_id := str(item.id)
		if item.get("reserved", false) and not item_id in offer_ids:
			continue
		var check := CheckButton.new()
		check.text = _item_name(item)
		check.button_pressed = item_id in offer_ids
		check.toggled.connect(func(enabled: bool):
			if enabled and not item_id in offer_ids:
				offer_ids.append(item_id)
			elif not enabled:
				offer_ids.erase(item_id))
		panel.add_child(check)
	_button(panel, "SAVE OFFER / RESET CONFIRMATIONS", func(): _perform("/trades/%s/offer" % trade_id, {"item_ids": offer_ids, "revision": revision}, "Offer updated. Both players must confirm the new revision.", HTTPClient.METHOD_PUT))
	_button(panel, "CONFIRM DISPLAYED REVISION", func():
		var proposed := offer_ids.duplicate()
		proposed.sort()
		if proposed != original_ids:
			_message("Your selection contains unsaved edits. Save your offer first, then review and confirm the new revision.", true)
			return
		var gives_n := _offer_count(giving)
		var gets_n := _offer_count(receiving)
		var gift: bool = gets_n == 0
		_confirm(trade_confirmation_text(trade), func(): _perform("/trades/%s/confirm" % trade_id, {"revision": revision}, "Confirmation recorded by server."),
			"CONFIRM GIFT  (RECEIVE NOTHING)" if gift else "CONFIRM THIS REVISION", "YOU GIVE %s   ·   YOU RECEIVE %s" % [_plural(gives_n, "item"), _plural(gets_n, "item")] + ("   ·   NOTHING IN RETURN" if gift else ""), gift, "CONFIRM TRADE  ·  REVISION %d" % revision))
	_button(panel, "CANCEL TRADE", func(): _perform("/trades/%s/cancel" % trade_id, {}, "Trade cancelled; reservations released."))
