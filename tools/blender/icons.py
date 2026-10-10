"""Render UI icons (transparent PNG) from the game models:
    Blender -b --factory-startup -P tools/blender/icons.py
Writes assets/ui/icons/<name>.png.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lowpoly  # noqa: E402
import mobs  # noqa: E402
import towers  # noqa: E402
from lowpoly import Model  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "assets", "ui", "icons")


def _icon_model(name, pal):
    m = Model(name, pal, glow_color="#FFFFFF", glow_strength=0.0, rig=False, ao=0.2)
    m.bone("root", (0, 0, 0))
    m.preview_dir = (0.25, -1.0, 0.25)
    return m


def coin():
    m = _icon_model("Coin", dict(gold="#E8B83A", gold2="#B8862A"))
    m.cyl("root", "gold", (0, 0, 0), r=0.5, h=0.12, n=20, rot=(90, 0, 0))
    m.ring("root", "gold2", (0, -0.06, 0), 0.42, 0.03, n=20, rot=(90, 0, 0))
    m.prism("root", "gold2", [(0, 0.22), (0.07, 0.07), (0.22, 0.05), (0.1, -0.05), (0.14, -0.22), (0, -0.12),
                              (-0.14, -0.22), (-0.1, -0.05), (-0.22, 0.05), (-0.07, 0.07)], 0.04, loc=(0, -0.06, 0))
    m.build()
    return m


def heart():
    m = _icon_model("Heart", dict(red="#D8323C", red2="#A82028"))
    for sx in (1, -1):
        m.ball("root", "red", (sx * 0.24, 0, 0.15), (0.56, 0.4, 0.56), sub=2)
    m.cyl("root", "red2", (0, 0, -0.17), r=0.48, r2=0.0, h=0.62, n=16, rot=(180, 0, 0), squash=(1, 0.7))
    m.build()
    return m


def swords():
    m = _icon_model("Swords", dict(steel="#C9D0D6", gold="#D2A43A", leather="#5B3A22"))
    for ang in (40, -40):
        rot = (0, ang, 0)
        m.prism("root", "steel", [(-0.05, -0.25), (0.05, -0.25), (0.05, 0.37), (0, 0.47), (-0.05, 0.37)], 0.03,
                rot=rot)
        m.box("root", "gold", _rot((0, 0, -0.27), ang), (0.28, 0.05, 0.05), rot=rot)
        m.box("root", "leather", _rot((0, 0, -0.4), ang), (0.05, 0.05, 0.22), rot=rot)
        m.ball("root", "gold", _rot((0, 0, -0.53), ang), 0.08)
    m.build()
    return m


def _rot(p, ang):
    """Rotate (x, 0, z) about the Y axis exactly like Euler (0, ang, 0)."""
    a = math.radians(ang)
    x, z = p[0], p[2]
    return (x * math.cos(a) + z * math.sin(a), 0, -x * math.sin(a) + z * math.cos(a))


ITEMS = dict(
    archer=(towers.TOWERS["archer_1"], "Idle"), cannon=(towers.TOWERS["cannon_2"], "Idle"),
    mage=(towers.TOWERS["mage_2"], "Idle"), ice=(towers.TOWERS["ice_2"], "Idle"),
    ballista=(towers.TOWERS["ballista_2"], "Idle"),
    goblin=(mobs.goblin, "Walk"), orc=(mobs.orc, "Walk"), troll=(mobs.troll, "Walk"), wyvern=(mobs.wyvern, "Fly"),
    necromancer=(mobs.necromancer, "Walk"), skeleton_knight=(mobs.skeleton_knight, "Walk"),
    coin=(coin, None), heart=(heart, None), wave=(swords, None),
)

os.makedirs(OUT, exist_ok=True)
only = [a for a in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else []
for name, (fn, anim) in ITEMS.items():
    if only and name not in only:
        continue
    lowpoly.clear_scene()
    model = fn()
    lowpoly.render_preview(model, os.path.join(OUT, f"{name}.png"), anim, frame=0, res=160, transparent=True,
                           zoom=1.75 if anim else 2.2)
    print(f"[icon] {name}")
