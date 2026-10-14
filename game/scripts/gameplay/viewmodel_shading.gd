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
const FLOOR := 0.08
## Rim light strength, on silhouette edges facing away from the camera.
const RIM := 0.22

const UNIFORMS := """
uniform float viewmodel_fov = 0.0;
uniform float viewmodel_depth = 0.08;
uniform float viewmodel_floor = 0.0;
uniform float viewmodel_rim = 0.0;
uniform vec3 viewmodel_rim_color : source_color = vec3(0.80, 0.84, 0.88);
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
		float facing = clamp(dot(NORMAL, VIEW), 0.0, 1.0);
		EMISSION += ALBEDO * viewmodel_floor * (0.6 + 0.4 * facing);
		EMISSION += viewmodel_rim_color * viewmodel_rim * pow(1.0 - facing, 3.0) * (0.35 + 0.65 * ALBEDO.g);
	}
"""

const SURFACE := "shader_type spatial;\n" + UNIFORMS + """
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
""" + FILL + """
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
	material.set_shader_parameter("viewmodel_rim", RIM)
