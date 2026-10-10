class_name Projectile
extends Node3D
## A shot fired by a tower: homing (arrows, orbs, shards, bolts) or lobbed along an arc (bombs).

var _tower: TowerData
var _stats: TowerLevel
var _target: Enemy
var _point := Vector3.ZERO
var _start := Vector3.ZERO
var _time := 0.0
var _flight := 1.0
var _arc := 0.0


func setup(tower: TowerData, stats: TowerLevel, target: Enemy, from: Vector3) -> void:
	_tower = tower
	_stats = stats
	_target = target
	_start = from
	_point = target.aim_point()
	if tower.ballistic:
		var distance := from.distance_to(_point)
		_flight = clampf(distance / tower.projectile_speed, 0.5, 1.3)
		_point = target.predict_position(_flight)
		_arc = 1.0 + distance * 0.18


func _ready() -> void:
	add_child(_tower.projectile.instantiate())
	global_position = _start


func _physics_process(delta: float) -> void:
	if _tower.ballistic:
		_time += delta
		var t := minf(_time / _flight, 1.0)
		var next := _start.lerp(_point, t) + Vector3.UP * _arc * 4.0 * t * (1.0 - t)
		_face(next - global_position)
		global_position = next
		if t >= 1.0:
			_impact(_point)
		return
	if is_instance_valid(_target) and _target.alive:
		_point = _target.aim_point()
	var to := _point - global_position
	var step := _tower.projectile_speed * delta
	if to.length() <= step:
		_impact(_point)
		return
	_face(to)
	global_position += to.normalized() * step


func _face(direction: Vector3) -> void:
	if direction.length_squared() < 0.000001:
		return
	direction = direction.normalized()
	var up := Vector3.UP if absf(direction.y) < 0.99 else Vector3.RIGHT
	global_basis = Basis.looking_at(direction, up, true)


func _impact(at: Vector3) -> void:
	var hit: Array[Enemy] = []
	if _stats.splash_radius > 0.0:
		for node in get_tree().get_nodes_in_group(&"enemies"):
			var enemy := node as Enemy
			var d := enemy.global_position - at
			if enemy.alive and _tower.can_target(enemy.data) and Vector2(d.x, d.z).length() <= _stats.splash_radius:
				hit.append(enemy)
	elif is_instance_valid(_target) and _target.alive:
		hit.append(_target)
	for enemy in hit:
		enemy.take_damage(_stats.damage)
		if _stats.slow_factor < 1.0:
			enemy.apply_slow(_stats.slow_factor, _stats.slow_duration)
	Effects.impact(get_parent(), at, _tower.impact_color, maxf(_stats.splash_radius, 0.5))
	queue_free()
