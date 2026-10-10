extends SceneTree
## Prints the routes of the current level: count and lengths.
##   godot --path . --headless -s tests/route_check.gd
## Untyped on purpose (see smoke_test.gd).

var frame := 0


func _init() -> void:
	process_frame.connect(_tick)


func _tick() -> void:
	frame += 1
	if frame == 1:
		change_scene_to_file("res://scenes/game/game.tscn")
	elif frame == 5:
		if current_scene == null or not "map" in current_scene:
			push_error("game scene failed to load")
			quit(1)
			return
		var map = current_scene.map
		print("ROUTES: %d" % map.routes.size())
		for i in map.routes.size():
			print("  route %d: %.1f m" % [i, map.routes[i].get_baked_length()])
		quit()
