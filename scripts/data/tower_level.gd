class_name TowerLevel
extends Resource
## One upgrade level of a tower.

@export var model: PackedScene
## Price of this level (build price for level 1, upgrade price for the next ones).
@export var cost := 100
@export var damage := 10.0
@export var attack_range := 7.0
## Shots per second.
@export var fire_rate := 1.0
## Area damage radius around the impact point; 0 = single target.
@export var splash_radius := 0.0
## Speed multiplier applied to hit enemies (1 = no slow).
@export var slow_factor := 1.0
@export var slow_duration := 0.0
