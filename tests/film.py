"""Run the bot and drop a frame every 20s, so motion bugs show up on film."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame

import bot


def main():
    pygame.init()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "film")
    os.makedirs(out, exist_ok=True)
    for name in os.listdir(out):
        os.remove(os.path.join(out, name))
    bot.run(200, "film", film=out)
    print("frames:", sorted(os.listdir(out)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
