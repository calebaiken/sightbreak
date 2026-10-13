extends SceneTree
## Native widget smoke coverage; optional live backend auth with ECONOMY_UI_TEST_URL.
const UI = preload("res://scripts/ui/economy_ui.gd")
var failures: Array[String] = []
var capture_dir := OS.get_environment("ECONOMY_CAPTURE_DIR")

func _initialize() -> void:
	call_deferred("run")

func check(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)
		push_error(message)

func capture(name: String) -> void:
	if capture_dir.is_empty():
		return
	await process_frame
	await RenderingServer.frame_post_draw
	DirAccess.make_dir_recursive_absolute(capture_dir)
	var shot := root.get_texture().get_image()
	check(shot.save_png(capture_dir.path_join(name + ".png")) == OK, "Save native screenshot " + name)

func run() -> void:
	var ui := UI.new()
	ui.configure({"xp": 430, "credits": 900000, "settings": {"reduced_motion": true}})
	root.add_child(ui)
	await process_frame
	check(ui.api.token.is_empty(), "Offline profile cannot create an online session")
	check(ui.account.is_empty(), "Offline balance cannot become an authoritative wallet")
	check(ui.reduced_motion, "Reduced motion preference is respected")
	for tab in ["inventory", "cases", "market", "trades", "profile"]:
		ui.open_tab(tab)
		await process_frame
		check(ui.content.get_child_count() > 1, "Offline %s renders content" % tab)
	check(not ui.api.configure_url("http://untrusted.example").is_empty(), "Remote plaintext server rejected")
	check(not ui.api.configure_url("http://10.attacker.example").is_empty(), "LAN-looking public hostname rejected")
	check(not ui.api.configure_url("https://name:password@example.org").is_empty(), "URL credentials rejected")
	check(ui.api.configure_url("http://127.0.0.1:8080").is_empty(), "Loopback development server accepted")
	var uuid := ui.api.key()
	check(uuid.length() == 36 and uuid[14] == "4", "Idempotency identifier is UUID v4")
	var first := {"id": "a", "name": "Obsidian / Graphite", "definition_id": "obsidian_common", "rarity": "Common", "kind": "weapon_skin", "collection": "Obsidian", "pattern_seed": 100, "wear": 0.12, "reserved": false}
	ui.api.token = "fixture-render-only"
	ui.api.player_id = "self"
	ui.account = {"display_name": "QA render fixture", "credits": 500, "xp": 200, "level": 1}
	ui.inventory = [first, {"id": "case", "kind": "case", "name": "Obsidian case", "definition_id": "obsidian_case"}, {"id": "key", "kind": "key", "definition_id": "key"}]
	ui.catalog = {"market_fee_basis_points": 300, "case_tables": {"version": "1", "probabilities": {"Common": 58, "Uncommon": 26, "Rare": 11, "Epic": 4, "Legendary": 0.9, "Mythic": 0.1}}, "definitions": [{"id": "key", "name": "Collection key", "kind": "key", "price": 150}, {"id": "obsidian_common", "name": "Obsidian / Graphite", "kind": "weapon_skin", "rarity": "Common"}]}
	ui.selected = first
	ui.listings = [{"id": "listing", "seller_id": "other", "price": 100, "item": first}]
	ui.trades = [{"id": "trade", "revision": 1, "state": "open", "offers": {"self": ["a"], "other": []}, "offer_items": {"self": [first], "other": []}, "confirmations": []}]
	for tab in ["inventory", "cases", "market", "trades", "profile"]:
		ui.active_tab = tab
		ui._render()
		await process_frame
		check(ui.content.get_child_count() > 1, "Online %s renders populated content" % tab)
		await capture("economy_" + tab)
	ui.reduced_motion = false
	var reveal_popup := ui._show_committed_reveal(first)
	var reel = reveal_popup.get_child(0).get_child(2)
	var reveal_events := [0]
	reel.finished.connect(func(): reveal_events[0] += 1)
	await create_timer(0.35).timeout
	check(reveal_popup.size.y < 600 and reveal_popup.position.y >= 0, "Carousel popup remains inside the viewport")
	check(reel.progress > 0.0 and reel.progress < 1.0 and not reel.revealed, "Case carousel advances before reveal")
	check(reel.committed_item.id == first.id, "Carousel preserves the server committed instance")
	await capture("economy_case_carousel")
	var early_progress: float = reel.progress
	await create_timer(0.35).timeout
	check(reel.progress > early_progress, "Case carousel continues in the same direction")
	reel.skip()
	reel.skip()
	check(reel.revealed and reel.progress == 1.0, "Skip aligns and reveals the committed reward immediately")
	check(reveal_events[0] == 1, "Repeated skip emits one reveal event")
	await capture("economy_case_result")
	reveal_popup.hide()
	await process_frame
	var inspector_popup := ui._show_inspector_popup(first)
	for frame in 4:
		await process_frame
	check(inspector_popup.visible and inspector_popup.size.y <= 720, "Inspector popup is visible and fits the viewport")
	var model = inspector_popup.find_children("*", "SubViewportContainer", true, false)[0]
	var original_rotation: Vector3 = model.pivot.rotation
	model._rotate_model(Vector2(30, 15))
	check(model.pivot.rotation != original_rotation, "Inspector drag rotates the actual 3D model")
	model.zoom(-100)
	check(is_equal_approx(model.distance, 2.3), "Inspector zoom stays within near limit")
	model.zoom(100)
	check(is_equal_approx(model.distance, 5.0), "Inspector zoom stays within far limit")
	model.zoom(-1.5)
	await capture("economy_inspector")
	inspector_popup.hide()
	await process_frame
	ui.reduced_motion = true
	var reduced_popup := ui._show_committed_reveal(first)
	var reduced_reel = reduced_popup.get_child(0).get_child(2)
	for frame in 4:
		await process_frame
	check(reduced_reel.revealed, "Reduced motion bypasses carousel movement")
	reduced_popup.hide()
	await process_frame
	ui.api.logout()
	var server := OS.get_environment("ECONOMY_UI_TEST_URL")
	if not server.is_empty():
		check(ui.api.configure_url(server).is_empty(), "Live backend URL accepted")
		var name := "ui_" + ui.api.key().replace("-", "").left(16)
		var result: Dictionary = await ui.api.request("/auth/register", HTTPClient.METHOD_POST, {"username": name, "password": "Temporary-UI-Test-481!", "display_name": "Native UI test"})
		check(result.has("token"), "Live native HTTP registration succeeds: " + str(result.get("_error", "")))
		if result.has("token"):
			ui.api.token = result.token
			ui.api.player_id = result.player_id
			ui.active_tab = "cases"
			await ui._refresh()
			check(int(ui.account.get("credits", -1)) == 0, "Real account starts zero despite offline balance")
			check(ui.inventory.is_empty(), "Real account inventory starts empty")
			check(ui.equipped_loadout.is_empty(), "Real account has no fabricated equipped cosmetics")
			check(ui.catalog.has("case_tables"), "Native HTTP retrieves real probability tables")
			var purchase: Dictionary = await ui.api.request("/store/buy", HTTPClient.METHOD_POST, {"definition_id": "key", "idempotency_key": ui.api.key()})
			check(purchase.has("_error"), "Native purchase cannot spend offline credits")
			var unequip: Dictionary = await ui.api.request("/loadout", HTTPClient.METHOD_PUT, {"slot": "rifle", "item_id": null})
			check(unequip.get("slots", {"unexpected": true}).is_empty(), "Native loadout unequip persists an empty owned loadout")
			await ui._logout()
			check(ui.api.token.is_empty(), "Signout clears bearer token")
	ui.queue_free()
	await process_frame
	if failures.is_empty():
		print("PASS: Economy native screens, offline separation, URL policy, UUIDs" + (" and live HTTP authentication" if not server.is_empty() else ""))
		quit(0)
	else:
		quit(1)
