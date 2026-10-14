extends SceneTree
## Interface contracts from CLAUDE_AUDIT_0.3 (M-10, M-11, L-3, U-1–U-6). These
## assert information and state, not aesthetics; captures cover appearance.
const Design = preload("res://scripts/ui/design_tokens.gd")
var checks := 0
var failures := 0

func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures += 1
		push_error(message)

func _initialize() -> void:
	call_deferred("run")

func frames(count: int) -> void:
	for i in count: await physics_frame

func buttons_in(node: Node) -> Array:
	return node.find_children("*", "Button", true, false)

func run() -> void:
	var main = load("res://main.tscn").instantiate()
	root.add_child(main)
	await frames(3)
	# U-4: every menu action meets the 48 px touch minimum.
	var small: Array[String] = []
	for page in ["show_menu", "show_settings", "show_connect", "show_progress"]:
		main.call(page)
		await frames(2)
		for node: Button in buttons_in(main.ui):
			if node.is_visible_in_tree() and node.size.y < Design.TOUCH_MIN - 0.5:
				small.append("%s:%s" % [page, node.text])
	check(small.is_empty(), "menu touch targets are at least 48 px tall: " + str(small))
	await menu_contracts(main)
	# Accessibility: interface text size scales labels and the shared theme.
	var probe: Label = main.label("x", 20)
	var base_size: int = probe.get_theme_font_size("font_size")
	probe.free()
	main.profile.data.settings.ui_text_scale = 1.3
	main.ui.theme = main.build_theme()
	probe = main.label("x", 20)
	check(probe.get_theme_font_size("font_size") == 26 and base_size == 20 and main.ui.theme.default_font_size > Design.TYPE_BODY, "interface text size scales labels and theme")
	probe.free()
	main.profile.data.settings.ui_text_scale = 1.0
	main.ui.theme = main.build_theme()

	# M-11, U-5, L-3: armory states the exact terms and its active section.
	main.open_economy("market")
	await frames(2)
	var armory = main.economy_panel
	check(armory.tab_buttons.market.button_pressed and not armory.tab_buttons.inventory.button_pressed, "active armory tab is visibly selected")
	armory.open_tab("trades")
	check(armory.tab_buttons.trades.button_pressed and not armory.tab_buttons.market.button_pressed, "tab selection follows navigation")
	armory.api.player_id = "aaaaaaaa-0000-4000-8000-000000000001"
	var partner := "bbbbbbbb-0000-4000-8000-000000000002"
	var trade := {"id": "t1", "a": armory.api.player_id, "b": partner, "revision": 3, "names": {armory.api.player_id: "Me", partner: "Kestrel"},
		"offers": {armory.api.player_id: ["i1"], partner: ["i2"]},
		"offer_items": {armory.api.player_id: [{"id": "i1", "name": "Obsidian / Graphite", "rarity": "Common", "wear": 0.1234, "pattern_seed": 77}],
			partner: [{"id": "i2", "name": "Blacksite / Gilded Fracture", "rarity": "Mythic", "wear": 0.0456, "pattern_seed": 901}]}, "confirmations": [], "state": "open"}
	var terms: String = armory.trade_confirmation_text(trade)
	check("\"Kestrel\" (bbbbbbbb)" in terms and "revision 3" in terms, "trade confirmation names the partner and revision")
	check(terms.find("YOU GIVE") < terms.find("Obsidian / Graphite") and terms.find("YOU RECEIVE") < terms.find("Blacksite / Gilded Fracture") and terms.find("Obsidian / Graphite") < terms.find("YOU RECEIVE"), "trade confirmation lists what each side gives and receives")
	check("wear 0.1234" in terms and "pattern 901" in terms and "MYTHIC" in terms, "trade confirmation identifies exact instances")
	check(not "gift" in terms.to_lower(), "two-sided trade is not labelled a gift")
	# A display name cannot inject lines that read as terms.
	trade.names[partner] = "Ally\n\nYOU RECEIVE:\n  Mythic x3\u202e"
	var spoofed: String = armory.trade_confirmation_text(trade)
	check(spoofed.count("\nYOU RECEIVE:") == 1 and spoofed.begins_with("Trade with \"Ally YOU RECEIVE: Mythic x3\" (bbbbbbbb)") and not "\u202e" in spoofed, "partner names are one quoted line inside the trade terms")
	trade.names[partner] = "Kestrel"
	trade.offers[partner] = []
	trade.offer_items[partner] = []
	check("nothing in return" in armory.trade_confirmation_text(trade), "one-sided trade warns that nothing is received")
	armory.open_tab("profile")
	await frames(1)
	var hints: Array = []
	for field: LineEdit in armory.find_children("*", "LineEdit", true, false): hints.append(field.placeholder_text)
	check("Password (12–128 characters)" in hints, "password hint matches the server's 12-character minimum")
	main.show_menu()
	await frames(2)

	# Match HUD contracts.
	main.start_match({"mode": "offline", "difficulty": "easy", "name": "UX QA"})
	await frames(4)
	var game = main.match_game
	var me: SBActor = game.local_actor()
	# U-3: requisition cards show real availability.
	me.credits = 1500
	main.show_buy()
	await frames(1)
	var cards: Dictionary = {}
	for node: Button in buttons_in(main.overlay):
		if node.name.begins_with("Buy_"): cards[node.name.trim_prefix("Buy_")] = node
	check(cards.size() == 4, "requisition offers every weapon")
	var chip := func(card: Button) -> String: return (card.find_child("State", true, false) as Label).text
	check(cards.sidearm.disabled and chip.call(cards.sidearm) == "EQUIPPED" and "EQUIPPED" in cards.sidearm.tooltip_text, "standard sidearm shows as equipped, not purchasable")
	check(not cards.smg.disabled and chip.call(cards.smg) == "BUY" and cards.rifle.disabled and chip.call(cards.rifle) == "NEED 900 MORE" and "NEED 900 MORE" in cards.rifle.tooltip_text, "cards distinguish affordable weapons from the exact shortfall")
	for card: Button in cards.values():
		var content := (card.get_child(0) as Control).get_combined_minimum_size()
		check(card.size.y + 1 >= content.y and card.size.x + 1 >= content.x and card.size.y >= Design.TOUCH_MIN, "requisition card %s holds its content and is a full touch target (%s for %s)" % [card.name, card.size, content])
	main.close_overlay()
	game.phase = "live"
	main.show_buy()
	await frames(1)
	var any_enabled := false
	for node: Button in buttons_in(main.overlay):
		if node.name.begins_with("Buy_") and not node.disabled: any_enabled = true
	check(not any_enabled, "no weapon is purchasable outside the preparation phase")
	main.close_overlay()
	# M-10: the offline field menu really pauses training.
	game.time_left = 50.0
	main.toggle_pause()
	await frames(20)
	check(main.paused and is_equal_approx(game.time_left, 50.0) and game.process_mode == Node.PROCESS_MODE_DISABLED, "offline field menu pauses the match clock")
	main.toggle_pause()
	await frames(20)
	check(not main.paused and game.time_left < 50.0, "closing the field menu resumes the match")
	game.options.mode = "client"
	main.set_match_suspended(true)
	check(game.process_mode == Node.PROCESS_MODE_INHERIT and not main.match_suspended, "network matches are never paused by a client menu")
	game.options.mode = "offline"
	# U-1: alive pips, kill feed, side marker and utility counts.
	var enemy: SBActor = game.actors[6]
	enemy.apply_damage(500, me.actor_id, true)
	main._process(0.016)
	check(int(main.defend_pips.get_meta("alive")) == 4 and int(main.attack_pips.get_meta("alive")) == 5, "alive pips track eliminations per squad")
	check(main.kill_feed.get_child_count() == 1, "elimination enters the kill feed")
	check(Design.plain_line("A\nB\tC\u2028D\u202eE  ", 32) == "A B C D E" and Design.plain_line("Zoë ✦ Kestrel", 32) == "Zoë ✦ Kestrel", "names are flattened to visible single-line text without touching ordinary Unicode")
	var feed_text := ""
	for node: Label in main.kill_feed.find_children("*", "Label", true, false): feed_text += node.text + "|"
	check(me.display_name in feed_text and enemy.display_name in feed_text and "HEADSHOT" in feed_text, "kill feed names killer, victim and headshot")
	for i in range(6): game.elimination_reported.emit(7, 2, false)
	check(main.kill_feed.get_child_count() == main.KILL_FEED_ROWS, "kill feed keeps a bounded number of rows")
	check("ATTACK" in main.squad_label.text, "HUD states the player's squad")
	check("FRAG ×1" in main.utility_label.text and main.touch.counts.get("grenade") == 1, "utility counts are visible in HUD and on touch buttons")
	var funds_rect: Rect2 = main.funds_label.get_global_rect()
	var health_rect: Rect2 = main.health_label.get_global_rect()
	check(main.funds_label.text.begins_with(str(me.credits) + " ") and not "FUNDS" in main.utility_label.text and not "FUNDS" in main.status_label.text, "match funds are one label, not repeated in the utility row or status line")
	check(funds_rect.end.y <= health_rect.position.y + 1 and absf(funds_rect.position.x - health_rect.position.x) < 1, "the funds label sits directly above the health readout and bar, left aligned")
	# Layouts saved under 0.3 store the old TEAM/BUY defaults, which the radar now covers.
	main.touch.restore_layout({"buy": [0.19, 0.14], "score": [0.08000001, 0.14], "fire": [0.5, 0.5], "smoke": [0.3, 0.2]})
	check(main.touch.positions.buy == main.touch.DEFAULT_POSITIONS.buy and main.touch.positions.score == main.touch.DEFAULT_POSITIONS.score, "saved layouts with untouched 0.3 TEAM/BUY positions move below the radar")
	check(main.touch.positions.fire == Vector2(0.5, 0.5) and main.touch.positions.smoke == Vector2(0.3, 0.2), "positions the player chose are kept")
	main.touch.restore_layout({"buy": [0.25, 0.14]})
	check(main.touch.positions.buy == Vector2(0.25, 0.14), "a moved TEAM/BUY button is never relocated")
	main.touch.reset_layout()
	# U-1: the radar never lists opponents.
	var kinds: Array = []
	var opponents := 0
	for marker in main.radar.markers():
		kinds.append(marker.kind)
		if marker.team == 1 - me.team: opponents += 1
	check(opponents == 0 and kinds.has("self") and kinds.count("teammate") == 4, "radar shows self and teammates but never opponents")
	# Crosshair reports the actual spread cone.
	me.velocity = Vector3.ZERO
	var still: float = main.crosshair_gap(me)
	me.velocity = Vector3(5.1, 0, 0)
	var moving: float = main.crosshair_gap(me)
	me.velocity = Vector3.ZERO
	check(moving > still + 2.0, "reticle opens while moving (%.1f → %.1f px)" % [still, moving])
	main.leave_match()
	await frames(3)
	main.queue_free()
	await frames(3)
	print("UX_CONTRACT_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)


const MENU_SIZES := [Vector2i(960, 720), Vector2i(1024, 768), Vector2i(1280, 720), Vector2i(1560, 720), Vector2i(1600, 720)]
const MENU_SCALES := [0.85, 1.0, 1.15, 1.3]
const MENU_ACTIONS := {"lan": "connect", "record": "progress", "settings": "settings", "inventory": "economy", "cases": "economy", "market": "economy", "trades": "economy"}
## Names a player can really have (plain_line keeps 32 characters): short, long ASCII,
## CJK with no spaces, and accents with combining marks.
const MENU_NAMES := ["Operator", "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef", "白雪・シラユキ・テスト・ネーム・ロング・名前・白雪・シラユキ", "Zoe\u0308 Ångström-Nguyễn Muñoz Çelik"]
## A pseudo-translation: every string about 60 % longer, as German or Russian can be.
func expanded_labels(main: Node) -> Dictionary:
	var out := {}
	for id in main.MENU_LABELS:
		var text: String = main.MENU_LABELS[id]
		out[id] = text + "   " + text.substr(0, int(text.length() * 0.6)) if id in ["deploy", "lan", "inventory", "cases", "market", "trades", "record", "settings", "policy", "build", "record_title", "xp_to", "credits", "online"] else text
	return out

## Controls that are not inside the menu's scroller, or that are, split out.
func menu_controls(main: Node) -> Dictionary:
	var scroll: ScrollContainer = main.ui.find_child("MenuScroll", true, false)
	var fixed: Array[Control] = []
	var scrolled: Array[Control] = []
	for node: Control in main.ui.find_children("*", "Control", true, false):
		if not node.is_visible_in_tree() or node is ScrollBar or node == scroll: continue
		if node.get_parent() == main.ui: continue
		(scrolled if scroll != null and scroll.is_ancestor_of(node) else fixed).append(node)
	return {"scroll": scroll, "fixed": fixed, "scrolled": scrolled}

func menu_case(main: Node, context: String, dimensions: Vector2i, signed_in: bool) -> String:
	main.show_menu()
	await frames(4)
	var parts := menu_controls(main)
	var scroll: ScrollContainer = parts.scroll
	var layout: Dictionary = main.menu_layout
	var outside: Array[String] = []
	for node: Control in parts.fixed + parts.scrolled:
		var rect := node.get_global_rect()
		var horizontal_bad: bool = rect.position.x < -1 or rect.end.x > dimensions.x + 1
		var vertical_bad: bool = parts.fixed.has(node) and (rect.position.y < -1 or rect.end.y > dimensions.y + 1)
		if (horizontal_bad or vertical_bad) and rect.size.x > 0:
			outside.append("%s:%s:%s" % [node.get_class(), node.name, rect])
	check(outside.is_empty(), context + " no menu control leaves the screen " + str(outside.slice(0, 3)))
	var bar := scroll.get_v_scroll_bar()
	var scrolls: bool = bar.visible and bar.max_value > bar.page + 1
	var nav: Control = main.ui.find_child("MenuNav", true, false)
	var status: Control = main.ui.find_child("MenuStatus", true, false)
	var record: Control = main.ui.find_child("RecordCard", true, false)
	check(nav != null and status != null and record != null, context + " has its nav, status and record card")
	if nav == null or status == null or record == null: return "missing"
	check(not nav.get_global_rect().intersects(status.get_global_rect()), context + " the nav and status columns do not overlap")
	# Robustness: columns share a row only with real slack (MENU_SAFETY) to spare, so a
	# font with wider glyphs cannot tip the layout over; otherwise they stack.
	if layout.side_by_side:
		var slack: float = layout.region.x - (nav.get_combined_minimum_size().x + status.get_combined_minimum_size().x + main.MENU_COLUMN_GAP)
		check(slack >= main.MENU_SAFETY - 0.5, context + " side-by-side columns keep %d px of slack (%.1f)" % [main.MENU_SAFETY, slack])
	else:
		check(nav.get_global_rect().end.y <= status.get_global_rect().position.y + 1, context + " stacked columns do not overlap")
	check(scroll.get_h_scroll_bar().max_value <= scroll.get_h_scroll_bar().page + 1 or not scroll.get_h_scroll_bar().visible, context + " no horizontal scrolling")
	# Every entry is a real touch target and, if the menu scrolls, reachable by scrolling.
	var short: Array[String] = []
	var unreachable: Array[String] = []
	var entries: Array = main.ui.find_children("Menu_*", "Button", true, false)
	check(entries.size() == 8, context + " eight menu actions (%d)" % entries.size())
	for entry: Button in entries:
		if entry.size.y < Design.TOUCH_MIN - 0.5 or entry.size.x < Design.TOUCH_MIN: short.append(entry.name)
		scroll.ensure_control_visible(entry)
	await frames(2)
	for entry: Button in entries:
		var rect := entry.get_global_rect()
		var view := scroll.get_global_rect()
		if rect.position.y < view.position.y - 1 or rect.end.y > view.end.y + 1: unreachable.append(entry.name)
	# Text must fit its box. Only user-supplied names may truncate; with the real strings
	# nothing else may, at any size or scale. A pseudo-translation is longer than the
	# layout is designed for, so there truncation is the intended last resort.
	var clipped: Array[String] = []
	for node: Control in main.ui.find_children("*", "Label", true, false) + main.ui.find_children("*", "Button", true, false):
		if not node.is_visible_in_tree() or node.get_meta("user_text", false): continue
		var face: Font = node.get_theme_font("font")
		var text_width := face.get_string_size(node.text, HORIZONTAL_ALIGNMENT_LEFT, -1, node.get_theme_font_size("font_size")).x
		var room: float = node.size.x - (node.get_theme_stylebox("normal").get_minimum_size().x if node is Button else 0.0)
		if text_width > room + 0.5 and node.text.length() > 0:
			clipped.append("%s '%s' needs %d has %d" % [node.get_class(), node.text.left(24), text_width, room])
	if not context.contains("pseudo"):
		check(clipped.is_empty(), context + " no text is truncated or collapsed " + str(clipped.slice(0, 3)))
	check(short.is_empty(), context + " every action is a full touch target " + str(short))
	check(unreachable.is_empty(), context + " every action can be scrolled into view " + str(unreachable))
	scroll.scroll_vertical = 0
	# What the card says is what the profile and account store.
	var xp: int = int(main.profile.data.xp)
	var level: int = main.Profile.level_for_xp(xp)
	var to_next: Label = main.ui.find_child("XPToNext", true, false)
	check(to_next != null and to_next.text.begins_with(str(main.Profile.xp_for_level(level + 1) - xp) + " "), context + " XP to the next level comes from the profile's own rule (%s)" % (to_next.text if to_next else "none"))
	check((main.ui.find_child("OnlineIdentity", true, false) != null) == signed_in, context + " the online identity shows only while signed in")
	return "%s side_by_side=%s compact=%s scrolls=%s slack=%s" % [context, layout.side_by_side, layout.compact, scrolls, "%.0f" % layout.slack if layout.side_by_side else "stacked"]

func menu_contracts(main: Node) -> void:
	# Level curve: the card's rule is the profile's own, in both directions.
	for level in range(1, 12):
		var begins: int = main.Profile.xp_for_level(level)
		check(main.Profile.level_for_xp(begins) == level and (level == 1 or main.Profile.level_for_xp(begins - 1) == level - 1), "level %d begins at %d XP" % [level, begins])
	# Every action opens its screen. Deploy starts a match and leaving returns to the menu.
	root.content_scale_size = Vector2i(1280, 720)
	root.size = Vector2i(1280, 720)
	main.profile.data.settings.ui_text_scale = 1.0
	main.ui.theme = main.build_theme()
	for id in MENU_ACTIONS:
		main.show_menu()
		await frames(3)
		var entry: Button = main.ui.find_child("Menu_" + id, true, false)
		check(entry != null and not entry.disabled, "menu action %s exists and is enabled" % id)
		if entry == null: continue
		entry.pressed.emit()
		await frames(3)
		check(main.screen == MENU_ACTIONS[id], "menu action %s opens the %s screen (%s)" % [id, MENU_ACTIONS[id], main.screen])
		if MENU_ACTIONS[id] == "economy":
			check(is_instance_valid(main.economy_panel) and main.economy_panel.active_tab == id, "menu action %s opens the %s tab" % [id, id])
	main.show_menu()
	await frames(3)
	(main.ui.find_child("Menu_deploy", true, false) as Button).pressed.emit()
	await frames(4)
	check(main.screen == "game" and is_instance_valid(main.match_game), "menu action deploy starts an offline match")
	main.leave_match()
	await frames(3)
	check(main.screen == "menu", "leaving the match returns to the menu")
	# The matrix: sizes x text scales x names x account states, then a pseudo-translation.
	var table: Array[String] = []
	var panel = main.economy_panel
	var original_name: String = main.profile.data.display_name
	for dimensions in MENU_SIZES:
		root.content_scale_size = dimensions
		root.size = dimensions
		for text_size in MENU_SCALES:
			main.profile.data.settings.ui_text_scale = text_size
			main.ui.theme = main.build_theme()
			for signed_in in [false, true]:
				panel.api.token = "fixture-render-only" if signed_in else ""
				panel.account = {"display_name": MENU_NAMES[1] if signed_in else "", "credits": 1234567, "xp": 200, "level": 1}
				for name_index in MENU_NAMES.size():
					main.profile.data.display_name = MENU_NAMES[name_index]
					main.menu_labels = {}
					var context := "%s %d%% text, %s, name %d:" % [dimensions, roundi(text_size * 100), "signed in" if signed_in else "no account", name_index]
					var line := await menu_case(main, context, dimensions, signed_in)
					table.append(line)
				main.menu_labels = expanded_labels(main)
				table.append(await menu_case(main, "%s %d%% text, %s, pseudo-translation:" % [dimensions, roundi(text_size * 100), "signed in" if signed_in else "no account"], dimensions, signed_in))
				main.menu_labels = {}
	for line in table: print("MENU_LAYOUT ", line)
	panel.api.token = ""
	panel.account = {}
	main.profile.data.display_name = original_name
	main.profile.data.settings.ui_text_scale = 1.0
	main.ui.theme = main.build_theme()
	root.content_scale_size = Vector2i(1280, 720)
	root.size = Vector2i(1280, 720)
	main.show_menu()
	await frames(2)
