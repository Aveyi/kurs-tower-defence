class_name TowerData
extends Resource
## A tower type with its upgrade levels.

enum Targets { GROUND = 1, AIR = 2, BOTH = 3 }

@export var id: StringName
@export var display_name := ""
@export_multiline var description := ""
@export var icon: Texture2D
@export var targets: Targets = Targets.BOTH
@export var projectile: PackedScene
## Homing speed, or horizontal speed for lobbed shots (m/s).
@export var projectile_speed := 20.0
## Lobbed along an arc at the predicted position (cannon) instead of homing.
@export var ballistic := false
@export var impact_color := Color(1.0, 0.85, 0.5)
@export var levels: Array[TowerLevel] = []


func can_target(enemy: EnemyData) -> bool:
	return targets & (Targets.AIR if enemy.flying else Targets.GROUND) != 0


func targets_text() -> String:
	match targets:
		Targets.GROUND:
			return "только наземные"
		Targets.AIR:
			return "только летающие"
	return "наземные и летающие"
