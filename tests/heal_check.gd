extends SceneTree
## Level 2 enemies check: spawns skeleton, zombie, witch, gargoyle and golem close together on one route,
## wounds everyone but the witch and checks that her spell heals them; then kills them all (Die animations)
## and saves screenshots of the group and of the heal.
##   godot --path . -s tests/heal_check.gd -- <screenshot_dir>
## Untyped on purpose (see smoke_test.gd).

const IDS := ["golem", "zombie", "witch", "skeleton", "gargoyle", "zombie"]

var game
var out_dir := ""
var frame := 0
var enemies := []
var witch
var wounded := {}  # enemy -> hp right after wounding
var heal_frame := -1
var failed := false


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	out_dir = args[0] if not args.is_empty() else "user://heal_check"
	DirAccess.make_dir_recursive_absolute(out_dir)
	process_frame.connect(_tick)


func _shot(name: String) -> void:
	root.get_texture().get_image().save_png("%s/%s.png" % [out_dir, name])


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
		for i in IDS.size():
			var data = load("res://data/enemies/%s.tres" % IDS[i])
			var enemy = game.spawner.spawn(data, 14.0 - i * 1.3, 0)
			enemies.append(enemy)
			if IDS[i] == "witch":
				witch = enemy
		var anchor = enemies[2].global_position
		game.camera_rig.setup(game.map.bounds(), anchor, 9.0)
		return
	if frame == 8:
		for enemy in enemies:
			var anims = enemy._anim.get_animation_list()
			_check(anims.has(enemy._move_anim) and anims.has(&"Hit") and anims.has(&"Die"),
					"%s animations: %s" % [enemy.data.id, ", ".join(anims)])
		_check(witch._anim.has_animation(&"Cast"), "witch has Cast")
		for enemy in enemies:
			if enemy != witch:
				enemy.take_damage(enemy.max_hp * 0.5)
				wounded[enemy] = enemy.hp
		return
	if frame == 40:
		_shot("01_group")
	if witch == null or frame < 9:
		return
	if heal_frame < 0 and witch._cast_left > 0.0 and witch._cast_left <= 0.75:
		heal_frame = frame
		var any_healed := false
		for enemy in wounded:
			var near: bool = enemy.global_position.distance_to(witch.global_position) <= witch.data.heal_radius
			var healed: bool = enemy.hp > wounded[enemy] + 1.0
			any_healed = any_healed or healed
			print("      %-9s dist %.1f m  hp %.0f -> %.0f / %.0f" % [enemy.data.id,
					enemy.global_position.distance_to(witch.global_position), wounded[enemy], enemy.hp, enemy.max_hp])
			_check(healed == near, "%s healed only if within %.0f m" % [enemy.data.id, witch.data.heal_radius])
		_check(any_healed, "the witch healed someone")
		_check(witch.hp == witch.max_hp, "the witch did not heal herself")
	if heal_frame > 0 and frame == heal_frame + 6:
		_shot("02_heal")
	if heal_frame > 0 and frame == heal_frame + 60:
		for enemy in enemies:
			enemy.take_damage(1e9)
	if heal_frame > 0 and frame == heal_frame + 100:
		_shot("03_dying")
	if heal_frame > 0 and frame == heal_frame + 260:
		_check(game.get_tree().get_nodes_in_group(&"enemies").is_empty(), "all enemies died")
		print("RESULT: %s" % ("FAIL" if failed else "PASS"))
		quit(1 if failed else 0)
	if frame > 2000:
		_check(false, "the witch never cast a heal")
		quit(1)
