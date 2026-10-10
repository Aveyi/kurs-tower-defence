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
	map.build(level)
	gold = level.start_gold
	lives = level.lives
	spawner.setup(level, map, _enemies)
	spawner.enemy_spawned.connect(_on_enemy_spawned)
	spawner.wave_started.connect(func(i: int) -> void: wave_started.emit(i, spawner.wave_count()))
	spawner.wave_cleared.connect(_on_wave_cleared)
	var rect := map.bounds()
	camera_rig.setup(rect, Vector3(rect.get_center().x, 0, rect.get_center().y + 1.0), 26.0)
	build.setup(self)
	hud.setup(self)
	_countdown = FIRST_WAVE_DELAY


func _process(delta: float) -> void:
	if _countdown > 0.0 and not over:
		_countdown -= delta
		countdown_changed.emit(_countdown)
		if _countdown <= 0.0:
			start_next_wave()


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
	return tower


func upgrade_tower(tower: Tower) -> bool:
	if over or not tower.can_upgrade() or gold < tower.upgrade_cost():
		return false
	_spend(tower.upgrade_cost())
	tower.upgrade()
	return true


func sell_tower(tower: Tower) -> void:
	gold += tower.sell_value()
	gold_changed.emit(gold)
	_towers.erase(tower.cell)
	tower.queue_free()


func _spend(amount: int) -> void:
	gold -= amount
	gold_changed.emit(gold)


# --- enemies and waves ---------------------------------------------------------------------
func _on_enemy_spawned(enemy: Enemy) -> void:
	enemy.died.connect(_on_enemy_died)
	enemy.reached_end.connect(_on_enemy_reached_end)


func _on_enemy_died(enemy: Enemy) -> void:
	gold += enemy.data.reward
	gold_changed.emit(gold)


func _on_enemy_reached_end(enemy: Enemy) -> void:
	if over:
		return
	lives = maxi(lives - enemy.data.damage, 0)
	lives_changed.emit(lives)
	if lives == 0:
		_finish(false)


func _on_wave_cleared(_index: int, bonus: int) -> void:
	if over:
		return
	gold += bonus
	gold_changed.emit(gold)
	if spawner.has_next_wave():
		_countdown = WAVE_DELAY
	else:
		_finish(true)


func _finish(victory: bool) -> void:
	over = true
	set_fast(false)
	build.clear()
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
