class_name CameraRig
extends Node3D
## Strategy camera.
## Pan: WASD / arrows, middle mouse drag. Rotate: Q / E.
## Zoom: mouse wheel, trackpad pinch or two-finger scroll, +/- keys.
## Close up the camera tilts toward the horizon and aims a bit higher, so the models are seen
## from the side; far away it looks down on the whole map.
## Uses real (unscaled) time so it stays responsive at x2 game speed and while paused.

@export var pan_speed := 16.0
@export var min_distance := 4.5
@export var max_distance := 40.0
## Camera pitch (degrees below the horizon) at the closest and the farthest zoom.
@export var pitch_near := 30.0
@export var pitch_far := 58.0
## Height of the look-at point above the ground at the closest zoom.
@export var look_height_near := 0.9
@export var rotate_speed := 1.6
@export var key_zoom_speed := 1.6

var bounds := Rect2()

var _distance := 26.0
var _target_distance := 26.0
var _yaw := 0.0
var _dragging := false

@onready var camera: Camera3D = $Camera3D


func setup(map_bounds: Rect2, focus: Vector3, distance := 26.0) -> void:
	bounds = map_bounds
	position = Vector3(focus.x, 0.0, focus.z)
	_distance = distance
	_target_distance = distance
	_apply()


## Multiplies the target distance (factor < 1 zooms in).
func zoom_by(factor: float) -> void:
	_target_distance = clampf(_target_distance * factor, min_distance, max_distance)


func _process(delta: float) -> void:
	var real_delta := delta / maxf(Engine.time_scale, 0.001)
	var move := Input.get_vector(&"cam_left", &"cam_right", &"cam_forward", &"cam_back")
	_yaw += Input.get_axis(&"cam_rotate_right", &"cam_rotate_left") * rotate_speed * real_delta
	position += Basis(Vector3.UP, _yaw) * Vector3(move.x, 0, move.y) * pan_speed * real_delta * (_distance / 26.0)
	var key_zoom := Input.get_axis(&"zoom_in", &"zoom_out")
	if key_zoom != 0.0:
		zoom_by(exp(key_zoom * key_zoom_speed * real_delta))
	_distance = lerpf(_distance, _target_distance, 1.0 - exp(-10.0 * real_delta))
	_apply()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var notch: float = event.factor if event.factor > 0.0 else 1.0  # smooth-scroll mice report fractions
		match event.button_index:
			MOUSE_BUTTON_WHEEL_UP:
				if event.pressed:
					zoom_by(pow(0.88, notch))
			MOUSE_BUTTON_WHEEL_DOWN:
				if event.pressed:
					zoom_by(pow(1.0 / 0.88, notch))
			MOUSE_BUTTON_MIDDLE:
				_dragging = event.pressed
	elif event is InputEventMagnifyGesture:  # trackpad pinch
		zoom_by(1.0 / event.factor)
	elif event is InputEventPanGesture:  # trackpad two-finger scroll
		zoom_by(exp(event.delta.y * 0.08))
	elif event is InputEventMouseMotion and _dragging:
		var k := _distance / 900.0
		position += Basis(Vector3.UP, _yaw) * Vector3(-event.relative.x, 0, -event.relative.y) * k


func _apply() -> void:
	if bounds.has_area():
		position.x = clampf(position.x, bounds.position.x, bounds.end.x)
		position.z = clampf(position.z, bounds.position.y, bounds.end.y)
	rotation.y = _yaw
	var t := inverse_lerp(min_distance, max_distance, _distance)
	var pitch := deg_to_rad(lerpf(pitch_near, pitch_far, sqrt(t)))
	var look := Vector3(0, lerpf(look_height_near, 0.0, t), 0)
	camera.position = look + Vector3(0, sin(pitch) * _distance, cos(pitch) * _distance)
	camera.rotation = Vector3(-pitch, 0, 0)
