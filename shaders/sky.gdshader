// Fantasy sky: a soft gradient with drifting clouds above, the sun with a warm halo, and a sea of
// clouds below the horizon - the battlefield is a floating island.
shader_type sky;

#include "res://shaders/include/noise.gdshaderinc"

uniform vec3 zenith_color : source_color = vec3(0.24, 0.44, 0.8);
uniform vec3 horizon_color : source_color = vec3(0.8, 0.84, 0.92);
uniform vec3 halo_color : source_color = vec3(1.0, 0.8, 0.55);
uniform vec3 cloud_light : source_color = vec3(1.0, 0.97, 0.92);
uniform vec3 cloud_shade : source_color = vec3(0.55, 0.62, 0.82);
uniform vec3 abyss_color : source_color = vec3(0.26, 0.36, 0.64);
uniform float cloud_speed = 0.012;

void sky() {
	vec3 dir = EYEDIR;
	// the radiance cubemap (ambient light) uses a static sky so it does not have to be re-rendered every frame
	float t = AT_CUBEMAP_PASS ? 0.0 : TIME;
	float up = dir.y;
	vec3 color = mix(horizon_color, zenith_color, pow(clamp(up, 0.0, 1.0), 0.55));

	if (LIGHT0_ENABLED) {
		float sun = max(dot(dir, LIGHT0_DIRECTION), 0.0);
		color += LIGHT0_COLOR * (pow(sun, 900.0) * 3.0 + pow(sun, 10.0) * 0.25 * halo_color);
	}

	if (up > 0.0) {  // high clouds
		vec2 uv = dir.xz / (up + 0.2) * 1.3 + vec2(t * cloud_speed, t * cloud_speed * 0.4);
		float c = smoothstep(0.52, 0.78, fbm(vec3(uv, t * 0.01))) * smoothstep(0.0, 0.3, up);
		float shade = smoothstep(0.4, 0.8, fbm(vec3(uv * 1.8 + 3.0, 1.0)));
		color = mix(color, mix(cloud_shade, cloud_light, shade), c * 0.85);
	}

	if (up < 0.05) {  // sea of clouds under the island
		float depth = max(-up, 0.0);
		vec2 uv = dir.xz / (depth + 0.12) * 2.6 + vec2(t * cloud_speed * 4.0, t * cloud_speed * 1.6);
		float c = fbm(vec3(uv, t * 0.02));
		float puffs = smoothstep(0.46, 0.56, c);
		// fake sun lighting: puffs are brighter where the cloud thins toward the sun
		vec2 to_sun = LIGHT0_ENABLED ? normalize(LIGHT0_DIRECTION.xz + 0.001) : vec2(0.5);
		float lit = clamp((c - fbm(vec3(uv + to_sun * 0.12, t * 0.02))) * 5.0 + 0.55, 0.0, 1.0);
		vec3 sea = mix(abyss_color, cloud_shade, smoothstep(0.2, 0.5, c));
		sea = mix(sea, mix(cloud_shade, cloud_light, lit), puffs);
		float haze = smoothstep(-0.25, 0.02, up);  // distant clouds melt into the horizon haze
		sea = mix(sea, horizon_color, haze * 0.6);
		color = mix(color, sea, smoothstep(0.05, -0.08, up));
	}
	COLOR = color;
}
