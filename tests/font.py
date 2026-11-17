"""Headless regression for the pixel-font engine.

    python tests/font.py

Checks that the baked atlas covers everything the game prints, that every
rendered pixel is fully opaque or fully transparent (no antialiasing), and that
scaling is exact integer multiplication.  Prints "FONT: PASS" on success.
"""
from __future__ import annotations

import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import numpy as np
import pygame

from core import pixelfont, text

FAILURES = []


def _safe_console():
    """The Windows console is GBK; a glyph it cannot encode must not crash a test."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="backslashreplace")
        except (AttributeError, ValueError):
            pass


def check(name, ok, detail=""):
    if ok:
        print("  ok   %s" % name)
    else:
        print("  FAIL %s %s" % (name, detail))
        FAILURES.append(name)
    return ok


def _bake_module():
    """The corpus scanner lives in the bake tool; reuse it, do not duplicate it."""
    path = os.path.join(ROOT, "tools", "font", "bake_atlas.py")
    spec = importlib.util.spec_from_file_location("bake_atlas", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def alpha_values(surface):
    return sorted({int(v) for v in np.unique(pygame.surfarray.array_alpha(surface))})


def main():
    _safe_console()
    pygame.init()
    pygame.font.init()

    bake = _bake_module()
    corpus, sources = bake.collect_corpus(ROOT)
    charset = pixelfont.charset()

    print("atlas   : %d glyphs, cell %dx%d, line height %d"
          % (len(charset), pixelfont.info().get("cell", 0), pixelfont.info().get("cell_h", 0),
             pixelfont.line_height(1)))
    print("corpus  : %d chars from %d files" % (len(corpus), len(sources)))

    check("atlas loaded", pixelfont.ready())

    # 1. coverage -------------------------------------------------------
    missing = sorted(corpus - charset)
    check("corpus fully covered", not missing,
          "missing %r - rerun python tools/font/bake_atlas.py" % (missing,))
    ascii_missing = [chr(c) for c in range(32, 127) if chr(c) not in charset]
    check("ascii 32..126 covered", not ascii_missing, "missing %r" % (ascii_missing,))
    extra_missing = [ch for ch in bake.EXTRA_SYMBOLS if ch not in charset]
    check("ui symbols covered", not extra_missing, "missing %r" % (extra_missing,))

    # every corpus glyph must actually have ink, not just an atlas slot
    blank = []
    for ch in sorted(corpus):
        surf = pixelfont.render(ch, 1, (255, 255, 255, 255))
        if not pygame.surfarray.array_alpha(surf).any():
            blank.append(ch)
    check("no blank glyphs", not blank, "blank %r" % (blank,))

    # 2. no antialiasing ------------------------------------------------
    samples = [
        ("欢闹厨房！", 84, True),
        ("★ 3 连击 x1.4", 18, True),
        ("Esc 继续    Tab 设置    Enter 回标题", 15, False),
        ("[F] 交互 · 下一步", 14, True),
        ("收摊结算 A+ 净收入 128", 40, True),
        ("N E V E R C O O K E D !", 22, False),
    ]
    for value, size, bold in samples:
        surf = text.render(value, size, (255, 255, 255), bold)
        values = alpha_values(surf)
        check("1-bit alpha %r@%d%s" % (value[:12], size, "b" if bold else ""),
              set(values) <= {0, 255}, "alpha values %r" % (values,))

    # 3. integer scaling ------------------------------------------------
    # 2x and above inserts one atlas pixel of air between two wide (CJK)
    # glyphs, so a width is scale x (advance + seams), not pure scale x.
    def expected(value, scale, bold=False):
        table, _ = pixelfont._table(bold)
        adv = pixelfont.measure(value, 1, bold)[0]
        seams = pixelfont._gaps(value, table, 1)
        return (adv + seams * pixelfont.tracking(scale)) * scale

    word = "欢闹厨房！"
    w12 = text.render(word, 12).get_width()
    w84 = text.render(word, 84).get_width()
    check("84px width scales 12px + CJK tracking", w84 == expected(word, 7),
          "%d vs %d" % (w84, expected(word, 7)))
    check("84px height == 84", text.render(word, 84).get_height() == 84,
          str(text.render(word, 84).get_height()))
    w24 = text.render(word, 20).get_width()
    check("20px renders at 2x plus tracking", w24 == expected(word, 2),
          "%d vs %d" % (w24, expected(word, 2)))
    # The wordmark: head (4 CJK) + "！", every glyph 12px advance at 1x.
    head = text.render("欢闹厨房", 84, (255, 255, 255), bold=True)
    whole = text.render("欢闹厨房！", 84, (255, 255, 255), bold=True)
    check("wordmark head 4 glyphs", head.get_width() == expected("欢闹厨房", 7, True),
          "%d vs %d" % (head.get_width(), expected("欢闹厨房", 7, True)))
    check("wordmark + ！", whole.get_width() == expected(word, 7, True), str(whole.get_width()))
    print("wordmark: 欢闹厨房@84 bold = %d x %d px, with ！ = %d px"
          % (head.get_width(), head.get_height(), whole.get_width()))
    bold84 = text.render(word, 84, bold=True).get_width()
    check("bold 84px scales the same way", bold84 == expected(word, 7, True),
          "%d vs %d" % (bold84, expected(word, 7, True)))
    table = [(10, 1), (12, 1), (13, 1), (14, 1), (15, 1), (16, 1), (17, 1), (18, 1),
             (19, 1), (20, 2), (22, 2), (24, 2), (27, 2), (30, 2), (31, 2), (33, 2),
             (34, 3), (38, 3), (40, 3), (48, 3), (58, 3), (59, 3),
             (60, 5), (72, 5), (79, 5), (80, 7), (84, 7), (96, 7)]
    bad = []
    base_h = pixelfont.render("A", 1).get_height()          # 12 regular
    bold_h = pixelfont.render("A", 1, bold=True).get_height()  # 13, the dilation
    for size, want in table:
        got = pixelfont.scale_for(size)
        if got != want:
            bad.append((size, got, want))
        surf = text.render("净收入 ★", size, (255, 255, 255), True)
        if surf.get_height() != bold_h * got:
            bad.append((size, "height", surf.get_height(), bold_h * got))
    check("scale table", not bad, repr(bad))

    # 5. unmapped characters fall back instead of crashing -----------------
    # built with chr() on purpose: a literal here would be scanned into the
    # atlas corpus by tools/font/bake_atlas.py and stop being "unmapped".
    probe = [chr(code) for code in (0x9F98, 0x20000, 0x1F004, 0x2211, 0x2665)]
    rare = next((ch for ch in probe if ch not in charset), None)
    if rare:
        try:
            surf = text.render("灶" + rare + "台", 14, (255, 255, 255), True)
            ok = surf.get_width() > 0
        except Exception as exc:  # noqa: BLE001 - the point is that it never raises
            ok = False
            print("   exception: %r" % (exc,))
        check("fallback for uncovered %r" % rare, ok)
    else:
        print("  skip fallback check (every probe char is in the atlas)")

    # 6. shadow_text keeps its contract ------------------------------------
    canvas = pygame.Surface((640, 200), pygame.SRCALPHA)
    rect = text.shadow_text(canvas, "净收入 ★128", (20, 20), size=22, color=(255, 255, 255), bold=True)
    check("shadow_text returns Rect", isinstance(rect, pygame.Rect) and rect.topleft == (20, 20),
          repr(rect))

    print("coverage: %d/%d corpus chars" % (len(corpus - (corpus - charset)), len(corpus)))
    if FAILURES:
        print("FONT: FAIL (%d) %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("FONT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
