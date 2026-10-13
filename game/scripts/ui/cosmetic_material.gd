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
const CODE := """shader_type spatial;
uniform vec4 base_paint : source_color;
uniform vec4 accent_paint : source_color;
uniform float pattern_seed = 1.0;
uniform float wear = 0.0;
uniform float patterned = 1.0;
uniform int finish_family = 0;
varying vec3 local_position;
void vertex() { local_position = VERTEX; }
void fragment() {
 vec3 p = local_position;
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
}"""

static func rarity_color(rarity: String) -> Color:
	return RARITIES.get(rarity.capitalize(), RARITIES.Common)

static func finish(metadata: Dictionary) -> ShaderMaterial:
	var material := ShaderMaterial.new()
	var shader := Shader.new()
	shader.code = CODE
	material.shader = shader
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
