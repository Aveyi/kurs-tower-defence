class_name Effects
extends RefCounted
## Small procedural one-shot effects.

static var _sphere: SphereMesh


## A glowing sphere that quickly expands and fades out (hits, explosions).
static func impact(parent: Node, at: Vector3, color: Color, radius: float) -> void:
	if _sphere == null:
		_sphere = SphereMesh.new()
		_sphere.radius = 0.5
		_sphere.height = 1.0
		_sphere.radial_segments = 12
		_sphere.rings = 6
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.albedo_color = Color(color.r * 2.0, color.g * 2.0, color.b * 2.0, 0.85)  # >1 feeds the glow
	var flash := MeshInstance3D.new()
	flash.mesh = _sphere
	flash.material_override = material
	flash.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(flash)
	flash.global_position = at
	flash.scale = Vector3.ONE * 0.2
	var tween := flash.create_tween().set_parallel()
	tween.tween_property(flash, "scale", Vector3.ONE * radius * 2.0, 0.3) \
			.set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tween.tween_property(material, "albedo_color:a", 0.0, 0.3)
	tween.chain().tween_callback(flash.queue_free)
