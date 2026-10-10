// Pulsing square frame marking the hovered / selected map cell.
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled;

uniform vec4 color : source_color = vec4(0.5, 1.0, 0.45, 1.0);
uniform float pulse = 1.0;

void fragment() {
	vec2 q = abs(UV - 0.5) * 2.0;
	float edge = max(q.x, q.y);
	float frame = smoothstep(0.82, 0.9, edge) * (1.0 - smoothstep(0.97, 1.0, edge));
	float glow = (1.0 - edge) * 0.12;
	float wave = 0.75 + 0.25 * sin(TIME * 5.0) * pulse;
	ALBEDO = color.rgb;
	ALPHA = (frame * wave + glow) * color.a;
}
