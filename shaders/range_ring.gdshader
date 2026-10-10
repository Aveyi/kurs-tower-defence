// Attack range indicator: a soft disc with an animated dashed rim (drawn on a PlaneMesh).
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled;

uniform vec4 color : source_color = vec4(0.45, 0.8, 1.0, 1.0);

void fragment() {
	vec2 p = UV - 0.5;
	float d = length(p) * 2.0;
	float rim = smoothstep(0.93, 0.965, d) * (1.0 - smoothstep(0.985, 1.0, d));
	float dash = 0.55 + 0.45 * step(0.5, fract(atan(p.y, p.x) / TAU * 48.0 - TIME * 0.6));
	float fill = (1.0 - smoothstep(0.96, 1.0, d)) * (0.06 + 0.06 * d * d);
	ALBEDO = color.rgb;
	ALPHA = max(rim * dash, fill) * color.a;
}
