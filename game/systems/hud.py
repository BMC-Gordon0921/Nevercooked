"""Top strip, order tickets, step banner, bottom key hints."""
from __future__ import annotations

import math

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
COL_WHITE = config.color("white")


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
    textmod.shadow_text(surface, clock, (config.SCREEN_W // 2, 20), size=24,
                        color=color, bold=True, anchor="center")

    score = world.score
    if score is not None:
        # Live net purse: income minus the penalties already on the books.
        purse = textmod.render("★ %d" % score.final_stars(), 24, COL_AMBER, True)
        surface.blit(purse, purse.get_rect(midright=(config.SCREEN_W - 20, 20)))
        combo = score.combo
        if combo >= 2:
            mult = min(1.0 + 0.1 * combo, 1.5)
            textmod.shadow_text(surface, "x%.1f 连击 %d" % (mult, combo),
                                (purse.get_width() and config.SCREEN_W - 40 - purse.get_width(), 20),
                                size=12, color=COL_PINK, bold=True, anchor="midright")


def _fit(value, size, max_width, bold=False):
    """Trim a string until it fits max_width at this layout size."""
    if not value or max_width <= 0:
        return value
    white = (255, 255, 255)
    if textmod.render(value, size, white, bold).get_width() <= max_width:
        return value
    cut = value
    while cut and textmod.render(cut + "..", size, white, bold).get_width() > max_width:
        cut = cut[:-1]
    return cut + ".."


def draw_tickets(surface, world, focus=None):
    orders = world.orders
    if orders is None:
        return
    from core import assets
    x = 12
    y = BAR_H + 10
    pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 300.0)
    for order in orders.active:
        card = pygame.Rect(x, y, 176, 56)
        chosen = order is focus
        pygame.draw.rect(surface, COL_INK, card, border_radius=4)
        if chosen:
            glow = pygame.Surface(card.inflate(8, 8).size, pygame.SRCALPHA)
            pygame.draw.rect(glow, (COL_CYAN[0], COL_CYAN[1], COL_CYAN[2],
                                    int(90 + 80 * pulse)),
                             glow.get_rect(), 3, border_radius=5)
            surface.blit(glow, card.inflate(8, 8).topleft)
            pygame.draw.rect(surface, COL_CYAN, card, 2, border_radius=4)
        else:
            pygame.draw.rect(surface, COL_SLATE, card, 1, border_radius=4)
        icon = assets.image("item_" + order.dish_id, (24, 24))
        surface.blit(icon, icon.get_rect(midleft=(card.x + 8, card.y + 16)))
        textmod.shadow_text(surface, order.name, (card.x + 38, card.y + 8), size=12,
                            color=COL_WHITE if chosen else COL_SILVER)
        textmod.shadow_text(surface, "%d" % order.price, (card.right - 8, card.y + 8),
                            size=12, color=COL_AMBER, bold=True, anchor="topright")
        left = int(round(max(0.0, order.time_left)))
        timer_col = COL_TOMATO if left <= 8 else (COL_AMBER if left <= 15 else COL_FOG)
        timer = "%ds" % left
        timer_w = textmod.render(timer, 12, timer_col, True).get_width()
        textmod.shadow_text(surface, timer, (card.right - 8, card.y + 28), size=12,
                            color=timer_col, bold=True, anchor="topright")
        hint = _fit(order.hint, 12, card.w - 46 - timer_w - 8)
        textmod.shadow_text(surface, hint, (card.x + 38, card.y + 28), size=12,
                            color=COL_FOG)
        ratio = order.patience_ratio
        bar = pygame.Rect(card.x + 8, card.y + card.h - 11, card.w - 16, 6)
        pygame.draw.rect(surface, COL_VOID, bar)
        fill = bar.copy()
        fill.w = max(0, int(bar.w * ratio))
        pygame.draw.rect(surface, _patience_color(ratio), fill)
        if chosen:
            textmod.shadow_text(surface, "▲ 引导", (card.x + 10, card.bottom + 4),
                                size=12, color=COL_CYAN, bold=True)
        y += card.h + (24 if chosen else 8)
    for index, order in enumerate(orders.queue[:2]):
        card = pygame.Rect(x, y + index * 22, 176, 20)
        textmod.shadow_text(surface, _fit("排队 " + order.name, 12, card.w - 16),
                            (card.x + 8, card.y + 2), size=12, color=COL_FOG)


def draw_bottom_bar(surface, hints):
    top = config.SCREEN_H - config.BAR_BOTTOM_H
    pygame.draw.rect(surface, COL_INK, (0, top, config.SCREEN_W, config.BAR_BOTTOM_H))
    pygame.draw.line(surface, COL_SLATE, (0, top), (config.SCREEN_W, top))
    x = config.SCREEN_W // 2
    for key, label in hints:
        tag = "[%s] %s" % (key, label)
        textmod.shadow_text(surface, tag, (x, top + 20), size=12, color=COL_FOG,
                            anchor="center")
        x += 220


def draw_hints(surface, hints):
    top = config.SCREEN_H - config.BAR_BOTTOM_H
    pygame.draw.rect(surface, COL_INK, (0, top, config.SCREEN_W, config.BAR_BOTTOM_H))
    pygame.draw.line(surface, COL_SLATE, (0, top), (config.SCREEN_W, top))
    widths = [textmod.render("[%s] %s" % (k, v), 12).get_width() for k, v in hints]
    gap = 38
    total = sum(widths) + gap * (len(hints) - 1)
    x = (config.SCREEN_W - total) // 2
    for (key, label), width in zip(hints, widths):
        textmod.shadow_text(surface, "[%s]" % key, (x, top + 20), size=12,
                            color=COL_CYAN, bold=True, anchor="midleft")
        key_w = textmod.render("[%s]" % key, 12, bold=True).get_width()
        textmod.shadow_text(surface, label, (x + key_w + 6, top + 20), size=12,
                            color=COL_FOG, anchor="midleft")
        x += width + gap


def draw_helper_status(surface, helper):
    """One line for the second cook: what the helper is on, or that it is idle.

    It sits on the floor line just above the hint bar, out of the way of the
    tickets on top; a paused helper turns amber so "why is nobody helping" has
    an answer on screen.
    """
    if helper is None:
        return
    tint = COL_AMBER if helper.paused else COL_CYAN
    text = textmod.render(helper.label(), 12, tint, True)
    chip = pygame.Rect(0, 0, text.get_width() + 18, 22)
    chip.bottomleft = (14, config.SCREEN_H - config.BAR_BOTTOM_H - 6)
    veil = pygame.Surface(chip.size, pygame.SRCALPHA)
    veil.fill((11, 14, 20, 176))
    surface.blit(veil, chip.topleft)
    pygame.draw.rect(surface, COL_SLATE, chip, 1, border_radius=6)
    surface.blit(text, text.get_rect(center=chip.center))


def draw_step_banner(surface, step, top=None):
    """The one line that answers "what now": stage mark, counter, verb, place.

    Returns the banner rect (or None) so the tutorial card can stack under it.
    """
    if not step or not step.get("label"):
        return None
    y = (BAR_H + 10) if top is None else top
    label = textmod.render(step["label"], 24, COL_WHITE)
    mark = textmod.render(step.get("mark", "做"), 24, COL_INK, True)
    counter = ""
    if step.get("index") and step.get("total"):
        counter = "%d/%d" % (step["index"], step["total"])
    badge_w, gap = 40, 12
    counter_w = textmod.render(counter, 12, COL_CYAN, True).get_width() + 18 if counter else 0
    width = min(config.SCREEN_W - 60, badge_w + gap + label.get_width() + 26 + counter_w)
    card = pygame.Rect(0, 0, width, 48)
    card.midtop = (config.SCREEN_W // 2, y)
    veil = pygame.Surface(card.size, pygame.SRCALPHA)
    veil.fill((11, 14, 20, 226))
    surface.blit(veil, card.topleft)
    pygame.draw.rect(surface, COL_CYAN, card, 2, border_radius=10)
    pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 260.0)
    badge = pygame.Rect(card.x + 8, card.y + 9, 30, 30)
    pygame.draw.rect(surface, COL_CYAN, badge, border_radius=8)
    pygame.draw.rect(surface, (255, 255, 255), badge, 1, border_radius=8)
    surface.blit(mark, mark.get_rect(center=badge.center))
    surface.blit(label, label.get_rect(midleft=(badge.right + gap, card.centery)))
    if counter:
        chip = textmod.render(counter, 12, COL_CYAN, True)
        surface.blit(chip, chip.get_rect(midright=(card.right - 12, card.centery)))
    if pulse > 0.6:
        pygame.draw.rect(surface, (COL_CYAN[0], COL_CYAN[1], COL_CYAN[2]),
                         card.inflate(6, 6), 1, border_radius=12)
    return card


def draw_tutorial(surface, text, top=None):
    """First-shift prompt: one line, out of the kitchen's way."""
    if not text:
        return None
    y = (BAR_H + 8) if top is None else top
    label = textmod.render(text, 24, COL_WHITE)
    hint = textmod.render("空格 跳过", 12, COL_FOG)
    width = max(label.get_width(), hint.get_width()) + 44
    card = pygame.Rect(0, 0, width, 54)
    card.midtop = (config.SCREEN_W // 2, y)
    veil = pygame.Surface(card.size, pygame.SRCALPHA)
    veil.fill((11, 14, 20, 214))
    surface.blit(veil, card.topleft)
    pygame.draw.rect(surface, COL_CYAN, card, 1, border_radius=8)
    surface.blit(label, label.get_rect(midtop=(card.centerx, card.y + 7)))
    surface.blit(hint, hint.get_rect(midbottom=(card.centerx, card.bottom - 5)))
    return card


def draw_guide(surface, label):
    """Bottom-left next-step line, kept for the paused/practice states."""
    if not label:
        return
    textmod.shadow_text(surface, "下一步 · " + label,
                        (14, config.SCREEN_H - config.BAR_BOTTOM_H + 20),
                        size=12, color=COL_CYAN, bold=True,
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
    main = textmod.render(label, 12, tint, True)
    sub = textmod.render(detail, 12, COL_FOG) if detail else None
    width = max(main.get_width(), sub.get_width() if sub is not None else 0) + 20
    chip = pygame.Rect(0, 0, width, 36 if sub is not None else 20)
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
        surface.blit(sub, sub.get_rect(midtop=(chip.centerx, chip.y + 20)))
