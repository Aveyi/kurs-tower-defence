// Per-instance magical effects shared by all model shaders.
// Driven from GDScript with GeometryInstance3D.set_instance_shader_parameter (see FantasyMaterials.set_fx):
//   fx_dissolve 0..1   - the model burns away into glowing embers (enemy death)
//   fx_flash    0..1   - white flash (enemy hit)
//   fx_frost    0..1   - icy crust and cold rim light (slowed by the ice tower)
//   fx_stun     0..1   - greyed out with a pulsing violet rim (tower stunned by a golem's slam)
//   fx_reveal_y metres - everything above this world height is not built yet; a golden runic band
//                        rises along the cut (tower construction / upgrade). 100000 = fully visible.
#ifndef FX_INC
#define FX_INC
#include "res://shaders/include/noise.gdshaderinc"

instance uniform float fx_dissolve = 0.0;
instance uniform float fx_flash = 0.0;
instance uniform float fx_frost = 0.0;
instance uniform float fx_stun = 0.0;
instance uniform float fx_reveal_y = 100000.0;

const vec3 FX_EMBER = vec3(1.0, 0.42, 0.1);
const vec3 FX_REVEAL = vec3(1.0, 0.78, 0.32);
const vec3 FX_FROST = vec3(0.55, 0.85, 1.0);
const vec3 FX_STUN = vec3(0.7, 0.42, 1.0);

float fx_dissolve_value(vec3 local) {
	return fbm(local * 3.2) - fx_dissolve * 1.08;
}

// Negative result: the fragment is gone and must be discarded.
float fx_cut(vec3 local, vec3 world) {
	float keep = 1.0;
	if (fx_dissolve > 0.0) {
		keep = fx_dissolve_value(local);
	}
	if (world.y > fx_reveal_y) {
		keep = -1.0;
	}
	return keep;
}

void fx_apply(inout vec3 albedo, inout vec3 emission, vec3 normal, vec3 view, vec3 local, vec3 world) {
	float fresnel = pow(1.0 - clamp(dot(normal, view), 0.0, 1.0), 3.0);
	if (fx_frost > 0.0) {
		float luma = dot(albedo, vec3(0.3, 0.59, 0.11));
		float crystals = step(0.62, value_noise(local * 18.0));
		albedo = mix(albedo, FX_FROST * (0.45 + luma + crystals * 0.3), fx_frost * 0.6);
		emission += FX_FROST * (fresnel * 0.9 + crystals * 0.08) * fx_frost;
	}
	if (fx_stun > 0.0) {
		float luma = dot(albedo, vec3(0.3, 0.59, 0.11));
		float pulse = 0.6 + 0.4 * sin(TIME * 9.0);
		albedo = mix(albedo, luma * vec3(0.75, 0.65, 0.95), fx_stun * 0.7);
		emission += FX_STUN * (fresnel * 2.2 + 0.15) * pulse * fx_stun;
	}
	if (fx_dissolve > 0.0) {
		float edge = 1.0 - smoothstep(0.0, 0.08, fx_dissolve_value(local));
		albedo = mix(albedo, vec3(0.04, 0.03, 0.03), edge);
		emission += FX_EMBER * edge * edge * 6.0;
	}
	if (fx_reveal_y < 9999.0) {
		float d = fx_reveal_y - world.y;
		float band = 1.0 - smoothstep(0.0, 0.3, d);
		float runes = step(0.55, fract(world.y * 10.0 - TIME * 3.0)) * step(0.35, value_noise(world * 7.0));
		emission += FX_REVEAL * band * (1.5 + 3.0 * runes);
		albedo = mix(albedo, FX_REVEAL, band * 0.4);
	}
	if (fx_flash > 0.0) {
		albedo = mix(albedo, vec3(1.0), fx_flash * 0.45);
		emission += vec3(1.0, 0.92, 0.8) * fx_flash * (0.6 + fresnel);
	}
}

#endif
