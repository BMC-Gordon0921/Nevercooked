"""Bake assets/font/pixel12.png from a 12px system font, antialias OFF.

The atlas is a grid of fixed cells holding hard 1-bit white glyphs on a
transparent background.  SimSun's embedded 12px bitmap strike is the source:
pygame.font.Font(path, 12).render(text, False, color) produces a monochrome
(colorkey) surface whose pixels are only 0 or 255, i.e. authentic pixel type.

The charset is what the game actually writes - every CJK character inside a
string literal under core/ game/ scenes/ tests/ tools/ and inside data/*.json -
plus ASCII, plus a handful of UI symbols.  By default the GB2312 level-1 hanzi
are appended as a safety net so a new Chinese string still renders as pixels
instead of falling back to the TTF rasteriser.

Usage (from the repo root):
    python tools/font/bake_atlas.py              # SimSun 12px + GB2312 level 1
    python tools/font/bake_atlas.py --corpus-only    # only what the code uses
    python tools/font/bake_atlas.py --all-gb2312     # + level-2 hanzi
    python tools/font/bake_atlas.py --font noto      # OFL fallback face

Outputs:
    assets/font/pixel12.png / pixel12_bold.png  (white glyphs, alpha 0/255)
    assets/font/pixel12.json                    (cell geometry, adv, order)
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import sys

import numpy as np
import pygame

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "assets", "font")

FONTS = {
    "simsun": (r"C:\Windows\Fonts\simsun.ttc", 12),
    "noto": (r"C:\Windows\Fonts\NotoSansSC-VF.ttf", 12),
}
# Faces tried in order for a character the primary face draws blank at 12px.
SECONDARY = "noto"

# Extra symbols the game/UI writes but that the ASCII range does not cover.
EXTRA_SYMBOLS = "★·！？，。：…→×①②③"

SCAN_DIRS = ("core", "game", "scenes", "tests", "tools")
SCAN_FILES = ("main.py",)
SCAN_DATA = ("data",)
SKIP_DIR_NAMES = {"__pycache__", ".git", "_sb", "venv", "venv-aseprite"}


def _safe_console():
    """Windows consoles are GBK; never die printing a glyph that will not encode."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="backslashreplace")
        except (AttributeError, ValueError):
            pass


# --------------------------------------------------------------------------
# corpus
# --------------------------------------------------------------------------
def _iter_python_files(root):
    for base in SCAN_DIRS:
        top = os.path.join(root, base)
        for dirpath, dirnames, filenames in os.walk(top):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
            for name in sorted(filenames):
                if name.endswith(".py"):
                    yield os.path.join(dirpath, name)
    for name in SCAN_FILES:
        path = os.path.join(root, name)
        if os.path.exists(path):
            yield path


def _strings_in_python(path):
    """Every str constant in a module, f-string parts included."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            source = fh.read()
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError:
        return []
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append(node.value)
    return out


def _strings_in_json(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _strings_in_json(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings_in_json(item)


def _wanted(ch):
    """Non-ASCII, printable, not a surrogate: something the font must draw."""
    code = ord(ch)
    if code < 128 or not ch.isprintable():
        return False
    return not (0xD800 <= code <= 0xDFFF)


def collect_corpus(root=ROOT):
    """Return (chars, sources) - every non-ASCII char the game can display."""
    chars = set()
    sources = {}
    for path in _iter_python_files(root):
        found = set()
        for value in _strings_in_python(path):
            found.update(c for c in value if _wanted(c))
        if found:
            chars |= found
            sources[os.path.relpath(path, root)] = len(found)
    for base in SCAN_DATA:
        data_dir = os.path.join(root, base)
        if not os.path.isdir(data_dir):
            continue
        for name in sorted(os.listdir(data_dir)):
            if not name.endswith(".json"):
                continue
            path = os.path.join(data_dir, name)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    doc = json.load(fh)
            except (OSError, ValueError, UnicodeDecodeError):
                continue
            found = set()
            for value in _strings_in_json(doc):
                found.update(c for c in value if _wanted(c))
            if found:
                chars |= found
                sources[os.path.relpath(path, root)] = len(found)
    return chars, sources


def gb2312_hanzi(levels=(1,)):
    """GB2312 hanzi as a list, level 1 (3755) first, then level 2."""
    ranges = {1: (0xB0, 0xD8), 2: (0xD8, 0xF8)}
    out = []
    for level in levels:
        first, last = ranges[level]
        for hi in range(first, last):
            for lo in range(0xA1, 0xFF):
                try:
                    out.append(bytes([hi, lo]).decode("gb2312"))
                except UnicodeDecodeError:
                    continue
    return out


def build_charset(root=ROOT, gb_levels=(1,)):
    corpus, sources = collect_corpus(root)
    ordered = [chr(code) for code in range(32, 127)] + list(EXTRA_SYMBOLS)
    ordered += sorted(corpus - set(ordered))
    if gb_levels:
        ordered += sorted(set(gb2312_hanzi(gb_levels)) - set(ordered))
    seen, unique = set(), []
    for ch in ordered:
        if ch not in seen:
            seen.add(ch)
            unique.append(ch)
    return unique, corpus, sources


# --------------------------------------------------------------------------
# rasterising
# --------------------------------------------------------------------------
def _mask_of(surface):
    """(w, h) boolean array of the surface's ink; only 0/255 may survive."""
    rgb = pygame.surfarray.array3d(surface)
    levels = np.unique(rgb)
    if levels.size and not np.all(np.isin(levels, (0, 255))):
        raise RuntimeError("glyph rendered with partial coverage; antialias is still on")
    return rgb[:, :, 0] > 0


def measure_font(font, chars):
    """Per-char (mask, adv) plus the tight vertical band the whole face needs.

    surfarray arrays are indexed [x][y], so ink rows live in the *second* array
    nonzero() returns.  Getting that backwards silently swaps cell width and
    height, so it is spelled out here.
    """
    masks, advs = {}, {}
    y_min, y_max, x_max = 10 ** 6, -1, 0
    for ch in chars:
        surf = font.render(ch, False, (255, 255, 255))
        mask = _mask_of(surf)
        masks[ch] = mask
        advs[ch] = font.size(ch)[0]
        xi, yi = np.nonzero(mask)
        if yi.size:
            y_min = min(y_min, int(yi.min()))
            y_max = max(y_max, int(yi.max()))
            x_max = max(x_max, int(xi.max()) + 1)
        x_max = max(x_max, mask.shape[0], advs[ch])
    if y_max < 0:
        raise RuntimeError("font rendered nothing at all")
    return masks, advs, y_min, y_max, x_max


def _secondary_glyph(font, ch, band, cell_w, cell_h):
    """Clip a fallback face's glyph into the primary face's band, or None."""
    if font is None:
        return None
    try:
        surf = font.render(ch, False, (255, 255, 255))
    except pygame.error:
        return None
    mask = _mask_of(surf)
    clipped = np.zeros((cell_w, cell_h), bool)
    piece = mask[:cell_w, band:band + cell_h]
    clipped[:piece.shape[0], :piece.shape[1]] = piece
    if not clipped.any():
        return None
    return clipped, font.size(ch)[0]


def _dilate(mask, cell_w, cell_h):
    """1px bold: OR the mask with itself shifted +1x and +1y."""
    out = np.zeros((cell_w + 1, cell_h + 1), bool)
    out[:cell_w, :cell_h] |= mask
    out[1:cell_w + 1, :cell_h] |= mask
    out[:cell_w, 1:cell_h + 1] |= mask
    return out


def _atlas_surface(cells, order, cell_w, cell_h, cols):
    rows = (len(order) + cols - 1) // cols
    alpha = np.zeros((cols * cell_w, rows * cell_h), np.uint8)
    positions = {}
    for index, ch in enumerate(order):
        col, row = index % cols, index // cols
        mask = cells[ch]
        x, y = col * cell_w, row * cell_h
        alpha[x:x + cell_w, y:y + cell_h] = np.where(mask, 255, 0).astype(np.uint8)
        positions[ch] = (col, row)
    surf = pygame.Surface((cols * cell_w, rows * cell_h), pygame.SRCALPHA)
    surf.fill((255, 255, 255, 0))
    view = pygame.surfarray.pixels_alpha(surf)
    view[:, :] = alpha
    del view
    rgb = pygame.surfarray.pixels3d(surf)
    rgb[:, :, :] = 255
    del rgb
    return surf, rows, cols, positions


def bake(font_key="simsun", root=ROOT, out_dir=OUT_DIR, cols=32, quiet=False,
         gb_levels=(1,)):
    path, size = FONTS[font_key]
    if not os.path.exists(path):
        raise SystemExit("font not found: %s" % path)
    pygame.init()
    pygame.font.init()
    font = pygame.font.Font(path, size)

    charset, corpus, sources = build_charset(root, gb_levels)
    masks, advs, y_min, y_max, x_max = measure_font(font, charset)
    cell_w, cell_h = int(x_max), int(y_max - y_min + 1)
    band = int(y_min)

    # A glyph the strike cannot draw (some dingbats are blank at 12px) borrows a
    # glyph from the secondary face rather than becoming a TTF fallback later.
    fallback = {}
    empties = [ch for ch in charset if ch.strip() and not masks[ch].any()]
    if empties:
        sec_path = FONTS.get(SECONDARY, (None, 12))[0]
        secondary = pygame.font.Font(sec_path, size) if sec_path and os.path.exists(sec_path) else None
        for ch in list(empties):
            got = _secondary_glyph(secondary, ch, band, cell_w, cell_h)
            if got is not None:
                masks[ch], advs[ch] = got
                fallback[ch] = SECONDARY
                empties.remove(ch)
    chars = [ch for ch in charset if ch not in set(empties)]

    cells, short = {}, []
    for ch in chars:
        mask = masks[ch]
        cell = np.zeros((cell_w, cell_h), bool)
        clipped = mask[:, band:band + cell_h][:, :cell_w]
        cell[:clipped.shape[0], :clipped.shape[1]] = clipped
        cells[ch] = cell
        if mask.shape[1] < band + cell_h:
            short.append((ch, mask.shape[1]))

    bold_cells = {ch: _dilate(cells[ch], cell_w, cell_h) for ch in chars}
    bold_w, bold_h = cell_w + 1, cell_h + 1

    surf, rows, cols, pos = _atlas_surface(cells, chars, cell_w, cell_h, cols)
    bold_surf, _, _, bold_pos = _atlas_surface(bold_cells, chars, bold_w, bold_h, cols)

    os.makedirs(out_dir, exist_ok=True)
    regular_png = os.path.join(out_dir, "pixel12.png")
    bold_png = os.path.join(out_dir, "pixel12_bold.png")
    pygame.image.save(surf, regular_png)
    pygame.image.save(bold_surf, bold_png)

    def glyph_table(positions):
        return {ch: {"col": positions[ch][0], "row": positions[ch][1], "adv": int(advs[ch])}
                for ch in chars}

    doc = {
        "family": font_key,
        "source": path,
        "size": size,
        "antialias": False,
        "cell": cell_w,
        "cell_h": cell_h,
        "line_height": int(font.get_linesize()),
        "baseline": int(font.get_ascent()) - band,
        "band_top": band,
        "png": "pixel12.png",
        "rows": rows,
        "cols": cols,
        "count": len(chars),
        "gb2312": list(gb_levels),
        "fallback": fallback,
        "undrawable": empties,
        "order": "".join(chars),
        "glyphs": glyph_table(pos),
        "bold": {
            "png": "pixel12_bold.png",
            "cell": bold_w,
            "cell_h": bold_h,
            "rows": rows,
            "cols": cols,
            "order": "".join(chars),
            "glyphs": glyph_table(bold_pos),
        },
    }
    json_path = os.path.join(out_dir, "pixel12.json")
    with open(json_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=False)
        fh.write("\n")

    if not quiet:
        print("font        : %s %dpx (%s)" % (font_key, size, path))
        print("cell        : %dx%d (bold %dx%d), band rows %d..%d"
              % (cell_w, cell_h, bold_w, bold_h, band, y_max))
        print("atlas       : %d cols x %d rows = %d x %d px"
              % (cols, rows, cols * cell_w, rows * cell_h))
        print("glyphs      : %d (corpus %d, gb2312 %s)"
              % (len(chars), len(corpus), list(gb_levels) or "off"))
        print("corpus      : %d chars from %d files" % (len(corpus), len(sources)))
        print("corpus missing from atlas: %s" % (sorted(corpus - set(chars)) or "none"))
        print("borrowed    : %s" % (sorted(fallback.items()) or "none"))
        print("undrawable  : %s" % (empties or "none"))
        print("short cells : %s" % (short or "none"))
        print("wrote       : %s" % ", ".join(
            os.path.relpath(p, root) for p in (regular_png, bold_png, json_path)))
    return doc


def main(argv=None):
    _safe_console()
    parser = argparse.ArgumentParser(description="Bake the 12px pixel font atlas.")
    parser.add_argument("--font", choices=sorted(FONTS), default="simsun",
                        help="system font to rasterise (default: simsun)")
    parser.add_argument("--cols", type=int, default=32, help="atlas columns")
    parser.add_argument("--corpus-only", action="store_true",
                        help="bake only the characters the code actually uses")
    parser.add_argument("--all-gb2312", action="store_true",
                        help="add GB2312 level-2 hanzi as well (6763 total)")
    args = parser.parse_args(argv)
    if args.corpus_only:
        levels = ()
    elif args.all_gb2312:
        levels = (1, 2)
    else:
        levels = (1,)
    bake(args.font, cols=args.cols, gb_levels=levels)
    return 0


if __name__ == "__main__":
    sys.exit(main())
