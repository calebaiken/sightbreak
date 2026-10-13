extends SceneTree
## Reproducible CPU serialization/authorization measurement; not GPU or mobile FPS.
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	var game := TacticalMatch.new()
	game.configure({"mode": "offline"})
	root.add_child(game)
	game.set_physics_process(false)
	await physics_frame
	var samples: Array[int] = []
	var bytes_total := 0
	var bytes_max := 0
	var baseline_bytes := var_to_bytes(game._snapshot()).compress(FileAccess.COMPRESSION_DEFLATE).size()
	var baseline_samples: Array[int] = []
	game._privacy.rays = 0
	for tick in range(120):
		var start := Time.get_ticks_usec()
		var full := var_to_bytes(game._snapshot()).compress(FileAccess.COMPRESSION_DEFLATE)
		baseline_samples.append(Time.get_ticks_usec() - start)
		assert(not full.is_empty())
		start = Time.get_ticks_usec()
		for recipient in range(1, 11):
			var packed := var_to_bytes(game._snapshot(recipient)).compress(FileAccess.COMPRESSION_DEFLATE)
			bytes_total += packed.size()
			bytes_max = maxi(bytes_max, packed.size())
		samples.append(Time.get_ticks_usec() - start)
		await process_frame
	samples.sort()
	baseline_samples.sort()
	print("NETWORK_PROFILE " + JSON.stringify({"fixture": "Relay Yard initial ten actors, 120 ten-recipient batches", "engine": Engine.get_version_info().string,
		"full_snapshot_bytes": baseline_bytes, "full_encode_p50_usec": baseline_samples[60], "full_encode_p95_usec": baseline_samples[114],
		"authorized_batch_p50_usec": samples[60], "authorized_batch_p95_usec": samples[114], "authorized_batch_max_usec": samples.back(),
		"authorized_mean_bytes": float(bytes_total) / 1200.0, "authorized_max_bytes": bytes_max,
		"ray_queries": game._privacy.rays, "note": "CPU headless; payload bytes exclude ENet/IP headers; no transport or physical device claim"}))
	game.queue_free()
	await process_frame
	await process_frame
	quit()
