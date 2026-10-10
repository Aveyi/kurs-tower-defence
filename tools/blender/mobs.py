"""Enemy (mob) models. Units are metres, the origin sits on the ground under the model."""
import math

from mathutils import Vector

from lowpoly import (SIDES, Anim, Model, _fcurves, biped_die, biped_hit, biped_rig, biped_walk, rag, rots)


def _mirror(s):
    return lambda x, y, z: (s * x, y, z)


def _dir(x, y, z):
    return Vector((x, y, z)).normalized()


def _grip(d):
    """Axis through a clenched fist whose forearm points along d: world up made perpendicular to d."""
    up = Vector((0, 0, 1))
    return (up - d * up.dot(d)).normalized()


def _along(d):
    """Euler (degrees) turning local +Z onto direction d (for rings/cylinders around a forearm)."""
    return [math.degrees(a) for a in d.to_track_quat("Z", "Y").to_euler()]


# ------------------------------------------------------------------------------------
def goblin():
    """Fast, weak base enemy (~0.9 m): big ears, hooked nose, curved dagger."""
    m = Model("Goblin", dict(
        skin="#79A93F", skin2="#5E8A31", belly="#93BF5A", nose="#6C9A38", ear_in="#C98B6B",
        leather="#5B3A22", leather2="#7A5032", cloth="#8A6A3E", cloth2="#6E5230", wrap="#C2AE84",
        metal="#B9C0C6", steel="#7E858C", teeth="#F1EBD2", mouth="#3A1A16", pupil="#1A1208",
        eye="#FFD447", claw="#3A2E22"),
        glow_color="#FFC93A", glow_strength=2.5, metal=("metal", "steel"), seed=11)
    # right forearm bent forward: the dagger hand is held in front, ready to stab
    elbow_r, dir_r = Vector((-0.18, -0.02, 0.48)), _dir(-0.1, -0.86, -0.5)
    wrist_r = elbow_r + dir_r * 0.125
    biped_rig(m, hips=(0, 0, 0.40), chest=(0, -0.01, 0.5), neck=(0, -0.04, 0.64), head=(0, -0.07, 0.69),
              shoulder=(0.13, -0.02, 0.62), elbow=(0.18, -0.02, 0.48), wrist=(0.21, -0.04, 0.36),
              hip=(0.075, 0, 0.40), knee=(0.085, -0.01, 0.23), ankle=(0.085, 0.01, 0.065), wrist_r=wrist_r)
    for s, side in SIDES:
        m.bone(f"ear_{side}", (s * 0.1, -0.07, 0.77), "head")

    # legs and arms
    for s, side in SIDES:
        P = _mirror(s)
        th, sh, ft = f"thigh_{side}", f"shin_{side}", f"foot_{side}"
        ua, fa, hand, ear = f"upperarm_{side}", f"forearm_{side}", f"hand_{side}", f"ear_{side}"
        m.seg(th, "cloth", P(0.075, 0, 0.42), P(0.08, -0.005, 0.33), 0.054, 0.05)
        m.seg(th, "skin", P(0.08, -0.005, 0.34), P(0.085, -0.01, 0.23), 0.04, 0.034, n=7)
        m.ball(sh, "skin2", P(0.085, -0.012, 0.23), 0.06)
        m.seg(sh, "skin", P(0.085, -0.01, 0.23), P(0.085, 0.01, 0.08), 0.033, 0.027, n=7)
        m.seg(sh, "wrap", P(0.085, 0.004, 0.13), P(0.085, 0.008, 0.088), 0.032, 0.031, n=7)
        m.box(ft, "skin", P(0.088, -0.03, 0.035), (0.075, 0.14, 0.055), taper=0.75, bevel=0.008)
        m.ball(ft, "skin2", P(0.088, 0.03, 0.035), (0.05, 0.05, 0.045))
        for dx in (-0.024, 0.0, 0.024):
            m.ball(ft, "skin", P(0.088 + dx, -0.105, 0.022), (0.03, 0.045, 0.03))
            m.cyl(ft, "claw", P(0.088 + dx, -0.13, 0.02), r=0.008, r2=0, h=0.02, n=4, rot=(90, 0, 0))

        m.seg(ua, "skin", P(0.13, -0.02, 0.62), P(0.18, -0.02, 0.48), 0.034, 0.028, n=7)
        m.ball(fa, "skin2", P(0.18, -0.02, 0.48), 0.05)
        if s > 0:  # left arm hangs, open clawed hand
            m.seg(fa, "skin", P(0.18, -0.02, 0.48), P(0.21, -0.04, 0.37), 0.027, 0.031, n=7)
            m.seg(fa, "wrap", P(0.197, -0.031, 0.425), P(0.209, -0.039, 0.38), 0.035, 0.036, n=7)
            m.box(hand, "skin", P(0.215, -0.045, 0.335), (0.05, 0.055, 0.06), bevel=0.008)
            m.seg(hand, "skin", P(0.198, -0.065, 0.345), P(0.194, -0.09, 0.32), 0.011, 0.008, n=5)  # thumb
            for dx in (-0.016, 0.0, 0.016):
                tip = P(0.22 + dx * 1.2, -0.075, 0.27)
                m.seg(hand, "skin", P(0.217 + dx, -0.055, 0.31), tip, 0.01, 0.007, n=5)
                m.seg(hand, "claw", tip, (tip[0], tip[1] - 0.012, tip[2] - 0.02), 0.007, 0, n=4)
        else:      # right forearm forward, fist around the dagger grip
            m.seg(fa, "skin", elbow_r, wrist_r, 0.027, 0.031, n=7)
            m.seg(fa, "wrap", elbow_r + dir_r * 0.06, elbow_r + dir_r * 0.11, 0.035, 0.036, n=7)
            fist = wrist_r + dir_r * 0.03
            m.box(hand, "skin", fist, (0.055, 0.06, 0.06), rot=_along(dir_r), bevel=0.008)
            m.box(hand, "skin2", fist + Vector((0.025, 0, 0)), (0.02, 0.05, 0.055), rot=_along(dir_r), bevel=0.005)

        # ears: outer leaf + pink inner ear
        m.seg(ear, "skin", P(0.09, -0.07, 0.77), P(0.32, -0.035, 0.85), 0.055, 0.0, n=6, squash=(0.33, 1))
        m.seg(ear, "ear_in", P(0.11, -0.083, 0.776), P(0.27, -0.046, 0.83), 0.036, 0.0, n=6, squash=(0.25, 1))
    m.ring("ear_L", "metal", (0.19, -0.06, 0.785), 0.016, 0.004, n=8, m=4, rot=(0, 90, 0))

    # body
    m.ball("hips", "belly", (0, -0.015, 0.48), (0.19, 0.16, 0.13), sub=2)
    m.box("hips", "cloth", (0, 0, 0.405), (0.2, 0.15, 0.1), bevel=0.015)
    m.ring("hips", "leather2", (0, -0.002, 0.452), 0.1, 0.016, n=12, squash=(1, 0.82))
    m.box("hips", "metal", (0, -0.092, 0.452), (0.035, 0.012, 0.03), bevel=0.004)
    m.prism("hips", "cloth2", rag(-0.06, 0.06, 0.445, 0.3, teeth=3, depth=0.025), 0.012, loc=(0, -0.096, 0))
    m.prism("hips", "cloth2", rag(-0.065, 0.065, 0.445, 0.31, teeth=3, depth=0.025), 0.012, loc=(0, 0.09, 0))
    m.box("hips", "leather", (-0.115, -0.05, 0.41), (0.05, 0.045, 0.06), bevel=0.008)       # pouch
    m.box("hips", "leather2", (-0.115, -0.074, 0.43), (0.052, 0.008, 0.03))

    m.ball("chest", "skin", (0, 0.005, 0.565), (0.23, 0.17, 0.19), rot=(15, 0, 0), sub=2)
    m.box("chest", "leather", (0, 0.01, 0.555), (0.255, 0.19, 0.13), rot=(15, 0, 0), taper=1.08, bevel=0.015)
    m.box("chest", "leather2", (0, -0.09, 0.528), (0.026, 0.012, 0.2), rot=rots((0, 38, 0), (15, 0, 0)))
    m.box("chest", "leather2", (0.15, -0.02, 0.63), (0.1, 0.12, 0.055), rot=(0, -15, 0), bevel=0.012)
    m.ring("chest", "wrap", (0, -0.03, 0.625), 0.07, 0.006, n=10, squash=(1, 0.8), rot=(15, 0, 0))
    for x in (-0.03, 0.0, 0.03):  # tooth necklace
        m.cyl("chest", "teeth", (x, -0.098, 0.6 - abs(x) * 0.3), r=0.009, r2=0, h=0.03, n=4, rot=(180, 0, 0))
    m.seg("neck", "skin", (0, -0.03, 0.6), (0, -0.07, 0.7), 0.04, 0.04)

    # head
    m.ball("head", "skin", (0, -0.08, 0.775), (0.22, 0.2, 0.18), sub=2, jitter=0.003)
    m.box("head", "skin", (0, -0.12, 0.71), (0.15, 0.11, 0.075), taper=1.15, bevel=0.012)
    m.ball("head", "belly", (0, -0.163, 0.69), (0.07, 0.05, 0.045))
    m.box("head", "skin2", (0, -0.158, 0.797), (0.17, 0.05, 0.035), rot=(-12, 0, 0), bevel=0.01)
    m.seg("head", "nose", (0, -0.16, 0.765), (0, -0.245, 0.722), 0.028, 0.013, n=6)
    m.ball("head", "nose", (0, -0.247, 0.72), 0.03)
    m.box("head", "mouth", (0, -0.176, 0.7), (0.11, 0.02, 0.02), bevel=0.004)
    for s in (1, -1):
        m.ball("head", "eye", (s * 0.05, -0.158, 0.765), (0.046, 0.032, 0.04), sub=2, glow=True)
        m.box("head", "pupil", (s * 0.05, -0.176, 0.765), (0.01, 0.008, 0.026))
        m.cyl("head", "teeth", (s * 0.032, -0.183, 0.705), r=0.009, r2=0, h=0.028, n=4)
    for x, y, z, rx in ((0, -0.03, 0.86, -20), (0.03, 0.0, 0.855, -35), (-0.025, 0.02, 0.845, -45)):
        m.cyl("head", "skin2", (x, y, z), r=0.012, r2=0, h=0.05, n=4, rot=(rx, 0, 0))  # hair tufts

    # curved dagger: its grip runs through the fist, the blade points forward and up
    g = _grip(dir_r)
    fist = wrist_r + dir_r * 0.03

    def Q(u, v):  # u along the grip axis, v along the forearm (blade back / edge)
        return fist + g * u + dir_r * v

    m.slab("hand_R", "metal", [Q(0.045, -0.02), Q(0.12, -0.024), Q(0.2, -0.016), Q(0.27, 0.012), Q(0.2, 0.02),
                               Q(0.12, 0.022), Q(0.045, 0.02)], 0.012)
    m.seg("hand_R", "steel", Q(0.04, -0.045), Q(0.04, 0.045), 0.012, n=5)
    m.seg("hand_R", "leather", fist - g * 0.04, fist + g * 0.04, 0.014, n=6)
    m.ball("hand_R", "steel", fist - g * 0.055, 0.024)
    m.build()

    def ears(k, ph, up, p):
        for side, sgn in (("L", 1), ("R", -1)):
            p[f"ear_{side}"] = dict(side=sgn * (6 if up else -6), pitch=4 * ph * sgn)
        p["forearm_R"] = dict(pitch=-6 * up)  # keep the dagger raised, just a little bounce
        p["upperarm_R"]["pitch"] *= 0.5

    biped_walk(m, frames=16, arm=28, elbow=30, bob=0.022, lean=8, sway=4, shift=0.008, twist=6, extra=ears)
    biped_hit(m, push=0.03, extra=lambda p: p.update(ear_L=dict(side=15), ear_R=dict(side=-15)))
    biped_die(m, depth=0.09, push=0.03)
    return m


# ------------------------------------------------------------------------------------
def orc():
    """Medium speed and health (~1.6 m): fur mantle, layered pauldron, big axe."""
    m = Model("Orc", dict(
        skin="#5F8A3E", skin2="#48692E", leather="#4A3324", leather2="#6B4A2F", boot="#2E2119",
        fur="#8C7355", fur2="#6E5840", iron="#6E757C", iron2="#A2A9B0", gold="#C59B3C",
        cloth="#8A2F27", cloth2="#5C1F1A", tusk="#EDE3C4", hair="#1C1C1C", wood="#6B4A2B", eye="#FF4A2A"),
        glow_color="#FF3B1F", glow_strength=4.0, metal=("iron", "iron2", "gold"), seed=22)
    # right forearm bent forward: the axe is held upright in front, ready to strike
    dir_r = _dir(-0.03, -0.95, -0.3)
    wrist_r = Vector((-0.36, 0, 0.98)) + dir_r * 0.22
    biped_rig(m, hips=(0, 0, 0.78), chest=(0, 0, 0.92), neck=(0, -0.03, 1.26), head=(0, -0.05, 1.33),
              shoulder=(0.3, 0, 1.24), elbow=(0.36, 0, 0.98), wrist=(0.39, -0.02, 0.75),
              hip=(0.13, 0, 0.76), knee=(0.14, -0.01, 0.43), ankle=(0.14, 0.01, 0.11), wrist_r=wrist_r)

    for s, side in SIDES:
        P = _mirror(s)
        th, sh, ft = f"thigh_{side}", f"shin_{side}", f"foot_{side}"
        ua, fa, hand = f"upperarm_{side}", f"forearm_{side}", f"hand_{side}"
        m.seg(th, "leather", P(0.13, 0, 0.8), P(0.14, -0.01, 0.45), 0.09, 0.075)
        m.ball(sh, "leather", P(0.14, -0.01, 0.43), 0.14)
        m.box(sh, "iron2", P(0.14, -0.075, 0.44), (0.11, 0.04, 0.12), bevel=0.012)
        m.seg(sh, "leather", P(0.14, -0.01, 0.43), P(0.14, 0.01, 0.2), 0.07, 0.065)
        m.seg(sh, "boot", P(0.14, 0.008, 0.27), P(0.14, 0.01, 0.1), 0.085, 0.09)
        m.seg(sh, "fur", P(0.14, 0.006, 0.295), P(0.14, 0.007, 0.25), 0.102, 0.1, jitter=0.006)
        m.box(ft, "boot", P(0.14, -0.045, 0.06), (0.15, 0.28, 0.12), taper=0.85, bevel=0.02)
        m.box(ft, "leather2", P(0.14, -0.165, 0.045), (0.13, 0.06, 0.07), taper=0.8, bevel=0.012)

        m.seg(ua, "skin", P(0.3, 0, 1.24), P(0.36, 0, 0.98), 0.085, 0.07)
        m.ball(ua, "skin", P(0.335, -0.012, 1.1), (0.15, 0.15, 0.17))
        elbow = Vector(P(0.36, 0, 0.98))
        fdir = (Vector(P(0.39, -0.02, 0.77)) - elbow).normalized() if s > 0 else dir_r
        wrist = elbow + fdir * (0.213 if s > 0 else 0.22)
        m.ball(fa, "skin2", elbow, 0.12)
        m.seg(fa, "skin", elbow, wrist, 0.065, 0.06)
        m.seg(fa, "leather", elbow + fdir * 0.04, elbow + fdir * 0.19, 0.078, 0.072)
        for t in (0.07, 0.15):
            m.seg(fa, "iron2", elbow + fdir * t, elbow + fdir * (t + 0.02), 0.081, 0.08)
        fist = wrist + fdir * 0.05
        m.box(hand, "skin", fist, (0.1, 0.11, 0.1), rot=_along(fdir), bevel=0.02)
        if s > 0:
            m.box(hand, "skin2", P(0.398, -0.075, 0.69), (0.09, 0.04, 0.08), bevel=0.012)
            m.seg(hand, "skin", P(0.37, -0.06, 0.73), P(0.36, -0.09, 0.7), 0.022, 0.018, n=5)
        else:  # fingers wrapped around the axe handle
            m.box(hand, "skin2", fist + Vector((0.05, 0, 0)), (0.03, 0.09, 0.09), rot=_along(fdir), bevel=0.01)

        # head details and hip plates
        m.seg("head", "tusk", P(0.075, -0.19, 1.35), P(0.09, -0.205, 1.445), 0.022, 0, n=5)
        m.ball("head", "eye", P(0.06, -0.185, 1.44), (0.045, 0.02, 0.03), glow=True)
        m.seg("head", "skin", P(0.12, -0.05, 1.45), P(0.24, -0.03, 1.51), 0.04, 0, n=5, squash=(0.4, 1))
        m.box("hips", "iron2", P(0.215, -0.01, 0.74), (0.04, 0.2, 0.17), rot=(0, -s * 12, 0), bevel=0.012)
        m.ball("hips", "gold", P(0.24, -0.06, 0.79), 0.022)
        m.ball("hips", "gold", P(0.24, 0.04, 0.79), 0.022)

    # hips
    m.box("hips", "leather", (0, 0, 0.79), (0.38, 0.25, 0.16), bevel=0.02)
    m.box("hips", "leather2", (0, 0, 0.865), (0.42, 0.28, 0.07), bevel=0.012)
    m.box("hips", "gold", (0, -0.145, 0.865), (0.1, 0.025, 0.08), bevel=0.01)
    m.box("hips", "iron", (0, -0.158, 0.865), (0.05, 0.01, 0.045), bevel=0.005)
    m.prism("hips", "cloth", rag(-0.09, 0.09, 0.84, 0.52, teeth=3, depth=0.05), 0.02, loc=(0, -0.14, 0))
    m.prism("hips", "cloth2", rag(-0.11, 0.11, 0.84, 0.55, teeth=3, depth=0.05), 0.02, loc=(0, 0.14, 0))

    # torso: skin, cuirass, plate, harness, fur mantle
    m.box("chest", "skin", (0, 0, 1.12), (0.46, 0.28, 0.28), taper=1.25, bevel=0.03, jitter=0.004)
    m.ball("chest", "skin", (0, 0.01, 1.24), (0.56, 0.32, 0.16), sub=2, jitter=0.004)
    m.box("chest", "leather", (0, 0, 0.98), (0.5, 0.31, 0.22), taper=1.05, bevel=0.02)
    m.box("chest", "iron", (0, -0.16, 1.03), (0.3, 0.04, 0.2), taper=1.1, bevel=0.012)
    for x, z in ((-0.11, 0.95), (0.11, 0.95), (-0.12, 1.11), (0.12, 1.11)):
        m.ball("chest", "iron2", (x, -0.182, z), 0.022)
    m.box("chest", "leather2", (0, -0.19, 1.07), (0.06, 0.016, 0.55), rot=(0, 35, 0))
    m.box("chest", "leather2", (0, 0.175, 1.07), (0.06, 0.016, 0.55), rot=(0, -35, 0))
    for x, y, z in ((0.2, 0.04, 1.27), (0.1, 0.09, 1.29), (0, 0.1, 1.3), (-0.1, 0.09, 1.29), (-0.2, 0.04, 1.27),
                    (0.15, -0.07, 1.27), (-0.15, -0.07, 1.27)):
        m.ball("chest", "fur" if x >= 0 else "fur2", (x, y, z), (0.17, 0.15, 0.11), jitter=0.01)
    m.seg("neck", "skin", (0, -0.01, 1.22), (0, -0.05, 1.35), 0.1, 0.095)

    # left pauldron (layered plates + spikes), right leather pad
    m.box("upperarm_L", "iron", (0.33, 0, 1.27), (0.24, 0.27, 0.1), rot=(0, -25, 0), bevel=0.02)
    m.box("upperarm_L", "iron2", (0.38, 0, 1.2), (0.16, 0.25, 0.08), rot=(0, -38, 0), bevel=0.015)
    m.box("upperarm_L", "gold", (0.335, 0, 1.325), (0.08, 0.275, 0.02), rot=(0, -25, 0))
    for y in (-0.07, 0.07):
        m.seg("upperarm_L", "iron2", (0.32, y, 1.3), (0.37, y, 1.44), 0.035, 0, n=5)
    m.box("upperarm_R", "leather2", (-0.32, 0, 1.26), (0.18, 0.24, 0.07), rot=(0, 25, 0), bevel=0.015)

    # head
    m.ball("head", "skin", (0, -0.06, 1.44), (0.27, 0.27, 0.25), sub=2, jitter=0.005)
    m.box("head", "skin", (0, -0.11, 1.355), (0.25, 0.17, 0.12), bevel=0.025)
    m.box("head", "skin2", (0, -0.19, 1.34), (0.2, 0.04, 0.05), bevel=0.01)
    m.box("head", "skin2", (0, -0.175, 1.47), (0.25, 0.07, 0.06), rot=(-10, 0, 0), bevel=0.015)
    m.box("head", "skin2", (0, -0.2, 1.415), (0.07, 0.05, 0.06), taper=0.6, bevel=0.01)
    for i, y in enumerate((-0.13, -0.06, 0.01, 0.08)):
        m.cyl("head", "hair", (0, y, 1.555 - 0.012 * abs(i - 1.5)), r=0.035, r2=0, h=0.11, n=4,
              rot=(-25, 0, 0), squash=(0.5, 1))
    m.seg("head", "hair", (0, 0.1, 1.5), (0, 0.17, 1.32), 0.03, 0.02, n=5)
    m.ring("head", "gold", (0, 0.14, 1.4), 0.03, 0.008, n=8, rot=(20, 0, 0))
    m.ring("head", "gold", (0.2, -0.035, 1.47), 0.016, 0.005, n=8, rot=(0, 90, 0))

    # axe: the handle runs through the fist (up = grip axis), the blade faces forward
    g = _grip(dir_r)
    fist = wrist_r + dir_r * 0.05
    head = fist + g * 0.5
    m.seg("hand_R", "wood", fist - g * 0.2, fist + g * 0.66, 0.026, 0.024, n=6)
    m.seg("hand_R", "leather2", fist - g * 0.09, fist + g * 0.09, 0.031, 0.031, n=6)
    m.seg("hand_R", "iron", fist - g * 0.2, fist - g * 0.28, 0.035, 0, n=5)
    m.seg("hand_R", "iron", head - g * 0.09, head + g * 0.09, 0.042, 0.042, n=6)

    def A(u, v):  # u along the handle, v forward across it
        return head + g * u + dir_r * v

    m.slab("hand_R", "iron", [A(-0.1, 0), A(-0.17, 0.16), A(-0.21, 0.2), A(0, 0.25), A(0.21, 0.2), A(0.17, 0.16),
                              A(0.1, 0)], 0.03)
    m.slab("hand_R", "iron2", [A(-0.21, 0.2), A(0, 0.25), A(0.21, 0.2), A(0.16, 0.175), A(0, 0.215),
                               A(-0.16, 0.175)], 0.034)
    m.seg("hand_R", "iron", head, head - dir_r * 0.12, 0.03, 0, n=4)
    m.seg("hand_R", "iron2", fist + g * 0.66, fist + g * 0.76, 0.025, 0, n=4)
    m.build()

    def axe_ready(k, ph, up, p):
        p["forearm_R"] = dict(pitch=-5 * up)
        p["upperarm_R"]["pitch"] *= 0.4

    biped_walk(m, frames=24, stride=0.9, arm=22, elbow=20, bob=0.035, lean=5, sway=3, shift=0.015, twist=6,
               extra=axe_ready)
    biped_hit(m, push=0.05)
    biped_die(m, depth=0.16, push=0.05)
    return m


# ------------------------------------------------------------------------------------
def troll():
    """Slow tank with lots of HP (~2.2 m, hunched): mossy back, skull necklace, spiked log club."""
    m = Model("Troll", dict(
        skin="#7E9089", skin2="#5E6E69", belly="#93A39B", loin="#6B5236", loin2="#4F3C27", rope="#B79E6E",
        wood="#5E4128", iron="#5B6168", nail="#E0D6B0", moss="#56752F", moss2="#6E8F3A",
        cream="#E8DCC0", red="#B8402F", bone="#E3DCC6", dark="#1E1A17", hair="#3A3F3C", eye="#FF9A1F"),
        glow_color="#FF9A1F", glow_strength=4.0, metal=("iron",), seed=33)
    # right forearm bent forward: the club is raised in front, heavy end up
    dir_r = _dir(-0.05, -0.9, -0.42)
    wrist_r = Vector((-0.66, -0.15, 1.25)) + dir_r * 0.38
    biped_rig(m, hips=(0, 0, 1.0), chest=(0, 0, 1.15), neck=(0, -0.3, 1.82), head=(0, -0.42, 1.9),
              shoulder=(0.55, -0.12, 1.8), elbow=(0.66, -0.15, 1.25), wrist=(0.71, -0.17, 0.84),
              hip=(0.26, 0, 0.95), knee=(0.28, -0.03, 0.53), ankle=(0.28, 0.01, 0.15), wrist_r=wrist_r)

    for s, side in SIDES:
        P = _mirror(s)
        th, sh, ft = f"thigh_{side}", f"shin_{side}", f"foot_{side}"
        ua, fa, hand = f"upperarm_{side}", f"forearm_{side}", f"hand_{side}"
        m.seg(th, "skin", P(0.26, 0, 1.0), P(0.28, -0.03, 0.55), 0.19, 0.15, jitter=0.012)
        m.ball(sh, "skin2", P(0.28, -0.04, 0.53), 0.26, jitter=0.01)
        m.seg(sh, "skin", P(0.28, -0.03, 0.53), P(0.28, 0.01, 0.17), 0.14, 0.13, jitter=0.01)
        m.ring(sh, "rope", P(0.28, 0.0, 0.25), 0.135, 0.015, n=10)
        m.box(ft, "skin2", P(0.29, -0.07, 0.08), (0.3, 0.4, 0.16), taper=0.85, bevel=0.03, jitter=0.008)
        for dx in (-0.09, 0.0, 0.09):
            m.box(ft, "skin", P(0.29 + dx, -0.27, 0.06), (0.08, 0.09, 0.09), bevel=0.015)
            m.box(ft, "nail", P(0.29 + dx, -0.315, 0.07), (0.06, 0.025, 0.05), bevel=0.006)

        m.ball(ua, "skin", P(0.55, -0.1, 1.8), 0.34, sub=2, jitter=0.012)
        m.seg(ua, "skin", P(0.56, -0.12, 1.75), P(0.66, -0.15, 1.27), 0.16, 0.13, jitter=0.012)
        m.ball(fa, "skin2", P(0.66, -0.15, 1.25), 0.24, jitter=0.01)
        if s > 0:  # left arm hangs down to the knuckles
            m.seg(fa, "skin", P(0.66, -0.15, 1.25), P(0.71, -0.17, 0.88), 0.13, 0.165, jitter=0.012)
            m.ring(fa, "rope", P(0.698, -0.165, 0.98), 0.155, 0.018, n=10)
            m.box(hand, "skin2", P(0.72, -0.18, 0.75), (0.22, 0.24, 0.2), bevel=0.035, jitter=0.008)
            for dx in (-0.065, 0.0, 0.065):
                m.box(hand, "skin", P(0.72 + dx, -0.3, 0.71), (0.065, 0.08, 0.13), bevel=0.015)
                m.box(hand, "nail", P(0.72 + dx, -0.335, 0.665), (0.05, 0.02, 0.04), bevel=0.005)
            m.seg(hand, "skin", P(0.62, -0.25, 0.79), P(0.6, -0.31, 0.74), 0.04, 0.035)
        else:  # right forearm forward, fist clenched around the club
            elbow = Vector(P(0.66, -0.15, 1.25))
            m.seg(fa, "skin", elbow, wrist_r, 0.13, 0.165, jitter=0.012)
            m.ring(fa, "rope", elbow + dir_r * 0.28, 0.155, 0.018, n=10, rot=_along(dir_r))
            fist = wrist_r + dir_r * 0.1
            m.box(hand, "skin2", fist, (0.22, 0.24, 0.2), rot=_along(dir_r), bevel=0.035, jitter=0.008)
            g = _grip(dir_r)
            for k in (-0.065, 0.0, 0.065):
                m.box(hand, "skin", fist + g * k + Vector((0.11, 0, 0)), (0.06, 0.09, 0.06), rot=_along(dir_r),
                      bevel=0.012)

        m.ball("head", "eye", P(0.09, -0.665, 2.02), (0.05, 0.03, 0.035), glow=True)
        m.seg("head", "skin", P(0.18, -0.48, 1.97), P(0.31, -0.45, 2.03), 0.06, 0, n=5, squash=(0.4, 1))
        m.cyl("head", "nail", P(0.12, -0.72, 1.92), r=0.03, r2=0, h=0.11, n=4)
        m.cyl("head", "nail", P(0.045, -0.73, 1.9), r=0.018, r2=0, h=0.05, n=4)

    # moss on the left shoulder with two little mushrooms
    m.ball("upperarm_L", "moss", (0.53, -0.08, 1.96), (0.3, 0.28, 0.1), jitter=0.012)
    for x, y, h in ((0.5, -0.05, 0.07), (0.58, -0.12, 0.05)):
        m.cyl("upperarm_L", "cream", (x, y, 2.0 + h / 2), r=0.018, h=h, n=6)
        m.cyl("upperarm_L", "red", (x, y, 2.0 + h + 0.015), r=0.05, r2=0.012, h=0.04, n=7)

    # hips: loincloth, rope belt, flaps
    m.box("hips", "loin", (0, 0, 1.0), (0.74, 0.5, 0.28), taper=0.9, bevel=0.03, jitter=0.008)
    m.ring("hips", "rope", (0, 0, 1.12), 0.38, 0.025, n=14, squash=(1, 0.72))
    m.ball("hips", "rope", (0.17, -0.27, 1.11), 0.07)
    m.prism("hips", "loin2", rag(-0.2, 0.2, 1.08, 0.66, teeth=4, depth=0.07), 0.035, loc=(0, -0.27, 0))
    m.prism("hips", "loin2", rag(-0.22, 0.22, 1.08, 0.68, teeth=4, depth=0.07), 0.035, loc=(0, 0.26, 0))

    # torso
    m.ball("chest", "belly", (0, -0.1, 1.35), (0.7, 0.48, 0.54), sub=2, jitter=0.015)
    m.ball("chest", "skin", (0, 0, 1.6), (1.1, 0.8, 0.82), sub=2, jitter=0.025)
    m.ball("chest", "skin2", (0, 0.2, 1.86), (0.82, 0.55, 0.45), jitter=0.02)
    m.ball("chest", "moss2", (-0.12, 0.3, 1.95), (0.45, 0.32, 0.14), jitter=0.015)
    for y, z, h in ((0.36, 2.0, 0.14), (0.45, 1.85, 0.16), (0.48, 1.67, 0.14), (0.44, 1.48, 0.11)):
        m.cyl("chest", "nail", (0, y, z), r=0.045, r2=0, h=h, n=4, rot=(-60, 0, 0))
    # skull necklace: rope follows the chest surface, skulls hang on it
    def on_chest(x, z, off):
        k = max(0.0, 1 - (x / 0.55) ** 2 - ((z - 1.6) / 0.41) ** 2)
        return (x, -0.4 * math.sqrt(k) - off, z)

    rope = [on_chest(x, 1.6 + 0.24 * (x / 0.32) ** 2, 0.012) for x in (-0.32, -0.2, -0.1, 0.0, 0.1, 0.2, 0.32)]
    for a, b in zip(rope, rope[1:]):
        m.seg("chest", "rope", a, b, 0.018, 0.018, n=5)
    for x in (-0.14, 0.0, 0.14):
        cx, cy, cz = on_chest(x, 1.6 + 0.24 * (x / 0.32) ** 2 - 0.06, 0.04)
        m.ball("chest", "bone", (cx, cy, cz), (0.09, 0.08, 0.085))
        m.box("chest", "bone", (cx, cy - 0.02, cz - 0.045), (0.05, 0.04, 0.03))
        for dx in (-0.02, 0.02):
            m.box("chest", "dark", (cx + dx, cy - 0.043, cz + 0.005), (0.022, 0.01, 0.02))
    m.seg("neck", "skin", (0, -0.12, 1.72), (0, -0.4, 1.9), 0.2, 0.17, jitter=0.01)

    # head
    m.ball("head", "skin", (0, -0.5, 1.95), (0.4, 0.38, 0.34), sub=2, jitter=0.01)
    m.box("head", "skin2", (0, -0.6, 1.84), (0.38, 0.26, 0.16), taper=1.1, bevel=0.03)
    m.ball("head", "skin2", (0, -0.71, 1.98), (0.15, 0.14, 0.17))
    m.box("head", "skin2", (0, -0.655, 2.07), (0.36, 0.09, 0.07), rot=(-8, 0, 0), bevel=0.02)
    m.ball("head", "skin2", (0.12, -0.6, 2.06), 0.04)
    m.ball("head", "skin2", (-0.15, -0.46, 2.1), 0.045)
    for x, y, rx in ((0, -0.47, -30), (0.05, -0.42, -45), (-0.04, -0.4, -50)):
        m.cyl("head", "hair", (x, y, 2.1), r=0.02, r2=0, h=0.08, n=4, rot=(rx, 0, 0))

    # log club: thin end in the fist, heavy spiked end raised forward
    fist = wrist_r + dir_r * 0.1
    d = (_grip(dir_r) + dir_r * 0.15).normalized()
    a, b = fist - d * 0.14, fist + d * 0.78
    m.seg("hand_R", "wood", a, b, 0.07, 0.18, n=8, jitter=0.01)
    u = d.cross(Vector((1, 0, 0))).normalized()
    v = d.cross(u)
    for t in (0.5, 0.82):
        c = a.lerp(b, t)
        r = 0.07 + 0.11 * t + 0.008
        m.seg("hand_R", "iron", c, c + d * 0.04, r, r)
    for t, ang in ((0.62, 0), (0.66, 120), (0.7, 240), (0.9, 60), (0.93, 180), (0.95, 300)):
        c = a.lerp(b, t)
        dirv = u * math.cos(math.radians(ang)) + v * math.sin(math.radians(ang))
        base = c + dirv * (0.07 + 0.11 * t - 0.01)
        m.seg("hand_R", "iron", base, base + dirv * 0.12, 0.03, 0, n=4)
    m.build()

    def heavy(k, ph, up, p):
        p["head"]["pitch"] = -6 + 3 * up
        p["neck"]["pitch"] = -4
        p["forearm_R"] = dict(pitch=-4 * up)
        p["upperarm_R"]["pitch"] *= 0.4

    biped_walk(m, frames=32, stride=0.7, arm=14, elbow=15, bob=0.05, lean=4, sway=6, shift=0.05, twist=5,
               extra=heavy)
    biped_hit(m, push=0.08)
    biped_die(m, depth=0.3, frames=40, push=0.1)
    return m


# ------------------------------------------------------------------------------------
def wyvern():
    """Flying enemy, only some towers can hit it. Origin on the ground, body hovers at ~1.8 m."""
    Z = 1.8

    def B(x, y, z):
        return (x, y, Z + z)

    m = Model("Wyvern", dict(
        scale="#8E2F2F", scale2="#6B2222", scale3="#A8443A", belly="#D9A066", belly2="#BF8A52",
        wing="#B5523B", wing2="#94402F", horn="#E8DFC8", horn2="#BFB39A", claw="#2B2420",
        mouth="#4A1515", teeth="#F1EBD2", eye="#FFE14D"),
        glow_color="#FFE14D", glow_strength=5.0, seed=44, ao_dist=0.12)
    m.preview_dir = (0.7, -1.0, 1.3)
    m.bone("root", (0, 0, 0))
    m.bone("body", B(0, 0, 0), "root")
    m.bone("neck1", B(0, -0.3, 0.06), "body")
    m.bone("neck2", B(0, -0.52, 0.24), "neck1")
    m.bone("head", B(0, -0.68, 0.37), "neck2")
    m.bone("jaw", B(0, -0.74, 0.36), "head")
    m.bone("tail1", B(0, 0.32, 0), "body")
    m.bone("tail2", B(0, 0.74, -0.03), "tail1")
    m.bone("tail3", B(0, 1.1, -0.06), "tail2")
    for s, side in SIDES:
        m.bone(f"wing_{side}", B(s * 0.15, -0.08, 0.12), "body")
        m.bone(f"wingfore_{side}", B(s * 0.6, 0.0, 0.2), f"wing_{side}")
        m.bone(f"thigh_{side}", B(s * 0.14, 0.12, -0.12), "body")
        m.bone(f"shin_{side}", B(s * 0.16, 0.24, -0.3), f"thigh_{side}")

    # body with belly plates and back spikes
    m.ball("body", "scale", B(0, 0, 0), (0.44, 0.86, 0.44), sub=2, jitter=0.006)
    m.ball("body", "scale3", B(0, 0.02, 0.06), (0.34, 0.7, 0.34), sub=2)
    m.ball("body", "belly2", B(0, -0.02, -0.07), (0.36, 0.72, 0.3), sub=2)
    for i in range(6):
        y = -0.3 + 0.12 * i
        t = y / 0.43
        w = math.sqrt(max(0.0, 1 - t * t))
        ang = math.degrees(math.atan(0.22 * (y / 0.43 ** 2) / max(w, 0.2)))
        m.box("body", "belly", B(0, y, -0.22 * w + 0.004), (0.27 * w, 0.115, 0.035), rot=(ang, 0, 0), bevel=0.008)
    for y in (-0.22, -0.06, 0.1, 0.24):
        top = 0.22 * math.sqrt(1 - (y / 0.43) ** 2)
        m.cyl("body", "scale2", B(0, y, top + 0.045), r=0.04, r2=0, h=0.12, n=4, rot=(-30, 0, 0))

    # neck
    m.seg("neck1", "scale", B(0, -0.22, 0.02), B(0, -0.52, 0.24), 0.14, 0.105)
    m.seg("neck1", "belly", B(0, -0.245, -0.025), B(0, -0.545, 0.205), 0.1, 0.075)
    m.ball("neck2", "scale", B(0, -0.52, 0.24), 0.2)
    m.seg("neck2", "scale", B(0, -0.52, 0.24), B(0, -0.7, 0.38), 0.105, 0.09)
    m.seg("neck2", "belly", B(0, -0.545, 0.205), B(0, -0.72, 0.34), 0.075, 0.06)
    for bone, y, z in (("neck1", -0.4, 0.22), ("neck2", -0.6, 0.39)):
        m.cyl(bone, "scale2", B(0, y, z), r=0.035, r2=0, h=0.1, n=4, rot=(-40, 0, 0))

    # head + jaw
    m.box("head", "scale", B(0, -0.8, 0.43), (0.21, 0.28, 0.15), taper=0.85, bevel=0.025)
    m.box("head", "scale", B(0, -0.98, 0.41), (0.15, 0.2, 0.1), taper=0.85, bevel=0.02)
    m.box("head", "scale2", B(0, -0.88, 0.475), (0.16, 0.22, 0.035), rot=(6, 0, 0), bevel=0.01)
    m.box("head", "mouth", B(0, -0.9, 0.362), (0.13, 0.26, 0.02))
    m.box("jaw", "belly2", B(0, -0.9, 0.33), (0.15, 0.33, 0.05), taper=0.9, bevel=0.012)
    m.box("jaw", "scale", B(0, -0.88, 0.312), (0.14, 0.3, 0.03), bevel=0.008)

    for s, side in SIDES:
        m.seg("head", "horn", B(s * 0.07, -0.74, 0.48), B(s * 0.12, -0.56, 0.6), 0.035, 0.018, n=5)
        m.seg("head", "horn2", B(s * 0.12, -0.56, 0.6), B(s * 0.14, -0.44, 0.58), 0.018, 0.0, n=5)
        m.seg("head", "horn2", B(s * 0.1, -0.78, 0.38), B(s * 0.2, -0.7, 0.36), 0.022, 0, n=4)
        m.ball("head", "eye", B(s * 0.085, -0.86, 0.46), (0.028, 0.05, 0.03), glow=True)
        m.box("head", "claw", B(s * 0.035, -1.075, 0.43), (0.02, 0.01, 0.012))
        for y in (-0.92, -0.98, -1.04):
            m.cyl("head", "teeth", B(s * 0.055, y, 0.35), r=0.01, r2=0, h=0.035, n=4, rot=(180, 0, 0))
            m.cyl("jaw", "teeth", B(s * 0.05, y + 0.03, 0.36), r=0.009, r2=0, h=0.03, n=4)

        # wings: two arm bones, three fingers, four membrane panels with a scalloped edge
        S, F = f"wing_{side}", f"wingfore_{side}"
        sh_, el, wr = B(s * 0.15, -0.08, 0.12), B(s * 0.6, 0.0, 0.2), B(s * 1.05, 0.05, 0.22)
        t1, t2, t3 = B(s * 1.6, 0.28, 0.22), B(s * 1.38, 0.65, 0.15), B(s * 1.0, 0.78, 0.1)
        m.seg(S, "scale2", sh_, el, 0.06, 0.042, n=6)
        m.ball(F, "scale2", el, 0.09)
        m.seg(F, "scale2", el, wr, 0.042, 0.03, n=6)
        m.ball(F, "scale2", wr, 0.065)
        m.seg(F, "horn", wr, B(s * 1.1, -0.07, 0.25), 0.025, 0, n=4)
        for t in (t1, t2, t3):
            m.seg(F, "scale2", wr, t, 0.022, 0.008, n=5)
        m.slab(S, "wing2", [sh_, el, B(s * 0.62, 0.6, 0.1), B(s * 0.4, 0.5, 0.08), B(s * 0.14, 0.42, 0.06)], 0.016)
        m.slab(F, "wing", [el, wr, t3, B(s * 0.8, 0.66, 0.08), B(s * 0.62, 0.6, 0.1)], 0.016)
        m.slab(F, "wing2", [wr, t2, B(s * 1.165, 0.55, 0.15), t3], 0.016)
        m.slab(F, "wing", [wr, t1, B(s * 1.38, 0.36, 0.19), t2], 0.016)

        # tucked legs with talons
        th, shn = f"thigh_{side}", f"shin_{side}"
        m.seg(th, "scale", B(s * 0.14, 0.12, -0.12), B(s * 0.16, 0.24, -0.3), 0.085, 0.06)
        m.seg(shn, "scale2", B(s * 0.16, 0.24, -0.3), B(s * 0.16, 0.36, -0.4), 0.055, 0.04, n=6)
        for dx in (-0.03, 0.0, 0.03):
            m.seg(shn, "claw", B(s * 0.16 + dx, 0.36, -0.4), B(s * 0.16 + dx * 1.5, 0.42, -0.48), 0.016, 0, n=4)

    # tail with spikes and a spade tip
    m.seg("tail1", "scale", B(0, 0.3, -0.005), B(0, 0.74, -0.03), 0.14, 0.1)
    m.seg("tail1", "belly2", B(0, 0.3, -0.05), B(0, 0.74, -0.065), 0.1, 0.07)
    m.ball("tail2", "scale", B(0, 0.74, -0.03), 0.2)
    m.seg("tail2", "scale", B(0, 0.74, -0.03), B(0, 1.1, -0.06), 0.1, 0.065)
    m.ball("tail3", "scale", B(0, 1.1, -0.06), 0.13)
    m.seg("tail3", "scale", B(0, 1.1, -0.06), B(0, 1.42, -0.075), 0.065, 0.025)
    m.slab("tail3", "scale2", [B(0, 1.36, -0.077), B(0.14, 1.45, -0.077), B(0.05, 1.5, -0.077), B(0, 1.66, -0.077),
                               B(-0.05, 1.5, -0.077), B(-0.14, 1.45, -0.077)], 0.022)
    for bone, y, z, h in (("tail1", 0.45, 0.13, 0.1), ("tail1", 0.62, 0.11, 0.09), ("tail2", 0.84, 0.07, 0.08),
                          ("tail2", 1.0, 0.04, 0.065), ("tail3", 1.2, 0.0, 0.05)):
        m.cyl(bone, "scale2", B(0, y, z), r=h * 0.35, r2=0, h=h, n=4, rot=(-35, 0, 0))
    m.build()

    a = Anim(m, "Fly", loop=True)
    for f, flap, lift in ((0, 35, 0.0), (5, 5, 0.06), (10, -40, 0.12), (15, -5, 0.06), (20, 35, 0.0)):
        a.pose(f, body=dict(loc=(0, 0, -lift), pitch=-3 + lift * 25),
               neck1=dict(pitch=-flap * 0.08), neck2=dict(pitch=-flap * 0.06), head=dict(pitch=flap * 0.12),
               tail1=dict(yaw=flap * 0.12, pitch=-flap * 0.06), tail2=dict(yaw=flap * 0.18),
               tail3=dict(yaw=flap * 0.25),
               wing_L=dict(side=-flap), wing_R=dict(side=flap),
               wingfore_L=dict(side=-flap * 0.6), wingfore_R=dict(side=flap * 0.6),
               thigh_L=dict(pitch=20), thigh_R=dict(pitch=20), shin_L=dict(pitch=15), shin_R=dict(pitch=15))
    a.done()

    a = Anim(m, "Hit")
    a.pose(0)
    a.pose(3, body=dict(loc=(0, 0.12, 0.05), pitch=-15, side=8), neck1=dict(pitch=-15), neck2=dict(pitch=-10),
           head=dict(pitch=-10), jaw=dict(pitch=30), wing_L=dict(side=-40), wing_R=dict(side=40),
           tail1=dict(pitch=15), tail2=dict(pitch=10))
    a.pose(10)
    a.done()

    a = Anim(m, "Die")
    a.pose(0)
    a.pose(8, body=dict(pitch=-25, side=20, loc=(0, 0, 0.1)), neck1=dict(pitch=-30), head=dict(pitch=-20),
           jaw=dict(pitch=35), wing_L=dict(side=-70), wing_R=dict(side=70))
    fallen = dict(root=dict(loc=(0, 0, -Z + 0.22)), body=dict(pitch=10, side=75), neck1=dict(pitch=20, yaw=20),
                  neck2=dict(pitch=10, yaw=10), head=dict(pitch=20), jaw=dict(pitch=25),
                  tail1=dict(yaw=30), tail2=dict(yaw=30), tail3=dict(yaw=20),
                  wing_L=dict(side=60, yaw=-20), wing_R=dict(side=-10, yaw=20), wingfore_L=dict(side=40))
    a.pose(26, **fallen)
    a.pose(36, **dict(fallen, root=dict(loc=(0, 0, -Z + 0.18)), body=dict(pitch=10, side=82)))
    a.done()
    return m


# ------------------------------------------------------------------------------------
def necromancer():
    """Boss: large hovering necromancer (~3 m): skull staff, spellbook, orbiting soul crystals."""
    m = Model("Necromancer", dict(
        robe="#2E2440", robe2="#231B32", robe3="#3B2E52", trim="#5B3F8C", trim2="#7A5BB0", hood="#0E0B13",
        bone="#D8D2BF", bone2="#A9A28C", gold="#C9A23A", gold2="#8F7027", wood="#3B2A1E", book="#4A2E22",
        page="#E6DCC0", magic="#59FF7A"),
        glow_color="#59FF7A", glow_strength=6.0, metal=("gold", "gold2"), seed=55)
    m.bone("root", (0, 0, 0))
    m.bone("hips", (0, 0, 1.0), "root")
    m.bone("robe", (0, 0, 0.95), "hips")
    m.bone("chest", (0, 0, 1.35), "hips")
    m.bone("neck", (0, -0.03, 2.18), "chest")
    m.bone("head", (0, -0.05, 2.28), "neck")
    m.bone("orbit", (0, 0, 0.55), "root")
    # both forearms bent forward: the right hand holds the staff in front, the left one an orb
    arm_dir = dict(L=_dir(0.04, -0.9, -0.4), R=_dir(-0.03, -0.97, -0.24))
    wrists = {}
    for s, side in SIDES:
        wrists[side] = Vector((s * 0.58, -0.03, 1.7)) + arm_dir[side] * (0.28 if s > 0 else 0.3)
        m.bone(f"upperarm_{side}", (s * 0.48, 0, 2.06), "chest")
        m.bone(f"forearm_{side}", (s * 0.58, -0.03, 1.7), f"upperarm_{side}")
        m.bone(f"hand_{side}", wrists[side], f"forearm_{side}")

    # lower robe with a rune panel and a tattered hem
    m.cyl("robe", "robe", (0, 0, 0.68), r=0.64, r2=0.42, h=1.1, n=10, jitter=0.01)
    m.cyl("robe", "trim", (0, 0, 0.16), r=0.66, r2=0.62, h=0.1, n=10)
    for i in range(10):
        a = math.radians(i * 36 + 18)
        m.cyl("robe", "robe2", (math.cos(a) * 0.56, math.sin(a) * 0.56, 0.07), r=0.13, r2=0, h=0.2, n=4,
              rot=(180, 0, 0))

    def robe_r(z):
        return 0.64 - 0.22 * (z - 0.13) / 1.1

    m.slab("robe", "trim2", [(-0.17, -robe_r(0.22) - 0.008, 0.22), (0.17, -robe_r(0.22) - 0.008, 0.22),
                             (0.11, -robe_r(1.15) - 0.008, 1.15), (-0.11, -robe_r(1.15) - 0.008, 1.15)], 0.03)
    m.slab("robe", "magic", [(0, -robe_r(0.5) - 0.024, 0.5), (0.05, -robe_r(0.6) - 0.024, 0.6),
                             (0, -robe_r(0.7) - 0.024, 0.7), (-0.05, -robe_r(0.6) - 0.024, 0.6)], 0.01, glow=True)

    # belt: skull buckle, spellbook, potion vials
    m.cyl("hips", "gold2", (0, 0, 1.27), r=0.445, h=0.07, n=10)
    m.ball("hips", "bone", (0, -0.45, 1.27), (0.13, 0.1, 0.13))
    m.box("hips", "bone2", (0, -0.47, 1.22), (0.08, 0.06, 0.04), bevel=0.008)
    for s in (1, -1):
        m.box("hips", "hood", (s * 0.03, -0.5, 1.285), (0.03, 0.01, 0.025))
    m.box("hips", "book", (0.4, -0.28, 1.12), (0.09, 0.22, 0.27), rot=(0, 0, -35), bevel=0.01)
    m.box("hips", "page", (0.4, -0.28, 1.12), (0.07, 0.226, 0.25), rot=(0, 0, -35))
    m.box("hips", "gold", (0.428, -0.3, 1.12), (0.04, 0.06, 0.08), rot=(0, 0, -35), bevel=0.005)
    for x, y, z in ((-0.385, -0.27, 1.15), (-0.43, -0.16, 1.13)):
        m.cyl("hips", "magic", (x, y, z), r=0.035, h=0.1, n=6, glow=True)
        m.cyl("hips", "wood", (x, y, z + 0.065), r=0.02, h=0.03, n=6)

    # torso: robe, V trim, amulet, mantle, collar spikes, shoulder skulls
    m.cyl("chest", "robe", (0, 0, 1.67), r=0.42, r2=0.54, h=0.8, n=10, jitter=0.008)

    def chest_y(x, z):
        r = 0.42 + 0.12 * (z - 1.27) / 0.8
        return -math.sqrt(max(r * r - x * x, 0.0)) - 0.01

    for s in (1, -1):
        m.slab("chest", "trim2", [(s * 0.2, chest_y(0.2, 2.0), 2.0), (s * 0.28, chest_y(0.28, 2.0), 2.0),
                                  (s * 0.06, chest_y(0.06, 1.3), 1.3), (0.0, chest_y(0.0, 1.3), 1.3)], 0.025)
    m.ring("chest", "gold", (0, -0.515, 1.85), 0.07, 0.015, n=10, rot=(90, 0, 0))
    m.ball("chest", "magic", (0, -0.525, 1.85), 0.1, glow=True)
    for s in (1, -1):
        m.seg("chest", "gold2", (s * 0.18, -0.5, 2.0), (s * 0.05, -0.52, 1.92), 0.01, 0.01, n=4)
    m.cyl("chest", "trim", (0, 0.02, 2.06), r=0.66, r2=0.3, h=0.26, n=10)
    m.cyl("chest", "gold2", (0, 0.02, 1.94), r=0.665, h=0.03, n=10)
    for deg in (-50, -25, 0, 25, 50):
        a = math.radians(deg)
        m.seg("chest", "robe3", (math.sin(a) * 0.22, 0.1 + math.cos(a) * 0.1, 2.12),
              (math.sin(a) * 0.42, 0.22 + math.cos(a) * 0.16, 2.62), 0.07, 0, n=4)
    for s in (1, -1):
        m.ball("chest", "bone", (s * 0.5, 0, 2.12), (0.24, 0.26, 0.22))
        m.box("chest", "bone2", (s * 0.5, -0.1, 2.05), (0.14, 0.08, 0.06), bevel=0.01)
        for dx in (-0.045, 0.045):
            m.box("chest", "hood", (s * 0.5 + dx, -0.12, 2.14), (0.045, 0.02, 0.04))
        m.seg("chest", "bone", (s * 0.52, 0.02, 2.2), (s * 0.62, 0.05, 2.38), 0.04, 0, n=4)

    # head: hood, skull face, glowing eyes
    m.ball("head", "robe", (0, 0, 2.42), (0.52, 0.52, 0.58), sub=2, jitter=0.005)
    m.seg("head", "robe", (0, 0.06, 2.62), (0, 0.32, 2.86), 0.15, 0, n=6)
    m.ring("head", "trim", (0, -0.2, 2.39), 0.19, 0.03, n=12, rot=(90, 0, 0), squash=(1, 1.2))
    m.ball("head", "hood", (0, -0.14, 2.39), (0.36, 0.3, 0.42), sub=2)
    m.ball("head", "bone", (0, -0.2, 2.37), (0.24, 0.2, 0.27), sub=2)
    m.box("head", "bone2", (0, -0.27, 2.26), (0.15, 0.09, 0.07), bevel=0.015)
    m.box("head", "bone", (0, -0.315, 2.275), (0.12, 0.012, 0.03))
    m.box("head", "hood", (0, -0.3, 2.33), (0.025, 0.01, 0.035))
    for s in (1, -1):
        m.box("head", "hood", (s * 0.055, -0.29, 2.4), (0.065, 0.02, 0.05), rot=(0, 0, s * -10), bevel=0.005)
        m.ball("head", "magic", (s * 0.055, -0.3, 2.4), (0.035, 0.012, 0.025), glow=True)

    # arms: flared sleeves, bony hands
    for s, side in SIDES:
        P = _mirror(s)
        ua, fa, hand = f"upperarm_{side}", f"forearm_{side}", f"hand_{side}"
        m.seg(ua, "robe", P(0.48, 0, 2.06), P(0.58, -0.03, 1.7), 0.13, 0.14)
        elbow, d, wrist = Vector(P(0.58, -0.03, 1.7)), arm_dir[side], wrists[side]
        m.ball(fa, "robe", elbow, 0.27)
        m.seg(fa, "robe", elbow, wrist, 0.14, 0.22)
        m.seg(fa, "trim", wrist - d * 0.015, wrist + d * 0.015, 0.225, 0.227)
        u = d.cross(Vector((0, 0, 1))).normalized()
        v = d.cross(u)
        for k in range(4):  # tattered cuff
            a = math.radians(k * 90 + 45)
            m.cyl(fa, "robe2", wrist + (u * math.cos(a) + v * math.sin(a)) * 0.17 - Vector((0, 0, 0.05)), r=0.06,
                  r2=0, h=0.12, n=4, rot=(180, 0, 0))
        palm = wrist + d * 0.07
        m.box(hand, "bone", palm, (0.08, 0.09, 0.08), rot=_along(d), bevel=0.01)
        if s > 0:  # open palm turned up under the orb
            for dx in (-0.025, 0.0, 0.025):
                m.seg(hand, "bone2", palm + d * 0.03 + Vector((dx, 0, 0)), palm + d * 0.08 + Vector((dx * 1.3, 0, 0.04)),
                      0.012, 0.008, n=5)
        else:  # fingers around the staff
            m.box(hand, "bone2", palm + Vector((0.035, 0, 0)), (0.03, 0.075, 0.07), rot=_along(d), bevel=0.008)
    m.ball("hand_L", "magic", wrists["L"] + arm_dir["L"] * 0.1 + Vector((0, 0, 0.17)), 0.15, glow=True)

    # skull staff with a soul crystal, held upright in front of the right hand
    x, y = (wrists["R"] + arm_dir["R"] * 0.08).xy
    m.seg("hand_R", "wood", (x, y, 0.25), (x, y, 2.58), 0.04, 0.034, n=6)
    for z in (1.0, 1.7, 2.3):
        m.seg("hand_R", "bone2", (x, y, z), (x, y, z + 0.04), 0.05, 0.05, n=6)
    for z in (2.45, 2.52):
        m.ball("hand_R", "bone", (x, y, z), (0.09, 0.09, 0.05))
    m.ball("hand_R", "bone", (x, y, 2.68), (0.2, 0.22, 0.2))
    m.box("hand_R", "bone2", (x, y - 0.07, 2.6), (0.12, 0.1, 0.05), bevel=0.008)
    for dx in (-0.045, 0.045):
        m.ball("hand_R", "magic", (x + dx, y - 0.1, 2.7), (0.035, 0.012, 0.03), glow=True)
    for ang in (45, 135, 225, 315):
        c, sn = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        m.seg("hand_R", "gold2", (x + c * 0.06, y + sn * 0.06, 2.74), (x + c * 0.1, y + sn * 0.1, 2.95),
              0.018, 0.006, n=4)
    m.cyl("hand_R", "magic", (x, y, 3.0), r=0.085, r2=0, h=0.16, n=4, glow=True)
    m.cyl("hand_R", "magic", (x, y, 2.88), r=0, r2=0.085, h=0.08, n=4, glow=True)

    # three soul crystals orbiting the hem
    for ang in (0, 120, 240):
        c, sn = math.cos(math.radians(ang)) * 0.9, math.sin(math.radians(ang)) * 0.9
        m.cyl("orbit", "magic", (c, sn, 0.6), r=0.05, r2=0, h=0.1, n=4, glow=True)
        m.cyl("orbit", "magic", (c, sn, 0.52), r=0, r2=0.05, h=0.06, n=4, glow=True)
    m.build()

    def glide(k, ph, up, p):
        p["forearm_L"] = dict(pitch=-3 * up)
        p["forearm_R"] = dict(pitch=-3 * up)
        p["root"] = dict(loc=(0, 0, 0.06 * up))
        p["robe"] = dict(pitch=-5 * (1 - up), side=3 * ph)
        p["orbit"] = dict(yaw=90 * k, loc=(0, 0, 0.04 * up))
        p["hips"] = dict(yaw=-2 * ph)

    biped_walk(m, frames=32, stride=0, arm=6, elbow=10, bob=0.0, lean=3, sway=0, shift=0, twist=3,
               linear=("orbit",), extra=glide)
    # the last Walk key wraps back to 0 deg -> make it a full turn so the crystals keep spinning
    act = m.arm.animation_data.nla_tracks["Walk"].strips[0].action
    for fc in _fcurves(act):
        if fc.data_path == 'pose.bones["orbit"].rotation_euler' and fc.array_index == 1:
            fc.keyframe_points[-1].co.y = math.radians(360)
            fc.update()

    biped_hit(m, push=0.06)

    a = Anim(m, "Die")
    a.pose(0)
    a.pose(10, chest=dict(pitch=-20), head=dict(pitch=-30), upperarm_L=dict(pitch=-60, side=-40),
           upperarm_R=dict(pitch=-60, side=40), orbit=dict(loc=(0, 0, 0.3)))
    a.pose(40, root=dict(loc=(0, 0, -1.1), yaw=90, scale=0.9), chest=dict(pitch=30), head=dict(pitch=35),
           robe=dict(scale=0.7), upperarm_L=dict(pitch=-20, side=-70), upperarm_R=dict(pitch=-20, side=70),
           orbit=dict(loc=(0, 0, -0.6), scale=0.01))
    a.done()

    a = Anim(m, "Cast", linear=("orbit",))  # summons minions / casts a spell
    a.pose(0)
    a.pose(10, chest=dict(pitch=-10), head=dict(pitch=-15), upperarm_L=dict(pitch=-150, side=-20),
           forearm_L=dict(pitch=-20), upperarm_R=dict(pitch=-60, side=10), orbit=dict(yaw=180, loc=(0, 0, 0.4)))
    a.pose(18, chest=dict(pitch=-12), head=dict(pitch=-18), upperarm_L=dict(pitch=-160, side=-25),
           forearm_L=dict(pitch=-10), upperarm_R=dict(pitch=-70, side=10), orbit=dict(yaw=360, loc=(0, 0, 0.6)))
    a.pose(26, chest=dict(pitch=15), head=dict(pitch=10), upperarm_L=dict(pitch=-70, side=-10),
           upperarm_R=dict(pitch=-20), orbit=dict(yaw=540, loc=(0, 0, 0.2)))
    a.pose(40, orbit=dict(yaw=720))
    a.done()
    return m


# ------------------------------------------------------------------------------------
def skeleton_knight():
    """Boss: armoured skeleton knight (~2.6 m): greatsword, kite shield, two-part tattered cape."""
    m = Model("SkeletonKnight", dict(
        bone="#E3DCC6", bone2="#A79F86", armor="#3E434A", armor2="#2E3238", edge="#8A929B", cape="#6E1E1E",
        cape2="#521616", gold="#B8902E", blade="#C9D0D6", blade2="#8E979F", dark="#15171A", leather="#3B2A20",
        soul="#4DE1FF"),
        glow_color="#4DE1FF", glow_strength=6.0, metal=("armor", "armor2", "edge", "gold", "blade", "blade2"),
        seed=66)
    # both forearms forward: sword at the ready on the right, shield in front on the left
    arm_dir = dict(L=_dir(0.05, -0.85, -0.52), R=_dir(-0.05, -0.82, -0.57))
    wrists = {side: Vector((s * 0.5, 0, 1.5)) + arm_dir[side] * 0.34 for s, side in SIDES}
    biped_rig(m, hips=(0, 0, 1.1), chest=(0, 0, 1.32), neck=(0, -0.02, 2.02), head=(0, -0.03, 2.12),
              shoulder=(0.42, 0, 1.96), elbow=(0.5, 0, 1.5), wrist=(0.52, -0.03, 1.14),
              hip=(0.18, 0, 1.06), knee=(0.19, -0.01, 0.62), ankle=(0.19, 0.01, 0.15),
              wrist_l=wrists["L"], wrist_r=wrists["R"])
    m.bone("cape", (0, 0.24, 2.0), "chest")
    m.bone("cape2", (0, 0.3, 1.28), "cape")

    for s, side in SIDES:
        P = _mirror(s)
        th, sh, ft = f"thigh_{side}", f"shin_{side}", f"foot_{side}"
        ua, fa, hand = f"upperarm_{side}", f"forearm_{side}", f"hand_{side}"
        m.seg(th, "bone", P(0.18, 0, 1.06), P(0.19, -0.01, 0.66), 0.045, 0.04, n=6)
        m.box(th, "armor", P(0.185, -0.055, 0.86), (0.15, 0.05, 0.3), taper=1.15, bevel=0.012)
        m.box(th, "edge", P(0.185, -0.083, 0.86), (0.02, 0.012, 0.28))
        m.ball(sh, "armor", P(0.19, -0.03, 0.62), 0.15)
        m.cyl(sh, "edge", P(0.19, -0.1, 0.62), r=0.03, r2=0, h=0.08, n=4, rot=(90, 0, 0))
        m.seg(sh, "armor", P(0.19, -0.01, 0.6), P(0.19, 0.01, 0.2), 0.085, 0.095)
        m.box(sh, "edge", P(0.19, -0.1, 0.4), (0.025, 0.02, 0.36))
        m.seg(sh, "gold", P(0.19, 0.0, 0.27), P(0.19, 0.0, 0.24), 0.1, 0.1)
        m.box(ft, "armor", P(0.19, -0.06, 0.07), (0.18, 0.34, 0.14), taper=0.8, bevel=0.02)
        m.box(ft, "armor2", P(0.19, -0.2, 0.05), (0.15, 0.1, 0.09), taper=0.8, bevel=0.015)

        # layered pauldron with spikes
        for k, (dz, sz) in enumerate(((0.06, 1.0), (-0.03, 0.85), (-0.11, 0.7))):
            m.box(ua, "armor" if k % 2 == 0 else "armor2", P(0.45 + 0.03 * k, 0, 1.98 + dz),
                  (0.3 * sz, 0.36 * sz, 0.09), rot=(0, -s * (25 + 10 * k), 0), bevel=0.015)
        for yy in (-0.07, 0.07):
            m.seg(ua, "edge", P(0.44, yy, 2.05), P(0.5, yy - 0.01, 2.25), 0.035, 0, n=4)
        m.seg(ua, "bone", P(0.42, 0, 1.92), P(0.5, 0, 1.52), 0.045, 0.04, n=6)
        elbow, d, wrist = Vector(P(0.5, 0, 1.5)), arm_dir[side], wrists[side]
        m.ball(fa, "armor", elbow, 0.13)
        m.seg(fa, "edge", elbow - d * 0.05, elbow - d * 0.13, 0.025, 0, n=4)
        m.seg(fa, "armor", elbow + d * 0.02, wrist, 0.08, 0.07)
        m.seg(fa, "gold", wrist - d * 0.06, wrist - d * 0.03, 0.075, 0.075)
        gauntlet = wrist + d * 0.07
        m.box(hand, "armor", gauntlet, (0.13, 0.15, 0.13), rot=_along(d), bevel=0.02)
        m.box(hand, "armor2", gauntlet + Vector((-s * 0.06, 0, 0)), (0.04, 0.12, 0.1), rot=_along(d), bevel=0.01)

        # head details
        m.box("head", "dark", P(0.065, -0.185, 2.28), (0.08, 0.03, 0.06), rot=(0, 0, s * -12), bevel=0.01)
        m.ball("head", "soul", P(0.065, -0.19, 2.28), 0.055, glow=True)
        m.ball("head", "bone", P(0.11, -0.15, 2.22), (0.06, 0.08, 0.05))
        m.seg("head", "bone2", P(0.17, -0.02, 2.42), P(0.3, 0.0, 2.55), 0.05, 0.03, n=6)
        m.seg("head", "bone2", P(0.3, 0.0, 2.55), P(0.32, -0.04, 2.72), 0.03, 0, n=6)
        m.ball("chest", "gold", P(0.3, 0.2, 2.02), 0.06)  # cape clasp

    # pelvis, faulds, tabard
    m.box("hips", "bone", (0, 0, 1.1), (0.34, 0.18, 0.12), bevel=0.02)
    m.cyl("hips", "armor", (0, 0, 1.02), r=0.37, r2=0.31, h=0.26, n=10)
    m.cyl("hips", "edge", (0, 0, 0.9), r=0.375, r2=0.37, h=0.03, n=10)
    m.cyl("hips", "gold", (0, 0, 1.14), r=0.315, h=0.03, n=10)

    def tabard_y(z):
        return -0.33 - 0.06 * min(max((1.12 - z) / 0.22, 0.0), 1.0) - 0.012

    m.slab("hips", "cape", [(x, tabard_y(z), z) for x, z in rag(-0.13, 0.13, 1.12, 0.55, teeth=3, depth=0.06)],
           0.025)
    m.box("hips", "gold", (0, tabard_y(0.8) - 0.012, 0.8), (0.07, 0.01, 0.1), bevel=0.004)

    # exposed spine and ribs between the faulds and the breastplate
    m.seg("chest", "bone2", (0, 0.06, 1.12), (0, 0.06, 1.44), 0.045, 0.045, n=6)
    for z in (1.2, 1.27, 1.34):
        m.ball("chest", "bone", (0, 0.07, z), (0.08, 0.07, 0.045))
    for i, z in enumerate((1.25, 1.33, 1.41)):
        m.ring("chest", "bone", (0, 0.0, z), 0.15 + 0.03 * i, 0.016, n=10, arc=290, squash=(1, 0.75))

    # breastplate
    m.box("chest", "armor", (0, 0, 1.72), (0.62, 0.4, 0.52), taper=1.2, bevel=0.03)
    m.box("chest", "edge", (0, -0.215, 1.74), (0.06, 0.04, 0.48), taper=1.1, bevel=0.01)
    m.box("chest", "gold", (0, 0, 1.47), (0.64, 0.42, 0.04), bevel=0.008)
    m.box("chest", "gold", (0, 0, 1.97), (0.76, 0.49, 0.035), bevel=0.008)
    m.ring("chest", "gold", (0, -0.235, 1.8), 0.055, 0.015, n=10, rot=(90, 0, 0))
    m.ball("chest", "soul", (0, -0.24, 1.8), (0.08, 0.04, 0.08), glow=True)
    for x, y, z in ((-0.22, -0.215, 1.55), (0.22, -0.215, 1.55), (-0.27, -0.235, 1.88), (0.27, -0.235, 1.88)):
        m.ball("chest", "edge", (x, y, z), 0.03)
    m.cyl("chest", "armor", (0, -0.01, 2.02), r=0.2, r2=0.16, h=0.12, n=10)

    # skull + helmet
    m.ball("head", "bone", (0, -0.04, 2.27), (0.28, 0.31, 0.3), sub=2, jitter=0.003)
    m.box("head", "bone2", (0, -0.13, 2.13), (0.2, 0.14, 0.08), taper=1.1, bevel=0.015)
    m.box("head", "bone", (0, -0.2, 2.17), (0.14, 0.02, 0.035), bevel=0.004)
    m.box("head", "dark", (0, -0.203, 2.152), (0.15, 0.02, 0.012))
    m.box("head", "dark", (0, -0.19, 2.22), (0.03, 0.02, 0.04), taper=0.5)
    m.cyl("head", "armor", (0, -0.02, 2.39), r=0.19, r2=0.17, h=0.16, n=10)
    m.cyl("head", "gold", (0, -0.02, 2.33), r=0.195, h=0.03, n=10)
    m.box("head", "armor", (0, -0.21, 2.33), (0.04, 0.03, 0.14), bevel=0.006)
    for deg in (-60, -30, 0, 30, 60):
        a = math.radians(deg)
        m.cyl("head", "gold", (math.sin(a) * 0.17, -0.02 - math.cos(a) * 0.17, 2.5), r=0.022, r2=0, h=0.07, n=4)

    # cape in two parts so it can sway
    m.slab("cape", "cape", [(-0.36, 0.23, 2.02), (0.36, 0.23, 2.02), (0.42, 0.3, 1.28), (-0.42, 0.3, 1.28)], 0.03)
    m.slab("cape2", "cape2", [(x, 0.3 + (1.3 - z) / 0.85 * 0.06, z)
                              for x, z in rag(-0.42, 0.42, 1.3, 0.45, teeth=4, depth=0.1)], 0.03)

    # greatsword: grip through the gauntlet, blade forward and up, edges up/down, flat sides facing outward
    hilt = wrists["R"] + arm_dir["R"] * 0.07
    c = (_grip(arm_dir["R"]) * 0.866 + arm_dir["R"] * 0.5).normalized()
    X = Vector((0, 0, 1))  # blade width direction (the crossguard runs along it too)
    X = (X - c * X.dot(c)).normalized()

    def at(t):
        return hilt + c * t

    blade = [(0.12, 0.065), (0.9, 0.055), (1.05, 0.0)]
    pts = [at(t) + X * w for t, w in blade] + [at(t) - X * w for t, w in reversed(blade[:-1])]
    m.slab("hand_R", "blade", pts, 0.03)
    m.slab("hand_R", "blade2", [at(0.15) + X * 0.015, at(0.85) + X * 0.012, at(0.85) - X * 0.012,
                                at(0.15) - X * 0.015], 0.036)
    m.seg("hand_R", "gold", at(0.1) - X * 0.16, at(0.1) + X * 0.16, 0.03, n=6)
    for sx in (1, -1):
        m.seg("hand_R", "gold", at(0.1) + X * sx * 0.15, at(0.16) + X * sx * 0.21, 0.025, 0, n=4)
    m.seg("hand_R", "leather", at(-0.17), at(0.08), 0.025, 0.025, n=6)
    m.ball("hand_R", "gold", at(-0.19), 0.07)
    m.ball("hand_R", "soul", at(-0.19) - c * 0.04, 0.03, glow=True)

    # kite shield strapped to the left forearm, facing forward and slightly outward
    n = Vector((math.sin(math.radians(20)), -math.cos(math.radians(20)), 0))
    C = wrists["L"] + arm_dir["L"] * 0.07 + n * 0.1
    kite = [(-0.26, 0.32), (0.26, 0.32), (0.26, 0.0), (0, -0.42), (-0.26, 0.0)]
    rim = [(-0.29, 0.35), (0.29, 0.35), (0.29, -0.01), (0, -0.47), (-0.29, -0.01)]
    m.prism("forearm_L", "edge", rim, 0.04, loc=C - n * 0.012, rot=(0, 0, 20))
    m.prism("forearm_L", "armor", kite, 0.05, loc=C, rot=(0, 0, 20))
    for ang in (40, -40):
        m.box("forearm_L", "bone2", C + n * 0.03, (0.045, 0.02, 0.42), rot=rots((0, ang, 0), (0, 0, 20)),
              bevel=0.006)
    m.ring("forearm_L", "gold", C + n * 0.035, 0.07, 0.018, n=10, rot=(90, 0, 20))
    m.ball("forearm_L", "soul", C + n * 0.04, (0.1, 0.04, 0.1), rot=(0, 0, 20), glow=True)
    m.build()

    def stomp(k, ph, up, p):
        p["cape"] = dict(pitch=-5 - 4 * up)
        p["cape2"] = dict(pitch=-6 * up)
        p["upperarm_R"]["pitch"] *= 0.4
        p["upperarm_L"]["pitch"] *= 0.3
        p["forearm_L"] = dict(pitch=-3 * up)
        p["forearm_R"] = dict(pitch=-4 * up)

    biped_walk(m, frames=32, stride=0.85, arm=16, elbow=15, bob=0.04, lean=3, sway=3, shift=0.02, twist=4,
               extra=stomp)
    biped_hit(m, push=0.06, extra=lambda p: p.update(cape=dict(pitch=-15), cape2=dict(pitch=-10)))
    biped_die(m, depth=0.22, frames=40, push=0.06,
              extra=lambda p: p.update(cape=dict(pitch=-30), cape2=dict(pitch=-20)))
    return m


MOBS = dict(goblin=goblin, orc=orc, troll=troll, wyvern=wyvern,
            necromancer=necromancer, skeleton_knight=skeleton_knight)
