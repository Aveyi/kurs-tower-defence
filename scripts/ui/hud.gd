class_name Hud
extends CanvasLayer
## In-game interface: resource bar, build and tower panels, wave banner, pause menu and end screen.

var game: Game
var _tower_buttons := {}  # TowerData -> Button
var _banner_tween: Tween

@onready var gold_label: Label = %GoldLabel
@onready var lives_label: Label = %LivesLabel
@onready var wave_label: Label = %WaveLabel
@onready var next_wave_button: Button = %NextWaveButton
@onready var speed_button: Button = %SpeedButton
@onready var pause_button: Button = %PauseButton
@onready var build_panel: Control = %BuildPanel
@onready var tower_buttons: HBoxContainer = %TowerButtons
@onready var tower_panel: Control = %TowerPanel
@onready var tower_icon: TextureRect = %TowerIcon
@onready var tower_name: Label = %TowerName
@onready var tower_level: Label = %TowerLevel
@onready var tower_stats: Label = %TowerStats
@onready var upgrade_button: Button = %UpgradeButton
@onready var sell_button: Button = %SellButton
@onready var banner: Label = %Banner
@onready var pause_menu: Control = %PauseMenu
@onready var end_screen: Control = %EndScreen
@onready var end_title: Label = %EndTitle
@onready var end_info: Label = %EndInfo


func _ready() -> void:
	build_panel.hide()
	tower_panel.hide()
	pause_menu.hide()
	end_screen.hide()
	banner.modulate.a = 0.0
	next_wave_button.pressed.connect(func() -> void: game.start_next_wave())
	speed_button.pressed.connect(_toggle_speed)
	pause_button.pressed.connect(_toggle_pause)
	upgrade_button.pressed.connect(_on_upgrade_pressed)
	sell_button.pressed.connect(_on_sell_pressed)
	%ResumeButton.pressed.connect(_toggle_pause)
	%RestartButton.pressed.connect(func() -> void: game.restart())
	%MenuButton.pressed.connect(func() -> void: game.to_menu())
	%EndRestartButton.pressed.connect(func() -> void: game.restart())
	%EndMenuButton.pressed.connect(func() -> void: game.to_menu())
	%SettingsButton.pressed.connect(_open_settings)


func setup(owner_game: Game) -> void:
	game = owner_game
	game.gold_changed.connect(_on_gold_changed)
	game.lives_changed.connect(_on_lives_changed)
	game.wave_started.connect(_on_wave_started)
	game.countdown_changed.connect(_on_countdown_changed)
	game.game_over.connect(_on_game_over)
	game.build.plot_selected.connect(_on_plot_selected)
	game.build.tower_selected.connect(_on_tower_selected)
	game.build.selection_cleared.connect(_on_selection_cleared)
	for data in game.tower_types:
		_add_tower_button(data)
	Audio.wire_buttons(self)
	_on_gold_changed(game.gold)
	lives_label.text = str(game.lives)
	wave_label.text = "Волна 0 / %d" % game.spawner.wave_count()
	_show_banner("Стройте башни на каменных площадках", 3.5)


func _unhandled_input(event: InputEvent) -> void:
	if game == null or game.over:
		return
	if event.is_action_pressed(&"pause"):
		if pause_menu.visible == false and get_tree().paused:
			return  # the settings screen handles Esc itself
		if not get_tree().paused and game.build.selected_cell != BuildController.NONE:
			game.build.clear()
		else:
			_toggle_pause()
		get_viewport().set_input_as_handled()
	elif get_tree().paused:
		return
	elif event.is_action_pressed(&"next_wave"):
		game.start_next_wave()
	elif event.is_action_pressed(&"toggle_speed"):
		_toggle_speed()


# --- top bar -------------------------------------------------------------------------------
func _on_gold_changed(gold: int) -> void:
	gold_label.text = str(gold)
	for data: TowerData in _tower_buttons:  # unaffordable towers look dim but still answer a click
		_tower_buttons[data].modulate = Color.WHITE if gold >= data.levels[0].cost else Color(0.6, 0.55, 0.55)
	if tower_panel.visible and game.build.selected_tower:
		_refresh_tower_panel(game.build.selected_tower)


func _on_lives_changed(lives: int) -> void:
	lives_label.text = str(lives)
	var tween := create_tween()
	lives_label.modulate = Color(1.0, 0.3, 0.25)
	tween.tween_property(lives_label, "modulate", Color.WHITE, 0.6)


func _on_wave_started(index: int, total: int) -> void:
	wave_label.text = "Волна %d / %d" % [index + 1, total]
	_show_banner("Волна %d" % (index + 1) if index + 1 < total else "Последняя волна!")


func _on_countdown_changed(seconds: float) -> void:
	if seconds >= 0.0:
		next_wave_button.disabled = false
		next_wave_button.text = "Начать волну (%d)" % ceili(seconds)
	else:
		next_wave_button.disabled = true
		next_wave_button.text = "Идёт волна…"


func _toggle_speed() -> void:
	game.set_fast(not game.fast)
	speed_button.text = "Скорость ×2" if game.fast else "Скорость ×1"


func _open_settings() -> void:
	var menu := SettingsMenu.new()
	pause_menu.hide()
	menu.closed.connect(func() -> void: pause_menu.show())
	$Root.add_child(menu)


func _toggle_pause() -> void:
	get_tree().paused = not get_tree().paused
	pause_menu.visible = get_tree().paused


# --- build panel ---------------------------------------------------------------------------
func _add_tower_button(data: TowerData) -> void:
	var button := Button.new()
	button.icon = data.icon
	button.expand_icon = true
	button.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	button.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP
	button.text = "%s\n%d" % [data.display_name, data.levels[0].cost]
	button.custom_minimum_size = Vector2(136, 176)
	button.focus_mode = Control.FOCUS_NONE
	button.tooltip_text = "%s\n\n%s\nЦели: %s" % [data.display_name, data.description, data.targets_text()]
	button.pressed.connect(_on_build_pressed.bind(data))
	button.mouse_entered.connect(func() -> void: game.build.show_range(data.levels[0].attack_range))
	button.mouse_exited.connect(func() -> void: game.build.show_range(0.0))
	tower_buttons.add_child(button)
	_tower_buttons[data] = button


func _on_build_pressed(data: TowerData) -> void:
	var tower := game.build_tower(data, game.build.selected_cell)
	if tower:
		game.build.select_tower(tower)
	elif game.gold < data.levels[0].cost:
		_not_enough_gold()


func _not_enough_gold() -> void:
	Audio.play(&"error")
	var tween := create_tween()
	gold_label.modulate = Color(1.0, 0.3, 0.25)
	tween.tween_property(gold_label, "modulate", Color.WHITE, 0.6)


func _on_plot_selected(_cell: Vector2i) -> void:
	tower_panel.hide()
	build_panel.show()


func _on_selection_cleared() -> void:
	build_panel.hide()
	tower_panel.hide()


# --- tower panel ---------------------------------------------------------------------------
func _on_tower_selected(tower: Tower) -> void:
	build_panel.hide()
	_refresh_tower_panel(tower)
	tower_panel.show()


func _refresh_tower_panel(tower: Tower) -> void:
	var s := tower.stats()
	tower_icon.texture = tower.data.icon
	tower_name.text = tower.data.display_name
	tower_level.text = "Уровень %d из %d" % [tower.level + 1, tower.data.levels.size()]
	var lines := PackedStringArray([
		"Урон: %s" % _num(s.damage),
		"Дальность: %s м" % _num(s.attack_range),
		"Выстрелов в секунду: %s" % _num(s.fire_rate),
		"Цели: %s" % tower.data.targets_text(),
		"Приоритет: %s" % tower.data.priority_text(),
	])
	if tower.data.air_damage_multiplier != 1.0:
		lines.append("Урон по летающим: ×%s" % _num(tower.data.air_damage_multiplier))
	if s.splash_radius > 0.0:
		lines.append("Урон по площади: %s м" % _num(s.splash_radius))
	if s.slow_factor < 1.0:
		lines.append("Замедление: −%d%% на %s с" % [roundi((1.0 - s.slow_factor) * 100), _num(s.slow_duration)])
	tower_stats.text = "\n".join(lines)
	if tower.can_upgrade():
		upgrade_button.text = "Улучшить — %d" % tower.upgrade_cost()
		upgrade_button.disabled = false
		upgrade_button.modulate = Color.WHITE if game.gold >= tower.upgrade_cost() else Color(0.6, 0.55, 0.55)
	else:
		upgrade_button.text = "Максимальный уровень"
		upgrade_button.disabled = true
		upgrade_button.modulate = Color.WHITE
	sell_button.text = "Продать +%d" % tower.sell_value()


func _on_upgrade_pressed() -> void:
	var tower := game.build.selected_tower
	if tower and game.upgrade_tower(tower):
		game.build.select_tower(tower)
	elif tower and tower.can_upgrade():
		_not_enough_gold()


func _on_sell_pressed() -> void:
	var tower := game.build.selected_tower
	if tower:
		game.sell_tower(tower)
		game.build.clear()


static func _num(value: float) -> String:
	return str(int(value)) if is_equal_approx(value, roundf(value)) else "%.1f" % value


# --- messages ------------------------------------------------------------------------------
func _show_banner(text: String, hold := 1.8) -> void:
	banner.text = text
	if _banner_tween:
		_banner_tween.kill()
	_banner_tween = create_tween()
	_banner_tween.tween_property(banner, "modulate:a", 1.0, 0.3)
	_banner_tween.tween_interval(hold)
	_banner_tween.tween_property(banner, "modulate:a", 0.0, 0.6)


func _on_game_over(victory: bool) -> void:
	build_panel.hide()
	tower_panel.hide()
	end_title.text = "Победа!" if victory else "Крепость пала"
	var waves := game.spawner.wave_index + (1 if victory else 0)
	end_info.text = "Отражено волн: %d из %d\nОсталось жизней: %d" % [waves, game.spawner.wave_count(), game.lives]
	end_screen.show()
