extends RefCounted
## Complete item_json fixtures. Production validators never read this test helper.
const ITEM_ID := "c0000000-0000-4000-8000-000000000001"

static func item(definition_id := "key", item_id := ITEM_ID) -> Dictionary:
	var kind := "key" if definition_id == "key" else ("case" if definition_id.ends_with("_case") else "weapon_skin")
	return {"id": item_id, "definition_id": definition_id, "rarity": "Common",
		"pattern_seed": 123, "wear": 0.125, "variant": "standard",
		"collection": "Universal" if kind == "key" else "Obsidian", "kind": kind,
		"name": "Collection key" if kind == "key" else ("Obsidian case" if kind == "case" else "Obsidian / Graphite"),
		"reserved": false, "trade_eligible": true, "marketplace_eligible": true,
		"acquired_at": "2026-10-24T08:00:00.123456+00:00"}
