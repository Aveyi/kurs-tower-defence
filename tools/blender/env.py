"""Environment: map tiles, the castle (player base), the enemy portal and props.

Tiles are 2 x 2 m (one tower cell), centred on the origin, grass level at z = 0, with soil
sides down to z = -0.5 so the map edge reads as a floating island. Road/river tiles share the
same cross-section on every edge, so any rotation of them connects. In Godot (+Z = Blender -Y):
  road_straight/river_straight run north-south; road_corner/river_corner join south and east;
  road_t: north-south + east; road_end: from the south edge to the centre; bridge: road
  east-west over a north-south river.
Leaves and grass use the "Foliage" material (wind shader), water uses "Water".
"""
import math
import random
from functools import partial

from mathutils import Vector

from lowpoly import Anim, Model
from towers import (KINGDOM, METALS, brazier, cone_roof, crenels_round, crenels_square, door, drum_out, flag, idle,
                    keg, lantern, polar, stone_drum, stone_square, tower_model, wall_banner, window)

ENV = dict(
    grass="#6FA14A", grass2="#5E9140", grass3="#7DAE52", soil="#7A5A3C", soil2="#5E4530",
    road="#B08B5E", road2="#9C7A50", road3="#C29C6C", bed="#56665A", bed2="#4A5A50", sand="#C9B48A",
    mud="#6E5A3E", water="#3F86C4", pebble="#8E8A80", pebble2="#A39E94", pebble3="#76726B",
    tuft="#5A9A3C", tuft2="#4C8A34", stem="#4E8A34", flower1="#F2D24B", flower2="#F4F0E8", flower3="#B07ED8",
    flower4="#E8667A", leaf="#4E8A34", leaf2="#3F7A2C", leaf3="#6AA444", autumn="#D08A2E", autumn2="#B8612A",
    autumn3="#E0A940", pine="#2F6B3A", pine2="#245A31", pine3="#3A7A44", bark="#6B4A2E", bark2="#4F3622",
    deadwood="#5A5048", cut="#C9A06A", cut2="#A87E4E", cream="#E8DCC0", red="#B8402F", berry="#C8323C",
    moss="#56752F", rock="#8E8A84", rock2="#7A766F", rock3="#A39E96", cloth="#C8B48A", pave="#8C8578")
FOLIAGE = ("tuft", "tuft2", "stem", "flower1", "flower2", "flower3", "flower4", "leaf", "leaf2", "leaf3",
           "autumn", "autumn2", "autumn3", "pine", "pine2", "pine3", "berry")

WATER_Z = -0.14
ROAD_W = 0.5      # road half-width
RIVER_W = 0.42    # flat river bed half-width; banks reach 0.85

PATHS = dict(
    straight=lambda x, y: abs(x),
    corner=lambda x, y: abs(math.hypot(x - 1, y + 1) - 1),
    t=lambda x, y: min(abs(x), abs(y) if x > 0 else math.hypot(x, y)),
    cross=lambda x, y: min(abs(x), abs(y)),
    end=lambda x, y: abs(x) if y < 0 else math.hypot(x, y),
    across=lambda x, y: abs(y),
)


def _model(name, colors=None, glow="#FFB347", seed=1, rig=False, glow_strength=4.0, **kw):
    pal = dict(KINGDOM)
    pal.update(ENV)
    pal.update(colors or {})
    m = Model(name, pal, glow_color=glow, glow_strength=glow_strength, metal=METALS, foliage=FOLIAGE, rig=rig,
              seed=seed, **kw)
    m.bone("root", (0, 0, 0))
    m.flames, m.flags = [], []
    return m


# --- terrain tiles ----------------------------------------------------------------------
def _smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def terrain_tile(name, road=None, river=None, bridge=False, plot=False, tufts=0, flowers=0, rocks=0, seed=0,
                 colors=None, glow="#FFB347", glow_strength=4.0, extra=None):
    """`colors` re-colours the palette (other locations), `extra(m, rng, free, height, on_road)` adds details
    before the mesh is built (`free(x, y)`: not on the road / river / plot)."""
    m = _model(name, colors, glow=glow, seed=seed, variance=0.05, glow_strength=glow_strength)
    rng = random.Random(seed)
    road_d = PATHS[road] if road else None
    river_d = PATHS[river] if river else None

    def on_river(x, y, margin=0.0):
        return river_d is not None and river_d(x, y) < 0.85 + margin

    def on_road(x, y, margin=0.0):
        return road_d is not None and road_d(x, y) < ROAD_W + margin and not on_river(x, y)

    def height(x, y):
        h = 0.0
        if river_d:
            d = river_d(x, y)
            h = -0.38 * (1 - _smooth((d - RIVER_W) / (0.85 - RIVER_W)))
        if road_d and not on_river(x, y):
            h = min(h, -0.03 * (1 - _smooth((road_d(x, y) - ROAD_W + 0.04) / 0.06)))
        return h

    def ground(x, y, z):
        if on_river(x, y):
            if z < -0.28:
                return rng.choice(("bed", "bed2"))
            return "sand" if z < -0.1 else "mud" if river_d(x, y) < 0.75 else "grass"
        if on_road(x, y, -0.01):
            return rng.choice(("road", "road", "road2", "road3"))
        # one grass colour: hue patches are added in world space by shaders/ground.gdshader,
        # so the pattern runs across tile borders instead of repeating per tile
        return "grass"

    # top surface: N x N grid, interior grass vertices jittered, edges exact so tiles connect
    N, step = 16, 2.0 / 16
    bm = m.bm
    grid = []
    for i in range(N + 1):
        col = []
        for j in range(N + 1):
            x, y = -1 + i * step, -1 + j * step
            z = height(x, y)
            if 0 < i < N and 0 < j < N and z == 0.0 and not on_road(x, y, 0.1):
                z += rng.uniform(-0.012, 0.02)
            col.append(bm.verts.new((x, y, z)))
        grid.append(col)
    for i in range(N):
        for j in range(N):
            a, b, c, d = grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]
            tris = ((a, b, c), (a, c, d)) if (i + j) % 2 else ((a, b, d), (b, c, d))
            for tri in tris:
                f = bm.faces.new(tri)
                cx = sum(v.co.x for v in tri) / 3
                cy = sum(v.co.y for v in tri) / 3
                cz = sum(v.co.z for v in tri) / 3
                m.paint_face(f, "root", ground(cx, cy, cz))

    # soil skirt (two layers) and bottom
    ring = ([grid[i][0] for i in range(N)] + [grid[N][j] for j in range(N)] +
            [grid[i][N] for i in range(N, 0, -1)] + [grid[0][j] for j in range(N, 0, -1)])
    mids = [bm.verts.new((v.co.x, v.co.y, min(-0.2, v.co.z - 0.05))) for v in ring]
    bots = [bm.verts.new((v.co.x, v.co.y, -0.5)) for v in ring]
    for k in range(len(ring)):
        q = (k + 1) % len(ring)
        m.paint_face(bm.faces.new((ring[k], ring[q], mids[q], mids[k])), "root", "soil")
        m.paint_face(bm.faces.new((mids[k], mids[q], bots[q], bots[k])), "root", "soil2")
    m.paint_face(bm.faces.new(list(reversed(bots))), "root", "soil2")

    # water surface over every cell that dips below the water line
    if river_d:
        for i in range(N):
            for j in range(N):
                if min(grid[a][b].co.z for a in (i, i + 1) for b in (j, j + 1)) < WATER_Z:
                    x0, y0 = -1 + i * step, -1 + j * step
                    vs = [bm.verts.new((x, y, WATER_Z)) for x, y in ((x0, y0), (x0 + step, y0),
                                                                    (x0 + step, y0 + step), (x0, y0 + step))]
                    m.paint_face(bm.faces.new(vs), "root", "water")

    def free(x, y, margin=0.12):
        return max(abs(x), abs(y)) < 0.9 and not on_road(x, y, margin) and not on_river(x, y, margin) and \
            not (plot and math.hypot(x, y) < 0.95)

    # cobbles along the road edge and a few pebbles on it
    if road_d:
        for i in range(-8, 9):
            for j in range(-8, 9):
                x, y = i * 0.115 + rng.uniform(-0.03, 0.03), j * 0.115 + rng.uniform(-0.03, 0.03)
                if max(abs(x), abs(y)) > 0.95 or on_river(x, y, 0.1) or rng.random() > 0.75:
                    continue
                if abs(road_d(x, y) - (ROAD_W + 0.02)) < 0.035:
                    m.ball("root", rng.choice(("pebble", "pebble2", "pebble3")), (x, y, height(x, y) + 0.01),
                           (rng.uniform(0.08, 0.13), rng.uniform(0.07, 0.11), rng.uniform(0.05, 0.07)),
                           rot=(0, 0, rng.uniform(0, 180)), jitter=0.008)
        for _ in range(5):
            x, y = rng.uniform(-0.9, 0.9), rng.uniform(-0.9, 0.9)
            if on_road(x, y, -0.1):
                m.ball("root", "pebble3", (x, y, -0.025), (0.05, 0.04, 0.03), rot=(0, 0, rng.uniform(0, 180)))

    def spots(count):
        out = []
        for _ in range(count * 20):
            if len(out) == count:
                break
            x, y = rng.uniform(-0.9, 0.9), rng.uniform(-0.9, 0.9)
            if free(x, y) and all(math.hypot(x - a, y - b) > 0.2 for a, b in out):
                out.append((x, y))
        return out

    for x, y in spots(tufts):
        for k in range(rng.randint(3, 5)):
            tilt = rng.uniform(-25, 25)
            m.cyl("root", rng.choice(("tuft", "tuft2")), (x + rng.uniform(-0.04, 0.04), y + rng.uniform(-0.04, 0.04),
                                                          0.06), r=0.018, r2=0, h=rng.uniform(0.1, 0.17), n=3,
                  rot=(tilt, rng.uniform(-25, 25), rng.uniform(0, 120)))
    for x, y in spots(flowers):
        h = rng.uniform(0.1, 0.18)
        m.seg("root", "stem", (x, y, 0), (x, y, h), 0.008, n=3)
        m.ball("root", rng.choice(("flower1", "flower2", "flower3", "flower4")), (x, y, h), (0.05, 0.05, 0.03))
    for x, y in spots(rocks):
        s = rng.uniform(0.08, 0.2)
        m.ball("root", rng.choice(("rock", "rock2", "rock3")), (x, y, s * 0.15), (s, s * 0.8, s * 0.6),
               rot=(0, 0, rng.uniform(0, 180)), jitter=s * 0.12)

    if extra:
        extra(m, rng, free, height, on_road)
    if bridge:
        _bridge(m)
    if plot:
        m.cyl("root", "stone2", (0, 0, 0.03), r=0.9, r2=0.86, h=0.08, n=8, rot=(0, 0, 22.5))
        m.cyl("root", "pave", (0, 0, 0.075), r=0.78, h=0.02, n=8, rot=(0, 0, 22.5))
        for k in range(8):
            m.box("root", "stone3", polar(0.83, k * 45 + 22.5, 0.09), (0.12, 0.12, 0.05), rot=(0, 0, k * 45 + 22.5),
                  bevel=0.015)
    m.build()
    return m


def _bridge(m):
    """Arched plank bridge carrying the east-west road over the river."""
    def z_at(x):
        return 0.04 + 0.12 * math.cos(math.pi * x / 2)

    xs = [-0.95 + k * 0.136 for k in range(15)]
    for k, x in enumerate(xs):
        slope = -0.12 * math.pi / 2 * math.sin(math.pi * x / 2)
        m.box("root", ("plank", "plank2")[k % 2], (x, 0, z_at(x)), (0.128, 0.9, 0.04),
              rot=(0, -math.degrees(math.atan(slope)), 0), bevel=0.006)
    for y in (-0.38, 0.38):
        pts = [(x, y, z_at(x) - 0.06) for x in (-0.98, -0.6, -0.2, 0.2, 0.6, 0.98)]
        for a, b in zip(pts, pts[1:]):
            m.seg("root", "wood2", a, b, 0.045, n=6)
    for y in (-0.47, 0.47):
        posts = [-0.9, -0.45, 0.0, 0.45, 0.9]
        for x in posts:
            m.seg("root", "wood", (x, y, z_at(x)), (x, y, z_at(x) + 0.32), 0.035, n=5)
        for a, b in zip(posts, posts[1:]):
            m.seg("root", "wood", (a, y, z_at(a) + 0.3), (b, y, z_at(b) + 0.3), 0.025, n=5)
    for sx in (1, -1):
        m.box("root", "stone2", (sx * 0.92, 0, -0.08), (0.22, 1.0, 0.2), bevel=0.02, jitter=0.005)


TILES = dict(
    grass_1=partial(terrain_tile, "Grass1", tufts=6, rocks=1, seed=1),
    grass_2=partial(terrain_tile, "Grass2", tufts=3, flowers=10, seed=2),
    grass_3=partial(terrain_tile, "Grass3", tufts=5, rocks=5, seed=3),
    road_straight=partial(terrain_tile, "RoadStraight", road="straight", tufts=3, seed=4),
    road_corner=partial(terrain_tile, "RoadCorner", road="corner", tufts=3, flowers=2, seed=5),
    road_t=partial(terrain_tile, "RoadT", road="t", tufts=2, seed=6),
    road_cross=partial(terrain_tile, "RoadCross", road="cross", tufts=2, seed=7),
    road_end=partial(terrain_tile, "RoadEnd", road="end", tufts=4, seed=8),
    river_straight=partial(terrain_tile, "RiverStraight", river="straight", tufts=3, seed=9),
    river_corner=partial(terrain_tile, "RiverCorner", river="corner", tufts=3, seed=10),
    bridge=partial(terrain_tile, "Bridge", road="across", river="straight", bridge=True, tufts=2, seed=11),
    plot=partial(terrain_tile, "Plot", plot=True, tufts=4, flowers=2, seed=12),
)


# --- castle -------------------------------------------------------------------------------
def stone_wall(m, a, b, z0, z1, depth=0.4, colors=("stone", "stone2", "stone3")):
    """Straight masonry wall from a to b (x, y), blocks on both faces around a mortar core."""
    a, b = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0))
    length = (b - a).length
    t = (b - a) / length
    n = Vector((-t.y, t.x, 0))
    yaw = math.degrees(math.atan2(t.y, t.x))
    mid = (a + b) / 2
    m.box("root", "mortar", (mid.x, mid.y, (z0 + z1) / 2), (length, depth * 0.8, z1 - z0), rot=(0, 0, yaw))
    rows = max(2, round((z1 - z0) / 0.26))
    rh = (z1 - z0) / rows
    k = max(1, round(length / 0.34))
    for i in range(rows):
        cuts = [q * length / k for q in range(k + 1)]
        if i % 2 and k > 1:
            cuts = [0.0] + [c + length / k / 2 for c in cuts[:-1]] + [length]
        for side in (1, -1):
            for u0, u1 in zip(cuts, cuts[1:]):
                p = a + t * ((u0 + u1) / 2) + n * side * (depth / 2 - 0.042)
                m.box("root", colors[m.rng.randrange(len(colors))], (p.x, p.y, z0 + (i + 0.5) * rh),
                      ((u1 - u0) * 0.93, 0.14, rh * 0.86), rot=(0, 0, yaw), bevel=min(0.02, rh * 0.12), jitter=0.005)
    m.box("root", "stone2", (mid.x, mid.y, z1 + 0.04), (length + 0.04, depth + 0.06, 0.08), rot=(0, 0, yaw),
          bevel=0.015)


def wall_crenels(m, a, b, z, depth=0.4, side=1, h=0.24):
    a, b = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0))
    length = (b - a).length
    t = (b - a) / length
    n = Vector((-t.y, t.x, 0))
    yaw = math.degrees(math.atan2(t.y, t.x))
    k = max(2, round(length / 0.42))
    for q in range(k):
        p = a + t * ((q + 0.5) * length / k) + n * side * (depth / 2 - 0.05)
        m.box("root", ("stone", "stone3")[q % 2], (p.x, p.y, z + 0.08 + h / 2), (0.22, 0.16, h), rot=(0, 0, yaw),
              bevel=0.02, jitter=0.004)


def castle():
    """Player base (~4.3 x 4 m, two tiles): curtain walls, four towers, a keep, gate with portcullis."""
    m = tower_model("Castle", dict(ENV), glow="#FFB347", seed=700)
    m.box("root", "stone2", (0, 0.1, 0.075), (4.3, 4.0, 0.15), bevel=0.04)
    m.box("root", "pave", (0, 0.1, 0.155), (3.4, 3.0, 0.02))
    z0, z1 = 0.15, 1.6
    FL, FR, BL, BR = (-1.35, -1.25), (1.35, -1.25), (-1.35, 1.45), (1.35, 1.45)
    for a, b, side in ((FL, (-0.6, -1.25), -1), ((0.6, -1.25), FR, -1), (FL, BL, 1), (FR, BR, -1), (BL, BR, 1)):
        stone_wall(m, a, b, z0, z1)
        wall_crenels(m, a, b, z1, side=side)

    # gatehouse with a portcullis
    stone_wall(m, (-0.78, -1.25), (-0.45, -1.25), z0, 2.05, depth=0.6)
    stone_wall(m, (0.45, -1.25), (0.78, -1.25), z0, 2.05, depth=0.6)
    stone_wall(m, (-0.45, -1.25), (0.45, -1.25), 1.15, 2.05, depth=0.6)
    for side in (1, -1):
        wall_crenels(m, (-0.78, -1.25), (0.78, -1.25), 2.05, depth=0.6, side=side)
    m.box("root", "dark", (0, -1.2, 0.65), (0.9, 0.5, 1.0))
    for x in (-0.36, -0.18, 0.0, 0.18, 0.36):
        m.seg("root", "iron", (x, -1.5, 0.5), (x, -1.5, 1.15), 0.018, n=4)
        m.cyl("root", "iron", (x, -1.5, 0.46), r=0.02, r2=0, h=0.08, n=4, rot=(180, 0, 0))
    for z in (0.62, 0.86, 1.1):
        m.seg("root", "iron", (-0.44, -1.5, z), (0.44, -1.5, z), 0.015, n=4)
    m.ring("root", "stone3", (0, -1.58, 1.15), 0.48, 0.05, n=10, arc=180, rot=(90, 0, 0))
    wall_banner(m, 0, -1.58, 270, 1.95, 0.6)
    for x in (-0.6, 0.6):
        brazier(m, f"flame_gate{'L' if x < 0 else 'R'}", (x, -1.42, 2.13), 0.7)

    # corner towers
    for (x, y), big, tag, deg in ((FL, True, "FL", 225), (FR, True, "FR", 315), (BL, False, "BL", 135),
                                  (BR, False, "BR", 45)):
        r0, r1, top = (0.6, 0.52, 2.5) if big else (0.52, 0.46, 2.1)
        stone_drum(m, z0, top, r0, r1, c=(x, y))
        crenels_round(m, top, r1, n=8, c=(x, y))
        window(m, deg, drum_out(z0, top, r0, r1, 1.7) - 0.02, 1.7, c=(x, y))
        tip = cone_roof(m, top + 0.1, r1 + 0.12, 1.0 if big else 0.8, c=(x, y))
        flag(m, f"flag_{tag}", (x, y, tip + 0.12), 0.45)

    # keep
    kc = (0, 0.55)
    stone_square(m, z0, 3.0, 0.9, 0.82, c=kc)
    crenels_square(m, 3.0, 0.82, c=kc)
    tip = cone_roof(m, 3.1, 0.75, 1.3, c=kc)
    flag(m, "flag_keep", (kc[0], kc[1], tip + 0.12), 0.8)
    door(m, 0.92, z0=z0, w=0.45, h=0.65, c=kc)
    for x, z in ((-0.4, 1.7), (0.4, 1.7), (0.0, 2.45)):
        window(m, 270, 0.88, z, w=0.11, h=0.26, c=(x, kc[1]))
    for x in (-0.48, 0.48):
        wall_banner(m, x, kc[1] - 0.9, 270, 2.75, 0.9)
    keg(m, (-1.0, 0.0, 0.16))
    keg(m, (-0.85, 0.25, 0.16), 0.9)
    m.build()
    idle(m)
    return m


# --- enemy portal ---------------------------------------------------------------------------
def portal():
    """Ruined stone arch around a swirling vortex; enemies step out toward -Y (Godot +Z)."""
    m = tower_model("Portal", dict(ENV, dstone="#4A4550", dstone2="#3A3640", dstone3="#5C5664", void="#1A0A26",
                                   crystal="#4B2A6B", crystal2="#6A3A8F", bone="#D8D2BF", rune="#E07BFF"),
                    glow="#C03CFF", strength=6.0, seed=800)
    rng = m.rng
    m.cyl("root", "dstone2", (0, 0, 0.06), r=1.1, r2=1.04, h=0.12, n=10, jitter=0.01)
    for k in range(7):
        x, y, _ = polar(rng.uniform(0.3, 0.85), k * 51 + rng.uniform(-10, 10), 0)
        m.box("root", rng.choice(("dstone", "dstone3")), (x, y, 0.13), (0.3, 0.25, 0.04),
              rot=(rng.uniform(-4, 4), rng.uniform(-4, 4), rng.uniform(0, 90)), bevel=0.01, jitter=0.01)

    for x, count in ((-0.9, 7), (0.9, 6)):
        for i in range(count):
            broken = x > 0 and i == count - 1
            m.box("root", ("dstone", "dstone3", "dstone2")[i % 3], (x + (0.06 if broken else 0), 0, 0.27 + i * 0.3),
                  (0.42, 0.42, 0.28), rot=(0, 18 if broken else 0, rng.uniform(-8, 8)), bevel=0.03, jitter=0.012)
            if i in (1, 3, 5):
                m.prism("root", "rune", [(0, -0.06), (0.04, 0), (0, 0.06), (-0.04, 0)], 0.02,
                        loc=(x, -0.215, 0.27 + i * 0.3), glow=True)
    for deg in (170, 148, 126, 104, 12, 34):
        a = math.radians(deg)
        m.box("root", rng.choice(("dstone", "dstone3")), (0.92 * math.cos(a), 0, 2.08 + 0.92 * math.sin(a)),
              (0.36, 0.42, 0.3), rot=(0, -(deg + 90), 0), bevel=0.03, jitter=0.012)
    m.box("root", "dstone", (0.62, -0.75, 0.13), (0.36, 0.36, 0.26), rot=(12, 20, 35), bevel=0.03, jitter=0.01)

    # vortex: dark disc, glowing rim, two counter-rotating spirals
    m.bone("pulse", (0, 0, 1.25), "root")
    m.bone("swirl", (0, 0, 1.25), "pulse")
    m.bone("swirl2", (0, 0, 1.25), "pulse")
    m.cyl("pulse", "void", (0, 0, 1.25), r=0.78, h=0.05, n=16, rot=(90, 0, 0))
    m.ring("root", "rune", (0, 0, 1.25), 0.8, 0.035, n=24, rot=(90, 0, 0), glow=True)
    for bone, arms, radius, turn, y in (("swirl", 3, 0.7, 200, -0.035), ("swirl2", 2, 0.5, -160, -0.05)):
        for k in range(arms):
            pts = []
            for q in range(9):
                t = q / 8
                r, a = 0.08 + (radius - 0.08) * t, math.radians(k * 360 / arms + turn * t)
                pts.append((r * math.cos(a), y, 1.25 + r * math.sin(a)))
            for q, (p1, p2) in enumerate(zip(pts, pts[1:])):
                m.seg(bone, "rune", p1, p2, 0.035 * (1 - q / 9) + 0.01, n=4, glow=True)
    m.ball("swirl", "rune", (0, -0.04, 1.25), (0.16, 0.06, 0.16), glow=True)

    for k in range(7):  # dark crystals breaking through the ground
        deg = k * 51 + 20
        a = math.radians(deg)
        base = Vector(polar(rng.uniform(1.0, 1.3), deg, 0))
        d = Vector((math.cos(a) * 0.5, math.sin(a) * 0.5, 1)).normalized()
        length = rng.uniform(0.35, 0.8)
        col = rng.choice(("crystal", "crystal2"))
        m.seg("root", col, base, base + d * length * 0.75, 0.08, 0.07, n=5)
        m.seg("root", col, base + d * length * 0.75, base + d * length, 0.07, 0, n=5)
    for x, y, yaw in ((0.5, -0.85, 20), (-0.65, -0.7, -30)):
        m.ball("root", "bone", (x, y, 0.08), (0.13, 0.15, 0.13), rot=(0, 0, yaw))
        for dx in (-0.03, 0.03):
            m.box("root", "void", (x + dx, y - 0.07, 0.09), (0.03, 0.02, 0.03), rot=(0, 0, yaw))
    m.build()

    def spin(t, p):
        p["swirl"] = dict(side=-360 * t)
        p["swirl2"] = dict(side=720 * t)
        p["pulse"] = dict(scale=1 + 0.03 * math.sin(4 * math.pi * t))

    idle(m, bones=("swirl", "swirl2", "pulse"), extra=spin, linear=("swirl", "swirl2"))
    a = Anim(m, "Spawn", only=("pulse",))  # played when an enemy comes out
    a.pose(0)
    a.pose(4, pulse=dict(scale=1.25))
    a.pose(10, pulse=dict(scale=0.95))
    a.pose(16)
    a.done()
    return m


STRUCTURES = dict(castle=castle, portal=portal)


# --- props -----------------------------------------------------------------------------------
def pine(v):
    m = _model(f"Pine{v}", seed=900 + v)
    height, tiers, width = ((3.0, 5, 0.85), (3.9, 6, 0.72))[v - 1]
    m.seg("root", "bark", (0, 0, 0), (0, 0, height * 0.5), 0.12, 0.07, n=6, jitter=0.005)
    for k in range(3):
        m.seg("root", "bark2", (0, 0, 0.12), polar(0.26, k * 120 + 20, 0), 0.06, 0.02, n=5)
    z = height * 0.16
    for i in range(tiers):  # stacked, heavily overlapping cones with ragged rims
        t = i / (tiers - 1)
        r, h = width * (1 - t * 0.75), height * 0.3 * (1 - t * 0.35)
        m.cyl("root", ("pine2", "pine", "pine3")[i % 3], (0, 0, z + h / 2), r=r, r2=0, h=h, n=8,
              rot=(m.rng.uniform(-3, 3), m.rng.uniform(-3, 3), i * 23), jitter=0.045)
        z += h * 0.5
    m.build()
    return m


def oak(v):
    m = _model(f"Oak{v}", seed=920 + v)
    leaves = ("leaf", "leaf2", "leaf3") if v == 1 else ("autumn", "autumn2", "autumn3")
    s = 1.0 if v == 1 else 0.9
    m.seg("root", "bark", (0, 0, 0), (0.05, 0.02, 1.15 * s), 0.16, 0.1, n=7, jitter=0.008)
    for a, b in (((0.05, 0.02, 0.9), (0.45, 0.12, 1.5)), ((0.0, 0.0, 1.0), (-0.4, -0.12, 1.55)),
                 ((0.03, 0.0, 1.1), (0.05, -0.35, 1.6))):
        m.seg("root", "bark", tuple(c * s for c in a), tuple(c * s for c in b), 0.07, 0.035, n=6)
    for k in range(4):
        m.seg("root", "bark2", (0, 0, 0.15), polar(0.32, k * 90 + 40, 0), 0.07, 0.025, n=5)
    rng = m.rng
    blobs = [(0, 0, 1.9, 1.05), (0.5, 0.15, 1.7, 0.75), (-0.5, -0.1, 1.72, 0.78), (0.1, -0.5, 1.75, 0.72),
             (-0.1, 0.5, 1.8, 0.75), (0.35, -0.3, 2.2, 0.7), (-0.3, 0.3, 2.25, 0.72), (0.05, 0.05, 2.5, 0.65),
             (0.55, 0.35, 2.05, 0.55), (-0.55, -0.4, 2.0, 0.55)]
    for x, y, z, r in blobs:
        col = leaves[1] if z < 1.8 else rng.choice(leaves)
        m.ball("root", col, (x * s, y * s, z * s), (r * s, r * s, r * s * 0.82), rot=(0, 0, rng.uniform(0, 90)),
               jitter=0.06)
    m.build()
    return m


def dead_tree():
    m = _model("DeadTree", seed=940)
    for a, b, r1, r2 in (((0, 0, 0), (0.08, 0, 0.8), 0.13, 0.1), ((0.08, 0, 0.8), (-0.05, 0.05, 1.6), 0.1, 0.07),
                         ((-0.05, 0.05, 1.6), (0.1, 0, 2.2), 0.07, 0.02), ((0.08, 0, 0.8), (0.6, 0.1, 1.3), 0.06, 0.02),
                         ((0.45, 0.08, 1.15), (0.6, -0.15, 1.45), 0.03, 0.01),
                         ((-0.02, 0.04, 1.3), (-0.55, 0, 1.75), 0.05, 0.015),
                         ((-0.4, 0.01, 1.65), (-0.5, 0.25, 1.95), 0.025, 0.01),
                         ((0.05, 0.03, 1.9), (0.35, -0.2, 2.3), 0.035, 0.01)):
        m.seg("root", "deadwood", a, b, r1, r2, n=6)
    for k in range(4):
        m.seg("root", "deadwood", (0, 0, 0.15), polar(0.35, k * 90 + 30, 0), 0.07, 0.02, n=5)
    m.build()
    return m


def bush(v):
    m = _model(f"Bush{v}", seed=960 + v)
    blobs = ((0, 0, 0.3, 0.6), (0.3, 0.1, 0.25, 0.45), (-0.28, 0.05, 0.24, 0.45), (0.05, -0.25, 0.22, 0.4),
             (0, 0.25, 0.25, 0.42))
    for x, y, z, r in blobs:
        m.ball("root", m.rng.choice(("leaf", "leaf2", "leaf3")), (x, y, z), (r, r, r * 0.85), jitter=0.03)
    if v == 2:
        for _ in range(12):
            x, y, z, r = m.rng.choice(blobs)
            d = Vector((m.rng.uniform(-1, 1), m.rng.uniform(-1, 1), m.rng.uniform(0, 1))).normalized()
            m.ball("root", "berry", Vector((x, y, z)) + d * r * 0.47, 0.05)
    m.build()
    return m


def rock(v):
    m = _model(f"Rock{v}", seed=980 + v)
    rng = m.rng
    if v == 1:
        pieces = ((0, 0, 0.5, 0.4, 0.3), (0.32, 0.12, 0.18, 0.15, 0.12))
    elif v == 2:
        pieces = ((0, 0, 0.6, 0.5, 0.45), (0.4, 0.15, 0.4, 0.35, 0.3), (-0.3, 0.2, 0.35, 0.3, 0.25),
                  (0.1, -0.35, 0.25, 0.2, 0.15))
    else:
        pieces = ((0, 0, 1.3, 1.1, 0.95), (0.7, 0.3, 0.45, 0.4, 0.35), (-0.6, -0.35, 0.35, 0.3, 0.25))
    for x, y, sx, sy, sz in pieces:
        m.ball("root", rng.choice(("rock", "rock2", "rock3")), (x, y, sz * 0.35), (sx, sy, sz),
               rot=(0, 0, rng.uniform(0, 180)), jitter=sx * 0.08)
    if v == 3:
        m.ball("root", "moss", (0, 0, 0.72), (1.0, 0.85, 0.25), jitter=0.04)
    m.build()
    return m


def _mushroom(m, x, y, h, r, cap="red"):
    m.seg("root", "cream", (x, y, 0), (x, y, h), r * 0.3, r * 0.25, n=6)
    m.cyl("root", cap, (x, y, h + r * 0.2), r=r, r2=r * 0.3, h=r * 0.5, n=8)
    if cap == "red":
        for k in range(3):
            dx, dy, _ = polar(r * 0.55, k * 120 + 30, 0)
            m.ball("root", "cream", (x + dx, y + dy, h + r * 0.3), r * 0.25)


def stump():
    m = _model("Stump", seed=1000)
    m.cyl("root", "bark", (0, 0, 0.17), r=0.27, r2=0.23, h=0.34, n=9, jitter=0.01)
    m.cyl("root", "cut", (0, 0, 0.345), r=0.22, h=0.012, n=9)
    for r in (0.07, 0.14):
        m.ring("root", "cut2", (0, 0, 0.352), r, 0.007, n=10, squash=(1, 1))
    for k in range(4):
        m.seg("root", "bark2", (0, 0, 0.12), polar(0.42, k * 90 + 20, 0), 0.08, 0.03, n=5)
    m.seg("root", "wood", (0.05, 0, 0.35), (0.22, 0.08, 0.72), 0.022, n=5)
    m.prism("root", "iron2", [(0, -0.05), (0.12, -0.08), (0.12, 0.06), (0, 0.04)], 0.02, loc=(0.03, 0.0, 0.38),
            rot=(0, -60, 20))
    for x, y, h, r in ((0.3, -0.1, 0.1, 0.06), (0.26, 0.12, 0.07, 0.045), (-0.25, -0.22, 0.12, 0.07)):
        _mushroom(m, x, y, h, r)
    m.build()
    return m


def mushrooms():
    m = _model("Mushrooms", seed=1010)
    for x, y, h, r, cap in ((0, 0, 0.22, 0.13, "red"), (0.18, 0.08, 0.14, 0.09, "red"),
                            (-0.12, 0.14, 0.1, 0.07, "cut2"), (0.05, -0.18, 0.12, 0.08, "red"),
                            (-0.2, -0.08, 0.08, 0.05, "cut2")):
        _mushroom(m, x, y, h, r, cap)
    m.build()
    return m


def fence():
    m = _model("Fence", seed=1020)
    for x in (-0.95, 0.0, 0.95):
        m.seg("root", "wood", (x, 0, 0), (x, 0, 0.75), 0.05, n=6, jitter=0.004)
        m.cyl("root", "wood2", (x, 0, 0.8), r=0.05, r2=0, h=0.1, n=6)
    for z in (0.3, 0.6):
        m.box("root", m.rng.choice(("plank", "plank2")), (0, 0.04, z), (2.0, 0.04, 0.1), bevel=0.01, jitter=0.005)
    m.build()
    return m


def crates():
    m = _model("Crates", seed=1030)
    for (x, y, z), s, yaw in (((0, 0, 0.25), 0.5, 5), ((0.55, 0.05, 0.22), 0.44, -10), ((0.25, 0.02, 0.72), 0.42, 20)):
        m.box("root", "plank", (x, y, z), (s, s, s), rot=(0, 0, yaw), bevel=0.02 * s / 0.5)
        m.box("root", "wood2", (x, y, z), (s + 0.01, s + 0.01, s * 0.16), rot=(0, 0, yaw))
        m.box("root", "wood2", (x, y, z), (s * 0.16, s + 0.01, s + 0.01), rot=(0, 0, yaw))
    keg(m, (-0.5, 0.1, 0), 1.2)
    m.ball("root", "cloth", (-0.45, -0.38, 0.15), (0.35, 0.3, 0.32), jitter=0.02)
    m.ring("root", "rope", (-0.45, -0.38, 0.3), 0.05, 0.01, n=8)
    m.build()
    return m


def signpost():
    m = _model("Signpost", seed=1040)
    m.seg("root", "wood", (0, 0, 0), (0, 0, 1.5), 0.05, n=6)
    m.cyl("root", "wood2", (0, 0, 1.53), r=0.06, r2=0, h=0.06, n=6)
    arrow = [(0, -0.08), (0.45, -0.08), (0.55, 0), (0.45, 0.08), (0, 0.08)]
    m.prism("root", "plank", arrow, 0.04, loc=(0.02, -0.05, 1.3))
    m.prism("root", "plank2", [(-x, z) for x, z in arrow], 0.04, loc=(-0.02, -0.05, 1.05), rot=(0, 0, 25))
    m.build()
    return m


def lamppost():
    m = _model("Lamppost", seed=1050)
    m.cyl("root", "iron", (0, 0, 0.05), r=0.12, r2=0.09, h=0.1, n=8)
    m.seg("root", "iron", (0, 0, 0), (0, 0, 1.75), 0.04, 0.03, n=6)
    m.seg("root", "iron", (0, 0, 1.68), (0.32, 0, 1.72), 0.02, n=5)
    m.seg("root", "iron", (0.3, 0, 1.72), (0.3, 0, 1.64), 0.006, n=4)
    lantern(m, "flame1", (0.3, 0, 1.38))
    m.build()
    return m


def well():
    m = _model("Well", seed=1060)
    stone_drum(m, 0, 0.6, 0.55, 0.55)
    m.ring("root", "stone2", (0, 0, 0.62), 0.5, 0.07, n=12)
    m.cyl("root", "water", (0, 0, 0.5), r=0.42, h=0.02, n=12)
    for sx in (1, -1):
        m.seg("root", "wood", (sx * 0.5, 0, 0.6), (sx * 0.5, 0, 1.75), 0.045, n=6)
    m.seg("root", "wood", (-0.58, 0, 1.4), (0.62, 0, 1.4), 0.035, n=6)
    m.seg("root", "wood2", (0.62, 0, 1.4), (0.62, -0.15, 1.3), 0.015, n=4)
    m.seg("root", "rope", (0, 0, 1.38), (0, 0, 1.0), 0.008, n=4)
    m.cyl("root", "wood", (0, 0, 0.95), r=0.1, r2=0.12, h=0.16, n=8)
    for sy in (1, -1):
        m.box("root", "roof", (0, sy * 0.25, 1.63), (1.35, 0.62, 0.05), rot=(-sy * 35, 0, 0), bevel=0.01)
    m.seg("root", "roof2", (-0.68, 0, 1.81), (0.68, 0, 1.81), 0.03, n=6)
    m.build()
    return m


PROPS = dict(pine_1=partial(pine, 1), pine_2=partial(pine, 2), oak_1=partial(oak, 1), oak_2=partial(oak, 2),
             dead_tree=dead_tree, bush_1=partial(bush, 1), bush_2=partial(bush, 2), rock_1=partial(rock, 1),
             rock_2=partial(rock, 2), rock_3=partial(rock, 3), stump=stump, mushrooms=mushrooms, fence=fence,
             crates=crates, signpost=signpost, lamppost=lamppost, well=well)
