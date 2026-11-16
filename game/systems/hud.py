"""Top strip, order tickets, bottom key hints. Nothing else on screen."""
from __future__ import annotations

import pygame

from core import config, text as textmod

BAR_H = config.BAR_TOP_H
COL_INK = config.color("ink")
COL_SLATE = config.color("slate")
COL_VOID = config.color("void")
COL_SILVER = config.color("silver")
COL_FOG = config.color("fog")
COL_CYAN = config.color("cyan")
COL_AMBER = config.color("amber")
COL_TOMATO = config.color("tomato")
COL_LIME = config.color("lime")
COL_PINK = config.color("pink")


def _patience_color(ratio):
    if ratio > 0.5:
        return COL_LIME
    if ratio > 0.25:
        return COL_AMBER
    return COL_TOMATO


def draw_top_bar(surface, world, elapsed, duration):
    pygame.draw.rect(surface, COL_INK, (0, 0, config.SCREEN_W, BAR_H))
    pygame.draw.line(surface, COL_SLATE, (0, BAR_H - 1), (config.SCREEN_W, BAR_H - 1))

    left = max(0.0, duration - elapsed)
    minutes = int(left) // 60
    seconds = int(left) % 60
    clock = "%d:%02d" % (minutes, seconds)
    urgent = left <= 30.0
    color = COL_TOMATO if urgent else COL_SILVER
    if urgent:
        pulse = 0.6 + 0.4 * abs(((elapsed * 2) % 2) - 1)
        color = (min(255, int(224 * pulse + 40)), 69, 47)
    textmod.shadow_text(surface, clock, (config.SCREEN_W // 2, 20), size=22,
                        color=color, bold=True, anchor="center")

    score = world.score
    if score is not None:
        # Live net purse: income minus the penalties already on the books.
        textmod.shadow_text(surface, "★ %d" % score.final_stars(), (config.SCREEN_W - 24, 17),
                            size=18, color=COL_AMBER, bold=True, anchor="midright")
        textmod.shadow_text(surface, "净收入", (config.SCREEN_W - 24, 32),
                            size=10, color=COL_FOG, anchor="midright")
        combo = score.combo
        if combo >= 2:
            mult = min(1.0 + 0.1 * combo, 1.5)
            size = 20 if combo >= 3 else 15
            textmod.shadow_text(surface, "x%.1f 连击 %d" % (mult, combo),
                                (config.SCREEN_W - 176, 20), size=size,
                                color=COL_PINK, bold=True, anchor="midright")


def draw_tickets(surface, world):
    orders = world.orders
    if orders is None:
        return
    x = 12
    y = BAR_H + 10
    for order in orders.active:
        card = pygame.Rect(x, y, 168, 54)
        pygame.draw.rect(surface, COL_INK, card)
        pygame.draw.rect(surface, COL_SLATE, card, 1)
        ratio = order.patience_ratio
        bar = pygame.Rect(card.x + 8, card.y + card.h - 14, card.w - 16, 7)
        pygame.draw.rect(surface, COL_VOID, bar)
        fill = bar.copy()
        fill.w = max(0, int(bar.w * ratio))
        pygame.draw.rect(surface, _patience_color(ratio), fill)
        from core import assets
        icon = assets.image("item_" + order.dish_id, (26, 26))
        surface.blit(icon, icon.get_rect(midleft=(card.x + 6, card.y + 22)))
        textmod.shadow_text(surface, order.name, (card.x + 36, card.y + 6), size=14,
                            color=COL_SILVER, bold=True)
        textmod.shadow_text(surface, "%d" % order.price, (card.right - 8, card.y + 6),
                            size=14, color=COL_AMBER, anchor="topright")
        textmod.shadow_text(surface, order.hint, (card.x + 36, card.y + 25), size=10,
                            color=COL_FOG)
        y += card.h + 8
    for index, order in enumerate(orders.queue[:2]):
        card = pygame.Rect(x, y + index * 26, 168, 20)
        textmod.shadow_text(surface, "排队 " + order.name, (card.x + 8, card.y + 2),
                            size=13, color=COL_FOG)


def draw_bottom_bar(surface, hints):
    top = config.SCREEN_H - config.BAR_BOTTOM_H
    pygame.draw.rect(surface, COL_INK, (0, top, config.SCREEN_W, config.BAR_BOTTOM_H))
    pygame.draw.line(surface, COL_SLATE, (0, top), (config.SCREEN_W, top))
    x = config.SCREEN_W // 2
    for key, label in hints:
        tag = "[%s] %s" % (key, label)
        textmod.shadow_text(surface, tag, (x, top + 20), size=15, color=COL_FOG,
                            anchor="center")
        x += 220
    # re-center the row
    return


def draw_hints(surface, hints):
    top = config.SCREEN_H - config.BAR_BOTTOM_H
    pygame.draw.rect(surface, COL_INK, (0, top, config.SCREEN_W, config.BAR_BOTTOM_H))
    pygame.draw.line(surface, COL_SLATE, (0, top), (config.SCREEN_W, top))
    widths = [textmod.render("[%s] %s" % (k, v), 15).get_width() for k, v in hints]
    gap = 46
    total = sum(widths) + gap * (len(hints) - 1)
    x = (config.SCREEN_W - total) // 2
    for (key, label), width in zip(hints, widths):
        textmod.shadow_text(surface, "[%s]" % key, (x, top + 20), size=15,
                            color=COL_CYAN, bold=True, anchor="midleft")
        key_w = textmod.render("[%s]" % key, 15, bold=True).get_width()
        textmod.shadow_text(surface, label, (x + key_w + 6, top + 20), size=15,
                            color=COL_FOG, anchor="midleft")
        x += width + gap


def draw_target_label(surface, cam, world, label):
    player = world.player
    if not label:
        return
    foot = cam.rect(player.foot)
    pos = (foot.centerx, foot.bottom - player.height * cam.zoom - 26)
    textmod.shadow_text(surface, label, pos, size=17, color=COL_CYAN, bold=True,
                        anchor="midbottom", shadow=(250, 246, 236))
