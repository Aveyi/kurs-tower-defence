// Stylized river water: colour and transparency by depth (depth buffer), foam along the banks,
// flowing ripples, caustic highlights and drifting magical sparkles.
shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_back, specular_schlick_ggx;

#include "res://shaders/include/noise.gdshaderinc"

uniform vec3 shallow_color : source_color = vec3(0.3, 0.78, 0.78);
uniform vec3 deep_color : source_color = vec3(0.07, 0.3, 0.58);
uniform vec3 foam_color : source_color = vec3(0.94, 0.98, 1.0);
uniform vec3 sparkle_color : source_color = vec3(0.75, 1.0, 1.0);
uniform float depth_fade = 0.3;
uniform float foam_width = 0.1;
uniform vec2 flow = vec2(0.0, 0.32);
uniform sampler2D depth_texture : hint_depth_texture, filter_nearest;

varying vec3 v_world;

void vertex() {
	v_world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	VERTEX.y += (sin(v_world.x * 3.0 + TIME * 1.4) + sin(v_world.z * 2.2 - TIME * 1.1)) * 0.004;
}

void fragment() {
	// thickness of water along the view ray: scene depth behind the surface minus surface depth
	float depth = texture(depth_texture, SCREEN_UV).r;
	vec4 behind = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, depth, 1.0);
	behind.xyz /= behind.w;
	float thickness = max(VERTEX.z - behind.z, 0.0);

	vec2 uv = v_world.xz;
	float t = TIME;
	float n1 = fbm(vec3(uv * 1.5 - flow * t, t * 0.12));
	float n2 = fbm(vec3(uv * 3.2 - flow * t * 1.7 + 4.1, t * 0.2));
	float caustic = pow(1.0 - abs(n2 * 2.0 - 1.0), 8.0);

	float deep = clamp(thickness / depth_fade, 0.0, 1.0);
	vec3 color = mix(shallow_color, deep_color, deep) * (0.9 + 0.2 * n1);
	color += caustic * 0.15 * (1.0 - deep * 0.5);

	float foam = 1.0 - smoothstep(0.0, foam_width, thickness);
	foam = smoothstep(0.35, 0.6, foam + (n2 - 0.5) * 0.7);
	color = mix(color, foam_color, foam);

	float sparkle = smoothstep(0.88, 0.95, value_noise(vec3(uv * 22.0 - flow * t * 3.0, t * 1.8)));
	sparkle *= 1.0 - foam;

	ALBEDO = color;
	EMISSION = sparkle_color * sparkle * 1.6 + caustic * vec3(0.05, 0.1, 0.12);
	ALPHA = clamp(mix(0.45, 0.88, deep) + foam, 0.0, 1.0);
	ROUGHNESS = 0.06;
	SPECULAR = 0.6;
	// gentle normal wobble from the ripples (view space)
	NORMAL = normalize(NORMAL + (VIEW_MATRIX * vec4((n1 - 0.5) * 0.35, 0.0, (n2 - 0.5) * 0.35, 0.0)).xyz);
}
