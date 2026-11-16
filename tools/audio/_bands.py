import sys, glob, os
sys.path.insert(0, "tools/audio")
import numpy as np, wavio

def bands(p):
    a, sr = wavio.load(p); x = a.mean(axis=1)
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    f = np.fft.rfftfreq(len(x), 1/sr)
    tot = spec.sum() + 1e-12
    def e(lo, hi):
        m = (f >= lo) & (f < hi)
        return spec[m].sum() / tot
    flat = float(np.exp(np.log(spec[1:] + 1e-12).mean()) / (spec[1:].mean() + 1e-12))
    return e(0,300), e(300,1000), e(1000,4000), e(4000,8000), flat

for p in sorted(glob.glob("assets/audio/sfx_*.wav")):
    lo, mid, pres, hi, flat = bands(p)
    print("%-14s <300=%4.1f%% 300-1k=%4.1f%% 1-4k=%4.1f%% 4-8k=%4.1f%% flatness=%.3f"
          % (os.path.basename(p)[:-4], lo*100, mid*100, pres*100, hi*100, flat))
