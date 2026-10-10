extends SceneTree
## Ghost knight check: archers and mages on every plot shoot a ghost knight walking the route. Checks the
## intangible windows (length and spacing), that it takes no damage or slow while intangible (shots pass
## through it), that it does take damage while solid, and that it dies normally. Saves screenshots.
##   godot --path . -s tests/phase_check.gd -- <screenshot_dir>
## Untyped on purpose (see smoke_test.gd).

var game
var knight
var out_dir := ""
var frame := 0
var failed := false
var start_msec := 0
var was_intangible := false
var changed_msec := 0
var phases := []  # [intangible?, seconds] of every finished window
var hp_at_change := 0.0
var passes := 0
var seen := {}
var shots := 0


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	out_dir = args[0] if not args.is_empty() else "user://phase_check"
	DirAccess.make_dir_recursive_absolute(out_dir)
	process_frame.connect(_tick)


func _check(ok: bool, message: String) -> void:
	print(("OK    " if ok else "FAIL  ") + message)
	failed = failed or not ok


func _now() -> float:
	return (Time.get_ticks_msec() - start_msec) / 1000.0


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
		var kinds := [load("res://data/towers/archer.tres"), load("res://data/towers/mage.tres")]
		var i := 0
		for row in game.map.size.y:
			for col in game.map.size.x:
				if game.build_tower(kinds[i % 2], Vector2i(col, row)):
					i += 1
		knight = game.spawner.spawn(load("res://data/enemies/ghost_knight.tres"), 1.0, 0)
		knight.max_hp = 1e6
		knight.hp = 1e6
		start_msec = Time.get_ticks_msec()
		changed_msec = start_msec
		hp_at_change = knight.hp
		return
	if knight == null or not knight.alive:
		return
	game.camera_rig.setup(game.map.bounds(), knight.global_position, 12.0)
	_count_passes()
	if knight.intangible != was_intangible:
		var seconds := (Time.get_ticks_msec() - changed_msec) / 1000.0
		phases.append([was_intangible, seconds, hp_at_change - knight.hp])
		was_intangible = knight.intangible
		changed_msec = Time.get_ticks_msec()
		hp_at_change = knight.hp
		if knight.intangible and phases.size() == 3:
			_probe_intangible()
		if not knight.intangible and phases.size() == 4:
			_probe_solid()
	if knight.intangible and phases.size() == 3 and Time.get_ticks_msec() - changed_msec > 500 \
			and not seen.has("shot"):
		seen["shot"] = true
		root.get_texture().get_image().save_png("%s/ghost_phased.png" % out_dir)
	if not knight.intangible and phases.size() == 4 and Time.get_ticks_msec() - changed_msec > 1500 \
			and not seen.has("shot2"):
		seen["shot2"] = true
		root.get_texture().get_image().save_png("%s/ghost_solid.png" % out_dir)
	if phases.size() >= 8:
		_report()


## Projectiles flying on after passing through the knight.
func _count_passes() -> void:
	for p in game.get_node("Projectiles").get_children():
		if p.get("_pass_left") != null:
			if not seen.has(p):
				seen[p] = false
				shots += 1
			if p._pass_left >= 0.0 and not seen[p]:
				seen[p] = true
				passes += 1


func _probe_intangible() -> void:
	var hp: float = knight.hp
	knight.take_damage(500.0)
	knight.apply_slow(0.5, 2.0)
	_check(knight.hp == hp and knight._slow == 1.0, "intangible: direct damage and slow are ignored")


func _probe_solid() -> void:
	var hp: float = knight.hp
	knight.take_damage(500.0)
	_check(knight.hp == hp - 500.0, "solid: direct damage lands")


func _report() -> void:
	for p in phases.slice(1):  # the first solid window is half an interval long
		print("      %-10s %.2f s, damage taken %.0f" % ["intangible" if p[0] else "solid", p[1], p[2]])
		if p[0]:
			_check(absf(p[1] - knight.data.phase_duration) < 0.15 and p[2] <= 1.0,
					"intangible window ~%.1f s without damage" % knight.data.phase_duration)
		else:
			_check(absf(p[1] - knight.data.phase_interval) < 0.25, "solid window ~%.1f s" % knight.data.phase_interval)
	_check(phases.slice(1).any(func(p) -> bool: return not p[0] and p[2] > 0.0), "towers hurt it while solid")
	_check(passes > 0, "%d of %d shots passed through it" % [passes, shots])
	knight.intangible = false
	knight.take_damage(1e9)
	_check(not knight.alive, "the ghost knight dies")
	print("RESULT: %s" % ("FAIL" if failed else "PASS"))
	quit(1 if failed else 0)
