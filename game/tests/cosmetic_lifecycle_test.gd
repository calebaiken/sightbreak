extends SceneTree
## Independent native resource regression: repeated real SubViewport studio lifetimes.
const INSPECTOR = preload("res://scripts/ui/item_inspector.gd")
const REVEAL = preload("res://scripts/ui/case_reveal.gd")
var checks := 0
var failures := 0
var textures: Array[int] = []
var fixture := {"id": "qa-no-owned-value", "kind": "weapon_skin", "definition_id": "obsidian_rare", "collection": "Obsidian", "rarity": "Rare", "pattern_seed": 100, "wear": 0.1}

func _initialize() -> void:
	call_deferred("run")

func check(ok: bool, reason: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(reason)

func drawn_frames(count: int) -> void:
	for index in count:
		await process_frame
		await RenderingServer.frame_post_draw

func run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("Cosmetic lifecycle requires an actual renderer")
		quit(2)
		return
	root.size = Vector2i(960, 720)
	for cycle in 6:
		var inspector = INSPECTOR.new()
		inspector.item = fixture
		inspector.position = Vector2(160, 140)
		inspector.size = Vector2(640, 360)
		root.add_child(inspector)
		await drawn_frames(3)
		var retired_item: WeakRef = weakref(inspector.pivot.get_child(0))
		inspector.show_item({"kind": "case"})
		await drawn_frames(2)
		check(retired_item.get_ref() == null, "Repeated item change releases prior mesh hierarchy")
		inspector.show_item({"kind": "knife_reference"})
		await drawn_frames(2)
		var old_studio: WeakRef = weakref(inspector.world)
		var old_inspector: WeakRef = weakref(inspector)
		inspector.queue_free()
		inspector = null
		await drawn_frames(3)
		check(old_inspector.get_ref() == null and old_studio.get_ref() == null, "Inspector and SubViewport release after close")
		var reveal = REVEAL.new()
		reveal.committed_item = fixture
		reveal.position = Vector2(160, 140)
		reveal.size = Vector2(640, 360)
		root.add_child(reveal)
		await drawn_frames(3)
		reveal.progress = 0.6
		await drawn_frames(2)
		reveal.skip()
		await drawn_frames(2)
		var old_reveal: WeakRef = weakref(reveal)
		var old_reveal_studio: WeakRef = weakref(reveal.world)
		reveal.queue_free()
		reveal = null
		await drawn_frames(3)
		check(old_reveal.get_ref() == null and old_reveal_studio.get_ref() == null, "Reveal and SubViewport release after skipped transition")
		textures.append(RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED))
		print("COSMETIC_LIFECYCLE cycle=", cycle, " texture_bytes=", textures[-1])
	check(textures[-1] <= textures[1] + 65536, "Warmed cosmetic texture allocation plateaus")
	print("COSMETIC_LIFECYCLE_TEST checks=%d failures=%d texture_bytes=%s" % [checks, failures, textures])
	quit(1 if failures else 0)
