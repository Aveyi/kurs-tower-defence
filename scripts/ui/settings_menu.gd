class_name SettingsMenu
extends Control
## Settings screen: display, graphics and sound. Opened from the main menu and the pause menu;
## works while the game is paused. Every change is applied and saved at once.

signal closed

const THEME := preload("res://assets/ui/theme.tres")
const PRESET_NAMES := {"low": "Низкое", "medium": "Среднее", "high": "Высокое", "ultra": "Ультра"}

var _grid: GridContainer
var _controls := {}  # option key -> Control
var _updating := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	theme = THEME
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.55)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(760, 0)
	center.add_child(panel)
	var box := VBoxContainer.new()
	box.add_theme_constant_override(&"separation", 14)
	panel.add_child(box)
	box.add_child(_title("Настройки", 40))

	_grid = GridContainer.new()
	_grid.columns = 2
	_grid.add_theme_constant_override(&"h_separation", 28)
	_grid.add_theme_constant_override(&"v_separation", 10)
	box.add_child(_grid)

	_section("Экран")
	_option("window_mode", "Режим окна", ["В окне", "Полный экран"])
	_check("vsync", "Вертикальная синхронизация")
	_slider("render_scale", "Разрешение 3D", 0.5, 1.0, 0.05, func(v: float) -> String: return "%d%%" % roundi(v * 100))

	_section("Графика")
	var presets := OptionButton.new()
	presets.add_item("Выбрать…")
	for key in PRESET_NAMES:
		presets.add_item(PRESET_NAMES[key])
	presets.item_selected.connect(func(index: int) -> void:
		if index > 0:
			Settings.apply_preset(PRESET_NAMES.keys()[index - 1])
			_refresh()
		presets.select(0))
	_row("Готовый профиль", presets)
	_option("antialiasing", "Сглаживание", ["Выкл.", "FXAA", "SMAA", "MSAA 2x", "MSAA 4x"])
	_option("shadows", "Тени", ["Выкл.", "Низкие", "Высокие"])
	_check("ssao", "Затенение в углах (SSAO)")
	_check("bloom", "Свечение (bloom)")
	_check("outlines", "Контурные линии")

	_section("Звук")
	for bus in [["Music", "Музыка"], ["SFX", "Звуки"]]:
		var slider := HSlider.new()
		slider.max_value = 1.0
		slider.step = 0.05
		slider.custom_minimum_size = Vector2(280, 32)
		slider.value = Audio.get_volume(bus[0])
		slider.value_changed.connect(func(v: float) -> void: Audio.set_volume(bus[0], v))
		_row(bus[1], slider)

	var back := Button.new()
	back.text = "Назад"
	back.custom_minimum_size = Vector2(0, 52)
	back.pressed.connect(close)
	box.add_child(back)
	_refresh()
	Audio.wire_buttons(self)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(&"pause"):
		close()
		get_viewport().set_input_as_handled()


func close() -> void:
	closed.emit()
	queue_free()


func _refresh() -> void:
	_updating = true
	for key in _controls:
		var control: Control = _controls[key]
		var value = Settings.get(key)
		if control is OptionButton:
			control.select(int(value))
		elif control is CheckButton:
			control.button_pressed = value
		elif control is HSlider:
			control.value = value
	_updating = false


# --- builders ------------------------------------------------------------------------------
func _title(text: String, size: int) -> Label:
	var label := Label.new()
	label.text = text
	label.theme_type_variation = &"TitleLabel"
	label.add_theme_font_size_override(&"font_size", size)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return label


func _section(text: String) -> void:
	var label := Label.new()
	label.text = text
	label.theme_type_variation = &"TitleLabel"
	label.add_theme_font_size_override(&"font_size", 28)
	_grid.add_child(label)
	_grid.add_child(Control.new())


func _row(text: String, control: Control) -> void:
	var label := Label.new()
	label.text = text
	_grid.add_child(label)
	control.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	control.focus_mode = Control.FOCUS_NONE
	_grid.add_child(control)


func _option(key: String, text: String, items: Array) -> void:
	var option := OptionButton.new()
	for item in items:
		option.add_item(item)
	option.item_selected.connect(func(index: int) -> void:
		if not _updating:
			Settings.set_option(key, index))
	_controls[key] = option
	_row(text, option)


func _check(key: String, text: String) -> void:
	var check := CheckButton.new()
	check.toggled.connect(func(on: bool) -> void:
		if not _updating:
			Settings.set_option(key, on))
	_controls[key] = check
	_row(text, check)


func _slider(key: String, text: String, from: float, to: float, step: float, format: Callable) -> void:
	var box := HBoxContainer.new()
	var slider := HSlider.new()
	slider.min_value = from
	slider.max_value = to
	slider.step = step
	slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	slider.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	slider.custom_minimum_size = Vector2(200, 32)
	var value_label := Label.new()
	value_label.custom_minimum_size = Vector2(70, 0)
	slider.value_changed.connect(func(v: float) -> void:
		value_label.text = format.call(v)
		if not _updating:
			Settings.set_option(key, v))
	value_label.text = format.call(slider.value)
	box.add_child(slider)
	box.add_child(value_label)
	_controls[key] = slider
	_row(text, box)
