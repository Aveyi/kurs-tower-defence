extends SceneTree
## Level 2 at night: screenshots of a fight (towers, new enemies, effects) close up and of the sky
## (moon, stars) toward the horizon. Checks that the night lighting was applied.
##   godot --path . -s tests/night_check.gd -- <screenshot_dir>
## Untyped on purpose (see smoke_test.gd).

var game
var out_dir := ""
var frame := 0
var failed := false


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	out_dir = args[0] if not args.is_empty() else "user://night_check"
	DirAccess.make_dir_recursive_absolute(out_dir)
	process_frame.connect(_tick)


func _check(ok: bool, message: String) -> void:
	print(("OK    " if ok else "FAIL  ") + message)
	failed = failed or not ok


func _tick() -> void:
	frame += 1
	if frame == 1:
		root.get_node("Session").record_results = false
		var scene = load("res://scenes/game/game.tscn").instantiate()
		scene.level = load("res://data/levels/level_02.tres")
		root.add_child(scene)
		current_scene = scene
		return
	if frame == 5:
		game = current_scene
		_check(game.get_node("WorldEnvironment").environment.fog_enabled, "fog on")
		_check(game.get_node("Sun").light_energy < 1.0, "moonlight")
		var lights: int = game.map.find_children("*", "OmniLight3D", false, false).size()
		_check(lights > 10, "%d point lights" % lights)
		game.gold = 100000
		var kinds := ["archer", "mage", "cannon", "ice", "ballista"]
		var plots = preload("res://tests/smoke_test.gd").ranked_plots(game.map, 7.0)
		for i in 6:
			var tower = game.build_tower(load("res://data/towers/%s.tres" % kinds[i % kinds.size()]), plots[i])
			for k in i % 3:
				game.upgrade_tower(tower)
		var ids := ["ghost_knight", "witch", "skeleton", "zombie", "skeleton", "gargoyle", "zombie", "skeleton"]
		for i in ids.size():
			var e = game.spawner.spawn(load("res://data/enemies/%s.tres" % ids[i]), 14.0 - i * 1.6, 0)
			e.max_hp *= 50.0
			e.hp = e.max_hp
	if frame == 120:
		var knight = game.get_node("Enemies").get_child(0)
		game.camera_rig.setup(game.map.bounds(), knight.global_position, 13.0)
	if frame == 200:
		root.get_texture().get_image().save_png("%s/night_fight.png" % out_dir)
		var rect: Rect2 = game.map.bounds()
		game.camera_rig.setup(rect, Vector3(rect.get_center().x, 0, rect.end.y), 30.0)
		game.camera_rig._pitch_offset = -20.0
		game.camera_rig._yaw = PI
	if frame == 260:
		root.get_texture().get_image().save_png("%s/night_sky.png" % out_dir)
		print("RESULT: %s" % ("FAIL" if failed else "PASS"))
		quit(1 if failed else 0)
