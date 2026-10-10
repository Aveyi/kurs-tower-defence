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
var _portal_bag: Array = []  # shuffled open portal indices still to hand out
var _route_bags := {}  # portal index -> shuffled route indices of that portal still to hand out
## The wave that just started opened a sealed portal (for the HUD).
var opened_portal := -1
## A sealed portal opens with the next wave (for the HUD's warning).
var portal_opens_next := -1
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
	opened_portal = -1
	portal_opens_next = -1
	if level.sealed_portal_wave >= 0 and wave_index >= level.sealed_portal_wave:
		for i in map.portals.size():
			if not map.portal_open[i]:
				map.open_portal(i)
				opened_portal = i
	elif level.sealed_portal_wave >= 0 and wave_index + 1 == level.sealed_portal_wave:
		for i in map.portals.size():
			if not map.portal_open[i]:
				map.stir_portal(i)
				portal_opens_next = i
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


## Spawns an enemy at `start` metres along a route (-1: the next route from shuffled bags, so every
## open portal gets an equal share of the wave and every branch of its forks gets its share of that).
func spawn(data: EnemyData, start := 0.0, route := -1) -> Enemy:
	if route < 0:
		route = _next_route()
	var enemy := Enemy.new()
	enemy.setup(data, map.routes[route], level.hp_multiplier(wave_index), start, randf_range(-0.3, 0.3))
	enemy.route = route
	enemy.summon_requested.connect(_on_summon_requested)
	_enemies_parent.add_child(enemy)
	if start == 0.0:
		map.play_portal_spawn(map.route_portal[route])
	enemy_spawned.emit(enemy)
	return enemy


func _next_route() -> int:
	if _portal_bag.is_empty():
		_portal_bag = range(map.portals.size()).filter(func(i: int) -> bool: return map.portal_open[i])
		_portal_bag.shuffle()
	var portal: int = _portal_bag.pop_back()
	var bag: Array = _route_bags.get(portal, [])
	if bag.is_empty():
		bag = range(map.routes.size()).filter(func(r: int) -> bool: return map.route_portal[r] == portal)
		bag.shuffle()
		_route_bags[portal] = bag
	return bag.pop_back()


func _on_summon_requested(boss: Enemy) -> void:
	for i in boss.data.summon_count:
		spawn(boss.data.summon, maxf(boss.progress - 0.7 * (i + 1), 0.01), boss.route)
