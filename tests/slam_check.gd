extends SceneTree
## Golem ground slam check: towers on every plot, a golem walks by and slams; only towers within
## slam_radius get stunned, stunned towers do not shoot, and they recover after slam_stun seconds.
##   godot --path . -s tests/slam_check.gd -- <screenshot_dir>
## Untyped on purpose (see smoke_test.gd).

var game
var golem
var towers := []
var out_dir := ""
var frame := 0
var stun_msec := -1
var stun_frame := -1
var stunned := []
var cooldowns := {}
var failed := false


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	out_dir = args[0] if not args.is_empty() else "user://slam_check"
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
		root.add_child(scene)
		current_scene = scene
		return
	if frame == 5:
		game = current_scene
		game.gold = 100000
		var archer = load("res://data/towers/archer.tres")
		for row in game.map.size.y:
			for col in game.map.size.x:
				var tower = game.build_tower(archer, Vector2i(col, row))
				if tower:
					towers.append(tower)
		# start the golem 2 m before the point of route 0 closest to the first tower
		var route = game.map.routes[0]
		var closest: float = route.get_closest_offset(route.get_closest_point(towers[0].position))
		golem = game.spawner.spawn(load("res://data/enemies/golem.tres"), maxf(closest - 2.0, 0.5), 0)
		golem.hp = 1e9
		golem.max_hp = 1e9
		golem._slam_left = 1.0
		return
	if golem == null:
		return
	if frame == 6:
		game.camera_rig.setup(game.map.bounds(), golem.global_position, 15.0)
	if stun_msec < 0 and towers.any(func(t) -> bool: return t.is_stunned()):
		stun_msec = Time.get_ticks_msec()
		stun_frame = frame
		var radius: float = golem.data.slam_radius
		for tower in towers:
			var d: Vector3 = tower.global_position - golem.global_position
			var dist := Vector2(d.x, d.z).length()
			if tower.is_stunned():
				stunned.append(tower)
				cooldowns[tower] = tower._cooldown
			_check(tower.is_stunned() == (dist <= radius), "tower %s at %.1f m: stunned=%s" % [tower.cell, dist,
					tower.is_stunned()])
		_check(not stunned.is_empty(), "%d of %d towers stunned" % [stunned.size(), towers.size()])
	if stun_frame > 0 and frame == stun_frame + 25:
		root.get_texture().get_image().save_png("%s/slam_ring.png" % out_dir)
		game.camera_rig.setup(game.map.bounds(), stunned[0].global_position + Vector3(0, 1.5, 0), 9.0)
	if stun_frame > 0 and frame == stun_frame + 50:
		root.get_texture().get_image().save_png("%s/slam_stunned_tower.png" % out_dir)
	if stun_msec > 0 and Time.get_ticks_msec() - stun_msec > 1500 and not cooldowns.is_empty():
		for tower in stunned:
			_check(tower.is_stunned() and tower._cooldown == cooldowns[tower] and tower._anim.speed_scale == 0.0,
					"tower %s frozen 1.5 s into the stun" % [tower.cell])
		cooldowns.clear()
	if stun_msec > 0 and Time.get_ticks_msec() - stun_msec > (golem.data.slam_stun + 0.4) * 1000.0:
		for tower in stunned:
			_check(not tower.is_stunned() and tower._anim.speed_scale == 1.0, "tower %s recovered" % [tower.cell])
		print("RESULT: %s" % ("FAIL" if failed else "PASS"))
		quit(1 if failed else 0)
	if frame > 3000:
		_check(false, "the golem never slammed")
		quit(1)
