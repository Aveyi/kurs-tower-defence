// Terrain tiles. Grass gets large hue patches and fine speckles from world-space noise, so the
// pattern flows across tile borders and the 2x2 m grid does not show; the jittered low-poly
// facets are lit a little softer for the same reason. Roads, sand and soil keep their colours.
shader_type spatial;

#include "res://shaders/include/fx.gdshaderinc"
#include "res://shaders/include/toon_light.gdshaderinc"

uniform vec3 patch_dark = vec3(0.8, 0.9, 0.72);
uniform vec3 patch_light = vec3(1.14, 1.1, 0.86);
uniform float patch_scale = 0.14;
uniform float detail_scale = 1.3;
uniform float facet_softening : hint_range(0.0, 1.0) = 0.55;

varying vec3 v_local;
varying vec3 v_world;

void vertex() {
	v_local = VERTEX;
	v_world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 albedo = COLOR.rgb;
	float grass = smoothstep(0.03, 0.12, albedo.g - max(albedo.r, albedo.b));
	float patches = fbm(vec3(v_world.xz * patch_scale, 0.0));
	float detail = value_noise(vec3(v_world.xz * detail_scale, 3.0));
	float k = clamp(patches * 1.5 - 0.25 + (detail - 0.5) * 0.3, 0.0, 1.0);
	albedo = mix(albedo, albedo * mix(patch_dark, patch_light, k), grass);
	vec3 up = (VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz;
	NORMAL = normalize(mix(NORMAL, up, facet_softening * grass));
	vec3 emission = vec3(0.0);
	fx_apply(albedo, emission, NORMAL, VIEW, v_local, v_world);
	ALBEDO = albedo;
	EMISSION = emission;
	ROUGHNESS = 0.9;
	SPECULAR = 0.1;
}
