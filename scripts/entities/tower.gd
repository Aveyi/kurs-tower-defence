class_name Tower
extends Node3D
## A tower on a plot. Turns its "turret" bone toward the target and fires from the "muzzle" bone.

## Turret turn speed, rad/s.
const TURN_SPEED := 7.0
## The turret must face the target within this angle to fire, rad.
const AIM_TOLERANCE := 0.35
const SELL_RATIO := 0.7

var data: TowerData
var level := 0
var cell := Vector2i.ZERO
## Gold spent on building and upgrades (sell price is a share of it).
var invested := 0

var _projectiles: Node
var _model: Node3D
var _skeleton: Skeleton3D
var _anim: AnimationPlayer
var _turret := -1
var _muzzle := -1
var _turret_rest := Quaternion.IDENTITY
var _yaw := 0.0
var _cooldown := 0.0
var _target: Enemy


func setup(tower_data: TowerData, at_cell: Vector2i, projectile_parent: Node) -> void:
	data = tower_data
	cell = at_cell
	_projectiles = projectile_parent
	invested = stats().cost


func _ready() -> void:
	_load_model()


func stats() -> TowerLevel:
	return data.levels[level]


func can_upgrade() -> bool:
	return level + 1 < data.levels.size()


func upgrade_cost() -> int:
	return data.levels[level + 1].cost if can_upgrade() else 0


func sell_value() -> int:
	return roundi(invested * SELL_RATIO)


func upgrade() -> void:
	level += 1
	invested += stats().cost
	_load_model()


func _load_model() -> void:
	if _model:
		_model.queue_free()
	_model = stats().model.instantiate()
	add_child(_model)
	_skeleton = _model.find_child("Skeleton3D", true, false)
	_anim = _model.find_child("AnimationPlayer", true, false)
	_turret = _skeleton.find_bone("turret")
	_muzzle = _skeleton.find_bone("muzzle")
	_turret_rest = _skeleton.get_bone_rest(_turret).basis.get_rotation_quaternion()
	_anim.get_animation(&"Idle").loop_mode = Animation.LOOP_LINEAR
	_anim.play(&"Idle")
	_apply_yaw()
	_model.scale = Vector3.ONE * 0.6
	create_tween().tween_property(_model, "scale", Vector3.ONE, 0.35) \
			.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


func _physics_process(delta: float) -> void:
	_cooldown -= delta
	if not _is_valid(_target):
		_target = _find_target()
	if _target == null:
		return
	var desired := _yaw_to(_target.aim_point())
	_yaw = rotate_toward(_yaw, desired, TURN_SPEED * delta)
	_apply_yaw()
	if _cooldown <= 0.0 and absf(angle_difference(_yaw, desired)) < AIM_TOLERANCE:
		_fire()


func _in_range(enemy: Enemy) -> bool:
	var d := enemy.global_position - global_position
	return Vector2(d.x, d.z).length() <= stats().attack_range


func _is_valid(enemy: Enemy) -> bool:
	return is_instance_valid(enemy) and enemy.alive and _in_range(enemy)


## Picks the enemy closest to the castle (furthest along the path) among those in range.
func _find_target() -> Enemy:
	var best: Enemy = null
	for node in get_tree().get_nodes_in_group(&"enemies"):
		var enemy := node as Enemy
		if enemy.alive and data.can_target(enemy.data) and _in_range(enemy):
			if best == null or enemy.progress > best.progress:
				best = enemy
	return best


func _yaw_to(point: Vector3) -> float:
	var local := _skeleton.global_transform.affine_inverse() * point
	var pivot := _skeleton.get_bone_global_pose(_turret).origin
	return atan2(local.x - pivot.x, local.z - pivot.z)


func _apply_yaw() -> void:
	_skeleton.set_bone_pose_rotation(_turret, Quaternion(Vector3.UP, _yaw) * _turret_rest)


func muzzle_position() -> Vector3:
	return _skeleton.global_transform * _skeleton.get_bone_global_pose(_muzzle).origin


func _fire() -> void:
	_cooldown = 1.0 / stats().fire_rate
	_anim.clear_queue()
	_anim.play(&"Shoot")
	_anim.seek(0.0, true)
	_anim.queue(&"Idle")
	var projectile := Projectile.new()
	projectile.setup(data, stats(), _target, muzzle_position())
	_projectiles.add_child(projectile)
