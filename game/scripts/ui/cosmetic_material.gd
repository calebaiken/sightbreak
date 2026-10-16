class_name CosmeticMaterial
extends RefCounted
## One deterministic finish for inspection and gameplay; metadata never changes stats.
const RARITIES := {"Common": Color("82909a"), "Uncommon": Color("76a896"), "Rare": Color("597eb9"), "Epic": Color("8d69b7"), "Legendary": Color("bba26e"), "Mythic": Color("b6314c")}
const PALETTES := {
	"Obsidian": [Color("263942"), Color("91afb6")],
	"Crimson Archive": [Color("662939"), Color("d5a477")],
	"Spectral Circuit": [Color("243c57"), Color("62cec7")],
	"Blacksite": [Color("394536"), Color("c7b779")]
}
const ViewmodelShading = preload("res://scripts/gameplay/viewmodel_shading.gd")
const PARAMETERS := """uniform vec4 base_paint : source_color;
uniform vec4 accent_paint : source_color;
uniform float pattern_seed = 1.0;
uniform float wear = 0.0;
uniform float patterned = 1.0;
uniform int finish_family = 0;
// Baked occlusion (R) and tangent normals from authored models; 0 leaves meshes
// without UVs (procedural weapons) exactly as before.
uniform float detail = 0.0;
uniform sampler2D detail_orm : hint_default_white, filter_linear_mipmap;
uniform sampler2D detail_normal : hint_normal, filter_linear_mipmap;
// Without a skin (patterned = 0) an authored model shows its own baked surface.
uniform sampler2D detail_albedo : source_color, hint_default_white, filter_linear_mipmap;
// Linear gain on the baked albedo, matching relay_ar_body.tres, so the unskinned parts and
// the rest of the model read as one graphite finish.
uniform float detail_gain = 0.70;
varying vec3 local_position;"""
const SURFACE := """ vec3 p = local_position;
 float phase = pattern_seed * 0.017;
 float diagonal = smoothstep(0.34, 0.40, sin(p.x*18.0 + p.z*23.0 + phase));
 float hexgrain = sin(p.x*32.0+phase) * sin(p.y*38.0+p.z*24.0);
 float mask = diagonal * 0.24;
 if (finish_family == 1) {
   mask = smoothstep(0.76,0.81,sin(p.x*14.0+p.z*20.0+phase)) * 0.82;
 } else if (finish_family == 2) {
   vec2 cell = abs(fract(p.xz*22.0 + phase)-0.5);
   mask = (1.0-smoothstep(0.025,0.065,min(cell.x,cell.y))) * 0.72;
 } else if (finish_family == 3) {
   mask = smoothstep(-0.08,0.10,hexgrain) * 0.48;
 }
 float abrasion = smoothstep(0.75,0.95,sin(p.x*145.0+p.y*80.0)) * smoothstep(0.4,0.9,hexgrain);
 vec3 paint = mix(base_paint.rgb, accent_paint.rgb, mask*patterned);
 ALBEDO = mix(paint, vec3(0.30,0.32,0.34), abrasion*wear*0.55);
 ROUGHNESS = 0.29 + wear*0.38 + abrasion*0.06;
 METALLIC = 0.66 - wear*0.14;
 vec3 orm = texture(detail_orm, UV).rgb;
 float occlusion = mix(1.0, orm.r, detail);
 ALBEDO *= mix(0.6, 1.0, occlusion);
 float baked = detail * (1.0 - patterned);
 ALBEDO = mix(ALBEDO, texture(detail_albedo, UV).rgb * detail_gain, baked);
 ROUGHNESS = mix(ROUGHNESS, orm.g, baked);
 METALLIC = mix(METALLIC, orm.b, baked);
 AO = occlusion;
 NORMAL_MAP = mix(vec3(0.5, 0.5, 1.0), texture(detail_normal, UV).rgb, detail);"""
# Inspection, third person and procedural weapons: the engine's own vertex transform.
const CODE := "shader_type spatial;\n" + PARAMETERS + "\nvoid vertex() { local_position = VERTEX; }\nvoid fragment() {\n" + SURFACE + "\n}"
# First person only: the viewmodel projection, depth and fill (see SBViewmodelShading).
const VIEWMODEL_CODE := "shader_type spatial;\n" + ViewmodelShading.RENDER_MODE + ViewmodelShading.UNIFORMS + PARAMETERS + "\nvoid vertex() {\n local_position = VERTEX;\n" + ViewmodelShading.PROJECT + "}\nvoid fragment() {\n" + SURFACE + "\n" + ViewmodelShading.FILL + ViewmodelShading.STUDIO + "}"

## Assigns one finish to every paint part, binding baked detail when the parts
## carry it (authored models set detail_orm/detail_normal/detail_albedo metadata).
## With no skin, the authored model keeps its baked albedo, roughness and metal.
static func apply(material: ShaderMaterial, parts: Array) -> void:
	for part: MeshInstance3D in parts:
		if part.has_meta("detail_orm"):
			material.set_shader_parameter("detail_orm", part.get_meta("detail_orm"))
			material.set_shader_parameter("detail_normal", part.get_meta("detail_normal"))
			material.set_shader_parameter("detail_albedo", part.get_meta("detail_albedo"))
			material.set_shader_parameter("detail", 1.0)
			break
	for part: MeshInstance3D in parts:
		var first_person: bool = material.get_shader_parameter("viewmodel_fov") != null and float(material.get_shader_parameter("viewmodel_fov")) > 0.0
		if first_person and part.name == "paint_handguard":
			var polymer: ShaderMaterial = material.duplicate()
			polymer.set_shader_parameter("viewmodel_roughness", ViewmodelShading.HANDGUARD_ROUGHNESS)
			polymer.set_shader_parameter("viewmodel_metal_scale", ViewmodelShading.HANDGUARD_METAL)
			part.material_override = polymer
		else:
			part.material_override = material

static func rarity_color(rarity: String) -> Color:
	return RARITIES.get(rarity.capitalize(), RARITIES.Common)

# One compiled program per use (world or first person); materials differ only in
# parameters.
static var _shader: Shader
static var _viewmodel_shader: Shader

static func shader(viewmodel: bool = false) -> Shader:
	if viewmodel:
		if _viewmodel_shader == null:
			_viewmodel_shader = Shader.new()
			_viewmodel_shader.code = VIEWMODEL_CODE
		return _viewmodel_shader
	if _shader == null:
		_shader = Shader.new()
		_shader.code = CODE
	return _shader

## viewmodel = true only for a first-person model drawn with SBViewmodelShading.
static func finish(metadata: Dictionary, viewmodel: bool = false) -> ShaderMaterial:
	var material := ShaderMaterial.new()
	material.shader = shader(viewmodel)
	if viewmodel:
		ViewmodelShading.enable(material)
		material.set_shader_parameter("viewmodel_roughness", ViewmodelShading.METAL_ROUGHNESS)
		material.set_shader_parameter("viewmodel_floor", ViewmodelShading.METAL_FLOOR)
		ViewmodelShading.metal(material)
	var collection := str(metadata.get("collection", ""))
	var definition := str(metadata.get("definition_id", metadata.get("id", ""))).to_lower()
	if collection.is_empty():
		for name in PALETTES:
			if definition.begins_with(str(name).to_snake_case()):
				collection = name
				break
	var palette: Array = PALETTES.get(collection, [Color("35414a"), Color("798b95")])
	material.set_shader_parameter("finish_family", maxi(0, PALETTES.keys().find(collection)))
	material.set_shader_parameter("base_paint", palette[0])
	material.set_shader_parameter("accent_paint", palette[1])
	material.set_shader_parameter("pattern_seed", float(int(metadata.get("pattern_seed", metadata.get("seed", 1))) % 10000))
	material.set_shader_parameter("wear", clampf(float(metadata.get("wear", 0.05)), 0, 1))
	material.set_shader_parameter("patterned", 0.0 if metadata.is_empty() else 1.0)
	return material
