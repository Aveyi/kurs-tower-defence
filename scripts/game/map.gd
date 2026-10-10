class_name Map
extends Node3D
## Builds the level from LevelData.layout with the tiles and decorations of LevelData.map_theme:
## - tiles, road and river ones auto-picked and rotated from their neighbours;
## - a fenced cemetery with gates where roads enter it;
## - the enemy portals ("S" open from the start, "s" sealed until open_portal()), the castle and decorations;
## - one enemy route (Curve3D) for every way along the road network from each portal to the
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
## Small flat props that need not cast shadows. Tiles cast shadows only when listed in the theme's
## shadow_tiles; flat ground only receives them (saves the shadow passes).
const NO_SHADOW_PROPS: Array[String] = ["mushrooms", "glow_mushrooms", "bones"]
const VORTEX_SHADER := preload("res://shaders/portal_vortex.gdshader")
## Safety limit for route enumeration on badly designed maps (road grids explode combinatorially).
const MAX_ROUTES := 32

## A sealed portal opened (the HUD announces it).
signal portal_opened(index: int)
## A sealed portal stirs: it will open with the next wave.
signal portal_stirring(index: int)

var layout: PackedStringArray
var size := Vector2i.ZERO
var theme: MapTheme
## Enemy routes from the portals to the castle: the first portal's routes first, shortest first.
var routes: Array[Curve3D] = []
## Index into `portals` of the portal each route starts at.
var route_portal: Array[int] = []
## Portals in order: the "S" ones, then the sealed "s" ones; `portal` is the first.
var portals: Array[Node3D] = []
var portal_open: Array[bool] = []
var portal: Node3D
var castle: Node3D
var castle_center := Vector3.ZERO

## Tiles and props are drawn in batches: one MultiMesh per model instead of hundreds of nodes.
var _batches := {}  # model path -> [mesh, mesh offset, cast shadows, Array[Transform3D]]
var _gate_column := -1
var _portal_anims: Array[AnimationPlayer] = []
var _vortices: Array = []  # per portal: its two vortex quads
var _castle_flags: WindFlags
var _last_portal_fx := {}  # portal index -> msec
var _landmark_bag: Array = []
## Props placed so far with their transforms, for point lights (prop name -> Array[Transform3D]).
var _placed := {}


func build(level: LevelData) -> void:
	layout = level.layout
	theme = level.map_theme if level.map_theme else MapTheme.new()
	size = Vector2i(layout[0].length(), layout.size())
	var columns := _find("C").map(func(c: Vector2i) -> int: return c.x)
	if not columns.is_empty():
		_gate_column = (columns.min() + columns.max()) / 2
	var rng := RandomNumberGenerator.new()
	rng.seed = level.decor_seed
	for row in size.y:
		for col in size.x:
			_place_tile(Vector2i(col, row), rng)
	_place_portals()
	_place_castle()
	_place_cemetery()
	_build_routes()
	_place_decor(rng)
	_flush_batches()


# --- queries -------------------------------------------------------------------------------
func char_at(cell: Vector2i) -> String:
	if cell.x < 0 or cell.y < 0 or cell.x >= size.x or cell.y >= size.y:
		return " "
	return layout[cell.y][cell.x]


func is_road(cell: Vector2i) -> bool:
	return char_at(cell) in ["#", "=", "S", "s"]


func is_river(cell: Vector2i) -> bool:
	return char_at(cell) in ["~", "="]


func is_plot(cell: Vector2i) -> bool:
	return char_at(cell) == "P"


func is_cemetery(cell: Vector2i) -> bool:
	return char_at(cell) == "G"


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


func play_portal_spawn(index := 0) -> void:
	var now := Time.get_ticks_msec()
	if now - int(_last_portal_fx.get(index, -100000)) < 700:
		return
	_last_portal_fx[index] = now
	_portal_anims[index].play(&"Spawn")
	_portal_anims[index].queue(&"Idle")
	Effects.burst(self, &"portal", portals[index].global_position + Vector3.UP * 1.25)
	Audio.play(&"portal_spawn", -6.0, 0.7)


## A sealed portal that opens with the next wave stirs: sparks, falling stones, a faint light.
func stir_portal(index: int) -> void:
	if portal_open[index]:
		return
	var at := portals[index].global_position + Vector3.UP * 1.25
	Effects.burst(self, &"portal", at, 1.2)
	Effects.burst(self, &"debris", portals[index].global_position + Vector3.UP * 0.3, 0.6)
	Audio.play(&"portal_spawn", -2.0)
	portal_stirring.emit(index)


## Opens a sealed portal: the vortex flares up and enemies may come out of it from now on.
func open_portal(index: int) -> void:
	if portal_open[index]:
		return
	portal_open[index] = true
	var anim := _portal_anims[index]
	anim.play(&"Spawn")
	anim.queue(&"Idle")
	for vortex: MeshInstance3D in _vortices[index]:
		vortex.visible = true
		vortex.scale = Vector3.ONE * 0.05
		create_tween().tween_property(vortex, "scale", Vector3.ONE, 0.8).set_trans(Tween.TRANS_BACK) \
				.set_ease(Tween.EASE_OUT)
	var at := portals[index].global_position + Vector3.UP * 1.25
	Effects.impact(self, at, Color(0.75, 0.3, 1.0), 2.0)
	Effects.burst(self, &"portal", at, 2.0)
	Effects.burst(self, &"debris", portals[index].global_position + Vector3.UP * 0.3, 1.2)
	Audio.play(&"summon")
	portal_opened.emit(index)


# --- tiles ---------------------------------------------------------------------------------
func _place_tile(cell: Vector2i, rng: RandomNumberGenerator) -> void:
	var tile := "grass_%d" % [1, 1, 2, 3][rng.randi() % 4]
	var turns := rng.randi() % 4
	match char_at(cell):
		"#", "S", "s":
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
		"G":
			if not theme.cemetery_tiles.is_empty():
				tile = theme.cemetery_tiles[rng.randi() % theme.cemetery_tiles.size()]
				turns = 0  # the graves face south
	if not tile in theme.cemetery_tiles:
		tile = _themed_tile(tile)
	_batch("tile:" + tile, TileLibrary.tile(tile), tile in theme.shadow_tiles,
			Transform3D(Basis(Vector3.UP, turns * PI / 2.0), cell_center(cell)))


## The theme's version of a tile, or the plain one when the set has none.
func _themed_tile(base: String) -> String:
	var themed := theme.tile_prefix + base
	if theme.tile_prefix.is_empty() or ResourceLoader.exists("res://models/tiles/%s.glb" % themed):
		return themed
	return base


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


## Portal cells in index order: the open "S" ones, then the sealed "s" ones.
func portal_cells() -> Array[Vector2i]:
	return _find("S") + _find("s")


func _place_portals() -> void:
	var material := ShaderMaterial.new()
	material.shader = VORTEX_SHADER
	for start in portal_cells():
		var toward := Vector3.FORWARD
		for d in DIRS:
			if is_road(start + d):
				toward = Vector3(d.x, 0, d.y)
		var node := _instance("res://models/structures/portal.glb", cell_center(start), _yaw_toward(toward))
		var anim := _play_idle(node)
		var quads := []
		for side in [1.0, -1.0]:  # a quad on each face of the arch's dark disc
			var vortex := MeshInstance3D.new()
			var quad := QuadMesh.new()
			quad.size = Vector2(1.62, 1.62)
			vortex.mesh = quad
			vortex.material_override = material
			vortex.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			vortex.position = Vector3(0.0, 1.25, 0.03 * side)
			vortex.rotation.y = 0.0 if side > 0.0 else PI
			node.add_child(vortex)
			quads.append(vortex)
		var sealed := char_at(start) == "s"
		if sealed:  # a dead arch: no vortex, the swirl shrunk away, only the runes glow
			anim.stop()
			var skeleton: Skeleton3D = node.find_child("Skeleton3D", true, false)
			skeleton.set_bone_pose_scale(skeleton.find_bone("pulse"), Vector3.ONE * 0.01)
			for vortex: MeshInstance3D in quads:
				vortex.visible = false
		portals.append(node)
		portal_open.append(not sealed)
		_portal_anims.append(anim)
		_vortices.append(quads)
	portal = portals[0]


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


# --- cemetery ----------------------------------------------------------------------------
## A fence along every border edge of the cemetery ("G" cells) and a gate where a road enters it: on the
## edge between a road cell walled in by graves on both sides and the next road cell outside.
func _place_cemetery() -> void:
	if theme.cemetery_fence.is_empty():
		return
	for cell in _find("G"):
		for d in DIRS:
			if not is_cemetery(cell + d):
				_edge_prop(theme.cemetery_fence, cell, d, CELL / 2.0)
	if theme.cemetery_gate.is_empty():
		return
	for cell in _find("#"):
		for along in DIRS:
			if _in_cemetery_lane(cell, along):
				var next := cell + along
				if is_road(next) and not _in_cemetery_lane(next, along):
					_edge_prop(theme.cemetery_gate, cell, along, CELL / 2.0)


## A road cell running along `along` with graves on both sides of it.
func _in_cemetery_lane(cell: Vector2i, along: Vector2i) -> bool:
	var side := Vector2i(along.y, along.x)
	return is_road(cell) and is_cemetery(cell + side) and is_cemetery(cell - side)


## A prop standing on the edge of `cell` toward `d`, its X axis along the edge.
func _edge_prop(prop: String, cell: Vector2i, d: Vector2i, distance: float) -> void:
	var at := cell_center(cell) + Vector3(d.x, 0, d.y) * distance
	var yaw := 0.0 if d.y != 0 else PI / 2.0
	_batch("prop:" + prop, TileLibrary.prop(prop), true, Transform3D(Basis(Vector3.UP, yaw), at))


# --- routes ------------------------------------------------------------------------------
## Every simple road path from a portal (default: the first) to the castle gate (cell lists). Forks
## multiply the count: two forks with two branches each give four routes.
func route_cells(start := Vector2i(-1, -1)) -> Array:
	if start.x < 0:
		start = portal_cells()[0]
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
	route_portal.clear()
	var starts := portal_cells()
	for i in starts.size():
		var cells_list := route_cells(starts[i])
		if cells_list.is_empty():
			push_error("Map: no road leads from the portal at %s to the castle gate" % starts[i])
		for cells in cells_list:
			routes.append(_curve_through(cells))
			route_portal.append(i)


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


# --- lighting ------------------------------------------------------------------------------
## Point lights at every placed prop listed in the theme's prop_lights (night levels).
func add_prop_lights() -> void:
	for prop in theme.prop_lights:
		var spec: Array = theme.prop_lights[prop]
		for at: Transform3D in _placed.get(prop, []):
			add_light(at * (spec[0] as Vector3), spec[1], spec[2], spec[3])


func add_light(at: Vector3, color: Color, energy: float, light_range: float) -> OmniLight3D:
	var light := OmniLight3D.new()
	light.light_color = color
	light.light_energy = energy
	light.omni_range = light_range
	light.omni_attenuation = 1.6
	light.light_specular = 0.2
	light.shadow_enabled = false
	add_child(light)
	light.position = at
	return light


## Sets a parameter of the ground shader on this map's tiles (night grass colours).
func set_ground_parameter(param: StringName, value: Variant) -> void:
	for node in get_children():
		if node is MultiMeshInstance3D and node.name.begins_with("tile_"):
			var mesh: Mesh = node.multimesh.mesh
			for i in mesh.get_surface_count():
				var material := mesh.surface_get_material(i) as ShaderMaterial
				if material and material.shader == FantasyMaterials.GROUND:
					material.set_shader_parameter(param, value)


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
	var basis := Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * rng.randf_range(0.85, 1.15))
	_batch("prop:" + prop, TileLibrary.prop(prop), not prop in NO_SHADOW_PROPS,
			Transform3D(basis, cell_center(cell) + offset))


func _batch(key: String, model: Array, cast_shadow: bool, at: Transform3D) -> void:
	if key.begins_with("prop:"):
		_placed.get_or_add(key.substr(5), []).append(at)
	if not _batches.has(key):
		_batches[key] = [model[0], model[1], cast_shadow, []]
	_batches[key][3].append(at * model[1])


func _flush_batches() -> void:
	for key in _batches:
		var batch: Array = _batches[key]
		var multimesh := MultiMesh.new()
		multimesh.transform_format = MultiMesh.TRANSFORM_3D
		multimesh.mesh = batch[0]
		multimesh.instance_count = batch[3].size()
		for i in batch[3].size():
			multimesh.set_instance_transform(i, batch[3][i])
		var instance := MultiMeshInstance3D.new()
		instance.name = key.replace(":", "_")
		instance.multimesh = multimesh
		instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if batch[2] \
				else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(instance)
	_batches.clear()


func _place_decor(rng: RandomNumberGenerator) -> void:
	var castle_props := Array(theme.castle_props)
	var trees := theme.trees
	var small := theme.small_props
	for row in size.y:
		for col in size.x:
			var cell := Vector2i(col, row)
			match char_at(cell):
				"T":
					for i in rng.randi_range(1, 3):
						_prop(trees[rng.randi() % trees.size()], cell, rng)
				"t":
					_prop(trees[rng.randi() % trees.size()], cell, rng, 0.35)
				"r":
					_prop(theme.rocks[rng.randi() % theme.rocks.size()], cell, rng, 0.3)
					_prop(small[rng.randi() % small.size()], cell, rng)
				"R":
					_place_landmark(cell, rng)
				".":
					if _near_castle(cell) and not castle_props.is_empty() and rng.randf() < 0.6:
						_prop(castle_props.pop_back(), cell, rng, 0.35)
					elif _near_road(cell):
						if rng.randf() < 0.12:
							_prop(theme.road_light, cell, rng, 0.3)
					elif rng.randf() < 0.3:
						_prop(small[rng.randi() % small.size()], cell, rng)


## One big piece per landmark cell ("R"): all of the theme's landmarks in random order before any repeats,
## turned square to the grid.
func _place_landmark(cell: Vector2i, rng: RandomNumberGenerator) -> void:
	if theme.landmarks.is_empty():
		_prop(theme.small_props[rng.randi() % theme.small_props.size()], cell, rng)
		return
	if _landmark_bag.is_empty():
		_landmark_bag = Array(theme.landmarks)
		for i in range(_landmark_bag.size() - 1, 0, -1):  # Fisher-Yates with the decor seed
			var j := rng.randi_range(0, i)
			var swap: Variant = _landmark_bag[i]
			_landmark_bag[i] = _landmark_bag[j]
			_landmark_bag[j] = swap
	var prop: String = _landmark_bag.pop_back()
	var offset := Vector3(rng.randf_range(-0.15, 0.15), 0, rng.randf_range(-0.15, 0.15))
	_batch("prop:" + prop, TileLibrary.prop(prop), true,
			Transform3D(Basis(Vector3.UP, (rng.randi() % 4) * PI / 2.0), cell_center(cell) + offset))
