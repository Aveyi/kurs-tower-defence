class_name BuildController
extends Node3D
## Mouse interaction with the map: hovering and selecting plots and towers, range preview.
## The HUD shows the build / tower panels in response to the selection signals.

signal plot_selected(cell: Vector2i)
signal tower_selected(tower: Tower)
signal selection_cleared

const HIGHLIGHT_SHADER := preload("res://shaders/cell_highlight.gdshader")
const RING_SHADER := preload("res://shaders/range_ring.gdshader")
const NONE := Vector2i(-1, -1)

var game: Game
var selected_cell := NONE
var selected_tower: Tower

var _hover: MeshInstance3D
var _selection: MeshInstance3D
var _ring: MeshInstance3D


func setup(owner_game: Game) -> void:
	game = owner_game
	_hover = _make_marker(Color(1.0, 0.95, 0.6, 0.7), 0.0)
	_selection = _make_marker(Color(0.5, 1.0, 0.45, 1.0), 1.0)
	_ring = MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(2, 2)
	_ring.mesh = plane
	var ring_material := ShaderMaterial.new()
	ring_material.shader = RING_SHADER
	_ring.material_override = ring_material
	_ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_ring.visible = false
	add_child(_ring)


func _make_marker(color: Color, pulse: float) -> MeshInstance3D:
	var marker := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(1.9, 1.9)
	marker.mesh = plane
	var material := ShaderMaterial.new()
	material.shader = HIGHLIGHT_SHADER
	material.set_shader_parameter(&"color", color)
	material.set_shader_parameter(&"pulse", pulse)
	marker.material_override = material
	marker.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	marker.visible = false
	add_child(marker)
	return marker


func _unhandled_input(event: InputEvent) -> void:
	if game.over:
		return
	if event is InputEventMouseMotion:
		_update_hover(event.position)
	elif event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_LEFT:
			_click(event.position)
		elif event.button_index == MOUSE_BUTTON_RIGHT:
			clear()


## Map cell under a screen point (ray against the ground plane).
func cell_at_screen(screen_pos: Vector2) -> Vector2i:
	var camera := get_viewport().get_camera_3d()
	var hit: Variant = Plane(Vector3.UP, 0.0).intersects_ray(
			camera.project_ray_origin(screen_pos), camera.project_ray_normal(screen_pos))
	return NONE if hit == null else game.map.world_to_cell(hit)


func _interactive(cell: Vector2i) -> bool:
	return game.map.is_plot(cell) or game.tower_at(cell) != null


func _update_hover(screen_pos: Vector2) -> void:
	var cell := cell_at_screen(screen_pos)
	_hover.visible = _interactive(cell) and cell != selected_cell
	if _hover.visible:
		_hover.position = game.map.cell_center(cell) + Vector3(0, Map.PLOT_HEIGHT + 0.02, 0)


func _click(screen_pos: Vector2) -> void:
	var cell := cell_at_screen(screen_pos)
	var tower := game.tower_at(cell)
	if tower:
		select_tower(tower)
	elif game.map.is_plot(cell):
		select_plot(cell)
	else:
		clear()


func select_plot(cell: Vector2i) -> void:
	selected_cell = cell
	selected_tower = null
	_show_selection()
	_ring.visible = false
	plot_selected.emit(cell)


func select_tower(tower: Tower) -> void:
	selected_cell = tower.cell
	selected_tower = tower
	_show_selection()
	show_range(tower.stats().attack_range)
	tower_selected.emit(tower)


func clear() -> void:
	selected_cell = NONE
	selected_tower = null
	_selection.visible = false
	_ring.visible = false
	selection_cleared.emit()


## Shows the range ring around the selected cell (radius <= 0 hides it unless a tower is selected).
func show_range(radius: float) -> void:
	if radius <= 0.0 and selected_tower:
		radius = selected_tower.stats().attack_range
	_ring.visible = radius > 0.0 and selected_cell != NONE
	if _ring.visible:
		_ring.position = game.map.cell_center(selected_cell) + Vector3(0, 0.12, 0)
		_ring.scale = Vector3(radius, 1, radius)


func _show_selection() -> void:
	_selection.visible = true
	_selection.position = game.map.cell_center(selected_cell) + Vector3(0, Map.PLOT_HEIGHT + 0.03, 0)
	_hover.visible = false
