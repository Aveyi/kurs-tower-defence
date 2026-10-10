extends SceneTree
## Smoke test: launches the game scene, builds towers, runs waves at high speed and saves screenshots.
##   godot --path . -s tests/smoke_test.gd -- <screenshot_dir> [waves]

var out_dir := "user://"
var waves_to_run := 3
var game: Game
var frame := 0
var shots := 0
var closeups := 0
var summoned := 0


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		out_dir = args[0]
	if args.size() > 1:
		waves_to_run = int(args[1])
	change_scene_to_file("res://scenes/game/game.tscn")
	process_frame.connect(_tick)


func _shot(name: String) -> void:
	shots += 1
	root.get_texture().get_image().save_png("%s/%02d_%s.png" % [out_dir, shots, name])


func _tick() -> void:
	frame += 1
	if frame == 5:
		game = current_scene as Game
		game.spawner.enemy_spawned.connect(func(e: Enemy) -> void: summoned += int(e.progress > 0.0))
		game.gold = 5000
		for spec in [["archer", Vector2i(2, 2)], ["cannon", Vector2i(6, 2)], ["mage", Vector2i(9, 3)],
				["ice", Vector2i(11, 3)], ["ballista", Vector2i(6, 5)], ["archer", Vector2i(11, 5)]]:
			var data: TowerData = load("res://data/towers/%s.tres" % spec[0])
			assert(game.build_tower(data, spec[1]) != null, "could not build %s" % spec[0])
		game.upgrade_tower(game.tower_at(Vector2i(9, 3)))
		game.upgrade_tower(game.tower_at(Vector2i(9, 3)))
		if waves_to_run > 3:  # a full run: max out a bigger defence
			for spec in [["mage", Vector2i(4, 3)], ["cannon", Vector2i(3, 4)], ["ballista", Vector2i(11, 1)]]:
				game.build_tower(load("res://data/towers/%s.tres" % spec[0]), spec[1])
			for tower in game.get_node("Towers").get_children():
				game.upgrade_tower(tower)
				game.upgrade_tower(tower)
		game.build.select_tower(game.tower_at(Vector2i(9, 3)))
	elif frame == 40:
		_shot("built")
		game.build.clear()
		game.build.select_plot(Vector2i(4, 3))
	elif frame == 60:
		_shot("build_panel")
		game.build.clear()
		game.start_next_wave()
		Engine.time_scale = 4.0
	if game and game.spawner.wave_index == game.spawner.wave_count() - 1 and frame % 60 == 0 and closeups < 3:
		for node in get_nodes_in_group(&"enemies"):  # close-up on a boss
			var enemy := node as Enemy
			if enemy.data.is_boss and enemy.progress > 8.0:
				game.camera_rig.setup(game.map.bounds(), enemy.global_position, 11.0)
				closeups += 1
				_shot("boss_closeup")
				break
	if frame > 60 and frame % 200 == 0:
		var enemies := get_nodes_in_group(&"enemies").size()
		print("frame %d: wave %d/%d running=%s enemies=%d gold=%d lives=%d" % [frame, game.spawner.wave_index + 1,
				game.spawner.wave_count(), game.spawner.wave_running, enemies, game.gold, game.lives])
		if enemies > 0 and shots < 6:
			_shot("combat")
		if not game.spawner.wave_running:
			if game.spawner.wave_index + 1 >= waves_to_run or game.over:
				_shot("end")
				print("RESULT: waves=%d lives=%d gold=%d over=%s summoned_minions=%d" % [game.spawner.wave_index + 1,
						game.lives, game.gold, game.over, summoned])
				quit()
			else:
				game.start_next_wave()
	if frame > 60000:
		print("TIMEOUT")
		quit(1)
