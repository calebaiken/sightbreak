extends SceneTree
## Graphics tiers: the presets are monotonic, tier 1 is exactly the pre-tier STANDARD look, phones are capped, and
## the arena really applies ambient occlusion and shadow softness only where a tier says so.
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
func run() -> void:
	check(SBGraphicsQuality.TIERS.size() == SBGraphicsQuality.COUNT and SBGraphicsQuality.LABELS.size() == SBGraphicsQuality.COUNT, "Every tier has a preset and a settings label")
	# Tiers 0 and 1 are the old LOW and STANDARD pipelines: no shadows or detail maps on LOW, MSAA 2x with shadows on STANDARD, and neither runs a post pass or filters anisotropically.
	var low := SBGraphicsQuality.config(SBGraphicsQuality.LOW)
	var medium := SBGraphicsQuality.config(SBGraphicsQuality.MEDIUM)
	check(not low.shadows and not low.detail_maps and not low.smoke_full and low.msaa == Viewport.MSAA_DISABLED, "LOW keeps the old no-shadow, no-detail-map, light-smoke preset")
	check(medium.shadows and medium.detail_maps and medium.smoke_full and medium.msaa == Viewport.MSAA_2X, "MEDIUM keeps the old STANDARD preset")
	check(not low.post and not medium.post and not low.ssao and not medium.ssao, "The tiers phones run keep the single-pass pipeline")
	check(low.aniso == Viewport.ANISOTROPY_DISABLED and medium.aniso == Viewport.ANISOTROPY_DISABLED, "The tiers phones run filter textures as before")
	for tier in SBGraphicsQuality.COUNT:
		check(bool(SBGraphicsQuality.config(tier).post) or not bool(SBGraphicsQuality.config(tier).ssao), "Tier %d never asks for ambient occlusion without the post pass it needs" % tier)
	for tier in range(1, SBGraphicsQuality.COUNT):
		var lower := SBGraphicsQuality.config(tier - 1)
		var higher := SBGraphicsQuality.config(tier)
		check(int(higher.msaa) >= int(lower.msaa), "Tier %d never lowers anti-aliasing" % tier)
		check(bool(higher.shadows) or not bool(lower.shadows), "Tier %d never drops shadows" % tier)
		check(bool(higher.ssao) or not bool(lower.ssao), "Tier %d never drops ambient occlusion" % tier)
		check(bool(higher.post) or not bool(lower.post), "Tier %d never drops the post pass" % tier)
		check(int(higher.aniso) >= int(lower.aniso), "Tier %d never lowers texture filtering" % tier)
	check(SBGraphicsQuality.clamp_tier(3, false) == SBGraphicsQuality.ULTRA and SBGraphicsQuality.clamp_tier(-4, false) == SBGraphicsQuality.LOW, "Desktop accepts every tier")
	check(SBGraphicsQuality.clamp_tier(3, true) == SBGraphicsQuality.MOBILE_MAX and SBGraphicsQuality.clamp_tier(2, true) == SBGraphicsQuality.MOBILE_MAX, "Phones and tablets stop at MEDIUM")
	check(SBGraphicsQuality.available_labels(true).size() == 2 and SBGraphicsQuality.available_labels(false).size() == 4, "The settings screen offers only tiers the platform may run")
	var arena := RelayYard.new()
	for tier in SBGraphicsQuality.COUNT:
		SBGraphicsQuality.apply(arena, root.get_viewport(), tier, 1.0, false)
	SBGraphicsQuality.current = SBGraphicsQuality.MEDIUM
	root.add_child(arena)
	await frames(2)
	var world_environment: WorldEnvironment = arena.find_children("*", "WorldEnvironment", false, false)[0]
	var sun: DirectionalLight3D = arena.find_children("*", "DirectionalLight3D", false, false)[0]
	check(not world_environment.environment.ssao_enabled and not world_environment.environment.adjustment_enabled and sun.shadow_enabled, "A world built on MEDIUM runs the single-pass pipeline with sun shadows")
	for tier in SBGraphicsQuality.COUNT:
		SBGraphicsQuality.apply(root, root.get_viewport(), tier, 1.0, false)
		var settings := SBGraphicsQuality.config(tier)
		check(world_environment.environment.ssao_enabled == bool(settings.ssao), "Tier %d sets ambient occlusion to %s" % [tier, settings.ssao])
		check(world_environment.environment.adjustment_enabled == bool(settings.post), "Tier %d sets the post pass to %s" % [tier, settings.post])
		check(sun.shadow_enabled == bool(settings.shadows), "Tier %d sets the sun shadow" % tier)
		check(root.get_viewport().anisotropic_filtering_level == settings.aniso, "Tier %d sets texture filtering" % tier)
		check(root.get_viewport().msaa_3d == settings.msaa, "Tier %d sets anti-aliasing" % tier)
		check(SBUtility.high_quality_smoke == bool(settings.smoke_full), "Tier %d sets the smoke budget" % tier)
	SBGraphicsQuality.apply(root, root.get_viewport(), 5, 1.0, true)
	check(SBGraphicsQuality.current == SBGraphicsQuality.MOBILE_MAX and not world_environment.environment.ssao_enabled, "A phone asking for ULTRA runs MEDIUM and no ambient occlusion")
	SBGraphicsQuality.apply(root, root.get_viewport(), SBGraphicsQuality.MEDIUM, 1.0, false)
	print("graphics_quality_test: %d checks, %d failures" % [checks, failures])
	quit(1 if failures > 0 else 0)
