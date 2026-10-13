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
	var purchase: Dictionary = await b._perform("/market/%s/buy" % listing.id, {"idempotency_key": b.api.key()})
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
	var one: Dictionary = await a._perform(path+"/confirm", {"revision":2})
	var two: Dictionary = await b._perform(path+"/confirm", {"revision":2})
	check(one.get("state")=="open" and two.get("state")=="completed","native two-sided confirmation settles")
	await a._refresh()
	check(a.inventory.size()==1 and a.inventory[0].id==reward_id and b.inventory.size()==1 and b.inventory[0].id==fixtures.skin,"native inventory refresh reflects both atomic ownership swaps")
	check(a.equipped_loadout.is_empty(), "native loadout automatically clears transferred item")
	print("NATIVE_REAL_ECONOMY_QA %d/%d passed (real case reveal, marketplace, trade; fictional isolated balances)" % [count-failures,count])
	a.queue_free(); b.queue_free()
	await process_frame
	await process_frame
	quit(0 if failures==0 else 1)
