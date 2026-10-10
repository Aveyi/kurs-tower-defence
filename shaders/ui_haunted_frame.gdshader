// Level 2 HUD frames (panels and buttons, see assets/ui/theme_haunted.tres). The frame texture is drawn as
// usual; on top of it a slow wave of violet light runs along the rune line and the corner gems, the outer
// glow breathes, and faint mist drifts over the dark fill. Works in screen space, so the light flows on
// across every patch of the nine-patch.
shader_type canvas_item;

#include "res://shaders/include/noise.gdshaderinc"

uniform vec3 glow_color : source_color = vec3(0.66, 0.4, 1.0);
uniform float glow_strength = 0.8;
uniform float mist_strength = 0.16;
uniform float pulse_speed = 1.4;

void fragment() {
	vec4 c = texture(TEXTURE, UV) * COLOR;
	// violet texels: the rune line, the gems and the outer glow
	float violet = smoothstep(0.1, 0.3, c.b - c.g);
	float wave = 0.5 + 0.5 * sin(TIME * pulse_speed - (FRAGCOORD.x + FRAGCOORD.y) * 0.01);
	c.rgb += glow_color * violet * c.a * glow_strength * (0.2 + 0.8 * wave * wave);
	c.a *= mix(1.0, 0.75 + 0.45 * wave, violet * step(c.a, 0.6));
	// mist over the dark fill only
	float dark = 1.0 - smoothstep(0.12, 0.3, max(c.r, max(c.g, c.b)));
	float n = fbm(vec3(FRAGCOORD.xy * 0.005 + vec2(TIME * 0.035, TIME * 0.012), TIME * 0.05));
	c.rgb += glow_color * mist_strength * smoothstep(0.45, 0.85, n) * dark * step(0.8, c.a);
	COLOR = c;
}
