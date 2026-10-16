class_name SBViewmodelShading
extends RefCounted
## Shading for the first-person weapon and arms. Presentation only.
##
## The viewmodel is drawn with its own projection, narrower than the world camera's
## 82 degrees, so it is not stretched at the screen edges. It keeps the camera's
## aspect ratio and position, so it still sits where the weapon node puts it. Its depth
## is compressed toward the near plane, so it never clips into walls the player stands
## against, but it keeps its own ordering. An ambient floor and a view rim keep it
## readable in shade and against a bright sky without an extra light pass.
## Only first-person materials may contain these snippets. Writing POSITION anywhere in
## a shader makes the engine skip its own vertex transform for every draw of it, so a
## shader shared with inspection or third person must not include PROJECT at all
## (CosmeticMaterial keeps a separate first-person variant for this reason).

## Vertical field of view of the viewmodel, in degrees (about 68 horizontal at 4:3).
const FOV := 54.0
## Fraction of the remaining depth range the viewmodel occupies in front of the world.
const DEPTH := 0.08
## Emission added from albedo, so the darkest shade never falls to black.
const FLOOR := 0.10
## The least albedo the fill sees: charcoal gloves (0.03 linear) would otherwise get a fifth of the fill the tan
## magazine does and fall to near black in shade, with no form to read. Only the emitted fill uses it.
const LIFT := 0.30
## Rim light strength, on silhouette edges facing away from the camera.
const RIM := 0.22
## The least roughness of the rifle's painted metal (receiver, handguard) in first person. The sky the engine reflects has a bright
## horizon band with dark ground below it; at roughness 0.3 to 0.5 the metal's reflection slides across that edge as the reload rolls
## and lifts the weapon (a few degrees are enough), and the receiver went from 54 to 83 median luma and from graphite to pale
## blue-grey (docs/reports/media/art-v9/rifle-discolouration). A rougher lobe averages the sky over the band and holds the finish.
const METAL_ROUGHNESS := 0.30
## The painted metal's own fill strength (FLOOR is the rest of the viewmodel's). The roughness floor above takes the sheen the
## sky's reflection gave the receiver and handguard, which was most of their value in shade and a dark interior (median luma
## 45 and 69 in the dark interior before it, 20 and 22 after): this puts it back as a constant fill instead of a reflection of
## whatever the pose faces.
const METAL_FLOOR := 0.12
## The handguard is a polymer part on the Relay AR (the receiver is the machined metal): its own roughness floor and a fraction of the
## baked metalness, so it takes the sun with a wider, softer lobe and reflects the studio less.
const HANDGUARD_ROUGHNESS := 0.62
const HANDGUARD_METAL := 0.30

## Low-light form (art-v11, lowlight track). Every number below is a constant of the viewmodel, like the studio ambient: nothing reads the
## world, so a dark interior is not lit up and an enemy's view is untouched. All of them are EMPIRICAL (chosen after rendering sweeps, see
## docs/reports/media/art-v11/lowlight); each is a uniform whose default (0) reproduces the previous pixels.
## The studio gradient is modulated by the detail normal's wrapped key (up, left, towards the camera): FORM = 0.8 puts 1.8x of it on what
## faces the key and 0.2x on what faces away. It is a re-distribution, not an addition: the receiver's median in sun and at the ready is
## unchanged (54.6), and what faces down or away from the key goes darker while what faces up or left goes lighter, so the rifle has form
## where it was one flat slate (shade receiver 19-35, p10-p90, before; see the probe).
const FORM := 0.80
## A thin cool edge on geometric edges (screen-space change of the surface normal) of the metal, weighted up: a bevel or a panel line
## catches a little light the way a machined edge does. Cool like the studio's strip. 0.16 is about +4 to +12 luma on the edge pixels only.
const EDGE := 0.16
const MAGAZINE_FORM := 0.30
const MAGAZINE_EDGE := 0.06
## The baked occlusion of the buffer tube is 0 over its rear half (it was baked with the stock around it; the first-person rifle has no
## stock), which drew a pure-black cylinder end in shade. A floor under the occlusion of the studio terms for the rifle's body only.
const BODY_AO_FLOOR := 0.45
## The pistol grip is meant to be the darkest thing in the hand, not black (median luma 6 in shade): a studio key on it, lifted by the
## albedo floor below so its darkened albedo (GRIP_DARKEN) does not leave it with nothing to light.
const GRIP_KEY := 0.35
const GRIP_KEY_LIFT := 0.12

const UNIFORMS := """
uniform float viewmodel_fov = 0.0;
uniform float viewmodel_depth = 0.08;
uniform float viewmodel_floor = 0.0;
uniform float viewmodel_lift = 0.0;
uniform float viewmodel_rim = 0.0;
uniform float viewmodel_roughness = 0.0;
uniform float viewmodel_specular = -1.0;
uniform vec3 viewmodel_rim_color : source_color = vec3(0.80, 0.84, 0.88);
uniform float viewmodel_env = 1.0;
uniform float viewmodel_sheen = 4.0;
uniform float viewmodel_metal_scale = 1.0;
uniform float viewmodel_reflect = 0.30;
uniform vec3 viewmodel_ambient = vec3(0.165, 0.214, 0.254);
uniform vec3 viewmodel_bounce = vec3(0.0);
uniform float viewmodel_form = 0.0;
uniform float viewmodel_key = 0.0;
uniform float viewmodel_key_lift = 0.10;
uniform float viewmodel_edge = 0.0;
uniform vec3 viewmodel_edge_color = vec3(0.30, 0.45, 0.80);
uniform float viewmodel_ao_floor = 0.0;
"""

## Inside vertex(). Scales the camera's projection to the viewmodel field of view,
## keeping its aspect ratio and signs (the Compatibility renderer flips Y when drawing
## into a viewport texture). Clip space is reversed-Z, so the near plane is z = w and
## depth is pulled toward it. Lighting still uses the true VERTEX. Once a shader writes
## POSITION the engine starts it at vec4(1.0), so with no field of view set this falls
## back to the camera's own projection rather than collapsing every vertex to a point.
const PROJECT := """
	vec4 view_position = MODELVIEW_MATRIX * vec4(VERTEX, 1.0);
	if (viewmodel_fov > 0.0) {
		mat4 projection = PROJECTION_MATRIX;
		float zoom = 1.0 / (tan(radians(viewmodel_fov) * 0.5) * abs(PROJECTION_MATRIX[1][1]));
		projection[0][0] *= zoom;
		projection[1][1] *= zoom;
		vec4 clip = projection * view_position;
		clip.z = clip.w - (clip.w - clip.z) * viewmodel_depth;
		POSITION = clip;
	} else {
		POSITION = PROJECTION_MATRIX * view_position;
	}
"""

## At the end of fragment().
const FILL := """
	if (viewmodel_fov > 0.0) {
		ROUGHNESS = max(ROUGHNESS, viewmodel_roughness);
		METALLIC *= viewmodel_metal_scale;
		if (viewmodel_specular >= 0.0) {
			SPECULAR = viewmodel_specular;
		}
		float facing = clamp(dot(NORMAL, VIEW), 0.0, 1.0);
		// Form: the fill is brighter on surfaces that face up and dimmer on those that face down (view space, the
		// camera is upright), so a fist or a forearm has a lit top and a darker underside even in shade.
		float form = mix(0.55, 1.35, clamp(NORMAL.y * 0.5 + 0.5, 0.0, 1.0));
		EMISSION += max(ALBEDO, vec3(viewmodel_lift)) * viewmodel_floor * (0.6 + 0.4 * facing) * form;
		EMISSION += viewmodel_rim_color * viewmodel_rim * pow(1.0 - facing, 3.0) * (0.35 + 0.65 * ALBEDO.g);
	}
"""

## The viewmodel's own lighting environment, for the shaders that declare `render_mode ambient_light_disabled` (the engine's sky
## radiance and ambient light are then not applied): the arena's flat ambient colour for the diffuse part, and a studio for the
## reflection (a soft sky-to-ground gradient, a broad key panel up and to the left, a thin cool strip behind on the right). The sky
## the engine reflects has a bright horizon band with dark ground below it, and a weapon that rolls and lifts slides its reflection
## across that edge (docs/reports/media/art-v9/rifle-discolouration); this environment has no edge, so what moves across the
## metal is a gradient and two soft lobes, which is lighting following the pose rather than the colour of the weapon changing.
## Uses the detail normal (the baked bevels and panel lines catch the lobes) and the baked ambient occlusion.
const STUDIO := """
	if (viewmodel_fov > 0.0 && viewmodel_env > 0.0) {
		vec3 detail_normal_ts = NORMAL_MAP * 2.0 - 1.0;
		vec3 n = normalize(TANGENT * detail_normal_ts.x + BINORMAL * detail_normal_ts.y + NORMAL * detail_normal_ts.z);
		float ndv = clamp(dot(n, VIEW), 0.0, 1.0);
		float up = clamp(n.y * 0.5 + 0.5, 0.0, 1.0);
		float studio_ao = mix(viewmodel_ao_floor, 1.0, AO);
		EMISSION += ALBEDO * (1.0 - METALLIC) * studio_ao * viewmodel_ambient * viewmodel_env;
		// Light bounced up from the ground onto what faces down (a forearm's underside, the underside of a fist): a constant of the
		// viewmodel like the ambient, not read from the world, so it adds form without adding visibility in a dark place.
		EMISSION += ALBEDO * (1.0 - METALLIC) * studio_ao * viewmodel_bounce * clamp(-n.y, 0.0, 1.0) * viewmodel_env;
		// Form in low light (art-v11): the detail normal rebuilt from its two stored channels (the blue channel reads 0 in the imported
		// normal maps, so `n` above has its z flipped: left as it is, the terms above are tuned to it), a wrapped studio key up and to the
		// left, and a form factor that modulates the studio's gradient by it: more on what faces the key, less on what faces away.
		vec2 ts = NORMAL_MAP.rg * 2.0 - 1.0;
		vec3 nd = normalize(TANGENT * ts.x + BINORMAL * ts.y + NORMAL * sqrt(max(1.0 - dot(ts, ts), 0.0)));
		// In the part's own frame, so the shading is attached to the weapon: a roll or a lift in the reload does not turn a lit face away
		// from the key, which would swing the finish's value with the pose (the stability bound of reload_discolour_probe).
		vec3 nd_local = normalize(transpose(mat3(MODEL_MATRIX)) * (INV_VIEW_MATRIX * vec4(nd, 0.0)).xyz);
		float studio_wrap = pow(clamp((dot(nd_local, normalize(vec3(-0.65, 0.60, 0.45))) + 0.25) / 1.25, 0.0, 1.0), 1.6);
		vec3 r = reflect(-VIEW, n);
		float gloss = 1.0 - ROUGHNESS;
		vec3 f0 = mix(vec3(0.08 * SPECULAR), ALBEDO, METALLIC);
		vec3 fresnel = f0 + (max(vec3(gloss), f0) - f0) * pow(1.0 - ndv, 5.0);
		vec3 gradient = mix(vec3(0.26, 0.29, 0.31), vec3(0.38, 0.42, 0.45), smoothstep(-1.0, 1.0, r.y));
		gradient = mix(gradient, vec3(0.30, 0.33, 0.36), ROUGHNESS * 0.6);
		gradient *= mix(1.0 - viewmodel_form, 1.0 + viewmodel_form, studio_wrap);
		float key = pow(max(dot(r, normalize(vec3(-0.50, 0.60, 0.62))), 0.0), mix(48.0, 5.0, ROUGHNESS)) * mix(1.0, 0.4, ROUGHNESS);
		float strip = pow(max(dot(r, normalize(vec3(0.78, 0.15, -0.40))), 0.0), mix(24.0, 4.0, ROUGHNESS)) * mix(1.0, 0.4, ROUGHNESS);
		vec3 radiance = gradient + vec3(1.0, 0.96, 0.90) * key * 3.0 * viewmodel_sheen + vec3(0.62, 0.76, 1.0) * strip * 1.2 * viewmodel_sheen;
		EMISSION += fresnel * radiance * studio_ao * viewmodel_env * viewmodel_reflect;
		EMISSION += max(ALBEDO, vec3(viewmodel_key_lift)) * viewmodel_key * studio_wrap * studio_ao;
		float edge = smoothstep(0.06, 0.40, length(fwidth(NORMAL)));
		EMISSION += viewmodel_edge_color * viewmodel_edge * edge * mix(0.4, 1.0, smoothstep(-0.6, 0.8, nd_local.y)) * studio_ao;
	}
"""

const RENDER_MODE := "render_mode ambient_light_disabled;\n"

const SURFACE := "shader_type spatial;\n" + RENDER_MODE + UNIFORMS + """
uniform sampler2D albedo_texture : source_color, filter_linear_mipmap;
uniform sampler2D orm_texture : hint_default_white, filter_linear_mipmap;
uniform sampler2D normal_texture : hint_normal, filter_linear_mipmap;
uniform float albedo_gain = 1.0;
uniform float albedo_saturation = 1.0;
void vertex() {
""" + PROJECT + """
}
void fragment() {
	vec3 orm = texture(orm_texture, UV).rgb;
	vec3 base = texture(albedo_texture, UV).rgb;
	ALBEDO = mix(vec3(dot(base, vec3(0.2126, 0.7152, 0.0722))), base, albedo_saturation) * albedo_gain;
	AO = orm.r;
	ROUGHNESS = orm.g;
	METALLIC = orm.b;
	NORMAL_MAP = texture(normal_texture, UV).rgb;
""" + FILL + STUDIO + """
}
"""

## Additive and unshaded: the flash mesh carries its own gradient in vertex colour (rgb is the
## hue, alpha the weight), `colour` tints the lot and `energy` brightens it past what 8-bit
## vertex colour can hold. Nothing is written to depth, so it never hides the muzzle behind it.
const FLASH := "shader_type spatial;\nrender_mode unshaded, cull_disabled, blend_add, depth_draw_never;\n" + UNIFORMS + """
uniform vec4 colour : source_color = vec4(1.0);
uniform float energy = 1.0;
void vertex() {
""" + PROJECT + """
}
void fragment() {
	ALBEDO = colour.rgb * COLOR.rgb * energy;
	ALPHA = COLOR.a * colour.a;
}
"""

## Alpha-blended, unshaded and depth-test-only, for the muzzle smoke: a soft grey puff whose vertex colour is the
## hue and alpha the density (zero at its rim), faded as a whole by `fade`. Drawn with the viewmodel projection.
const SMOKE := "shader_type spatial;\nrender_mode unshaded, cull_disabled, blend_mix, depth_draw_never;\n" + UNIFORMS + """
uniform float fade = 1.0;
void vertex() {
""" + PROJECT + """
}
void fragment() {
	ALBEDO = COLOR.rgb;
	ALPHA = COLOR.a * fade;
}
"""

## Vertex-coloured surface for procedural first-person parts merged into one mesh (the
## gloves and sleeves drawn on the authored rifle when no hand asset is used). The colour
## conversion matches StandardMaterial3D with vertex_color_is_srgb.
const VERTEX_COLOUR := "shader_type spatial;\n" + UNIFORMS + """
uniform float roughness = 1.0;
uniform float metallic = 0.0;
void vertex() {
	if (!OUTPUT_IS_SRGB) {
		COLOR.rgb = mix(pow((COLOR.rgb + vec3(0.055)) * (1.0 / (1.0 + 0.055)), vec3(2.4)), COLOR.rgb * (1.0 / 12.92), lessThan(COLOR.rgb, vec3(0.04045)));
	}
""" + PROJECT + """
}
void fragment() {
	ALBEDO = COLOR.rgb;
	ROUGHNESS = roughness;
	METALLIC = metallic;
""" + FILL + """
}
"""

static var _surface_shader: Shader
static var _surfaces: Dictionary = {}
static var _flash_shader: Shader
static var _smoke_shader: Shader
static var _vertex_colour_shader: Shader
static var _vertex_colours: Dictionary = {}

## Unshaded muzzle flash drawn with the viewmodel projection, so it stays on the muzzle.
static func flash(colour: Color, energy: float = 2.0) -> ShaderMaterial:
	if _flash_shader == null:
		_flash_shader = Shader.new()
		_flash_shader.code = FLASH
	var material := ShaderMaterial.new()
	material.shader = _flash_shader
	material.set_shader_parameter("colour", colour)
	material.set_shader_parameter("energy", energy)
	material.set_shader_parameter("viewmodel_fov", FOV)
	material.set_shader_parameter("viewmodel_depth", DEPTH)
	return material

## The muzzle smoke's material (one per actor: its `fade` is animated).
static func smoke() -> ShaderMaterial:
	if _smoke_shader == null:
		_smoke_shader = Shader.new()
		_smoke_shader.code = SMOKE
	var material := ShaderMaterial.new()
	material.shader = _smoke_shader
	material.set_shader_parameter("viewmodel_fov", FOV)
	material.set_shader_parameter("viewmodel_depth", DEPTH)
	return material

## First-person surface for an authored texture set (shared per prefix).
static func surface(prefix: String, gain: float = 1.0, saturation: float = 1.0) -> ShaderMaterial:
	var key := "%s|%s|%s" % [prefix, gain, saturation]
	if not _surfaces.has(key):
		if _surface_shader == null:
			_surface_shader = Shader.new()
			_surface_shader.code = SURFACE
		var material := ShaderMaterial.new()
		material.shader = _surface_shader
		material.set_shader_parameter("albedo_texture", load(prefix + "_albedo.png"))
		material.set_shader_parameter("orm_texture", load(prefix + "_orm.png"))
		material.set_shader_parameter("normal_texture", load(prefix + "_normal.png"))
		material.set_shader_parameter("albedo_gain", gain)
		material.set_shader_parameter("albedo_saturation", saturation)
		enable(material)
		_surfaces[key] = material
	return _surfaces[key]

## First-person vertex-coloured surface (shared per roughness and metallic).
static func vertex_colour(roughness: float, metallic: float) -> ShaderMaterial:
	var key := "%.2f|%.2f" % [roughness, metallic]
	if not _vertex_colours.has(key):
		if _vertex_colour_shader == null:
			_vertex_colour_shader = Shader.new()
			_vertex_colour_shader.code = VERTEX_COLOUR
		var material := ShaderMaterial.new()
		material.shader = _vertex_colour_shader
		material.set_shader_parameter("roughness", roughness)
		material.set_shader_parameter("metallic", metallic)
		enable(material)
		_vertex_colours[key] = material
	return _vertex_colours[key]

## Switches a material using these snippets to first-person drawing.
static func enable(material: ShaderMaterial) -> void:
	material.set_shader_parameter("viewmodel_fov", FOV)
	material.set_shader_parameter("viewmodel_depth", DEPTH)
	material.set_shader_parameter("viewmodel_floor", FLOOR)
	material.set_shader_parameter("viewmodel_lift", LIFT)
	material.set_shader_parameter("viewmodel_rim", RIM)

## Sets the low-light form terms on a first-person surface (see FORM and the constants after it).
static func shape(material: ShaderMaterial, form: float, edge: float, ao_floor: float = 0.0) -> void:
	material.set_shader_parameter("viewmodel_form", form)
	material.set_shader_parameter("viewmodel_edge", edge)
	material.set_shader_parameter("viewmodel_ao_floor", ao_floor)
