class_name TileLibrary
extends RefCounted
## Builds (once) the MeshLibrary used by the map GridMap from the tile models.

const TILES: Array[String] = [
	"grass_1", "grass_2", "grass_3", "road_straight", "road_corner", "road_t", "road_cross", "road_end",
	"river_straight", "river_corner", "bridge", "plot",
]

static var _library: MeshLibrary


static func get_library() -> MeshLibrary:
	if _library:
		return _library
	_library = MeshLibrary.new()
	for i in TILES.size():
		var scene: Node3D = load("res://models/tiles/%s.glb" % TILES[i]).instantiate()
		var mesh_instance: MeshInstance3D = scene.find_children("*", "MeshInstance3D", true, false)[0]
		var xform := Transform3D.IDENTITY
		var node: Node = mesh_instance
		while node != scene:
			xform = (node as Node3D).transform * xform
			node = node.get_parent()
		_library.create_item(i)
		_library.set_item_name(i, TILES[i])
		FantasyMaterials.apply_to_mesh(mesh_instance.mesh, true)
		_library.set_item_mesh(i, mesh_instance.mesh)
		_library.set_item_mesh_transform(i, xform)
		scene.free()
	return _library


static func id_of(tile: String) -> int:
	return TILES.find(tile)
