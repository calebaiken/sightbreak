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
## The machined metal of the Relay AR (receiver, rails, barrel and suppressor: where the baked metalness is high), art-v11 sun-metal
## track. Every value is EMPIRICAL, set after rendering and measuring the baseline (sun receiver 54.6 median luma at the ready, hue
## (r - b) / luma +0.018, sun ratio 1.209, shade 28.4) and keeping the stability bounds (1.25, 0.06) unchanged; none is a visual standard.
## The baked albedo is a graphite of 0.03 linear and the baked metalness 0.44, so the engine's reflectance (f0) was 0.036, a black
## glossy dielectric; the warm sun's diffuse on it plus a flat cool studio sheen added up to a neutral olive grey that is the same over
## every face (docs/reports/media/art-v11/sunmetal).
## Reflectance of the metal (`viewmodel_f0`, a Fresnel f0 in linear light): the sun's specular on bevels and edges.
const METAL_F0 := 0.15
## The fraction of the baked diffuse the metal keeps (`viewmodel_diffuse`): the warm sun's diffuse on a graphite is most of the olive.
const METAL_DIFFUSE := 0.45
## The strength of the studio's constant gradient on metal (`viewmodel_metal_reflect`), against the default 0.30 that polymer, the magazine
## and the arms keep: the cool base that replaces the diffuse the metal gave up. The key and strip lobes keep the default strength.
const METAL_REFLECT := 0.45
## Finish variation on the metal's reflection (`viewmodel_variation`), a fraction of it, fixed to the weapon.
const METAL_VARIATION := 0.30

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
uniform float viewmodel_f0 = 0.0;
uniform float viewmodel_diffuse = 1.0;
uniform float viewmodel_metal_reflect = -1.0;
uniform float viewmodel_variation = 0.0;
uniform float viewmodel_normal_fix = 0.0;
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

## Reflectance of the machined metal, applied before the studio and the sun see the material (ALBEDO and METALLIC are what the
## engine's own light reads, so the remap has to be made in them). Where the baked metalness says metal (a smooth ramp, so polymer and
## the tan magazine, metalness 0, are untouched) it asks for the reflectance `viewmodel_f0` and for `viewmodel_diffuse` of the diffuse the
## material has (albedo * (1 - metalness)); the albedo becomes the baked hue at that reflectance and the metalness 1 - d / f, which the
## engine turns back into exactly that diffuse and a reflectance of about f. A finish already more reflective than f (a bright skin)
## keeps its own. Needs viewmodel_f0 > 0 (the default 0 leaves the material as it was).
const REFLECTANCE := """
	if (viewmodel_fov > 0.0 && viewmodel_f0 > 0.0) {
		float s0 = 0.08 * SPECULAR;
		float w = smoothstep(0.10, 0.40, METALLIC);
		float lum = max(dot(ALBEDO, vec3(0.2126, 0.7152, 0.0722)), 0.0001);
		float f_now = dot(mix(vec3(s0), ALBEDO, METALLIC), vec3(0.3333));
		float f_wanted = mix(s0, viewmodel_f0, w);
		float d = lum * (1.0 - METALLIC) * mix(1.0, viewmodel_diffuse, w);
		float t = w * smoothstep(0.0, 0.02, f_wanted - f_now);
		float u = clamp(d / f_wanted, 0.0, 1.0);
		ALBEDO = mix(ALBEDO, ALBEDO / lum * f_wanted, t);
		METALLIC = mix(METALLIC, 1.0 - u, t);
	}
"""

## The viewmodel's own lighting environment, for the shaders that declare `render_mode ambient_light_disabled` (the engine's sky
## radiance and ambient light are then not applied): the arena's flat ambient colour for the diffuse part, and a studio for the
## reflection (a soft sky-to-ground gradient, a broad key panel up and to the left, a thin cool strip behind on the right). The sky
## the engine reflects has a bright horizon band with dark ground below it, and a weapon that rolls and lifts slides its reflection
## across that edge (docs/reports/media/art-v9/rifle-discolouration); this environment has no edge, so what moves across the
## metal is a gradient and two soft lobes, which is lighting following the pose rather than the colour of the weapon changing.
## Uses the detail normal (the baked bevels and panel lines catch the lobes) and the baked ambient occlusion.
const STUDIO := REFLECTANCE + """
	if (viewmodel_fov > 0.0 && viewmodel_env > 0.0) {
		// The baked normal maps are imported as RG-only normal maps (the blue channel is not stored; the engine's own normal mapping
		// rebuilds z from x and y), so reading the blue channel here gives z = -1: the normal is turned inside out, its bevels lean the
		// wrong way and n.v is 0 on every face. `viewmodel_normal_fix` rebuilds z from x and y (the rifle sets it; the arms keep the old
		// behaviour, which their bounce bounds in viewmodel_light_probe.gd were measured with).
		vec2 detail_xy = NORMAL_MAP.xy * 2.0 - 1.0;
		float detail_z = mix(NORMAL_MAP.z * 2.0 - 1.0, sqrt(max(0.0, 1.0 - dot(detail_xy, detail_xy))), viewmodel_normal_fix);
		vec3 detail_normal_ts = vec3(detail_xy, detail_z);
		vec3 n = normalize(TANGENT * detail_normal_ts.x + BINORMAL * detail_normal_ts.y + NORMAL * detail_normal_ts.z);
		// Schlick's term stays at grazing incidence (n.v = 0), which is what the inside-out normal made it on every face and what the
		// finish-stability bound (1.25) was met with: evaluated at the real n.v the receiver's median luma swung 1.25 to 1.31 through
		// the reload (docs/reports/media/art-v11/sunmetal).
		float ndv = clamp(dot(n, VIEW), 0.0, 1.0) * (1.0 - viewmodel_normal_fix);
		float up = clamp(n.y * 0.5 + 0.5, 0.0, 1.0);
		EMISSION += ALBEDO * (1.0 - METALLIC) * AO * viewmodel_ambient * viewmodel_env;
		// Light bounced up from the ground onto what faces down (a forearm's underside, the underside of a fist): a constant of the
		// viewmodel like the ambient, not read from the world, so it adds form without adding visibility in a dark place.
		EMISSION += ALBEDO * (1.0 - METALLIC) * AO * viewmodel_bounce * clamp(-n.y, 0.0, 1.0) * viewmodel_env;
		vec3 r = reflect(-VIEW, n);
		float gloss = 1.0 - ROUGHNESS;
		vec3 f0 = mix(vec3(0.08 * SPECULAR), ALBEDO, METALLIC);
		vec3 fresnel = f0 + (max(vec3(gloss), f0) - f0) * pow(1.0 - ndv, 5.0);
		// Metal (after the remap its metalness is near 1; polymer's is 0.13) takes its own strength for the studio's constant gradient, the
		// cool base that replaces the diffuse it gave up. The key and strip lobes keep the default strength: with it the bevels (now
		// leaning the right way) catch them at about the glint brightness the baseline's sunlit rifle already had, and no brighter in a
		// dark interior than that (a lobe gain of 8 put 234 of 255 on the suppressor there).
		float metal = smoothstep(0.30, 0.70, METALLIC);
		float gradient_strength = viewmodel_metal_reflect < 0.0 ? viewmodel_reflect : mix(viewmodel_reflect, viewmodel_metal_reflect, metal);
		vec3 gradient = mix(vec3(0.26, 0.29, 0.31), vec3(0.38, 0.42, 0.45), smoothstep(-1.0, 1.0, r.y));
		gradient = mix(gradient, vec3(0.30, 0.33, 0.36), ROUGHNESS * 0.6);
		float key = pow(max(dot(r, normalize(vec3(-0.50, 0.60, 0.62))), 0.0), mix(48.0, 5.0, ROUGHNESS)) * mix(1.0, 0.4, ROUGHNESS);
		float strip = pow(max(dot(r, normalize(vec3(0.78, 0.15, -0.40))), 0.0), mix(24.0, 4.0, ROUGHNESS)) * mix(1.0, 0.4, ROUGHNESS);
		vec3 lobes = vec3(1.0, 0.96, 0.90) * key * 3.0 * viewmodel_sheen + vec3(0.62, 0.76, 1.0) * strip * 1.2 * viewmodel_sheen;
		// Finish variation on the metal's reflection, fixed to the weapon in object space (the barrel runs along z) so it does not move
		// with the pose: a slow swell along the barrel and a fine brushed grain along it, zero on average, so the median holds. A flat
		// face under a distant environment has one reflection direction over its whole area; this is what puts structure on it.
		float variation = 1.0;
		if (viewmodel_variation > 0.0) {
			vec3 vp = local_position;
			float swell = sin(vp.z * 23.0 + vp.y * 11.0 + 1.7) * sin(vp.z * 7.0 - vp.x * 40.0 + 0.6);
			// The grain fades out where a pixel spans more than about a third of its period (a lower render scale, a grazing view), so it
			// does not alias and shimmer as the weapon moves.
			float phase_fine = vp.y * 900.0 + sin(vp.x * 300.0 + vp.z * 18.0) * 2.0;
			float phase_coarse = vp.y * 370.0 + vp.x * 410.0 + vp.z * 9.0;
			float grain = 0.5 * sin(phase_fine) * (1.0 - smoothstep(2.0, 3.2, fwidth(phase_fine))) + 0.5 * sin(phase_coarse) * (1.0 - smoothstep(2.0, 3.2, fwidth(phase_coarse)));
			variation = 1.0 + viewmodel_variation * metal * (0.6 * swell + 0.4 * grain);
		}
		EMISSION += fresnel * (gradient * gradient_strength + lobes * viewmodel_reflect) * AO * viewmodel_env * variation;
	}
"""

const RENDER_MODE := "render_mode ambient_light_disabled;\n"

const SURFACE := "shader_type spatial;\n" + RENDER_MODE + UNIFORMS + """
varying vec3 local_position;
uniform sampler2D albedo_texture : source_color, filter_linear_mipmap;
uniform sampler2D orm_texture : hint_default_white, filter_linear_mipmap;
uniform sampler2D normal_texture : hint_normal, filter_linear_mipmap;
uniform float albedo_gain = 1.0;
uniform float albedo_saturation = 1.0;
void vertex() {
	local_position = VERTEX;
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

## The machined-metal finish of the rifle (see METAL_F0): reflectance, kept diffuse, the studio's strength and gain on metal, the
## finish variation and the rebuilt detail normal. Only where the baked metalness is high; the polymer, the magazine and the arms are
## not metal, and a material that does not call this keeps exactly the behaviour it had.
static func metal(material: ShaderMaterial) -> void:
	material.set_shader_parameter("viewmodel_f0", METAL_F0)
	material.set_shader_parameter("viewmodel_diffuse", METAL_DIFFUSE)
	material.set_shader_parameter("viewmodel_metal_reflect", METAL_REFLECT)
	material.set_shader_parameter("viewmodel_variation", METAL_VARIATION)
	material.set_shader_parameter("viewmodel_normal_fix", 1.0)
