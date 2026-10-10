class_name Game
extends Node3D
## Root of the game scene: economy (gold, lives), wave flow, building and the end of the game.

signal gold_changed(gold: int)
signal lives_changed(lives: int)
signal wave_started(index: int, total: int)
## Seconds until the next wave starts automatically; negative when no countdown is running.
signal countdown_changed(seconds: float)
signal game_over(victory: bool)

const FIRST_WAVE_DELAY := 30.0
const WAVE_DELAY := 15.0

@export var level: LevelData
@export var tower_types: Array[TowerData] = []

var gold := 0
var lives := 0
var over := false
var fast := false

var _countdown := -1.0
var _towers := {}  # Vector2i -> Tower

@onready var map: Map = $Map
@onready var spawner: WaveSpawner = $WaveSpawner
@onready var camera_rig: CameraRig = $CameraRig
@onready var build: BuildController = $BuildController
@onready var hud: Hud = $HUD
@onready var _enemies: Node3D = $Enemies
@onready var _tower_root: Node3D = $Towers
@onready var _projectiles: Node3D = $Projectiles


func _ready() -> void:
	get_tree().paused = false
	Engine.time_scale = 1.0
	if Session.level:
		level = Session.level
	Settings.changed.connect(_apply_graphics)
	_apply_graphics()
	map.build(level)
	_apply_lighting(level.lighting)
	gold = level.start_gold
	lives = level.lives
	spawner.setup(level, map, _enemies)
	spawner.enemy_spawned.connect(_on_enemy_spawned)
	map.portal_opened.connect(func(_i: int) -> void: camera_rig.shake(0.5))
	spawner.wave_started.connect(func(i: int) -> void: wave_started.emit(i, spawner.wave_count()))
	spawner.wave_cleared.connect(_on_wave_cleared)
	var rect := map.bounds()
	camera_rig.setup(rect, Vector3(rect.get_center().x, 0, rect.get_center().y + 1.0), 38.0)
	build.setup(self)
	hud.setup(self)
	_countdown = FIRST_WAVE_DELAY
	Effects.prewarm(_projectiles)
	Audio.play_music(level.music)


func _process(delta: float) -> void:
	if _countdown > 0.0 and not over:
		_countdown -= delta
		countdown_changed.emit(_countdown)
		if _countdown <= 0.0:
			start_next_wave()


## Night (or any custom) lighting of the level; without one the scene's daylight stays as it is.
func _apply_lighting(lighting: LevelLighting) -> void:
	if lighting == null:
		return
	var sun: DirectionalLight3D = $Sun
	sun.light_color = lighting.light_color
	sun.light_energy = lighting.light_energy
	sun.rotation_degrees = lighting.light_rotation
	var environment: Environment = $WorldEnvironment.environment
	environment.ambient_light_energy = lighting.ambient_energy
	environment.ambient_light_sky_contribution = lighting.ambient_sky_contribution
	environment.tonemap_exposure = lighting.exposure
	environment.glow_intensity = lighting.glow_intensity
	environment.glow_bloom = lighting.glow_bloom
	environment.fog_enabled = lighting.fog_density > 0.0
	environment.fog_light_color = lighting.fog_color
	environment.fog_density = lighting.fog_density
	environment.fog_sky_affect = 0.0
	environment.fog_height = lighting.fog_height
	environment.fog_height_density = lighting.fog_height_density
	var sky: ShaderMaterial = environment.sky.sky_material
	for param in [&"zenith_color", &"horizon_color", &"halo_color", &"cloud_light", &"cloud_shade", &"abyss_color"]:
		sky.set_shader_parameter(param, lighting.get(param))
	sky.set_shader_parameter(&"stars", lighting.stars)
	sky.set_shader_parameter(&"moon", lighting.moon)
	var grade: ShaderMaterial = $PostProcess/ColorGrade.material
	for param in [&"saturation", &"contrast", &"shadow_tint", &"highlight_tint", &"vignette", &"vignette_color"]:
		grade.set_shader_parameter(param, lighting.get(param))
	map.set_ground_parameter(&"patch_dark", lighting.grass_patch_dark)
	map.set_ground_parameter(&"patch_light", lighting.grass_patch_light)
	map.add_prop_lights()
	for i in map.portals.size():
		var light := map.add_light(map.portals[i].position + Vector3.UP * 1.3, lighting.portal_light,
				lighting.portal_light_energy if map.portal_open[i] else lighting.portal_light_energy * 0.15, 7.0)
		map.portal_opened.connect(func(index: int) -> void:
			if index == i:
				create_tween().tween_property(light, "light_energy", lighting.portal_light_energy, 1.0))
		map.portal_stirring.connect(func(index: int) -> void:
			if index == i:
				create_tween().tween_property(light, "light_energy", lighting.portal_light_energy * 0.4, 1.5))
	map.add_light(map.castle_center + Vector3.UP * 2.6, lighting.castle_light, lighting.castle_light_energy, 9.0)


func _apply_graphics() -> void:
	Settings.apply_to_scene($WorldEnvironment.environment, $Sun, $CameraRig/Camera3D/Outline)


func start_next_wave() -> void:
	if over or spawner.wave_running or not spawner.has_next_wave():
		return
	_countdown = -1.0
	countdown_changed.emit(_countdown)
	spawner.start_next_wave()


func set_fast(value: bool) -> void:
	fast = value
	Engine.time_scale = 2.0 if fast else 1.0


# --- towers --------------------------------------------------------------------------------
func tower_at(cell: Vector2i) -> Tower:
	return _towers.get(cell)


func can_build(data: TowerData, cell: Vector2i) -> bool:
	return not over and map.is_plot(cell) and not _towers.has(cell) and gold >= data.levels[0].cost


func build_tower(data: TowerData, cell: Vector2i) -> Tower:
	if not can_build(data, cell):
		return null
	_spend(data.levels[0].cost)
	var tower := Tower.new()
	tower.setup(data, cell, _projectiles)
	tower.position = map.cell_center(cell) + Vector3(0, Map.PLOT_HEIGHT, 0)
	_tower_root.add_child(tower)
	_towers[cell] = tower
	Audio.play(&"build")
	Effects.burst(_projectiles, &"dust", tower.position, 2.0)
	Effects.burst(_projectiles, &"gold", tower.position + Vector3.UP * 0.5)
	return tower


func upgrade_tower(tower: Tower) -> bool:
	if over or not tower.can_upgrade() or gold < tower.upgrade_cost():
		return false
	_spend(tower.upgrade_cost())
	tower.upgrade()
	Audio.play(&"upgrade")
	Effects.burst(_projectiles, &"gold", tower.position + Vector3.UP * 1.0, 1.6)
	return true


func sell_tower(tower: Tower) -> void:
	gold += tower.sell_value()
	gold_changed.emit(gold)
	_towers.erase(tower.cell)
	Audio.play(&"sell")
	Effects.burst(_projectiles, &"dust", tower.position, 2.0)
	tower.queue_free()


func _spend(amount: int) -> void:
	gold -= amount
	gold_changed.emit(gold)


# --- enemies and waves ---------------------------------------------------------------------
func _on_enemy_spawned(enemy: Enemy) -> void:
	enemy.died.connect(_on_enemy_died)
	enemy.reached_end.connect(_on_enemy_reached_end)
	enemy.slammed.connect(func(_e: Enemy) -> void: camera_rig.shake(0.35))


func _on_enemy_died(enemy: Enemy) -> void:
	gold += enemy.data.reward
	gold_changed.emit(gold)
	Audio.play(&"coin", -8.0, 0.08)
	Effects.floating_text(_projectiles, enemy.global_position + Vector3.UP * (enemy.data.hp_bar_height + 0.3),
			"+%d" % enemy.data.reward, Color(1.0, 0.85, 0.3))
	if enemy.data.is_boss:
		camera_rig.shake(0.3)


func _on_enemy_reached_end(enemy: Enemy) -> void:
	if over:
		return
	lives = maxi(lives - enemy.data.damage, 0)
	lives_changed.emit(lives)
	Audio.play(&"castle_hit", 0.0, 0.25)
	camera_rig.shake(0.25 + 0.04 * enemy.data.damage)
	var gate := enemy.global_position + Vector3.UP * 0.8
	Effects.impact(_projectiles, gate, Color(1.0, 0.3, 0.2), 1.0)
	Effects.burst(_projectiles, &"debris", gate)
	Effects.burst(_projectiles, &"dust", gate, 1.5)
	if lives == 0:
		_finish(false)


func _on_wave_cleared(_index: int, bonus: int) -> void:
	if over:
		return
	gold += bonus
	gold_changed.emit(gold)
	if spawner.has_next_wave():
		_countdown = WAVE_DELAY
		Audio.play(&"wave_clear")
	else:
		_finish(true)


func _finish(victory: bool) -> void:
	over = true
	set_fast(false)
	build.clear()
	Audio.stop_music(1.0)
	Audio.play(&"victory" if victory else &"defeat")
	Session.record_result(level, victory, lives)
	game_over.emit(victory)


# --- scene flow ----------------------------------------------------------------------------
func restart() -> void:
	get_tree().paused = false
	Engine.time_scale = 1.0
	get_tree().reload_current_scene()


func to_menu() -> void:
	get_tree().paused = false
	Engine.time_scale = 1.0
	get_tree().change_scene_to_file("res://scenes/ui/main_menu.tscn")
