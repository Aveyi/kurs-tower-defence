"""Tower models (5 types x 3 levels) and their projectiles.

Every tower is one skinned mesh. Bones the game code relies on:
  turret - yaw pivot, rotated by code toward the target (no animation touches it)
  muzzle - spawn point of projectiles
Animations: "Idle" (loop: flags, fire, floating crystals) and "Shoot".
The front of every weapon and projectile is -Y in Blender (= +Z in Godot, the glTF model front).
Levels: 1 wood, 2 stone, 3 stone with gold, banners and braziers. Footprint fits a 2x2 m cell.
"""
import math
from functools import partial

from mathutils import Matrix, Vector

from lowpoly import Anim, Model, rag

KINGDOM = dict(
    stone="#9A9488", stone2="#857F74", stone3="#ADA79A", mortar="#5A564F", dirt="#6B5A42",
    wood="#7A5232", wood2="#5E3F27", plank="#9A6B40", plank2="#86593A", roof="#3E5C8C", roof2="#2C4570",
    gold="#D2A43A", iron="#4F555C", iron2="#8A9198", banner="#2F5DA8", banner2="#E8C547", rope="#B79E6E",
    dark="#2A211B", flame="#FFB347", ball="#2E3236")
METALS = ("gold", "iron", "iron2", "bronze")


def polar(r, deg, z, c=(0, 0)):
    a = math.radians(deg)
    return (c[0] + r * math.cos(a), c[1] + r * math.sin(a), z)


def tower_model(name, colors=None, glow="#FFB347", strength=4.0, seed=1):
    pal = dict(KINGDOM)
    pal.update(colors or {})
    m = Model(name, pal, glow_color=glow, glow_strength=strength, metal=METALS, seed=seed)
    m.bone("root", (0, 0, 0))
    m.flames, m.flags = [], []
    return m


# --- architecture -------------------------------------------------------------------
def plinth(m, r=0.92, h=0.14, square=False):
    if square:
        m.box("root", "stone2", (0, 0, h / 2), (2 * r, 2 * r, h), bevel=0.03)
    else:
        m.cyl("root", "stone2", (0, 0, h / 2), r=r, r2=r - 0.04, h=h, n=12)


def drum_out(z0, z1, r0, r1, z, depth=0.14):
    """Outer radius of a stone_drum at height z."""
    return r0 + (r1 - r0) * (z - z0) / (z1 - z0) + depth * 0.2


def stone_drum(m, z0, z1, r0, r1, depth=0.14, colors=("stone", "stone2", "stone3"), c=(0, 0)):
    """Round masonry: staggered bevelled blocks around a mortar core."""
    rows = max(2, round((z1 - z0) / 0.26))
    rh = (z1 - z0) / rows
    per_row = max(8, round(2 * math.pi * (r0 + r1) / 2 / 0.34))
    m.cyl("root", "mortar", (c[0], c[1], (z0 + z1) / 2), r=r0 - depth * 0.35, r2=r1 - depth * 0.35, h=z1 - z0,
          n=per_row)
    for i in range(rows):
        r = r0 + (r1 - r0) * (i + 0.5) / rows
        w = 2 * r * math.sin(math.pi / per_row) * 0.93
        for j in range(per_row):
            deg = (j + 0.5 * (i % 2)) * 360 / per_row
            m.box("root", colors[m.rng.randrange(len(colors))], polar(r - depth * 0.3, deg, z0 + (i + 0.5) * rh, c),
                  (w, depth, rh * 0.86), rot=(0, 0, deg + 90), bevel=min(0.02, rh * 0.12), jitter=0.005)
    return per_row


def stone_square(m, z0, z1, h0, h1, depth=0.14, colors=("stone", "stone2", "stone3"), c=(0, 0)):
    """Square masonry; each side skips one corner (pinwheel) so blocks never overlap."""
    rows = max(2, round((z1 - z0) / 0.26))
    rh = (z1 - z0) / rows
    core0, core1 = h0 - depth * 0.35, h1 - depth * 0.35
    m.box("root", "mortar", (c[0], c[1], (z0 + z1) / 2), (2 * core0, 2 * core0, z1 - z0), taper=core1 / core0)
    sides = ((Vector((0, -1, 0)), Vector((1, 0, 0)), 0), (Vector((1, 0, 0)), Vector((0, 1, 0)), 90),
             (Vector((0, 1, 0)), Vector((-1, 0, 0)), 180), (Vector((-1, 0, 0)), Vector((0, -1, 0)), 270))
    for i in range(rows):
        h = h0 + (h1 - h0) * (i + 0.5) / rows
        z = z0 + (i + 0.5) * rh
        k = max(3, round(2 * h / 0.36))
        lo, hi = -h, h - depth
        cuts = [lo + (hi - lo) * q / k for q in range(k + 1)]
        if i % 2:
            cuts = [cuts[0]] + [c + (hi - lo) / k / 2 for c in cuts[:-1]] + [cuts[-1]]
        for n, t, yaw in sides:
            for a, b in zip(cuts, cuts[1:]):
                p = n * (h - depth * 0.3) + t * ((a + b) / 2)
                m.box("root", colors[m.rng.randrange(len(colors))], (c[0] + p.x, c[1] + p.y, z),
                      ((b - a) * 0.93, depth, rh * 0.86),
                      rot=(0, 0, yaw), bevel=min(0.02, rh * 0.12), jitter=0.005)


def crenels_round(m, z, r, n=10, h=0.24, c=(0, 0)):
    m.cyl("root", "stone2", (c[0], c[1], z + 0.05), r=r + 0.05, h=0.1, n=2 * n)
    w = 2 * r * math.sin(math.pi / n) * 0.55
    for j in range(n):
        deg = j * 360 / n + 90
        m.box("root", ("stone", "stone3")[j % 2], polar(r - 0.06, deg, z + 0.1 + h / 2, c), (w, 0.17, h),
              rot=(0, 0, deg + 90), bevel=0.02, jitter=0.004)


def crenels_square(m, z, half, h=0.24, c=(0, 0)):
    m.box("root", "stone2", (c[0], c[1], z + 0.05), (2 * half + 0.1, 2 * half + 0.1, 0.1), bevel=0.02)
    e = half - 0.08
    for x, y in ((e, e), (-e, e), (e, -e), (-e, -e)):
        m.box("root", "stone3", (c[0] + x, c[1] + y, z + 0.1 + h / 2), (0.22, 0.22, h), bevel=0.02, jitter=0.004)
    for x, y, yaw in ((0, -e, 0), (0, e, 0), (e, 0, 90), (-e, 0, 90)):
        m.box("root", "stone", (c[0] + x, c[1] + y, z + 0.1 + h / 2), (0.3, 0.17, h), rot=(0, 0, yaw), bevel=0.02,
              jitter=0.004)


def cone_roof(m, z, r, h, n=8, color="roof", trim="roof2", c=(0, 0)):
    x, y = c
    m.cyl("root", trim, (x, y, z + 0.03), r=r + 0.06, r2=r + 0.02, h=0.06, n=n)
    m.cyl("root", color, (x, y, z + 0.06 + h / 2), r=r, r2=0, h=h, n=n)
    for t in (0.3, 0.6):  # overlapping tile rows
        rr = r * (1 - t)
        m.cyl("root", trim, (x, y, z + 0.06 + h * t + 0.03), r=rr + 0.025, r2=rr * 0.93 + 0.02, h=0.06, n=n)
    m.seg("root", "gold", (x, y, z + h), (x, y, z + h + 0.3), 0.035, 0.0, n=5)
    m.ball("root", "gold", (x, y, z + h + 0.08), 0.08)
    return z + h + 0.1


def door(m, r, z0=0.14, w=0.34, h=0.5, trim="stone3", c=(0, 0)):
    """Arched wooden door on the front (-Y) wall whose outer face is at distance r from centre c."""
    x, y = c[0], c[1] - r
    m.box("root", "wood2", (x, y, z0 + h / 2), (w, 0.08, h), bevel=0.01)
    m.cyl("root", "wood2", (x, y + 0.002, z0 + h), r=w / 2, h=0.07, n=10, rot=(90, 0, 0))
    for z in (z0 + h * 0.25, z0 + h * 0.75):
        m.box("root", "iron", (x, y - 0.042, z), (w + 0.01, 0.01, 0.03))
    m.ring("root", trim, (x, y - 0.01, z0 + h), w / 2 + 0.035, 0.035, n=8, arc=180, rot=(90, 0, 0))
    for sx in (1, -1):
        m.box("root", trim, (x + sx * (w / 2 + 0.035), y - 0.01, z0 + h / 2), (0.07, 0.09, h), bevel=0.01)


def window(m, deg, r, z, w=0.09, h=0.2, lit=True, c=(0, 0)):
    m.box("root", "flame" if lit else "dark", polar(r, deg, z, c), (w, 0.06, h), rot=(0, 0, deg + 90), glow=lit)
    m.box("root", "wood2", polar(r + 0.01, deg, z - h / 2 - 0.02, c), (w + 0.07, 0.07, 0.035), rot=(0, 0, deg + 90))
    m.box("root", "wood2", polar(r + 0.01, deg, z + h / 2 + 0.02, c), (w + 0.04, 0.07, 0.03), rot=(0, 0, deg + 90))


def wall_banner(m, x, y, deg, ztop, length=0.8, color="banner", emblem="banner2"):
    """Cloth hanging on a wall at (x, y), facing outward along `deg`."""
    rot = (0, 0, deg + 90)
    out = Vector(polar(1, deg, 0))
    p = Vector((x, y, ztop))
    m.prism("root", color, [(-0.15, 0), (0.15, 0), (0.15, -length + 0.12), (0, -length), (-0.15, -length + 0.12)],
            0.02, loc=p + out * 0.012, rot=rot)
    m.prism("root", emblem, [(0, -0.15), (0.08, -0.26), (0, -0.37), (-0.08, -0.26)], 0.026, loc=p + out * 0.014,
            rot=rot)
    left = Vector(polar(0.2, deg + 90, 0))
    m.seg("root", "gold", p + out * 0.02 - left, p + out * 0.02 + left, 0.015, n=5)


def flag(m, name, p, h=0.6, color="banner", emblem="banner2"):
    """Pole with a swallow-tail flag; the flag gets its own bone for waving."""
    x, y, z = p
    m.seg("root", "wood2", (x, y, z), (x, y, z + h), 0.025, 0.02, n=5)
    m.ball("root", "gold", (x, y, z + h + 0.03), 0.05)
    m.bone(name, (x, y, z + h), "root")
    m.prism(name, color, [(0, 0), (0.5, -0.02), (0.4, -0.15), (0.5, -0.28), (0, -0.3)], 0.02,
            loc=(x + 0.02, y, z + h - 0.03))
    m.prism(name, emblem, [(0.14, -0.06), (0.23, -0.15), (0.14, -0.24), (0.05, -0.15)], 0.026,
            loc=(x + 0.02, y, z + h - 0.03))
    m.flags.append(name)


def brazier(m, name, p, s=1.0):
    x, y, z = p
    for k in range(3):
        lx, ly, _ = polar(0.1 * s, k * 120 + 30, 0)
        m.seg("root", "iron", (x + lx, y + ly, z), (x, y, z + 0.12 * s), 0.012 * s, n=4)
    m.cyl("root", "iron", (x, y, z + 0.15 * s), r=0.07 * s, r2=0.14 * s, h=0.08 * s, n=8)
    m.cyl("root", "dark", (x, y, z + 0.19 * s), r=0.12 * s, h=0.01, n=8)
    m.bone(name, (x, y, z + 0.18 * s), "root")
    m.cyl(name, "flame", (x, y, z + 0.3 * s), r=0.09 * s, r2=0, h=0.24 * s, n=5, glow=True)
    m.cyl(name, "flame", (x + 0.04 * s, y, z + 0.26 * s), r=0.05 * s, r2=0, h=0.15 * s, n=4, rot=(0, 15, 0), glow=True)
    m.cyl(name, "flame", (x - 0.03 * s, y + 0.03 * s, z + 0.25 * s), r=0.05 * s, r2=0, h=0.13 * s, n=4,
          rot=(-15, -10, 0), glow=True)
    m.flames.append(name)


def lantern(m, name, p, s=1.0):
    x, y, z = p
    m.box("root", "iron", (x, y, z + 0.01 * s), (0.13 * s, 0.13 * s, 0.02 * s))
    for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        m.seg("root", "iron", (x + dx * 0.055 * s, y + dy * 0.055 * s, z), (x + dx * 0.055 * s, y + dy * 0.055 * s,
                                                                             z + 0.16 * s), 0.008 * s, n=4)
    m.cyl("root", "iron", (x, y, z + 0.19 * s), r=0.09 * s, r2=0.02 * s, h=0.06 * s, n=4, rot=(0, 0, 45))
    m.ring("root", "iron", (x, y, z + 0.24 * s), 0.025 * s, 0.006 * s, n=6, rot=(90, 0, 0))
    m.bone(name, (x, y, z + 0.02 * s), "root")
    m.box(name, "flame", (x, y, z + 0.09 * s), (0.08 * s, 0.08 * s, 0.13 * s), glow=True)
    m.flames.append(name)


def keg(m, p, s=1.0):
    x, y, z = p
    m.cyl("root", "wood", (x, y, z + 0.14 * s), r=0.11 * s, h=0.28 * s, n=8)
    m.cyl("root", "wood", (x, y, z + 0.14 * s), r=0.125 * s, h=0.12 * s, n=8)
    for dz in (0.03, 0.25):
        m.ring("root", "iron", (x, y, z + dz * s), 0.115 * s, 0.01 * s, n=8)
    m.cyl("root", "plank2", (x, y, z + 0.285 * s), r=0.1 * s, h=0.01, n=8)


def ball_pile(m, p, r=0.1):
    x, y, z = p
    for k in range(3):
        bx, by, _ = polar(r * 1.15, k * 120 + 90, 0)
        m.ball("root", "ball", (x + bx, y + by, z + r), 2 * r, sub=2)
    m.ball("root", "ball", (x, y, z + r * 2.6), 2 * r, sub=2)


def wood_frame(m, F, half_bottom, half_top, rail=0.55, footing=True):
    """Four slanted log legs, X-braces, plank floor and a railing (level 1 towers)."""
    legs = {}
    for sx in (1, -1):
        for sy in (1, -1):
            a, b = Vector((sx * half_bottom, sy * half_bottom, 0)), Vector((sx * half_top, sy * half_top, F))
            legs[(sx, sy)] = (a, b)
            if footing:
                m.box("root", "stone2", (a.x, a.y, 0.06), (0.22, 0.22, 0.12), bevel=0.02)
            m.seg("root", "wood", a, b + Vector((0, 0, rail)), 0.07, 0.06, n=6, jitter=0.004)

    def leg_at(c, z):
        a, b = legs[c]
        return a.lerp(b, z / F)

    sides = (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1)))
    for c1, c2 in sides:
        for z0, z1 in ((0.25, F * 0.52), (F * 0.55, F - 0.12)):
            m.seg("root", "wood2", leg_at(c1, z0), leg_at(c2, z1), 0.035, n=5)
            m.seg("root", "wood2", leg_at(c2, z0), leg_at(c1, z1), 0.035, n=5)
        p1, p2 = Vector((c1[0] * half_top, c1[1] * half_top, 0)), Vector((c2[0] * half_top, c2[1] * half_top, 0))
        for dz in (rail * 0.5, rail * 0.92):
            m.seg("root", "wood", p1 + Vector((0, 0, F + dz)), p2 + Vector((0, 0, F + dz)), 0.025, n=5)
    w = 2 * half_top + 0.2
    m.box("root", "wood2", (0, 0, F - 0.08), (w - 0.1, w - 0.1, 0.1), bevel=0.015)
    k = 8
    for i in range(k):
        m.box("root", ("plank", "plank2")[i % 2], (-w / 2 + (i + 0.5) * w / k, 0, F), (w / k * 0.95, w, 0.05),
              bevel=0.008, jitter=0.003)
    return F + 0.025


# --- idle animation shared by all towers -----------------------------------------------
def idle(m, bones=(), extra=None, linear=(), frames=48):
    only = list(m.flames) + list(m.flags) + list(bones)
    a = Anim(m, "Idle", loop=True, linear=linear, only=only or ("root",))
    n = 8
    for i in range(n + 1):
        t = i / n
        p = {}
        for j, name in enumerate(m.flames):  # flicker twice per loop
            w = 2 * math.pi * (2 * t) + j * 1.7
            p[name] = dict(scale=1 + 0.12 * math.sin(w), yaw=8 * math.sin(w * 1.5))
        for j, name in enumerate(m.flags):
            p[name] = dict(yaw=14 * math.sin(2 * math.pi * t + j))
        if extra:
            extra(t, p)
        a.pose(round(frames * t), **p)
    a.done()


# --- archer tower ---------------------------------------------------------------------
def _archer_figure(m, z0, L):
    m.bone("turret", (0, 0, z0), "root")
    m.bone("archer", (0, 0, z0 + 0.45), "turret")
    m.bone("bow_arm", (0.12, -0.02, z0 + 0.78), "archer")
    m.bone("draw_arm", (-0.12, -0.02, z0 + 0.78), "archer")
    m.bone("arrow", (0.06, -0.1, z0 + 0.8), "draw_arm")
    m.bone("muzzle", (0.08, -0.5, z0 + 0.79), "turret")

    def Z(x, y, z):
        return (x, y, z0 + z)

    for s in (1, -1):
        m.box("turret", "boot", Z(s * 0.07, -0.03, 0.04), (0.08, 0.15, 0.08), bevel=0.012)
        m.seg("turret", "leather", Z(s * 0.07, 0, 0.46), Z(s * 0.07, -0.005, 0.07), 0.045, 0.038, n=6)
        m.box("archer", "boot", Z(s * 0.028, -0.071, 0.87), (0.018, 0.01, 0.012))
    m.cyl("archer", "tunic", Z(0, 0, 0.44), r=0.13, r2=0.115, h=0.14, n=8)
    m.box("archer", "tunic", Z(0, 0, 0.62), (0.24, 0.15, 0.3), taper=1.12, bevel=0.025)
    m.box("archer", "leather", Z(0, 0, 0.5), (0.255, 0.165, 0.04), bevel=0.008)
    m.box("archer", "gold" if L == 3 else "iron2", Z(0, -0.085, 0.5), (0.04, 0.01, 0.035))
    m.slab("archer", "cloak", [Z(x, 0.09 + (0.78 - z) * 0.1, z) for x, z in rag(-0.15, 0.15, 0.78, 0.3, 3, 0.04)],
           0.02)
    m.ball("archer", "skin", Z(0, -0.012, 0.86), (0.12, 0.12, 0.13), sub=2)
    m.ball("archer", "cloak", Z(0, 0.018, 0.885), (0.16, 0.16, 0.17), sub=2)
    m.seg("archer", "cloak", Z(0, 0.07, 0.93), Z(0, 0.14, 0.83), 0.05, 0, n=5)
    m.ring("archer", "cloak2" if L < 3 else "gold", Z(0, 0.0, 0.775), 0.1, 0.022, n=10)
    m.seg("archer", "leather", Z(0.07, 0.12, 0.5), Z(0.11, 0.15, 0.84), 0.045, 0.042, n=6)
    for dx, dy in ((-0.015, 0), (0.015, 0.005), (0, -0.012)):
        m.cyl("archer", "fletch", Z(0.115 + dx, 0.155 + dy, 0.89), r=0.013, r2=0, h=0.07, n=3)
    if L >= 2:
        m.box("archer", "leather", Z(0.13, -0.02, 0.77), (0.09, 0.12, 0.05), rot=(0, -20, 0), bevel=0.01)

    m.seg("bow_arm", "tunic", Z(0.12, -0.02, 0.78), Z(0.08, -0.33, 0.79), 0.035, 0.03, n=6)
    m.ball("bow_arm", "skin", Z(0.08, -0.36, 0.79), 0.05)
    G, U, T = Z(0.08, -0.38, 0.79), Z(0.08, -0.34, 0.99), Z(0.08, -0.27, 1.15)
    D, B = Z(0.08, -0.34, 0.59), Z(0.08, -0.27, 0.43)
    wood = "gold" if L == 3 else "bowwood"
    for a, b, r1, r2 in ((G, U, 0.018, 0.015), (U, T, 0.015, 0.007), (G, D, 0.018, 0.015), (D, B, 0.015, 0.007)):
        m.seg("bow_arm", wood, a, b, r1, r2, n=5)
    m.seg("bow_arm", "leather", Z(0.08, -0.38, 0.75), Z(0.08, -0.38, 0.83), 0.022, n=5)

    N = Z(0.06, -0.1, 0.8)
    m.seg("draw_arm", "tunic", Z(-0.12, -0.02, 0.78), Z(0.035, -0.1, 0.8), 0.033, 0.03, n=6)
    m.ball("draw_arm", "skin", Z(0.05, -0.1, 0.8), 0.045)
    m.seg("draw_arm", "string", T, N, 0.004, n=4)
    m.seg("draw_arm", "string", B, N, 0.004, n=4)
    m.seg("arrow", "plank", N, Z(0.08, -0.46, 0.79), 0.007, n=4)
    m.seg("arrow", "iron2", Z(0.08, -0.46, 0.79), Z(0.08, -0.52, 0.79), 0.018, 0, n=4)
    m.slab("arrow", "fletch", [N, Z(0.065, -0.17, 0.8), Z(0.063, -0.14, 0.835)], 0.004)


def archer(L):
    m = tower_model(f"ArcherTower{L}", dict(
        cloak="#3F6B3A", cloak2="#2F5230", tunic="#6E8A4A", skin="#E0B08A", leather="#6B4A2F", boot="#3A2A1E",
        bowwood="#8A5A2B", string="#E8E0C8", fletch="#E6E0D0"), glow="#FFB347", seed=100 + L)
    if L == 1:
        F = wood_frame(m, 2.2, 0.72, 0.55)
        for sx in (1, -1):
            m.seg("root", "wood2", (sx * 0.17, 0.98, 0), (sx * 0.17, 0.72, 2.2), 0.025, n=5)
        for k in range(1, 8):
            z = k * 2.2 / 8
            y = 0.98 - 0.26 * z / 2.2
            m.seg("root", "wood", (-0.17, y, z), (0.17, y, z), 0.018, n=4)
        lantern(m, "flame1", (0.55, -0.55, F + 0.53))
        flag(m, "flag1", (-0.55, 0.55, F + 0.53), 0.55)
    else:
        top = 1.45 if L == 2 else 2.2
        r0, r1 = (0.8, 0.72) if L == 2 else (0.9, 0.76)
        plinth(m, r0 + 0.12)
        stone_drum(m, 0.14, top, r0, r1)
        door(m, r0 + 0.02)
        for deg in (210, 330):
            window(m, deg, drum_out(0.14, top, r0, r1, top * 0.6) - 0.02, top * 0.6)
        if L == 2:
            m.cyl("root", "wood2", (0, 0, top + 0.03), r=r1 + 0.1, h=0.06, n=12)
            F = top + 0.085
            m.cyl("root", "plank", (0, 0, F - 0.025), r=r1 + 0.14, h=0.05, n=12)
            for k in range(8):
                deg = k * 45
                m.box("root", "wood2", polar(r1 + 0.1, deg, top - 0.02), (0.1, 0.24, 0.08), rot=(0, 0, deg + 90),
                      bevel=0.01)
                m.seg("root", "wood", polar(r1 + 0.1, deg + 22.5, F), polar(r1 + 0.1, deg + 22.5, F + 0.5), 0.028, n=5)
            for z in (F + 0.25, F + 0.48):
                m.ring("root", "wood", (0, 0, z), r1 + 0.1, 0.022, n=16)
            lantern(m, "flame1", polar(r1 + 0.1, 292.5, F + 0.5))
        else:
            m.cyl("root", "stone3", (0, 0, top * 0.5), r=(r0 + r1) / 2 + 0.05, h=0.08, n=20)
            crenels_round(m, top, r1)
            F = top + 0.1
            for deg in (252, 288):
                brazier(m, f"flame{deg}", polar(r1 - 0.06, deg, F + 0.24), 0.7)
            for deg in (230, 310):
                rr = drum_out(0.14, top, r0, r1, top - 0.65)
                wall_banner(m, *polar(rr, deg, 0)[:2], deg, top - 0.25, 0.85)
        posts_r, roof_z = (r1 + 0.02, F + 1.45) if L == 2 else (r1 - 0.12, F + 1.55)
        for deg in (45, 135, 225, 315):
            if L == 2:
                m.seg("root", "wood", polar(posts_r, deg, F), polar(posts_r, deg, roof_z), 0.045, n=6)
            else:
                m.box("root", "stone3", polar(posts_r, deg, (F + roof_z) / 2), (0.14, 0.14, roof_z - F),
                      rot=(0, 0, deg), bevel=0.02)
        tip = cone_roof(m, roof_z, 1.0 if L == 2 else 1.1, 0.95 if L == 2 else 1.1)
        flag(m, "flag1", (0, 0, tip + 0.15), 0.45)

    _archer_figure(m, F, L)
    m.build()

    idle(m, bones=("archer",), extra=lambda t, p: p.update(archer=dict(pitch=1.5 * math.sin(2 * math.pi * t))))
    a = Anim(m, "Shoot", only=("archer", "bow_arm", "draw_arm", "arrow"))
    a.pose(0)
    a.pose(2, archer=dict(pitch=-4), bow_arm=dict(pitch=-5), draw_arm=dict(pitch=-12, yaw=10),
           arrow=dict(scale=0.01))
    a.pose(8, draw_arm=dict(pitch=-115, yaw=-10), arrow=dict(scale=0.01))
    a.pose(12, draw_arm=dict(pitch=-20), arrow=dict(scale=0.01))
    a.pose(13)
    a.pose(16)
    a.done()
    return m


# --- cannon tower ---------------------------------------------------------------------
def _cannon_gun(m, F, s, metal, trim):
    m.bone("turret", (0, 0, F), "root")
    m.bone("barrel", (0, 0.05 * s, F + 0.36 * s), "turret")
    m.bone("muzzle", (0, -0.66 * s, F + 0.44 * s), "barrel")

    def S(x, y, z):
        return Vector((x * s, y * s, F + z * s))

    m.cyl("turret", "wood2", S(0, 0, 0.03), r=0.42 * s, h=0.06 * s, n=12)
    m.ring("turret", "iron", S(0, 0, 0.03), 0.42 * s, 0.02 * s, n=16)
    for sx in (1, -1):
        m.slab("turret", "wood", [S(sx * 0.13, 0.32, 0.06), S(sx * 0.13, -0.3, 0.06), S(sx * 0.13, -0.22, 0.4),
                                  S(sx * 0.13, 0.16, 0.3)], 0.06 * s)
        m.box("turret", "iron", S(sx * 0.13, 0.05, 0.37), (0.075 * s, 0.11 * s, 0.03 * s))
    for y, r in ((-0.14, 0.14), (0.2, 0.1)):
        m.seg("turret", "iron", S(-0.27, y, r + 0.06), S(0.27, y, r + 0.06), 0.028 * s, n=6)
        for sx in (1, -1):
            c = S(sx * 0.23, y, r + 0.06)
            m.cyl("turret", "wood2", c, r=r * s, h=0.05 * s, n=10, rot=(0, 90, 0))
            m.ring("turret", "iron", c, r * s, 0.014 * s, n=12, rot=(0, 90, 0))
            m.cyl("turret", "iron2", c, r=0.035 * s, h=0.07 * s, n=6, rot=(0, 90, 0))

    B, M = S(0, 0.4, 0.34), S(0, -0.62, 0.43)
    d = (M - B).normalized()
    m.seg("barrel", metal, B, M, 0.13 * s, 0.09 * s, n=10)
    for t, rr in ((0.08, 0.14), (0.4, 0.122), (0.7, 0.105)):
        c = B.lerp(M, t)
        m.seg("barrel", trim, c, c + d * 0.04 * s, rr * s, rr * s, n=10)
    m.seg("barrel", trim, M - d * 0.07 * s, M, 0.105 * s, 0.12 * s, n=10)
    m.seg("barrel", "dark", M - d * 0.005, M + d * 0.006, 0.065 * s, 0.065 * s, n=8)
    m.ball("barrel", trim, B - d * 0.06 * s, 0.12 * s)
    m.seg("barrel", trim, S(-0.17, 0.05, 0.36), S(0.17, 0.05, 0.36), 0.04 * s, n=6)


def cannon(L):
    m = tower_model(f"CannonTower{L}", dict(bronze="#B5803F"), glow="#FF9A3A", seed=200 + L)
    if L == 1:
        m.cyl("root", "dirt", (0, 0, 0.3), r=0.9, r2=0.74, h=0.6, n=12, jitter=0.015)
        F = 0.63
        m.cyl("root", "plank", (0, 0, F - 0.025), r=0.72, h=0.05, n=12)
        for k in range(15):
            deg = k * 24 + 7
            h = 0.78 + 0.06 * math.sin(k * 2.3)
            m.seg("root", "wood", polar(0.84, deg, 0), polar(0.84, deg, h), 0.065, n=6, jitter=0.004)
            m.cyl("root", "wood2", polar(0.84, deg, h + 0.07), r=0.065, r2=0, h=0.14, n=6)
        for z in (0.3, 0.55):
            m.ring("root", "rope", (0, 0, z), 0.86, 0.02, n=30)
        m.seg("root", "wood", polar(0.55, 40, F), polar(0.55, 40, F + 0.35), 0.03, n=5)
        lantern(m, "flame1", polar(0.55, 40, F + 0.35))
        keg(m, polar(0.5, 140, F), 0.9)
        ball_pile(m, polar(0.52, 95, F), 0.07)
        s, metal, trim = 0.8, "iron", "iron2"
    else:
        top, r0, r1 = (1.25, 0.85, 0.78) if L == 2 else (1.8, 0.9, 0.8)
        plinth(m, r0 + 0.1)
        stone_drum(m, 0.14, top, r0, r1)
        door(m, r0 + 0.02)
        for deg in (200, 340):
            window(m, deg, drum_out(0.14, top, r0, r1, top * 0.62) - 0.02, top * 0.62, lit=L == 3)
        crenels_round(m, top, r1, n=10 if L == 2 else 12)
        F = top + 0.1
        brazier(m, "flame1", polar(0.5, 45, F), 0.8)
        keg(m, polar(0.52, 150, F))
        ball_pile(m, polar(0.5, 100, F), 0.08)
        s, metal, trim = (1.0, "iron", "iron2") if L == 2 else (1.15, "bronze", "gold")
        if L == 3:
            m.cyl("root", "stone3", (0, 0, top * 0.5), r=(r0 + r1) / 2 + 0.05, h=0.08, n=20)
            for deg in (240, 300):
                rr = drum_out(0.14, top, r0, r1, top - 0.65)
                wall_banner(m, *polar(rr, deg, 0)[:2], deg, top - 0.25, 0.85)
            for deg in (240, 300):
                brazier(m, f"flame{deg}", polar(r1 - 0.06, deg, F + 0.24), 0.7)
            flag(m, "flag1", polar(0.62, 70, F), 1.1)

    _cannon_gun(m, F, s, metal, trim)
    m.build()

    idle(m)
    a = Anim(m, "Shoot", only=("barrel",))
    a.pose(0)
    a.pose(2, barrel=dict(loc=(0, 0.14 * s, 0.01), pitch=-7))
    a.pose(10, barrel=dict(loc=(0, 0.03 * s, 0), pitch=-1))
    a.pose(16)
    a.done()
    return m


# --- magic towers (mage, ice) ------------------------------------------------------------
def _crystal_core(m, z_turret, cz, s, rings=0, orbit=0, orbit_r=0.6, orbit_style="stone"):
    m.bone("turret", (0, 0, z_turret), "root")
    m.bone("float", (0, 0, cz), "turret")
    m.bone("pulse", (0, 0, cz), "float")
    m.bone("crystal", (0, 0, cz), "pulse")
    m.bone("muzzle", (0, 0, cz), "float")
    m.cyl("crystal", "crystal", (0, 0, cz + 0.8 * s), r=s, r2=0, h=1.6 * s, n=6, glow=True)
    m.cyl("crystal", "crystal", (0, 0, cz - 0.5 * s), r=0, r2=s, h=1.0 * s, n=6, glow=True)
    for k in range(3):
        x, y, _ = polar(s * 1.25, k * 120 + 30, 0)
        m.cyl("crystal", "crystal", (x, y, cz - 0.1 * s), r=0.3 * s, r2=0, h=0.9 * s, n=4, glow=True)
        m.cyl("crystal", "crystal", (x, y, cz - 0.7 * s), r=0, r2=0.3 * s, h=0.3 * s, n=4, glow=True)
    for k in range(rings):
        name = f"ring{k + 1}"
        m.bone(name, (0, 0, cz), "float")
        m.ring(name, "crystal", (0, 0, cz), s * 2.4 + 0.1 * k, 0.012, n=24, rot=(70 - 25 * k, 0, 50 * k), glow=True)
    if orbit:
        m.bone("orbit", (0, 0, cz), "turret")
        for k in range(orbit):
            x, y, z = polar(orbit_r, k * 360 / orbit, cz - 0.15 + 0.15 * (k % 2))
            if orbit_style == "stone":
                m.ball("orbit", "stone3", (x, y, z), 0.13, jitter=0.012)
                m.cyl("orbit", "crystal", (x, y, z + 0.11), r=0.03, r2=0, h=0.1, n=4, glow=True)
            else:
                m.cyl("orbit", "ice3", (x, y, z + 0.06), r=0.05, r2=0, h=0.16, n=5)
                m.cyl("orbit", "ice2", (x, y, z - 0.04), r=0, r2=0.05, h=0.08, n=5)


def _magic_anims(m, rings, orbit):
    bones = ["float", "crystal"] + [f"ring{k + 1}" for k in range(rings)] + (["orbit"] if orbit else [])

    def spin(t, p):
        p["float"] = dict(loc=(0, 0, 0.05 * math.sin(2 * math.pi * t)))
        p["crystal"] = dict(yaw=360 * t)
        for k in range(rings):
            p[f"ring{k + 1}"] = dict(yaw=(-1) ** k * 360 * t)
        if orbit:
            p["orbit"] = dict(yaw=-360 * t)

    idle(m, bones=bones, extra=spin, linear=("crystal", "ring1", "ring2", "orbit"))
    a = Anim(m, "Shoot", only=("pulse",))
    a.pose(0)
    a.pose(3, pulse=dict(scale=1.4))
    a.pose(7, pulse=dict(scale=0.92))
    a.pose(12)
    a.done()


def _prongs(m, n, base, mid, tip, color, r=0.07, start=45, tip_color=None):
    """Curved stone horns around the top: base/mid/tip are (radius, z)."""
    for k in range(n):
        deg = start + k * 360 / n
        a, b, c = polar(base[0], deg, base[1]), polar(mid[0], deg, mid[1]), polar(tip[0], deg, tip[1])
        m.seg("root", color, a, b, r, r * 0.8, n=6)
        m.ball("root", color, b, r * 1.6)
        m.seg("root", tip_color or color, b, c, r * 0.8, 0, n=6)


def mage(L):
    m = tower_model(f"MageTower{L}", dict(
        stone="#8E8A9A", stone2="#7A7688", stone3="#A29EAE", mortar="#55516A", roof="#4B3A7A", roof2="#38295E",
        crystal="#C9A8FF", banner="#5B3A9A"), glow="#A77BFF", strength=5.0, seed=300 + L)
    if L == 1:
        plinth(m, 0.75)
        stone_drum(m, 0.14, 1.3, 0.62, 0.52)
        door(m, 0.63, w=0.3, h=0.42)
        for deg in (30, 150, 300):
            m.prism("root", "crystal", [(0, -0.08), (0.05, 0), (0, 0.08), (-0.05, 0)], 0.02,
                    loc=polar(0.6, deg, 0.85), rot=(0, 0, deg + 90), glow=True)
        m.cyl("root", "stone2", (0, 0, 1.35), r=0.6, r2=0.56, h=0.1, n=12)
        _prongs(m, 3, (0.46, 1.38), (0.5, 1.8), (0.28, 2.2), "stone3", r=0.065, start=90)
        _crystal_core(m, 1.4, 1.95, 0.12)
        rings, orbit = 0, 0
    elif L == 2:
        plinth(m, 0.85)
        stone_drum(m, 0.14, 1.9, 0.72, 0.58)
        door(m, 0.73)
        for deg, z in ((30, 1.1), (150, 1.1), (270, 1.45)):
            window(m, deg, drum_out(0.14, 1.9, 0.72, 0.58, z) - 0.02, z, lit=True)
        m.cyl("root", "roof", (0, 0, 1.97), r=0.8, r2=0.6, h=0.14, n=10)
        m.cyl("root", "roof2", (0, 0, 1.9), r=0.81, h=0.03, n=10)
        _prongs(m, 4, (0.5, 2.02), (0.58, 2.5), (0.34, 3.0), "stone3", tip_color="gold")
        _crystal_core(m, 2.05, 2.65, 0.15, rings=1)
        rings, orbit = 1, 0
    else:
        plinth(m, 0.92)
        stone_drum(m, 0.14, 2.4, 0.8, 0.62)
        door(m, 0.81, trim="gold")
        for deg, z in ((30, 1.2), (150, 1.2), (210, 1.75), (330, 1.75), (270, 1.85)):
            window(m, deg, drum_out(0.14, 2.4, 0.8, 0.62, z) - 0.02, z, lit=True)
        for z in (0.9, 1.55):
            m.cyl("root", "gold", (0, 0, z), r=drum_out(0.14, 2.4, 0.8, 0.62, z) + 0.01, h=0.04, n=20)
        crenels_round(m, 2.4, 0.66, n=10, h=0.14)
        for deg in (240, 300):
            wall_banner(m, *polar(drum_out(0.14, 2.4, 0.8, 0.62, 1.7), deg, 0)[:2], deg, 2.1, 0.8)
        _prongs(m, 4, (0.56, 2.5), (0.66, 3.1), (0.38, 3.75), "stone3", r=0.08, tip_color="gold")
        _crystal_core(m, 2.6, 3.2, 0.19, rings=2, orbit=3, orbit_r=0.78)
        rings, orbit = 2, 3
    m.build()
    _magic_anims(m, rings, orbit)
    return m


def _ice_shard(m, bone, base, direction, length, r):
    base, d = Vector(base), Vector(direction).normalized()
    mid = base + d * length * 0.72
    col = ("ice", "ice2", "ice3")[m.rng.randrange(3)]
    m.seg(bone, col, base, mid, r, r * 0.9, n=6)
    m.seg(bone, col, mid, base + d * length, r * 0.9, 0, n=6)


def _ice_cluster(m, z, count, ring_r, hmin, hmax, tilt, start=0.0, thick=0.13):
    for k in range(count):
        deg = start + k * 360 / count + m.rng.uniform(-12, 12)
        t = math.radians(tilt + m.rng.uniform(-6, 6))
        a = math.radians(deg)
        length = m.rng.uniform(hmin, hmax)
        _ice_shard(m, "root", polar(ring_r, deg, z), (math.cos(a) * math.sin(t), math.sin(a) * math.sin(t),
                                                       math.cos(t)), length, min(length * thick, 0.12))


def _snow_cap(m, z, r):
    m.cyl("root", "snow", (0, 0, z + 0.04), r=r + 0.03, r2=r - 0.06, h=0.08, n=12, jitter=0.012)
    for k in range(10):
        deg = k * 36 + m.rng.uniform(-8, 8)
        m.cyl("root", "ice3", polar(r + 0.01, deg, z - 0.06), r=0.025, r2=0, h=m.rng.uniform(0.1, 0.2), n=4,
              rot=(180, 0, 0))


def ice(L):
    m = tower_model(f"IceTower{L}", dict(
        stone="#8C97A0", stone2="#76818A", stone3="#A3ADB5", mortar="#5A636B", ice="#A9E4F5", ice2="#7CC6E6",
        ice3="#D8F4FB", snow="#F2F7FA", crystal="#BFF3FF", banner="#3A8FC0"), glow="#7FE8FF", strength=4.5,
        seed=400 + L)
    if L == 1:
        plinth(m, 0.72)
        stone_drum(m, 0.14, 0.8, 0.6, 0.52)
        _snow_cap(m, 0.8, 0.52)
        _ice_cluster(m, 0.84, 6, 0.3, 0.35, 0.7, 20)
        _crystal_core(m, 0.88, 1.55, 0.12)
        rings, orbit = 0, 0
    elif L == 2:
        plinth(m, 0.8)
        stone_drum(m, 0.14, 1.25, 0.66, 0.55)
        door(m, 0.67, w=0.3, h=0.45)
        for deg in (30, 150):
            window(m, deg, drum_out(0.14, 1.25, 0.66, 0.55, 0.8) - 0.02, 0.8, lit=True)
        _ice_cluster(m, 0.1, 6, 0.72, 0.3, 0.5, 50, start=15)
        _snow_cap(m, 1.25, 0.55)
        _ice_cluster(m, 1.29, 8, 0.42, 0.55, 0.95, 20, thick=0.1)
        _crystal_core(m, 1.33, 2.25, 0.15, orbit=3, orbit_r=0.55, orbit_style="shard")
        rings, orbit = 0, 3
    else:
        plinth(m, 0.88)
        stone_drum(m, 0.14, 1.6, 0.74, 0.6)
        door(m, 0.75)
        m.cyl("root", "stone3", (0, 0, 0.85), r=0.72, h=0.08, n=20)
        for deg, z in ((30, 1.15), (150, 1.15), (270, 1.2)):
            window(m, deg, drum_out(0.14, 1.6, 0.74, 0.6, z) - 0.02, z, lit=True)
        for deg in (215, 325):
            wall_banner(m, *polar(drum_out(0.14, 1.6, 0.74, 0.6, 1.1), deg, 0)[:2], deg, 1.45, 0.7)
        _ice_cluster(m, 0.1, 7, 0.8, 0.35, 0.6, 50, start=10)
        _snow_cap(m, 1.6, 0.6)
        _ice_cluster(m, 1.64, 8, 0.5, 1.0, 1.5, 24, thick=0.08)
        _ice_cluster(m, 1.64, 6, 0.36, 0.45, 0.75, 14, start=30, thick=0.1)
        _crystal_core(m, 1.68, 2.85, 0.19, rings=1, orbit=4, orbit_r=0.62, orbit_style="shard")
        rings, orbit = 1, 4
    m.build()
    _magic_anims(m, rings, orbit)
    return m


# --- ballista tower ---------------------------------------------------------------------
def _ballista_gun(m, F, s, fancy):
    P0 = Vector((0, 0, F + 0.55 * s))
    R = Matrix.Rotation(math.radians(-15), 3, "X")  # weapon tilted 15 deg up (anti-air)

    def T(x, y, z):
        return P0 + R @ Vector((x * s, y * s, z * s))

    m.bone("turret", (0, 0, F), "root")
    for side, sx in (("L", 1), ("R", -1)):
        m.bone(f"arm_{side}", T(sx * 0.13, -0.45, 0.06), "turret")
    m.bone("string", T(0, 0.3, 0.13), "turret")
    m.bone("bolt", T(0, 0.25, 0.14), "turret")
    m.bone("muzzle", T(0, -0.92, 0.14), "turret")

    m.seg("turret", "wood2", (0, 0, F), (0, 0, F + 0.5 * s), 0.07 * s, n=8)
    for k in range(4):
        m.seg("turret", "wood2", (0, 0, F + 0.1 * s), polar(0.35 * s, 45 + 90 * k, F + 0.02), 0.04 * s, n=5)
    m.cyl("turret", "iron", (0, 0, F + 0.04), r=0.12 * s, h=0.08 * s, n=8)
    m.box("turret", "wood", (0, 0, F + 0.5 * s), (0.22 * s, 0.12 * s, 0.1 * s), bevel=0.01 * s)

    m.box("turret", "wood", T(0, 0.05, 0.06), (0.14 * s, 1.2 * s, 0.1 * s), rot=(-15, 0, 0), bevel=0.012 * s)
    m.box("turret", "dark", T(0, 0.05, 0.115), (0.04 * s, 1.1 * s, 0.01 * s), rot=(-15, 0, 0))
    m.box("turret", "wood", T(0, -0.45, 0.06), (0.36 * s, 0.14 * s, 0.22 * s), rot=(-15, 0, 0), bevel=0.012 * s)
    for dy in (-0.52, -0.38):
        m.box("turret", "iron", T(0, dy, 0.06), (0.37 * s, 0.02 * s, 0.23 * s), rot=(-15, 0, 0))
    for sx in (1, -1):
        m.seg("turret", "rope", T(sx * 0.13, -0.45, -0.08), T(sx * 0.13, -0.45, 0.2), 0.05 * s, n=8)
        m.seg("turret", "iron", T(sx * 0.13, -0.45, 0.2), T(sx * 0.13, -0.45, 0.23), 0.055 * s, n=8)
    if fancy:
        for dy in (-0.15, 0.25):
            m.box("turret", "iron2", T(0, dy, 0.06), (0.16 * s, 0.12 * s, 0.11 * s), rot=(-15, 0, 0), bevel=0.006)
        for dz in (-0.05, 0.17):
            m.box("turret", "gold", T(0, -0.53, dz), (0.38 * s, 0.025 * s, 0.025 * s), rot=(-15, 0, 0))
        for sx in (1, -1):
            m.cyl("turret", "gold", T(sx * 0.13, -0.45, 0.26), r=0.035 * s, r2=0, h=0.07 * s, n=5, rot=(-15, 0, 0))
    m.seg("turret", "iron", T(-0.12, 0.6, 0.06), T(0.12, 0.6, 0.06), 0.02 * s, n=6)
    for sx in (1, -1):
        c = T(sx * 0.12, 0.6, 0.06)
        m.cyl("turret", "wood2", c, r=0.08 * s, h=0.03 * s, n=8, rot=(0, 90, 0))
        for k in range(4):
            a = math.radians(k * 45)
            spoke = Vector((0, math.cos(a), math.sin(a))) * 0.11 * s
            m.seg("turret", "wood", c - spoke, c + spoke, 0.012 * s, n=4)

    for side, sx in (("L", 1), ("R", -1)):
        root, tip = T(sx * 0.13, -0.45, 0.06), T(sx * 0.62, -0.2, 0.1)
        m.seg(f"arm_{side}", "wood", root, tip, 0.04 * s, 0.025 * s, n=6)
        m.ball(f"arm_{side}", "gold" if fancy else "iron", tip, 0.05 * s)
        m.seg("string", "rope", tip, T(0, 0.3, 0.13), 0.008 * s, n=4)
    m.box("string", "iron", T(0, 0.32, 0.13), (0.06 * s, 0.04 * s, 0.04 * s), rot=(-15, 0, 0))

    m.seg("bolt", "wood", T(0, 0.28, 0.14), T(0, -0.75, 0.14), 0.02 * s, n=6)
    m.seg("bolt", "iron2", T(0, -0.75, 0.14), T(0, -0.9, 0.14), 0.045 * s, 0, n=4)
    for k in range(3):
        a = math.radians(90 + k * 120)
        off = R @ Vector((math.cos(a), 0, math.sin(a)))
        m.slab("bolt", "banner" if fancy else "plank", [T(0, 0.27, 0.14) + off * 0.02 * s, T(0, 0.1, 0.14) + off * 0.02 * s,
                                                         T(0, 0.18, 0.14) + off * 0.07 * s,
                                                         T(0, 0.28, 0.14) + off * 0.06 * s], 0.006)
    return R


def ballista(L):
    m = tower_model(f"BallistaTower{L}", seed=500 + L)
    if L == 1:
        F = wood_frame(m, 1.15, 0.7, 0.62, rail=0.4)
        lantern(m, "flame1", (0.62, -0.62, F + 0.38))
        s = 0.85
    else:
        top, h0, h1 = (1.3, 0.8, 0.72) if L == 2 else (1.9, 0.86, 0.76)
        plinth(m, h0 + 0.1, square=True)
        stone_square(m, 0.14, top, h0, h1)
        door(m, h0 + 0.02)
        for deg in (0, 180):
            window(m, deg, h0 - 0.02, top * 0.62, lit=L == 3)
        crenels_square(m, top, h1)
        F = top + 0.1
        flag(m, "flag1", (h1 - 0.08, h1 - 0.08, F + 0.24), 0.9)
        brazier(m, "flame1", (-0.45, 0.45, F), 0.7)
        s = 1.0
        if L == 3:
            m.box("root", "stone3", (0, 0, top * 0.5), (2 * h0 + 0.02, 2 * h0 + 0.02, 0.08), bevel=0.01)
            for x in (-0.4, 0.4):
                wall_banner(m, x, -(h0 + 0.01), 270, top - 0.25, 0.8)
            brazier(m, "flame2", (h1 - 0.08, -(h1 - 0.08), F + 0.24), 0.6)
            brazier(m, "flame3", (-(h1 - 0.08), -(h1 - 0.08), F + 0.24), 0.6)
            s = 1.15
    R = _ballista_gun(m, F, s, fancy=L == 3)
    m.build()

    idle(m)
    fwd = R @ Vector((0, -0.48 * s, -0.02 * s))
    a = Anim(m, "Shoot", only=("string", "arm_L", "arm_R", "bolt"))
    a.pose(0)
    a.pose(2, string=dict(loc=tuple(fwd)), arm_L=dict(yaw=-22), arm_R=dict(yaw=22), bolt=dict(scale=0.01))
    a.pose(4, string=dict(loc=tuple(fwd * 0.9)), arm_L=dict(yaw=-18), arm_R=dict(yaw=18), bolt=dict(scale=0.01))
    a.pose(14, bolt=dict(scale=0.01))
    a.pose(16)
    a.done()
    return m


# --- projectiles (static meshes, centred on the origin, flying toward -Y) -----------------
def _proj(name, glow="#FFB347", colors=None):
    pal = dict(KINGDOM)
    pal.update(colors or {})
    m = Model(name, pal, glow_color=glow, glow_strength=5.0, metal=METALS, rig=False, ao=0.25)
    m.bone("root", (0, 0, 0))
    return m


def _fletching(m, y0, y1, r0, r1, color):
    for k in range(3):
        a = math.radians(90 + k * 120)
        d = Vector((math.cos(a), 0, math.sin(a)))
        m.slab("root", color, [Vector((0, y0, 0)) + d * r0, Vector((0, y1, 0)) + d * r0,
                               Vector((0, (y0 + y1) / 2 - 0.01, 0)) + d * r1, Vector((0, y0 + 0.01, 0)) + d * r1],
               0.004)


def arrow():
    m = _proj("Arrow", colors=dict(fletch="#E6E0D0", shaft="#A57A48"))
    m.seg("root", "shaft", (0, 0.27, 0), (0, -0.22, 0), 0.009, n=5)
    m.seg("root", "iron2", (0, -0.22, 0), (0, -0.31, 0), 0.022, 0, n=4)
    _fletching(m, 0.26, 0.15, 0.006, 0.035, "fletch")
    m.build()
    return m


def bomb():
    m = _proj("Bomb", glow="#FF9A3A")
    m.ball("root", "ball", (0, 0, 0), 0.26, sub=2)
    m.ring("root", "iron2", (0, 0, 0), 0.13, 0.012, n=16, rot=(90, 0, 0))
    m.cyl("root", "iron2", (0, 0, 0.13), r=0.035, h=0.04, n=6)
    m.seg("root", "rope", (0, 0, 0.15), (0.02, 0.03, 0.22), 0.008, n=4)
    m.cyl("root", "flame", (0.02, 0.03, 0.25), r=0.03, r2=0, h=0.07, n=4, glow=True)
    m.cyl("root", "flame", (0.02, 0.03, 0.25), r=0.03, r2=0, h=0.07, n=4, rot=(90, 0, 45), glow=True)
    m.build()
    return m


def magic_orb():
    m = _proj("MagicOrb", glow="#A77BFF", colors=dict(crystal="#C9A8FF"))
    m.ball("root", "crystal", (0, 0, 0), 0.2, sub=2, glow=True)
    m.ring("root", "crystal", (0, 0, 0), 0.17, 0.01, n=16, rot=(90, 0, 0), glow=True)
    m.ring("root", "crystal", (0, 0, 0), 0.17, 0.01, n=16, rot=(0, 90, 0), glow=True)
    for k in range(4):
        x, y, z = polar(0.24, k * 90 + 45, 0)
        m.cyl("root", "crystal", (x, z, y), r=0.025, r2=0, h=0.06, n=4, glow=True)
    m.build()
    return m


def ice_shard():
    m = _proj("IceShard", glow="#7FE8FF", colors=dict(ice="#A9E4F5", ice2="#7CC6E6", ice3="#D8F4FB"))
    m.seg("root", "ice2", (0, 0.14, 0), (0, -0.1, 0), 0.05, 0.055, n=6)
    m.seg("root", "ice3", (0, -0.1, 0), (0, -0.28, 0), 0.055, 0, n=6, glow=True)
    m.seg("root", "ice", (0, 0.14, 0), (0, 0.22, 0), 0.05, 0, n=6)
    for sx in (1, -1):
        m.seg("root", "ice3", (sx * 0.03, 0.05, 0), (sx * 0.09, 0.14, 0.02), 0.022, 0, n=5)
    m.build()
    return m


def ballista_bolt():
    m = _proj("BallistaBolt", colors=dict(fletch="#2F5DA8"))
    m.seg("root", "wood", (0, 0.55, 0), (0, -0.45, 0), 0.022, n=6)
    m.seg("root", "iron2", (0, -0.45, 0), (0, -0.64, 0), 0.05, 0, n=4)
    m.slab("root", "iron", [(0, -0.42, 0.0), (0.07, -0.47, 0), (0, -0.56, 0), (-0.07, -0.47, 0)], 0.01)
    for y in (-0.42, 0.4):
        m.seg("root", "iron", (0, y, 0), (0, y - 0.03, 0), 0.026, n=6)
    _fletching(m, 0.53, 0.3, 0.02, 0.08, "fletch")
    m.build()
    return m


TOWERS = {f"{kind}_{L}": partial(fn, L)
          for kind, fn in (("archer", archer), ("cannon", cannon), ("mage", mage), ("ice", ice),
                           ("ballista", ballista)) for L in (1, 2, 3)}
PROJECTILES = dict(arrow=arrow, bomb=bomb, magic_orb=magic_orb, ice_shard=ice_shard, ballista_bolt=ballista_bolt)
