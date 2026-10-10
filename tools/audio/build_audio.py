"""Generate all game audio:
    Blender -b --factory-startup -P tools/audio/build_audio.py -- [name ...]
Blender is used only as a Python interpreter that ships numpy.
Writes assets/audio/sfx/<name>.wav (44.1 kHz mono/stereo) and assets/audio/music/<name>.wav
(22.05 kHz stereo loops: plenty for this arrangement and keeps the repository small).
"""
import math
import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402

import synth as s  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SFX_DIR = os.path.join(ROOT, "assets", "audio", "sfx")
MUSIC_DIR = os.path.join(ROOT, "assets", "audio", "music")


# --- sound effects: each returns a mono or stereo signal; the peak sets its relative loudness ----
def arrow_hit():
    thud = s.sine(s.sweep(180, 90, 0.12), 0.12) * s.env_exp(0.12, 0.03)
    tap = s.band(s.noise(0.08), lo=300, hi=2500) * s.env_exp(0.08, 0.012)
    return s.mix((thud, 0.9), (tap, 0.6))


def cannon_shoot():
    boom = s.sine(s.sweep(95, 38, 0.6), 0.6) * s.env_exp(0.6, 0.18)
    blast = s.band_sweep(s.noise(0.9), hi_fn=lambda t: 2500 * math.exp(-t * 5) + 200) * s.env_exp(0.9, 0.22)
    return s.reverb(s.mix((boom, 1.0), (blast, 0.9)), rt60=1.0, wet=0.2)


def explosion():
    blast = s.band_sweep(s.noise(1.3), hi_fn=lambda t: 4000 * math.exp(-t * 4) + 150) * s.env_exp(1.3, 0.3)
    rumble = s.sine(s.sweep(70, 30, 1.2), 1.2) * s.env_exp(1.2, 0.35)
    crackle = s.band(s.noise(0.8), lo=1500) * (s._rng.random(s.samples(0.8)) > 0.985) * s.env_exp(0.8, 0.25)
    return s.reverb(s.mix((blast, 1.0), (rumble, 0.9), (crackle, 0.6, 0.05)), rt60=1.3, wet=0.25)


def magic_shoot():
    d = 0.45
    f = s.sweep(500, 1500, d)
    mod = s.sine(f * 2.01, d) * 2.5
    chirp = np.sin(s.phase(f, s.samples(d)) + mod) * s.env_points(d, [(0, 0), (0.03, 1), (0.25, 0.6), (d, 0)])
    sparkle = sum(s.bell(2400 * r, d, decay=0.25) for r in (1.0, 1.26, 1.5)) / 3
    return s.reverb(s.mix((chirp, 0.6), (sparkle, 0.5, 0.05)), rt60=0.9, wet=0.3)


def magic_hit():
    d = 0.35
    f = s.sweep(1300, 260, d)
    zap = np.sin(s.phase(f, s.samples(d)) + 3 * s.sine(f * 1.5, d)) * s.env_exp(d, 0.1)
    burst = s.band(s.noise(d), lo=800, hi=5000) * s.env_exp(d, 0.05)
    return s.reverb(s.mix((zap, 0.7), (burst, 0.5)), rt60=0.9, wet=0.3)


def ice_shoot():
    chime = sum(s.bell(f, 0.8, decay=0.35) for f in (1760, 2217, 2637)) / 3
    glint = s.whoosh(0.25, 6000, 9000) * s.env_exp(0.25, 0.08)
    return s.reverb(s.mix((chime, 0.8), (glint, 0.3)), rt60=1.0, wet=0.3)


def ice_hit():
    d = 0.45
    clicks = s.band(s.noise(d), lo=3000) * (s._rng.random(s.samples(d)) > 0.97) * s.env_exp(d, 0.12)
    shatter = s.band(s.noise(d), lo=2500, hi=9000) * s.env_exp(d, 0.05)
    tinkle = sum(s.bell(f, d, decay=0.15) for f in (2900, 3520, 4186)) / 3
    return s.reverb(s.mix((shatter, 0.6), (clicks, 0.7), (tinkle, 0.4)), rt60=1.0, wet=0.3)


def ballista_shoot():
    twang = s.pluck(98, 0.15, bright=0.4, tail=0.35)
    thunk = s.sine(s.sweep(160, 90, 0.15), 0.15) * s.env_exp(0.15, 0.04)
    swish = s.whoosh(0.3, 2500, 900) * s.env_points(0.3, [(0, 0), (0.04, 1), (0.3, 0)])
    return s.mix((twang, 0.8), (thunk, 0.9), (swish, 0.45, 0.03))


def enemy_die():
    d = 0.35
    grunt = s.band(s.saw(s.sweep(170, 85, d), d, 10), lo=300, hi=1400) * s.env_exp(d, 0.12, attack=0.01)
    thud = s.sine(s.sweep(120, 55, 0.25), 0.25) * s.env_exp(0.25, 0.07)
    return s.mix((grunt, 0.7), (thud, 0.8, 0.12))


def boss_die():
    d = 1.6
    roar = s.band(s.saw(s.sweep(110, 45, d), d, 16), lo=80, hi=1800)
    roar = np.tanh(roar * 2.5) * s.env_points(d, [(0, 0), (0.08, 1), (0.9, 0.7), (d, 0)])
    rumble = s.sine(s.sweep(60, 28, d), d) * s.env_exp(d, 0.6)
    fall = s.drum(90, 35, 0.9, 0.3, click=0.8)
    return s.reverb(s.mix((roar, 0.6), (rumble, 0.8), (fall, 0.9, 0.9)), rt60=2.0, wet=0.3)


def coin():
    return s.mix((s.bell(2093, 0.35, 0.25), 0.6), (s.bell(2637, 0.35, 0.25), 0.6, 0.06))


def build():
    knock = lambda f: s.mix((s.sine(s.sweep(f, f * 0.7, 0.15), 0.15) * s.env_exp(0.15, 0.04), 1.0),  # noqa: E731
                            (s.band(s.noise(0.05), lo=600, hi=4000) * s.env_exp(0.05, 0.008), 0.6))
    return s.reverb(s.mix((knock(240), 1.0), (knock(260), 0.9, 0.14), (knock(220), 1.0, 0.28),
                          (s.whoosh(0.5, 400, 200) * s.env_exp(0.5, 0.2), 0.25, 0.3)), rt60=0.8, wet=0.2)


def upgrade():
    notes = [s.midi(m) for m in (72, 76, 79, 84)]
    arp = s.mix(*[(s.bell(f, 1.0, 0.6), 0.7, i * 0.08) for i, f in enumerate(notes)])
    shimmer = s.whoosh(0.7, 3000, 8000) * s.env_points(0.7, [(0, 0), (0.3, 1), (0.7, 0)])
    return s.reverb(s.mix((arp, 1.0), (shimmer, 0.15, 0.1)), rt60=1.5, wet=0.3)


def sell():
    pings = [(s.bell(s._rng.uniform(1900, 3200), 0.4, 0.25), 0.5, i * 0.05 + s._rng.uniform(0, 0.02))
             for i in range(6)]
    return s.reverb(s.mix(*pings), rt60=0.8, wet=0.2)


def error():
    buzz = s.band(s.additive(110, 0.12, [1, 0, 0.33, 0, 0.2, 0, 0.14]), hi=1500) * s.env_adsr(0.12, 0.005, 0.02, 0.8, 0.03)
    return s.mix((buzz, 1.0), (buzz, 1.0, 0.14))


def ui_click():
    tick = s.band(s.noise(0.03), lo=1500, hi=6000) * s.env_exp(0.03, 0.006)
    knock = s.sine(900, 0.05) * s.env_exp(0.05, 0.012)
    return s.mix((tick, 0.6), (knock, 0.6))


def ui_hover():
    return s.band(s.noise(0.02), lo=3000, hi=8000) * s.env_exp(0.02, 0.004)


def castle_hit():
    boom = s.drum(80, 35, 1.0, 0.3, click=1.0)
    clang = s.bell(311, 1.4, 0.8)
    debris = s.band(s.noise(0.8), lo=400, hi=3000) * s.env_exp(0.8, 0.2)
    return s.reverb(s.mix((boom, 1.0), (clang, 0.45), (debris, 0.35, 0.05)), rt60=1.6, wet=0.3)


def wave_horn():
    a = s.horn(s.midi(50), 0.55)
    b = s.horn(s.midi(57), 1.1)
    return s.reverb(s.mix((a, 0.8), (b, 0.9, 0.5)), rt60=2.2, wet=0.35)


def wave_clear():
    notes = [(62, 0.0, 0.25), (66, 0.18, 0.25), (69, 0.36, 0.25), (74, 0.54, 0.8)]
    parts = [(s.horn(s.midi(m), d, vibrato=False), 0.6, at) for m, at, d in notes]
    return s.reverb(s.mix(*parts), rt60=1.8, wet=0.3)


def victory():
    melody = [(62, 0.0, 0.3), (66, 0.3, 0.3), (69, 0.6, 0.3), (74, 0.9, 0.6), (71, 1.5, 0.3), (74, 1.8, 1.4)]
    parts = [(s.horn(s.midi(m), d), 0.55, at) for m, at, d in melody]
    parts += [(s.strings(s.midi(m), 1.6), 0.25, 1.8) for m in (50, 57, 62, 66)]
    parts += [(s.drum(140, 70, 0.3, 0.1, 0.6), 0.5, 0.0 + 0.1 * i) for i in range(8)]
    parts += [(s.drum(), 0.9, 1.8)]
    return s.reverb(s.mix(*parts), rt60=2.2, wet=0.3)


def defeat():
    melody = [(62, 0.0, 0.6), (60, 0.6, 0.6), (58, 1.2, 0.6), (57, 1.8, 1.6)]
    parts = [(s.horn(s.midi(m), d), 0.55, at) for m, at, d in melody]
    parts += [(s.strings(s.midi(m), 2.0), 0.3, 1.8) for m in (45, 52, 57, 60)]
    parts += [(s.drum(70, 30, 1.2, 0.5, 0.8), 1.0, 1.8)]
    return s.reverb(s.mix(*parts), rt60=2.5, wet=0.35)


def portal_spawn():
    d = 0.7
    swirl = s.whoosh(d, 250, 1400) * s.env_points(d, [(0, 0), (0.3, 1), (d, 0)])
    swirl *= 1 + 0.5 * s.sine(14, d)
    hum = s.sine(s.sweep(90, 60, d), d) * s.env_points(d, [(0, 0), (0.2, 1), (d, 0)])
    return s.reverb(s.mix((swirl, 0.7), (hum, 0.5)), rt60=1.5, wet=0.35)


def summon():
    d = 1.4
    voices = [s.band(s.saw(s.sweep(s.midi(m), s.midi(m + 5), d), d, 14), lo=200, hi=1600) for m in (38, 45, 50)]
    choir = sum(voices) / 3 * s.env_points(d, [(0, 0), (0.5, 1), (1.1, 0.8), (d, 0)])
    swell = s.whoosh(d, 200, 2000) * s.env_points(d, [(0, 0), (1.0, 1), (d, 0)])
    return s.reverb(s.mix((choir, 0.7), (swell, 0.4)), rt60=2.4, wet=0.4)


SFX = dict(  # name: (recipe, peak)
    arrow_hit=(arrow_hit, 0.35), cannon_shoot=(cannon_shoot, 0.8), explosion=(explosion, 0.85),
    magic_shoot=(magic_shoot, 0.22), magic_hit=(magic_hit, 0.25),
    ice_shoot=(ice_shoot, 0.13), ice_hit=(ice_hit, 0.15), ballista_shoot=(ballista_shoot, 0.6),
    enemy_die=(enemy_die, 0.45), boss_die=(boss_die, 0.9), coin=(coin, 0.25), build=(build, 0.7),
    upgrade=(upgrade, 0.6), sell=(sell, 0.55), error=(error, 0.4), ui_click=(ui_click, 0.35),
    ui_hover=(ui_hover, 0.12), castle_hit=(castle_hit, 0.9), wave_horn=(wave_horn, 0.75),
    wave_clear=(wave_clear, 0.6), victory=(victory, 0.85), defeat=(defeat, 0.85),
    portal_spawn=(portal_spawn, 0.35), summon=(summon, 0.7),
)


# --- music ----------------------------------------------------------------------------------------
CHORDS = {  # root MIDI note in octave 3 and chord tones (semitones)
    "Dm": (50, (0, 3, 7)), "C": (48, (0, 4, 7)), "Bb": (46, (0, 4, 7)), "F": (53, (0, 4, 7)),
    "Gm": (55, (0, 3, 7)), "A": (57, (0, 4, 7)),
}
SECTION_A = ["Dm", "C", "Bb", "C", "Dm", "F", "C", "A"]
SECTION_B = ["Gm", "Dm", "Bb", "F", "Gm", "Dm", "A", "A"]
# melody: per bar a list of (MIDI note or None for a rest, beats)
MELODY_A = [
    [(69, 1), (74, 1), (76, 0.5), (77, 0.5), (76, 1)],
    [(76, 1.5), (74, 0.5), (72, 1), (67, 1)],
    [(65, 1), (70, 1), (69, 0.5), (67, 0.5), (65, 1)],
    [(67, 1.5), (69, 0.5), (67, 1), (64, 1)],
    [(62, 1), (65, 1), (69, 1), (74, 1)],
    [(72, 1.5), (69, 0.5), (77, 1), (72, 1)],
    [(76, 1), (74, 0.5), (72, 0.5), (67, 1), (72, 1)],
    [(69, 3), (None, 1)],
]
MELODY_B = [
    [(74, 1), (70, 1), (67, 1), (70, 1)],
    [(69, 1.5), (65, 0.5), (62, 1), (65, 1)],
    [(65, 0.5), (67, 0.5), (70, 1), (74, 1), (70, 1)],
    [(72, 2), (69, 1), (65, 1)],
    [(67, 1), (70, 1), (74, 1.5), (72, 0.5)],
    [(69, 1), (65, 1), (64, 0.5), (65, 0.5), (62, 1)],
    [(64, 1), (69, 1), (73, 1), (76, 1)],
    [(69, 3), (None, 1)],
]


def _chord_notes(name, octave_shift=0):
    root, tones = CHORDS[name]
    return [root + t + 12 * octave_shift for t in tones]


def compose(bpm, bars, melodies, drums, arp_pattern, melody_octave=0, flute_gain=0.5, intensity=None):
    beat = 60.0 / bpm
    bar = 4 * beat
    length = len(bars) * bar
    buf = np.zeros((s.samples(length + 4.0), 2))
    for i, chord in enumerate(bars):
        t0 = i * bar
        level = intensity[i] if intensity else 1.0
        notes = _chord_notes(chord)
        # strings pad, two inversions panned apart
        for k, m in enumerate(notes):
            s.place(buf, s.strings(s.midi(m + 12), bar), t0, 0.07, pan=-0.5 + 0.5 * k)
        # lute bass: root on 1 and 3, fifth on the "and" of 4
        root = notes[0] - 12
        for at, m in ((0, root), (2, root), (3.5, root + 7)):
            s.place(buf, s.pluck(s.midi(m), beat * 1.5, bright=0.5, tail=0.6), t0 + at * beat, 0.35, pan=0.0)
        # harp arpeggio
        up = [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[0] + 24]
        for j, idx in enumerate(arp_pattern):
            m = up[idx % 4]
            s.place(buf, s.pluck(s.midi(m), beat * 0.5, bright=1.0, tail=1.2, damp=False),
                    t0 + j * beat * 4 / len(arp_pattern), 0.16 * (0.8 + 0.2 * level), pan=-0.35)
        # drums
        for at, kind in drums:
            if kind == "big":
                s.place(buf, s.drum(), t0 + at * beat, 0.55 * level, pan=0.05)
            elif kind == "tom":
                s.place(buf, s.drum(180, 110, 0.3, 0.1, 0.4), t0 + at * beat, 0.3 * level, pan=0.25)
            elif kind == "shaker":
                s.place(buf, s.shaker(), t0 + at * beat, 0.08 * level, pan=0.4)
    # flute melody
    for i, phrase in enumerate(melodies):
        t = i * bar
        for m, beats in phrase:
            if m is not None:
                s.place(buf, s.flute(s.midi(m + 12 * melody_octave), beats * beat * 0.95), t, flute_gain, pan=0.2)
            t += beats * beat
    wet = s.reverb(buf, rt60=2.4, wet=0.3)
    n = s.samples(length)
    loop = wet[:n].copy()
    tail = wet[n:]
    loop[:len(tail)] += tail[:n]  # wrap the reverb tail around so the loop is seamless
    return s.normalize(loop, 0.85)


def music_battle():
    bars = SECTION_A + SECTION_B + SECTION_A + SECTION_B
    melodies = MELODY_A + MELODY_B + MELODY_A + MELODY_B
    drums = [(0, "big"), (1.5, "big"), (2, "big"), (3.5, "tom"), (3.75, "tom")] + [(k * 0.5, "shaker") for k in range(8)]
    intensity = [0.7] * 16 + [1.0] * 16
    return compose(112, bars, melodies, drums, arp_pattern=[0, 1, 2, 3, 2, 1, 0, 1], intensity=intensity)


def music_menu():
    bars = SECTION_A + SECTION_B
    melodies = MELODY_A + MELODY_B
    drums = [(0, "big")]
    return compose(76, bars, melodies, drums, arp_pattern=[0, 1, 2, 3, 2, 3, 1, 2], melody_octave=-1,
                   flute_gain=0.45, intensity=[0.4] * 16)


MUSIC = dict(menu=music_menu, battle=music_battle)


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    os.makedirs(SFX_DIR, exist_ok=True)
    os.makedirs(MUSIC_DIR, exist_ok=True)
    for name, (recipe, peak) in SFX.items():
        if args and name not in args:
            continue
        s.reseed(zlib.crc32(name.encode()))
        x = s.fade(s.normalize(s.trim(recipe()), peak), 0.001, 0.03)
        s.write_wav(os.path.join(SFX_DIR, f"{name}.wav"), x)
        print(f"[sfx] {name}: {len(x) / s.SR:.2f} s")
    s.SR = 22050
    for name, recipe in MUSIC.items():
        if args and name not in args:
            continue
        s.reseed(42)
        x = recipe()
        s.write_wav(os.path.join(MUSIC_DIR, f"{name}.wav"), x)
        print(f"[music] {name}: {len(x) / s.SR:.1f} s")


main()
