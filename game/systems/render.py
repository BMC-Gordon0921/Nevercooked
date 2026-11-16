"""The painter: floor, aim, sorted entities, occlusion fade, tosses, feedback.

Everything world-shaped goes through the camera, so the kitchen is drawn at
2x and the eye sees a counter, not a map.
"""
from __future__ import annotations

import math

import pygame

from core import assets, config
from game.entities.item import GroundItem
from game.entities.station import Station
from game.systems import interaction

FADE = config.TUNING["fade"]
COL_INK = config.color("ink")
COL_SLATE = config.color("slate")
COL_STEEL = config.color("steel")
COL_CYAN = config.color("cyan")
COL_FOG = config.color("fog")
COL_AMBER = config.color("amber")
COL_LABEL = (86, 96, 116)

_BG = {}
_SHADOWS = {}
_TILE = config.TILE


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


def draw_aim(surface, world, cam, ok=True, top=False):
    """Show the tile the cook is aiming at, before anything walks over it.

    The whole point is that aiming stops being invisible: without this the
    player presses F, nothing happens, and there is no way to tell whether the
    target was the tile in front, the tile underfoot, or nothing at all.

    Drawn in two passes: the tint goes under the furniture (a machine is 50-76
    tall and would otherwise swallow the whole marker), the outline and the F
    keycap go on top so the aim is legible even standing right at a counter.
    """
    player = world.player
    tile = interaction.facing_rect(player, world)
    rect = cam.rect(tile)
    tint = COL_CYAN if ok else COL_FOG
    if not top:
        layer = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        layer.fill((tint[0], tint[1], tint[2], 40 if ok else 22))
        surface.blit(layer, rect.topleft)
        return
    pygame.draw.rect(surface, tint, rect.inflate(-2, -2), 2 if ok else 1)
    # A keycap inside the tile says "this is what F acts on".
    cap = pygame.Rect(0, 0, 20, 20)
    cap.center = (rect.centerx, rect.bottom - 16)
    pygame.draw.rect(surface, COL_INK, cap, border_radius=4)
    pygame.draw.rect(surface, (tint[0], tint[1], tint[2]), cap, 1, border_radius=4)
    from core import text as textmod
    label = textmod.render("F", 13, tint if ok else COL_FOG, True)
    surface.blit(label, label.get_rect(center=cap.center))


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
            pygame.draw.rect(surface, COL_AMBER
                             if station.phase == Station.PHASE_COOK
                             else COL_CYAN, fill)
        if wants:
            missing = config.ITEMS[station.pending[0]]
            icon = assets.image(missing["icon"], (30, 30))
            icon.set_alpha(150)
            surface.blit(icon, icon.get_rect(midbottom=(foot.centerx + 24, top + 44)))


def draw_suggestions(surface, cam, world, stations):
    """A ! over every machine that would take what the cook is holding.

    Cheap, and it kills the read-the-JSON guessing game at the wok.
    """
    if not stations:
        return
    pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 260.0)
    for station in stations:
        foot = cam.rect(station.foot)
        top = foot.bottom - station.height * cam.zoom
        cx = foot.centerx + 22
        cy = top - 6
        radius = 9
        pygame.draw.circle(surface, COL_INK, (cx, cy + 1), radius + 1)
        pygame.draw.circle(surface, COL_AMBER, (cx, cy), radius)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), radius, 1)
        from core import text as textmod
        mark = textmod.render("!", 14, COL_INK, True)
        surface.blit(mark, mark.get_rect(center=(cx, cy - 1)))
        if pulse > 0.7:
            pygame.draw.circle(surface, COL_AMBER, (cx, cy), radius + 3, 1)


def draw_pulse(surface, cam, station):
    """Soft ring on the machine the guide wants next: findable at a glance."""
    if station is None:
        return
    foot = cam.rect(station.foot)
    phase = (pygame.time.get_ticks() % 900) / 900.0
    grow = int(6 + 10 * phase)
    alpha = int(190 * (1.0 - phase))
    halo = pygame.Surface((foot.w + grow * 2, foot.h + grow * 2), pygame.SRCALPHA)
    rect = halo.get_rect()
    pygame.draw.ellipse(halo, (*COL_CYAN[:3], alpha), rect, 3)
    surface.blit(halo, halo.get_rect(center=(foot.centerx, foot.bottom - 6)))
    top = foot.bottom - station.height * cam.zoom
    pygame.draw.line(surface, COL_CYAN, (foot.centerx, top - 26),
                     (foot.centerx, top - 6), 3)
    pygame.draw.polygon(surface, COL_CYAN,
                        ((foot.centerx - 7, top - 12), (foot.centerx + 7, top - 12),
                         (foot.centerx, top - 1)))


def draw_tosses(surface, world, cam):
    """The 0.18s arc of a thrown item: enough to read where it went."""
    if not world.tosses:
        return
    for toss in world.tosses:
        u = max(0.0, min(1.0, toss["t"] / 0.18))
        wx = toss["x0"] + (toss["x1"] - toss["x0"]) * u
        wy = toss["y0"] + (toss["y1"] - toss["y0"]) * u - math.sin(math.pi * u) * 26
        icon = assets.image(toss["icon"], (26, 26))
        surface.blit(icon, icon.get_rect(center=(cam.sx(wx), cam.sy(wy))))


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


def render(surface, world, cam, aim_ok=True, aim=True, suggestions=()):
    reset_fade(world)
    update_fade(world)
    draw_floor(surface, world, cam)
    if aim:
        draw_aim(surface, world, cam, aim_ok)
    draw_sorted(surface, world, cam)
    if aim:
        draw_aim(surface, world, cam, aim_ok, top=True)
    draw_suggestions(surface, cam, world, suggestions)
    draw_station_state(surface, world, cam)
    draw_player_busy(surface, cam, world)
    draw_tosses(surface, world, cam)
