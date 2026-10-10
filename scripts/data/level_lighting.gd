class_name LevelLighting
extends Resource
## Lighting of a level: the main light (sun or moon), sky, ambient light, exposure, glow, fog, colour grading
## and the small point lights at the portals and the castle. A level without one keeps the lighting of the
## game scene (level 1 daylight). Applied by Game._apply_lighting.

@export_group("Main light")
@export var light_color := Color(0.62, 0.7, 1.0)
@export var light_energy := 0.8
## Euler angles (degrees) of the DirectionalLight3D.
@export var light_rotation := Vector3(-50.0, -30.0, 0.0)

@export_group("Sky")
@export var zenith_color := Color(0.04, 0.05, 0.12)
@export var horizon_color := Color(0.17, 0.15, 0.3)
@export var halo_color := Color(0.6, 0.65, 0.9)
@export var cloud_light := Color(0.3, 0.3, 0.45)
@export var cloud_shade := Color(0.08, 0.08, 0.16)
@export var abyss_color := Color(0.03, 0.02, 0.07)
## 0..1: stars in the sky.
@export var stars := 1.0
## 0..1: the main light is drawn as a moon instead of a sun.
@export var moon := 1.0

@export_group("Environment")
@export var ambient_energy := 0.8
@export var ambient_sky_contribution := 0.7
@export var exposure := 1.1
@export var glow_intensity := 0.9
@export var glow_bloom := 0.08
@export var fog_color := Color(0.16, 0.12, 0.26)
@export var fog_density := 0.004
## Extra fog near the ground: thick below this height (metres), thinning above it.
@export var fog_height := 0.8
@export var fog_height_density := 0.2

@export_group("Colour grading")
@export var saturation := 0.92
@export var contrast := 1.08
@export var shadow_tint := Color(0.9, 0.92, 1.08)
@export var highlight_tint := Color(0.98, 0.96, 1.04)
@export var vignette := 0.4
@export var vignette_color := Color(0.04, 0.02, 0.08)
## Grass hue patches of shaders/ground.gdshader.
@export var grass_patch_dark := Color(0.72, 0.78, 0.78)
@export var grass_patch_light := Color(0.96, 0.98, 0.92)

@export_group("Point lights")
@export var portal_light := Color(0.7, 0.35, 1.0)
@export var portal_light_energy := 2.5
@export var castle_light := Color(1.0, 0.7, 0.4)
@export var castle_light_energy := 2.0
