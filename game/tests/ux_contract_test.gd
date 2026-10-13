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
	check(cards.sidearm.disabled and "EQUIPPED" in cards.sidearm.text, "standard sidearm shows as equipped, not purchasable")
	check(not cards.smg.disabled and cards.rifle.disabled and "NEED 900 MORE" in cards.rifle.text, "cards distinguish affordable weapons from the exact shortfall")
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
