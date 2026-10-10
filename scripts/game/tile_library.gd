class_name TileLibrary
extends RefCounted
## Static meshes for batched drawing (tiles and props): loads a model once, takes its mesh with
## the stylized materials applied, and remembers the mesh's offset inside the imported scene.

const TILES: Array[String] = [
	"grass_1", "grass_2", "grass_3", "road_straight", "road_corner", "road_t", "road_cross", "road_end",
	"river_straight", "river_corner", "bridge", "plot",
]

static var _cache := {}  # model path -> [Mesh, Transform3D]


static func tile(name: String) -> Array:
	return model("res://models/tiles/%s.glb" % name, true)


static func prop(name: String) -> Array:
	return model("res://models/props/%s.glb" % name)


## [mesh, transform of the mesh inside the model] for a single-mesh, unrigged model.
static func model(path: String, terrain := false) -> Array:
	if _cache.has(path):
		return _cache[path]
	var scene: Node3D = load(path).instantiate()
	var mesh_instance: MeshInstance3D = scene.find_children("*", "MeshInstance3D", true, false)[0]
	var xform := Transform3D.IDENTITY
	var node: Node = mesh_instance
	while node != scene:
		xform = (node as Node3D).transform * xform
		node = node.get_parent()
	FantasyMaterials.apply_to_mesh(mesh_instance.mesh, terrain)
	_cache[path] = [mesh_instance.mesh, xform]
	scene.free()
	return _cache[path]
