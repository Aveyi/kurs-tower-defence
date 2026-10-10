class_name LevelData
extends Resource
## A level: the map as a character grid plus economy and waves.
##
## Layout legend (one character per 2x2 m cell, rows go north to south):
##   .  grass          T  forest          r  rocks
##   #  road           S  enemy portal (road start)
##   ~  river          =  bridge (road over the river)
##   P  tower plot     C  castle (a 3x2 block; the road enters through its middle column)
## Roads may fork and rejoin: enemies are spread over every route from the portal to the gate.
## Keep separate branches from touching each other sideways, or the tiles will join them.

@export var display_name := ""
@export var layout: PackedStringArray
@export var start_gold := 220
@export var lives := 20
## Enemy HP multiplier for wave n (counted from 0): 1 + hp_growth * n ^ hp_growth_power.
## A power above 1 keeps the first waves gentle and makes the last ones much tougher.
@export var hp_growth := 0.06
@export var hp_growth_power := 1.0


func hp_multiplier(wave_index: int) -> float:
	return 1.0 + hp_growth * pow(maxi(wave_index, 0), hp_growth_power)
## Seed for decorations (trees, rocks, grass variants).
@export var decor_seed := 1
@export var waves: Array[WaveData] = []
