"""Level 2 "Haunted Forest" enemies: skeleton, zombie, witch (heals other enemies), gargoyle (flying)
and the stone golem boss. Same toolkit and conventions as mobs.py: Walk/Fly, Hit, Die; the witch and the
golem also have "Cast" (heal / ground slam), which enemy.gd plays for special abilities.
Glow colours keep enemies readable against the purple-lit level: skeleton and golem purple, zombie
yellow-green, witch mint (healing), gargoyle amber.
"""
import math

from mathutils import Vector

from haunted import Frame
from towers import polar
from lowpoly import SIDES, Anim, Model, biped_die, biped_hit, biped_rig, biped_walk, rag
from mobs import _along, _dir, _grip, _mirror


# ------------------------------------------------------------------------------------
def skeleton():
    """Fast, fragile (~1.25 m): bare bones, dented rusty helmet, notched rusty sword; purple eyes."""
    m = Model("Skeleton", dict(
        bone="#E2DBC6", bone2="#B5AD96", dark="#1A1620", rust="#7B5238", rust2="#5E3E2B", iron="#6C7177",
        iron2="#9AA0A6", cloth="#4A4038", cloth2="#3A322B", leather="#4A3426", eye="#B46CFF"),
        glow_color="#B46CFF", glow_strength=4.0, metal=("iron", "iron2"), seed=101)
    elbow_r, dir_r = Vector((-0.19, -0.01, 0.8)), _dir(-0.08, -0.85, -0.5)
    wrist_r = elbow_r + dir_r * 0.17
    biped_rig(m, hips=(0, 0, 0.62), chest=(0, 0, 0.72), neck=(0, -0.02, 0.98), head=(0, -0.03, 1.04),
              shoulder=(0.16, 0, 0.97), elbow=(0.19, -0.01, 0.8), wrist=(0.2, -0.03, 0.62),
              hip=(0.08, 0, 0.6), knee=(0.09, -0.01, 0.34), ankle=(0.09, 0.01, 0.075), wrist_r=wrist_r)
    m.bone("jaw", (0, -0.06, 1.06), "head")

    for s, side in SIDES:
        P = _mirror(s)
        th, sh, ft = f"thigh_{side}", f"shin_{side}", f"foot_{side}"
        ua, fa, hand = f"upperarm_{side}", f"forearm_{side}", f"hand_{side}"
        m.ball(th, "bone", P(0.08, 0, 0.6), 0.05)
        m.seg(th, "bone", P(0.08, 0, 0.6), P(0.09, -0.01, 0.36), 0.024, 0.02, n=6)
        m.ball(sh, "bone", P(0.09, -0.012, 0.34), (0.055, 0.05, 0.05))
        m.seg(sh, "bone2", P(0.09, -0.01, 0.33), P(0.09, 0.01, 0.09), 0.02, 0.017, n=6)
        m.seg(sh, "bone2", P(0.106, 0.0, 0.31), P(0.106, 0.012, 0.11), 0.009, n=4)
        m.ball(ft, "bone", P(0.09, 0.01, 0.075), 0.045)
        m.box(ft, "bone", P(0.09, -0.03, 0.035), (0.065, 0.11, 0.035), taper=0.8, bevel=0.008)
        for dx in (-0.02, 0.0, 0.02):
            m.seg(ft, "bone2", P(0.09 + dx, -0.08, 0.025), P(0.09 + dx * 1.3, -0.135, 0.014), 0.008, 0.006, n=4)

        m.ball(ua, "bone", P(0.16, 0, 0.97), 0.05)
        m.seg(ua, "bone", P(0.16, 0, 0.97), P(0.19, -0.01, 0.8), 0.018, 0.015, n=6)
        m.seg("chest", "bone", (0, -0.05, 0.945), P(0.15, -0.01, 0.965), 0.012, n=4)  # collarbone
        elbow = Vector(P(0.19, -0.01, 0.8))
        wrist = Vector(P(0.2, -0.03, 0.62)) if s > 0 else wrist_r
        m.ball(fa, "bone", elbow, 0.04)
        m.seg(fa, "bone2", elbow, wrist, 0.014, 0.012, n=5)
        m.seg(fa, "bone2", elbow + Vector((s * 0.013, 0, 0)), wrist + Vector((s * 0.013, 0, 0)), 0.008, n=4)
        if s > 0:  # bony hand hanging open
            m.box(hand, "bone", P(0.2, -0.035, 0.6), (0.04, 0.045, 0.04), bevel=0.006)
            for dx in (-0.013, 0.0, 0.013):
                m.seg(hand, "bone2", P(0.2 + dx, -0.04, 0.58), P(0.2 + dx * 1.3, -0.065, 0.52), 0.006, 0.004, n=4)
        else:
            m.box(hand, "bone", wrist_r + dir_r * 0.025, (0.045, 0.05, 0.045), rot=_along(dir_r), bevel=0.006)

    # pelvis with a tattered loincloth
    m.box("hips", "bone", (0, 0.01, 0.6), (0.17, 0.09, 0.06), bevel=0.015)
    for s in (1, -1):
        m.ball("hips", "bone", (s * 0.07, 0.0, 0.65), (0.09, 0.05, 0.09), rot=(0, -s * 20, 0))
    m.ring("hips", "leather", (0, 0.0, 0.645), 0.105, 0.012, n=10, squash=(1, 0.7))
    m.prism("hips", "cloth", rag(-0.06, 0.06, 0.64, 0.47, teeth=3, depth=0.03), 0.012, loc=(0, -0.07, 0))
    m.prism("hips", "cloth2", rag(-0.07, 0.07, 0.64, 0.45, teeth=3, depth=0.03), 0.012, loc=(0, 0.07, 0))

    # spine and ribcage (open at the front, a sternum in the gap)
    m.seg("chest", "bone2", (0, 0.04, 0.63), (0, 0.04, 0.94), 0.02, n=5)
    for z in (0.68, 0.73, 0.78, 0.83, 0.88, 0.93):
        m.ball("chest", "bone", (0, 0.05, z), (0.04, 0.04, 0.028))
    for z, r in ((0.76, 0.1), (0.81, 0.105), (0.86, 0.1), (0.91, 0.085)):
        m.ring("chest", "bone", (0, -0.005, z), r, 0.01, n=10, arc=290, squash=(1, 0.75))
    m.box("chest", "bone", (0, -0.075, 0.86), (0.025, 0.015, 0.13), bevel=0.004)
    m.seg("neck", "bone2", (0, 0.0, 0.94), (0, -0.03, 1.06), 0.018, n=5)
    for z in (0.97, 1.01):
        m.ball("neck", "bone", (0, -0.012 - (z - 0.94) * 0.25, z), (0.04, 0.04, 0.025))

    # skull, jaw and a dented rusty helmet
    m.ball("head", "bone", (0, -0.03, 1.13), (0.19, 0.21, 0.19), sub=2, jitter=0.003)
    m.box("head", "bone", (0, -0.1, 1.075), (0.12, 0.08, 0.07), taper=0.9, bevel=0.012)
    for s in (1, -1):
        m.box("head", "dark", (s * 0.038, -0.124, 1.12), (0.05, 0.03, 0.045), rot=(0, 0, -s * 10), bevel=0.006)
        m.ball("head", "eye", (s * 0.038, -0.132, 1.12), 0.024, glow=True)
    m.box("head", "dark", (0, -0.138, 1.087), (0.018, 0.02, 0.025), taper=0.5)
    m.box("head", "bone", (0, -0.136, 1.052), (0.09, 0.014, 0.02), bevel=0.003)
    m.box("jaw", "bone2", (0, -0.1, 1.025), (0.1, 0.08, 0.03), taper=0.85, bevel=0.008)
    m.box("jaw", "bone", (0, -0.134, 1.042), (0.08, 0.012, 0.016))
    m.ball("head", "iron", (0.012, -0.025, 1.19), (0.215, 0.235, 0.17), rot=(-6, 12, 0), sub=2)
    m.cyl("head", "rust", (0.008, -0.025, 1.165), r=0.118, r2=0.11, h=0.03, n=10, rot=(-6, 12, 0))
    m.seg("head", "rust2", (0.03, -0.03, 1.275), (0.0, 0.08, 1.24), 0.012, n=4)  # crest ridge
    m.box("head", "rust", (0.06, -0.1, 1.24), (0.05, 0.03, 0.035), rot=(20, 12, 25))  # rust patch / dent

    # rusty notched sword: grip through the fist, blade up and forward, edges forward/back
    g = _grip(dir_r)
    fist = wrist_r + dir_r * 0.025
    X = (dir_r - g * dir_r.dot(g)).normalized()

    def at(t, w=0.0):
        return fist + g * t + X * w

    edge = [(0.06, 0.026), (0.18, 0.027), (0.21, 0.012), (0.24, 0.027), (0.42, 0.024), (0.5, 0.0),
            (0.42, -0.022), (0.32, -0.026), (0.29, -0.014), (0.26, -0.026), (0.06, -0.026)]
    m.slab("hand_R", "iron", [at(t, w) for t, w in edge], 0.012)
    m.slab("hand_R", "rust", [at(0.09, 0.02), at(0.16, 0.022), at(0.15, -0.018), at(0.1, -0.02)], 0.016)
    m.seg("hand_R", "rust2", at(0.05, -0.06), at(0.05, 0.06), 0.011, n=4)
    m.seg("hand_R", "leather", at(-0.05), at(0.045), 0.013, n=5)
    m.ball("hand_R", "rust", at(-0.06), 0.028)
    m.build()

    def rattle(k, ph, up, p):
        p["jaw"] = dict(pitch=14 * up)
        p["head"]["yaw"] = p["head"].get("yaw", 0) + 6 * ph
        p["forearm_R"] = dict(pitch=-6 * up)
        p["upperarm_R"]["pitch"] *= 0.4

    biped_walk(m, frames=16, arm=30, elbow=20, bob=0.025, lean=7, sway=5, shift=0.01, twist=8, extra=rattle)
    biped_hit(m, push=0.03, extra=lambda p: p.update(jaw=dict(pitch=30)))
    biped_die(m, depth=0.08, push=0.03, extra=lambda p: p.update(jaw=dict(pitch=25)))
    return m


# ------------------------------------------------------------------------------------
def zombie():
    """Slow and tough (~1.6 m): hunched shambler reaching forward, torn clothes, open wound, limping."""
    m = Model("Zombie", dict(
        skin="#7D9468", skin2="#647A52", skin3="#8EA678", wound="#5E2A2E", wound2="#3E1A1E",
        shirt="#6E7A8A", shirt2="#525C6A", pants="#5A4A3A", pants2="#45392D", shoe="#2E2620",
        bone="#D8D0B8", teeth="#C8BC98", dark="#141016", hair="#2A2622", eye="#C6FF3A", rope="#8C7A58",
        stitch="#2A2420"),
        glow_color="#C6FF3A", glow_strength=3.5, seed=102)
    # both arms reach forward; the right one droops lower
    biped_rig(m, hips=(0, 0, 0.8), chest=(0, 0, 0.9), neck=(0, -0.14, 1.3), head=(0, -0.18, 1.37),
              shoulder=(0.2, -0.1, 1.24), elbow=(0.22, -0.34, 1.18), wrist=(0.22, -0.57, 1.14),
              hip=(0.1, 0, 0.78), knee=(0.11, -0.02, 0.44), ankle=(0.11, 0.01, 0.08), wrist_r=(-0.2, -0.53, 1.03))
    m.bone("jaw", (0, -0.25, 1.4), "head")

    for s, side in SIDES:
        P = _mirror(s)
        th, sh, ft = f"thigh_{side}", f"shin_{side}", f"foot_{side}"
        ua, fa, hand = f"upperarm_{side}", f"forearm_{side}", f"hand_{side}"
        m.seg(th, "pants", P(0.1, 0, 0.82), P(0.11, -0.02, 0.46), 0.072, 0.058, n=7)
        m.ball(sh, "pants2", P(0.11, -0.02, 0.44), 0.11)
        if s > 0:  # left trouser leg torn off at the knee: bare shin and foot
            m.prism(sh, "pants2", rag(0.05, 0.17, 0.44, 0.33, teeth=2, depth=0.03), 0.02, loc=(0, -0.05, 0))
            m.seg(sh, "skin", P(0.11, -0.02, 0.42), P(0.11, 0.01, 0.1), 0.042, 0.034, n=6)
            m.ball(sh, "bone", P(0.125, -0.045, 0.28), (0.03, 0.03, 0.06))  # shin bone showing
            m.box(ft, "skin", P(0.11, -0.04, 0.035), (0.08, 0.17, 0.05), taper=0.8, bevel=0.01)
            for dx in (-0.025, 0.0, 0.025):
                m.ball(ft, "skin2", P(0.11 + dx, -0.125, 0.025), (0.025, 0.04, 0.025))
        else:
            m.seg(sh, "pants", P(0.11, -0.02, 0.42), P(0.11, 0.01, 0.12), 0.058, 0.055, n=7)
            m.prism(sh, "pants2", rag(-0.17, -0.05, 0.16, 0.1, teeth=2, depth=0.025), 0.02, loc=(0, -0.05, 0))
            m.box(ft, "shoe", P(0.11, -0.04, 0.045), (0.1, 0.2, 0.08), taper=0.85, bevel=0.015)
            m.box(ft, "pants2", P(0.11, -0.12, 0.05), (0.06, 0.02, 0.03), bevel=0.005)  # sole flapping

        # arms: torn sleeve to the elbow, bare forearm, long drooping fingers
        elbow = Vector(P(0.22, -0.34, 1.18))
        wrist = Vector(P(0.22, -0.57, 1.14)) if s > 0 else Vector((-0.2, -0.53, 1.03))
        fdir = (wrist - elbow).normalized()
        m.ball(ua, "shirt", P(0.2, -0.1, 1.24), 0.12)
        m.seg(ua, "shirt", P(0.2, -0.1, 1.24), elbow, 0.055, 0.05, n=7)
        m.ball(fa, "skin2", elbow, 0.075)
        m.seg(fa, "shirt2", elbow - fdir * 0.02, elbow + fdir * 0.05, 0.058, 0.06, n=7)
        m.seg(fa, "skin", elbow, wrist, 0.04, 0.034, n=6)
        palm = wrist + fdir * 0.04
        m.box(hand, "skin", palm, (0.08, 0.08, 0.03), rot=_along(fdir), bevel=0.008)
        for k, dx in enumerate((-0.027, -0.009, 0.009, 0.027)):
            base = palm + fdir * 0.035 + Vector((dx, 0, 0))
            tip = base + fdir * 0.06 + Vector((0, 0, -0.045 - 0.01 * (k % 2)))
            m.seg(hand, "skin", base, tip, 0.01, 0.007, n=4)
            m.seg(hand, "dark", tip, tip + Vector((0, -0.006, -0.015)), 0.007, 0, n=3)
        m.seg(hand, "skin", palm + Vector((-s * 0.04, 0, 0)), palm + Vector((-s * 0.06, -0.04, -0.02)), 0.011, 0.008,
              n=4)
        if s > 0:  # only one ear left
            m.ball("head", "skin2", P(0.115, -0.2, 1.47), (0.03, 0.05, 0.06))

    # hips, belt, shirt tails
    m.box("hips", "pants", (0, 0, 0.82), (0.32, 0.22, 0.17), bevel=0.02)
    m.ring("hips", "rope", (0, 0, 0.88), 0.165, 0.014, n=10, squash=(1, 0.7))
    # hunched torso: shirt with a hole over the belly and a wound with ribs on the side
    m.box("chest", "shirt", (0, -0.06, 1.08), (0.38, 0.24, 0.4), rot=(22, 0, 0), taper=1.15, bevel=0.025, jitter=0.004)
    m.prism("chest", "shirt2", rag(-0.17, 0.17, 0.95, 0.8, teeth=4, depth=0.04), 0.02, loc=(0, -0.11, 0),
            rot=(10, 0, 0))
    m.prism("chest", "shirt", rag(-0.17, 0.17, 0.95, 0.82, teeth=3, depth=0.035), 0.02, loc=(0, 0.11, 0))
    m.ball("chest", "skin3", (0.03, -0.155, 1.02), (0.13, 0.05, 0.11))
    m.ball("chest", "wound", (0.165, -0.06, 1.06), (0.06, 0.15, 0.14))
    m.ball("chest", "wound2", (0.17, -0.06, 1.06), (0.05, 0.11, 0.1))
    for z in (1.02, 1.06, 1.1):
        m.seg("chest", "bone", (0.19, -0.11, z), (0.19, -0.01, z + 0.01), 0.008, n=4)
    for k in range(4):  # stitches across the shirt
        m.box("chest", "stitch", (-0.1 + k * 0.03, -0.17, 1.17 - k * 0.02), (0.006, 0.01, 0.04), rot=(22, 0, 40))
    m.seg("neck", "skin", (0, -0.11, 1.24), (0, -0.19, 1.4), 0.055, 0.05, n=7)

    # head: bald, stitched scar, mismatched glowing eyes, hanging jaw
    m.ball("head", "skin", (0, -0.2, 1.47), (0.24, 0.25, 0.25), sub=2, jitter=0.004)
    m.ball("head", "bone", (0.06, -0.13, 1.56), (0.09, 0.09, 0.06))  # bare skull patch
    m.box("head", "skin2", (0, -0.3, 1.5), (0.2, 0.06, 0.04), rot=(-8, 0, 0), bevel=0.01)
    m.box("head", "dark", (0.05, -0.31, 1.465), (0.065, 0.03, 0.05), bevel=0.008)
    m.box("head", "dark", (-0.05, -0.31, 1.46), (0.06, 0.03, 0.045), bevel=0.008)
    m.ball("head", "eye", (0.05, -0.322, 1.465), 0.034, glow=True)
    m.ball("head", "eye", (-0.05, -0.32, 1.455), 0.022, glow=True)
    m.box("head", "skin2", (0, -0.33, 1.43), (0.035, 0.03, 0.04), taper=0.6)
    m.box("head", "dark", (0, -0.31, 1.395), (0.13, 0.04, 0.04))
    m.box("head", "teeth", (0, -0.322, 1.41), (0.1, 0.012, 0.016))
    m.box("jaw", "skin2", (0, -0.29, 1.365), (0.15, 0.1, 0.04), rot=(18, 0, 0), taper=0.85, bevel=0.01)
    for x in (-0.04, -0.01, 0.025, 0.05):
        m.cyl("jaw", "teeth", (x, -0.33, 1.385), r=0.008, r2=0, h=0.022, n=4)
    for k in range(5):
        m.box("head", "stitch", (-0.11 + k * 0.03, -0.24 + k * 0.02, 1.575 - abs(k - 2) * 0.008),
              (0.008, 0.04, 0.008), rot=(0, 0, 30))
    for x, y in ((-0.06, -0.08), (-0.09, -0.12), (-0.03, -0.06)):
        m.seg("head", "hair", (x, y, 1.56), (x - 0.03, y + 0.04, 1.47), 0.009, 0.003, n=3)
    m.build()

    def shamble(k, ph, up, p):
        p["thigh_R"]["pitch"] *= 0.6  # stiff right leg -> limp
        p["shin_R"]["pitch"] *= 0.3
        p["foot_R"]["pitch"] *= 0.3
        p["head"] = dict(pitch=6, side=12 + 4 * ph, yaw=-5 * ph)
        p["jaw"] = dict(pitch=6 + 8 * up)
        p["upperarm_L"] = dict(pitch=-4 * up + 4 * ph, side=-3)
        p["upperarm_R"] = dict(pitch=-3 * up - 4 * ph, side=3)
        p["forearm_L"] = dict(pitch=-5 * up)
        p["forearm_R"] = dict(pitch=-3 * up)

    biped_walk(m, frames=32, stride=0.65, arm=0, elbow=0, bob=0.04, lean=6, sway=7, shift=0.03, twist=5,
               extra=shamble)
    biped_hit(m, push=0.05, extra=lambda p: p.update(jaw=dict(pitch=25)))
    biped_die(m, depth=0.14, push=0.05, extra=lambda p: p.update(jaw=dict(pitch=20)))
    return m


# ------------------------------------------------------------------------------------
def witch():
    """Healer (~1.95 m with the hat): hunched old witch in a ragged robe, crooked hat, gnarled staff with a
    glowing crystal. Cast: raises the staff to heal enemies around her."""
    m = Model("Witch", dict(
        skin="#8FA37A", skin2="#73865F", nose="#7E9268", wart="#5E6E4A", nail="#2A2420",
        robe="#3A2A4A", robe2="#2C2038", robe3="#4A3760", shawl="#4E3B2E", shawl2="#3C2D22",
        hat="#2A2033", hat2="#1E1726", band="#6B4A8A", buckle="#B8902E", hair="#B9B6AE", hair2="#8F8C85",
        wood="#4A3524", wood2="#3A291C", boot="#241C18", bottle="#2F5A4A", cork="#8A6A45", magic="#5CFFB0",
        bone="#D8D0B8", rope="#8C7A58", dark="#141016"),
        glow_color="#5CFFB0", glow_strength=4.5, metal=("buckle",), seed=103)
    elbow_r, dir_r = Vector((-0.21, -0.04, 1.0)), _dir(-0.05, -0.9, -0.35)
    wrist_r = elbow_r + dir_r * 0.2
    biped_rig(m, hips=(0, 0, 0.82), chest=(0, 0, 0.92), neck=(0, -0.1, 1.3), head=(0, -0.14, 1.36),
              shoulder=(0.17, -0.05, 1.24), elbow=(0.21, -0.04, 1.0), wrist=(0.22, -0.07, 0.8),
              hip=(0.08, 0, 0.8), knee=(0.09, -0.02, 0.45), ankle=(0.09, 0.0, 0.08), wrist_r=wrist_r)

    # robe: a ragged cone on the hips hides the legs, pointy boots peek out at the front
    m.cyl("hips", "robe", (0, 0.02, 0.47), r=0.3, r2=0.16, h=0.78, n=10, jitter=0.01)
    for k in range(10):
        deg = k * 36 + 18
        x, y = 0.28 * math.cos(math.radians(deg)), 0.02 + 0.28 * math.sin(math.radians(deg))
        m.cyl("hips", ("robe2", "robe")[k % 2], (x, y, 0.08 + (k % 3) * 0.01), r=0.075, r2=0, h=0.13, n=3,
              rot=(180, 0, deg + 90))
    m.ring("hips", "rope", (0, 0.0, 0.83), 0.165, 0.016, n=10)
    for x, col, lit in ((0.12, "bottle", True), (-0.13, "bottle", False)):
        m.ball("hips", "magic" if lit else col, (x, -0.13, 0.76), (0.06, 0.06, 0.08), glow=lit)
        m.cyl("hips", "cork", (x, -0.13, 0.82), r=0.015, h=0.025, n=5)
    m.box("hips", "shawl2", (0.17, -0.06, 0.74), (0.07, 0.06, 0.09), rot=(0, 0, 20), bevel=0.01)  # pouch
    for s, side in SIDES:
        P = _mirror(s)
        ft = f"foot_{side}"
        m.box(ft, "boot", P(0.09, -0.08, 0.04), (0.08, 0.2, 0.07), taper=0.75, bevel=0.012)
        m.seg(ft, "boot", P(0.09, -0.17, 0.04), P(0.09, -0.24, 0.08), 0.022, 0.0, n=4)
        m.seg(ft, "boot", P(0.09, 0.0, 0.06), P(0.09, 0.0, 0.2), 0.04, n=6)

    # torso and shawl
    m.box("chest", "robe2", (0, -0.04, 1.06), (0.32, 0.22, 0.36), rot=(18, 0, 0), taper=1.1, bevel=0.025)
    m.ball("chest", "shawl", (0, -0.07, 1.2), (0.46, 0.32, 0.18), rot=(18, 0, 0), jitter=0.006)
    for k in range(9):  # tassels along the shawl edge
        deg = 200 + k * 17.5
        x, y = 0.22 * math.cos(math.radians(deg)), -0.07 - 0.15 * math.sin(math.radians(deg))
        m.cyl("chest", "shawl2", (x, y, 1.1 - 0.03 * (k % 2)), r=0.02, r2=0, h=0.08, n=3, rot=(180, 0, 0))
    m.seg("neck", "skin", (0, -0.07, 1.24), (0, -0.14, 1.38), 0.04, 0.035, n=6)

    # arms: bell sleeves, bony green hands with dark nails
    for s, side in SIDES:
        P = _mirror(s)
        ua, fa, hand = f"upperarm_{side}", f"forearm_{side}", f"hand_{side}"
        elbow = Vector(P(0.21, -0.04, 1.0))
        wrist = Vector(P(0.22, -0.07, 0.8)) if s > 0 else wrist_r
        fdir = (wrist - elbow).normalized()
        m.seg(ua, "robe3", P(0.17, -0.05, 1.24), elbow, 0.05, 0.055, n=7)
        m.ball(fa, "robe3", elbow, 0.065)
        m.seg(fa, "robe3", elbow, elbow + fdir * 0.15, 0.055, 0.09, n=8)
        m.seg(fa, "skin", elbow + fdir * 0.1, wrist, 0.025, 0.022, n=5)
        if s > 0:
            m.box(hand, "skin", P(0.222, -0.075, 0.77), (0.045, 0.05, 0.05), bevel=0.008)
            for dx in (-0.014, 0.0, 0.014):
                tip = P(0.222 + dx * 1.3, -0.1, 0.7)
                m.seg(hand, "skin", P(0.222 + dx, -0.085, 0.75), tip, 0.008, 0.006, n=4)
                m.seg(hand, "nail", tip, (tip[0], tip[1] - 0.012, tip[2] - 0.018), 0.006, 0, n=3)
        else:
            fist = wrist_r + dir_r * 0.03
            m.box(hand, "skin", fist, (0.05, 0.055, 0.05), rot=_along(dir_r), bevel=0.008)

    # head: long hooked nose with a wart, pointy chin, stringy grey hair, crooked hat
    m.ball("head", "skin", (0, -0.16, 1.44), (0.19, 0.21, 0.21), sub=2, jitter=0.003)
    m.seg("head", "skin", (0, -0.2, 1.36), (0, -0.28, 1.3), 0.04, 0.01, n=6)
    m.seg("head", "nose", (0, -0.24, 1.45), (0, -0.33, 1.41), 0.026, 0.016, n=6)
    m.seg("head", "nose", (0, -0.33, 1.41), (0, -0.345, 1.37), 0.016, 0.005, n=5)
    m.ball("head", "wart", (0.016, -0.3, 1.43), 0.018)
    m.box("head", "dark", (0, -0.245, 1.37), (0.07, 0.02, 0.012), rot=(0, 0, 6))
    for s in (1, -1):
        m.ball("head", "magic", (s * 0.045, -0.245, 1.465), (0.03, 0.02, 0.022), glow=True)
        m.box("head", "skin2", (s * 0.05, -0.245, 1.495), (0.05, 0.03, 0.015), rot=(0, s * 15, 0))
    for x, y, dz in ((0.09, -0.16, 0.32), (0.07, -0.08, 0.38), (-0.09, -0.16, 0.3), (-0.07, -0.08, 0.36),
                     (0.0, -0.04, 0.42), (0.04, -0.05, 0.4), (-0.04, -0.05, 0.4)):
        m.seg("head", m.rng.choice(("hair", "hair2")), (x, y, 1.53), (x * 1.5, y + 0.12, 1.53 - dz), 0.022, 0.006,
              n=4)
    m.cyl("head", "hat", (0, -0.15, 1.55), r=0.3, h=0.025, n=12, rot=(-10, 6, 0), jitter=0.006)
    m.seg("head", "hat", (0, -0.15, 1.55), (0.01, -0.11, 1.8), 0.15, 0.09, n=10)
    m.seg("head", "hat2", (0.01, -0.11, 1.8), (0.05, 0.0, 1.97), 0.09, 0.045, n=8)
    m.seg("head", "hat2", (0.05, 0.0, 1.97), (0.13, 0.1, 2.0), 0.045, 0.0, n=8)
    m.ring("head", "band", (0, -0.14, 1.6), 0.14, 0.018, n=12)
    m.box("head", "buckle", (0, -0.28, 1.6), (0.06, 0.012, 0.045), bevel=0.004)

    # gnarled staff: grip through the fist, three wooden claws hold the glowing crystal
    g = _grip(dir_r)
    fist = wrist_r + dir_r * 0.03
    kink = fist + g * 0.25 + Vector((0.02, 0.0, 0.0))
    top = fist + g * 0.5
    m.seg("hand_R", "wood", fist - g * 0.72, fist, 0.022, 0.024, n=6)
    m.seg("hand_R", "wood", fist, kink, 0.024, 0.022, n=6)
    m.seg("hand_R", "wood", kink, top, 0.022, 0.026, n=6)
    m.ball("hand_R", "wood2", kink, 0.035)
    crystal = top + g * 0.08
    for k in range(3):
        a = math.radians(k * 120)
        out = Vector((math.cos(a), math.sin(a), 0)) * 0.055
        m.seg("hand_R", "wood2", top, crystal + out + g * 0.01, 0.014, 0.008, n=4)
        m.seg("hand_R", "wood2", crystal + out + g * 0.01, crystal + out * 0.4 + g * 0.08, 0.008, 0.0, n=4)
    m.ball("hand_R", "magic", crystal, (0.07, 0.07, 0.1), glow=True)
    m.seg("hand_R", "rope", top - g * 0.04, top - g * 0.04 + Vector((0.03, -0.02, -0.12)), 0.004, n=3)
    m.ball("hand_R", "bone", top - g * 0.04 + Vector((0.03, -0.02, -0.14)), (0.03, 0.03, 0.035))
    m.build()

    def hobble(k, ph, up, p):
        p["upperarm_R"]["pitch"] *= 0.3
        p["forearm_R"] = dict(pitch=-4 * up)
        p["head"]["pitch"] = p["head"].get("pitch", 0) + 3 * up

    biped_walk(m, frames=28, stride=0.6, arm=12, elbow=10, bob=0.03, lean=6, sway=4, shift=0.015, twist=5,
               extra=hobble)
    biped_hit(m, push=0.04)
    biped_die(m, depth=0.13, push=0.04)

    a = Anim(m, "Cast")
    # the staff is lifted upright: forearm and hand counter-rotate the raised upper arm
    raised = dict(chest=dict(pitch=-10), head=dict(pitch=-15), upperarm_R=dict(pitch=-80, side=8),
                  forearm_R=dict(pitch=30), hand_R=dict(pitch=45), upperarm_L=dict(pitch=-130, side=-25),
                  forearm_L=dict(pitch=-20), hips=dict(loc=(0, 0, 0.03)))
    a.pose(0)
    a.pose(8, **raised)
    a.pose(18, **dict(raised, upperarm_R=dict(pitch=-95, side=8), forearm_R=dict(pitch=35), hand_R=dict(pitch=55),
                      upperarm_L=dict(pitch=-145, side=-30),
                      hips=dict(loc=(0, 0, 0.05))))
    a.pose(26, **raised)
    a.pose(34)
    a.done()
    return m


# ------------------------------------------------------------------------------------
def gargoyle():
    """Flying stone gargoyle, body hovers at ~1.9 m: horns, stone bat wings, claws, tail, glowing eyes and cracks."""
    Z = 1.9

    def B(x, y, z):
        return (x, y, Z + z)

    m = Model("Gargoyle", dict(
        stone="#7E7B86", stone2="#67646F", stone3="#93909A", dark="#4E4B55", moss="#4F6B3A",
        wing="#5E5B66", wing2="#4C4954", horn="#3E3B44", claw="#2C2A30", eye="#FF8A3A"),
        glow_color="#FF8A3A", glow_strength=4.5, seed=104, ao_dist=0.12)
    m.preview_dir = (0.8, -1.0, 0.9)
    m.bone("root", (0, 0, 0))
    m.bone("body", B(0, 0, 0), "root")
    m.bone("chest", B(0, -0.03, 0.12), "body")
    m.bone("head", B(0, -0.24, 0.4), "chest")
    m.bone("jaw", B(0, -0.36, 0.4), "head")
    m.bone("tail1", B(0, 0.2, -0.2), "body")
    m.bone("tail2", B(0, 0.55, -0.4), "tail1")
    for s, side in SIDES:
        m.bone(f"wing_{side}", B(s * 0.13, 0.14, 0.32), "chest")
        m.bone(f"wingfore_{side}", B(s * 0.6, 0.28, 0.55), f"wing_{side}")
        m.bone(f"upperarm_{side}", B(s * 0.24, -0.14, 0.28), "chest")
        m.bone(f"forearm_{side}", B(s * 0.3, -0.24, 0.02), f"upperarm_{side}")
        m.bone(f"thigh_{side}", B(s * 0.13, 0.05, -0.2), "body")
        m.bone(f"shin_{side}", B(s * 0.16, -0.18, -0.36), f"thigh_{side}")

    # torso leaning forward with a glowing crack across the chest
    m.ball("body", "stone2", B(0, 0.03, -0.13), (0.34, 0.3, 0.3), jitter=0.012)
    C = Frame(B(0, -0.06, 0.18), (28, 0, 0))
    m.box("chest", "stone", C.p((0, 0, 0)), (0.44, 0.3, 0.42), rot=C.r(), taper=1.25, bevel=0.04, jitter=0.01)
    for sx in (1, -1):
        m.box("chest", "stone3", C.p((sx * 0.1, -0.16, 0.08)), (0.17, 0.06, 0.14), rot=C.r((0, 0, sx * 6)),
              bevel=0.02)
    for k in range(3):
        m.box("chest", "stone2", C.p((0, -0.155, -0.04 - k * 0.06)), (0.16 - k * 0.02, 0.05, 0.045), rot=C.r(),
              bevel=0.01)
    for (x0, z0), (x1, z1) in zip(((-0.12, 0.13), (-0.05, 0.05), (0.03, 0.08), (0.08, -0.02)),
                                  ((-0.05, 0.05), (0.03, 0.08), (0.08, -0.02), (0.13, -0.08))):
        m.seg("chest", "eye", C.p((x0, -0.19, z0)), C.p((x1, -0.19, z1)), 0.008, n=3, glow=True)
    m.ball("chest", "moss", C.p((0.15, 0.05, 0.2)), (0.2, 0.18, 0.06), rot=C.r())
    for k in range(3):  # spine ridge
        m.cyl("chest", "horn", C.p((0, 0.16, 0.12 - k * 0.12)), r=0.035, r2=0, h=0.1, n=4, rot=C.r((-40, 0, 0)))

    # head with horns, brow, glowing eyes and a fanged jaw
    m.box("head", "stone", B(0, -0.33, 0.48), (0.22, 0.24, 0.2), taper=0.85, bevel=0.03, jitter=0.006)
    m.box("head", "stone2", B(0, -0.45, 0.45), (0.15, 0.14, 0.1), taper=0.85, bevel=0.02)
    m.box("head", "dark", B(0, -0.44, 0.535), (0.21, 0.06, 0.04), rot=(-15, 0, 0), bevel=0.01)
    m.box("jaw", "stone2", B(0, -0.42, 0.385), (0.15, 0.18, 0.05), taper=0.9, bevel=0.012)
    for s, side in SIDES:
        m.ball("head", "eye", B(s * 0.055, -0.44, 0.5), (0.04, 0.03, 0.025), glow=True)
        m.seg("head", "horn", B(s * 0.07, -0.3, 0.56), B(s * 0.15, -0.2, 0.7), 0.04, 0.025, n=5)
        m.seg("head", "horn", B(s * 0.15, -0.2, 0.7), B(s * 0.13, -0.06, 0.8), 0.025, 0.0, n=5)
        m.seg("head", "stone2", B(s * 0.1, -0.3, 0.5), B(s * 0.2, -0.25, 0.56), 0.035, 0.0, n=4, squash=(0.4, 1))
        m.cyl("head", "stone3", B(s * 0.045, -0.5, 0.39), r=0.012, r2=0, h=0.04, n=4, rot=(180, 0, 0))
        m.cyl("jaw", "stone3", B(s * 0.055, -0.47, 0.42), r=0.013, r2=0, h=0.05, n=4)

        # arms dangling forward with claws
        ua, fa = f"upperarm_{side}", f"forearm_{side}"
        sh_, el, wr = Vector(B(s * 0.24, -0.14, 0.28)), Vector(B(s * 0.3, -0.24, 0.02)), Vector(B(s * 0.28, -0.4, -0.18))
        m.ball(ua, "stone2", sh_ + Vector((s * 0.02, 0, 0.03)), (0.2, 0.2, 0.17), jitter=0.01)
        m.seg(ua, "stone", sh_, el, 0.065, 0.055, n=6)
        m.ball(fa, "stone2", el, 0.1)
        m.seg(fa, "stone", el, wr, 0.055, 0.05, n=6)
        fdir = (wr - el).normalized()
        m.box(fa, "stone2", wr + fdir * 0.04, (0.09, 0.09, 0.07), rot=_along(fdir), bevel=0.012)
        for dx in (-0.03, 0.0, 0.03):
            base = wr + fdir * 0.07 + Vector((dx, 0, 0))
            m.seg(fa, "claw", base, base + fdir * 0.05 + Vector((0, 0, -0.05)), 0.014, 0.0, n=4)

        # crouched legs with talons
        th, shn = f"thigh_{side}", f"shin_{side}"
        hip, knee, ankle = B(s * 0.13, 0.05, -0.2), B(s * 0.16, -0.18, -0.36), B(s * 0.16, 0.02, -0.56)
        m.seg(th, "stone", hip, knee, 0.085, 0.065, n=6)
        m.ball(shn, "stone2", knee, 0.12)
        m.seg(shn, "stone", knee, ankle, 0.06, 0.045, n=6)
        m.box(shn, "stone2", B(s * 0.16, -0.05, -0.6), (0.1, 0.16, 0.06), taper=0.8, bevel=0.012)
        for dx in (-0.035, 0.0, 0.035):
            m.seg(shn, "claw", B(s * 0.16 + dx, -0.12, -0.6), B(s * 0.16 + dx * 1.3, -0.18, -0.66), 0.015, 0, n=4)

        # wings: arm bones, three fingers, angular stone membranes
        S, F = f"wing_{side}", f"wingfore_{side}"
        w0, w1, w2 = B(s * 0.13, 0.14, 0.32), B(s * 0.6, 0.28, 0.55), B(s * 1.0, 0.32, 0.6)
        t1, t2, t3 = B(s * 1.35, 0.42, 0.38), B(s * 1.18, 0.55, 0.05), B(s * 0.78, 0.5, -0.05)
        m.seg(S, "stone2", w0, w1, 0.055, 0.04, n=6)
        m.ball(F, "stone2", w1, 0.08)
        m.seg(F, "stone2", w1, w2, 0.04, 0.03, n=6)
        m.ball(F, "stone2", w2, 0.06)
        m.seg(F, "horn", w2, B(s * 1.08, 0.3, 0.75), 0.03, 0.0, n=4)
        for t in (t1, t2, t3):
            m.seg(F, "stone2", w2, t, 0.022, 0.008, n=5)
        m.slab(S, "wing2", [w0, w1, B(s * 0.6, 0.45, 0.05), B(s * 0.35, 0.38, -0.02), B(s * 0.14, 0.28, 0.05)], 0.02)
        m.slab(F, "wing", [w1, w2, t3, B(s * 0.6, 0.45, 0.05)], 0.02)
        m.slab(F, "wing2", [w2, t2, B(s * 0.95, 0.56, -0.05), t3], 0.02)
        m.slab(F, "wing", [w2, t1, B(s * 1.22, 0.52, 0.25), t2], 0.02)

    # tail with a spade tip
    m.seg("tail1", "stone", B(0, 0.18, -0.2), B(0, 0.55, -0.4), 0.07, 0.05, n=6)
    m.ball("tail2", "stone2", B(0, 0.55, -0.4), 0.09)
    m.seg("tail2", "stone", B(0, 0.55, -0.4), B(0, 0.88, -0.62), 0.05, 0.02, n=6)
    m.slab("tail2", "horn", [B(0, 0.84, -0.6), B(0.09, 0.92, -0.66), B(0, 1.06, -0.74), B(-0.09, 0.92, -0.66)], 0.025)
    m.build()

    a = Anim(m, "Fly", loop=True)
    for f, flap, lift in ((0, 30, 0.0), (6, 5, 0.07), (12, -35, 0.14), (18, -5, 0.07), (24, 30, 0.0)):
        a.pose(f, body=dict(loc=(0, 0, -lift), pitch=-2 + lift * 20), chest=dict(pitch=-flap * 0.05),
               head=dict(pitch=flap * 0.1), jaw=dict(pitch=4 + lift * 30),
               tail1=dict(pitch=-flap * 0.15, yaw=flap * 0.1), tail2=dict(pitch=-flap * 0.2, yaw=flap * 0.15),
               wing_L=dict(side=-flap), wing_R=dict(side=flap),
               wingfore_L=dict(side=-flap * 0.6), wingfore_R=dict(side=flap * 0.6),
               upperarm_L=dict(pitch=-10 + flap * 0.2), upperarm_R=dict(pitch=-10 + flap * 0.2),
               forearm_L=dict(pitch=10), forearm_R=dict(pitch=10),
               thigh_L=dict(pitch=10), thigh_R=dict(pitch=10), shin_L=dict(pitch=-10), shin_R=dict(pitch=-10))
    a.done()

    a = Anim(m, "Hit")
    a.pose(0)
    a.pose(3, body=dict(loc=(0, 0.12, 0.05), pitch=-15, side=8), chest=dict(pitch=-12), head=dict(pitch=-12),
           jaw=dict(pitch=30), wing_L=dict(side=-40), wing_R=dict(side=40), upperarm_L=dict(pitch=-30),
           upperarm_R=dict(pitch=-30), tail1=dict(pitch=15))
    a.pose(10)
    a.done()

    a = Anim(m, "Die")
    a.pose(0)
    a.pose(8, body=dict(pitch=-25, side=20, loc=(0, 0, 0.1)), head=dict(pitch=-20), jaw=dict(pitch=35),
           wing_L=dict(side=-70), wing_R=dict(side=70))
    fallen = dict(root=dict(loc=(0, 0, -Z + 0.3)), body=dict(pitch=10, side=75), chest=dict(pitch=15),
                  head=dict(pitch=20, yaw=20), jaw=dict(pitch=25), tail1=dict(yaw=30), tail2=dict(yaw=30),
                  wing_L=dict(side=60, yaw=-20), wing_R=dict(side=-10, yaw=20), wingfore_L=dict(side=40),
                  upperarm_L=dict(pitch=-40), upperarm_R=dict(pitch=-20))
    a.pose(24, **fallen)
    a.pose(32, **dict(fallen, root=dict(loc=(0, 0, -Z + 0.26)), body=dict(pitch=10, side=82)))
    a.done()
    return m


# ------------------------------------------------------------------------------------
def golem():
    """Boss: huge rune-carved stone golem (~3.3 m) built from ruin blocks: glowing purple core and runes,
    mossy boulder shoulders, crystals on the back. Cast: ground slam with both fists."""
    m = Model("Golem", dict(
        stone="#86838C", stone2="#6F6C76", stone3="#9A97A0", dark="#3C3A42", moss="#4F6B3A", moss2="#3E5830",
        crystal="#4B2A6B", crystal2="#6A3A8F", rune="#C27CFF"),
        glow_color="#B46CFF", glow_strength=5.0, seed=105, ao_dist=0.3)
    K = 1.2
    biped_rig(m, hips=(0, 0, 1.15), chest=(0, 0, 1.35), neck=(0, -0.2, 2.4), head=(0, -0.25, 2.45),
              shoulder=(0.62, -0.05, 2.3), elbow=(0.78, -0.1, 1.65), wrist=(0.82, -0.18, 1.08),
              hip=(0.3, 0, 1.1), knee=(0.33, -0.05, 0.62), ankle=(0.33, 0, 0.2))

    for s, side in SIDES:
        P = _mirror(s)
        th, sh, ft = f"thigh_{side}", f"shin_{side}", f"foot_{side}"
        ua, fa, hand = f"upperarm_{side}", f"forearm_{side}", f"hand_{side}"
        # legs: stacked blocks
        m.box(th, "stone2", P(0.31, -0.02, 0.88), (0.36, 0.38, 0.44), bevel=0.04, jitter=0.015)
        m.ball(sh, "stone", P(0.33, -0.06, 0.62), (0.32, 0.32, 0.28), jitter=0.015)
        m.box(sh, "stone3", P(0.33, -0.2, 0.64), (0.2, 0.08, 0.18), rot=(-10, 0, 0), bevel=0.02)
        m.box(sh, "stone", P(0.33, -0.02, 0.38), (0.36, 0.38, 0.38), taper=1.15, bevel=0.04, jitter=0.015)
        m.box(ft, "stone2", P(0.33, -0.1, 0.1), (0.5, 0.62, 0.2), taper=0.9, bevel=0.04, jitter=0.012)
        for dx in (-0.14, 0.0, 0.14):
            m.box(ft, "stone3", P(0.33 + dx, -0.43, 0.07), (0.13, 0.14, 0.13), bevel=0.025, jitter=0.008)

        # arms: boulder shoulder, upper block, elbow, forearm widening to a huge fist
        m.ball(ua, "stone2", P(0.68, -0.02, 2.33), (0.56, 0.56, 0.46), jitter=0.03)
        m.ball(ua, m.rng.choice(("moss", "moss2")), P(0.66, 0.0, 2.52), (0.42, 0.42, 0.14), jitter=0.02)
        m.box(ua, "stone", P(0.71, -0.07, 1.98), (0.3, 0.3, 0.55), rot=(0, -s * 14, 0), bevel=0.04, jitter=0.012)
        m.ball(fa, "stone2", P(0.78, -0.1, 1.65), (0.3, 0.3, 0.28), jitter=0.015)
        m.box(fa, "stone", P(0.8, -0.14, 1.38), (0.36, 0.38, 0.55), taper=0.75, rot=(0, -s * 4, 0), bevel=0.04,
              jitter=0.012)
        F = Frame(P(0.97, -0.14, 1.38), (0, 0, s * 90))  # local -Y = outward
        for k, z in enumerate((-0.12, 0.0, 0.12)):  # glowing runes on the outer side of the forearm
            m.box(fa, "rune", F.p((0, 0, z)), (0.12 if k != 1 else 0.06, 0.02, 0.03), rot=F.r(), glow=True)
        m.box(hand, "stone3", P(0.82, -0.2, 0.92), (0.42, 0.44, 0.4), bevel=0.05, jitter=0.015)
        for dx in (-0.14, -0.045, 0.045, 0.14):
            m.box(hand, "stone2", P(0.82 + dx, -0.42, 0.86), (0.09, 0.07, 0.14), bevel=0.02, jitter=0.006)
        m.box(hand, "stone2", P(0.82 - 0.2, -0.34, 0.98), (0.09, 0.12, 0.16), rot=(0, 0, -s * 20), bevel=0.02)

    # pelvis and torso, the torso wider at the top and leaning forward
    m.box("hips", "stone2", (0, 0, 1.15), (0.85, 0.5, 0.32), bevel=0.05, jitter=0.012)
    m.box("hips", "dark", (0, -0.26, 1.15), (0.5, 0.04, 0.08), bevel=0.01)
    m.box("hips", "rune", (0, -0.285, 1.15), (0.3, 0.02, 0.025), glow=True)
    m.box("chest", "stone", (0, 0.02, 1.85), (1.1, 0.75, 0.95), taper=1.3, rot=(8, 0, 0), bevel=0.07, jitter=0.02)
    for sx in (1, -1):
        m.box("chest", "stone3", (sx * 0.27, -0.44, 2.05), (0.42, 0.12, 0.36), rot=(8, 0, sx * 5), bevel=0.03,
              jitter=0.008)
    m.box("chest", "stone2", (0, -0.36, 1.48), (0.62, 0.14, 0.2), rot=(8, 0, 0), bevel=0.03)
    # core: a glowing heart in a ring of dark stones with cracks radiating out
    m.ring("chest", "dark", (0, -0.42, 1.68), 0.17, 0.06, n=10, rot=(98, 0, 0))
    m.ball("chest", "rune", (0, -0.43, 1.68), (0.24, 0.12, 0.24), glow=True)
    C = Frame((0, -0.395, 1.68), (8, 0, 0))
    for k, deg in enumerate((20, 75, 160, 215, 290)):
        a = math.radians(deg)
        r = 0.27 + 0.04 * (k % 2)
        m.box("chest", "rune", C.p((r * math.sin(a), 0, r * math.cos(a))), (0.022, 0.02, 0.16), rot=C.r((0, deg, 0)),
              glow=True)
    # crystals growing out of the back, moss on top
    for x, z, lean, length in ((0.25, 2.2, 25, 0.5), (-0.2, 2.1, 30, 0.6), (0.05, 1.95, 40, 0.45),
                               (-0.35, 1.8, 35, 0.35)):
        base = Vector((x, 0.32, z))
        d = Vector((x * 0.6, math.sin(math.radians(lean)), math.cos(math.radians(lean)))).normalized()
        col = m.rng.choice(("crystal", "crystal2"))
        m.seg("chest", col, base, base + d * length * 0.75, 0.08, 0.07, n=5)
        m.seg("chest", col, base + d * length * 0.75, base + d * length, 0.07, 0.0, n=5)
        m.seg("chest", "rune", base + d * length * 0.82, base + d * length * 0.97, 0.03, 0.0, n=4, glow=True)
    m.ball("chest", "moss", (0, 0.15, 2.32), (0.8, 0.5, 0.12), jitter=0.02)

    # small head sunk between the shoulders: heavy brow, glowing eye slits, stone tusks
    m.box("head", "stone3", (0, -0.33, 2.55), (0.36, 0.34, 0.3), taper=0.9, bevel=0.04, jitter=0.008)
    m.box("head", "dark", (0, -0.49, 2.62), (0.4, 0.12, 0.08), rot=(-10, 0, 0), bevel=0.02)
    m.box("head", "stone2", (0, -0.45, 2.43), (0.3, 0.14, 0.1), bevel=0.02)
    for s in (1, -1):
        m.box("head", "rune", (s * 0.085, -0.505, 2.56), (0.085, 0.02, 0.035), rot=(0, 0, -s * 8), glow=True)
        m.seg("head", "stone3", (s * 0.12, -0.5, 2.43), (s * 0.14, -0.55, 2.55), 0.03, 0.0, n=4)
    m.ball("head", "moss2", (0.04, -0.3, 2.71), (0.26, 0.24, 0.07))
    for v in m.bm.verts:  # boss size: everything above was laid out for ~2.75 m
        v.co *= K
    m.bones = {name: (head * K, parent) for name, (head, parent) in m.bones.items()}
    m.build()

    def stomp(k, ph, up, p):
        p["chest"]["side"] = p["chest"].get("side", 0) * 1.5
        p["forearm_L"] = dict(pitch=-6 - 4 * up)
        p["forearm_R"] = dict(pitch=-6 - 4 * up)

    biped_walk(m, frames=40, stride=0.55, arm=14, elbow=6, bob=0.06 * K, lean=4, sway=5, shift=0.06 * K, twist=5,
               extra=stomp)
    biped_hit(m, push=0.08)
    biped_die(m, depth=0.4 * K, frames=44, push=0.1 * K)

    a = Anim(m, "Cast")  # ground slam
    up = dict(chest=dict(pitch=-15), head=dict(pitch=-10), hips=dict(loc=(0, 0, 0.05 * K)),
              upperarm_L=dict(pitch=-160, side=-12), upperarm_R=dict(pitch=-160, side=12),
              forearm_L=dict(pitch=-15), forearm_R=dict(pitch=-15))
    slam = dict(chest=dict(pitch=30), head=dict(pitch=10), hips=dict(loc=(0, -0.05 * K, -0.25 * K)),
                upperarm_L=dict(pitch=-45, side=-5), upperarm_R=dict(pitch=-45, side=5),
                forearm_L=dict(pitch=-10), forearm_R=dict(pitch=-10))
    for side in "LR":
        slam[f"thigh_{side}"] = dict(pitch=-35)
        slam[f"shin_{side}"] = dict(pitch=50)
        slam[f"foot_{side}"] = dict(pitch=-15)
    a.pose(0)
    a.pose(14, **up)
    a.pose(20, **slam)
    a.pose(30, **slam)
    a.pose(46)
    a.done()
    return m


# ------------------------------------------------------------------------------------
def ghost_knight():
    """Boss: spectral knight (~2.4 m) hovering on ragged wisps instead of legs: great helm with glowing eyes,
    spectral greatsword, a soul lantern on a chain, broken shackles, tattered cape and plume. In the game it
    regularly turns intangible (fx_phase) and shots pass through it."""
    m = Model("GhostKnight", dict(
        armor="#5E7A84", armor2="#455C66", edge="#9DB8C0", cloth="#24343C", cloth2="#1A262C", wisp="#6F949A",
        wisp2="#4F7076", leather="#2E3A3E", blade="#B8D4DA", blade2="#88A6AE", iron="#3F4A50", dark="#0E1418",
        soul="#7FF7FF"),
        glow_color="#7FF7FF", glow_strength=4.5, metal=("armor", "armor2", "edge", "blade", "blade2", "iron"), seed=106)
    arm_dir = dict(L=_dir(0.1, -0.75, -0.65), R=_dir(-0.05, -0.82, -0.57))
    wrists = {side: Vector((s * 0.5, -0.02, 1.45)) + arm_dir[side] * 0.33 for s, side in SIDES}
    m.bone("root", (0, 0, 0))
    m.bone("hover", (0, 0, 0.9), "root")
    m.bone("hips", (0, 0, 1.1), "hover")
    m.bone("wisp", (0, 0, 1.05), "hips")
    m.bone("wisp2", (0, 0.04, 0.6), "wisp")
    m.bone("chest", (0, 0, 1.3), "hips")
    m.bone("neck", (0, -0.02, 1.95), "chest")
    m.bone("head", (0, -0.03, 2.03), "neck")
    m.bone("cape", (0, 0.22, 1.95), "chest")
    m.bone("cape2", (0, 0.29, 1.25), "cape")
    for s, side in SIDES:
        m.bone(f"upperarm_{side}", (s * 0.42, 0, 1.88), "chest")
        m.bone(f"forearm_{side}", (s * 0.5, -0.02, 1.45), f"upperarm_{side}")
        m.bone(f"hand_{side}", tuple(wrists[side]), f"forearm_{side}")
    lantern_top = wrists["L"] + arm_dir["L"] * 0.06 + Vector((0, 0, -0.05))
    m.bone("lantern", tuple(lantern_top), "hand_L")

    # lower body: a ragged spectral robe streaming into wisps
    m.cyl("wisp", "cloth", (0, 0.02, 0.86), r=0.2, r2=0.35, h=0.52, n=10, jitter=0.01)
    m.cyl("wisp", "cloth2", (0, 0.03, 0.62), r=0.17, r2=0.2, h=0.06, n=10)
    for k in range(8):
        deg = k * 45 + 10
        top = Vector(polar(0.17, deg, 0.62, (0, 0.03)))
        bottom = Vector(polar(0.06, deg + 25, 0.12 + 0.12 * (k % 3), (0, 0.12)))
        mid = top.lerp(bottom, 0.5) + Vector((0, 0.04, 0))
        col = ("wisp", "wisp2", "cloth")[k % 3]
        m.seg("wisp2", col, top, mid, 0.075, 0.05, n=5)
        m.seg("wisp2", col, mid, bottom, 0.05, 0.0, n=5)
    for deg in (60, 200, 320):  # faint glowing threads inside the wisps
        m.seg("wisp2", "soul", polar(0.1, deg, 0.6, (0, 0.03)), polar(0.05, deg + 30, 0.25, (0, 0.1)), 0.008, 0.0,
              n=3, glow=True)

    # faulds and tabard
    m.cyl("hips", "armor", (0, 0, 1.13), r=0.36, r2=0.3, h=0.24, n=10)
    m.cyl("hips", "edge", (0, 0, 1.02), r=0.365, r2=0.36, h=0.025, n=10)
    m.slab("hips", "cloth2", [(x, -0.37 - 0.05 * (1.2 - z), z) for x, z in rag(-0.12, 0.12, 1.2, 0.72, teeth=3,
                                                                                    depth=0.06)], 0.02)

    # breastplate with a cracked glowing soul in the middle
    m.box("chest", "armor", (0, 0, 1.62), (0.6, 0.38, 0.5), taper=1.2, bevel=0.03)
    m.box("chest", "edge", (0, -0.205, 1.64), (0.05, 0.035, 0.46), taper=1.1, bevel=0.008)
    m.box("chest", "armor2", (0, 0, 1.36), (0.58, 0.36, 0.06), bevel=0.01)
    m.cyl("chest", "armor", (0, -0.01, 1.92), r=0.2, r2=0.15, h=0.1, n=10)
    m.ring("chest", "edge", (0, -0.225, 1.68), 0.07, 0.016, n=10, rot=(90, 0, 0))
    m.ball("chest", "soul", (0, -0.23, 1.68), (0.09, 0.035, 0.09), glow=True)
    for (x0, z0), (x1, z1) in (((0.05, 1.71), (0.13, 1.8)), ((-0.04, 1.64), (-0.12, 1.55)), ((0.06, 1.64), (0.1, 1.52))):
        m.seg("chest", "soul", (x0, -0.222, z0), (x1, -0.215, z1), 0.008, n=3, glow=True)

    for s, side in SIDES:
        P = _mirror(s)
        ua, fa, hand = f"upperarm_{side}", f"forearm_{side}", f"hand_{side}"
        # rounded pauldron with two lames
        m.ball(ua, "armor", P(0.44, 0, 1.93), (0.32, 0.36, 0.24), rot=(0, -s * 20, 0))
        for k, dz in enumerate((-0.08, -0.15)):
            m.box(ua, ("armor2", "armor")[k], P(0.47 + 0.02 * k, 0, 1.92 + dz), (0.24 - 0.03 * k, 0.3, 0.06),
                  rot=(0, -s * (30 + 8 * k), 0), bevel=0.012)
        m.seg(ua, "armor2", P(0.42, 0, 1.86), P(0.5, -0.02, 1.48), 0.06, 0.055, n=7)
        elbow, d, wrist = Vector(P(0.5, -0.02, 1.45)), arm_dir[side], wrists[side]
        m.ball(fa, "armor", elbow, 0.12)
        m.seg(fa, "armor", elbow + d * 0.03, wrist, 0.065, 0.075, n=8)
        m.ring(fa, "iron", wrist - d * 0.05, 0.085, 0.018, n=10, rot=_along(d))  # shackle
        gauntlet = wrist + d * 0.06
        m.box(hand, "armor2", gauntlet, (0.12, 0.13, 0.12), rot=_along(d), bevel=0.02)
        # a few broken chain links hanging from the shackle
        link = wrist - d * 0.05 + Vector((s * 0.02, 0.0, -0.09))
        for k in range(3):
            m.ring(fa, "iron", link + Vector((0, 0, -0.065 * k)), 0.028, 0.008, n=8,
                   rot=(0, 90 if k % 2 else 0, s * 20))

    # great helm with a T-visor, glowing eyes and a tattered plume
    m.cyl("head", "armor", (0, -0.03, 2.14), r=0.165, r2=0.15, h=0.3, n=10)
    m.ball("head", "armor", (0, -0.03, 2.3), (0.3, 0.3, 0.12))
    m.box("head", "dark", (0, -0.18, 2.17), (0.2, 0.04, 0.035))
    m.box("head", "dark", (0, -0.18, 2.1), (0.035, 0.04, 0.12))
    for s in (1, -1):
        m.ball("head", "soul", (s * 0.055, -0.2, 2.17), (0.05, 0.025, 0.028), glow=True)
        for z in (2.04, 2.0):
            m.box("head", "dark", (s * 0.07, -0.172, z), (0.012, 0.03, 0.012))
    m.cyl("head", "edge", (0, -0.03, 2.25), r=0.172, h=0.03, n=10)
    m.box("head", "edge", (0, -0.19, 2.12), (0.03, 0.02, 0.2))  # nasal ridge
    m.slab("head", "cloth", [(0, -0.05, 2.35), (0, 0.08, 2.44), (0, 0.3, 2.32), (0, 0.42, 2.12), (0, 0.33, 2.15),
                             (0, 0.37, 2.0), (0, 0.22, 2.18), (0, 0.1, 2.3)], 0.04)

    # cape in two parts so it can sway
    m.slab("cape", "cloth", [(-0.34, 0.22, 1.97), (0.34, 0.22, 1.97), (0.42, 0.29, 1.27), (-0.42, 0.29, 1.27)], 0.03)
    m.slab("cape2", "cloth2", [(x, 0.29 + (1.29 - z) / 0.9 * 0.12, z)
                               for x, z in rag(-0.42, 0.42, 1.29, 0.42, teeth=5, depth=0.14)], 0.03)

    # spectral greatsword: grip through the right gauntlet, a glowing rune channel along the blade
    hilt = wrists["R"] + arm_dir["R"] * 0.06
    c = (_grip(arm_dir["R"]) * 0.866 + arm_dir["R"] * 0.5).normalized()
    X = (Vector((0, 0, 1)) - c * c.z).normalized()

    def at(t):
        return hilt + c * t

    blade = [(0.12, 0.06), (0.95, 0.05), (1.1, 0.0)]
    m.slab("hand_R", "blade", [at(t) + X * w for t, w in blade] + [at(t) - X * w for t, w in reversed(blade[:-1])],
           0.028)
    m.slab("hand_R", "soul", [at(0.18) + X * 0.012, at(0.88) + X * 0.008, at(0.88) - X * 0.008, at(0.18) - X * 0.012],
           0.034, glow=True)
    m.seg("hand_R", "edge", at(0.1) - X * 0.17, at(0.1) + X * 0.17, 0.028, n=6)
    for sx in (1, -1):
        m.seg("hand_R", "edge", at(0.1) + X * sx * 0.16, at(0.05) + X * sx * 0.23, 0.024, 0.0, n=4)
    m.seg("hand_R", "leather", at(-0.18), at(0.08), 0.024, n=6)
    m.ball("hand_R", "soul", at(-0.21), 0.05, glow=True)

    # soul lantern hanging on a short chain from the left gauntlet
    for k in range(2):
        m.ring("lantern", "iron", lantern_top + Vector((0, 0, -0.03 - 0.06 * k)), 0.025, 0.007, n=8,
               rot=(0, 90 if k % 2 else 0, 0))
    lz = lantern_top + Vector((0, 0, -0.38))
    m.cyl("lantern", "iron", lz + Vector((0, 0, 0.22)), r=0.11, r2=0.02, h=0.1, n=6)
    m.cyl("lantern", "iron", lz + Vector((0, 0, 0.16)), r=0.1, h=0.025, n=6)
    m.cyl("lantern", "iron", lz, r=0.09, r2=0.1, h=0.03, n=6)
    for k in range(6):
        a = math.radians(k * 60)
        p = lz + Vector((math.cos(a) * 0.088, math.sin(a) * 0.088, 0))
        m.seg("lantern", "iron", p, p + Vector((0, 0, 0.16)), 0.008, n=3)
    m.ball("lantern", "soul", lz + Vector((0, 0, 0.08)), (0.1, 0.1, 0.14), glow=True)
    m.build()

    a = Anim(m, "Walk", loop=True)
    for f in (0, 10, 20, 30, 40):
        ph = math.sin(f / 40 * 2 * math.pi)
        ph2 = math.cos(f / 40 * 2 * math.pi)
        a.pose(f, hover=dict(loc=(0, 0, 0.06 * ph)), hips=dict(yaw=3 * ph2), chest=dict(pitch=4, yaw=-4 * ph2),
               head=dict(pitch=-3 + 2 * ph), wisp=dict(pitch=-6 - 4 * ph2, side=4 * ph),
               wisp2=dict(pitch=-10 - 6 * ph2, side=-6 * ph), cape=dict(pitch=-6 - 3 * ph2),
               cape2=dict(pitch=-8 - 5 * ph2, side=3 * ph), upperarm_L=dict(pitch=-4 * ph2), upperarm_R=dict(pitch=2 * ph2),
               forearm_R=dict(pitch=-3 * ph), lantern=dict(pitch=12 * ph2, side=6 * ph))
    a.done()

    a = Anim(m, "Hit")
    a.pose(0)
    a.pose(3, hover=dict(loc=(0, 0.06, 0.02)), chest=dict(pitch=-12), head=dict(pitch=-10),
           upperarm_L=dict(pitch=-20, side=-10), upperarm_R=dict(pitch=-15, side=10), lantern=dict(pitch=-25),
           cape=dict(pitch=-12), cape2=dict(pitch=-10), wisp2=dict(pitch=-15))
    a.pose(10)
    a.done()

    a = Anim(m, "Die")  # the knight wails, then sinks into the ground, bowing forward
    a.pose(0)
    a.pose(10, hover=dict(loc=(0, 0, 0.12)), chest=dict(pitch=-22), head=dict(pitch=-30),
           upperarm_L=dict(pitch=-60, side=-35), upperarm_R=dict(pitch=-50, side=35), lantern=dict(pitch=-30),
           cape=dict(pitch=-20), wisp=dict(scale=1.1))
    a.pose(40, hover=dict(loc=(0, 0, -0.75)), chest=dict(pitch=35), head=dict(pitch=25), hips=dict(pitch=10),
           upperarm_L=dict(pitch=-20, side=-20), upperarm_R=dict(pitch=-30, side=25), lantern=dict(pitch=40),
           cape=dict(pitch=10), cape2=dict(pitch=15), wisp=dict(scale=0.5), wisp2=dict(scale=0.4))
    a.done()
    return m


MOBS = dict(skeleton=skeleton, zombie=zombie, witch=witch, gargoyle=gargoyle, golem=golem, ghost_knight=ghost_knight)
