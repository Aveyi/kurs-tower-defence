// Leaves, grass and flowers: sway in the wind, vary in hue, let the sun shine through.
shader_type spatial;
render_mode cull_disabled;

#include "res://shaders/include/fx.gdshaderinc"
#include "res://shaders/include/toon_light.gdshaderinc"

uniform float wind_strength = 0.05;
uniform float wind_speed = 1.3;
uniform vec2 wind_direction = vec2(0.8, 0.6);  // keep equal to WindFlags.DIRECTION
/// Extra sway of short plants (grass tufts barely rise above their pivot).
uniform float grass_sway = 0.35;
uniform float hue_variation : hint_range(0.0, 0.5) = 0.18;

varying vec3 v_local;
varying vec3 v_world;

void vertex() {
	vec3 world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float height = max(VERTEX.y, 0.0);
	float phase = dot(world.xz, vec2(0.35, 0.27));
	float sway = sin(TIME * wind_speed + phase) * 0.7 + sin(TIME * wind_speed * 2.3 + world.x * 1.3 + world.z * 0.9) * 0.3;
	float gust = 0.6 + 0.4 * sin(TIME * 0.35 + phase * 0.3);
	float amount = wind_strength * gust * (height + grass_sway * smoothstep(0.0, 0.15, height));
	vec3 offset = vec3(wind_direction.x, 0.0, wind_direction.y) * sway * amount;
	offset.y -= abs(sway) * amount * 0.25;
	VERTEX += mat3(inverse(MODEL_MATRIX)) * offset;
	v_local = VERTEX;
	v_world = world;
}

void fragment() {
	if (fx_cut(v_local, v_world) < 0.0) {
		discard;
	}
	float tone = value_noise(v_world * 0.6);
	vec3 albedo = COLOR.rgb * (1.0 - hue_variation * 0.5 + hue_variation * tone);
	albedo.r *= 1.0 + (tone - 0.5) * hue_variation;  // a little warmer / cooler patches
	vec3 emission = vec3(0.0);
	fx_apply(albedo, emission, NORMAL, VIEW, v_local, v_world);
	ALBEDO = albedo;
	EMISSION = emission;
	ROUGHNESS = 0.9;
	SPECULAR = 0.1;
}
