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
var _reveal_tween: Tween
var _flags: WindFlags
var _stun_left := 0.0
var _stun_tween: Tween
var _stun_sparks: GPUParticles3D


func setup(tower_data: TowerData, at_cell: Vector2i, projectile_parent: Node) -> void:
	data = tower_data
	cell = at_cell
	_projectiles = projectile_parent
	invested = stats().cost


func _ready() -> void:
	add_to_group(&"towers")
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
	FantasyMaterials.apply(_model)
	_skeleton = _model.find_child("Skeleton3D", true, false)
	_anim = _model.find_child("AnimationPlayer", true, false)
	_turret = _skeleton.find_bone("turret")
	_muzzle = _skeleton.find_bone("muzzle")
	_turret_rest = _skeleton.get_bone_rest(_turret).basis.get_rotation_quaternion()
	_flags = WindFlags.new(_model)
	_anim.get_animation(&"Idle").loop_mode = Animation.LOOP_LINEAR
	_anim.play(&"Idle")
	_apply_yaw()
	_play_reveal()
	if _stun_left > 0.0:  # upgraded while stunned
		_anim.speed_scale = 0.0
		FantasyMaterials.set_fx(_model, &"fx_stun", 1.0)


## The tower materialises from the ground up behind a rising band of golden runes.
func _play_reveal() -> void:
	if _reveal_tween:
		_reveal_tween.kill()
	var model := _model
	var base := global_position.y - 0.05
	var top := FantasyMaterials.top_of(model) + 0.35
	FantasyMaterials.set_fx(model, &"fx_reveal_y", base)
	_reveal_tween = create_tween()
	FantasyMaterials.tween_fx(_reveal_tween, model, &"fx_reveal_y", base, top, 0.4 + 0.15 * (top - base)) \
			.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_reveal_tween.tween_callback(func() -> void:
		FantasyMaterials.set_fx(model, &"fx_reveal_y", FantasyMaterials.REVEAL_NONE))


func _process(_delta: float) -> void:
	if _flags:
		_flags.update()


## Stunned by a ground slam: stops shooting and freezes for `duration` seconds.
func stun(duration: float) -> void:
	var already := _stun_left > 0.0
	_stun_left = maxf(_stun_left, duration)
	if already:
		return
	_anim.speed_scale = 0.0
	_tween_stun(1.0)
	_stun_sparks = Effects.trail(self, &"stun")
	_stun_sparks.position = Vector3.UP * (FantasyMaterials.top_of(_model) - global_position.y + 0.2)


func is_stunned() -> bool:
	return _stun_left > 0.0


func _end_stun() -> void:
	_anim.speed_scale = 1.0
	_tween_stun(0.0)
	Effects.release_trail(_stun_sparks, _projectiles)
	_stun_sparks = null


func _tween_stun(target: float) -> void:
	if _stun_tween:
		_stun_tween.kill()
	_stun_tween = create_tween()
	FantasyMaterials.tween_fx(_stun_tween, _model, &"fx_stun", 1.0 - target, target, 0.2)


func _physics_process(delta: float) -> void:
	if _stun_left > 0.0:
		_stun_left -= delta
		if _stun_left <= 0.0:
			_end_stun()
		return
	_cooldown -= delta
	# a sniper re-picks the strongest enemy before every shot
	if not _is_valid(_target) or (data.priority == TowerData.Priority.STRONGEST and _cooldown <= 0.0):
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


## Picks a target in range: the enemy with the least way left to the castle (routes differ in
## length, so this is not the same as the distance already walked), or for snipers the one
## with the most health left.
func _find_target() -> Enemy:
	var best: Enemy = null
	var strongest := data.priority == TowerData.Priority.STRONGEST
	for node in get_tree().get_nodes_in_group(&"enemies"):
		var enemy := node as Enemy
		if enemy.alive and data.can_target(enemy.data) and _in_range(enemy):
			if best == null:
				best = enemy
			elif strongest and not is_equal_approx(enemy.hp, best.hp):
				if enemy.hp > best.hp:
					best = enemy
			elif enemy.remaining_distance() < best.remaining_distance():
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
	Audio.play(data.shoot_sound, -3.0, 0.06)
	if not data.muzzle_effect.is_empty():
		var forward := _skeleton.global_transform.basis * (Quaternion(Vector3.UP, _yaw) * Vector3.BACK)
		Effects.burst(_projectiles, data.muzzle_effect, muzzle_position(), 1.0, forward)
