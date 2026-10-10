class_name Enemy
extends Node3D
## An enemy moving along the map path (Curve3D). Created by WaveSpawner.

signal died(enemy: Enemy)
signal reached_end(enemy: Enemy)
## A summoner boss finished its cast; WaveSpawner spawns the minions.
signal summon_requested(enemy: Enemy)

const HEALTH_BAR_SHADER := preload("res://shaders/health_bar.gdshader")
const CAST_TIME := 1.4
const CAST_SUMMON_AT := 0.8

static var _bar_material: ShaderMaterial

var data: EnemyData
var max_hp := 1.0
var hp := 1.0
## Distance travelled along the path, metres.
var progress := 0.0
var alive := true
## Sideways offset from the path centre so a crowd does not walk in single file.
var lane := 0.0
## Index of the map route this enemy follows.
var route := 0

var _curve: Curve3D
var _length := 0.0
var _anim: AnimationPlayer
var _move_anim := &"Walk"
var _bar: MeshInstance3D
var _model: Node3D
var _flash_tween: Tween
var _frost_tween: Tween
var _frost := 0.0
var _slow := 1.0
var _slow_left := 0.0
var _hit_cooldown := 0.0
var _summon_left := 0.0
var _cast_left := 0.0


func setup(enemy_data: EnemyData, path: Curve3D, hp_multiplier: float, start := 0.0, lane_offset := 0.0) -> void:
	data = enemy_data
	_curve = path
	_length = path.get_baked_length()
	max_hp = data.max_hp * hp_multiplier
	hp = max_hp
	progress = start
	lane = lane_offset
	_summon_left = data.summon_interval


func _ready() -> void:
	add_to_group(&"enemies")
	_model = data.model.instantiate()
	add_child(_model)
	FantasyMaterials.apply(_model)
	_anim = _model.find_child("AnimationPlayer", true, false)
	_move_anim = &"Fly" if _anim.has_animation(&"Fly") else &"Walk"
	var move := _anim.get_animation(_move_anim)
	move.loop_mode = Animation.LOOP_LINEAR
	_anim.speed_scale = data.anim_speed
	_anim.play(_move_anim)
	_anim.seek(randf() * move.length, true)
	_bar = _make_health_bar()
	_update_transform()


func _physics_process(delta: float) -> void:
	if not alive:
		return
	_hit_cooldown -= delta
	if _slow_left > 0.0:
		_slow_left -= delta
		if _slow_left <= 0.0:
			_slow = 1.0
			_anim.speed_scale = data.anim_speed
			_set_frost(0.0)
	if _cast_left > 0.0:
		_update_cast(delta)
		return
	if data.summon and data.summon_count > 0:
		_summon_left -= delta
		if _summon_left <= 0.0:
			_start_cast()
	progress += data.speed * _slow * delta
	if progress >= _length:
		alive = false
		remove_from_group(&"enemies")
		reached_end.emit(self)
		queue_free()
		return
	_update_transform()


func _update_transform() -> void:
	var pos := _curve.sample_baked(progress)
	var dir := _curve.sample_baked(minf(progress + 0.4, _length)) - pos
	if dir.length_squared() < 0.0001:
		return
	dir = dir.normalized()
	global_position = pos + dir.cross(Vector3.UP) * lane
	global_basis = Basis.looking_at(dir, Vector3.UP, true)


## Metres left to the castle gate (towers aim at whoever is closest to it).
func remaining_distance() -> float:
	return _length - progress


## Where the enemy will be in `seconds` if nothing slows it down (for lobbed shots).
func predict_position(seconds: float) -> Vector3:
	return _curve.sample_baked(minf(progress + data.speed * _slow * seconds, _length))


## The point projectiles fly to.
func aim_point() -> Vector3:
	return global_position + Vector3.UP * data.aim_height


func take_damage(amount: float) -> void:
	if not alive:
		return
	hp -= amount
	_bar.visible = true
	_bar.set_instance_shader_parameter(&"ratio", clampf(hp / max_hp, 0.0, 1.0))
	_flash()
	if hp <= 0.0:
		_die()
	elif not data.is_boss and _hit_cooldown <= 0.0 and _cast_left <= 0.0:
		_hit_cooldown = 0.6
		_play(&"Hit")
		_anim.queue(_move_anim)


func apply_slow(factor: float, duration: float) -> void:
	if not alive:
		return
	_slow = minf(_slow, factor) if _slow_left > 0.0 else factor
	_slow_left = maxf(_slow_left, duration)
	_anim.speed_scale = data.anim_speed * _slow
	_set_frost(1.0)


func _flash() -> void:
	if _flash_tween:
		_flash_tween.kill()
	_flash_tween = create_tween()
	FantasyMaterials.tween_fx(_flash_tween, _model, &"fx_flash", 1.0, 0.0, 0.18)


func _set_frost(target: float) -> void:
	if _frost_tween:
		_frost_tween.kill()
	_frost_tween = create_tween()
	FantasyMaterials.tween_fx(_frost_tween, _model, &"fx_frost", _frost, target, 0.25)
	_frost = target


func _die() -> void:
	alive = false
	remove_from_group(&"enemies")
	_bar.visible = false
	died.emit(self)
	_anim.speed_scale = 1.0
	_play(&"Die")
	var world := get_parent()
	Effects.burst(world, &"death", global_position + Vector3.UP * 0.4, 1.6 if data.is_boss else 1.0)
	if data.is_boss:
		Effects.burst(world, &"souls", global_position + Vector3.UP * 1.0, 1.5)
		Audio.play(&"boss_die")
	else:
		Audio.play(&"enemy_die", -5.0, 0.08)
	if _frost_tween:
		_frost_tween.kill()
	FantasyMaterials.set_fx(_model, &"fx_frost", 0.0)
	# the body falls, then burns away into embers
	var tween := create_tween()
	tween.tween_interval(_anim.get_animation(&"Die").length + 0.2)
	FantasyMaterials.tween_fx(tween, _model, &"fx_dissolve", 0.0, 1.0, 1.6 if data.is_boss else 1.1)
	tween.tween_callback(queue_free)


func _start_cast() -> void:
	_cast_left = CAST_TIME
	_summon_left = data.summon_interval
	_play(&"Cast" if _anim.has_animation(&"Cast") else &"Hit")
	Audio.play(&"summon")
	Effects.burst(get_parent(), &"portal", global_position + Vector3.UP * 1.2, 1.3)


func _update_cast(delta: float) -> void:
	var before := _cast_left
	_cast_left -= delta
	if before > CAST_SUMMON_AT and _cast_left <= CAST_SUMMON_AT:
		summon_requested.emit(self)
	if _cast_left <= 0.0:
		_play(_move_anim)


func _play(anim: StringName) -> void:
	_anim.clear_queue()
	_anim.play(anim)
	_anim.seek(0.0, true)


func _make_health_bar() -> MeshInstance3D:
	if _bar_material == null:
		_bar_material = ShaderMaterial.new()
		_bar_material.shader = HEALTH_BAR_SHADER
	var quad := QuadMesh.new()
	quad.size = Vector2(1.6, 0.13) if data.is_boss else Vector2(0.9, 0.09)
	var bar := MeshInstance3D.new()
	bar.mesh = quad
	bar.material_override = _bar_material
	bar.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	bar.position.y = data.hp_bar_height
	bar.visible = data.is_boss
	add_child(bar)
	bar.set_instance_shader_parameter(&"ratio", 1.0)
	return bar
