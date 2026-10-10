extends Node
## Graphics settings (autoload "Settings"): stored in user://settings.cfg, applied to the window and
## the root viewport here; scene-dependent options (shadows, SSAO, bloom, outlines) are applied by
## the game scene through apply_to_scene() whenever `changed` fires.

signal changed

enum WindowMode { WINDOWED, FULLSCREEN }
enum AntiAliasing { OFF, FXAA, SMAA, MSAA_2X, MSAA_4X }
enum Shadows { OFF, LOW, HIGH }

const PATH := "user://settings.cfg"
const SECTION := "graphics"
const PRESETS := {
	"low": {render_scale = 0.75, antialiasing = AntiAliasing.FXAA, shadows = Shadows.LOW, ssao = false,
			bloom = true, outlines = true},
	"medium": {render_scale = 1.0, antialiasing = AntiAliasing.SMAA, shadows = Shadows.LOW, ssao = false,
			bloom = true, outlines = true},
	"high": {render_scale = 1.0, antialiasing = AntiAliasing.SMAA, shadows = Shadows.HIGH, ssao = true,
			bloom = true, outlines = true},
	"ultra": {render_scale = 1.0, antialiasing = AntiAliasing.MSAA_4X, shadows = Shadows.HIGH, ssao = true,
			bloom = true, outlines = true},
}

var window_mode := WindowMode.WINDOWED
var vsync := true
## 3D resolution relative to the window; below 1.0 the image is upscaled with AMD FSR 1.0.
var render_scale := 1.0
var antialiasing := AntiAliasing.SMAA
var shadows := Shadows.HIGH
var ssao := true
var bloom := true
var outlines := true


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	load_settings()
	apply()


func load_settings() -> void:
	var config := ConfigFile.new()
	if config.load(PATH) != OK:
		return
	for key in ["window_mode", "vsync", "render_scale", "antialiasing", "shadows", "ssao", "bloom", "outlines"]:
		if config.has_section_key(SECTION, key):
			set(key, config.get_value(SECTION, key))


func save_settings() -> void:
	var config := ConfigFile.new()
	config.load(PATH)  # keep the audio section written by Audio
	for key in ["window_mode", "vsync", "render_scale", "antialiasing", "shadows", "ssao", "bloom", "outlines"]:
		config.set_value(SECTION, key, get(key))
	config.save(PATH)


func set_option(key: String, value: Variant) -> void:
	set(key, value)
	save_settings()
	apply()


func apply_preset(preset: String) -> void:
	for key in PRESETS[preset]:
		set(key, PRESETS[preset][key])
	save_settings()
	apply()


## Window and root viewport options; then tells open scenes to refresh their own options.
func apply() -> void:
	if not DisplayServer.get_name() == "headless":
		var fullscreen := window_mode == WindowMode.FULLSCREEN
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if fullscreen
				else DisplayServer.WINDOW_MODE_WINDOWED)
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if vsync else DisplayServer.VSYNC_DISABLED)
	var viewport := get_tree().root
	viewport.scaling_3d_mode = Viewport.SCALING_3D_MODE_FSR if render_scale < 0.99 else Viewport.SCALING_3D_MODE_BILINEAR
	viewport.scaling_3d_scale = render_scale
	viewport.msaa_3d = {AntiAliasing.MSAA_2X: Viewport.MSAA_2X, AntiAliasing.MSAA_4X: Viewport.MSAA_4X}.get(
			antialiasing, Viewport.MSAA_DISABLED)
	viewport.screen_space_aa = {AntiAliasing.FXAA: Viewport.SCREEN_SPACE_AA_FXAA,
			AntiAliasing.SMAA: Viewport.SCREEN_SPACE_AA_SMAA}.get(antialiasing, Viewport.SCREEN_SPACE_AA_DISABLED)
	RenderingServer.directional_shadow_atlas_set_size(4096 if shadows == Shadows.HIGH else 2048, true)
	changed.emit()


## Options that live in the 3D scene itself.
func apply_to_scene(environment: Environment, sun: DirectionalLight3D, outline: Node3D) -> void:
	environment.ssao_enabled = ssao
	environment.glow_enabled = bloom
	sun.shadow_enabled = shadows != Shadows.OFF
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS if shadows == Shadows.HIGH \
			else DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	outline.visible = outlines
