// Level 2 HUD: a dark violet vignette with slowly drifting mist around the screen edges. Drawn behind the
// HUD panels on a full-screen ColorRect that ignores the mouse; the middle of the screen stays clear.
shader_type canvas_item;

#include "res://shaders/include/noise.gdshaderinc"

uniform vec3 tint : source_color = vec3(0.06, 0.02, 0.1);
uniform vec3 mist_color : source_color = vec3(0.45, 0.3, 0.7);
uniform float strength = 0.6;
uniform float mist_strength = 0.16;

void fragment() {
	vec2 d = (UV - 0.5) * vec2(2.0, 2.4);
	float edge = length(d);
	float vignette = smoothstep(0.75, 1.55, edge);
	float n = fbm(vec3(UV * vec2(3.2, 2.4) + vec2(TIME * 0.025, -TIME * 0.01), TIME * 0.04));
	float mist = smoothstep(0.42, 0.78, n) * smoothstep(0.5, 1.3, edge);
	COLOR = vec4(mix(tint, mist_color, mist * 0.6), clamp(vignette * strength + mist * mist_strength, 0.0, 0.85));
}
