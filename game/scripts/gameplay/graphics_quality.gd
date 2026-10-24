class_name SBGraphicsQuality
extends RefCounted
## Graphics presets: the one place that says what each quality level switches on.
##
## Every entry uses only what the Compatibility renderer of Godot 4.7.2 was measured to apply (the project renders
## with it on desktop and mobile; screen-space reflections and indirect lighting are not available and are not
## listed). Two settings that look like quality levers do nothing there and are deliberately absent: directional
## shadow blur and the soft-shadow filter level (docs/art/GRAPHICS_BACKLOG.md, evidence M6).
## LOW and MEDIUM keep the pipeline phones already run. HIGH and ULTRA are desktop only until a physical-device
## frame-time record exists.
const LOW := 0
const MEDIUM := 1
const HIGH := 2
const ULTRA := 3
const COUNT := 4
## The most a phone or tablet may select. Raise it only with a device frame-time record.
const MOBILE_MAX := MEDIUM

const LABELS: Array[String] = [
	"LOW  ·  NO SHADOWS",
	"MEDIUM  ·  SHADOWS",
	"HIGH  ·  FILMIC TONES",
	"ULTRA  ·  OCCLUSION + 4X AA",
]

## Each key is read by apply() or by RelayYard.apply_graphics(). A new key needs a reader and a check in
## tests/graphics_quality_test.gd.
##   post: resolve the tonemap in a post pass (keeps sunlit surfaces from clipping; costs one full-screen pass)
##   ssao: screen-space ambient occlusion, half resolution (needs post)
##   aniso: anisotropic filtering of the surface textures at grazing angles
##   impact_holes: how many bullet holes stay on the walls (one pooled draw; the ring replaces the oldest)
const TIERS: Array[Dictionary] = [
	{"shadows": false, "msaa": Viewport.MSAA_DISABLED, "detail_maps": false, "smoke_full": false,
		"post": false, "ssao": false, "aniso": Viewport.ANISOTROPY_DISABLED, "impact_holes": 12},
	{"shadows": true, "msaa": Viewport.MSAA_2X, "detail_maps": true, "smoke_full": true,
		"post": false, "ssao": false, "aniso": Viewport.ANISOTROPY_DISABLED, "impact_holes": 32},
	{"shadows": true, "msaa": Viewport.MSAA_2X, "detail_maps": true, "smoke_full": true,
		"post": true, "ssao": false, "aniso": Viewport.ANISOTROPY_4X, "impact_holes": 48},
	{"shadows": true, "msaa": Viewport.MSAA_4X, "detail_maps": true, "smoke_full": true,
		"post": true, "ssao": true, "aniso": Viewport.ANISOTROPY_16X, "impact_holes": 64},
]

## The tier a freshly built world starts with; apply() keeps it current.
static var current := MEDIUM

static func clamp_tier(value: int, mobile: bool = OS.has_feature("mobile")) -> int:
	return clampi(value, LOW, MOBILE_MAX if mobile else ULTRA)

## Tiers the settings screen offers on this platform.
static func available_labels(mobile: bool = OS.has_feature("mobile")) -> Array[String]:
	var labels: Array[String] = []
	for tier in range(clamp_tier(ULTRA, mobile) + 1):
		labels.append(LABELS[tier])
	return labels

static func config(tier: int) -> Dictionary:
	return TIERS[clampi(tier, LOW, ULTRA)]

## Applies a tier to a viewport and every world under `root`. Safe to call repeatedly.
static func apply(root: Node, viewport: Viewport, tier: int, render_scale: float, mobile: bool = OS.has_feature("mobile")) -> void:
	tier = clamp_tier(tier, mobile)
	current = tier
	var settings := config(tier)
	SBUtility.high_quality_smoke = bool(settings.smoke_full)
	viewport.msaa_3d = settings.msaa
	viewport.anisotropic_filtering_level = settings.aniso
	# The 3D world can render below native resolution (the HUD stays sharp): the main fill-rate control on
	# phones. Compatibility supports bilinear scaling.
	viewport.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	viewport.scaling_3d_scale = clampf(render_scale, 0.5, 1.0)
	if root == null:
		return
	for node in root.find_children("*", "Node3D", true, false):
		if node.has_method("apply_graphics"):
			node.apply_graphics(settings)
	for light in root.find_children("*", "DirectionalLight3D", true, false):
		light.shadow_enabled = bool(settings.shadows)
