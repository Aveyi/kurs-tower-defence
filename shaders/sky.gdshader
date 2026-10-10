// Fantasy sky: a soft gradient with drifting clouds above, the sun with a warm halo, and a sea of
// clouds below the horizon - the battlefield is a floating island. At night (LevelLighting) the main
// light is drawn as a moon and twinkling stars come out.
shader_type sky;

#include "res://shaders/include/noise.gdshaderinc"

uniform vec3 zenith_color : source_color = vec3(0.24, 0.44, 0.8);
uniform vec3 horizon_color : source_color = vec3(0.8, 0.84, 0.92);
uniform vec3 halo_color : source_color = vec3(1.0, 0.8, 0.55);
uniform vec3 cloud_light : source_color = vec3(1.0, 0.97, 0.92);
uniform vec3 cloud_shade : source_color = vec3(0.55, 0.62, 0.82);
uniform vec3 abyss_color : source_color = vec3(0.26, 0.36, 0.64);
uniform float cloud_speed = 0.012;
uniform float stars : hint_range(0.0, 1.0) = 0.0;
uniform float moon : hint_range(0.0, 1.0) = 0.0;
uniform vec3 moon_color : source_color = vec3(0.92, 0.94, 1.0);

void sky() {
	vec3 dir = EYEDIR;
	// the radiance cubemap (ambient light) uses a static sky so it does not have to be re-rendered every frame
	float t = AT_CUBEMAP_PASS ? 0.0 : TIME;
	float up = dir.y;
	vec3 color = mix(horizon_color, zenith_color, pow(clamp(up, 0.0, 1.0), 0.55));

	if (LIGHT0_ENABLED) {
		float sun = max(dot(dir, LIGHT0_DIRECTION), 0.0);
		color += LIGHT0_COLOR * (pow(sun, 900.0) * 3.0 + pow(sun, 10.0) * 0.25 * halo_color) * (1.0 - moon);
		// the moon: a crisp pale disc with a faint dark mare and a wide cold halo
		float disc = smoothstep(0.99935, 0.9996, sun);
		float mare = value_noise(dir * 260.0 + vec3(1.0));
		color += moon * (moon_color * disc * (1.6 - 0.5 * mare) + halo_color * (pow(sun, 60.0) * 0.35 + pow(sun, 6.0) * 0.08));
	}

	if (stars > 0.0 && up > 0.0) {
		vec3 p = dir * 160.0;
		vec3 cell = floor(p);
		float h = hash13(cell);
		float d = length(fract(p) - 0.5);
		float twinkle = 0.65 + 0.35 * sin(t * (2.0 + h * 3.0) + h * 40.0);
		color += vec3(0.9, 0.92, 1.0) * stars * step(0.994, h) * smoothstep(0.32, 0.0, d) * twinkle
				* smoothstep(0.0, 0.25, up) * (0.6 + 2.0 * (h - 0.994) / 0.006);
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
