class_name MapTheme
extends Resource
## What a level's map is built from: the tile set and the decorations. The defaults are the level 1
## ("Valley of Forks") kingdom look, so a level without a theme looks exactly like before.

## Prefix of the tile models (models/tiles/<prefix><name>.glb); a tile missing in the set falls back to the
## unprefixed one (e.g. the haunted set has no river).
@export var tile_prefix := ""
## Forest cells ("T"): 1-3 of these, picked at random (repeat a name to make it more common).
@export var trees: PackedStringArray = ["pine_1", "pine_2", "oak_1", "pine_1", "pine_2", "oak_2"]
## Scattered on grass and next to the rocks.
@export var small_props: PackedStringArray = ["bush_1", "bush_2", "rock_1", "rock_2", "mushrooms", "stump"]
## The big piece on a rock cell ("r").
@export var rocks: PackedStringArray = ["rock_3", "rock_2"]
## Placed around the castle, each once.
@export var castle_props: PackedStringArray = ["crates", "well", "fence", "lamppost"]
## Occasional light next to the road.
@export var road_light := "lamppost"
## Landmark cells ("R"): one each, in random order without repeats until all are used.
@export var landmarks: PackedStringArray = []
## Cemetery cells ("G"): graves tiles (placed unrotated: the graves face south) ...
@export var cemetery_tiles: PackedStringArray = []
## ... fenced along the cemetery border, with a gate where a road enters the cemetery.
@export var cemetery_fence := ""
@export var cemetery_gate := ""
## Tiles taller than flat ground that should cast shadows.
@export var shadow_tiles: PackedStringArray = ["bridge"]
## Point lights at props (e.g. ghost lanterns, a crypt's door): prop name -> [offset in the prop's frame
## (Vector3, Godot axes), Color, energy, range (m)]. Only created by maps whose level has a lighting.
@export var prop_lights := {}
