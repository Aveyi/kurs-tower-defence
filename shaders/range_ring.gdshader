// Tower range indicator drawn as a magic circle: double outer ring, a band of slowly turning
// procedural runes and a counter-rotating hexagram (drawn on a PlaneMesh, UV 0..1).
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled;

#include "res://shaders/include/noise.gdshaderinc"

uniform vec4 color : source_color = vec4(0.45, 0.82, 1.0, 1.0);
uniform float rune_count = 40.0;

float ring(float r, float centre, float width) {
	return 1.0 - smoothstep(width * 0.5, width, abs(r - centre));
}

float segment(vec2 p, vec2 a, vec2 b, float width) {
	vec2 pa = p - a;
	vec2 ba = b - a;
	float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
	return 1.0 - smoothstep(width * 0.5, width, length(pa - ba * h));
}

// Signed distance to an equilateral triangle with circumradius r (Inigo Quilez).
float triangle(vec2 p, float r) {
	const float k = sqrt(3.0);
	r *= k * 0.5;
	p.x = abs(p.x) - r;
	p.y = p.y + r / k;
	if (p.x + k * p.y > 0.0) {
		p = vec2(p.x - k * p.y, -k * p.x - p.y) / 2.0;
	}
	p.x -= clamp(p.x, -2.0 * r, 0.0);
	return -length(p) * sign(p.y);
}

// A rune: up to six strokes chosen by the bits of a per-cell random number.
float rune(vec2 q, float seed) {
	float bits = floor(hash12(vec2(seed, 7.3)) * 64.0);
	float g = 0.0;
	vec2 s[12] = vec2[](
		vec2(0.2, 0.15), vec2(0.2, 0.85), vec2(0.8, 0.15), vec2(0.8, 0.85), vec2(0.5, 0.15), vec2(0.5, 0.85),
		vec2(0.2, 0.85), vec2(0.8, 0.85), vec2(0.2, 0.15), vec2(0.8, 0.85), vec2(0.2, 0.5), vec2(0.8, 0.5));
	for (int i = 0; i < 6; i++) {
		if (mod(floor(bits / pow(2.0, float(i))), 2.0) > 0.5) {
			g = max(g, segment(q, s[i * 2], s[i * 2 + 1], 0.13));
		}
	}
	g = max(g, segment(q, vec2(0.5, 0.15), vec2(0.5, 0.85), 0.13));  // every rune has a stem
	return g;
}

void fragment() {
	vec2 p = (UV - 0.5) * 2.0;
	float r = length(p);
	if (r > 1.02) {
		discard;
	}
	float lines = ring(r, 0.985, 0.022) + ring(r, 0.885, 0.012) + ring(r, 0.43, 0.012) * 0.7;

	// rune band between the two outer rings, turning slowly
	float a = atan(p.y, p.x) / TAU + 0.5 + TIME * 0.012;
	float cell = floor(a * rune_count);
	float v = (r - 0.895) / 0.08;
	if (v > 0.0 && v < 1.0) {
		vec2 q = vec2(fract(a * rune_count), v);
		q.x = (q.x - 0.5) * 1.6 + 0.5;  // cells are wider than tall
		lines += rune(q, mod(cell, rune_count)) * 0.9;
	}

	// hexagram turning the other way + dots on its points
	float spin = -TIME * 0.05;
	mat2 rot = mat2(vec2(cos(spin), sin(spin)), vec2(-sin(spin), cos(spin)));
	vec2 h = rot * p;
	float star = max(1.0 - smoothstep(0.004, 0.011, abs(triangle(h, 0.86))),
			1.0 - smoothstep(0.004, 0.011, abs(triangle(-h, 0.86))));
	lines += star * 0.75;

	float pulse = 0.85 + 0.15 * sin(TIME * 2.5);
	float fill = (1.0 - smoothstep(0.95, 1.0, r)) * (0.05 + 0.1 * r * r);
	ALBEDO = color.rgb * (1.0 + clamp(lines, 0.0, 1.0) * 1.2);
	ALPHA = max(clamp(lines, 0.0, 1.0) * pulse, fill) * color.a;
}
