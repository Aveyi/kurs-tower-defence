extends Control
## Level select: a card per level with its preview, description and best result.
## Levels come from Session.LEVELS; entries without a file are shown as "in development".

const THEME := preload("res://assets/ui/theme.tres")
const BACKGROUND := preload("res://assets/ui/menu_bg.png")


func _ready() -> void:
	theme = THEME
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var bg := TextureRect.new()
	bg.texture = BACKGROUND
	bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bg.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.modulate = Color(0.3, 0.3, 0.36)
	add_child(bg)

	var root := VBoxContainer.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_theme_constant_override(&"separation", 24)
	root.offset_left = 80
	root.offset_right = -80
	root.offset_top = 60
	root.offset_bottom = -50
	add_child(root)
	var title := Label.new()
	title.text = "Выбор уровня"
	title.add_theme_font_size_override(&"font_size", 56)
	title.add_theme_color_override(&"font_color", Color(0.98, 0.84, 0.45))
	title.add_theme_constant_override(&"outline_size", 12)
	root.add_child(title)

	var cards := HBoxContainer.new()
	cards.add_theme_constant_override(&"separation", 32)
	cards.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(cards)
	for i in Session.LEVELS.size():
		cards.add_child(_card(i + 1, Session.LEVELS[i]))

	var back := Button.new()
	back.text = "Назад"
	back.custom_minimum_size = Vector2(260, 56)
	back.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	back.pressed.connect(func() -> void: get_tree().change_scene_to_file("res://scenes/ui/main_menu.tscn"))
	root.add_child(back)
	Audio.play_music(&"menu")
	Audio.wire_buttons(self)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(&"pause"):
		get_tree().change_scene_to_file("res://scenes/ui/main_menu.tscn")


func _card(number: int, entry: Dictionary) -> Control:
	if entry.path.is_empty():
		return _locked_card(number)
	var level: LevelData = load(entry.path)
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(520, 0)
	var box := VBoxContainer.new()
	box.add_theme_constant_override(&"separation", 12)
	panel.add_child(box)

	var preview := TextureRect.new()
	preview.custom_minimum_size = Vector2(480, 270)
	preview.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	preview.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	preview.texture = level.preview if level.preview else BACKGROUND
	box.add_child(preview)

	var name := Label.new()
	name.text = "%d. %s" % [number, level.display_name]
	name.add_theme_font_size_override(&"font_size", 30)
	box.add_child(name)

	var description := Label.new()
	description.text = level.description
	description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	description.custom_minimum_size = Vector2(480, 0)
	description.add_theme_font_size_override(&"font_size", 18)
	description.modulate = Color(1, 1, 1, 0.85)
	box.add_child(description)

	var best := Session.best_result(level.id)
	var stars := Session.stars(best)
	var result := "ещё не пройден"
	if not best.is_empty():
		result = "%s %s, жизней %d/%d" % ["★".repeat(stars) + "☆".repeat(3 - stars),
				"победа" if best.victory else "поражение", best.lives, best.max_lives]
	var info := Label.new()
	info.text = "Волн: %d   •   Лучший результат: %s" % [level.waves.size(), result]
	info.add_theme_font_size_override(&"font_size", 19)
	info.add_theme_color_override(&"font_color", Color(0.85, 0.72, 0.45))
	box.add_child(info)

	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	box.add_child(spacer)

	var play := Button.new()
	play.text = "Играть"
	play.custom_minimum_size = Vector2(0, 56)
	play.add_theme_font_size_override(&"font_size", 24)
	play.pressed.connect(func() -> void:
		Session.level = level
		get_tree().change_scene_to_file("res://scenes/game/game.tscn"))
	box.add_child(play)
	return panel


## A level still in development: a black card with a big question mark.
func _locked_card(number: int) -> Control:
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(520, 0)
	var style: StyleBoxFlat = THEME.get_stylebox(&"panel", &"PanelContainer").duplicate()
	style.bg_color = Color(0.02, 0.02, 0.02, 0.97)
	style.border_color = Color(0.36, 0.32, 0.26)
	panel.add_theme_stylebox_override(&"panel", style)
	var box := VBoxContainer.new()
	box.alignment = BoxContainer.ALIGNMENT_CENTER
	box.add_theme_constant_override(&"separation", 18)
	panel.add_child(box)
	var mark := Label.new()
	mark.text = "?"
	mark.add_theme_font_size_override(&"font_size", 220)
	mark.add_theme_color_override(&"font_color", Color(0.45, 0.42, 0.38))
	mark.add_theme_constant_override(&"outline_size", 0)
	mark.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(mark)
	var caption := Label.new()
	caption.text = "Уровень %d — в разработке" % number
	caption.add_theme_font_size_override(&"font_size", 28)
	caption.add_theme_color_override(&"font_color", Color(0.6, 0.56, 0.5))
	caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(caption)
	return panel
