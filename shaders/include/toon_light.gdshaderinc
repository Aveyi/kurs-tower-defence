// Stylized ("storybook") lighting: two soft light bands, softened shadows, warm rim light,
// optional sharp toon highlight for metal and light transmission for leaves.
#ifndef TOON_LIGHT_INC
#define TOON_LIGHT_INC

uniform float band_softness : hint_range(0.01, 0.5) = 0.1;
uniform float shadow_softness : hint_range(0.05, 1.0) = 0.35;
uniform float rim_strength : hint_range(0.0, 2.0) = 0.35;
uniform vec3 rim_tint : source_color = vec3(1.0, 0.86, 0.62);
uniform float highlight_strength : hint_range(0.0, 4.0) = 0.0;
uniform float highlight_size : hint_range(0.0, 0.5) = 0.08;
uniform float translucency : hint_range(0.0, 2.0) = 0.0;

void light() {
	float ndl = dot(NORMAL, LIGHT);
	float shadow = smoothstep(0.5 - shadow_softness * 0.5, 0.5 + shadow_softness * 0.5, ATTENUATION);
	float lit = smoothstep(-0.05, -0.05 + band_softness, ndl) * 0.72
			+ smoothstep(0.38, 0.38 + band_softness, ndl) * 0.28;
	vec3 energy = LIGHT_COLOR / PI;
	DIFFUSE_LIGHT += energy * lit * shadow;

	float rim = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 3.0);
	rim *= smoothstep(-0.2, 0.3, ndl);
	SPECULAR_LIGHT += energy * rim * rim_strength * rim_tint * mix(vec3(1.0), ALBEDO, 0.5) * shadow;

	if (highlight_strength > 0.0) {
		float nh = dot(NORMAL, normalize(LIGHT + VIEW));
		float glint = smoothstep(1.0 - highlight_size, 1.0 - highlight_size + 0.015, nh);
		SPECULAR_LIGHT += energy * glint * highlight_strength * shadow;
	}
	if (translucency > 0.0) {  // sunlight shining through leaves seen against the sun
		float back = pow(clamp(dot(VIEW, -LIGHT), 0.0, 1.0), 3.0);
		DIFFUSE_LIGHT += energy * back * translucency * (1.0 - lit * 0.5) * vec3(1.0, 1.05, 0.7);
	}
}

#endif
