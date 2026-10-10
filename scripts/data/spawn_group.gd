class_name SpawnGroup
extends Resource
## A batch of identical enemies inside a wave.

@export var enemy: EnemyData
@export var count := 5
## Seconds between two enemies of the group.
@export var interval := 1.0
## Seconds after the wave start before the first enemy of the group appears.
@export var delay := 0.0
