import wave, glob, os, struct
def info(p):
    with open(p,'rb') as f:
        head=f.read(64)
    riff=head[:4]; fmt=head[8:12]
    audio_fmt=struct.unpack('<H',head[20:22])[0]
    ch=struct.unpack('<H',head[22:24])[0]
    sr=struct.unpack('<I',head[24:28])[0]
    bits=struct.unpack('<H',head[34:36])[0]
    with wave.open(p,'rb') as w:
        try: dur=w.getnframes()/w.getframerate()
        except Exception: dur=-1
    return f"{os.path.basename(p)[:34]:36s} fmt={audio_fmt} ch={ch} sr={sr} bits={bits} dur={dur:5.2f}"
for p in sorted(glob.glob('assets/audio/sfx_*.wav'))[:4] + sorted(glob.glob('D:/AI/Soundbox/sounds/*.wav'))[:4]:
    print(info(p))
