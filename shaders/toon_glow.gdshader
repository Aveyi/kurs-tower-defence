// Glowing parts: eyes, crystals, runes, magic orbs. Pulses gently and shimmers at grazing angles.
shader_type spatial;

#include "res://shaders/include/fx.gdshaderinc"

uniform vec3 glow_color : source_color = vec3(1.0);
uniform float glow_energy = 4.0;
uniform float pulse_speed = 2.2;
uniform float pulse_amount : hint_range(0.0, 1.0) = 0.25;

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
	float fresnel = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.0);
	float phase = dot(v_world, vec3(1.7, 2.3, 1.1));
	float pulse = 1.0 + pulse_amount * sin(TIME * pulse_speed + phase);
	float shimmer = 0.85 + 0.3 * value_noise(v_world * 6.0 + vec3(0.0, TIME * 1.5, 0.0));
	vec3 albedo = glow_color;
	vec3 emission = glow_color * glow_energy * 0.45 * pulse * shimmer * (0.75 + 0.7 * fresnel);
	fx_apply(albedo, emission, NORMAL, VIEW, v_local, v_world);
	ALBEDO = albedo;
	EMISSION = emission;
	ROUGHNESS = 0.3;
}
