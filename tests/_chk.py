import sys
sys.path.insert(0, ".")
import pygame
pygame.init()
s = pygame.image.load("assets/art/chef.png")
print("chef", s.get_size(), "frames", s.get_width() // 44)
for f in (0, 4, 8):
    fr = s.subsurface(pygame.Rect(f * 44, 0, 44, 64))
    xs = [x for x in range(44) if fr.get_at((x, 63)).a]
    print("frame", f, "bottom-row span", (min(xs), max(xs)) if xs else None)
    cols = [x for x in range(44) for y in range(64) if fr.get_at((x, y)).a]
    print("   width used", min(cols), "-", max(cols))
