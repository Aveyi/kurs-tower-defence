// Final colour grading on top of the 3D image (canvas layer under the HUD): a little more
// saturation and contrast, cool shadows / warm highlights, a warm storybook vignette.
shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, filter_linear_mipmap;
uniform float saturation = 1.12;
uniform float contrast = 1.05;
uniform vec3 shadow_tint : source_color = vec3(0.88, 0.94, 1.0);
uniform vec3 highlight_tint : source_color = vec3(1.04, 1.0, 0.93);
uniform float vignette = 0.35;
uniform vec3 vignette_color : source_color = vec3(0.16, 0.09, 0.05);

void fragment() {
	vec3 c = textureLod(screen_texture, SCREEN_UV, 0.0).rgb;
	float luma = dot(c, vec3(0.2126, 0.7152, 0.0722));
	c = mix(vec3(luma), c, saturation);
	c = (c - 0.5) * contrast + 0.5;
	c *= mix(shadow_tint, highlight_tint, smoothstep(0.1, 0.8, luma));
	vec2 d = (SCREEN_UV - 0.5) * vec2(1.25, 1.0);
	float v = smoothstep(0.35, 0.85, length(d));
	c = mix(c, vignette_color, v * vignette);
	COLOR = vec4(c, 1.0);
}
