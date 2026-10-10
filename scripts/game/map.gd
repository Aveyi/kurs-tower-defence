class_name Map
extends Node3D
## Builds the level from LevelData.layout:
## - tiles in a GridMap, road and river tiles auto-picked and rotated from their neighbours;
## - the enemy portal, the castle and decorations;
## - one enemy route (Curve3D) for every way along the road network from the portal to the
##   castle gate; forks and rejoining branches are allowed.

const CELL := 2.0
## Top of the tower plot platform; towers stand on it.
const PLOT_HEIGHT := 0.085
## Neighbour directions in grid space (x = column/east, y = row/south): N, E, S, W.
const DIRS: Array[Vector2i] = [Vector2i(0, -1), Vector2i(1, 0), Vector2i(0, 1), Vector2i(-1, 0)]
## Connections of the unrotated tiles (indices into DIRS), see tools/blender/env.py.
const ROAD_TILES := {
	"road_end": [2], "road_straight": [0, 2], "road_corner": [2, 1], "road_t": [0, 2, 1], "road_cross": [0, 1, 2, 3],
}
const RIVER_TILES := {"river_straight": [0, 2], "river_corner": [2, 1]}
const TREES: Array[String] = ["pine_1", "pine_2", "oak_1", "pine_1", "pine_2", "oak_2"]
const SMALL_PROPS: Array[String] = ["bush_1", "bush_2", "rock_1", "rock_2", "mushrooms", "stump"]
const CASTLE_PROPS: Array[String] = ["crates", "well", "fence", "lamppost"]
const VORTEX_SHADER := preload("res://shaders/portal_vortex.gdshader")
## Safety limit for route enumeration on badly designed maps (road grids explode combinatorially).
const MAX_ROUTES := 32

var layout: PackedStringArray
var size := Vector2i.ZERO
## Enemy routes from the portal to the castle, shortest first.
var routes: Array[Curve3D] = []
var portal: Node3D
var castle: Node3D
var castle_center := Vector3.ZERO

var _grid: GridMap
var _gate_column := -1
var _portal_anim: AnimationPlayer
var _castle_flags: WindFlags
var _last_portal_fx := -100000


func build(level: LevelData) -> void:
	layout = level.layout
	size = Vector2i(layout[0].length(), layout.size())
	_grid = GridMap.new()
	_grid.mesh_library = TileLibrary.get_library()
	_grid.cell_size = Vector3(CELL, 1.0, CELL)
	_grid.cell_center_y = false
	add_child(_grid)
	var columns := _find("C").map(func(c: Vector2i) -> int: return c.x)
	if not columns.is_empty():
		_gate_column = (columns.min() + columns.max()) / 2
	var rng := RandomNumberGenerator.new()
	rng.seed = level.decor_seed
	for row in size.y:
		for col in size.x:
			_place_tile(Vector2i(col, row), rng)
	_place_portal()
	_place_castle()
	_build_routes()
	_place_decor(rng)


# --- queries -------------------------------------------------------------------------------
func char_at(cell: Vector2i) -> String:
	if cell.x < 0 or cell.y < 0 or cell.x >= size.x or cell.y >= size.y:
		return " "
	return layout[cell.y][cell.x]


func is_road(cell: Vector2i) -> bool:
	return char_at(cell) in ["#", "=", "S"]


func is_river(cell: Vector2i) -> bool:
	return char_at(cell) in ["~", "="]


func is_plot(cell: Vector2i) -> bool:
	return char_at(cell) == "P"


## A castle cell in the gate (middle) column: the only place a road may enter the castle.
func _is_gate(cell: Vector2i) -> bool:
	return char_at(cell) == "C" and cell.x == _gate_column


func _at_gate(cell: Vector2i) -> bool:
	return DIRS.any(func(d: Vector2i) -> bool: return _is_gate(cell + d))


func cell_center(cell: Vector2i) -> Vector3:
	return Vector3((cell.x + 0.5) * CELL, 0.0, (cell.y + 0.5) * CELL)


func world_to_cell(point: Vector3) -> Vector2i:
	return Vector2i(floori(point.x / CELL), floori(point.z / CELL))


func bounds() -> Rect2:
	return Rect2(0, 0, size.x * CELL, size.y * CELL)


func _process(_delta: float) -> void:
	if _castle_flags:
		_castle_flags.update()


func play_portal_spawn() -> void:
	var now := Time.get_ticks_msec()
	if now - _last_portal_fx < 700:
		return
	_last_portal_fx = now
	if _portal_anim:
		_portal_anim.play(&"Spawn")
		_portal_anim.queue(&"Idle")
	Effects.burst(self, &"portal", portal.global_position + Vector3.UP * 1.25)
	Audio.play(&"portal_spawn", -6.0, 0.7)


# --- tiles ---------------------------------------------------------------------------------
func _place_tile(cell: Vector2i, rng: RandomNumberGenerator) -> void:
	var tile := "grass_%d" % [1, 1, 2, 3][rng.randi() % 4]
	var turns := rng.randi() % 4
	match char_at(cell):
		"#", "S":
			var fit := _fit(_mask(cell, func(n: Vector2i) -> bool: return is_road(n) or _is_gate(n)), ROAD_TILES)
			tile = fit[0]
			turns = fit[1]
		"~":
			var mask := _mask(cell, is_river)
			if mask.size() <= 1:  # river flows off the map edge
				mask = [0, 2] if mask.is_empty() else [mask[0], (mask[0] + 2) % 4]
			var fit := _fit(mask, RIVER_TILES)
			tile = fit[0]
			turns = fit[1]
		"=":
			tile = "bridge"
			turns = 0 if is_road(cell + DIRS[1]) or is_road(cell + DIRS[3]) else 1
		"P":
			tile = "plot"
			turns = 0
		"C":
			tile = "grass_1"
	var orientation := _grid.get_orthogonal_index_from_basis(Basis(Vector3.UP, turns * PI / 2.0))
	_grid.set_cell_item(Vector3i(cell.x, 0, cell.y), TileLibrary.id_of(tile), orientation)


## Indices of the DIRS where `connects` is true for the neighbour.
func _mask(cell: Vector2i, connects: Callable) -> Array:
	var out := []
	for d in DIRS.size():
		if connects.call(cell + DIRS[d]):
			out.append(d)
	return out


## Finds the tile whose connections, rotated `turns` times by +90 deg, equal the mask.
## A +90 deg turn about Y maps S->E->N->W, i.e. direction index d -> d - 1.
func _fit(mask: Array, tiles: Dictionary) -> Array:
	for tile in tiles:
		var base: Array = tiles[tile]
		if base.size() != mask.size():
			continue
		for turns in 4:
			var rotated := base.map(func(d: int) -> int: return (d + 4 - turns) % 4)
			if rotated.all(func(d: int) -> bool: return d in mask):
				return [tile, turns]
	return ["grass_1", 0]


# --- structures ----------------------------------------------------------------------------
func _find(ch: String) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for row in size.y:
		for col in size.x:
			if layout[row][col] == ch:
				out.append(Vector2i(col, row))
	return out


## Yaw that turns the model front (+Z) toward `direction`.
static func _yaw_toward(direction: Vector3) -> float:
	return snappedf(atan2(direction.x, direction.z), PI / 2.0)


func _instance(path: String, at: Vector3, yaw := 0.0, scale_factor := 1.0) -> Node3D:
	var node: Node3D = load(path).instantiate()
	add_child(node)
	node.position = at
	node.rotation.y = yaw
	node.scale = Vector3.ONE * scale_factor
	FantasyMaterials.apply(node)
	return node


func _play_idle(node: Node3D) -> AnimationPlayer:
	var anim: AnimationPlayer = node.find_child("AnimationPlayer", true, false)
	anim.get_animation(&"Idle").loop_mode = Animation.LOOP_LINEAR
	anim.play(&"Idle")
	return anim


func _place_portal() -> void:
	var start := _find("S")[0]
	var toward := Vector3.FORWARD
	for d in DIRS:
		if is_road(start + d):
			toward = Vector3(d.x, 0, d.y)
	portal = _instance("res://models/structures/portal.glb", cell_center(start), _yaw_toward(toward))
	_portal_anim = _play_idle(portal)
	var material := ShaderMaterial.new()
	material.shader = VORTEX_SHADER
	for side in [1.0, -1.0]:  # a quad on each face of the arch's dark disc
		var vortex := MeshInstance3D.new()
		var quad := QuadMesh.new()
		quad.size = Vector2(1.62, 1.62)
		vortex.mesh = quad
		vortex.material_override = material
		vortex.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		vortex.position = Vector3(0.0, 1.25, 0.03 * side)
		vortex.rotation.y = 0.0 if side > 0.0 else PI
		portal.add_child(vortex)


func _place_castle() -> void:
	var cells := _find("C")
	for c in cells:
		castle_center += cell_center(c)
	castle_center /= cells.size()
	var toward := Vector3.FORWARD
	for c in cells:
		for d in DIRS:
			if _is_gate(c) and is_road(c + d):
				toward = Vector3(d.x, 0, d.y)
	castle = _instance("res://models/structures/castle.glb", castle_center, _yaw_toward(toward))
	_castle_flags = WindFlags.new(castle)
	_play_idle(castle)


# --- routes ------------------------------------------------------------------------------
## Every simple road path from the portal to the castle gate (cell lists). Forks multiply the count:
## two forks with two branches each give four routes.
func route_cells() -> Array:
	var start := _find("S")[0]
	var found := []
	_walk(start, {start: true}, [start], found)
	found.sort_custom(func(a: Array, b: Array) -> bool: return a.size() < b.size())
	return found


func _walk(cell: Vector2i, seen: Dictionary, path: Array, found: Array) -> void:
	if found.size() >= MAX_ROUTES:
		return
	if _at_gate(cell):
		found.append(path.duplicate())
		return
	for d in DIRS:
		var next := cell + d
		if is_road(next) and not seen.has(next):
			seen[next] = true
			path.append(next)
			_walk(next, seen, path, found)
			path.pop_back()
			seen.erase(next)


func _build_routes() -> void:
	routes.clear()
	for cells in route_cells():
		routes.append(_curve_through(cells))
	if routes.is_empty():
		push_error("Map: no road leads from the portal to the castle gate")


## Smooth path through the given road cells: straight through the middle of the tiles, quarter
## arcs through corners, then into the castle gate.
func _curve_through(cells: Array) -> Curve3D:
	var curve := Curve3D.new()
	curve.bake_interval = 0.2
	var centers := cells.map(cell_center)
	curve.add_point(centers[0])
	for i in range(1, cells.size()):
		var entry: Vector3 = (centers[i - 1] + centers[i]) / 2.0
		curve.add_point(entry)
		if i + 1 < cells.size():
			var exit: Vector3 = (centers[i] + centers[i + 1]) / 2.0
			var a: Vector3 = entry - centers[i]
			var b: Vector3 = exit - centers[i]
			if a.dot(b) > -0.5:  # a corner: follow the tile's quarter arc around the inner corner
				var pivot: Vector3 = centers[i] + a + b
				for t in [0.25, 0.5, 0.75]:
					curve.add_point(pivot + (entry - pivot).slerp(exit - pivot, t))
	var last: Vector3 = centers[-1]
	for d in DIRS:
		if _is_gate(cells[-1] + d):
			curve.add_point(last + Vector3(d.x, 0, d.y) * (CELL / 2.0 + 0.4))
	return curve


# --- decorations ---------------------------------------------------------------------------
func _near_road(cell: Vector2i) -> bool:
	for d in DIRS:
		if is_road(cell + d):
			return true
	return false


func _near_castle(cell: Vector2i) -> bool:
	for dx in range(-1, 2):
		for dy in range(-1, 2):
			if char_at(cell + Vector2i(dx, dy)) == "C":
				return true
	return false


func _prop(prop: String, cell: Vector2i, rng: RandomNumberGenerator, spread := 0.55) -> void:
	var offset := Vector3(rng.randf_range(-spread, spread), 0, rng.randf_range(-spread, spread))
	_instance("res://models/props/%s.glb" % prop, cell_center(cell) + offset, rng.randf() * TAU,
			rng.randf_range(0.85, 1.15))


func _place_decor(rng: RandomNumberGenerator) -> void:
	var castle_props := CASTLE_PROPS.duplicate()
	for row in size.y:
		for col in size.x:
			var cell := Vector2i(col, row)
			match char_at(cell):
				"T":
					for i in rng.randi_range(1, 3):
						_prop(TREES[rng.randi() % TREES.size()], cell, rng)
				"r":
					_prop(["rock_3", "rock_2"][rng.randi() % 2], cell, rng, 0.3)
					_prop(SMALL_PROPS[rng.randi() % SMALL_PROPS.size()], cell, rng)
				".":
					if _near_castle(cell) and not castle_props.is_empty() and rng.randf() < 0.6:
						_prop(castle_props.pop_back(), cell, rng, 0.35)
					elif _near_road(cell):
						if rng.randf() < 0.12:
							_prop("lamppost", cell, rng, 0.3)
					elif rng.randf() < 0.3:
						_prop(SMALL_PROPS[rng.randi() % SMALL_PROPS.size()], cell, rng)
