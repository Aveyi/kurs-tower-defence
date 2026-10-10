extends SceneTree
## Smoke test: launches the game scene, builds towers, runs waves at high speed and saves screenshots.
##   godot --path . -s tests/smoke_test.gd -- <screenshot_dir> [waves]
## Game classes are used untyped on purpose: with --script this file is compiled before autoloads
## (Audio) are registered, so it must not pull the game scripts in at compile time.

var out_dir := "user://"
var waves_to_run := 3
var game
var frame := 0
var shots := 0
var closeups := 0
var _free_plot
var summoned := 0


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		out_dir = args[0]
	if args.size() > 1:
		waves_to_run = int(args[1])
	process_frame.connect(_tick)


func _shot(name: String) -> void:
	shots += 1
	root.get_texture().get_image().save_png("%s/%02d_%s.png" % [out_dir, shots, name])


func _tick() -> void:
	frame += 1
	if frame == 1:
		root.get_node("Session").record_results = false
	if frame == 1:  # not in _init: autoloads are registered only after it returns
		change_scene_to_file("res://scenes/game/game.tscn")
	elif frame == 5:
		game = current_scene
		if game == null or not game.has_method("start_next_wave"):
			push_error("game scene failed to load")
			quit(1)
			return
		game.spawner.enemy_spawned.connect(func(e) -> void: summoned += int(e.progress > 0.0))
		game.gold = 5000
		var plots := ranked_plots(game.map, 7.0)
		var kinds := ["archer", "cannon", "mage", "ice", "ballista", "archer", "cannon", "mage", "ice", "archer"]
		var count := 10 if waves_to_run > 3 else 6
		for i in count:
			assert(game.build_tower(load("res://data/towers/%s.tres" % kinds[i]), plots[i]) != null, "could not build")
		for tower in game.get_node("Towers").get_children():
			game.upgrade_tower(tower)
			if waves_to_run > 3:  # a full run: max out the defence
				game.upgrade_tower(tower)
		game.build.select_tower(game.tower_at(plots[2]))
		_free_plot = plots[count]
	elif frame == 40:
		_shot("built")
		game.build.clear()
		game.build.select_plot(_free_plot)
	elif frame == 60:
		_shot("build_panel")
		game.build.clear()
		game.start_next_wave()
		Engine.time_scale = 4.0
	if game and game.spawner.wave_index == game.spawner.wave_count() - 1 and frame % 60 == 0 and closeups < 3:
		for node in get_nodes_in_group(&"enemies"):  # close-up on a boss
			var enemy = node
			if enemy.data.is_boss and enemy.progress > 8.0:
				game.camera_rig.setup(game.map.bounds(), enemy.global_position, 11.0)
				closeups += 1
				_shot("boss_closeup")
				break
	if frame > 60 and frame % 200 == 0:
		var enemies := get_nodes_in_group(&"enemies").size()
		print("frame %d: wave %d/%d running=%s enemies=%d gold=%d lives=%d fps=%d" % [frame, game.spawner.wave_index + 1,
				game.spawner.wave_count(), game.spawner.wave_running, enemies, game.gold, game.lives,
				Engine.get_frames_per_second()])
		if enemies > 0 and shots < 6:
			_shot("combat")
		if not game.spawner.wave_running:
			if game.spawner.wave_index + 1 >= waves_to_run or game.over:
				_shot("end")
				print("RESULT: waves=%d lives=%d gold=%d over=%s summoned_minions=%d" % [game.spawner.wave_index + 1,
						game.lives, game.gold, game.over, summoned])
				print("SOUNDS: ", root.get_node("Audio")._players.keys())
				quit()
			else:
				game.start_next_wave()
	if frame > 60000:
		print("TIMEOUT")
		quit(1)


## Tower plots sorted by how much of the enemy routes they cover within `reach` metres.
static func ranked_plots(map, reach: float) -> Array:
	var samples := []
	for curve in map.routes:
		var length: float = curve.get_baked_length()
		for d in range(0, int(length), 2):
			var p: Vector3 = curve.sample_baked(d)
			if not samples.any(func(q) -> bool: return q.distance_to(p) < 1.0):
				samples.append(p)
	var plots := []
	for row in map.size.y:
		for col in map.size.x:
			var cell := Vector2i(col, row)
			if map.is_plot(cell):
				var at: Vector3 = map.cell_center(cell)
				plots.append([samples.filter(func(q) -> bool: return q.distance_to(at) <= reach).size(), cell])
	plots.sort_custom(func(a, b) -> bool: return a[0] > b[0])
	return plots.map(func(p): return p[1])
