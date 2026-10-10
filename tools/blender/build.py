"""Build models headlessly:
    Blender -b --factory-startup -P tools/blender/build.py -- [name | category ...] [--no-preview]
Categories: enemies, towers, projectiles, tiles, structures, props (default: everything).
Writes models/<category>/<name>.glb, art/blend/<name>.blend and art/previews/<name>.png.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402

import lowpoly  # noqa: E402
import env  # noqa: E402
import mobs  # noqa: E402
import towers  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CATALOG = {}
for category, builders in (("enemies", mobs.MOBS), ("towers", towers.TOWERS), ("projectiles", towers.PROJECTILES),
                           ("tiles", env.TILES), ("structures", env.STRUCTURES), ("props", env.PROPS)):
    for name, fn in builders.items():
        CATALOG[name] = (category, fn)

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
preview = "--no-preview" not in args
names = []
for a in (a for a in args if not a.startswith("-")):
    names += [n for n, (c, _) in CATALOG.items() if c == a] or [a]
names = names or list(CATALOG)

for name in names:
    category, fn = CATALOG[name]
    lowpoly.clear_scene()
    model = fn()
    os.makedirs(os.path.join(ROOT, "models", category), exist_ok=True)
    lowpoly.export_glb(model, os.path.join(ROOT, "models", category, f"{name}.glb"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "art", "blend", f"{name}.blend"))
    anims = [t.name for t in model.arm.animation_data.nla_tracks] if model.arm else []
    if preview:
        lowpoly.render_preview(model, os.path.join(ROOT, "art", "previews", f"{name}.png"),
                               anims[0] if anims else None, frame=4)
    tris = sum(len(p.vertices) - 2 for p in model.obj.data.polygons)
    print(f"[build] {name}: {tris} tris, height {model.height():.2f} m, anims {anims}")
