class_name Effects
extends RefCounted
## Procedural visual effects: GPU particle bursts and trails, flashes, floating text.
## No textures are loaded: particles use a generated soft-dot texture, colours above 1.0 feed the glow.

## Particle presets. Keys:
##   amount, lifetime, colors (gradient over the lifetime), speed [min, max], dir + spread (degrees),
##   gravity, damping, size [min, max], curve ("grow" | "shrink" | "pop"), radius (emission sphere),
##   additive (bright light) or alpha-blended (smoke, dust), swirl (tangential acceleration),
##   mesh = "chunk" for solid debris instead of billboards.
const PRESETS := {
	&"dust": {amount = 10, lifetime = 0.7, colors = [Color(0.78, 0.68, 0.52, 0.7), Color(0.62, 0.56, 0.46, 0.0)],
			speed = [0.5, 1.6], dir = Vector3.UP, spread = 75.0, gravity = Vector3(0, -0.8, 0), damping = 1.5,
			size = [0.25, 0.5], curve = "grow", radius = 0.15},
	&"fire": {amount = 18, lifetime = 0.45, colors = [Color(3.0, 2.0, 0.8), Color(2.2, 0.8, 0.2, 0.8), Color(0.3, 0.1, 0.05, 0.0)],
			speed = [2.0, 4.5], dir = Vector3.UP, spread = 180.0, gravity = Vector3.ZERO, damping = 7.0,
			size = [0.5, 0.9], curve = "shrink", radius = 0.3, additive = true},
	&"smoke": {amount = 14, lifetime = 1.5, colors = [Color(0.24, 0.21, 0.19, 0.75), Color(0.42, 0.4, 0.37, 0.0)],
			speed = [1.0, 2.5], dir = Vector3.UP, spread = 80.0, gravity = Vector3(0, 0.7, 0), damping = 2.0,
			size = [0.7, 1.3], curve = "grow", radius = 0.4},
	&"sparks": {amount = 24, lifetime = 0.6, colors = [Color(3.0, 2.2, 1.0), Color(2.0, 0.8, 0.2, 0.0)],
			speed = [4.0, 8.0], dir = Vector3.UP, spread = 180.0, gravity = Vector3(0, -9.0, 0), damping = 0.5,
			size = [0.05, 0.1], curve = "shrink", radius = 0.1, additive = true},
	&"magic": {amount = 14, lifetime = 0.55, colors = [Color(1.3, 0.7, 2.0), Color(0.6, 0.25, 1.1, 0.0)],
			speed = [2.0, 4.0], dir = Vector3.UP, spread = 180.0, gravity = Vector3.ZERO, damping = 4.0,
			size = [0.12, 0.25], curve = "shrink", radius = 0.1, additive = true},
	&"frost": {amount = 14, lifetime = 0.7, colors = [Color(1.0, 1.6, 2.0), Color(0.4, 0.8, 1.2, 0.0)],
			speed = [1.5, 3.5], dir = Vector3.UP, spread = 180.0, gravity = Vector3(0, -3.0, 0), damping = 1.0,
			size = [0.1, 0.22], curve = "shrink", radius = 0.15, additive = true},
	&"death": {amount = 12, lifetime = 1.0, colors = [Color(0.5, 0.48, 0.42, 0.7), Color(0.55, 0.5, 0.45, 0.0)],
			speed = [0.5, 1.5], dir = Vector3.UP, spread = 60.0, gravity = Vector3(0, 0.3, 0), damping = 1.0,
			size = [0.4, 0.8], curve = "grow", radius = 0.3},
	&"souls": {amount = 10, lifetime = 1.5, colors = [Color(1.2, 2.6, 2.0), Color(0.3, 1.0, 0.8, 0.0)],
			speed = [0.5, 1.2], dir = Vector3.UP, spread = 25.0, gravity = Vector3(0, 1.2, 0), damping = 0.5,
			size = [0.15, 0.3], curve = "pop", radius = 0.35, additive = true},
	&"portal": {amount = 26, lifetime = 0.9, colors = [Color(2.4, 0.8, 3.0), Color(0.8, 0.2, 1.2, 0.0)],
			speed = [0.3, 1.0], dir = Vector3.UP, spread = 180.0, gravity = Vector3.ZERO, damping = 1.0,
			size = [0.12, 0.25], curve = "pop", radius = 0.7, additive = true, swirl = 6.0},
	&"gold": {amount = 20, lifetime = 1.0, colors = [Color(3.0, 2.4, 0.8), Color(1.6, 1.0, 0.2, 0.0)],
			speed = [1.0, 3.0], dir = Vector3.UP, spread = 50.0, gravity = Vector3(0, -2.0, 0), damping = 1.0,
			size = [0.08, 0.16], curve = "pop", radius = 0.5, additive = true},
	&"debris": {amount = 12, lifetime = 1.2, colors = [Color(0.6, 0.57, 0.52), Color(0.5, 0.47, 0.42)],
			speed = [3.0, 6.0], dir = Vector3.UP, spread = 60.0, gravity = Vector3(0, -12.0, 0), damping = 0.2,
			size = [0.6, 1.2], curve = "none", radius = 0.3, mesh = "chunk"},
	&"puff": {amount = 8, lifetime = 0.9, colors = [Color(0.85, 0.82, 0.78, 0.7), Color(0.7, 0.68, 0.65, 0.0)],
			speed = [0.8, 2.0], dir = Vector3.FORWARD, spread = 35.0, gravity = Vector3(0, 0.6, 0), damping = 2.5,
			size = [0.25, 0.5], curve = "grow", radius = 0.1},
	# continuous trails behind projectiles
	&"trail_magic": {amount = 30, lifetime = 0.4, colors = [Color(1.1, 0.55, 1.7), Color(0.5, 0.2, 1.0, 0.0)],
			speed = [0.1, 0.4], dir = Vector3.UP, spread = 180.0, gravity = Vector3.ZERO, damping = 0.0,
			size = [0.1, 0.2], curve = "shrink", radius = 0.08, additive = true, trail = true},
	&"trail_frost": {amount = 30, lifetime = 0.35, colors = [Color(0.9, 1.4, 1.8), Color(0.4, 0.8, 1.2, 0.0)],
			speed = [0.1, 0.3], dir = Vector3.UP, spread = 180.0, gravity = Vector3(0, -1.0, 0), damping = 0.0,
			size = [0.07, 0.14], curve = "shrink", radius = 0.05, additive = true, trail = true},
	&"trail_smoke": {amount = 30, lifetime = 0.6, colors = [Color(0.45, 0.42, 0.4, 0.55), Color(0.5, 0.48, 0.45, 0.0)],
			speed = [0.1, 0.3], dir = Vector3.UP, spread = 180.0, gravity = Vector3(0, 0.4, 0), damping = 0.0,
			size = [0.12, 0.25], curve = "grow", radius = 0.04, trail = true},
}

static var _process_materials := {}
static var _draw_meshes := {}
static var _sphere: SphereMesh
static var _label_font: Font = preload("res://assets/fonts/title_font.tres")


## One-shot particle burst at `at`. `direction` turns the preset's main direction (e.g. a muzzle).
static func burst(parent: Node, preset: StringName, at: Vector3, scale := 1.0, direction := Vector3.ZERO) -> GPUParticles3D:
	var particles := _make(preset)
	parent.add_child(particles)
	particles.global_position = at
	if direction != Vector3.ZERO:
		particles.global_basis = Basis.looking_at(direction.normalized(),
				Vector3.UP if absf(direction.normalized().y) < 0.99 else Vector3.RIGHT)
	particles.scale = Vector3.ONE * scale
	particles.amount = maxi(1, roundi(particles.amount * clampf(scale, 0.5, 2.0)))
	particles.emitting = true
	parent.get_tree().create_timer(particles.lifetime + 0.5, false).timeout.connect(particles.queue_free)
	return particles


## A continuous trail that follows `node`; call release_trail() when the node goes away.
static func trail(node: Node3D, preset: StringName) -> GPUParticles3D:
	var particles := _make(preset)
	node.add_child(particles)
	particles.emitting = true
	return particles


## Leaves a trail in the world to fade out after its owner has been freed.
static func release_trail(particles: GPUParticles3D, world: Node) -> void:
	if particles == null or not is_instance_valid(particles):
		return
	particles.reparent(world)
	particles.emitting = false
	world.get_tree().create_timer(particles.lifetime + 0.3, false).timeout.connect(particles.queue_free)


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
	material.albedo_color = Color(color.r * 1.3, color.g * 1.3, color.b * 1.3, 0.55)  # >1 feeds the glow
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


## Text rising from a point and fading out (gold rewards).
static func floating_text(parent: Node, at: Vector3, text: String, color: Color) -> void:
	var label := Label3D.new()
	label.text = text
	label.font = _label_font
	label.font_size = 60
	label.outline_size = 14
	label.pixel_size = 0.006
	label.modulate = color
	label.outline_modulate = Color(0.1, 0.06, 0.02)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.no_depth_test = true
	label.render_priority = 10
	parent.add_child(label)
	label.global_position = at
	var tween := label.create_tween().set_parallel()
	tween.tween_property(label, "position:y", label.position.y + 1.1, 1.0).set_ease(Tween.EASE_OUT)
	tween.tween_property(label, "modulate:a", 0.0, 0.45).set_delay(0.55)
	tween.chain().tween_callback(label.queue_free)


## Compiles every preset once (off-screen) so the first explosion in a battle does not stutter.
static func prewarm(parent: Node) -> void:
	for preset in PRESETS:
		var particles := _make(preset)
		parent.add_child(particles)
		particles.position = Vector3(0, -50, 0)
		particles.emitting = true
		parent.get_tree().create_timer(0.3, false).timeout.connect(particles.queue_free)


# --- construction -------------------------------------------------------------------------
static func _make(preset: StringName) -> GPUParticles3D:
	var p: Dictionary = PRESETS[preset]
	var particles := GPUParticles3D.new()
	particles.amount = p.amount
	particles.lifetime = p.lifetime
	particles.one_shot = not p.get("trail", false)
	particles.explosiveness = 0.0 if p.get("trail", false) else 0.95
	particles.local_coords = false
	particles.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if p.get("mesh", "") == "chunk" \
			else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	particles.visibility_aabb = AABB(Vector3(-6, -6, -6), Vector3(12, 12, 12))
	particles.process_material = _process_material(preset, p)
	particles.draw_pass_1 = _draw_mesh(p)
	return particles


static func _process_material(preset: StringName, p: Dictionary) -> ParticleProcessMaterial:
	if _process_materials.has(preset):
		return _process_materials[preset]
	var m := ParticleProcessMaterial.new()
	m.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	m.emission_sphere_radius = p.radius
	m.direction = p.dir
	m.spread = p.spread
	m.initial_velocity_min = p.speed[0]
	m.initial_velocity_max = p.speed[1]
	m.gravity = p.gravity
	m.damping_min = p.damping
	m.damping_max = p.damping
	m.scale_min = p.size[0]
	m.scale_max = p.size[1]
	if p.has("swirl"):
		m.tangential_accel_min = p.swirl
		m.tangential_accel_max = p.swirl
	if p.get("mesh", "") == "chunk":
		m.particle_flag_rotate_y = true
		m.angular_velocity_min = -360.0
		m.angular_velocity_max = 360.0
	else:
		m.angle_min = -180.0
		m.angle_max = 180.0
	var gradient := Gradient.new()
	var colors: Array = p.colors
	gradient.offsets = PackedFloat32Array(range(colors.size()).map(func(i: int) -> float: return float(i) / (colors.size() - 1)))
	gradient.colors = PackedColorArray(colors)
	var ramp := GradientTexture1D.new()
	ramp.gradient = gradient
	m.color_ramp = ramp
	if p.curve != "none":
		var curve := Curve.new()
		match p.curve:
			"grow":
				curve.add_point(Vector2(0, 0.4))
				curve.add_point(Vector2(1, 1))
			"shrink":
				curve.add_point(Vector2(0, 1))
				curve.add_point(Vector2(1, 0))
			"pop":
				curve.add_point(Vector2(0, 0))
				curve.add_point(Vector2(0.2, 1))
				curve.add_point(Vector2(1, 0))
		var curve_texture := CurveTexture.new()
		curve_texture.curve = curve
		m.scale_curve = curve_texture
	_process_materials[preset] = m
	return m


static func _draw_mesh(p: Dictionary) -> Mesh:
	var key := "chunk" if p.get("mesh", "") == "chunk" else ("add" if p.get("additive", false) else "mix")
	if _draw_meshes.has(key):
		return _draw_meshes[key]
	var material := StandardMaterial3D.new()
	material.vertex_color_use_as_albedo = true
	var mesh: PrimitiveMesh
	if key == "chunk":
		var box := BoxMesh.new()
		box.size = Vector3(0.12, 0.09, 0.1)
		mesh = box
	else:
		mesh = QuadMesh.new()
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		material.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
		material.albedo_texture = _soft_dot()
		if key == "add":
			material.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mesh.material = material
	_draw_meshes[key] = mesh
	return mesh


static func _soft_dot() -> Texture2D:
	var gradient := Gradient.new()
	gradient.offsets = PackedFloat32Array([0.0, 0.45, 1.0])
	gradient.colors = PackedColorArray([Color(1, 1, 1, 1), Color(1, 1, 1, 0.55), Color(1, 1, 1, 0)])
	var texture := GradientTexture2D.new()
	texture.gradient = gradient
	texture.fill = GradientTexture2D.FILL_RADIAL
	texture.fill_from = Vector2(0.5, 0.5)
	texture.fill_to = Vector2(0.5, 0.0)
	texture.width = 64
	texture.height = 64
	return texture
