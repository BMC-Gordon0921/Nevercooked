import sys
sys.stdout.reconfigure(errors="backslashreplace")
import pygame, numpy as np
pygame.init(); pygame.font.init()
def art(s):
    a = pygame.surfarray.array3d(s)[:,:,0].T
    return "\n".join("".join("#" if v else "." for v in row) for row in a)
f = pygame.font.Font(r"C:\Windows\Fonts\NotoSansSC-VF.ttf", 12)
for ch in ["\u25b6", "\u2605", "\u2192", "\u2460"]:
    s = f.render(ch, False, (255,255,255))
    a = pygame.surfarray.array3d(s)[:,:,0]
    xi, yi = np.nonzero(a)
    print(hex(ord(ch)), "size", s.get_size(), "adv", f.size(ch)[0], "ink rows", (int(yi.min()), int(yi.max())) if len(yi) else None, "ink cols", (int(xi.min()), int(xi.max())) if len(xi) else None)
    print(art(s))
han = []
for hi in range(0xB0, 0xF8):
    for lo in range(0xA1, 0xFF):
        try:
            ch = bytes([hi, lo]).decode("gb2312")
        except UnicodeDecodeError:
            continue
        han.append(ch)
print("gb2312 hanzi", len(han), han[:5], han[-3:])
