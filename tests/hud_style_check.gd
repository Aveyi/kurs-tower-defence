extends SceneTree
## Screenshots of the HUD in a given style on the level 1 map: overview, build panel, tower panel,
## boss warning, pause menu and settings.
##   godot --path . -s tests/hud_style_check.gd -- <screenshot_dir> [style]   (style: haunted | kingdom)
## Untyped on purpose (see smoke_test.gd).

var game
var hud
var out_dir := ""
var style := &"haunted"
var frame := 0
var tower


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	out_dir = args[0] if not args.is_empty() else "user://hud_style"
	if args.size() > 1:
		style = StringName(args[1])
	DirAccess.make_dir_recursive_absolute(out_dir)
	process_frame.connect(_tick)


func _shot(name: String) -> void:
	root.get_texture().get_image().save_png("%s/%s_%s.png" % [out_dir, style, name])
	print("shot ", name)


func _tick() -> void:
	frame += 1
	if frame == 1:
		root.get_node("Session").record_results = false
		var scene = load("res://scenes/game/game.tscn").instantiate()
		var level = load("res://data/levels/level_01.tres").duplicate()
		level.hud_style = style
		scene.level = level
		root.add_child(scene)
		current_scene = scene
		return
	if frame == 5:
		game = current_scene
		hud = game.hud
		print("style ", style, " theme ", hud.get_node("Root").theme.resource_path)
	if frame == 60:
		_shot("1_overview")
		var plots = preload("res://tests/smoke_test.gd").ranked_plots(game.map, 7.0)
		game.camera_rig.setup(game.map.bounds(), game.map.cell_center(plots[0]), 16.0)
		game.build.select_plot(plots[0])
	if frame == 100:
		_shot("2_build_panel")
		var plots = preload("res://tests/smoke_test.gd").ranked_plots(game.map, 7.0)
		tower = game.build_tower(load("res://data/towers/mage.tres"), plots[0])
		game.build.select_tower(tower)
	if frame == 140:
		hud._set_upgrade_hover(true)
	if frame == 150:
		_shot("3_tower_panel")
		hud._set_upgrade_hover(false)
		game.build.clear()
		hud._show_boss_warning(PackedStringArray(["Каменный голем"]))
	if frame == 290:
		_shot("4_boss_warning")
		hud._toggle_pause()
	if frame == 330:
		_shot("5_pause")
		hud._open_settings()
	if frame == 360:
		_shot("6_settings")
		quit()
