"""Build the contact sheet and the UI preview used to eyeball the pixel font.

    python tools/font/sheet.py

tests/font_sheet.png        whole charset at 1x, plus a 3x sample block
tests/font_ui_preview.png   real UI strings at their real layout sizes/colours

Also prints a size -> scale -> measured width table (pixel vs TTF) so the layout
impact of the snapping is visible as numbers, not guesses.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from core import config, pixelfont, text

TESTS = os.path.join(ROOT, "tests")
BG = (18, 20, 26)
PAPER = (240, 236, 226)


def _safe_console():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="backslashreplace")
        except (AttributeError, ValueError):
            pass


def contact_sheet(path):
    """Whole atlas at 1x, 48 glyphs per row, then a 3x sample block."""
    chars = [ch for ch in pixelfont.info().get("order", "") if ch.strip()] or sorted(pixelfont.charset())
    cols, cell = 48, 12
    rows = (len(chars) + cols - 1) // cols
    pad, block_top = 16, rows * cell + 40
    samples = ["欢闹厨房！", "NEVERCOOKED", "★ 128 x1.4", "碗底港·第七码头", "F 交互 ▶ 设置"]
    sample_h = 3 * 12 * len(samples) + 20 * len(samples)
    width = max(cols * cell + 2 * pad, 760)
    height = block_top + sample_h + 3 * 12 + 40
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    surf.fill(BG)

    for index, ch in enumerate(chars):
        col, row = index % cols, index // cols
        pygame.draw.rect(surf, (34, 38, 46), (pad + col * cell, pad + row * cell, cell - 1, cell - 1))
        surf.blit(pixelfont.render(ch, 1, PAPER), (pad + col * cell, pad + row * cell))
    pygame.draw.line(surf, (60, 66, 78), (pad, block_top - 20), (width - pad, block_top - 20))

    y = block_top
    for index, sample in enumerate(samples):
        col = (255, 214, 120) if index % 2 == 0 else (120, 226, 214)
        surf.blit(pixelfont.render(sample, 1, col), (pad, y))
        surf.blit(pixelfont.render(sample, 3, col), (pad + 320, y - 12))
        y += sample_h // len(samples)

    pygame.image.save(surf, path)
    return width, height, len(chars)


def ui_preview(path):
    """Real strings, real sizes, real colours - what the game will actually show.

    Geometry is copied from game/systems/hud.py and scenes/settings.py so a
    collision here is a collision in the game, not an artefact of the preview.
    """
    W, H = 1280, 720
    surf = pygame.Surface((W, H))
    surf.fill(BG)
    ink, fog, steel = config.color("ink"), config.color("fog"), config.color("steel")
    amber, cyan = config.color("amber"), config.color("cyan")
    flame, teal, white = config.color("flame"), config.color("teal"), config.color("white")

    # --- top bar (hud.draw_top_bar) -------------------------------------
    bar_h = getattr(config, "BAR_TOP_H", 40)
    pygame.draw.rect(surf, ink, (0, 0, W, bar_h))
    pygame.draw.line(surf, steel, (0, bar_h - 1), (W, bar_h - 1))
    text.shadow_text(surf, "2:47", (W // 2, 20), size=22, color=white, bold=True, anchor="center")
    text.shadow_text(surf, "★ 3", (W - 24, 17), size=18, color=amber, bold=True, anchor="midright")
    text.shadow_text(surf, "净收入", (W - 24, 32), size=10, color=fog, anchor="midright")
    text.shadow_text(surf, "x1.4 连击 4", (W - 176, 20), size=20, color=amber, bold=True,
                     anchor="center")

    # --- order ticket (hud.draw_tickets, 168x54) -------------------------
    card = pygame.Rect(40, 60, 168, 54)
    pygame.draw.rect(surf, ink, card)
    pygame.draw.rect(surf, cyan, card, 2)
    text.shadow_text(surf, "星尘炒饭", (card.x + 36, card.y + 6), size=14, color=white, bold=True)
    text.shadow_text(surf, "18", (card.right - 8, card.y + 6), size=14, color=amber, bold=True,
                     anchor="topright")
    text.shadow_text(surf, "星米>蒸>蛋+星尘>炒", (card.x + 36, card.y + 25), size=10, color=fog)
    text.shadow_text(surf, "92s", (card.right - 8, card.y + 25), size=11, color=fog,
                     anchor="topright")
    pygame.draw.rect(surf, (60, 200, 96), (card.x + 8, card.y + card.h - 14, card.w - 16, 7))
    text.shadow_text(surf, "▲ 引导", (card.x + 8, card.bottom + 3), size=11, color=cyan, bold=True)

    # --- key hints (hud.draw_hints) --------------------------------------
    hints = [("[F]", "交互"), ("[Q]", "抛出"), ("[Tab]", "设置")]
    x, top = 320, 78
    for key, label in hints:
        text.shadow_text(surf, key, (x, top), size=15, color=cyan, bold=True, anchor="midleft")
        key_w = text.render(key, 15, bold=True).get_width()
        text.shadow_text(surf, label, (x + key_w + 6, top), size=15, color=fog, anchor="midleft")
        x += 150

    # --- step banner (hud.draw_step_banner, 46px card) --------------------
    banner = pygame.Rect(0, 0, 560, 46)
    banner.midtop = (W // 2, 160)
    pygame.draw.rect(surf, (11, 14, 20), banner)
    pygame.draw.rect(surf, cyan, banner, 2, border_radius=10)
    label = text.render("去蒸笼 蒸 星米", 20, white, True)
    surf.blit(label, label.get_rect(midleft=(banner.x + 60, banner.centery)))
    chip = text.render("1/3", 13, cyan, True)
    surf.blit(chip, chip.get_rect(midright=(banner.right - 12, banner.centery)))

    # --- tutorial card (hud.draw_tutorial, 58px card) ---------------------
    body = text.render("站到蒸笼前按 F 跳上去，把它倒进", 16, white, True)
    hint = text.render("空格 跳过", 12, fog)
    tut = pygame.Rect(0, 0, max(body.get_width(), hint.get_width()) + 36, 58)
    tut.midtop = (W // 2, 216)
    pygame.draw.rect(surf, (11, 14, 20), tut)
    pygame.draw.rect(surf, cyan, tut, 1, border_radius=8)
    surf.blit(body, body.get_rect(midtop=(tut.centerx, tut.y + 8)))
    surf.blit(hint, hint.get_rect(midbottom=(tut.centerx, tut.bottom - 6)))

    # --- settings rows (scenes/settings.py) ------------------------------
    y = 320
    for index, (label_text, sub) in enumerate((("音效音量", "调低可以只听清设备提示音"),
                                               ("路径指示", "在厨房地面上画出通往下一站的粗箭头"))):
        chosen = index == 0
        if chosen:
            tag = text.render("▶", 14, cyan, True)
            surf.blit(tag, tag.get_rect(midleft=(96, y)))
        text.shadow_text(surf, label_text, (140, y - 8), size=19, color=white if chosen else steel,
                         bold=chosen, anchor="midleft")
        text.shadow_text(surf, sub, (140, y + 14), size=12, color=fog, anchor="midleft")
        y += 78
    text.shadow_text(surf, "↑↓ 选择    ←→ 调整    Enter / Esc 返回", (W // 2, 470), size=15,
                     color=fog, anchor="center")

    # --- title wordmark (scenes/title.py, 84px) --------------------------
    head, bang = "欢闹厨房", "！"
    w_head = text.render(head, 84, flame, bold=True).get_width()
    w_bang = text.render(bang, 84, teal, bold=True).get_width()
    x_head = (W - (w_head + w_bang)) // 2
    text.shadow_text(surf, head, (x_head, 520), size=84, color=flame, bold=True)
    text.shadow_text(surf, bang, (x_head + w_head, 520), size=84, color=teal, bold=True)
    text.shadow_text(surf, "N E V E R C O O K E D !", (W // 2, 640), size=22, color=(60, 70, 92),
                     bold=True, anchor="center")
    text.shadow_text(surf, "碗底港 · 第七码头  ·  三分钟一局", (W // 2, 682), size=13, color=fog,
                     anchor="center")

    pygame.image.save(surf, path)
    return W, H


def width_table():
    strings = [
        ("[F] 交互", 15, True),
        ("星米>蒸>蛋+星尘>炒", 10, False),
        ("音效音量", 19, False),
        ("下一步 · 把炒饭端到窗口", 20, True),
        ("设置", 34, True),
        ("收摊结算", 40, True),
        ("欢闹厨房", 84, True),
        ("欢闹厨房！", 84, True),
    ]
    rows = []
    for value, size, bold in strings:
        pixel = text.render(value, size, (255, 255, 255), bold)
        ttf = text.font(size, bold).render(value, True, (255, 255, 255))
        delta = 100.0 * (pixel.get_width() - ttf.get_width()) / max(1, ttf.get_width())
        rows.append((size, pixelfont.scale_for(size), pixel.get_width(), pixel.get_height(),
                     ttf.get_width(), "%+.0f%%" % delta, value))
    return rows


def main():
    _safe_console()
    pygame.init()
    pygame.font.init()
    if not pixelfont.ready():
        raise SystemExit("atlas missing: run tools/font/bake_atlas.py first")
    sheet = os.path.join(TESTS, "font_sheet.png")
    preview = os.path.join(TESTS, "font_ui_preview.png")
    print("sheet  : %dx%d, %d glyphs -> %s" % (*contact_sheet(sheet), os.path.relpath(sheet, ROOT)))
    print("preview: %dx%d -> %s" % (*ui_preview(preview), os.path.relpath(preview, ROOT)))
    print("size scale  pixel      ttf   delta  string (ascii-escaped: console is GBK)")
    for size, scale, px_w, px_h, ttf_w, delta, value in width_table():
        print("%4d %5d %4dx%-3d %4d %7s  %s"
              % (size, scale, px_w, px_h, ttf_w, delta,
                 value.encode("unicode_escape").decode("ascii")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
