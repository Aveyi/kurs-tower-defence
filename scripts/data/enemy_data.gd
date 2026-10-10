class_name EnemyData
extends Resource
## Static description of an enemy type: balance values and visuals.

@export var id: StringName
@export var display_name := ""
@export var icon: Texture2D
@export var model: PackedScene
@export var max_hp := 100.0
## Metres per second along the path.
@export var speed := 2.0
## Playback speed of the walk cycle, so feet roughly match the movement.
@export var anim_speed := 1.0
## Gold for a kill.
@export var reward := 5
## Lives taken when it reaches the castle.
@export var damage := 1
@export var flying := false
@export var is_boss := false
## Height of the health bar above the origin, metres.
@export var hp_bar_height := 1.2
## Height projectiles aim at, metres.
@export var aim_height := 0.6

@export_group("Summoner")
@export var summon: EnemyData
@export var summon_count := 0
@export var summon_interval := 8.0
