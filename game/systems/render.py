"""The painter: floor, path, aim, sorted entities, occlusion fade, tosses.

Everything world-shaped goes through the camera, so the kitchen is drawn at
2x and the eye sees a counter, not a map.

Guidance is drawn in three layers on purpose: the thick arrow path sits on the
floor (under the cook's feet), the goal brackets go above the furniture, and the
pulse arrow hovers over the machine -- so a player can follow the route without
hunting for a 3px ring that the counter hides.
"""
from __future__ import annotations

import math

import pygame

from core import assets, config
from game.entities.item import GroundItem
from game.entities.station import Station
from game.systems import interaction, nav

FADE = config.TUNING["fade"]
COL_INK = config.color("ink")
COL_SLATE = config.color("slate")
COL_STEEL = config.color("steel")
COL_CYAN = config.color("cyan")
COL_FOG = config.color("fog")
COL_AMBER = config.color("amber")
COL_GOLD = config.color("amber_light") if "amber_light" in config.PALETTE else COL_AMBER
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


# -- guidance ------------------------------------------------------------

def _path_points(world, cam, cells):
    """Cook's feet -> every tile centre, in screen space."""
    player = world.player
    pts = [(cam.sx(player.foot.centerx), cam.sy(player.foot.bottom - 10))]
    for cell in cells:
        cx, cy = nav.center_of(cell)
        point = (cam.sx(cx), cam.sy(cy + 6))
        if abs(point[0] - pts[-1][0]) + abs(point[1] - pts[-1][1]) >= 8:
            pts.append(point)
    return pts


def _chevrons(layer, pts, tint, step=34.0, size=11):
    """Arrow heads marching along the route: direction is readable at a glance."""
    if len(pts) < 2:
        return
    colour = (tint[0], tint[1], tint[2], 238)
    travelled = step * 0.5
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        if seg < 1.0:
            continue
        ux, uy = (x1 - x0) / seg, (y1 - y0) / seg
        while travelled <= seg:
            cx, cy = x0 + ux * travelled, y0 + uy * travelled
            tip = (cx + ux * size, cy + uy * size)
            left = (cx - ux * size * 0.35 - uy * size * 0.8,
                    cy - uy * size * 0.35 + ux * size * 0.8)
            right = (cx - ux * size * 0.35 + uy * size * 0.8,
                     cy - uy * size * 0.35 - ux * size * 0.8)
            pygame.draw.polygon(layer, colour, (tip, left, right))
            travelled += step
        travelled -= seg


def draw_path(surface, world, cam, cells, tint=None):
    """A continuous thick arrow path from the cook to the goal tile.

    Drawn on its own translucent layer and blitted under the entities, so the
    cook and the machines stand on the route instead of hiding it.
    """
    if not cells:
        return
    tint = tint or COL_CYAN
    pts = _path_points(world, cam, cells)
    if len(pts) < 2:
        return
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pygame.draw.lines(layer, (tint[0], tint[1], tint[2], 54), False, pts, 30)
    pygame.draw.lines(layer, (tint[0], tint[1], tint[2], 104), False, pts, 20)
    pygame.draw.lines(layer, (min(255, tint[0] + 40), min(255, tint[1] + 40),
                              min(255, tint[2] + 40), 74), False, pts, 8)
    _chevrons(layer, pts, tint)
    surface.blit(layer, (0, 0))


def draw_goal_tile(surface, cam, world, station, tint=None):
    """Corner brackets on the goal tile: reads even when a 76px oven fills it."""
    if station is None:
        return
    tint = tint or COL_CYAN
    rect = cam.rect(station.reach)
    pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 220.0)
    arm = 20
    thick = 4
    for (cx, cy, sx, sy) in ((rect.left, rect.top, 1, 1),
                             (rect.right, rect.top, -1, 1),
                             (rect.left, rect.bottom, 1, -1),
                             (rect.right, rect.bottom, -1, -1)):
        pygame.draw.line(surface, COL_INK, (cx, cy), (cx + sx * (arm + 2), cy), thick + 2)
        pygame.draw.line(surface, COL_INK, (cx, cy), (cx, cy + sy * (arm + 2)), thick + 2)
        pygame.draw.line(surface, tint, (cx, cy), (cx + sx * arm, cy), thick)
        pygame.draw.line(surface, tint, (cx, cy), (cx, cy + sy * arm), thick)
    ring = pygame.Surface((rect.w + 18, rect.h + 18), pygame.SRCALPHA)
    pygame.draw.ellipse(ring, (tint[0], tint[1], tint[2], int(120 + 70 * pulse)),
                        ring.get_rect(), 3)
    surface.blit(ring, ring.get_rect(center=rect.center))


def draw_pulse(surface, cam, station):
    """Arrow over the machine the guide wants next, clamped into the viewport.

    The kitchen is 320px tall in a 640x320 view, so a crate in the top row has
    its sprite top *above* the camera: the arrow is pinned to the top edge with
    a stub instead of being drawn off-screen.
    """
    if station is None:
        return
    foot = cam.rect(station.foot)
    busy = (pygame.time.get_ticks() % 760) / 760.0
    wob = int(math.sin(pygame.time.get_ticks() / 190.0) * 4)
    top = foot.bottom - station.height * cam.zoom
    tip_y = max(config.BAR_TOP_H + 46, top - 18 + wob)
    bob = int(6 * abs(math.sin(pygame.time.get_ticks() / 260.0)))
    cx = foot.centerx
    pygame.draw.polygon(surface, COL_INK,
                        ((cx - 14, tip_y - 24 - bob), (cx + 14, tip_y - 24 - bob),
                         (cx, tip_y - bob + 2)))
    pygame.draw.polygon(surface, COL_CYAN,
                        ((cx - 11, tip_y - 22 - bob), (cx + 11, tip_y - 22 - bob),
                         (cx, tip_y - 3 - bob)))
    alpha = int(90 + 90 * (1.0 - busy))
    halo = pygame.Surface((80, 80), pygame.SRCALPHA)
    pygame.draw.ellipse(halo, (COL_CYAN[0], COL_CYAN[1], COL_CYAN[2], alpha),
                        halo.get_rect().inflate(-10, -10), 4)
    if tip_y > config.BAR_TOP_H + 54:
        surface.blit(halo, halo.get_rect(center=(cx, tip_y - 2)))


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


# -- entities -----------------------------------------------------------

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
        cy = max(config.BAR_TOP_H + 30, top - 6)
        radius = 9
        pygame.draw.circle(surface, COL_INK, (cx, cy + 1), radius + 1)
        pygame.draw.circle(surface, COL_AMBER, (cx, cy), radius)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), radius, 1)
        from core import text as textmod
        mark = textmod.render("!", 14, COL_INK, True)
        surface.blit(mark, mark.get_rect(center=(cx, cy - 1)))
        if pulse > 0.7:
            pygame.draw.circle(surface, COL_AMBER, (cx, cy), radius + 3, 1)


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


def render(surface, world, cam, aim_ok=True, aim=True, suggestions=(),
           path=None, goal=None, show_path=True):
    reset_fade(world)
    update_fade(world)
    draw_floor(surface, world, cam)
    if show_path and path:
        draw_path(surface, world, cam, path)
    if aim:
        draw_aim(surface, world, cam, aim_ok)
    draw_sorted(surface, world, cam)
    if goal is not None:
        draw_goal_tile(surface, cam, world, goal)
    if aim:
        draw_aim(surface, world, cam, aim_ok, top=True)
    draw_suggestions(surface, cam, world, suggestions)
    draw_station_state(surface, world, cam)
    draw_player_busy(surface, cam, world)
    draw_tosses(surface, world, cam)
    if goal is not None:
        draw_pulse(surface, cam, goal)
