"""Minimal WAV read/write: 16-bit, 24-bit and 32-bit float PCM -> float32 stereo."""
import struct
import numpy as np


def _fmt(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[0:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("not a wav: %s" % path)
    pos = 12
    fmt = None
    payload = None
    while pos + 8 <= len(data):
        cid = data[pos:pos + 4]
        size = struct.unpack("<I", data[pos + 4:pos + 8])[0]
        body = data[pos + 8:pos + 8 + size]
        if cid == b"fmt ":
            fmt = body
        elif cid == b"data":
            payload = body
        pos += 8 + size + (size & 1)
    if fmt is None or payload is None:
        raise ValueError("missing chunks: %s" % path)
    audio_fmt, ch, sr = struct.unpack("<HHI", fmt[:8])
    bits = struct.unpack("<H", fmt[14:16])[0]
    return audio_fmt, ch, sr, bits, payload


def load(path):
    audio_fmt, ch, sr, bits, raw = _fmt(path)
    if audio_fmt == 3 or bits == 32:
        a = np.frombuffer(raw, dtype="<f4").astype(np.float32)
    elif bits == 16:
        a = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    elif bits == 24:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        v = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        v = np.where(v >= 1 << 23, v - (1 << 24), v)
        a = (v / float(1 << 23)).astype(np.float32)
    else:
        raise ValueError("unsupported bits: %d" % bits)
    if ch > 1:
        a = a.reshape(-1, ch)
    else:
        a = a.reshape(-1, 1)
    return a, sr


def save_mono(path, a, sr=44100, peak_db=None):
    """peak_db=None keeps the caller's gain (use it when loudness is already set)."""
    a = np.asarray(a, dtype=np.float32)
    if peak_db is not None:
        peak = float(np.abs(a).max()) or 1.0
        a = a * (10 ** (peak_db / 20.0) / peak)
    pcm = np.clip(a, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype("<i2")
    stereo = np.repeat(pcm.reshape(-1, 1), 2, axis=1).reshape(-1)
    with open(path, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", 36 + stereo.nbytes) + b"WAVE")
        f.write(b"fmt " + struct.pack("<IHHIIHH", 16, 1, 2, sr, sr * 4, 4, 16))
        f.write(b"data" + struct.pack("<I", stereo.nbytes) + stereo.tobytes())
