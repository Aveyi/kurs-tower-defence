// Main material of every model ("Body" and "Metal" surfaces of the generated glTF files).
// Colour comes from the vertex colours (baked ambient occlusion included).
shader_type spatial;

#include "res://shaders/include/fx.gdshaderinc"
#include "res://shaders/include/toon_light.gdshaderinc"

uniform float metallic : hint_range(0.0, 1.0) = 0.0;
uniform float roughness : hint_range(0.0, 1.0) = 0.85;
uniform float specular : hint_range(0.0, 1.0) = 0.15;

varying vec3 v_local;
varying vec3 v_world;

void vertex() {
	v_local = VERTEX;
	v_world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	if (fx_cut(v_local, v_world) < 0.0) {
		discard;
	}
	vec3 albedo = COLOR.rgb;
	vec3 emission = vec3(0.0);
	fx_apply(albedo, emission, NORMAL, VIEW, v_local, v_world);
	ALBEDO = albedo;
	EMISSION = emission;
	METALLIC = metallic;
	ROUGHNESS = roughness;
	SPECULAR = specular;
}
