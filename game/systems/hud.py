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
        left = int(round(max(0.0, order.time_left)))
        timer_col = COL_TOMATO if left <= 8 else (COL_AMBER if left <= 15 else COL_FOG)
        textmod.shadow_text(surface, "%ds" % left, (card.right - 8, card.y + 25),
                            size=11, color=timer_col, anchor="topright")
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


def draw_tutorial(surface, text):
    """First-shift prompt: one line, top centre, out of the kitchen's way."""
    if not text:
        return
    label = textmod.render(text, 16, config.color("white"), True)
    hint = textmod.render("空格 跳过", 12, config.color("fog"))
    width = max(label.get_width(), hint.get_width()) + 36
    card = pygame.Rect(0, 0, width, 58)
    card.midtop = (config.SCREEN_W // 2, BAR_H + 8)
    veil = pygame.Surface(card.size, pygame.SRCALPHA)
    veil.fill((11, 14, 20, 214))
    surface.blit(veil, card.topleft)
    pygame.draw.rect(surface, config.color("cyan"), card, 1, border_radius=8)
    surface.blit(label, label.get_rect(midtop=(card.centerx, card.y + 8)))
    surface.blit(hint, hint.get_rect(midbottom=(card.centerx, card.bottom - 6)))


def draw_guide(surface, label):
    """Bottom-left next-step line: the recipe turned into a walking order."""
    if not label:
        return
    textmod.shadow_text(surface, "下一步 · " + label,
                        (14, config.SCREEN_H - config.BAR_BOTTOM_H + 20),
                        size=14, color=config.color("cyan"), bold=True,
                        anchor="midleft", shadow=(11, 14, 20))


def draw_target_label(surface, cam, world, label, detail=None, ok=True):
    """One place for the prompt: what F does, and -- when it cannot -- why.

    It rides above the cook's hat on a dark chip.  A plain drop shadow was fine
    on the floor and unreadable the moment the prompt landed on a bright enamel
    counter, which is where it lands most of the time.
    """
    if not label:
        return
    player = world.player
    foot = cam.rect(player.foot)
    tint = COL_CYAN if ok else COL_AMBER
    main = textmod.render(label, 15, tint, True)
    sub = textmod.render(detail, 12, COL_FOG) if detail else None
    width = max(main.get_width(), sub.get_width() if sub is not None else 0) + 18
    chip = pygame.Rect(0, 0, width, 40 if sub is not None else 24)
    chip.midbottom = (foot.centerx, foot.bottom - player.height * cam.zoom - 4)
    chip.clamp_ip(pygame.Rect(6, BAR_H + 6,
                              config.SCREEN_W - 12,
                              config.SCREEN_H - BAR_H - config.BAR_BOTTOM_H - 12))
    veil = pygame.Surface(chip.size, pygame.SRCALPHA)
    veil.fill((11, 14, 20, 172))
    surface.blit(veil, chip.topleft)
    pygame.draw.rect(surface, tint, chip, 1, border_radius=6)
    surface.blit(main, main.get_rect(midtop=(chip.centerx, chip.y + 4)))
    if sub is not None:
        surface.blit(sub, sub.get_rect(midtop=(chip.centerx, chip.y + 26)))
