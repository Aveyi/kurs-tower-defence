"""Writes data/levels/level_02.tres ("Haunted Forest"): layout, theme, lighting and the waves.
    python3 tools/levels/level_02.py
Waves are (bonus, [(enemy, count, interval s, delay s), ...]); edit the tables below and re-run.
The sealed east portal opens with the first wave after the ghost knight's wave.
"""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

LAYOUT = [
    "TTTTTTTTTTTTTTTTTTTTTTTT",
    "T......T.TTTTTT.TT.....T",
    "TS###.P..R.t.r..t..###sT",
    "T.TP#...t..Rt.tP.t.#...T",
    "T...#P.GGGG..R..####Pr.T",
    "T.r.#..GGGGr.tR.#.t#..TT",
    "T...#########...#P.#GGTT",
    "T.P.#..GGGG.#P.t#.R#GG.T",
    "T...#.PGGGGP#.R.#t.#.R.T",
    "TT..#..R..t.#t.r####.TTT",
    "T.R.#tr.P..t#.P..RP#T.TT",
    "T...#########.tr...#.P.T",
    "TT.T.P.rTTP.########..rT",
    "TTTT..T.TT.CCC.P.r.TTTTT",
    "TTTTTTTTTTTCCCTTTTTTTTTT",
]

START_GOLD = 350
LIVES = 20
HP_GROWTH = 0.05
HP_GROWTH_POWER = 1.25
DECOR_SEED = 13

WAVES = [
    (20, [("skeleton", 8, 1.0, 0)]),
    (25, [("skeleton", 10, 0.8, 0), ("zombie", 2, 2.5, 6)]),
    (30, [("zombie", 4, 2.0, 0), ("skeleton", 8, 0.7, 4)]),
    (35, [("gargoyle", 3, 2.2, 0), ("skeleton", 10, 0.6, 3)]),
    (40, [("skeleton", 16, 0.5, 0), ("zombie", 5, 1.8, 3), ("witch", 1, 5.0, 6)]),
    (45, [("gargoyle", 6, 1.4, 0), ("zombie", 6, 1.6, 4), ("witch", 1, 6.0, 6)]),
    (60, [("ghost_knight", 1, 1.0, 6), ("zombie", 6, 1.6, 0), ("witch", 1, 6.0, 4)]),
    (75, [("skeleton", 18, 0.5, 0), ("zombie", 5, 1.8, 3), ("witch", 1, 5.0, 6)]),
    (80, [("troll", 2, 4.0, 0), ("skeleton", 16, 0.45, 2), ("zombie", 4, 2.0, 6), ("witch", 2, 5.0, 5)]),
    (85, [("zombie", 10, 1.2, 0), ("gargoyle", 6, 1.5, 5), ("witch", 2, 5.0, 3)]),
    (90, [("ghost_knight", 2, 8.0, 4), ("skeleton", 14, 0.5, 0), ("witch", 2, 5.0, 6)]),
    (0, [("golem", 1, 1.0, 6), ("zombie", 10, 1.2, 0), ("witch", 3, 5.0, 4), ("ghost_knight", 1, 1.0, 16),
         ("gargoyle", 6, 1.6, 10)]),
]


def sealed_portal_wave():
    """Index of the first wave after the first one with the ghost knight."""
    return next(i for i, (_, groups) in enumerate(WAVES) if any(g[0] == "ghost_knight" for g in groups)) + 1


def build():
    enemies = sorted({g[0] for _, groups in WAVES for g in groups})
    ids = {e: f"{10 + i}_{e}" for i, e in enumerate(enemies)}
    out = ['[gd_resource type="Resource" script_class="LevelData" format=3]', "",
           '[ext_resource type="Script" path="res://scripts/data/level_data.gd" id="1_level"]',
           '[ext_resource type="Script" path="res://scripts/data/wave_data.gd" id="2_wave"]',
           '[ext_resource type="Script" path="res://scripts/data/spawn_group.gd" id="3_group"]',
           '[ext_resource type="Resource" path="res://data/themes/haunted.tres" id="4_theme"]',
           '[ext_resource type="Resource" path="res://data/lighting/haunted_night.tres" id="5_lighting"]',
           '[ext_resource type="Texture2D" path="res://assets/ui/level_02_preview.png" id="6_preview"]']
    out += [f'[ext_resource type="Resource" path="res://data/enemies/{e}.tres" id="{ids[e]}"]' for e in enemies]
    out.append("")
    for w, (bonus, groups) in enumerate(WAVES, 1):
        for g, (enemy, count, interval, delay) in enumerate(groups, 1):
            out += [f'[sub_resource type="Resource" id="Resource_w{w}g{g}"]', 'script = ExtResource("3_group")',
                    f'enemy = ExtResource("{ids[enemy]}")', f"count = {count}", f"interval = {float(interval)}"]
            if delay:
                out.append(f"delay = {float(delay)}")
            out.append("")
        refs = ", ".join(f'SubResource("Resource_w{w}g{g}")' for g in range(1, len(groups) + 1))
        out += [f'[sub_resource type="Resource" id="Resource_wave{w}"]', 'script = ExtResource("2_wave")',
                f'groups = Array[ExtResource("3_group")]([{refs}])', f"bonus = {bonus}", ""]
    waves = ", ".join(f'SubResource("Resource_wave{w}")' for w in range(1, len(WAVES) + 1))
    layout = ", ".join(f'"{row}"' for row in LAYOUT)
    out += ["[resource]", 'script = ExtResource("1_level")', 'id = &"haunted_forest"', 'display_name = "Жуткий лес"',
            'description = "Ночной лес, древние руины и старое кладбище. Мертвецы идут из портала на западе, '
            'а после рыцаря-призрака открывается второй — на востоке. В финале — каменный голем."',
            'preview = ExtResource("6_preview")', f"layout = PackedStringArray({layout})", 'music = &"battle_haunted"',
            'map_theme = ExtResource("4_theme")', 'lighting = ExtResource("5_lighting")', 'hud_style = &"haunted"',
            f"start_gold = {START_GOLD}", f"lives = {LIVES}", f"hp_growth = {HP_GROWTH}",
            f"hp_growth_power = {HP_GROWTH_POWER}", f"sealed_portal_wave = {sealed_portal_wave()}",
            f"decor_seed = {DECOR_SEED}", f"waves = Array[ExtResource(\"2_wave\")]([{waves}])", ""]
    path = os.path.join(ROOT, "data", "levels", "level_02.tres")
    with open(path, "w") as f:
        f.write("\n".join(out))
    print(f"wrote {path}: {len(WAVES)} waves, second portal opens with wave {sealed_portal_wave() + 1}")


if __name__ == "__main__":
    build()
