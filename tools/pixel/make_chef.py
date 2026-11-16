import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pygame

from core import config
from tools.pixel.chef_art import chef_frame

ART = config.ART_DIR
ORDER = [("down", i) for i in range(4)] + [("up", i) for i in range(4)] + [("side", i) for i in range(4)]


def main():
    pygame.init()
    surf = pygame.Surface((44 * 12, 64), pygame.SRCALPHA)
    for i, (dirn, step) in enumerate(ORDER):
        art = chef_frame(dirn, step)
        assert art.s.get_size() == (44, 64)
        surf.blit(art.s, (i * 44, 0))
    pygame.image.save(surf, os.path.join(ART, "chef.png"))
    print("chef.png", surf.get_size())
    for scale, path in ((2, "tests/_chef_2x.png"), (4, "tests/_chef_strip.png")):
        strip = pygame.Surface((44 * 12 * scale, 64 * scale), pygame.SRCALPHA)
        strip.fill((233, 220, 194))
        strip.blit(pygame.transform.scale(surf, (44 * 12 * scale, 64 * scale)), (0, 0))
        pygame.image.save(strip, path)


if __name__ == "__main__":
    main()
