extends Control
## Title screen.


func _ready() -> void:
	get_tree().paused = false
	Engine.time_scale = 1.0
	%PlayButton.pressed.connect(func() -> void: get_tree().change_scene_to_file("res://scenes/game/game.tscn"))
	%QuitButton.pressed.connect(func() -> void: get_tree().quit())
	%PlayButton.grab_focus()
