class_name WindFlags
extends RefCounted
## Turns every "flag*" bone of a model so that all flags on the map stream downwind together,
## whatever the rotation of their model, with gusts that travel across the map.
## Takes the flags out of the model's Idle animation (it used its own phase per flag).

## Wind direction in world space (x, z); matches wind_direction in shaders/foliage.gdshader.
const DIRECTION := Vector3(0.8, 0.0, 0.6)
const FLUTTER_DEGREES := 11.0
const FLUTTER_SPEED := 2.3
## Gust phase change per metre along the wind.
const GUST_WAVELENGTH := 0.45

var _skeleton: Skeleton3D
var _flags: Array = []  # [bone, parent bone, global rest rotation]


func _init(model: Node) -> void:
	_skeleton = model.find_child("Skeleton3D", true, false)
	if _skeleton == null:
		return
	for bone in _skeleton.get_bone_count():
		if _skeleton.get_bone_name(bone).begins_with("flag"):
			_flags.append([bone, _skeleton.get_bone_parent(bone),
					_skeleton.get_bone_global_rest(bone).basis.get_rotation_quaternion()])
	if _flags.is_empty():
		return
	var player: AnimationPlayer = model.find_child("AnimationPlayer", true, false)
	if player and player.has_animation(&"Idle"):
		var idle := player.get_animation(&"Idle")  # shared by all instances: removing once is enough
		for i in range(idle.get_track_count() - 1, -1, -1):
			if String(idle.track_get_path(i).get_concatenated_subnames()).begins_with("flag"):
				idle.remove_track(i)


func is_empty() -> bool:
	return _flags.is_empty()


## Call every frame. Uses the wall clock, so every flag on the map shares the same gusts.
func update() -> void:
	if _flags.is_empty() or not is_instance_valid(_skeleton):
		return
	var time := Time.get_ticks_msec() * 0.001
	var wind := _skeleton.global_basis.inverse() * DIRECTION
	var downwind := atan2(-wind.z, wind.x)  # flags are modelled pointing along +X
	for flag in _flags:
		var bone: int = flag[0]
		var parent: int = flag[1]
		var at := _skeleton.global_transform * _skeleton.get_bone_global_pose(bone).origin
		var phase := at.dot(DIRECTION.normalized()) * GUST_WAVELENGTH
		var flutter := sin(time * FLUTTER_SPEED - phase) * 0.7 + sin(time * FLUTTER_SPEED * 2.7 - phase * 1.4) * 0.3
		var yaw := downwind + deg_to_rad(FLUTTER_DEGREES) * flutter
		var parent_rotation := Quaternion.IDENTITY
		if parent >= 0:
			parent_rotation = _skeleton.get_bone_global_pose(parent).basis.get_rotation_quaternion()
		_skeleton.set_bone_pose_rotation(bone, parent_rotation.inverse() * Quaternion(Vector3.UP, yaw) * flag[2])
