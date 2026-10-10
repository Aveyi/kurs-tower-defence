"""A tiny numpy synthesizer: every sound and every note of music in the game is generated here,
no recorded samples are used.

Building blocks: oscillators with frequency sweeps, envelopes, FFT/STFT filters, convolution
reverb with a synthetic impulse response, and a handful of instruments (plucked string, flute,
strings, horn, bell, drums).
"""
import wave

import numpy as np

SR = 44100
_rng = np.random.default_rng(1)


def reseed(n):
    global _rng
    _rng = np.random.default_rng(n)


def samples(d):
    return max(1, int(round(d * SR)))


def time(d):
    return np.arange(samples(d)) / SR


def midi(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


# --- oscillators ----------------------------------------------------------------------------
def _freq_array(freq, n):
    f = np.asarray(freq, dtype=float)
    return np.full(n, float(f)) if f.ndim == 0 else f[:n]


def phase(freq, n, start=0.0):
    return start + 2 * np.pi * np.cumsum(_freq_array(freq, n)) / SR


def sine(freq, d, start=0.0):
    return np.sin(phase(freq, samples(d), start))


def sweep(f0, f1, d, exponential=True):
    t = np.linspace(0.0, 1.0, samples(d))
    return f0 * (f1 / f0) ** t if exponential else f0 + (f1 - f0) * t


def additive(freq, d, amps, ratios=None, phases=None):
    """Sum of partials; `ratios` default to harmonics 1, 2, 3..."""
    n = samples(d)
    ph = phase(freq, n)
    out = np.zeros(n)
    for k, a in enumerate(amps):
        r = ratios[k] if ratios is not None else k + 1
        p0 = phases[k] if phases is not None else 0.0
        out += a * np.sin(ph * r + p0)
    return out


def saw(freq, d, harmonics=12, rolloff=1.0):
    return additive(freq, d, [1.0 / (k ** rolloff) for k in range(1, harmonics + 1)])


def noise(d):
    return _rng.uniform(-1.0, 1.0, samples(d))


# --- envelopes ------------------------------------------------------------------------------
def env_exp(d, tau, attack=0.002):
    t = time(d)
    e = np.exp(-t / tau)
    if attack > 0:
        e *= np.minimum(t / attack, 1.0)
    return e


def env_adsr(d, a, dcy, s, r):
    a = min(a, d * 0.5)
    r = min(r, d - a)
    knots = [0.0, a, min(a + dcy, d - r), d - r, d]
    knots = np.maximum.accumulate(knots)
    return np.interp(time(d), knots, [0.0, 1.0, s, s, 0.0])


def env_points(d, points):
    """Piecewise-linear envelope from (time, value) pairs."""
    ts, vs = zip(*points)
    return np.interp(time(d), ts, vs)


# --- filters --------------------------------------------------------------------------------
def _response(f, lo, hi, order):
    h = np.ones_like(f)
    if hi:
        h /= np.sqrt(1.0 + (f / hi) ** (2 * order))
    if lo:
        with np.errstate(divide="ignore"):
            h /= np.sqrt(1.0 + (lo / np.maximum(f, 1e-6)) ** (2 * order))
    return h


def band(x, lo=None, hi=None, order=2):
    """Zero-phase Butterworth-like filter in the frequency domain (lo = high-pass, hi = low-pass)."""
    n = len(x)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    return np.fft.irfft(np.fft.rfft(x) * _response(f, lo, hi, order), n)


def band_sweep(x, lo_fn=None, hi_fn=None, order=2, frame=2048, hop=512):
    """Time-varying filter (STFT overlap-add); lo_fn/hi_fn map time in seconds to a cutoff."""
    win = np.hanning(frame)
    pad = np.concatenate([np.zeros(frame), x, np.zeros(frame)])
    out = np.zeros_like(pad)
    norm = np.zeros_like(pad)
    f = np.fft.rfftfreq(frame, 1.0 / SR)
    for start in range(0, len(pad) - frame, hop):
        t = (start + frame / 2 - frame) / SR
        seg = pad[start:start + frame] * win
        h = _response(f, lo_fn(t) if lo_fn else None, hi_fn(t) if hi_fn else None, order)
        out[start:start + frame] += np.fft.irfft(np.fft.rfft(seg) * h, frame) * win
        norm[start:start + frame] += win ** 2
    out /= np.maximum(norm, 1e-6)
    return out[frame:frame + len(x)]


# --- mixing ---------------------------------------------------------------------------------
def mix(*parts):
    """Sum signals of different lengths, all starting at 0. Each part may be (signal, gain, delay_s)."""
    items = [(p, 1.0, 0.0) if isinstance(p, np.ndarray) else (p[0], p[1], p[2] if len(p) > 2 else 0.0)
             for p in parts]
    n = max(len(x) + samples(dl) for x, _, dl in items)
    out = np.zeros(n)
    for x, g, dl in items:
        s = samples(dl) if dl > 0 else 0
        out[s:s + len(x)] += g * x
    return out


def place(buf, x, at, gain=1.0, pan=0.0):
    """Add mono x into a stereo buffer at time `at` with constant-power panning (-1 left .. 1 right)."""
    s = samples(at) if at > 0 else 0
    e = min(len(buf), s + len(x))
    if e <= s:
        return
    angle = (pan + 1.0) * np.pi / 4.0
    buf[s:e, 0] += x[:e - s] * gain * np.cos(angle)
    buf[s:e, 1] += x[:e - s] * gain * np.sin(angle)


def _fft_convolve(a, b):
    n = len(a) + len(b) - 1
    size = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(a, size) * np.fft.rfft(b, size), size)[:n]


def reverb(x, rt60=1.2, wet=0.25, predelay=0.012, damp=5000.0, seed=3):
    """Convolution reverb with an exponentially decaying noise impulse response.
    Mono input gives a stereo result (decorrelated left/right tails)."""
    rng = np.random.default_rng(seed)
    t = time(rt60 * 1.1)
    decay = np.exp(-6.9 * t / rt60)
    channels = x.T if x.ndim == 2 else (x, x)
    out = []
    for ch, src in enumerate(channels):
        ir = band(rng.uniform(-1, 1, len(t)) * decay, hi=damp)
        ir = np.concatenate([np.zeros(samples(predelay) + ch * 37), ir])
        ir /= np.sqrt(np.sum(ir ** 2))
        tail = _fft_convolve(src, ir)
        dry = np.concatenate([src, np.zeros(len(tail) - len(src))])
        out.append(dry * (1.0 - wet * 0.5) + tail * wet)
    n = max(len(o) for o in out)
    return np.stack([np.pad(o, (0, n - len(o))) for o in out], axis=1)


def trim(x, threshold=0.002, keep=0.05):
    """Cut the inaudible end of a tail (below `threshold` of the peak), keeping a short margin."""
    level = np.abs(x).max(axis=1) if x.ndim == 2 else np.abs(x)
    loud = np.nonzero(level > threshold * level.max())[0]
    return x[:min(len(x), loud[-1] + 1 + samples(keep))] if len(loud) else x


def normalize(x, peak=0.9):
    m = np.max(np.abs(x))
    return x * (peak / m) if m > 0 else x


def fade(x, fade_in=0.002, fade_out=0.02):
    x = x.copy()
    a, b = min(samples(fade_in), len(x) // 4), min(samples(fade_out), len(x) // 2)
    x[:a] *= np.linspace(0, 1, a)[:, None] if x.ndim == 2 else np.linspace(0, 1, a)
    x[-b:] *= np.linspace(1, 0, b)[:, None] if x.ndim == 2 else np.linspace(1, 0, b)
    return x


def write_wav(path, x):
    data = np.clip(x, -1.0, 1.0)
    data = (data * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1 if data.ndim == 1 else 2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


# --- instruments ----------------------------------------------------------------------------
def pluck(freq, d, bright=1.0, tail=1.0, damp=True):
    """Plucked string (lute / harp): harmonics decaying faster the higher they are."""
    total = d + tail
    t = time(total)
    out = np.zeros(len(t))
    for k in range(1, 16):
        if k * freq > 11000:
            break
        amp = (abs(np.sin(np.pi * k * 0.17)) + 0.05) / k ** (1.3 - 0.3 * bright)
        tau = (0.25 + 0.6 * bright) / (1 + 0.5 * (k - 1))
        out += amp * np.sin(2 * np.pi * k * freq * t + _rng.uniform(0, 6.28)) * np.exp(-t / tau)
    out += band(noise(total), lo=2000) * np.exp(-t / 0.004) * 0.15
    if damp:  # the player mutes the string when the note ends
        out *= np.interp(t, [0, d, d + 0.25, total], [1, 1, 0, 0])
    return out * np.minimum(t / 0.0015, 1)


def flute(freq, d):
    total = d + 0.15
    t = time(total)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.15) / 0.25, 0, 1)
    ph = phase(freq * vib, len(t))
    tone = np.sin(ph) + 0.28 * np.sin(2 * ph) + 0.09 * np.sin(3 * ph) + 0.03 * np.sin(4 * ph)
    breath = band(noise(total), lo=freq * 1.5, hi=freq * 4) * 0.09
    return (tone + breath) * env_adsr(total, 0.06, 0.12, 0.8, 0.14)


def strings(freq, d):
    total = d + 0.6
    out = np.zeros(samples(total))
    for cents in (-7, 0, 7):
        out += saw(freq * 2 ** (cents / 1200), total, harmonics=10, rolloff=1.2)
    return out * env_adsr(total, 0.45, 0.3, 0.8, 0.6) / 3


def horn(freq, d, vibrato=True):
    total = d + 0.2
    t = time(total)
    vib = 1 + (0.008 * np.sin(2 * np.pi * 5.0 * t) * np.clip((t - 0.25) / 0.3, 0, 1) if vibrato else 0)
    f = freq * vib
    dull = additive(f, total, [1.0, 0.45, 0.2, 0.08])
    bright = additive(f, total, [1.0 / k ** 0.9 for k in range(1, 15)])
    shape = env_adsr(total, 0.07, 0.25, 0.75, 0.18)
    brightness = np.clip(shape * 1.1, 0, 1) ** 1.5
    return (dull * (1 - brightness) + bright * brightness * 0.8) * shape


def bell(freq, d=1.5, decay=1.0):
    ratios = [1.0, 2.0, 2.76, 4.07, 5.4, 8.93]
    amps = [1.0, 0.55, 0.45, 0.3, 0.2, 0.1]
    taus = [1.2, 0.9, 0.7, 0.45, 0.3, 0.18]
    t = time(d)
    out = np.zeros(len(t))
    for r, a, tau in zip(ratios, amps, taus):
        if freq * r < 16000:
            out += a * np.sin(2 * np.pi * freq * r * t) * np.exp(-t / (tau * decay))
    return out * np.minimum(t / 0.001, 1)


def drum(f0=110.0, f1=48.0, d=0.6, tau=0.22, click=0.5):
    """Big frame drum / taiko: a falling sine plus a short noise smack."""
    body = sine(sweep(f0, f1, d), d) * env_exp(d, tau)
    smack = band(noise(d), hi=1200) * env_exp(d, 0.012) * click
    return body + smack


def shaker(d=0.09, tone=6000.0):
    return band(noise(d), lo=tone) * env_points(d, [(0, 0), (0.008, 1), (d, 0)])


def whoosh(d, f0, f1, width=1.5):
    """Band-passed noise whose centre slides from f0 to f1."""
    centre = lambda t: f0 * (f1 / f0) ** min(max(t / d, 0), 1)  # noqa: E731
    return band_sweep(noise(d), lo_fn=lambda t: centre(t) / width, hi_fn=lambda t: centre(t) * width)
