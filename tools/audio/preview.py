"""One file to audition every cue: 0.75 s of silence between sounds."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import wavio  # noqa: E402

ORDER = ["sfx_pickup", "sfx_place", "sfx_chop", "sfx_sizzle", "sfx_steam", "sfx_oven",
         "sfx_ready", "sfx_bell", "sfx_order", "sfx_fail", "sfx_tick", "sfx_trash"]
AUDIO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "audio"))


def main():
    sr = 44100
    gap = np.zeros(int(sr * 0.75), dtype=np.float32)
    chunks = []
    for name in ORDER:
        a, file_sr = wavio.load(os.path.join(AUDIO, name + ".wav"))
        assert file_sr == sr, (name, file_sr)
        mono = a.mean(axis=1)
        chunks.append(mono)
        chunks.append(gap)
    out = np.concatenate(chunks)
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tests",
                                        "audio_preview.wav"))
    wavio.save_mono(path, out, sr, peak_db=-1.0)
    print("wrote %s  %.1fs  (%s)" % (path, len(out) / sr, " → ".join(ORDER)))


if __name__ == "__main__":
    main()
