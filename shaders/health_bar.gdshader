// Billboarded health bar; the fill ratio is a per-instance uniform, so all bars share one material.
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, shadows_disabled;

instance uniform float ratio : hint_range(0.0, 1.0) = 1.0;
uniform vec4 full_color : source_color = vec4(0.35, 0.9, 0.3, 1.0);
uniform vec4 low_color : source_color = vec4(0.95, 0.25, 0.15, 1.0);
uniform vec4 back_color : source_color = vec4(0.08, 0.06, 0.05, 0.85);

void vertex() {
	// keep the position, replace the rotation with the camera's so the quad always faces the viewer
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
}

void fragment() {
	float border = step(0.03, UV.x) * step(UV.x, 0.97) * step(0.18, UV.y) * step(UV.y, 0.82);
	float x = (UV.x - 0.03) / 0.94;
	vec3 fill = mix(low_color.rgb, full_color.rgb, smoothstep(0.15, 0.7, ratio));
	fill *= 1.0 - 0.25 * step(0.5, UV.y);  // a little bevel
	vec3 col = x < ratio ? fill : back_color.rgb;
	ALBEDO = mix(vec3(0.02), col, border);
	ALPHA = 0.92;
}
