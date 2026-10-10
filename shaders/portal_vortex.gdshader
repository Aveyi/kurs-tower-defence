// Swirling vortex inside the enemy portal arch: spiral arms of fractal noise pulled into a dark core.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_back, shadows_disabled;

#include "res://shaders/include/noise.gdshaderinc"

uniform vec3 core_color : source_color = vec3(0.04, 0.0, 0.08);
uniform vec3 arm_color : source_color = vec3(0.55, 0.12, 0.95);
uniform vec3 glow_color : source_color = vec3(1.0, 0.45, 1.0);
uniform float twist = 5.0;
uniform float speed = 1.2;
uniform float intensity = 2.2;

void fragment() {
	vec2 p = (UV - 0.5) * 2.0;
	float r = length(p);
	float angle = atan(p.y, p.x) + twist * (1.0 - r) * (1.0 - r) + TIME * speed;
	// sample the noise on a circle (cos/sin) so there is no seam where atan wraps around
	vec2 ring = vec2(cos(angle), sin(angle));
	float pull = TIME * 0.6 - log(r + 0.05) * 0.8;  // detail flows toward the centre
	float n = fbm(vec3(ring * 1.6, pull));
	float arms = smoothstep(0.35, 0.75, n + 0.25 * sin(angle * 3.0));
	float stars = smoothstep(0.93, 0.98, value_noise(vec3(ring * 9.0, pull * 3.0))) * r;

	vec3 color = mix(core_color, arm_color * intensity * 0.6, arms * smoothstep(0.05, 0.6, r));
	color += glow_color * intensity * pow(arms, 3.0) * 0.6;
	color += glow_color * intensity * exp(-r * 7.0) * 0.8;          // bright heart
	color += glow_color * intensity * smoothstep(0.82, 0.97, r) * (0.6 + 0.4 * n);  // rim
	color += vec3(1.0, 0.85, 1.0) * stars * 3.0;
	ALBEDO = color;
	ALPHA = 1.0 - smoothstep(0.93, 1.0, r);
}
