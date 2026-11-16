import pygame
pygame.init()
s = pygame.image.load("assets/art/chef.png")
fr = s.subsurface(pygame.Rect(0,0,44,64)).copy()
seen = {}
out = []
for y in range(64):
    row = ""
    for x in range(44):
        c = fr.get_at((x,y))
        if c.a == 0:
            row += "."
        else:
            k = (c.r,c.g,c.b)
            if k not in seen:
                seen[k] = chr(ord("A") + len(seen))
            row += seen[k]
    out.append("%2d %s" % (y, row))
print("\n".join(out))
print(seen)
