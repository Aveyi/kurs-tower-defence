extends SceneTree
## Renders a level's card picture for the level select screen: the map with a few towers and enemies on
## the road, the HUD hidden.
##   godot --path . --resolution 1600x900 -s tools/render_preview.gd -- <level.tres> <out.png> [enemy ids...]
## Untyped on purpose (see tests/smoke_test.gd).

var game
var frame := 0
var args := []


func _init() -> void:
	args = OS.get_cmdline_user_args()
	process_frame.connect(_tick)


func _tick() -> void:
	frame += 1
	if frame == 1:
		root.get_node("Session").record_results = false
		var scene = load("res://scenes/game/game.tscn").instantiate()
		scene.level = load(args[0])
		root.add_child(scene)
		current_scene = scene
		return
	if frame == 5:
		game = current_scene
		game.hud.visible = false
		game.gold = 100000
		for i in game.map.portals.size():
			game.map.open_portal(i)
		var kinds := ["archer", "mage", "cannon", "ice", "ballista", "mage", "archer"]
		var plots = preload("res://tests/smoke_test.gd").ranked_plots(game.map, 7.0)
		for i in mini(kinds.size(), plots.size()):
			var tower = game.build_tower(load("res://data/towers/%s.tres" % kinds[i]), plots[i])
			for k in (i % 3):
				game.upgrade_tower(tower)
		var ids: Array = args.slice(2) if args.size() > 2 else ["goblin", "orc", "troll"]
		for r in game.map.routes.size():
			for i in ids.size():
				var e = game.spawner.spawn(load("res://data/enemies/%s.tres" % ids[i]), 8.0 + i * 3.5 + r * 2.0, r)
				e.max_hp *= 100.0
				e.hp = e.max_hp
		var rect: Rect2 = game.map.bounds()
		game.camera_rig.setup(rect, Vector3(rect.get_center().x, 0, rect.get_center().y + 1.5), 30.0)
	if frame == 150:
		root.get_texture().get_image().save_png(args[1])
		print("saved ", args[1])
		quit()
