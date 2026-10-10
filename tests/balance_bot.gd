extends SceneTree
## Balance check: a simple "average player" bot plays the level with the normal starting gold.
## It builds a mixed set of towers on the free plots that cover the most road from the portals open at that
## moment (so a sealed portal is defended once it opens), then upgrades them,
## and starts every wave as soon as the previous one is cleared.
##   godot --path . --headless -s tests/balance_bot.gd [-- res://path/to/level.tres]
## Untyped on purpose (see smoke_test.gd).

const BUILD_ORDER := ["archer", "cannon", "archer", "mage", "ice", "ballista", "archer", "cannon", "mage",
		"archer", "ice", "mage", "cannon", "ballista", "archer", "mage"]
## Keep building until this many towers stand, then prefer upgrades.
const BUILD_FIRST := 6

var game
var plots := []
var frame := 0
var lives_before := 0
var report := []
var _leaks := {}  # enemy id -> how many reached the castle this wave
var _coverage_cache := {}  # "open_only/portal" -> plot cell -> covered road samples (routes never change)


func _init() -> void:
	process_frame.connect(_tick)


func _tick() -> void:
	frame += 1
	if frame == 1:
		root.get_node("Session").record_results = false
	if frame == 1:
		var scene = load("res://scenes/game/game.tscn").instantiate()
		var args := OS.get_cmdline_user_args()
		if not args.is_empty():
			scene.level = load(args[0])
		root.add_child(scene)
		current_scene = scene
		return
	if frame == 5:
		game = current_scene
		if game == null or not game.has_method("start_next_wave"):
			push_error("game scene failed to load")
			quit(1)
			return
		plots = _free_plots()
		game.spawner.wave_cleared.connect(_on_wave_cleared)
		game.spawner.enemy_spawned.connect(func(e) -> void:
			e.reached_end.connect(func(x) -> void: _leaks[x.data.id] = _leaks.get(x.data.id, 0) + 1))
		Engine.time_scale = 4.0
		_spend()
		lives_before = game.lives
		game.start_next_wave()
		return
	if game == null:
		return
	if frame % 20 == 0:
		_spend()
	if game.over:
		_finish()
	elif not game.spawner.wave_running and game.spawner.has_next_wave() and frame % 20 == 10:
		lives_before = game.lives
		game.start_next_wave()
	if frame > 200000:
		print("TIMEOUT")
		quit(1)


## Free plots, best first, by the road they cover on the open portals' routes - and, like a player who has
## read the level description, on a sealed portal's routes one wave before it opens.
func _free_plots() -> Array:
	var sealed_soon: bool = game.level.sealed_portal_wave >= 0 \
			and game.spawner.wave_index + 1 >= game.level.sealed_portal_wave
	var cover := _coverage(not sealed_soon, -1)
	var free := cover.keys().filter(func(cell) -> bool: return game.tower_at(cell) == null)
	free.sort_custom(func(a, b) -> bool: return cover[a] > cover[b])
	return free


func _coverage(open_only: bool, portal: int) -> Dictionary:
	var open_now: Array = game.map.portal_open
	var key := "%s/%d/%s" % [open_only, portal, open_now]
	if not _coverage_cache.has(key):
		_coverage_cache[key] = preload("res://tests/smoke_test.gd").plot_coverage(game.map, 7.0, open_only, portal)
	return _coverage_cache[key]


## Free plots guarding a portal (open, or opening with the next wave) that has fewer than 2 towers covering at
## least 8 m of its road; empty when every such portal is guarded.
func _guard_plots() -> Array:
	var map = game.map
	for p in map.portals.size():
		var soon: bool = game.level.sealed_portal_wave >= 0 and game.spawner.wave_index + 1 >= game.level.sealed_portal_wave
		if not map.portal_open[p] and not soon:
			continue
		var cover: Dictionary = _coverage(false, p)
		var guards := _towers().filter(func(t) -> bool: return cover.get(t.cell, 0) >= 4).size()
		if guards < 2:
			var free := cover.keys().filter(func(c) -> bool: return cover[c] >= 4 and game.tower_at(c) == null)
			free.sort_custom(func(a, b) -> bool: return cover[a] > cover[b])
			if not free.is_empty():
				return free
	return []


func _towers() -> Array:
	return game.get_node("Towers").get_children()


func _spend() -> void:
	for _i in 4:  # several purchases per check if affordable
		var towers := _towers()
		var built := towers.size()
		var guard := _guard_plots()
		if not guard.is_empty():  # a portal without towers of its own comes first
			var kind: String = BUILD_ORDER[built] if built < BUILD_ORDER.size() else "archer"
			var guard_data = load("res://data/towers/%s.tres" % kind)
			if game.gold >= guard_data.levels[0].cost:
				game.build_tower(guard_data, guard[0])
				continue
			return
		plots = _free_plots()
		var next_kind = BUILD_ORDER[built] if built < BUILD_ORDER.size() and not plots.is_empty() else null
		var cheapest = null
		for t in towers:
			if t.can_upgrade() and (cheapest == null or t.upgrade_cost() < cheapest.upgrade_cost()):
				cheapest = t
		var upgrades_owed: int = towers.reduce(func(acc, t) -> int: return acc + (2 - t.level), 0)
		var want_build: bool = next_kind != null and (built < BUILD_FIRST or upgrades_owed < built)
		if want_build:
			var data = load("res://data/towers/%s.tres" % next_kind)
			if game.gold >= data.levels[0].cost:
				game.build_tower(data, plots[0])
				continue
			return
		if cheapest and game.gold >= cheapest.upgrade_cost():
			game.upgrade_tower(cheapest)
			continue
		return


func _on_wave_cleared(index: int, _bonus: int) -> void:
	report.append("wave %2d: lives lost %2d, towers %2d, gold %4d%s" % [index + 1, lives_before - game.lives,
			_towers().size(), game.gold, "" if _leaks.is_empty() else ", leaked %s" % _leaks])
	_leaks = {}


func _finish() -> void:
	if not _leaks.is_empty():
		report.append("wave %2d (lost): leaked %s" % [game.spawner.wave_index + 1, _leaks])
	for line in report:
		print(line)
	var levels := {}
	for t in _towers():
		var key := "%s_%d" % [t.data.id, t.level + 1]
		levels[key] = levels.get(key, 0) + 1
	print("BALANCE: %s, lives left %d/%d, towers %s" % ["victory" if game.lives > 0 else "defeat", game.lives,
			game.level.lives, levels])
	quit()
