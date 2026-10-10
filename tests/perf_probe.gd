extends SceneTree
## Performance probe: a busy battle (12 towers, 40 walking enemies), averaged over a few seconds.
##   godot --path . --disable-vsync --resolution 1920x1080 -s tests/perf_probe.gd [-- toggle ...]
## Toggles switch one feature off to see what it costs: ssao, glow, msaa, outline, grade, shadows,
## sky, enemies (no enemies), towers (no towers), particles (no particles).
## Untyped on purpose (see smoke_test.gd).

var frame := 0
var game
var t_start := 0
var frames_counted := 0
var info := {}


func _init() -> void:
	process_frame.connect(_tick)


func _tick() -> void:
	frame += 1
	if frame == 1:
		Engine.max_fps = 0
		change_scene_to_file("res://scenes/game/game.tscn")
	elif frame == 5:
		game = current_scene
		var off := OS.get_cmdline_user_args()
		var env: Environment = game.get_node("WorldEnvironment").environment
		if "ssao" in off: env.ssao_enabled = false
		if "glow" in off: env.glow_enabled = false
		if "msaa" in off: root.msaa_3d = Viewport.MSAA_DISABLED
		if "smaa" in off:  # MSAA replaced by screen-space SMAA
			root.msaa_3d = Viewport.MSAA_DISABLED
			root.screen_space_aa = Viewport.SCREEN_SPACE_AA_SMAA
		if "fxaa" in off:
			root.msaa_3d = Viewport.MSAA_DISABLED
			root.screen_space_aa = Viewport.SCREEN_SPACE_AA_FXAA
		if "outline" in off: game.get_node("CameraRig/Camera3D/Outline").visible = false
		if "grade" in off: game.get_node("PostProcess").visible = false
		if "shadows" in off: game.get_node("Sun").shadow_enabled = false
		if "sky" in off: env.background_mode = Environment.BG_COLOR
		game.gold = 99999
		var plots = preload("res://tests/smoke_test.gd").ranked_plots(game.map, 7.0)
		var kinds := ["archer", "cannon", "mage", "ice", "ballista", "archer", "cannon", "mage", "ice", "archer", "mage", "cannon"]
		for i in (0 if "towers" in OS.get_cmdline_user_args() else kinds.size()):
			var t = game.build_tower(load("res://data/towers/%s.tres" % kinds[i]), plots[i])
			game.upgrade_tower(t)
		var ids := ["goblin", "orc", "troll", "wyvern"]
		for i in (0 if "enemies" in OS.get_cmdline_user_args() else 40):
			game.spawner.spawn(load("res://data/enemies/%s.tres" % ids[i % 4]), 2.0 + i * 1.3)
		for e in get_nodes_in_group(&"enemies"):
			e.max_hp = 1e9
			e.hp = 1e9
		game.over = true
	elif frame == 120:
		t_start = Time.get_ticks_usec()
	elif frame > 120 and frame <= 420:
		frames_counted += 1
		if frame == 300:
			for key in ["objects", "primitives", "draw_calls"]:
				var id = {"objects": RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME,
						"primitives": RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME,
						"draw_calls": RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME}[key]
				info[key] = RenderingServer.get_rendering_info(id)
	elif frame == 421:
		var seconds := (Time.get_ticks_usec() - t_start) / 1e6
		print("PERF: %.1f fps (%.2f ms/frame), %s" % [frames_counted / seconds, seconds * 1000.0 / frames_counted, info])
		quit()
