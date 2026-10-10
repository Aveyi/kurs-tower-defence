extends SceneTree
## Prints a fingerprint of a built map: every MultiMesh batch with its instance count and a checksum of
## the instance positions, plus routes. Used to prove a refactor did not change a level.
##   godot --path . --headless -s tests/map_dump.gd [-- res://data/levels/level_01.tres]
## Untyped on purpose (see smoke_test.gd).

var frame := 0


func _init() -> void:
	process_frame.connect(_tick)


func _tick() -> void:
	frame += 1
	if frame == 1:
		root.get_node("Session").record_results = false
		var scene = load("res://scenes/game/game.tscn").instantiate()
		var args := OS.get_cmdline_user_args()
		if not args.is_empty():
			scene.level = load(args[0])
		root.add_child(scene)
		current_scene = scene
	elif frame == 3:
		var map = current_scene.map
		var lines := []
		for node in map.get_children():
			if node is MultiMeshInstance3D:
				var mm: MultiMesh = node.multimesh
				var sum := Vector3.ZERO
				for i in mm.instance_count:
					var t := mm.get_instance_transform(i)
					sum += t.origin + t.basis.x * 0.37 + t.basis.z * 0.11
				lines.append("%s %d %.3f %.3f %.3f" % [node.name, mm.instance_count, sum.x, sum.y, sum.z])
		lines.sort()
		for line in lines:
			print("BATCH ", line)
		print("ROUTES ", map.routes.size(), " ", map.routes.map(func(c) -> String: return "%.2f" % c.get_baked_length()))
		quit()
