"""Low-poly character toolkit for headless Blender.

A model is assembled from primitives (box / cylinder / segment / ball / ring / slab). Every
part is rigidly bound to one bone (100% weight) and coloured through a per-corner colour
attribute "Col". Materials:
  0 "Glow"  - flat glow colour + emission (eyes, crystals, magic) for bloom in Godot;
  1 "Body"  - base colour from vertex colours, matte;
  2 "Metal" - vertex colours, metallic (palette colours listed in `metal=`);
  3 "Foliage" - vertex colours, for leaves/grass (palette colours in `foliage=`), the wind shader target;
  4 "Water" - flat translucent colour (palette colour "water"), the water shader target.
Glow goes first on purpose: Godot 4.7's glTF importer does not enable vertex colours
for the first surface of a mesh (has_vertex_color is set after the material is
processed), so vertex-coloured materials must not be surface 0. Models without glowing
parts get an invisible 1 mm Glow triangle below the ground to keep that order.

On build, ambient occlusion is baked per face into the vertex colours (rays against the
model itself) plus a slight per-face brightness variance - the classic "rich low-poly" look.

Coordinate convention (Blender): Z up, character faces -Y, character's left = +X.
All bones point straight up (+Z) with zero roll, so bone-local axes match world:
  pitch - rotation about X (positive: limb end swings backward, torso leans forward,
          jaw/foot tip goes down)
  yaw   - rotation about vertical axis (positive: turn toward character's left)
  side  - rotation about Y (positive: top tilts toward character's left, so a hanging
          LEFT arm swings inward; raise it outward with a negative value)
"""
import math
import random

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector, geometry
from mathutils.bvhtree import BVHTree

SIDES = ((1, "L"), (-1, "R"))


def hex_to_linear(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def rots(*eulers):
    """Compose rotations (degrees, XYZ) applied in the given order; returns degrees."""
    m = Matrix.Identity(3)
    for e in eulers:
        m = Euler([math.radians(a) for a in e]).to_matrix() @ m
    return tuple(math.degrees(a) for a in m.to_euler())


def rag(x0, x1, top, bottom, teeth=3, depth=0.03):
    """Outline (x, z) of a cloth flap with a ragged bottom edge."""
    pts = [(x0, top), (x1, top)]
    k = teeth * 2
    for i in range(k + 1):
        z = bottom + (depth if i % 2 else 0.0) + 0.25 * depth * math.sin(i * 1.7)
        pts.append((x1 + (x0 - x1) * i / k, z))
    return pts


def clear_scene():
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.armatures, bpy.data.actions,
                 bpy.data.materials, bpy.data.cameras, bpy.data.lights, bpy.data.worlds):
        for item in list(coll):
            coll.remove(item)
    bpy.context.scene.render.fps = 24


def _make_material(name, emission=None, strength=0.0, roughness=0.85, metallic=0.0, flat=None, alpha=1.0):
    mat = bpy.data.materials.new(name)
    if hasattr(mat, "use_nodes"):
        mat.use_nodes = True
    mat.use_backface_culling = True
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        if hasattr(mat, "surface_render_method"):
            mat.surface_render_method = "BLENDED"
    if flat:
        bsdf.inputs["Base Color"].default_value = hex_to_linear(flat)
    elif not emission:
        vcol = nt.nodes.new("ShaderNodeVertexColor")
        vcol.layer_name = "Col"
        nt.links.new(vcol.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = hex_to_linear(emission)
        bsdf.inputs["Emission Color"].default_value = hex_to_linear(emission)
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def _hemisphere(n):
    """Cosine-weighted directions around +Z (golden spiral)."""
    out = []
    for i in range(n):
        u = (i + 0.5) / n
        r, phi = math.sqrt(u), i * 2.399963
        out.append(Vector((r * math.cos(phi), r * math.sin(phi), math.sqrt(max(0.0, 1 - u)))))
    return out


def _fcurves(action):
    """F-curves of an action (Blender 5 layered actions, with a fallback for older API)."""
    if hasattr(action, "layers"):
        return [fc for layer in action.layers for strip in layer.strips
                for bag in strip.channelbags for fc in bag.fcurves]
    return list(action.fcurves)


class Model:
    def __init__(self, name, palette, glow_color="#FFFFFF", glow_strength=4.0, metal=(), seed=1,
                 ao=0.45, ao_dist=None, variance=0.035, rig=True, foliage=()):
        self.name = name
        self.rig = rig
        self.foliage = set(foliage)
        self.pal = palette
        self.glow = (glow_color, glow_strength)
        self.metal = set(metal)
        self.ao, self.ao_dist, self.variance = ao, ao_dist, variance
        self.rng = random.Random(seed)
        self.bm = bmesh.new()
        self.dl = self.bm.verts.layers.deform.verify()
        self.cl = self.bm.loops.layers.float_color.new("Col")
        self.groups = {}
        self.bones = {}
        self.order = []
        self.obj = self.arm = None

    # --- skeleton ---------------------------------------------------------------
    def bone(self, name, head, parent=None):
        assert parent is None or parent in self.bones, parent
        self.bones[name] = (Vector(head), parent)
        self.order.append(name)

    # --- primitives -------------------------------------------------------------
    def _place(self, verts, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
        m = (Matrix.Translation(loc) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
             @ Matrix.Diagonal((*scale, 1.0)))
        bmesh.ops.transform(self.bm, matrix=m, verts=verts)

    def _paint(self, verts, bone, color, glow, jitter=0.0):
        assert bone in self.bones, bone
        verts = [v for v in verts if v.is_valid]
        if jitter:
            for v in verts:
                v.co += Vector([self.rng.uniform(-jitter, jitter) for _ in range(3)])
        gi = self.groups.setdefault(bone, len(self.groups))
        for v in verts:
            v[self.dl][gi] = 1.0
        col = hex_to_linear(self.pal.get(color, color))
        mat = self._mat(color, glow)
        for f in {f for v in verts for f in v.link_faces}:
            f.material_index = mat
            f.smooth = False
            for loop in f.loops:
                loop[self.cl] = col

    def _mat(self, color, glow=False):
        if glow:
            return 0
        if color == "water":
            return 4
        return 2 if color in self.metal else 3 if color in self.foliage else 1

    def paint_face(self, f, bone, color):
        """Colour a single hand-built face (used by terrain)."""
        gi = self.groups.setdefault(bone, len(self.groups))
        for v in f.verts:
            v[self.dl][gi] = 1.0
        f.material_index = self._mat(color)
        f.smooth = False
        col = hex_to_linear(self.pal.get(color, color))
        for loop in f.loops:
            loop[self.cl] = col

    def _finish(self, verts, bone, color, glow, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), jitter=0.0):
        verts = [v for v in verts if v.is_valid]
        self._place(verts, loc, rot, scale)
        self._paint(verts, bone, color, glow, jitter)

    def box(self, bone, color, loc, size, rot=(0, 0, 0), taper=1.0, bevel=0.0, glow=False, jitter=0.0):
        """Box of given size; `taper` scales the top (+Z) face, `bevel` chamfers edges (metres)."""
        verts = bmesh.ops.create_cube(self.bm, size=1.0)["verts"]
        if taper != 1.0:
            for v in verts:
                if v.co.z > 0:
                    v.co.x *= taper
                    v.co.y *= taper
        self._place(verts, loc, rot, size)
        if bevel:
            faces = list({f for v in verts for f in v.link_faces})
            edges = list({e for v in verts for e in v.link_edges})
            new = bmesh.ops.bevel(self.bm, geom=edges, offset=bevel, segments=1, profile=0.5,
                                  affect="EDGES", clamp_overlap=True)["faces"]
            verts = list({v for f in faces + new if f.is_valid for v in f.verts})
        self._paint(verts, bone, color, glow, jitter)

    def cyl(self, bone, color, loc, r, h, r2=None, n=6, rot=(0, 0, 0), squash=(1, 1), glow=False, jitter=0.0):
        """Cylinder/cone along local Z: radius `r` at the bottom, `r2` at the top (0 = cone tip)."""
        r2 = r if r2 is None else r2
        verts = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=n,
                                      radius1=r, radius2=r2, depth=h)["verts"]
        bmesh.ops.remove_doubles(self.bm, verts=verts, dist=1e-6)
        self._finish(verts, bone, color, glow, loc, rot, (squash[0], squash[1], 1.0), jitter)

    def seg(self, bone, color, p1, p2, r1, r2=None, n=8, squash=(1, 1), glow=False, jitter=0.0):
        """Cylinder/cone from point p1 (radius r1) to p2 (radius r2). `squash[0]` flattens front-back."""
        p1, p2 = Vector(p1), Vector(p2)
        d = p2 - p1
        rot = [math.degrees(a) for a in d.to_track_quat("Z", "Y").to_euler()]
        self.cyl(bone, color, (p1 + p2) / 2, r=r1, r2=r1 if r2 is None else r2, h=d.length, n=n, rot=rot,
                 squash=squash, glow=glow, jitter=jitter)

    def ball(self, bone, color, loc, size, rot=(0, 0, 0), sub=1, glow=False, jitter=0.0):
        if not isinstance(size, (tuple, list)):
            size = (size, size, size)
        verts = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=0.5)["verts"]
        self._finish(verts, bone, color, glow, loc, rot, size, jitter)

    def ring(self, bone, color, loc, R, r, n=12, m=4, rot=(0, 0, 0), squash=(1, 1), arc=360.0, glow=False):
        """Torus around local Z. A partial `arc` (degrees) is centred on +Y (the back) and capped."""
        full = arc >= 360.0
        cols = n if full else n + 1
        grid = []
        for i in range(cols):
            a = math.radians(-arc / 2 + arc * i / n)
            u = Vector((math.sin(a), math.cos(a), 0.0))
            grid.append([self.bm.verts.new(u * R + u * r * math.cos(b) + Vector((0, 0, r * math.sin(b))))
                         for b in (2 * math.pi * j / m for j in range(m))])
        for i in range(n):
            i2 = (i + 1) % cols
            for j in range(m):
                j2 = (j + 1) % m
                self.bm.faces.new((grid[i][j], grid[i2][j], grid[i2][j2], grid[i][j2]))
        if not full:
            self.bm.faces.new(grid[0])
            self.bm.faces.new(list(reversed(grid[-1])))
        self._finish([v for row in grid for v in row], bone, color, glow, loc, rot, (squash[0], squash[1], 1.0))

    def slab(self, bone, color, pts, thickness, loc=(0, 0, 0), rot=(0, 0, 0), glow=False, jitter=0.0):
        """Planar polygon (3D points) extruded symmetrically along its normal."""
        pts = [Vector(p) for p in pts]
        off = geometry.normal(pts) * (thickness / 2)
        top = [self.bm.verts.new(p + off) for p in pts]
        bot = [self.bm.verts.new(p - off) for p in pts]
        self.bm.faces.new(top)
        self.bm.faces.new(list(reversed(bot)))
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            self.bm.faces.new((bot[i], bot[j], top[j], top[i]))
        self._finish(top + bot, bone, color, glow, loc, rot, (1, 1, 1), jitter)

    def prism(self, bone, color, pts_xz, thickness, loc=(0, 0, 0), rot=(0, 0, 0), glow=False):
        """Flat shape drawn in the XZ plane (facing -Y), then placed with loc/rot."""
        self.slab(bone, color, [(x, 0, z) for x, z in pts_xz], thickness, loc, rot, glow)

    # --- assembly ---------------------------------------------------------------
    def _bake_ao(self, bm, samples=24):
        if self.ao <= 0:
            return
        bm.faces.ensure_lookup_table()
        tree = BVHTree.FromBMesh(bm)
        lo = Vector([min(v.co[i] for v in bm.verts) for i in range(3)])
        hi = Vector([max(v.co[i] for v in bm.verts) for i in range(3)])
        dist = self.ao_dist or 0.07 * max(hi - lo)
        dirs = _hemisphere(samples)
        for f in bm.faces:
            if f.material_index in (0, 4) or f.normal.length < 0.5:
                continue
            basis = f.normal.to_track_quat("Z", "Y").to_matrix()
            origin = f.calc_center_median() + f.normal * (dist * 0.01)
            hits = sum(1 for d in dirs if tree.ray_cast(origin, basis @ d, dist)[0] is not None)
            k = (1 - self.ao * hits / samples) * (1 + self.rng.uniform(-self.variance, self.variance))
            for loop in f.loops:
                c = loop[self.cl]
                loop[self.cl] = (c[0] * k, c[1] * k, c[2] * k, 1.0)

    def build(self):
        bm = self.bm
        # open water quads are built facing up; recalculation only makes sense for closed parts
        bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f.material_index != 4])
        self._bake_ao(bm)
        if not any(f.material_index == 0 for f in bm.faces):  # keep Glow as surface 0 (see module doc)
            gi = self.groups.setdefault(self.order[0], len(self.groups))
            tri = [bm.verts.new(p) for p in ((0, 0, -0.05), (0.001, 0, -0.05), (0, 0.001, -0.05))]
            for v in tri:
                v[self.dl][gi] = 1.0
            bm.faces.new(tri).material_index = 0
        me = bpy.data.meshes.new(self.name)
        bm.to_mesh(me)
        bm.free()
        return self._rig(me)

    def _materials(self):
        return [_make_material("Glow", *self.glow), _make_material("Body"),
                _make_material("Metal", roughness=0.4, metallic=0.6), _make_material("Foliage", roughness=0.9),
                _make_material("Water", roughness=0.1, flat=self.pal.get("water", "#3F86C4"), alpha=0.75)]

    def _rig(self, me):
        """Wrap the finished mesh into an object, add materials and the armature."""
        me.color_attributes.active_color_name = "Col"
        for mat in self._materials():
            me.materials.append(mat)

        obj = bpy.data.objects.new(self.name, me)
        if not self.rig:
            bpy.context.scene.collection.objects.link(obj)
            self.obj = obj
            return self
        for name, _ in sorted(self.groups.items(), key=lambda kv: kv[1]):
            obj.vertex_groups.new(name=name)

        arm_data = bpy.data.armatures.new(self.name + "Rig")
        arm = bpy.data.objects.new(self.name + "Rig", arm_data)
        scene = bpy.context.scene
        scene.collection.objects.link(arm)
        scene.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode="EDIT")
        for name in self.order:
            head, parent = self.bones[name]
            eb = arm_data.edit_bones.new(name)
            eb.head = head
            eb.tail = head + Vector((0, 0, 0.1))
            eb.roll = 0.0
            if parent:
                eb.parent = arm_data.edit_bones[parent]
        bpy.ops.object.mode_set(mode="OBJECT")

        obj.parent = arm
        obj.modifiers.new("Armature", "ARMATURE").object = arm
        for pb in arm.pose.bones:
            pb.rotation_mode = "XYZ"
        self.obj, self.arm = obj, arm
        return self

    def height(self):
        return max(v.co.z for v in self.obj.data.vertices)


def biped_rig(m, hips, chest, neck, head, shoulder, elbow, wrist, hip, knee, ankle, wrist_l=None, wrist_r=None):
    """Standard humanoid skeleton; limb joints are given for the left side and mirrored.
    `wrist_l` / `wrist_r` override a wrist (world position) for an arm bent to hold a weapon."""
    m.bone("root", (0, 0, 0))
    m.bone("hips", hips, "root")
    m.bone("chest", chest, "hips")
    m.bone("neck", neck, "chest")
    m.bone("head", head, "neck")
    for s, side in SIDES:
        def mir(p):
            return (s * p[0], p[1], p[2])
        m.bone(f"upperarm_{side}", mir(shoulder), "chest")
        m.bone(f"forearm_{side}", mir(elbow), f"upperarm_{side}")
        own = wrist_l if side == "L" else wrist_r
        m.bone(f"hand_{side}", tuple(own) if own is not None else mir(wrist), f"forearm_{side}")
        m.bone(f"thigh_{side}", mir(hip), "hips")
        m.bone(f"shin_{side}", mir(knee), f"thigh_{side}")
        m.bone(f"foot_{side}", mir(ankle), f"shin_{side}")


class Anim:
    """One action. Every key sets ALL bones (unlisted ones go to rest) so actions never leak -
    unless `only` is given: then just those bones get tracks (e.g. towers leave "turret" to code)."""

    def __init__(self, model, name, loop=False, linear=(), only=None):
        self.arm = model.arm
        self.name = name
        self.loop = loop
        self.linear = linear
        self.only = set(only) if only else None
        self.last = 0
        self.action = bpy.data.actions.new(name)
        self.action.use_fake_user = True
        ad = self.arm.animation_data or self.arm.animation_data_create()
        ad.action = self.action

    def pose(self, frame, **bones):
        self.last = max(self.last, frame)
        for pb in self.arm.pose.bones:
            if self.only is not None and pb.name not in self.only:
                continue
            spec = bones.get(pb.name, {})
            pb.rotation_euler = (math.radians(spec.get("pitch", 0)), math.radians(spec.get("yaw", 0)),
                                 -math.radians(spec.get("side", 0)))
            x, y, z = spec.get("loc", (0, 0, 0))
            pb.location = (x, z, -y)  # world offset -> bone-local (Y up the bone)
            pb.scale = (spec.get("scale", 1.0),) * 3
            for path in ("rotation_euler", "location", "scale"):
                pb.keyframe_insert(path, frame=frame, group=pb.name)

    def done(self):
        act = self.action
        act.use_frame_range = True
        act.frame_start, act.frame_end = 0, self.last
        for fc in _fcurves(act):
            if any(f'"{b}"' in fc.data_path for b in self.linear):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
            if self.loop:
                act.use_cyclic = True
                fc.modifiers.new("CYCLES")  # also makes auto handles wrap around smoothly
            fc.update()
        ad = self.arm.animation_data
        track = ad.nla_tracks.new()
        track.name = self.name
        track.strips.new(self.name, 0, act)
        track.mute = True
        ad.action = None


# --- reusable humanoid animations ------------------------------------------------
def biped_walk(m, frames=24, stride=1.0, arm=25, elbow=25, bob=0.03, lean=6, sway=3, shift=0.01, twist=5,
               name="Walk", linear=(), extra=None):
    """Walk cycle with bending knees and rolling feet.
    Keys: 0 left heel strike, q right leg passing, 2q right heel strike, 3q left leg passing."""
    a = Anim(m, name, loop=True, linear=linear)
    q = frames // 4
    for i, f in enumerate((0, q, 2 * q, 3 * q, frames)):
        k = i % 4
        ph = (1, 0, -1, 0)[k]  # +1: left leg forward
        st = (0, 1, 0, -1)[k]  # +1: standing on the left leg
        up = (0, 1, 0, 1)[k]
        p = dict(
            hips=dict(loc=(shift * st, 0, bob * up - bob * 0.3), side=-sway * st, yaw=-twist * ph),
            chest=dict(pitch=lean, yaw=twist * 1.6 * ph, side=sway * 0.7 * st),
            neck=dict(pitch=-lean * 0.4),
            head=dict(pitch=-lean * 0.5 + 2 * up, yaw=-twist * 0.5 * ph),
        )
        for side, sgn in (("L", 1), ("R", -1)):
            pp = ph * sgn  # +1 this leg forward
            if k in (1, 3) and ((k == 1) == (side == "R")):
                th, sh, ft = -12, 50, -20   # swinging leg passes under the body
            elif k in (1, 3):
                th, sh, ft = 6, 6, -12      # stance leg
            elif pp > 0:
                th, sh, ft = -32, 8, 14     # heel strike
            else:
                th, sh, ft = 26, 22, -20    # toe off
            p[f"thigh_{side}"] = dict(pitch=th * stride)
            p[f"shin_{side}"] = dict(pitch=sh * stride)
            p[f"foot_{side}"] = dict(pitch=ft * stride)
            p[f"upperarm_{side}"] = dict(pitch=arm * pp, side=-sgn * 4)
            p[f"forearm_{side}"] = dict(pitch=-elbow - 0.6 * elbow * max(-pp, 0))
        if extra:
            extra(k, ph, up, p)
        a.pose(f, **p)
    a.done()


def biped_hit(m, frames=10, push=0.04, extra=None):
    a = Anim(m, "Hit")
    a.pose(0)
    p = dict(hips=dict(loc=(0, push, -push * 0.3)), chest=dict(pitch=-14), neck=dict(pitch=-6), head=dict(pitch=-14),
             upperarm_L=dict(pitch=-25, side=-18), upperarm_R=dict(pitch=-25, side=18),
             forearm_L=dict(pitch=-35), forearm_R=dict(pitch=-35))
    for side in "LR":
        p[f"thigh_{side}"] = dict(pitch=-8)
        p[f"shin_{side}"] = dict(pitch=14)
        p[f"foot_{side}"] = dict(pitch=-6)
    if extra:
        extra(p)
    a.pose(3, **p)
    a.pose(frames)
    a.done()


def biped_die(m, depth=0.15, frames=32, push=0.05, extra=None):
    """Knees buckle, then the body falls on its back. `depth` lifts it so the back rests on the ground."""
    a = Anim(m, "Die")
    knees = dict(thigh_L=dict(pitch=-35), shin_L=dict(pitch=60), foot_L=dict(pitch=-20),
                 thigh_R=dict(pitch=-25), shin_R=dict(pitch=45), foot_R=dict(pitch=-15))
    p1 = dict(hips=dict(loc=(0, 0, -depth * 0.6)), chest=dict(pitch=-18), head=dict(pitch=-25),
              upperarm_L=dict(pitch=-60, side=-25), upperarm_R=dict(pitch=-60, side=25),
              forearm_L=dict(pitch=-30), forearm_R=dict(pitch=-30), **knees)
    lying = dict(root=dict(pitch=-88, loc=(0, push, depth)), chest=dict(pitch=-8), neck=dict(pitch=-10),
                 head=dict(pitch=-20, yaw=25), upperarm_L=dict(pitch=-40, side=-70),
                 upperarm_R=dict(pitch=-30, side=75), forearm_L=dict(pitch=-35), forearm_R=dict(pitch=-20),
                 thigh_L=dict(pitch=-30), shin_L=dict(pitch=35), thigh_R=dict(pitch=-10, side=-8),
                 shin_R=dict(pitch=15))
    bounce = dict(lying, root=dict(pitch=-80, loc=(0, push, depth)))
    if extra:
        for p in (p1, lying, bounce):
            extra(p)
    a.pose(0)
    a.pose(int(frames * 0.25), **p1)
    a.pose(int(frames * 0.62), **lying)
    a.pose(int(frames * 0.78), **bounce)
    a.pose(frames, **lying)
    a.done()


# --- export / preview --------------------------------------------------------------
def export_glb(model, path):
    bpy.ops.object.select_all(action="DESELECT")
    model.obj.select_set(True)
    if model.arm:
        model.arm.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True,
                              export_animations=model.arm is not None, export_animation_mode="ACTIONS",
                              export_yup=True, export_apply=False)


def render_preview(model, path, action="Walk", frame=0, res=768, transparent=False, zoom=1.9):
    scene = bpy.context.scene
    ad = model.arm.animation_data if model.arm else None
    if ad:
        for t in ad.nla_tracks:
            t.mute = True
        ad.action = bpy.data.actions[action]
    scene.frame_set(frame)

    vs = [v.co for v in model.obj.data.vertices]
    lo = Vector([min(v[i] for v in vs) for i in range(3)])
    hi = Vector([max(v[i] for v in vs) for i in range(3)])
    h = max(hi - lo)
    target = (lo + hi) / 2
    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_data.lens = 50
    cam = bpy.data.objects.new("PreviewCam", cam_data)
    cam.location = target + Vector(getattr(model, "preview_dir", (1.1, -2.0, 0.6))).normalized() * h * zoom
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(cam)
    scene.camera = cam

    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(50), 0, math.radians(30))
    scene.collection.objects.link(sun)
    world = bpy.data.worlds.new("World")
    world.color = (0.35, 0.38, 0.45)
    scene.world = world

    for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH"):
        try:
            scene.render.engine = engine
            break
        except TypeError:
            continue
    scene.render.resolution_x = scene.render.resolution_y = res
    scene.render.film_transparent = transparent
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    if ad:
        ad.action = None
    for obj in (cam, sun):
        bpy.data.objects.remove(obj)
