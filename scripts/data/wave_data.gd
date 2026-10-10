class_name WaveData
extends Resource
## One wave: several spawn groups running in parallel.

@export var groups: Array[SpawnGroup] = []
## Gold paid when the wave is cleared.
@export var bonus := 20
