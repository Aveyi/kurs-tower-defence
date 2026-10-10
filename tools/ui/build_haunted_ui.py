"""Nine-patch frame textures for the level 2 ("Haunted Forest") HUD:
    Blender -b --factory-startup -P tools/ui/build_haunted_ui.py
Blender is used only as a Python interpreter with numpy and an image writer.
Writes assets/ui/haunted/<name>.png. Every texture is a rounded frame drawn from a signed distance:
  outer violet glow (expand margin) | dark outline | tarnished silver band lit from above |
  dark groove | thin violet rune line (pulsed by shaders/ui_haunted_frame.gdshader) | dark fill.
Panels also get a glowing rune gem in each corner.
"""
import os

import bpy
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "assets", "ui", "haunted")


def rgb(*c):
    return np.array(c, dtype=float) / 255.0


def frame(size, radius, glow, bands, fill_top, fill_bottom, fill_alpha=0.94, gem=0.0, glow_color=rgb(120, 60, 210),
          glow_alpha=0.4, seed=1):
    """`bands`: list of (width px, colour, lit) from the outline inwards; lit bands get a top-down gradient."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size].astype(float) + 0.5
    inset = glow
    # signed distance to the rounded rectangle [inset, size - inset]; positive inside
    half = (size - 2 * inset) / 2.0
    cx = cy = size / 2.0
    qx = np.abs(x - cx) - (half - radius)
    qy = np.abs(y - cy) - (half - radius)
    outside = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - radius
    d = -outside
    v = y / size  # 0 top .. 1 bottom
    img = np.zeros((size, size, 4))
    # outer glow
    g = np.clip(-d, 0, None)
    img[..., :3] = glow_color
    img[..., 3] = np.where(d < 0, glow_alpha * np.exp(-g / max(glow * 0.45, 0.5)) * (g < glow), 0.0)
    # bands, from the outline inwards
    edge = 0.0
    for width, color, lit in bands:
        mask = (d >= edge) & (d < edge + width)
        col = color * (1.25 - 0.5 * v[..., None]) if lit else np.broadcast_to(color, (size, size, 3))
        if lit:  # bevel: the outer half of the band catches more light
            col = col * (1.1 - 0.25 * np.clip((d - edge) / width, 0, 1))[..., None]
        img[mask, :3] = col[mask]
        img[mask, 3] = 1.0
        edge += width
    inner = d >= edge
    fill = fill_top[None, None, :] * (1 - v[..., None]) + fill_bottom[None, None, :] * v[..., None]
    fill = fill + rng.uniform(-0.012, 0.012, (size, size, 1))
    img[inner, :3] = fill[inner]
    img[inner, 3] = fill_alpha
    # anti-aliased outer edge
    aa = np.clip(d + 0.5, 0, 1)
    img[..., 3] = np.where((d > -0.5) & (d < 0.5), np.maximum(img[..., 3] * aa, glow_alpha * 0.8 * (1 - aa)),
                           img[..., 3])
    if gem > 0:  # a rune gem (rhombus) sitting on the silver band in every corner
        c = inset + 6.5
        for gx in (c, size - c):
            for gy in (c, size - c):
                r = np.abs(x - gx) + np.abs(y - gy)
                outline = r < gem + 1.6
                img[outline, :3] = rgb(10, 6, 16)
                img[outline, 3] = 1.0
                core = r < gem
                shade = np.clip(1.15 - r / gem * 0.5 - (y - gy) / gem * 0.25, 0, 1.3)[..., None]
                img[core, :3] = (rgb(185, 120, 255) * shade)[core]
                spark = r < gem * 0.35
                img[spark, :3] = rgb(240, 215, 255)
    return np.clip(img, 0, 1)


def save(name, img):
    h, w = img.shape[:2]
    image = bpy.data.images.new(name, w, h, alpha=True)
    image.pixels = img[::-1].ravel()  # Blender images are stored bottom row first
    image.filepath_raw = os.path.join(OUT, f"{name}.png")
    image.file_format = "PNG"
    image.save()
    print(f"[ui] {name}: {w}x{h}")


SILVER, SILVER_DIM, DARK = rgb(128, 116, 150), rgb(84, 78, 98), rgb(9, 6, 14)
RUNE, RUNE_HOT = rgb(150, 92, 228), rgb(196, 140, 255)

os.makedirs(OUT, exist_ok=True)
# large panels: 72 px, glow 6, outline 2, silver 3.5, groove 1.5, rune line 1.5, then the fill
save("panel", frame(72, 11, 6, [(2, DARK, False), (3.5, SILVER, True), (1.5, DARK, False), (1.5, RUNE, False)],
                    rgb(26, 18, 38), rgb(11, 8, 17), gem=4.2, seed=1))
save("tooltip", frame(40, 7, 3, [(1.5, DARK, False), (2, SILVER_DIM, True), (1, RUNE, False)],
                      rgb(20, 14, 30), rgb(10, 7, 15), fill_alpha=0.97, glow_alpha=0.3, seed=2))
button = [(1.5, DARK, False), (2.5, SILVER, True), (1, DARK, False)]
save("button", frame(48, 8, 4, button, rgb(54, 40, 76), rgb(30, 22, 44), fill_alpha=1.0, glow_alpha=0.0, seed=3))
save("button_hover", frame(48, 8, 4, [(1.5, DARK, False), (2.5, RUNE_HOT, True), (1, DARK, False)],
                           rgb(74, 52, 106), rgb(42, 29, 62), fill_alpha=1.0, glow_alpha=0.55, seed=4))
save("button_pressed", frame(48, 8, 4, [(1.5, DARK, False), (2.5, RUNE, True), (1, DARK, False)],
                             rgb(22, 15, 33), rgb(38, 27, 54), fill_alpha=1.0, glow_alpha=0.35, seed=5))
save("button_disabled", frame(48, 8, 4, [(1.5, DARK, False), (2.5, SILVER_DIM * 0.8, True), (1, DARK, False)],
                              rgb(34, 31, 40), rgb(24, 22, 29), fill_alpha=0.88, glow_alpha=0.0, seed=6))
