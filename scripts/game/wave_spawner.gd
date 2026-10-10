class_name WaveSpawner
extends Node
## Runs the waves of a level: a time-ordered spawn queue per wave, clear detection, boss summons.
## Driven by _process, so it follows pause and Engine.time_scale automatically.

signal wave_started(index: int)
signal wave_cleared(index: int, bonus: int)
signal enemy_spawned(enemy: Enemy)

var level: LevelData
var map: Map
var wave_index := -1
var wave_running := false

var _enemies_parent: Node3D
var _queue: Array = []  # [[time, EnemyData], ...] sorted by time
var _clock := 0.0


func setup(level_data: LevelData, level_map: Map, enemies_parent: Node3D) -> void:
	level = level_data
	map = level_map
	_enemies_parent = enemies_parent


func wave_count() -> int:
	return level.waves.size()


func has_next_wave() -> bool:
	return wave_index + 1 < wave_count()


func start_next_wave() -> void:
	if wave_running or not has_next_wave():
		return
	wave_index += 1
	wave_running = true
	_clock = 0.0
	_queue.clear()
	for group in level.waves[wave_index].groups:
		for i in group.count:
			_queue.append([group.delay + i * group.interval, group.enemy])
	_queue.sort_custom(func(a: Array, b: Array) -> bool: return a[0] < b[0])
	Audio.play(&"wave_horn")
	wave_started.emit(wave_index)


func _process(delta: float) -> void:
	if not wave_running:
		return
	_clock += delta
	while not _queue.is_empty() and _queue[0][0] <= _clock:
		spawn(_queue.pop_front()[1])
	if _queue.is_empty() and get_tree().get_nodes_in_group(&"enemies").is_empty():
		wave_running = false
		wave_cleared.emit(wave_index, level.waves[wave_index].bonus)


func spawn(data: EnemyData, start := 0.0) -> Enemy:
	var enemy := Enemy.new()
	enemy.setup(data, map.curve, 1.0 + level.hp_growth * maxi(wave_index, 0), start, randf_range(-0.3, 0.3))
	enemy.summon_requested.connect(_on_summon_requested)
	_enemies_parent.add_child(enemy)
	if start == 0.0:
		map.play_portal_spawn()
	enemy_spawned.emit(enemy)
	return enemy


func _on_summon_requested(boss: Enemy) -> void:
	for i in boss.data.summon_count:
		spawn(boss.data.summon, maxf(boss.progress - 0.7 * (i + 1), 0.01))
