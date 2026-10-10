class_name LevelData
extends Resource
## A level: the map as a character grid plus economy and waves.
##
## Layout legend (one character per 2x2 m cell, rows go north to south):
##   .  grass          T  forest          r  rocks
##   #  road           S  enemy portal (road start)
##   ~  river          =  bridge (road over the river)
##   P  tower plot     C  castle (a 3x2 block; the road must touch its middle column)

@export var display_name := ""
@export var layout: PackedStringArray
@export var start_gold := 220
@export var lives := 20
## Enemy HP grows by this fraction with every wave.
@export var hp_growth := 0.06
## Seed for decorations (trees, rocks, grass variants).
@export var decor_seed := 1
@export var waves: Array[WaveData] = []
