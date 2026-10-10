"""Level 2 "Haunted Forest" decor: leafless trees, graves, a crypt, ancient ruins, cemetery fence and gate,
ghost lanterns and a few extras (ritual stones, scarecrow, witch's cauldron, bones, glowing mushrooms).

Same conventions as the props in env.py: one mesh, no rig, ground at z = 0, fits a 2 x 2 m cell, front -Y.
Every model glows the same faint purple (runes, ghost candles, lanterns, mushrooms) through the Glow
material; GLOW_STRENGTH is kept low on purpose - the night scene and bloom do the rest.
Stone colours are overridden with a cold grey, so the masonry helpers from towers.py / env.py fit in.
"""
import math
from functools import partial

from mathutils import Euler, Quaternion, Vector

from env import ENV, FOLIAGE, stone_wall, terrain_tile
from lowpoly import Model, rag, rots
from towers import KINGDOM, METALS, polar

GLOW = "#A45CFF"
GLOW_STRENGTH = 2.2

HAUNT = dict(
    stone="#807D86", stone2="#6C6A73", stone3="#94919B", mortar="#43414A",
    slate="#4A4853", slate2="#3A3842",
    deadbark="#4D433C", deadbark2="#3B332E", deadbark3="#64584D",
    earth="#4A3D31", earth2="#3A3028", earth3="#5C4B3B",
    moss="#4B6638", moss2="#3C552F", hang="#6D7A62",
    bone="#D9D3C0", bone2="#BDB5A0", socket="#16121B",
    wood="#5C4837", wood2="#46372A", plank="#6E5843", plank2="#5D4A38",
    iron="#3C4046", iron2="#5E646B", pot="#2B2C31",
    cloth="#5E5448", cloth2="#433B33", sack="#9A8564", straw="#B39858", rope="#8C7A58",
    candle="#D6CDB5", stem2="#CEC4DA", shroom="#4A3366",
    crow="#1E1C23", crow2="#2B2932", beak="#3B3631", bottle="#2F5A4A", cork="#8A6A45",
    rune=GLOW)


def _model(name, seed, **kw):
    pal = dict(KINGDOM)
    pal.update(ENV)
    pal.update(HAUNT)
    m = Model(name, pal, glow_color=GLOW, glow_strength=GLOW_STRENGTH, metal=METALS, foliage=FOLIAGE + ("hang",),
              rig=False, seed=seed, **kw)
    m.bone("root", (0, 0, 0))
    return m


class Frame:
    """Local frame for a tilted group of parts: p() maps a local point, r() composes a part rotation."""

    def __init__(self, loc=(0, 0, 0), rot=(0, 0, 0)):
        self.t = Vector(loc)
        self.rot = tuple(rot)
        self.R = Euler([math.radians(a) for a in rot]).to_matrix()

    def p(self, v):
        return tuple(self.t + self.R @ Vector(v))

    def r(self, rot=(0, 0, 0)):
        return rots(rot, self.rot)


# --- shared pieces ----------------------------------------------------------------------------
def _rand_dir(rng):
    return Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))


def _limb(m, p, d, length, r, depth, color="deadbark", spread=35, forks=(2, 3), wander=0.35, rise=0.12, nodes=None):
    """Gnarled branch: a few kinked segments, then forks; recursion ends in thin twig tips.
    Kink points go to `nodes` as (point, direction, radius, depth) for hanging moss, crows etc."""
    rng = m.rng
    p, d = Vector(p), Vector(d).normalized()
    kinks = 3 if r > 0.06 else 2
    r_end = max(r * 0.6, 0.012)
    tip_r = r_end if depth else 0.004
    for k in range(kinks):
        d = (d + _rand_dir(rng) * wander + Vector((0, 0, rise))).normalized()
        q = p + d * (length / kinks)
        ra = r + (tip_r - r) * k / kinks
        rb = r + (tip_r - r) * (k + 1) / kinks
        m.seg("root", color, p - d * ra * 0.3, q, ra, rb, n=6 if ra > 0.05 else 5 if ra > 0.025 else 4)
        if nodes is not None:
            nodes.append((q.copy(), d.copy(), rb, depth))
        p = q
    if depth == 0:
        return
    side = d.orthogonal().normalized()
    base = rng.uniform(0, 360)
    n = rng.randint(*forks)
    for i in range(n):
        perp = Quaternion(d, math.radians(base + i * 360 / n + rng.uniform(-25, 25))) @ side
        s = math.radians(spread * rng.uniform(0.7, 1.3))
        _limb(m, p, d * math.cos(s) + perp * math.sin(s), length * rng.uniform(0.6, 0.8),
              r_end * rng.uniform(0.75, 0.95), depth - 1, color, spread, forks, wander, rise, nodes)


def _trunk(m, pts, radii, color="deadbark", n=8):
    for a, b, ra, rb in zip(pts, pts[1:], radii, radii[1:]):
        m.seg("root", color, a, b, ra, rb, n=n, jitter=0.01)


def _roots(m, count, reach, r, z=0.25, start=0.0, color="deadbark2"):
    for k in range(count):
        deg = start + k * 360 / count + m.rng.uniform(-15, 15)
        mid = polar(reach * 0.45, deg, z * 0.35)
        m.seg("root", color, (0, 0, z), mid, r, r * 0.6, n=5)
        m.seg("root", color, mid, polar(reach * m.rng.uniform(0.85, 1.1), deg, -0.03), r * 0.6, 0.015, n=5)


def _hanging_moss(m, nodes, count, zmin=1.3):
    picks = [nd for nd in nodes if nd[0].z > zmin and nd[2] < 0.07]
    m.rng.shuffle(picks)
    for p, _, r, _ in picks[:count]:
        for k in range(m.rng.randint(1, 3)):
            top = p + Vector((m.rng.uniform(-0.04, 0.04), m.rng.uniform(-0.04, 0.04), -r))
            bottom = top + Vector((m.rng.uniform(-0.05, 0.05), m.rng.uniform(-0.05, 0.05),
                                   -m.rng.uniform(0.25, 0.6)))
            m.seg("root", m.rng.choice(("hang", "moss2")), top, bottom, 0.022, 0.004, n=3)


def _crow(m, p, yaw=0.0, s=1.0):
    """Perched crow (~0.25 m) with faintly glowing eyes; p is where its feet touch the perch."""
    F = Frame(p, (0, 0, yaw))

    def P(x, y, z):
        return F.p((x * s, y * s, z * s))

    m.ball("root", "crow", P(0, 0.02, 0.11), (0.11 * s, 0.2 * s, 0.12 * s), rot=F.r((-15, 0, 0)))
    m.ball("root", "crow2", P(0, -0.09, 0.19), 0.09 * s)
    m.cyl("root", "beak", P(0, -0.165, 0.185), r=0.02 * s, r2=0, h=0.07 * s, n=4, rot=F.r((95, 0, 0)))
    m.box("root", "crow2", P(0, 0.18, 0.08), (0.08 * s, 0.16 * s, 0.015 * s), rot=F.r((-20, 0, 0)), taper=1.0)
    for sx in (1, -1):
        m.ball("root", "crow2", P(sx * 0.055, 0.04, 0.12), (0.04 * s, 0.19 * s, 0.09 * s), rot=F.r((-12, 0, 0)))
        m.seg("root", "beak", P(sx * 0.025, 0, 0.0), P(sx * 0.025, 0.005, 0.06), 0.007 * s, n=3)
        m.ball("root", "rune", P(sx * 0.035, -0.125, 0.205), 0.018 * s, glow=True)


def _skull(m, p, yaw=0.0, s=1.0, pitch=0.0, jaw=True):
    F = Frame(p, (pitch, 0, yaw))

    def P(x, y, z):
        return F.p((x * s, y * s, z * s))

    m.ball("root", "bone", P(0, 0.01, 0.095), (0.15 * s, 0.17 * s, 0.14 * s), rot=F.r())
    m.box("root", "bone", P(0, -0.055, 0.06), (0.11 * s, 0.06 * s, 0.07 * s), rot=F.r(), bevel=0.012 * s)
    for sx in (1, -1):
        m.box("root", "socket", P(sx * 0.028, -0.084, 0.074), (0.036 * s, 0.02 * s, 0.03 * s), rot=F.r())
    m.box("root", "socket", P(0, -0.086, 0.047), (0.016 * s, 0.02 * s, 0.02 * s), rot=F.r())
    if jaw:
        m.box("root", "bone2", P(0, -0.05, 0.02), (0.09 * s, 0.06 * s, 0.03 * s), rot=F.r(), bevel=0.006 * s)


def _bone(m, a, b, r=0.018):
    m.seg("root", "bone2", a, b, r, n=5)
    for p in (a, b):
        m.ball("root", "bone", p, (r * 2.4, r * 2.4, r * 1.8))


def _candle(m, p, h=0.12, r=0.025):
    x, y, z = p
    m.cyl("root", "candle", (x, y, z + h / 2), r=r, h=h, n=6)
    m.cyl("root", "candle", (x, y, z + 0.012), r=r * 1.5, r2=r * 1.1, h=0.024, n=6)
    m.seg("root", "socket", (x, y, z + h), (x, y, z + h + 0.015), 0.004, n=3)
    m.ball("root", "rune", (x, y, z + h + 0.04), (0.032, 0.032, 0.06), glow=True)


def _lantern(m, p, s=1.0):
    """Iron lantern with a ghostly flame; p is the bottom plate centre, total height 0.33*s."""
    x, y, z = p
    m.box("root", "iron", (x, y, z), (0.15 * s, 0.15 * s, 0.025 * s))
    m.box("root", "iron", (x, y, z + 0.16 * s), (0.17 * s, 0.17 * s, 0.025 * s))
    m.cyl("root", "iron", (x, y, z + 0.22 * s), r=0.12 * s, r2=0, h=0.1 * s, n=4, rot=(0, 0, 45))
    m.ring("root", "iron", (x, y, z + 0.3 * s), 0.025 * s, 0.006 * s, n=6, rot=(90, 0, 0))
    for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        m.seg("root", "iron", (x + dx * 0.07 * s, y + dy * 0.07 * s, z), (x + dx * 0.07 * s, y + dy * 0.07 * s,
                                                                           z + 0.16 * s), 0.008 * s, n=3)
    m.box("root", "rune", (x, y, z + 0.08 * s), (0.08 * s, 0.08 * s, 0.11 * s), glow=True)


def _glyph(m, F, loc, kind=0, s=1.0, rot=(0, 0, 0)):
    """Small glowing rune on a surface facing local -Y."""
    shapes = ([(0, -0.06), (0.04, 0), (0, 0.06), (-0.04, 0)],
              [(-0.012, -0.06), (0.012, -0.06), (0.012, 0.0), (0.04, 0.03), (0.03, 0.045), (0.0, 0.02),
               (-0.03, 0.045), (-0.04, 0.03), (-0.012, 0.0)],
              [(-0.04, -0.05), (0.04, -0.05), (0.0, 0.06)])
    pts = [(x * s, z * s) for x, z in shapes[kind % len(shapes)]]
    m.prism("root", "rune", pts, 0.012, loc=F.p(loc), rot=F.r(rot), glow=True)


def _mound(m, x, y, length, width, h=0.28):
    m.ball("root", "earth", (x, y, -0.02), (width, length, h), sub=2, jitter=0.02)
    for _ in range(3):
        px, py = x + m.rng.uniform(-width, width) * 0.4, y + m.rng.uniform(-length, length) * 0.4
        m.ball("root", "earth3", (px, py, h * 0.32), (0.08, 0.07, 0.05), rot=(0, 0, m.rng.uniform(0, 180)))


def _tufts(m, spots):
    for x, y in spots:
        for _ in range(m.rng.randint(3, 4)):
            m.cyl("root", m.rng.choice(("tuft", "tuft2")), (x + m.rng.uniform(-0.04, 0.04),
                                                            y + m.rng.uniform(-0.04, 0.04), 0.06),
                  r=0.018, r2=0, h=m.rng.uniform(0.12, 0.2), n=3,
                  rot=(m.rng.uniform(-25, 25), m.rng.uniform(-25, 25), m.rng.uniform(0, 120)))


def _rubble(m, count, x0, x1, y0, y1, smin=0.1, smax=0.22, colors=("stone", "stone2", "stone3")):
    rng = m.rng
    for _ in range(count):
        s = rng.uniform(smin, smax)
        m.box("root", rng.choice(colors), (rng.uniform(x0, x1), rng.uniform(y0, y1), s * 0.35),
              (s, s * rng.uniform(0.7, 1.0), s * rng.uniform(0.6, 0.9)),
              rot=(rng.uniform(-12, 12), rng.uniform(-12, 12), rng.uniform(0, 90)), bevel=s * 0.12, jitter=s * 0.06)


def _moss(m, p, size, rot=(0, 0, 0)):
    m.ball("root", m.rng.choice(("moss", "moss2")), p, size, rot=rot, jitter=min(size) * 0.15)


# --- trees ----------------------------------------------------------------------------------
def gnarled_tree(v):
    m = _model(f"GnarledTree{v}", seed=2000 + v)
    nodes = []
    if v == 1:
        # squat old oak: thick twisted trunk, wide crown of bare limbs, a hollow with eyes, a crow
        _trunk(m, [(0, 0, 0), (0.08, 0.02, 0.6), (-0.04, 0.06, 1.1), (0.05, 0.0, 1.45)], [0.3, 0.24, 0.2, 0.17])
        top = Vector((0.05, 0.0, 1.4))
        for deg, tilt, length in ((20, 55, 1.05), (140, 50, 0.95), (260, 45, 1.1), (330, 25, 0.8)):
            a, t = math.radians(deg), math.radians(tilt)
            d = Vector((math.cos(a) * math.sin(t), math.sin(a) * math.sin(t), math.cos(t)))
            _limb(m, top, d, length, 0.12, 3, spread=40, nodes=nodes)
        _roots(m, 5, 0.75, 0.13, z=0.3)
        m.seg("root", "deadbark", (0.04, 0.02, 1.15), (-0.45, -0.25, 1.5), 0.08, 0.05, n=6)
        m.seg("root", "deadbark", (-0.45, -0.25, 1.5), (-0.8, -0.32, 1.52), 0.05, 0.025, n=5)
        _crow(m, (-0.66, -0.3, 1.55), yaw=-70)
        # hollow: dark oval with a bark rim and two faint eyes inside
        m.ball("root", "socket", (0.06, -0.21, 0.6), (0.17, 0.12, 0.3))
        m.ring("root", "deadbark3", (0.06, -0.255, 0.6), 0.14, 0.035, n=10, squash=(0.62, 1.0), rot=(90, 0, 0))
        for sx in (1, -1):
            m.ball("root", "rune", (0.06 + sx * 0.03, -0.27, 0.64), (0.025, 0.01, 0.018), glow=True)
        _moss(m, (0.12, 0.12, 0.35), (0.3, 0.22, 0.25))
    else:
        # tall, leaning, thin tree draped with hanging moss
        _trunk(m, [(0, 0, 0), (0.1, 0.05, 0.9), (0.3, 0.0, 1.7), (0.38, 0.1, 2.3)], [0.2, 0.15, 0.12, 0.09], n=7)
        _limb(m, (0.38, 0.1, 2.25), (0.1, 0.1, 1), 0.9, 0.08, 3, spread=38, nodes=nodes)
        _limb(m, (0.2, 0.03, 1.4), (-1, -0.3, 0.6), 0.9, 0.07, 2, spread=35, rise=0.06, nodes=nodes)
        _limb(m, (0.32, 0.03, 1.9), (0.6, -0.8, 0.5), 0.8, 0.06, 2, spread=35, rise=0.06, nodes=nodes)
        _roots(m, 4, 0.6, 0.11, z=0.25, start=30)
        _hanging_moss(m, nodes, 12)
    m.build()
    return m


def dead_spruce():
    """Dead spruce: whorls of drooping bare branches, broken top."""
    m = _model("DeadSpruce", seed=2010)
    rng = m.rng
    _trunk(m, [(0, 0, 0), (0.02, 0.0, 1.6), (-0.03, 0.02, 2.95)], [0.16, 0.1, 0.045], n=7)
    for k in range(4):  # splintered top
        m.seg("root", "deadbark3", polar(0.025, k * 90, 2.9, (-0.03, 0.02)),
              polar(0.04, k * 90 + 20, 2.95 + rng.uniform(0.08, 0.25), (-0.03, 0.02)), 0.025, 0.0, n=3)
    z, i = 0.8, 0
    while z < 2.8:
        t = (z - 0.8) / 2.0
        length = 0.95 * (1 - 0.65 * t)
        for k in range(5):
            if rng.random() < 0.25:
                continue
            deg = k * 72 + i * 31 + rng.uniform(-12, 12)
            base = polar(0.05, deg, z)
            end = polar(length * rng.uniform(0.75, 1.05), deg, z - length * 0.35)
            m.seg("root", "deadbark", base, end, 0.035 * (1 - 0.4 * t), 0.008, n=4)
            mid = Vector(base).lerp(Vector(end), 0.5)
            for side in (35, -35):
                twig = polar(length * 0.3, deg + side, mid.z - 0.08, (mid.x, mid.y))
                m.seg("root", "deadbark3", mid, twig, 0.012, 0.003, n=3)
        z += 0.27
        i += 1
    _roots(m, 4, 0.5, 0.09, z=0.2, start=10)
    m.build()
    return m


def hollow_stump():
    """Broken hollow trunk with jagged splinters and glowing shelf fungi."""
    m = _model("HollowStump", seed=2020)
    rng = m.rng
    m.cyl("root", "deadbark", (0, 0, 0.27), r=0.38, r2=0.32, h=0.55, n=10, jitter=0.012)
    m.cyl("root", "socket", (0, 0, 0.552), r=0.24, h=0.012, n=10)
    for k in range(8):
        deg = k * 45 + rng.uniform(-8, 8)
        h = rng.uniform(0.06, 0.22) if k not in (2, 3) else rng.uniform(0.35, 0.5)
        m.seg("root", rng.choice(("deadbark", "deadbark3")), polar(0.29, deg, 0.5),
              polar(0.31, deg + rng.uniform(-6, 6), 0.55 + h), 0.11, 0.0, n=4)
    _roots(m, 5, 0.6, 0.12, z=0.15)
    for deg, z, s in ((300, 0.35, 1.0), (330, 0.22, 0.75), (60, 0.42, 0.85)):
        x, y, _ = polar(0.36, deg, 0)
        m.ball("root", "rune", (x, y, z), (0.18 * s, 0.18 * s, 0.045 * s), rot=(0, 0, deg), glow=True)
    _moss(m, polar(0.3, 150, 0.2), (0.3, 0.25, 0.2))
    m.build()
    return m


def dead_bush():
    m = _model("DeadBush", seed=2030)
    rng = m.rng
    for k in range(7):
        a = math.radians(k * 51 + rng.uniform(-10, 10))
        tilt = math.radians(rng.uniform(25, 55))
        d = (math.cos(a) * math.sin(tilt), math.sin(a) * math.sin(tilt), math.cos(tilt))
        _limb(m, (0, 0, 0), d, rng.uniform(0.45, 0.7), 0.03, 2, color="deadbark3", spread=32, forks=(2, 2),
              wander=0.4, rise=0.08)
    m.ball("root", "earth", (0, 0, -0.03), (0.4, 0.4, 0.12))
    m.build()
    return m


def glow_mushrooms():
    m = _model("GlowMushrooms", seed=2040)
    for x, y, h, r, lit in ((0, 0, 0.2, 0.11, True), (0.17, 0.09, 0.13, 0.08, True), (-0.13, 0.13, 0.09, 0.06, False),
                            (0.06, -0.18, 0.11, 0.07, True), (-0.2, -0.07, 0.07, 0.05, True),
                            (0.25, -0.12, 0.06, 0.04, False), (-0.05, 0.25, 0.12, 0.06, True)):
        m.seg("root", "stem2", (x, y, 0), (x + 0.01, y, h), r * 0.28, r * 0.22, n=6)
        m.cyl("root", "rune" if lit else "shroom", (x + 0.01, y, h + r * 0.15), r=r, r2=r * 0.25, h=r * 0.55, n=8,
              glow=lit)
    m.ball("root", "moss2", (0, 0, -0.02), (0.5, 0.45, 0.06), jitter=0.015)
    m.build()
    return m


# --- graves -----------------------------------------------------------------------------------
def _headstone(m, F, w=0.48, h=0.6, rune=0, lit=True):
    """Rounded headstone on a plinth, facing local -Y; `lit` adds the faint glowing rune."""
    m.box("root", "stone2", F.p((0, 0, 0.06)), (w + 0.14, 0.26, 0.12), rot=F.r(), bevel=0.02)
    m.box("root", "stone", F.p((0, 0, 0.1 + h / 2)), (w, 0.13, h), rot=F.r(), bevel=0.02, jitter=0.004)
    m.cyl("root", "stone", F.p((0, 0, 0.1 + h)), r=w / 2, h=0.13, n=10, rot=F.r((90, 0, 0)))
    for z, lw in ((0.38, 0.3), (0.31, 0.24), (0.25, 0.28)):
        m.box("root", "stone2", F.p((0, -0.062, z * h / 0.6)), (lw * w / 0.48, 0.012, 0.025), rot=F.r())
    if lit:
        m.ring("root", "rune", F.p((0, -0.068, 0.1 + h * 0.85)), 0.075, 0.011, n=12, m=3, rot=F.r((90, 0, 0)),
               glow=True)
        _glyph(m, F, (0, -0.07, 0.1 + h * 0.85), kind=rune, s=0.8)


def grave(v):
    m = _model(f"Grave{v}", seed=2100 + v)
    if v == 1:
        _mound(m, 0, -0.15, 1.1, 0.55)
        _headstone(m, Frame((0, 0.5, 0), (-6, 4, 0)), rune=1)
        _moss(m, (0.1, 0.52, 0.92), (0.2, 0.15, 0.07))
        _tufts(m, ((0.4, 0.3), (-0.35, -0.5), (0.3, -0.65)))
    elif v == 2:
        # leaning stone cross with a ring
        _mound(m, 0, -0.2, 1.0, 0.5)
        F = Frame((0.02, 0.45, 0), (-4, 10, 6))
        m.box("root", "stone2", F.p((0, 0, 0.05)), (0.5, 0.4, 0.1), rot=F.r(), bevel=0.02)
        m.box("root", "stone", F.p((0, 0, 0.16)), (0.34, 0.26, 0.12), rot=F.r(), bevel=0.02)
        m.box("root", "stone3", F.p((0, 0, 0.72)), (0.14, 0.12, 1.0), rot=F.r(), bevel=0.015, jitter=0.004)
        m.box("root", "stone3", F.p((0, 0, 0.98)), (0.56, 0.12, 0.14), rot=F.r(), bevel=0.015, jitter=0.004)
        m.ring("root", "stone", F.p((0, 0, 0.98)), 0.17, 0.03, n=12, rot=F.r((90, 0, 0)))
        _glyph(m, F, (0, -0.066, 0.98), kind=0, s=0.9)
        _moss(m, F.p((-0.2, 0, 1.06)), (0.14, 0.13, 0.05))
        _tufts(m, ((-0.4, 0.2), (0.35, -0.45)))
    else:
        # broken headstone, the fallen piece, a skull and ghost candles
        _mound(m, 0, -0.15, 0.95, 0.5)
        F = Frame((0, 0.5, 0), (0, 0, -8))
        m.box("root", "stone2", F.p((0, 0, 0.06)), (0.6, 0.26, 0.12), rot=F.r(), bevel=0.02)
        broken = [(-0.22, 0.1), (0.22, 0.1), (0.22, 0.48), (0.12, 0.56), (0.05, 0.45), (-0.06, 0.62), (-0.14, 0.55),
                  (-0.22, 0.66)]
        m.prism("root", "stone", broken, 0.12, loc=F.p((0, 0, 0)), rot=F.r())
        _glyph(m, F, (-0.08, -0.063, 0.36), kind=2, s=0.9)
        m.prism("root", "stone", [(-0.2, 0), (0.2, 0), (0.15, 0.28), (0.02, 0.18), (-0.18, 0.26)], 0.12,
                loc=(0.48, 0.2, 0.06), rot=(88, 0, 35))
        _skull(m, (-0.36, -0.2, 0), yaw=25)
        for p, h in (((0.3, 0.3, 0), 0.14), ((0.38, 0.12, 0), 0.09), ((-0.32, 0.32, 0), 0.11)):
            _candle(m, p, h)
        _tufts(m, ((-0.4, -0.55), (0.35, -0.5)))
    m.build()
    return m


def grave_open():
    """Freshly dug grave: dark pit, dirt pile with a shovel, coffin lid aside, small headstone."""
    m = _model("GraveOpen", seed=2110)
    m.box("root", "socket", (0, 0, 0.012), (0.62, 1.12, 0.024))
    for x, y, sx, sy in ((0.39, 0, 0.18, 1.32), (-0.39, 0, 0.18, 1.32), (0, 0.64, 0.96, 0.18), (0, -0.64, 0.96, 0.18)):
        m.box("root", "earth", (x, y, 0.05), (sx, sy, 0.1), bevel=0.03, jitter=0.015)
    for x, y, sx, sy, rx, ry in ((0.29, 0, 0.06, 1.1, 0, 40), (-0.29, 0, 0.06, 1.1, 0, -40),
                                 (0, 0.54, 0.6, 0.06, -40, 0), (0, -0.54, 0.6, 0.06, 40, 0)):
        m.box("root", "earth2", (x, y, 0.03), (sx, sy, 0.06), rot=(rx, ry, 0))
    m.ball("root", "earth", (0.68, 0.1, 0.0), (0.5, 0.9, 0.55), sub=2, jitter=0.03)
    m.ball("root", "earth3", (0.7, -0.15, 0.2), (0.22, 0.25, 0.12), jitter=0.02)
    m.seg("root", "wood", (0.66, 0.22, 0.12), (0.55, 0.05, 1.0), 0.022, n=5)
    m.box("root", "wood2", (0.545, 0.04, 1.02), (0.16, 0.03, 0.03), rot=(0, -7, 0))
    m.box("root", "iron2", (0.675, 0.24, 0.12), (0.2, 0.03, 0.26), rot=(18, -7, 0), bevel=0.01)
    coffin = [(-0.15, -0.5), (0.15, -0.5), (0.22, 0.28), (0.15, 0.5), (-0.15, 0.5), (-0.22, 0.28)]
    F = Frame((-0.66, -0.05, 0.06), (0, -16, 6))
    m.slab("root", "plank2", [(x, y, 0) for x, y in coffin], 0.05, loc=F.p((0, 0, 0)), rot=F.r())
    m.box("root", "wood2", F.p((0, 0.08, 0.03)), (0.05, 0.62, 0.015), rot=F.r())
    m.box("root", "wood2", F.p((0, 0.25, 0.03)), (0.28, 0.05, 0.015), rot=F.r())
    _headstone(m, Frame((0, 0.84, 0.0), (-3, 0, 4)), w=0.4, h=0.45, rune=2)
    _tufts(m, ((-0.6, 0.65), (-0.5, -0.75), (0.3, -0.85)))
    m.build()
    return m


def crypt():
    """Small mausoleum: masonry walls, slate gable roof on a portico, a door left ajar with purple light."""
    m = _model("Crypt", seed=2200)
    m.box("root", "stone2", (0, 0.04, 0.06), (1.8, 1.9, 0.12), bevel=0.03, jitter=0.01)
    m.box("root", "stone", (0, 0.13, 0.18), (1.6, 1.62, 0.12), bevel=0.03)
    z0, z1, W, Y0, Y1 = 0.24, 1.5, 0.7, -0.45, 0.85
    stone_wall(m, (-W, Y1), (W, Y1), z0, z1, depth=0.28)
    stone_wall(m, (-W, Y0), (-W, Y1), z0, z1, depth=0.28)
    stone_wall(m, (W, Y0), (W, Y1), z0, z1, depth=0.28)
    stone_wall(m, (-W, Y0), (-0.3, Y0), z0, z1, depth=0.28)
    stone_wall(m, (0.3, Y0), (W, Y0), z0, z1, depth=0.28)
    stone_wall(m, (-0.3, Y0), (0.3, Y0), 1.08, z1, depth=0.28)
    m.box("root", "socket", (0, 0.2, 0.8), (1.1, 1.1, 1.0))
    # doorway: ghost light inside, left leaf shut, right leaf ajar
    m.box("root", "rune", (0, -0.36, 0.66), (0.58, 0.02, 0.84), glow=True)
    m.box("root", "iron", (-0.15, -0.47, 0.66), (0.29, 0.05, 0.84), bevel=0.01)
    F = Frame((0.3, -0.45, 0.66), (0, 0, -38))
    m.box("root", "iron", F.p((-0.145, 0, 0)), (0.29, 0.05, 0.84), rot=F.r(), bevel=0.01)
    for z in (-0.25, 0.25):
        m.box("root", "iron2", (-0.15, -0.5, 0.66 + z), (0.29, 0.012, 0.04))
        m.box("root", "iron2", F.p((-0.145, -0.03, z)), (0.29, 0.012, 0.04), rot=F.r())
    m.ring("root", "iron2", (-0.05, -0.51, 0.66), 0.035, 0.008, n=8, rot=(90, 0, 0))
    _glyph(m, Frame((0, -0.63, 1.3)), (0, 0, 0), kind=1, s=1.2)
    m.ring("root", "rune", (0, -0.63, 1.3), 0.1, 0.012, n=12, m=3, rot=(90, 0, 0), glow=True)
    # portico columns on the lower step
    for x in (-0.58, 0.58):
        m.box("root", "stone2", (x, -0.79, 0.17), (0.22, 0.22, 0.1), bevel=0.015)
        m.cyl("root", "stone3", (x, -0.79, 0.85), r=0.075, r2=0.065, h=1.3, n=8)
        m.box("root", "stone2", (x, -0.79, 1.48), (0.22, 0.22, 0.06), bevel=0.015)
    m.box("root", "stone", (0, -0.79, 1.56), (1.5, 0.22, 0.12), bevel=0.02)
    # gable roof (ridge along Y) with pediments and tile rows
    w, a = 0.88, 32.0
    rise = w * math.tan(math.radians(a))
    zr = 1.62
    for sx in (1, -1):
        S = Frame((sx * w / 2, 0.0, zr + rise / 2), (0, sx * a, 0))
        m.box("root", "slate", S.p((0, 0, 0)), (w / math.cos(math.radians(a)) + 0.04, 1.96, 0.07), rot=S.r())
        for t in (-0.3, 0.0, 0.3):
            m.box("root", "slate2", S.p((t, 0, 0.045)), (0.05, 1.98, 0.03), rot=S.r())
        _moss(m, S.p((sx * 0.15, m.rng.uniform(-0.6, 0.6), 0.05)), (0.3, 0.35, 0.06), rot=S.r())
    for y in (-0.92, 0.92):
        m.prism("root", "stone", [(-w * 0.92, 0), (w * 0.92, 0), (0, rise * 0.92)], 0.1, loc=(0, y, zr))
    m.ring("root", "rune", (0, -0.975, zr + 0.2), 0.08, 0.011, n=12, m=3, rot=(90, 0, 0), glow=True)
    m.seg("root", "stone2", (0, -1.0, zr + rise + 0.02), (0, 1.0, zr + rise + 0.02), 0.045, n=6)
    m.box("root", "stone3", (0, -0.92, zr + rise + 0.22), (0.07, 0.07, 0.42), bevel=0.01)
    m.box("root", "stone3", (0, -0.92, zr + rise + 0.3), (0.26, 0.07, 0.07), bevel=0.01)
    for x in (-0.32, 0.32):
        _candle(m, (x, -0.86, 0.12), 0.13)
    m.box("root", "slate", (0.85, -0.5, 0.04), (0.3, 0.2, 0.04), rot=(6, -10, 30))
    _rubble(m, 3, -0.95, -0.7, 0.2, 0.9)
    m.build()
    return m


def obelisk():
    m = _model("Obelisk", seed=2210)
    m.box("root", "stone2", (0, 0, 0.075), (0.9, 0.9, 0.15), bevel=0.03, jitter=0.008)
    m.box("root", "stone", (0, 0, 0.225), (0.7, 0.7, 0.15), bevel=0.025)
    m.box("root", "stone2", (0, 0, 0.4), (0.5, 0.5, 0.2), bevel=0.02)
    m.box("root", "stone3", (0, 0, 1.3), (0.34, 0.34, 1.6), taper=0.65, bevel=0.015)
    m.cyl("root", "stone3", (0, 0, 2.24), r=0.157, r2=0, h=0.28, n=4, rot=(0, 0, 45))
    for k, z in enumerate((0.8, 1.15, 1.5, 1.8)):
        half = 0.17 * (1 - 0.35 * (z - 0.5) / 1.6)
        _glyph(m, Frame((0, -half - 0.004, z)), (0, 0, 0), kind=k, s=0.75)
    m.box("root", "stone2", (0.48, -0.35, 0.07), (0.22, 0.18, 0.14), rot=(8, -6, 25), bevel=0.02, jitter=0.01)
    _moss(m, (-0.3, 0.25, 0.17), (0.35, 0.3, 0.08))
    _moss(m, (0.2, 0.18, 0.31), (0.2, 0.22, 0.05))
    m.build()
    return m


# --- cemetery fence, gate and lantern ------------------------------------------------------------
def _stone_post(m, x, y, h=0.85, s=0.2):
    m.box("root", "stone", (x, y, h / 2), (s, s, h), bevel=0.02, jitter=0.004)
    m.box("root", "stone3", (x, y, h + 0.03), (s + 0.06, s + 0.06, 0.06), bevel=0.015)
    m.cyl("root", "stone2", (x, y, h + 0.13), r=(s + 0.04) * 0.7, r2=0, h=0.14, n=4, rot=(0, 0, 45))


def _iron_bars(m, F, x0, x1, z0, z1, step=0.16, skip=(), bent=()):
    """Spiked iron railing in a local frame, spanning local x0..x1."""
    count = int(round((x1 - x0) / step))
    for i in range(count + 1):
        if i in skip:
            continue
        x = x0 + (x1 - x0) * i / count
        top = (x + 0.12, -0.1, z1 - 0.05) if i in bent else (x, 0, z1)
        m.seg("root", "iron", F.p((x, 0, z0)), F.p(top), 0.012, n=4)
        m.cyl("root", "iron", F.p((top[0], top[1], top[2] + 0.05)), r=0.028, r2=0, h=0.1, n=4, rot=F.r())
    for z in (z0 + 0.12, z1 - 0.15):
        m.seg("root", "iron", F.p((x0 - 0.02, 0, z)), F.p((x1 + 0.02, 0, z)), 0.014, n=4)


def cemetery_fence():
    m = _model("CemeteryFence", seed=2300)
    for x in (-0.9, 0.9):
        _stone_post(m, x, 0)
    m.box("root", "stone2", (0, 0, 0.04), (1.7, 0.16, 0.08), bevel=0.015, jitter=0.006)
    _iron_bars(m, Frame(), -0.72, 0.72, 0.08, 0.85, skip=(6,), bent=(3,))
    m.seg("root", "hang", (0.24, -0.02, 0.8), (0.26, -0.03, 0.35), 0.02, 0.004, n=3)
    _moss(m, (-0.4, 0, 0.08), (0.3, 0.17, 0.05))
    _tufts(m, ((0.5, -0.15), (-0.7, 0.15)))
    m.build()
    return m


def cemetery_gate():
    """Two stone pillars with lanterns, a wrought-iron arch, one gate leaf swung open."""
    m = _model("CemeteryGate", seed=2310)
    rng = m.rng
    for x in (-0.82, 0.82):
        m.box("root", "stone2", (x, 0, 0.06), (0.4, 0.4, 0.12), bevel=0.02)
        for i in range(5):
            m.box("root", ("stone", "stone3", "stone2")[i % 3], (x, 0, 0.12 + 0.135 + i * 0.27),
                  (0.32, 0.32, 0.25), rot=(0, 0, rng.uniform(-4, 4)), bevel=0.025, jitter=0.008)
        m.box("root", "stone3", (x, 0, 1.6), (0.4, 0.4, 0.07), bevel=0.02)
        _lantern(m, (x, 0, 1.64), 0.9)
    m.ring("root", "iron", (0, 0, 1.3), 0.66, 0.02, n=16, m=4, arc=180, rot=(90, 0, 0))
    m.ring("root", "iron", (0, 0, 1.3), 0.5, 0.014, n=12, m=4, arc=180, rot=(90, 0, 0))
    for deg in (30, 60, 90, 120, 150):  # spokes between the two arcs
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        m.seg("root", "iron", (0.5 * c, 0, 1.3 + 0.5 * s), (0.66 * c, 0, 1.3 + 0.66 * s), 0.01, n=3)
    _skull(m, (0, -0.02, 1.88), s=0.9)
    m.seg("root", "iron", (-0.66, 0, 1.3), (0.66, 0, 1.3), 0.016, n=4)
    _iron_bars(m, Frame((-0.66, 0, 0)), 0.02, 0.64, 0.05, 1.18, step=0.16)
    _iron_bars(m, Frame((0.66, 0, 0), (0, 0, 62)), -0.64, -0.02, 0.05, 1.18, step=0.16, bent=(2,))
    _tufts(m, ((-0.5, -0.4), (0.3, 0.5), (0.85, -0.45)))
    m.build()
    return m


def ghost_lantern():
    """Crooked wooden post with a hanging lantern - the level 2 roadside light."""
    m = _model("GhostLantern", seed=2320)
    m.seg("root", "wood", (0, 0, 0), (0.04, 0.02, 0.9), 0.06, 0.05, n=6, jitter=0.004)
    m.seg("root", "wood", (0.04, 0.02, 0.9), (-0.02, 0, 1.75), 0.05, 0.04, n=6, jitter=0.004)
    m.seg("root", "wood", (-0.02, 0, 1.62), (0.3, 0, 1.78), 0.035, 0.028, n=5)
    m.seg("root", "wood", (0.3, 0, 1.78), (0.5, 0, 1.72), 0.028, 0.022, n=5)
    for k in range(3):
        z = 1.66 - k * 0.07
        m.ring("root", "iron", (0.48, 0, z), 0.022, 0.006, n=6, rot=(90 if k % 2 else 0, 0, 90))
    _lantern(m, (0.48, 0, 1.24))
    _rubble(m, 4, -0.25, 0.25, -0.25, 0.25, 0.12, 0.2)
    m.build()
    return m


# --- ancient ruins ------------------------------------------------------------------------------
def _column(m, x, y, z0, h, r=0.15, broken=False, capital=True):
    rng = m.rng
    m.box("root", "stone2", (x, y, z0 + 0.05), (2.5 * r, 2.5 * r, 0.1), bevel=0.02, jitter=0.006)
    k = max(1, math.ceil(h / 0.4))
    dh = h / k
    for i in range(k):
        last = i == k - 1
        hh = dh * (0.98 if not last else 1.0)
        m.cyl("root", ("stone", "stone3")[i % 2], (x + rng.uniform(-0.01, 0.01), y, z0 + 0.1 + i * dh + hh / 2),
              r=r, r2=r * 0.97, h=hh, n=8, rot=(0, 0, rng.uniform(0, 45)), jitter=0.02 if broken and last else 0.004)
    top = z0 + 0.1 + h
    if broken:
        for j in range(3):
            deg = rng.uniform(0, 360)
            m.seg("root", "stone", polar(r * 0.55, deg, top - 0.04, (x, y)),
                  polar(r * 0.5, deg + 15, top + rng.uniform(0.08, 0.2), (x, y)), r * 0.35, 0.0, n=4)
    elif capital:
        m.cyl("root", "stone3", (x, y, top + 0.05), r=r * 1.05, r2=r * 1.45, h=0.1, n=8)
        m.box("root", "stone2", (x, y, top + 0.14), (2.9 * r, 2.9 * r, 0.08), bevel=0.015)
    return top


def ruin_columns():
    m = _model("RuinColumns", seed=2400)
    rng = m.rng
    for i in range(4):
        for j in range(3):
            if (i, j) in ((3, 0), (0, 2)) or rng.random() < 0.12:
                continue
            m.box("root", rng.choice(("stone", "stone2", "stone3")),
                  (-0.66 + i * 0.44 + rng.uniform(-0.02, 0.02), -0.44 + j * 0.44, 0.05 + rng.uniform(-0.02, 0.02)),
                  (0.42, 0.42, 0.1), rot=(rng.uniform(-3, 3), rng.uniform(-3, 3), rng.uniform(-4, 4)), bevel=0.02,
                  jitter=0.008)
    top = _column(m, -0.48, 0.2, 0.1, 1.9)
    _column(m, 0.28, 0.28, 0.1, 1.1, broken=True)
    _column(m, 0.6, -0.3, 0.1, 0.32, broken=True)
    for p, deg in (((0.05, -0.45, 0.25), 75), ((0.85, 0.35, 0.15), 20)):
        m.cyl("root", "stone3", p, r=0.15, h=0.36, n=8, rot=(90, 0, deg), jitter=0.006)
    F = Frame((-0.25, -0.62, 0.25), (0, 6, 12))
    m.box("root", "stone", F.p((0, 0, 0)), (1.0, 0.26, 0.24), rot=F.r(), bevel=0.025, jitter=0.008)
    for k, x in enumerate((-0.28, 0.0, 0.28)):
        _glyph(m, F, (x, -0.135, 0), kind=k, s=0.75)
    for k in range(4):
        z = top - 0.05
        deg = 200 + k * 35
        m.seg("root", rng.choice(("hang", "moss2")), polar(0.2, deg, z, (-0.48, 0.2)),
              polar(0.19, deg + 5, z - rng.uniform(0.5, 1.1), (-0.48, 0.2)), 0.022, 0.005, n=3)
    _moss(m, (-0.48, 0.2, top + 0.19), (0.3, 0.28, 0.06))
    _moss(m, (0.5, 0.4, 0.1), (0.4, 0.3, 0.06))
    _rubble(m, 3, 0.5, 0.9, -0.85, -0.55)
    m.build()
    return m


def ruin_arch():
    """Pier of a fallen gothic arch: one side stands with half of the pointed arch, the other is a stump."""
    m = _model("RuinArch", seed=2410)
    rng = m.rng
    m.box("root", "stone2", (0, 0, 0.05), (1.9, 0.6, 0.1), bevel=0.03, jitter=0.01)
    bw, bd, bh = 0.36, 0.42, 0.3
    zt = 0.1
    for i in range(6):
        m.box("root", ("stone", "stone3", "stone2")[i % 3], (-0.75 + rng.uniform(-0.015, 0.015), 0, zt + bh / 2),
              (bw, bd, bh * 0.94), rot=(0, 0, rng.uniform(-4, 4)), bevel=0.03, jitter=0.01)
        zt += bh
    # pointed arch: left arc centred at (+0.25, zt), radius 1.0, from the pier top up to the apex
    for k in range(4):
        deg = 180 - (k + 0.5) * 75.5 / 4
        a = math.radians(deg)
        m.box("root", ("stone3", "stone")[k % 2], (0.25 + math.cos(a) - 0.04, 0, zt + math.sin(a)),
              (0.31, bd, 0.28), rot=(0, -(deg + 90), rng.uniform(-3, 3)), bevel=0.03, jitter=0.01)
    for i, rot in enumerate(((0, 0, 3), (0, 0, -5), (6, 14, 8))):
        m.box("root", ("stone2", "stone", "stone3")[i], (0.75 + (0.04 if i == 2 else 0), 0, 0.1 + bh * (i + 0.5)),
              (bw, bd, bh * 0.94), rot=rot, bevel=0.03, jitter=0.012)
    for p, rot in (((0.45, -0.55, 0.14), (8, -6, 30)), ((0.95, 0.5, 0.13), (-10, 4, 70)),
                   ((0.15, 0.55, 0.12), (4, 12, -20))):
        m.box("root", rng.choice(("stone", "stone3")), p, (0.31, 0.4, 0.27), rot=rot, bevel=0.03, jitter=0.012)
    F = Frame((-0.75, -bd / 2 - 0.008, 0))
    for k, z in enumerate((0.55, 1.15, 1.75)):
        _glyph(m, F, (0, 0, z), kind=k, s=0.8)
    for k in range(5):
        deg = 175 - k * 16
        a = math.radians(deg)
        p = (0.25 + 1.12 * math.cos(a) - 0.04, rng.uniform(-0.2, 0.2), zt + 1.12 * math.sin(a) - 0.12)
        m.seg("root", rng.choice(("hang", "moss2")), p, (p[0], p[1], p[2] - rng.uniform(0.35, 0.8)), 0.022, 0.005,
              n=3)
    _moss(m, (-0.75, 0, 0.12), (0.5, 0.55, 0.08))
    _moss(m, (0.75, 0, 0.1 + bh * 3), (0.3, 0.35, 0.07))
    m.build()
    return m


def ruin_wall():
    """Crumbling wall with an arched window; the top steps down to a rubble heap on the right."""
    m = _model("RuinWall", seed=2420)
    rng = m.rng
    L, depth, rh = 1.9, 0.34, 0.26
    win_x, win_w, win_z0, win_z1 = -0.45, 0.42, 0.75, 1.3

    def profile(x):
        return 2.1 - 0.35 * max(0.0, -0.2 - x) if x < -0.2 else 2.1 - 1.7 * (x + 0.2) / 1.15

    m.box("root", "stone2", (0, 0, 0.05), (L + 0.1, depth + 0.12, 0.1), bevel=0.03, jitter=0.01)
    tops = []  # (x, top z) of the uppermost block in each column, for moss and vines
    for i in range(9):
        z = 0.1 + (i + 0.5) * rh
        k = 6
        cuts = [-L / 2 + L * q / k for q in range(k + 1)]
        if i % 2:
            cuts = [cuts[0]] + [c + L / k / 2 for c in cuts[:-1]] + [cuts[-1]]
        for x0, x1 in zip(cuts, cuts[1:]):
            x = (x0 + x1) / 2
            if z > profile(x) + rng.uniform(-0.12, 0.12):
                continue
            if abs(x - win_x) < win_w / 2 + 0.08 and win_z0 - 0.05 < z < win_z1 + win_w / 2 + 0.05:
                continue
            m.box("root", "mortar", (x, 0, z), (x1 - x0, depth * 0.7, rh))
            m.box("root", rng.choice(("stone", "stone2", "stone3")), (x, 0, z), ((x1 - x0) * 0.95, depth, rh * 0.9),
                  rot=(0, 0, rng.uniform(-2, 2)), bevel=0.025, jitter=0.008)
            tops = [t for t in tops if abs(t[0] - x) > 0.05] + [(x, z + rh / 2)]
    # window: jambs, sill and a round arch of voussoirs
    for sx in (1, -1):
        m.box("root", "stone3", (win_x + sx * (win_w / 2 + 0.05), 0, (win_z0 + win_z1) / 2),
              (0.1, depth + 0.02, win_z1 - win_z0), bevel=0.015)
    m.box("root", "stone3", (win_x, 0, win_z0 - 0.04), (win_w + 0.24, depth + 0.06, 0.08), bevel=0.015)
    rr = win_w / 2 + 0.05
    for q in range(5):
        deg = 180 - (q + 0.5) * 180 / 5
        a = math.radians(deg)
        m.box("root", ("stone3", "stone")[q % 2], (win_x + rr * math.cos(a), 0, win_z1 + rr * math.sin(a)),
              (0.13, depth + 0.02, 0.1), rot=(0, -(deg + 90), 0), bevel=0.015)
    m.box("root", "socket", (win_x, 0, (win_z0 + win_z1) / 2 + 0.05), (win_w, depth * 0.5, win_z1 - win_z0 + 0.1))
    m.cyl("root", "socket", (win_x, 0, win_z1), r=win_w / 2, h=depth * 0.5, n=10, rot=(90, 0, 0))
    F = Frame((0, -depth / 2 - 0.004, 0))
    _glyph(m, F, (0.05, 0, 1.05), kind=1, s=0.9)
    _glyph(m, F, (-0.8, 0, 0.55), kind=0, s=0.8)
    tops.sort()
    for x, top in (tops[0], tops[1], tops[len(tops) // 2], tops[len(tops) // 2 + 1]):
        top -= 0.06
        m.seg("root", rng.choice(("hang", "moss2")), (x, -depth / 2 - 0.02, top),
              (x + rng.uniform(-0.05, 0.05), -depth / 2 - 0.03, top - rng.uniform(0.4, 0.9)), 0.024, 0.005, n=3)
    _rubble(m, 7, 0.3, 0.95, -0.55, 0.5, 0.12, 0.26)
    x, top = max(tops, key=lambda t: t[1])
    _moss(m, (x, 0, top), (0.3, depth + 0.04, 0.06))
    m.build()
    return m


def ritual_stones():
    """Circle of leaning menhirs with glowing runes around an altar slab and a rune ring on the ground."""
    m = _model("RitualStones", seed=2430)
    rng = m.rng
    m.cyl("root", "earth2", (0, 0, 0.012), r=0.72, h=0.024, n=14, jitter=0.01)
    m.ring("root", "rune", (0, 0, 0.03), 0.6, 0.012, n=28, m=3, glow=True)
    for k in range(5):
        _glyph(m, Frame(polar(0.48, k * 72 + 36, 0.03)), (0, 0, 0), kind=k, s=0.7, rot=(-90, 0, k * 72 + 126))
    for k in range(5):
        deg = k * 72 + 18 + rng.uniform(-6, 6)
        h = rng.uniform(0.9, 1.35)
        F = Frame(polar(0.8, deg, 0), (rng.uniform(-9, 4), rng.uniform(-5, 5), deg - 90))
        m.box("root", rng.choice(("stone", "stone3", "stone2")), F.p((0, 0, h / 2 - 0.03)), (0.26, 0.2, h),
              rot=F.r(), taper=0.7, bevel=0.03, jitter=0.015)
        half = 0.1 * (1 - 0.3 * 0.55 / h)
        _glyph(m, F, (0, -half - 0.014, 0.55), kind=k, s=0.75)
        _moss(m, F.p((0.02, 0.05, 0.08)), (0.22, 0.2, 0.08), rot=F.r())
    for x in (-0.22, 0.22):
        m.box("root", "stone2", (x, 0, 0.18), (0.16, 0.32, 0.36), bevel=0.02, jitter=0.006)
    m.box("root", "stone3", (0, 0, 0.41), (0.7, 0.42, 0.1), rot=(0, 2, 4), bevel=0.02, jitter=0.006)
    _skull(m, (0.12, 0.02, 0.46), yaw=-20, s=0.8)
    for p, h in (((-0.2, 0.08, 0.46), 0.12), ((-0.08, -0.1, 0.46), 0.08), ((0.27, -0.12, 0.46), 0.1)):
        _candle(m, p, h, 0.02)
    m.build()
    return m


# --- extras -----------------------------------------------------------------------------------
def bones():
    m = _model("Bones", seed=2500)
    _skull(m, (0.1, -0.15, 0), yaw=-30, pitch=-8)
    for a, b in (((-0.3, 0.1, 0.02), (0.05, 0.25, 0.02)), ((0.25, 0.1, 0.02), (0.42, -0.2, 0.02)),
                 ((-0.2, -0.3, 0.02), (-0.4, -0.05, 0.03)), ((0.05, 0.35, 0.03), (0.3, 0.42, 0.02))):
        _bone(m, a, b)
    for k in range(5):  # ribcage lying on its side, half buried: ribs arch up from the spine
        r = 0.13 - k * 0.012
        m.ring("root", "bone2", (-0.08 + k * 0.075, 0.18 - r * 0.97, 0.0), r, 0.011, n=8, m=3, arc=150,
               rot=(90, 0, 90))
    m.seg("root", "bone", (-0.14, 0.18, 0.015), (0.3, 0.18, 0.015), 0.02, n=5)
    # rusty sword stuck in the ground
    F = Frame((-0.35, 0.3, 0), (8, -12, 20))
    m.box("root", "iron2", F.p((0, 0, 0.22)), (0.06, 0.015, 0.5), rot=F.r(), taper=0.8)
    m.box("root", "iron", F.p((0, 0, 0.48)), (0.22, 0.04, 0.035), rot=F.r(), bevel=0.008)
    m.seg("root", "wood2", F.p((0, 0, 0.5)), F.p((0, 0, 0.64)), 0.018, n=5)
    m.ball("root", "iron", F.p((0, 0, 0.66)), 0.04)
    _tufts(m, ((0.4, 0.3), (-0.45, -0.35)))
    m.build()
    return m


def scarecrow():
    m = _model("Scarecrow", seed=2510)
    m.ball("root", "earth", (0, 0, -0.03), (0.6, 0.6, 0.14))
    m.seg("root", "wood", (0, 0, 0), (0.02, 0, 1.7), 0.045, 0.04, n=6)
    m.seg("root", "wood", (-0.62, 0, 1.33), (0.62, 0, 1.39), 0.035, n=6)
    m.box("root", "cloth", (0, 0, 1.08), (0.4, 0.22, 0.56), taper=1.25, bevel=0.02)
    for y, col in ((-0.115, "cloth"), (0.115, "cloth2")):
        m.prism("root", col, rag(-0.24, 0.24, 0.85, 0.66, teeth=4, depth=0.06), 0.02, loc=(0, y, 0))
    m.ring("root", "rope", (0, 0, 0.88), 0.2, 0.02, n=10, squash=(1, 0.6))
    for sx in (1, -1):
        m.seg("root", "cloth", (sx * 0.2, 0, 1.33), (sx * 0.5, 0, 1.37), 0.075, 0.065, n=6)
        for k in range(3):
            m.cyl("root", "straw", (sx * (0.56 + k * 0.012), (k - 1) * 0.035, 1.37 + (k - 1) * 0.02), r=0.022, r2=0,
                  h=0.16, n=3, rot=(0, sx * (90 + (k - 1) * 20), 0))
        m.prism("root", "cloth2", rag(-0.06, 0.06, 0.04, -0.1, teeth=2, depth=0.03), 0.015,
                loc=(sx * 0.42, -0.01, 1.3), rot=(0, 0, 90))
    for k in range(5):
        x = -0.12 + k * 0.06
        m.cyl("root", "straw", (x, (k % 2) * 0.05 - 0.02, 0.66), r=0.022, r2=0, h=0.16, n=3, rot=(180 + (k - 2) * 8, 0, 0))
    m.ball("root", "sack", (0, 0, 1.68), (0.3, 0.28, 0.32), jitter=0.01)
    m.ring("root", "rope", (0, 0, 1.55), 0.1, 0.015, n=8)
    for sx in (1, -1):
        m.ball("root", "rune", (sx * 0.065, -0.13, 1.72), (0.05, 0.02, 0.04), glow=True)
    for k in range(5):
        m.box("root", "socket", (-0.08 + k * 0.04, -0.138, 1.6 + (0.012 if k % 2 else 0)), (0.03, 0.01, 0.012),
              rot=(0, 30 if k % 2 else -30, 0))
    m.cyl("root", "cloth2", (0, 0, 1.83), r=0.27, h=0.03, n=10)
    m.seg("root", "cloth2", (0, 0, 1.84), (0.02, 0.01, 2.08), 0.14, 0.08, n=8)
    m.seg("root", "cloth2", (0.02, 0.01, 2.08), (0.14, 0.06, 2.24), 0.08, 0.0, n=8)
    _crow(m, (0.5, 0, 1.42), yaw=30, s=0.8)
    m.build()
    return m


def witch_cauldron():
    m = _model("WitchCauldron", seed=2520)
    rng = m.rng
    for k in range(4):
        deg = k * 45 + rng.uniform(-8, 8)
        m.seg("root", ("wood", "wood2")[k % 2], polar(0.38, deg, 0.05), polar(0.38, deg + 180, 0.05), 0.05, n=6)
    m.cyl("root", "socket", (0, 0, 0.01), r=0.3, h=0.02, n=10)
    for k in range(3):
        m.seg("root", "pot", polar(0.24, k * 120 + 30, 0.2), polar(0.3, k * 120 + 30, 0.0), 0.03, 0.02, n=4)
    m.cyl("root", "pot", (0, 0, 0.26), r=0.22, r2=0.37, h=0.16, n=12)
    m.cyl("root", "pot", (0, 0, 0.49), r=0.37, r2=0.31, h=0.3, n=12)
    m.ring("root", "pot", (0, 0, 0.64), 0.31, 0.04, n=12)
    m.cyl("root", "rune", (0, 0, 0.645), r=0.29, h=0.01, n=12, glow=True)
    for x, y, s in ((0.08, 0.05, 0.07), (-0.1, -0.06, 0.05), (0.02, -0.14, 0.04)):
        m.ball("root", "rune", (x, y, 0.655), s, glow=True)
    for sx in (1, -1):
        m.ring("root", "pot", (sx * 0.39, 0, 0.52), 0.06, 0.012, n=8, rot=(90, 0, 90))
    m.seg("root", "wood2", (0.05, 0.08, 0.5), (0.3, 0.3, 0.95), 0.02, n=5)
    for p, h in (((0.55, -0.35, 0), 0.16), ((0.42, -0.5, 0), 0.12)):
        x, y, _ = p
        m.ball("root", "bottle", (x, y, h * 0.45), (h * 0.7, h * 0.7, h * 0.9))
        m.seg("root", "bottle", (x, y, h * 0.8), (x, y, h * 1.15), h * 0.12, n=5)
        m.cyl("root", "cork", (x, y, h * 1.2), r=h * 0.13, h=h * 0.12, n=5)
    _skull(m, (-0.5, -0.4, 0), yaw=40, s=0.9)
    m.build()
    return m


PROPS = dict(
    gnarled_tree_1=partial(gnarled_tree, 1), gnarled_tree_2=partial(gnarled_tree, 2), dead_spruce=dead_spruce,
    hollow_stump=hollow_stump, dead_bush=dead_bush, glow_mushrooms=glow_mushrooms,
    grave_1=partial(grave, 1), grave_2=partial(grave, 2), grave_3=partial(grave, 3), grave_open=grave_open,
    crypt=crypt, obelisk=obelisk, cemetery_fence=cemetery_fence, cemetery_gate=cemetery_gate,
    ghost_lantern=ghost_lantern, ruin_columns=ruin_columns, ruin_arch=ruin_arch, ruin_wall=ruin_wall,
    ritual_stones=ritual_stones, bones=bones, scarecrow=scarecrow, witch_cauldron=witch_cauldron)


# --- terrain tiles ------------------------------------------------------------------------------
# Same shapes and edge profiles as env.TILES, so Map's auto-tiling works unchanged; names get "haunt_".
# Withered grass stays slightly green so shaders/ground.gdshader still adds its patches to it.
GROUND = dict(HAUNT, grass="#4C6236", soil="#4A3C2E", soil2="#372C23", road="#665846", road2="#584B3C",
              road3="#736451", mud="#4A3D30", pebble="#66646C", pebble2="#78767E", pebble3="#55535B",
              tuft="#6E6B42", tuft2="#59603A", rock="#6E6C74", rock2="#5E5C64", rock3="#807E86",
              leafd="#6B4A2A", leafd2="#7E5B30", leafd3="#5A3F28", pave="#5E5C64")


def _litter(m, rng, free, leaves=10, twigs=2, bones=0, shrooms=0, dirt=0):
    """Bare earth patches, fallen leaves, twigs, bone fragments and tiny glowing mushrooms on free ground."""
    def spot():
        for _ in range(30):
            x, y = rng.uniform(-0.9, 0.9), rng.uniform(-0.9, 0.9)
            if free(x, y, 0.04):
                return x, y
        return None

    for _ in range(dirt):
        p = spot()
        if p and max(abs(p[0]), abs(p[1])) < 0.6:
            m.ball("root", rng.choice(("earth", "earth3")), (p[0], p[1], -0.005), (rng.uniform(0.35, 0.6),
                   rng.uniform(0.3, 0.5), 0.045), rot=(0, 0, rng.uniform(0, 180)), jitter=0.01)
    for _ in range(leaves):
        p = spot()
        if p:
            m.prism("root", rng.choice(("leafd", "leafd2", "leafd3")), [(0, -0.05), (0.035, 0), (0, 0.05), (-0.035, 0)],
                    0.008, loc=(p[0], p[1], 0.016), rot=(90 + rng.uniform(-8, 8), 0, rng.uniform(0, 180)))
    for _ in range(twigs):
        p = spot()
        if p:
            a, length = rng.uniform(0, math.tau), rng.uniform(0.2, 0.35)
            end = (p[0] + math.cos(a) * length, p[1] + math.sin(a) * length, 0.02)
            if max(abs(end[0]), abs(end[1])) > 0.9 or not free(end[0], end[1], 0.0):
                continue
            m.seg("root", "deadbark3", (p[0], p[1], 0.02), end, 0.013, 0.006, n=4)
            mid = Vector((p[0], p[1], 0.02)).lerp(Vector(end), 0.5)
            m.seg("root", "deadbark3", mid, mid + Vector((math.cos(a + 0.7) * 0.09, math.sin(a + 0.7) * 0.09, 0.0)),
                  0.007, 0.003, n=3)
    for _ in range(bones):
        p = spot()
        if p:
            a = rng.uniform(0, math.tau)
            _bone(m, (p[0], p[1], 0.02), (p[0] + math.cos(a) * 0.16, p[1] + math.sin(a) * 0.16, 0.02), 0.011)
    for _ in range(shrooms):
        p = spot()
        if p:
            for k in range(rng.randint(2, 3)):
                x, y, h = p[0] + rng.uniform(-0.05, 0.05), p[1] + rng.uniform(-0.05, 0.05), rng.uniform(0.04, 0.08)
                m.seg("root", "stem2", (x, y, 0), (x, y, h), 0.008, n=4)
                m.cyl("root", "rune", (x, y, h + 0.008), r=0.025, r2=0.008, h=0.016, n=6, glow=True)


def _flagstones(m, rng, on_road, height, keep=0.55):
    """Remains of an ancient paved path: sunken, tilted flagstones, many missing."""
    step = 0.27
    for i in range(-4, 5):
        for j in range(-4, 5):
            x, y = i * step + rng.uniform(-0.03, 0.03), j * step + rng.uniform(-0.03, 0.03)
            if max(abs(x), abs(y)) > 0.9 or not on_road(x, y, -0.12) or rng.random() > keep:
                continue
            s = rng.uniform(0.17, 0.23)
            m.box("root", rng.choice(("stone", "stone2", "stone3")), (x, y, height(x, y) + 0.006),
                  (s, s * rng.uniform(0.8, 1.1), 0.04), rot=(rng.uniform(-3, 3), rng.uniform(-3, 3), rng.uniform(-12, 12)),
                  bevel=0.012, jitter=0.006)


def _small_grave(m, rng, x, y, kind, lit=False):
    """Grave in a quarter of a cemetery tile: the stone at the head (+Y), the mound in front (-Y)."""
    _mound(m, x, y - 0.14, 0.5, 0.27, h=0.24)
    F = Frame((x, y + 0.24, 0), (rng.uniform(-6, 4), rng.uniform(-6, 6), rng.uniform(-8, 8)))
    if kind == "stone":
        _headstone(m, F, w=0.3, h=0.32, rune=rng.randrange(3), lit=lit)
    elif kind == "cross":
        m.box("root", "stone2", F.p((0, 0, 0.04)), (0.22, 0.16, 0.08), rot=F.r(), bevel=0.015)
        m.box("root", "stone3", F.p((0, 0, 0.32)), (0.07, 0.07, 0.5), rot=F.r(), bevel=0.01)
        m.box("root", "stone3", F.p((0, 0, 0.44)), (0.28, 0.07, 0.07), rot=F.r(), bevel=0.01)
        if lit:
            _glyph(m, F, (0, -0.04, 0.44), kind=0, s=0.5)
    elif kind == "broken":
        m.box("root", "stone2", F.p((0, 0, 0.04)), (0.4, 0.2, 0.08), rot=F.r(), bevel=0.015)
        m.prism("root", "stone", [(-0.15, 0.08), (0.15, 0.08), (0.15, 0.3), (0.06, 0.36), (0.0, 0.28), (-0.08, 0.4),
                                  (-0.15, 0.34)], 0.09, loc=F.p((0, 0, 0)), rot=F.r())
        if lit:
            _glyph(m, F, (-0.05, -0.048, 0.22), kind=2, s=0.6)
    else:  # ledger slab lying on the grave with a cross in relief
        m.box("root", "stone", (x, y - 0.05, 0.12), (0.32, 0.6, 0.07), rot=(2, 0, rng.uniform(-5, 5)), bevel=0.015)
        m.box("root", "stone3", (x, y + 0.02, 0.16), (0.05, 0.3, 0.015))
        m.box("root", "stone3", (x, y + 0.08, 0.16), (0.18, 0.05, 0.015))
    if rng.random() < 0.5:
        _moss(m, F.p((rng.uniform(-0.08, 0.08), 0.0, 0.06)), (0.16, 0.14, 0.05))


def _graves(layout, candles=0, shrooms=0, bush=False):
    def extra(m, rng, free, height, on_road):
        for x, y, kind, lit in layout:
            _small_grave(m, rng, x, y, kind, lit)
        for k in range(candles):
            _candle(m, (0.08 + 0.09 * k, -0.85 + 0.05 * (k % 2), 0.0), 0.08 + 0.03 * (k % 2), 0.02)
        if bush:
            for k in range(5):
                a = math.radians(k * 72 + rng.uniform(-15, 15))
                _limb(m, (0.62, -0.7, 0), (math.cos(a) * 0.5, math.sin(a) * 0.5, 1), rng.uniform(0.3, 0.45), 0.022,
                      2, color="deadbark3", spread=32, forks=(2, 2), wander=0.4, rise=0.08)
        _litter(m, rng, lambda x, y, margin=0.0: free(x, y, margin) and not any(
            abs(x - gx) < 0.22 and -0.5 < y - gy < 0.4 for gx, gy, _, _ in layout), leaves=8, twigs=1, shrooms=shrooms)
    return extra


def haunt_tile(name, colors=GROUND, extra=None, plot=False, **kw):
    def details(m, rng, free, height, on_road):
        if kw.get("road"):
            _flagstones(m, rng, on_road, height)
        if plot:  # faint rune ring around the paved top and some moss on the rim
            m.ring("root", "rune", (0, 0, 0.088), 0.66, 0.012, n=24, m=3, glow=True)
            for deg in (40, 200):
                _moss(m, polar(0.86, deg, 0.06), (0.22, 0.16, 0.06), rot=(0, 0, deg))
        if extra:
            extra(m, rng, free, height, on_road)
    return terrain_tile(name, plot=plot, colors=colors, glow=GLOW, glow_strength=GLOW_STRENGTH, extra=details, **kw)


def _ground_litter(**kw):
    return lambda m, rng, free, height, on_road: _litter(m, rng, free, **kw)


TILES = dict(
    haunt_grass_1=partial(haunt_tile, "HauntGrass1", tufts=5, rocks=1, seed=31, extra=_ground_litter(leaves=12, twigs=2, dirt=1)),
    haunt_grass_2=partial(haunt_tile, "HauntGrass2", tufts=3, seed=32,
                          extra=_ground_litter(leaves=8, twigs=1, bones=1, shrooms=1, dirt=2)),
    haunt_grass_3=partial(haunt_tile, "HauntGrass3", tufts=4, rocks=4, seed=33, extra=_ground_litter(leaves=6, twigs=3, dirt=1)),
    haunt_road_straight=partial(haunt_tile, "HauntRoadStraight", road="straight", tufts=3, seed=34,
                                extra=_ground_litter(leaves=5)),
    haunt_road_corner=partial(haunt_tile, "HauntRoadCorner", road="corner", tufts=3, seed=35,
                              extra=_ground_litter(leaves=5, twigs=1)),
    haunt_road_t=partial(haunt_tile, "HauntRoadT", road="t", tufts=2, seed=36, extra=_ground_litter(leaves=4)),
    haunt_road_cross=partial(haunt_tile, "HauntRoadCross", road="cross", tufts=2, seed=37, extra=_ground_litter(leaves=3)),
    haunt_road_end=partial(haunt_tile, "HauntRoadEnd", road="end", tufts=4, seed=38, extra=_ground_litter(leaves=5)),
    haunt_plot=partial(haunt_tile, "HauntPlot", plot=True, tufts=3, seed=39, extra=_ground_litter(leaves=6)),
    # cemetery cells (instead of the river on level 1); graves face south (+Z in Godot), place unrotated
    haunt_graves_1=partial(haunt_tile, "HauntGraves1", tufts=3, seed=40, extra=_graves(
        [(-0.5, -0.4, "stone", False), (0.5, -0.4, "cross", True), (-0.5, 0.5, "stone", False),
         (0.5, 0.5, "broken", False)])),
    haunt_graves_2=partial(haunt_tile, "HauntGraves2", tufts=2, seed=41, extra=_graves(
        [(-0.5, -0.4, "slab", False), (0.5, -0.4, "stone", True), (-0.5, 0.5, "cross", False)], candles=3,
        shrooms=1)),
    haunt_graves_3=partial(haunt_tile, "HauntGraves3", tufts=4, seed=42, extra=_graves(
        [(-0.5, 0.5, "broken", True), (0.45, 0.5, "stone", False), (-0.5, -0.4, "cross", False)], bush=True)),
)
