class_name LevelData
extends Resource
## A level: the map as a character grid plus economy and waves.
##
## Layout legend (one character per 2x2 m cell, rows go north to south):
##   .  grass          T  forest (1-3 trees)   t  a lone tree   r  rocks
##   #  road           S  enemy portal (road start)
##   ~  river          =  bridge (road over the river)
##   P  tower plot     C  castle (a 3x2 block; the road enters through its middle column)
##   G  cemetery (graves tiles, fenced; a gate where a road enters it)
##   R  landmark (one big piece from the theme: ruins, crypt, standing stones...)
##   s  sealed enemy portal (road start): opens at wave `sealed_portal_wave`
##   L  lantern beside the road (the theme's `lantern`)
## Roads may fork and rejoin: enemies are spread over every route from the portal to the gate.
## Keep separate branches from touching each other sideways, or the tiles will join them.

## Key for saved results.
@export var id: StringName
@export var display_name := ""
@export_multiline var description := ""
@export var preview: Texture2D
@export var layout: PackedStringArray
## Battle music: a track in assets/audio/music (built by tools/audio/build_audio.py).
@export var music := &"battle"
## Tiles and decorations; empty = the level 1 kingdom set (see MapTheme).
@export var map_theme: MapTheme
## Lighting (sky, sun or moon, fog, grading); empty = the game scene's daylight.
@export var lighting: LevelLighting
## Look of the in-game HUD: "kingdom" (warm wood and gold) or "haunted" (dark violet, see Hud._apply_style).
@export var hud_style := &"kingdom"
@export var start_gold := 220
@export var lives := 20
## Enemy HP multiplier for wave n (counted from 0): 1 + hp_growth * n ^ hp_growth_power.
## A power above 1 keeps the first waves gentle and makes the last ones much tougher.
@export var hp_growth := 0.06
@export var hp_growth_power := 1.0
## Difficulty: every enemy's HP (bosses too) on top of the wave growth.
@export var enemy_hp_scale := 1.0


func hp_multiplier(wave_index: int) -> float:
	return enemy_hp_scale * (1.0 + hp_growth * pow(maxi(wave_index, 0), hp_growth_power))
## Wave (counted from 0) that opens the sealed portals ("s"); -1 = they are open from the start.
@export var sealed_portal_wave := -1
## Seed for decorations (trees, rocks, grass variants).
@export var decor_seed := 1
@export var waves: Array[WaveData] = []
