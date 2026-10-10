class_name TowerData
extends Resource
## A tower type with its upgrade levels.

enum Targets { GROUND = 1, AIR = 2, BOTH = 3 }
## FIRST: the enemy closest to the castle. STRONGEST: the enemy with the most health (snipers).
enum Priority { FIRST, STRONGEST }

@export var id: StringName
@export var display_name := ""
@export_multiline var description := ""
@export var icon: Texture2D
@export var targets: Targets = Targets.BOTH
@export var priority: Priority = Priority.FIRST
## Damage multiplier against flying enemies.
@export var air_damage_multiplier := 1.0
@export var projectile: PackedScene
## Homing speed, or horizontal speed for lobbed shots (m/s).
@export var projectile_speed := 20.0
## Lobbed along an arc at the predicted position (cannon) instead of homing.
@export var ballistic := false
@export var impact_color := Color(1.0, 0.85, 0.5)
@export var levels: Array[TowerLevel] = []

@export_group("Audio and effects")
## Sound effect names from assets/audio/sfx; either may be empty (the archers have no shot sound).
@export var shoot_sound: StringName
@export var impact_sound: StringName
## Effects.PRESETS names; "explosion" is a combined fire + smoke + sparks + debris burst.
@export var impact_effect: StringName
@export var trail_effect: StringName
@export var muzzle_effect: StringName


func can_target(enemy: EnemyData) -> bool:
	return targets & (Targets.AIR if enemy.flying else Targets.GROUND) != 0


func priority_text() -> String:
	return "самый живучий враг" if priority == Priority.STRONGEST else "ближайший к замку"


func targets_text() -> String:
	match targets:
		Targets.GROUND:
			return "только наземные"
		Targets.AIR:
			return "только летающие"
	return "наземные и летающие"
