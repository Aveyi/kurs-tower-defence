extends SceneTree
## Level 2 two-portal check: routes per portal, the sealed portal sends nobody until its wave, then both
## portals get an equal share; the HUD announces the opening. Saves screenshots of the map and the opening.
##   godot --path . -s tests/portals_check.gd -- <screenshot_dir>
## Untyped on purpose (see smoke_test.gd).

var game
var out_dir := ""
var frame := 0
var failed := false


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	out_dir = args[0] if not args.is_empty() else "user://portals_check"
	DirAccess.make_dir_recursive_absolute(out_dir)
	process_frame.connect(_tick)


func _check(ok: bool, message: String) -> void:
	print(("OK    " if ok else "FAIL  ") + message)
	failed = failed or not ok


## How many of `n` handed-out routes start at each portal.
func _share(n: int) -> Array:
	var counts := [0, 0]
	for i in n:
		counts[game.map.route_portal[game.spawner._next_route()]] += 1
	return counts


func _tick() -> void:
	frame += 1
	if frame == 1:
		root.get_node("Session").record_results = false
		var level = load("res://data/levels/level_02.tres").duplicate()
		var waves := []
		for i in level.sealed_portal_wave + 2:  # tiny stand-in waves (the real ones come later)
			var wave = load("res://scripts/data/wave_data.gd").new()
			var group = load("res://scripts/data/spawn_group.gd").new()
			group.enemy = load("res://data/enemies/skeleton.tres")
			group.count = 1
			wave.groups.append(group)
			waves.append(wave)
		level.waves.assign(waves)
		var scene = load("res://scenes/game/game.tscn").instantiate()
		scene.level = level
		root.add_child(scene)
		current_scene = scene
		return
	if frame == 5:
		game = current_scene
		var map = game.map
		var per_portal := [0, 0]
		for p in map.route_portal:
			per_portal[p] += 1
		_check(map.portals.size() == 2, "portals: %d" % map.portals.size())
		_check(per_portal == [2, 2], "routes per portal: %s, lengths %s" % [per_portal,
				map.routes.map(func(c) -> String: return "%.0f m" % c.get_baked_length())])
		_check(map.portal_open == [true, false], "second portal sealed at the start")
		var before := _share(40)
		_check(before == [40, 0], "before it opens all enemies use the first portal: %s" % [before])
		var rect: Rect2 = map.bounds()
		game.camera_rig.setup(rect, Vector3(rect.get_center().x, 0, rect.get_center().y + 1.0), 34.0)
	if frame == 60:
		root.get_texture().get_image().save_png("%s/level2_overview.png" % out_dir)
		game.camera_rig.setup(game.map.bounds(), game.map.portals[1].global_position, 9.0)
		game.camera_rig._yaw = -PI / 2.0  # look at the arch from the road side (west)
	if frame == 90:
		root.get_texture().get_image().save_png("%s/portal_sealed.png" % out_dir)
		game.spawner.wave_index = game.level.sealed_portal_wave - 2
		game.start_next_wave()
		_check(not game.map.portal_open[1], "still sealed during wave %d" % (game.spawner.wave_index + 1))
		_check(game.spawner.portal_opens_next == 1, "warned one wave ahead (wave %d)" % (game.spawner.wave_index + 1))
		_check(game.map._vortices[1][0].visible, "the stirring portal already looks open (vortex shown)")
		game.spawner.wave_running = false
		game.start_next_wave()
		_check(game.map.portal_open[1] and game.spawner.opened_portal == 1,
				"opened with wave %d" % (game.spawner.wave_index + 1))
		game.spawner._portal_bag.clear()
		var after := _share(40)
		_check(after == [20, 20], "after it opens both portals get an equal share: %s" % [after])
	if frame == 215:
		root.get_texture().get_image().save_png("%s/portal_opened.png" % out_dir)
		var alerts: Array = [game.hud.boss_title.text] + game.hud._alert_queue.map(func(a) -> String: return a[0])
		_check("Второй портал пробуждается" in alerts and "Открылся второй портал!" in alerts,
				"HUD warns, then announces the opening: %s" % [alerts])
		print("RESULT: %s" % ("FAIL" if failed else "PASS"))
		quit(1 if failed else 0)
