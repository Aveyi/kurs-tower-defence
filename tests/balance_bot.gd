extends SceneTree
## Balance check: a simple "average player" bot plays the level with the normal starting gold.
## It builds a mixed set of towers on the plots that cover the most road, then upgrades them,
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


func _init() -> void:
	process_frame.connect(_tick)


func _tick() -> void:
	frame += 1
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
		plots = preload("res://tests/smoke_test.gd").ranked_plots(game.map, 7.0)
		game.spawner.wave_cleared.connect(_on_wave_cleared)
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


func _towers() -> Array:
	return game.get_node("Towers").get_children()


func _spend() -> void:
	for _i in 4:  # several purchases per check if affordable
		var towers := _towers()
		var built := towers.size()
		var next_kind = BUILD_ORDER[built] if built < BUILD_ORDER.size() and built < plots.size() else null
		var cheapest = null
		for t in towers:
			if t.can_upgrade() and (cheapest == null or t.upgrade_cost() < cheapest.upgrade_cost()):
				cheapest = t
		var upgrades_owed: int = towers.reduce(func(acc, t) -> int: return acc + (2 - t.level), 0)
		var want_build: bool = next_kind != null and (built < BUILD_FIRST or upgrades_owed < built)
		if want_build:
			var data = load("res://data/towers/%s.tres" % next_kind)
			if game.gold >= data.levels[0].cost:
				game.build_tower(data, plots[built])
				continue
			return
		if cheapest and game.gold >= cheapest.upgrade_cost():
			game.upgrade_tower(cheapest)
			continue
		return


func _on_wave_cleared(index: int, _bonus: int) -> void:
	report.append("wave %2d: lives lost %2d, towers %2d, gold %4d" % [index + 1, lives_before - game.lives,
			_towers().size(), game.gold])


func _finish() -> void:
	for line in report:
		print(line)
	var levels := {}
	for t in _towers():
		var key := "%s_%d" % [t.data.id, t.level + 1]
		levels[key] = levels.get(key, 0) + 1
	print("BALANCE: %s, lives left %d/%d, towers %s" % ["victory" if game.lives > 0 else "defeat", game.lives,
			game.level.lives, levels])
	quit()
