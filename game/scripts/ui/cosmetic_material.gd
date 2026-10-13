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
varying vec3 local_position;
void vertex() { local_position = VERTEX; }
void fragment() {
 float band = smoothstep(0.30, 0.38, sin(local_position.x*48.0 + local_position.z*65.0 + pattern_seed));
 float fine = smoothstep(0.97, 1.0, sin(local_position.x*120.0 + local_position.y*150.0));
 float grain = fract(sin(dot(floor(local_position*580.0),vec3(12.98,78.23,31.18))+pattern_seed)*43758.54);
 vec3 paint = mix(base_paint.rgb, accent_paint.rgb, (band*0.52+fine*0.15)*patterned);
 ALBEDO = mix(paint, vec3(0.25,0.27,0.28), step(1.0-wear*0.30,grain));
 ROUGHNESS = 0.34 + wear*0.46;
 METALLIC = 0.55 - wear*0.20;
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
	material.set_shader_parameter("base_paint", palette[0])
	material.set_shader_parameter("accent_paint", palette[1])
	material.set_shader_parameter("pattern_seed", float(int(metadata.get("pattern_seed", metadata.get("seed", 1))) % 10000))
	material.set_shader_parameter("wear", clampf(float(metadata.get("wear", 0.05)), 0, 1))
	material.set_shader_parameter("patterned", 0.0 if metadata.is_empty() else 1.0)
	return material
