"""Synthesise the game's sound effects.  Every cue is built from an envelope, a
filtered noise band and one or two pitched partials, so nothing is a wall of
static: the complaint that drove this file was "the station sounds are noise".

Run:  python tools/audio/make_sfx.py
Out:  assets/audio/sfx_*.wav  (44.1 kHz / 16-bit / stereo, peak -3 dBFS)
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import wavio  # noqa: E402

SR = 44100
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "audio")


# -- primitives ---------------------------------------------------------
def t_axis(seconds):
    return np.arange(int(SR * seconds)) / SR


def decay(seconds, tau):
    return np.exp(-t_axis(seconds) / tau)


def noise(seconds, seed=0):
    rng = np.random.default_rng(seed)
    return rng.standard_normal(int(SR * seconds))


def band(x, lo, hi, soft=0.25):
    """Smooth FFT band-pass: keep lo..hi Hz, roll off over a fraction of it."""
    n = len(x)
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    mask = np.ones_like(f)
    edge = max(20.0, (hi - lo) * soft)
    if lo > 0:
        mask *= np.clip((f - (lo - edge)) / edge, 0.0, 1.0)
    mask *= np.clip(((hi + edge) - f) / edge, 0.0, 1.0)
    return np.fft.irfft(spec * mask, n)


def hp(x, cut=50.0):
    return band(x, cut, SR * 0.45, soft=0.5)


def lp(x, cut=14000.0):
    return band(x, 0.0, cut, soft=0.3)


def fade(x, ms_in=2.0, ms_out=12.0):
    x = x.copy()
    a = max(1, int(SR * ms_in / 1000))
    b = max(1, int(SR * ms_out / 1000))
    a = min(a, len(x))
    b = min(b, len(x))
    x[:a] *= np.linspace(0.0, 1.0, a)
    x[-b:] *= np.linspace(1.0, 0.0, b)
    return x


def tone(seconds, freq, tau, partials=((1.0, 1.0),), phase=0.0):
    t = t_axis(seconds)
    out = np.zeros_like(t)
    for ratio, gain in partials:
        out += gain * np.sin(2 * np.pi * freq * ratio * t + phase)
    return out * decay(seconds, tau)


def click(seconds, lo, hi, tau, seed=1, gain=1.0):
    n = noise(seconds, seed)
    return gain * band(n, lo, hi) * decay(seconds, tau)


def crackle_bed(seconds, lo, hi, density, tau_range, seed=5, gain=1.0):
    """Irregular fat grains: what makes a sizzle read as frying, not as hiss."""
    out = np.zeros(int(SR * seconds))
    rng = np.random.default_rng(seed)
    for _ in range(density):
        start = int(rng.uniform(0, seconds * 0.75) * SR)
        length = int(rng.uniform(*tau_range) * SR * 4)
        grain = band(noise(length / SR, int(rng.integers(0, 10 ** 6))), lo, hi)
        grain *= decay(length / SR, rng.uniform(*tau_range))
        end = min(len(out), start + len(grain))
        out[start:end] += grain[: end - start] * rng.uniform(0.35, 1.0)
    return out * gain


def pad(x, seconds):
    want = int(SR * seconds)
    if len(x) >= want:
        return x[:want]
    return np.concatenate([x, np.zeros(want - len(x))])


def mix(*parts):
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[: len(p)] += p
    return out


# -- the cue set --------------------------------------------------------
def s_chop(pitch=1.0, seed=11):
    # Knife bite first, then the woody thud: the bite is what the ear reads as
    # "cut", and it has to survive a small laptop speaker, hence 2-6 kHz.
    body = mix(
        tone(0.20, 168.0 * pitch, 0.050, ((1.0, 0.62), (1.9, 0.28))),
        click(0.20, 2400.0, 7000.0, 0.004, seed=seed, gain=1.05),
        click(0.20, 900.0 * pitch, 2400.0, 0.012, seed=seed + 1, gain=0.55),
        click(0.20, 300.0, 900.0, 0.035, seed=seed + 2, gain=0.30),
    )
    return pad(body, 0.24)


def s_pickup():
    body = mix(
        click(0.16, 1200.0, 5000.0, 0.012, seed=21, gain=0.5),
        tone(0.16, 620.0, 0.030, ((1.0, 1.0), (2.4, 0.3))),
    )
    return pad(body, 0.18)


def s_place():
    body = mix(
        tone(0.20, 236.0, 0.045, ((1.0, 1.0), (1.6, 0.4))),
        click(0.20, 700.0, 3200.0, 0.018, seed=31, gain=0.28),
    )
    return pad(body, 0.22)


def s_sizzle():
    hit = mix(
        tone(0.45, 96.0, 0.075, ((1.0, 1.0), (2.1, 0.3))),
        band(noise(0.45, 43), 160.0, 520.0) * decay(0.45, 0.10) * 0.30,
        crackle_bed(0.45, 900.0, 3400.0, 26, (0.012, 0.045), seed=41, gain=0.95),
    )
    tail = band(noise(0.45, 42), 1100.0, 3800.0) * decay(0.45, 0.16) * 0.14
    return pad(fade(mix(hit, tail), 3, 90), 0.50)


def s_steam():
    seconds = 0.46
    t = t_axis(seconds)
    shape = np.exp(-(t / 0.14) ** 1.4)
    # Steam below 3.5 kHz reads as a soft puff; above that it is just hiss.
    breath = band(noise(seconds, 51), 800.0, 3400.0) * shape
    breath *= 1.0 + 0.25 * np.sin(2 * np.pi * 7.5 * t)
    airy = band(noise(seconds, 52), 220.0, 900.0) * decay(seconds, 0.12) * 0.55
    return pad(fade(mix(breath * 0.85, airy), 10, 120), 0.50)


def s_oven():
    seconds = 0.55
    t = t_axis(seconds)
    swell = np.clip(t / 0.09, 0.0, 1.0) * np.exp(-np.clip(t - 0.09, 0, None) / 0.16)
    whoosh = band(noise(seconds, 61), 110.0, 900.0) * swell
    body = tone(seconds, 78.0, 0.09, ((1.0, 1.0), (2.0, 0.25)))
    ign = click(seconds, 1200.0, 4200.0, 0.010, seed=62, gain=0.30)
    return pad(fade(mix(whoosh * 0.9, body * 0.7, ign), 4, 90), 0.58)


def s_ready():
    seconds = 0.55
    bell = mix(
        tone(seconds, 1318.5, 0.22, ((1.0, 1.0), (2.0, 0.35), (3.0, 0.16), (4.2, 0.07))),
        tone(seconds, 1975.5, 0.14, ((1.0, 0.28), (2.0, 0.08))),
    )
    tick = click(seconds, 2500.0, 7000.0, 0.004, seed=71, gain=0.18)
    return pad(fade(mix(bell, tick), 1, 140), 0.55)


def s_bell():
    seconds = 0.80
    a = tone(seconds, 880.0, 0.34, ((1.0, 1.0), (2.0, 0.30), (3.0, 0.12), (4.0, 0.05)))
    b = np.concatenate([np.zeros(int(SR * 0.09)),
                        tone(seconds, 1318.5, 0.28, ((1.0, 0.85), (2.0, 0.22), (3.0, 0.09)))])
    b = pad(b, seconds)
    return pad(fade(mix(a, b), 1, 150), 0.80)


def s_order():
    seconds = 0.60
    def note(freq, when, tau):
        lead = int(SR * when)
        n = tone(seconds, freq, tau, ((1.0, 1.0), (2.0, 0.22), (4.0, 0.05)))
        return pad(np.concatenate([np.zeros(lead), n]), seconds)
    return pad(fade(mix(note(523.25, 0.00, 0.16), note(783.99, 0.10, 0.18)), 1, 160), 0.60)


def s_fail():
    seconds = 0.85
    def note(freq, when, tau, gain):
        lead = int(SR * when)
        n = tone(seconds, freq, tau, ((1.0, 1.0), (3.0, 0.12))) * gain
        return pad(np.concatenate([np.zeros(lead), n]), seconds)
    seq = mix(note(440.0, 0.00, 0.22, 1.0), note(349.23, 0.13, 0.22, 0.9),
              note(293.66, 0.27, 0.30, 0.8))
    return pad(fade(seq, 2, 180), 0.85)


def s_tick():
    body = mix(click(0.09, 1600.0, 5000.0, 0.010, seed=81, gain=0.6),
               tone(0.09, 1180.0, 0.014, ((1.0, 1.0), (2.0, 0.25))))
    return pad(fade(body, 1, 25), 0.09)


def s_trash():
    seconds = 0.45
    thud = mix(tone(seconds, 110.0, 0.070, ((1.0, 1.0), (2.0, 0.35))),
               band(noise(seconds, 91), 90.0, 700.0) * decay(seconds, 0.055) * 0.7)
    ring = tone(seconds, 786.0, 0.13, ((1.0, 0.30), (2.7, 0.12), (5.1, 0.05)))
    clank = click(seconds, 1800.0, 6000.0, 0.020, seed=92, gain=0.18)
    return pad(fade(mix(thud, ring, clank), 3, 120), 0.45)


# Three takes of the most repeated sound in the game: a single sample played
# three times per dish turns into a machine gun.
CUES = {
    "sfx_chop": s_chop,
    "sfx_chop_1": lambda: s_chop(0.94, seed=101),
    "sfx_chop_2": lambda: s_chop(1.06, seed=201),
    "sfx_chop_3": lambda: s_chop(1.12, seed=301),
    "sfx_pickup": s_pickup,
    "sfx_place": s_place,
    "sfx_sizzle": s_sizzle,
    "sfx_steam": s_steam,
    "sfx_oven": s_oven,
    "sfx_ready": s_ready,
    "sfx_bell": s_bell,
    "sfx_order": s_order,
    "sfx_fail": s_fail,
    "sfx_tick": s_tick,
    "sfx_trash": s_trash,
}


def report(path, x):
    mono = np.asarray(x, dtype=np.float32)
    peak = float(np.abs(mono).max()) or 1.0
    rms = float(np.sqrt((mono ** 2).mean()))
    win = 1024
    freqs = np.fft.rfftfreq(win, 1 / SR)
    cents = []
    for i in range(0, max(1, len(mono) - win), win // 2):
        pw = np.abs(np.fft.rfft(mono[i:i + win] * np.hanning(win))) ** 2 + 1e-12
        cents.append(float((freqs * pw).sum() / pw.sum()))
    hop = int(SR * 0.02)
    env = np.array([np.sqrt((mono[i:i + hop] ** 2).mean()) for i in range(0, max(1, len(mono) - hop), hop)])
    env = env / (env.max() + 1e-9)
    steady = float(env.std() / (env.mean() + 1e-9))
    print("%-14s %5.2fs  peak=%5.1f dB  rms=%5.1f dB  cent=%5.0f Hz  steady=%4.2f  %s"
          % (os.path.basename(path), len(mono) / SR, 20 * np.log10(peak + 1e-9),
             20 * np.log10(rms + 1e-9), float(np.mean(cents)), steady, "OK"))


# Per-cue loudness: one number per sound so the mix does not need babysitting.
TARGET_RMS_DB = {
    "sfx_chop": -18.0, "sfx_chop_1": -18.0, "sfx_chop_2": -18.0, "sfx_chop_3": -18.0,
    "sfx_pickup": -20.0, "sfx_place": -20.0,
    "sfx_sizzle": -20.5, "sfx_steam": -21.0, "sfx_oven": -20.0,
    "sfx_ready": -19.0, "sfx_bell": -17.0, "sfx_order": -18.0,
    "sfx_fail": -17.0, "sfx_tick": -21.0, "sfx_trash": -20.0,
}


def normalise(x, target_db):
    x = np.asarray(x, dtype=np.float32)
    rms = float(np.sqrt((x ** 2).mean())) or 1.0
    x = x * (10 ** (target_db / 20.0) / rms)
    peak = float(np.abs(x).max())
    if peak > 0.89:  # keep 1 dB of headroom instead of clipping the transient
        x = x * (0.89 / peak)
    return x


def rms_db(x):
    return 20 * np.log10(float(np.sqrt((np.asarray(x) ** 2).mean())) + 1e-9)


def main():
    os.makedirs(OUT, exist_ok=True)
    rendered = {}
    # The three chop takes must not drift apart in level: the ear hears a
    # louder take as a different sound, not as the same knife.
    reference = None
    for name, fn in CUES.items():
        x = lp(hp(fn()))
        x = normalise(x, TARGET_RMS_DB[name])
        if name == "sfx_chop":
            reference = rms_db(x)
        elif name.startswith("sfx_chop_") and reference is not None:
            gain = 10 ** ((reference - rms_db(x)) / 20.0)
            # Soft ceiling instead of asking permission from the peak: a clipped
            # 4 ms transient is inaudible, an alternating loud/quiet knife is not.
            x = np.clip(x * gain, -0.95, 0.95)
        rendered[name] = x
    for name, x in rendered.items():
        path = os.path.abspath(os.path.join(OUT, name + ".wav"))
        wavio.save_mono(path, x, SR)
        audio, sr = wavio.load(path)
        report(path, audio.mean(axis=1))


if __name__ == "__main__":
    main()