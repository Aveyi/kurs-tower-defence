class_name FantasyMaterials
extends RefCounted
## Replaces the materials of the generated glTF models (named Body / Metal / Glow / Foliage / Water
## by tools/blender/lowpoly.py) with the project's stylized shaders, and drives the per-instance
## magical effects declared in shaders/include/fx.gdshaderinc.

const TOON := preload("res://shaders/toon.gdshader")
const GROUND := preload("res://shaders/ground.gdshader")
const GLOW := preload("res://shaders/toon_glow.gdshader")
const FOLIAGE := preload("res://shaders/foliage.gdshader")
const WATER := preload("res://shaders/water.gdshader")

## Fully built / not dissolved (see fx_reveal_y in fx.gdshaderinc).
const REVEAL_NONE := 100000.0

static var _cache := {}  # imported Material -> ShaderMaterial (null when not ours)


## Swaps the materials of every mesh under `root` (instances keep sharing the converted materials).
static func apply(root: Node) -> void:
	for node in root.find_children("*", "MeshInstance3D", true, false):
		var mesh_instance := node as MeshInstance3D
		for i in mesh_instance.mesh.get_surface_count():
			var replacement := material_for(mesh_instance.mesh.surface_get_material(i))
			if replacement:
				mesh_instance.set_surface_override_material(i, replacement)


## Swaps the materials stored in a mesh itself (meshes used by a GridMap's MeshLibrary).
## `terrain` gives the "Body" surface the ground shader (world-space grass patches).
static func apply_to_mesh(mesh: Mesh, terrain := false) -> void:
	for i in mesh.get_surface_count():
		var replacement := material_for(mesh.surface_get_material(i), terrain)
		if replacement:
			mesh.surface_set_material(i, replacement)


static func material_for(source: Material, terrain := false) -> Material:
	if source == null:
		return null
	if _cache.has(source):
		return _cache[source]
	var material := ShaderMaterial.new()
	match source.resource_name:
		"Body":
			material.shader = GROUND if terrain else TOON
		"Metal":
			material.shader = TOON
			material.set_shader_parameter(&"metallic", 0.4)
			material.set_shader_parameter(&"roughness", 0.32)
			material.set_shader_parameter(&"specular", 0.5)
			material.set_shader_parameter(&"highlight_strength", 1.2)
			material.set_shader_parameter(&"rim_strength", 0.5)
		"Glow":
			var base := source as BaseMaterial3D
			material.shader = GLOW
			material.set_shader_parameter(&"glow_color", base.emission)
			material.set_shader_parameter(&"glow_energy", base.emission_energy_multiplier)
		"Foliage":
			material.shader = FOLIAGE
			material.set_shader_parameter(&"translucency", 0.6)
			material.set_shader_parameter(&"rim_strength", 0.2)
		"Water":
			material.shader = WATER
		_:
			material = null
	_cache[source] = material
	return material


## Sets an fx_* instance parameter on every mesh under `root`.
static func set_fx(root: Node, param: StringName, value: float) -> void:
	if not is_instance_valid(root):
		return
	for node in root.find_children("*", "GeometryInstance3D", true, false):
		(node as GeometryInstance3D).set_instance_shader_parameter(param, value)


## Tweens an fx_* parameter from `from` to `to` on every mesh under `root`.
static func tween_fx(tween: Tween, root: Node, param: StringName, from: float, to: float, duration: float) -> MethodTweener:
	return tween.tween_method(func(v: float) -> void: set_fx(root, param, v), from, to, duration)


## World-space top of all meshes under `root` (rest pose).
static func top_of(root: Node3D) -> float:
	var top := root.global_position.y
	for node in root.find_children("*", "MeshInstance3D", true, false):
		var mesh_instance := node as MeshInstance3D
		top = maxf(top, (mesh_instance.global_transform * mesh_instance.get_aabb()).end.y)
	return top
