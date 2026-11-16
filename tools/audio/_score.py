import sys, glob, os
sys.path.insert(0, "tools/audio")
import numpy as np
import wavio


def feats(p):
    a, sr = wavio.load(p)
    a = a.mean(axis=1)
    a = a / (np.abs(a).max() + 1e-9)
    n = len(a)
    dur = n / sr
    hop = int(sr * 0.02)
    env = np.array([np.sqrt((a[i:i + hop] ** 2).mean()) for i in range(0, max(1, n - hop), hop)])
    e = env / (env.max() + 1e-9)
    tot = (e ** 2).sum() + 1e-9
    head = (e[:max(1, len(e) // 4)] ** 2).sum() / tot
    steady = float(e.std() / (e.mean() + 1e-9))
    win = 1024
    freqs = np.fft.rfftfreq(win, 1 / sr)
    cents, rolls = [], []
    for i in range(0, max(1, n - win), win // 2):
        seg = a[i:i + win] * np.hanning(win)
        pw = np.abs(np.fft.rfft(seg)) ** 2 + 1e-12
        cents.append(float((freqs * pw).sum() / pw.sum()))
        cum = np.cumsum(pw)
        rolls.append(float(freqs[np.searchsorted(cum, cum[-1] * 0.95)]))
    return dict(dur=dur, cent=float(np.mean(cents)), roll=float(np.mean(rolls)), head=head, steady=steady)


for p in sorted(glob.glob("D:/AI/Soundbox/sounds/*.wav")) + sorted(glob.glob("assets/audio/sfx_*.wav")):
    try:
        f = feats(p)
    except Exception as ex:
        print("skip", os.path.basename(p), ex)
        continue
    print("%-40s dur=%5.2f cent=%6.0f roll95=%6.0f head=%4.2f steady=%4.2f" % (
        os.path.basename(p)[:38], f["dur"], f["cent"], f["roll"], f["head"], f["steady"]))
