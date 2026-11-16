import wave, numpy as np, os, glob
def load(p):
    with wave.open(p,'rb') as w:
        n=w.getnframes(); ch=w.getnchannels(); sr=w.getframerate()
        raw=w.readframes(n)
    a=np.frombuffer(raw,dtype='<i2').astype(np.float32)/32768.0
    if ch>1: a=a.reshape(-1,ch).mean(axis=1)
    return a, sr
for p in sorted(glob.glob('assets/audio/sfx_*.wav')):
    a,sr=load(p)
    a=a/max(1e-9,np.abs(a).max())
    n=len(a); win=2048; hop=512
    freqs=np.fft.rfftfreq(win,1/sr)
    cents=[]; roll=[]
    for i in range(0,max(1,n-win),hop):
        seg=a[i:i+win]*np.hanning(win)
        mag=np.abs(np.fft.rfft(seg))+1e-12
        pw=mag**2
        cents.append(float((freqs*pw).sum()/pw.sum()))
        cum=np.cumsum(pw); roll.append(float(freqs[np.searchsorted(cum,cum[-1]*0.95)]))
    # envelope flatness: how steady is the level (noise = steady)
    env=np.array([np.sqrt((a[i:i+hop]**2).mean()) for i in range(0,n-hop,hop)])
    env=env/(env.max()+1e-9)
    steady=float(env.std()/ (env.mean()+1e-9))
    # tonality: peak bin vs median
    spec=np.abs(np.fft.rfft(a*np.hanning(len(a))))
    peakiness=float(spec.max()/(np.median(spec)+1e-9))
    print(f"{os.path.basename(p):18s} {n/sr:5.2f}s centroid={np.mean(cents):6.0f}Hz roll95={np.mean(roll):5.0f}Hz env_std={steady:4.2f} peak/med={peakiness:7.1f}")
