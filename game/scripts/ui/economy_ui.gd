class_name EconomyUI
extends Control
## Authoritative account views. Offline progress never enters an API payload.
signal closed
signal loadout_changed(slots: Dictionary)

const API = preload("res://scripts/ui/economy_api.gd")
const INSPECTOR = preload("res://scripts/ui/item_inspector.gd")
const REVEAL = preload("res://scripts/ui/case_reveal.gd")
const SAFE_AREA = preload("res://scripts/ui/safe_area.gd")
const DESIGN = preload("res://scripts/ui/design_tokens.gd")
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
var reduced_motion := false
var content: VBoxContainer
var status: Label
var wallet: Label
var dialog: ConfirmationDialog
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

func configure(profile: Dictionary) -> void:
	offline_profile = profile.duplicate(true)
	reduced_motion = bool(offline_profile.get("settings", {}).get("reduced_motion", false))

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
	dialog = ConfirmationDialog.new()
	dialog.title = "CONFIRM TRANSACTION"
	dialog.confirmed.connect(func():
		if pending_action.is_valid():
			pending_action.call()
		pending_action = Callable())
	add_child(dialog)
	theme = DESIGN.build_theme(float(offline_profile.get("settings", {}).get("ui_text_scale", 1.0)))

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
	node.add_theme_font_size_override("font_size", font_size)
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
	wallet.text = "ONLINE  •  %s  •  LEVEL %s  •  %s EARNED CREDITS" % [account.get("display_name", ""), account.get("level", 1), account.get("credits", 0)] if not api.token.is_empty() else "OFFLINE TRAINING  •  LOCAL PROGRESS ONLY"
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
	match active_tab:
		"profile": _profile()
		"inventory": _inventory()
		"cases": _cases()
		"market": _market()
		"trades": _trades()

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
		_text(online, "ONLINE ACCOUNT  /  " + str(account.get("display_name", "")), 22)
		var identity := _field(online, "Player ID", api.player_id)
		identity.editable = false
		_text(online, "XP: %s  •  Level: %s  •  Earned Credits: %s" % [account.get("xp", 0), account.get("level", 1), account.get("credits", 0)])
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
	loadout_changed.emit(equipped_loadout)
	busy = false
	_render()
	_message("Signed out. Local session cleared." if not result.has("_error") else "Local session cleared. Server revocation could not be confirmed; the remote session will expire.")

func _refresh() -> bool:
	if busy:
		return false
	if api.token.is_empty():
		_message("Sign in under PROFILE to connect to the online economy.")
		return false
	busy = true
	_message("Refreshing authoritative account data…")
	var me := await api.request("/me")
	if _failed(me):
		busy = false
		_render()
		return false
	account = me
	var owned := await api.request("/inventory")
	if _failed(owned):
		busy = false
		return false
	inventory = owned.get("items", [])
	var definitions := await api.request("/catalog")
	if _failed(definitions):
		busy = false
		return false
	catalog = definitions
	var loadout := await api.request("/loadout")
	if _failed(loadout):
		busy = false
		return false
	equipped_loadout = loadout.get("slots", {})
	loadout_changed.emit(equipped_loadout.duplicate(true))
	if active_tab == "market":
		var market_data := await api.request("/market")
		if _failed(market_data):
			busy = false
			return false
		listings = market_data.get("listings", [])
	if active_tab == "trades":
		var trade_data := await api.request("/trades")
		if _failed(trade_data):
			busy = false
			return false
		trades = trade_data.get("trades", [])
	busy = false
	_render()
	_message("Connected. Data confirmed by your economy server.")

	return true

func _message(value: String, error := false) -> void:
	status.text = value
	status.add_theme_color_override("font_color", Color("f0a1aa") if error else MUTED)

func _failed(result: Dictionary) -> bool:
	if result.has("_error"):
		if int(result.get("_status", 0)) == 401:
			account = {}
			inventory = []
			selected = {}
			equipped_loadout = {}
			loadout_changed.emit({})
			_render()
		_message(str(result["_error"]), true)
		return true
	return false

func _confirm(message: String, action: Callable) -> void:
	if busy:
		return
	dialog.dialog_text = message
	pending_action = action
	dialog.popup_centered(Vector2i(mini(560, int(size.x) - 40), 220))

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
		return result
	var refreshed := await _refresh()
	if refreshed:
		_message(message)
	else:
		_message("Transaction confirmed, but account refresh failed. Refresh before making another transaction.", true)
	return result

func _item_name(item: Dictionary) -> String:
	return str(item.get("name", item.get("definition_id", "Training rifle"))).replace("_", " ")

func _inspect(parent: Node, item: Dictionary) -> void:
	var panel := _panel(parent)
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
	_text(panel, "%s  •  %s\nPattern %s  /  Wear %.4f  /  %s" % [item.get("rarity", "Standard"), item.get("collection", "Training"), item.get("pattern_seed", 0), float(item.get("wear", 0)), item.get("variant", "Standard")], 15, MUTED)
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
		_text(content, "Your collection starts here. Earn online Credits through validated matches, then visit Cases.", 18)
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
		var rarity := str(item.get("rarity", "Supply"))
		var card := _button(cards, "%s\n%s  /  %s\n%s" % [_item_name(item), rarity.to_upper(), item.get("collection", "SUPPLY"), "RESERVED" if item.get("reserved", false) else "INSPECT ITEM"], func(): selected = item; _render())
		card.custom_minimum_size = Vector2(260, 104)
		card.alignment = HORIZONTAL_ALIGNMENT_LEFT
		var style := StyleBoxFlat.new()
		style.bg_color = Color("18222b")
		style.border_color = REVEAL.FINISH.rarity_color(rarity)
		style.border_width_left = 4
		style.set_corner_radius_all(4)
		style.content_margin_left = 16
		style.content_margin_right = 12
		style.content_margin_top = 12
		style.content_margin_bottom = 12
		card.add_theme_stylebox_override("normal", style)
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

	_knife_reference_button()

func _knife_reference_button() -> void:
	var row := HFlowContainer.new()
	content.add_child(row)
	_button(row, "FIELD KNIFE REFERENCE", func(): _show_inspector_popup({"name": "K-4 / Field knife", "kind": "knife_reference", "collection": "Training reference"}, "REFERENCE MODEL • NOT OWNED"))

func _cases() -> void:
	if _needs_account():
		return
	var table: Dictionary = catalog.get("case_tables", {})
	var odds: Dictionary = table.get("probabilities", {})
	var panel := _panel(content)
	_text(panel, "PUBLISHED PROBABILITIES  /  v" + str(table.get("version", "—")), 18, GOLD)
	var probabilities: Array[String] = []
	for rarity in odds:
		probabilities.append("%s  %s%%" % [rarity, odds[rarity]])
	_text(panel, "    ·    ".join(probabilities), 16)
	_text(panel, "One case + one collection key are consumed. The server commits the reward before its reveal. Skipping has no effect on the outcome.", 15, MUTED)
	var store := _panel(content)
	_text(store, "COLLECTION SUPPLIES", 20)
	for raw in catalog.get("definitions", []):
		var definition: Dictionary = raw
		if definition.get("kind") in ["case", "key"]:
			var price := int(definition.get("price", 0))
			_button(store, "%s  /  %d Credits" % [definition.get("name", definition.id), price], func():
				_confirm("Buy %s for %d earned Credits?" % [definition.get("name", definition.id), price], func(): _perform("/store/buy", {"definition_id": definition.id, "idempotency_key": api.key()}, "Supply added to inventory.")))
	var key_item: Dictionary = {}
	for raw in inventory:
		if raw.get("kind") == "key" and not raw.get("reserved", false):
			key_item = raw
	var cases := _panel(content)
	_text(cases, "YOUR CASES", 20)
	var count := 0
	for raw in inventory:
		var item: Dictionary = raw
		if item.get("kind") != "case" or item.get("reserved", false):
			continue
		count += 1
		var button := _button(cases, "OPEN  /  " + _item_name(item), func():
			_confirm("Consume %s and one key?\n\n%s\n\nThese are the actual server probabilities. Results are final." % [_item_name(item), "  ·  ".join(probabilities)], _open_case.bind(item, key_item)))
		button.disabled = key_item.is_empty() or odds.is_empty()
	if count == 0:
		_text(cases, "No available cases. Earn Credits in eligible online matches, then obtain supplies above.", 15, MUTED)
	elif key_item.is_empty():
		_text(cases, "A collection key is required. Obtain one with earned Credits above.", 15, GOLD)
	var previews := _panel(content)
	_text(previews, "COLLECTION FINISHES", 20)
	for raw in catalog.get("definitions", []):
		var definition: Dictionary = raw
		if definition.get("kind") == "weapon_skin":
			_button(previews, "%s  /  %s" % [definition.name, definition.rarity], func(): selected = definition; _show_inspector_popup(definition))

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
	var form := _panel(content)
	_text(form, "LIST AN OWNED COSMETIC", 18, GOLD)
	var fee_percent := float(catalog.get("market_fee_basis_points", 0)) / 100.0
	_text(form, "Transaction fee: %s%% of the asking price, deducted from seller proceeds on sale." % fee_percent, 14, MUTED)
	var options := OptionButton.new()
	options.custom_minimum_size.y = 44
	form.add_child(options)
	var eligible: Array = []
	for item in inventory:
		if item.get("marketplace_eligible", not item.get("reserved", false)) and item.get("kind") == "weapon_skin":
			eligible.append(item)
			options.add_item(_item_name(item))
	var price := SpinBox.new()
	price.min_value = 1
	price.max_value = 1000000
	price.value = 100
	price.prefix = "Credits "
	price.custom_minimum_size.y = 44
	form.add_child(price)
	var list_button := _button(form, "CREATE LISTING", func():
		if options.selected >= 0:
			var item: Dictionary = eligible[options.selected]
			_confirm("List %s for %d Credits? It will be reserved until sold or cancelled. A %s%% transaction fee is deducted from sale proceeds." % [_item_name(item), int(price.value), fee_percent], func(): _perform("/market/list", {"item_id": item.id, "price": int(price.value)}, "Listing created.")))
	list_button.disabled = eligible.is_empty()
	if eligible.is_empty():
		_text(form, "You have no available weapon finishes to list.", 14, MUTED)
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
		var item: Dictionary = listing.get("item", {})
		count += 1
		var row := _panel(content)
		_text(row, "%s  /  %s Credits" % [_item_name(item), listing.get("price", 0)], 18)
		_text(row, "%s  •  %s  •  Wear %.3f" % [str(item.get("rarity", "Common")).to_upper(), item.get("collection", ""), float(item.get("wear", 0))], 14, REVEAL.FINISH.rarity_color(str(item.get("rarity", "Common"))))
		_button(row, "INSPECT", _show_inspector_popup.bind(item))
		if str(listing.get("seller_id")) == api.player_id:
			_button(row, "CANCEL MY LISTING", func(): _perform("/market/%s/cancel" % listing.id, {}, "Listing cancelled; item returned."))
		else:
			_button(row, "BUY WITH EARNED CREDITS", func():
				_confirm("Buy this exact item for %s earned Credits?\n\n%s\n%s  ·  %s\nWear %.4f  ·  Pattern %s\n\nThe seller receives the price minus the market fee." % [listing.get("price", 0), _item_name(item), str(item.get("rarity", "")).to_upper(), item.get("collection", ""), float(item.get("wear", 0)), item.get("pattern_seed", "—")], func(): _perform("/market/%s/buy" % listing.id, {"idempotency_key": api.key()}, "Purchase confirmed.")))
	if count == 0:
		_text(content, "No matching active listings. Refresh to check for new offers.", 18, MUTED)

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
		_text(content, "No trades yet. Exchange player IDs with a friend to start.", 18, MUTED)
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
			lines.append("    %s  ·  %s  ·  wear %.4f  ·  pattern %s" % [_item_name(item), str(item.get("rarity", "")).to_upper(), float(item.get("wear", 0)), item.get("pattern_seed", "—")])
		else:
			lines.append("    item " + str(item))
	return "\n".join(lines)

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

func _trade_card(trade: Dictionary) -> void:
	var panel := _panel(content)
	var trade_id := str(trade.get("id", ""))
	var revision := int(trade.get("revision", 0))
	_text(panel, "TRADE %s  /  REVISION %d" % [trade_id.left(8), revision], 18, GOLD)
	_text(panel, "State: " + str(trade.get("state", "open")), 15)
	var offers: Dictionary = trade.get("offers", {})
	var offer_items: Dictionary = trade.get("offer_items", offers)
	var partner := partner_label(trade)
	_text(panel, "WITH  " + partner, 15)
	for owner in offers:
		_text(panel, ("YOU GIVE" if str(owner) == api.player_id else partner + " GIVES"), 15, GOLD)
		var offered: Variant = offer_items.get(owner, offers[owner])
		if offered is Array:
			if offered.is_empty():
				_text(panel, "No items offered", 14, MUTED)
			for item in offered:
				if item is Dictionary:
					_button(panel, _item_name(item), _show_inspector_popup.bind(item))
				else:
					_text(panel, str(item), 13, MUTED)
	var confirmations: Array = trade.get("confirmations", [])
	_text(panel, "%d / 2 confirmations  •  %s" % [confirmations.size(), "You confirmed this revision" if api.player_id in confirmations else "You have not confirmed this revision"], 14, MUTED)
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
		_confirm(trade_confirmation_text(trade), func(): _perform("/trades/%s/confirm" % trade_id, {"revision": revision}, "Confirmation recorded by server.")))
	_button(panel, "CANCEL TRADE", func(): _perform("/trades/%s/cancel" % trade_id, {}, "Trade cancelled; reservations released."))
