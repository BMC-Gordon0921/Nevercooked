"""The painter: floor, sorted entities, occlusion fade, floating feedback.

Everything world-shaped goes through the camera, so the kitchen is drawn at
2x and the eye sees a counter, not a map.
"""
from __future__ import annotations

import pygame

from core import assets, config
from game.entities.item import GroundItem
from game.entities.station import Station

FADE = config.TUNING["fade"]
COL_INK = config.color("ink")
COL_SLATE = config.color("slate")
COL_STEEL = config.color("steel")
COL_CYAN = config.color("cyan")
COL_LABEL = (86, 96, 116)

_BG = {}
_SHADOWS = {}


def _shadow(width):
    key = max(12, int(width))
    surf = _SHADOWS.get(key)
    if surf is None:
        surf = pygame.Surface((key, max(8, key // 3)), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, 80), surf.get_rect())
        _SHADOWS[key] = surf
    return surf


def _background(world):
    """Deck, floor and trim are static: bake them once per world, at world scale."""
    key = id(world)
    cached = _BG.get(key)
    if cached is not None:
        return cached
    bounds = world.bounds
    surf = pygame.Surface((bounds.w, bounds.h), pygame.SRCALPHA)
    tiles = config.TILE
    deck_a = assets.image("deck_a")
    deck_b = assets.image("deck_b")
    floor_a = assets.image("floor_a")
    floor_b = assets.image("floor_b")
    for ty in range(0, bounds.h // tiles + 1):
        for tx in range(0, bounds.w // tiles + 1):
            surf.blit(deck_a if (tx + ty) % 2 == 0 else deck_b, (tx * tiles, ty * tiles))
    room = world.room
    inner = room.inflate(-tiles * 2, -tiles * 2)
    ox, oy = inner.x - bounds.x, inner.y - bounds.y
    for ty in range(inner.h // tiles):
        for tx in range(inner.w // tiles):
            surf.blit(floor_a if (tx + ty) % 2 == 0 else floor_b,
                      (ox + tx * tiles, oy + ty * tiles))
    trim = room.inflate(-tiles, -tiles).move(-bounds.x, -bounds.y)
    pygame.draw.rect(surf, config.hex_rgb("#1E3B52"), trim, 2)
    pygame.draw.rect(surf, config.hex_rgb("#0B1220"), trim.inflate(6, 6), 1)
    _BG[key] = (surf, bounds.topleft)
    return _BG[key]


def draw_floor(surface, world, cam):
    bg, pos = _background(world)
    surface.blit(cam.sprite(bg), (cam.sx(pos[0]), cam.sy(pos[1])))


def _blit_entity(surface, cam, entity, alpha):
    sprite = entity.sprite
    if sprite is None:
        return
    rect = cam.rect(entity.sprite_rect())
    foot = cam.rect(entity.foot)
    shade = _shadow(foot.w + 12)
    surface.blit(shade, shade.get_rect(center=(foot.centerx, foot.bottom - 4)))
    big = cam.sprite(sprite)
    if alpha >= 255:
        surface.blit(big, rect)
    else:
        copy = big.copy()
        copy.set_alpha(alpha)
        surface.blit(copy, rect)


def update_fade(world):
    """Anything tall that covers the player turns translucent."""
    player = world.player
    prow = player.sprite_rect()
    min_h = FADE["min_height"]
    for entity in world.entities:
        if entity is player or entity.alpha_target != 255:
            continue
        if entity.height < min_h:
            continue
        if entity.foot.bottom <= player.foot.bottom:
            continue
        if entity.sprite_rect().colliderect(prow):
            entity.alpha_target = FADE["alpha"]


def reset_fade(world):
    for entity in world.entities:
        entity.alpha_target = 255


def draw_sorted(surface, world, cam):
    drawable = [e for e in world.entities if e.sprite is not None and e.alive]
    drawable.sort(key=lambda e: e.sort_key)
    for entity in drawable:
        _blit_entity(surface, cam, entity, int(entity.alpha))


def _label(surface, value, pos, size=13, color=COL_LABEL, bold=False, anchor="midtop"):
    from core import text as textmod

    textmod.shadow_text(surface, value, pos, size=size, color=color, bold=bold,
                        anchor=anchor, shadow=(250, 246, 236))


def draw_station_state(surface, world, cam):
    """Slot contents, progress and names sit above each machine, never hidden."""
    for station in world.stations:
        foot = cam.rect(station.foot)
        top = foot.bottom - station.height * cam.zoom
        if station.stype != "crate":
            _label(surface, station.label, (foot.centerx, foot.bottom + 6))
        if station.stype == "crate" and station.dispense:
            icon = assets.image(config.ITEMS[station.dispense]["icon"], (38, 38))
            surface.blit(icon, icon.get_rect(midbottom=(foot.centerx, top - 2)))
        wants = station.phase == Station.PHASE_ADD and station.pending
        if station.slot is not None:
            offset = -22 if wants else 0
            icon = assets.image(station.slot.icon, (40, 40))
            surface.blit(icon, icon.get_rect(midbottom=(foot.centerx + offset, top + 46)))
        ratio = station.progress
        if ratio > 0:
            bar = pygame.Rect(foot.centerx - 30, top - 12, 60, 7)
            pygame.draw.rect(surface, COL_INK, bar.inflate(4, 4))
            fill = bar.copy()
            fill.width = max(1, int(bar.width * min(1.0, ratio)))
            pygame.draw.rect(surface, config.color("amber")
                             if station.phase == Station.PHASE_COOK
                             else config.color("cyan"), fill)
        if wants:
            missing = config.ITEMS[station.pending[0]]
            icon = assets.image(missing["icon"], (30, 30))
            icon.set_alpha(150)
            surface.blit(icon, icon.get_rect(midbottom=(foot.centerx + 24, top + 44)))


def draw_target(surface, cam, world, target, label):
    if target is None:
        return
    if isinstance(target, GroundItem):
        wx, wy = target.foot.centerx, target.foot.top - 14
    else:
        wx, wy = target.foot.centerx, target.foot.top - target.height - 6
    cx, cy = cam.sx(wx), cam.sy(wy)
    pulse = 1.0 + 0.12 * pygame.time.get_ticks() / 1000.0 % 1.0
    color = COL_CYAN if label else config.color("fog")
    size = int(7 * pulse) + 6
    pygame.draw.polygon(surface, (12, 16, 24),
                        [(cx, cy + size + 2), (cx - size - 2, cy - size),
                         (cx + size + 2, cy - size)])
    pygame.draw.polygon(surface, color,
                        [(cx, cy + size), (cx - size, cy - size), (cx + size, cy - size)])


def draw_hand(surface, cam, world):
    player = world.player
    if player.hand is None:
        return
    foot = cam.rect(player.foot)
    # Held item rides beside the torso, not on top of it: drawn over the chest
    # it reads as a floating sign rather than something in the cook's hands.
    icon = assets.image(player.hand.icon, (32, 32))
    surface.blit(icon, icon.get_rect(midbottom=(foot.centerx + 40, foot.bottom - 30)))


def draw_player_busy(surface, cam, world):
    player = world.player
    if player.busy <= 0 or player.busy_total <= 0:
        return
    ratio = max(0.0, min(1.0, 1.0 - player.busy / player.busy_total))
    foot = cam.rect(player.foot)
    top = foot.bottom - player.height * cam.zoom
    bar = pygame.Rect(foot.centerx - 20, top - 14, 40, 6)
    pygame.draw.rect(surface, COL_INK, bar.inflate(4, 4))
    fill = bar.copy()
    fill.width = max(1, int(bar.width * ratio))
    pygame.draw.rect(surface, config.color("cyan"), fill)


def draw_popups(surface, cam, world):
    from core import text as textmod

    for popup in world.popups:
        alpha = int(255 * min(1.0, popup["life"] / max(0.01, popup["max"]) * 1.6))
        alpha = max(0, min(255, alpha))
        label = textmod.render(popup["text"], 18, popup["color"], True)
        shade = textmod.render(popup["text"], 18, (20, 24, 32), True)
        out = pygame.Surface((label.get_width() + 2, label.get_height() + 2),
                             pygame.SRCALPHA)
        out.blit(shade, (2, 2))
        out.blit(label, (0, 0))
        out.set_alpha(alpha)
        surface.blit(out, out.get_rect(midbottom=(cam.sx(popup["x"]), cam.sy(popup["y"]))))


def render(surface, world, cam):
    reset_fade(world)
    update_fade(world)
    draw_floor(surface, world, cam)
    draw_sorted(surface, world, cam)
    draw_station_state(surface, world, cam)
    draw_player_busy(surface, cam, world)
