// Screen-space ink outlines from depth discontinuities (full-screen quad in front of the camera).
// A Laplacian of the linear depth ignores smooth slopes and only reacts to silhouettes.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, depth_test_disabled, cull_disabled, shadows_disabled, fog_disabled;

uniform sampler2D depth_texture : hint_depth_texture, filter_nearest;
uniform vec3 line_color : source_color = vec3(0.1, 0.06, 0.05);
uniform float thickness = 1.3;
uniform float sensitivity = 0.012;
uniform float opacity : hint_range(0.0, 1.0) = 0.42;
uniform float fade_start = 45.0;
uniform float fade_end = 110.0;

void vertex() {
	POSITION = vec4(VERTEX.xy, 1.0, 1.0);
}

float linear_depth(vec2 uv, mat4 inv_projection) {
	float depth = texture(depth_texture, uv).r;
	vec4 view = inv_projection * vec4(uv * 2.0 - 1.0, depth, 1.0);
	return -view.z / view.w;
}

void fragment() {
	vec2 px = thickness / VIEWPORT_SIZE;
	float c = linear_depth(SCREEN_UV, INV_PROJECTION_MATRIX);
	float l = linear_depth(SCREEN_UV - vec2(px.x, 0.0), INV_PROJECTION_MATRIX);
	float r = linear_depth(SCREEN_UV + vec2(px.x, 0.0), INV_PROJECTION_MATRIX);
	float u = linear_depth(SCREEN_UV - vec2(0.0, px.y), INV_PROJECTION_MATRIX);
	float d = linear_depth(SCREEN_UV + vec2(0.0, px.y), INV_PROJECTION_MATRIX);
	float laplace = abs(l + r + u + d - 4.0 * c) / max(c, 0.001);
	float edge = smoothstep(sensitivity, sensitivity * 2.5, laplace);
	edge *= 1.0 - smoothstep(fade_start, fade_end, min(c, min(min(l, r), min(u, d))));
	ALBEDO = line_color;
	ALPHA = edge * opacity;
}
