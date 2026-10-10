extends SceneTree
## Builds a small test map with the haunted MapTheme (a road running through a fenced cemetery, landmarks,
## forest, rocks, plots) and saves screenshots; prints the batches and checks fences, gates and routes.
##   godot --path . -s tests/haunted_map_check.gd -- <screenshot_dir>
## Untyped on purpose (see smoke_test.gd).

const LAYOUT := [
	"TTTTTTTTTTTTTTTT",
	"T..R.GGGGG..r..T",
	"TS###########.TT",
	"T.P..GGGGG.P#..T",
	"T...R.......#R.T",
	"TT..P.....RCCC.T",
	"TT....r....CCC.T",
	"TTTTTTTTTTTTTTTT",
]

var game
var out_dir := ""
var frame := 0
var failed := false


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	out_dir = args[0] if not args.is_empty() else "user://haunted_map"
	DirAccess.make_dir_recursive_absolute(out_dir)
	process_frame.connect(_tick)


func _check(ok: bool, message: String) -> void:
	print(("OK    " if ok else "FAIL  ") + message)
	failed = failed or not ok


func _tick() -> void:
	frame += 1
	if frame == 1:
		root.get_node("Session").record_results = false
		var level = load("res://scripts/data/level_data.gd").new()
		level.layout = PackedStringArray(LAYOUT)
		level.map_theme = load("res://data/themes/haunted.tres")
		level.hud_style = &"haunted"
		level.music = &"battle_haunted"
		level.decor_seed = 7
		var scene = load("res://scenes/game/game.tscn").instantiate()
		scene.level = level
		root.add_child(scene)
		current_scene = scene
		return
	if frame == 5:
		game = current_scene
		var counts := {}
		for node in game.map.get_children():
			if node is MultiMeshInstance3D:
				counts[String(node.name)] = node.multimesh.instance_count
		var names := counts.keys()
		names.sort()
		for n in names:
			print("BATCH %s %d" % [n, counts[n]])
		# 5 + 5 graves cells: border edges = 2 x (5 top + 5 bottom) + 2 x 2 sides, minus the 2 x 5 edges
		# shared with the road lane between them -> 24 fence segments; the lane has a gate at both ends
		_check(counts.get("prop_cemetery_fence", 0) == 24, "fence segments: %d" % counts.get("prop_cemetery_fence", 0))
		_check(counts.get("prop_cemetery_gate", 0) == 2, "gates: %d" % counts.get("prop_cemetery_gate", 0))
		_check(not counts.keys().any(func(k) -> bool: return k.begins_with("tile_") and not k.begins_with("tile_haunt_")),
				"only haunted tiles")
		_check(game.map.routes.size() == 1, "routes: %d" % game.map.routes.size())
		var landmarks := counts.keys().filter(func(k) -> bool: return k in ["prop_ruin_columns", "prop_ruin_arch",
				"prop_ruin_wall", "prop_ritual_stones", "prop_crypt", "prop_obelisk", "prop_witch_cauldron",
				"prop_grave_open"])
		_check(landmarks.size() == 4, "4 different landmarks: %s" % ", ".join(landmarks))
		var rect: Rect2 = game.map.bounds()
		game.camera_rig.setup(rect, Vector3(rect.get_center().x, 0, rect.get_center().y + 1.0), 30.0)
	if frame == 60:
		root.get_texture().get_image().save_png("%s/map_overview.png" % out_dir)
		game.camera_rig.setup(game.map.bounds(), game.map.cell_center(Vector2i(5, 2)), 10.0)
	if frame == 100:
		root.get_texture().get_image().save_png("%s/map_gate.png" % out_dir)
		game.camera_rig.setup(game.map.bounds(), game.map.cell_center(Vector2i(11, 4)), 11.0)
	if frame == 140:
		root.get_texture().get_image().save_png("%s/map_castle_side.png" % out_dir)
		print("RESULT: %s" % ("FAIL" if failed else "PASS"))
		quit(1 if failed else 0)
