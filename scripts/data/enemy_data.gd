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

@export_group("Healer")
## Share of a wounded ally's max HP restored per cast (0 = not a healer). The healer never heals itself.
@export_range(0.0, 1.0) var heal_fraction := 0.0
## Allies within this many metres are healed.
@export var heal_radius := 5.0
## Seconds between casts; the healer only casts when someone nearby is wounded.
@export var heal_interval := 6.0

@export_group("Ground slam")
## Seconds towers within `slam_radius` are stunned by the slam (0 = no slam).
@export var slam_stun := 0.0
## Towers within this many metres (horizontally) are stunned.
@export var slam_radius := 6.5
## Seconds between slams; the enemy only slams when a tower is in reach.
@export var slam_interval := 10.0

@export_group("Ghost")
## Seconds the enemy stays intangible: shots pass through, no damage, no slow (0 = not a ghost).
@export var phase_duration := 0.0
## Seconds between becoming intangible.
@export var phase_interval := 4.0
