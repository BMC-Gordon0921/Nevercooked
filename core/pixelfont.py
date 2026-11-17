"""Pixel-font engine: a 12px bitmap atlas drawn at integer scales, never smooth.

The atlas (assets/font/pixel12.png + .json) is baked by tools/font/bake_atlas.py
from SimSun's embedded 12px bitmap strike with antialiasing off, so every glyph
is a hard 1-bit mask.  This module is the only thing that reads it:

    ready()                     -> True once the atlas is loaded (never raises)
    covers(text)                -> True when every char in text has a glyph
    missing(text)               -> set of chars the atlas has no glyph for
    measure(text, scale, bold)  -> (width, height) in pixels
    render(text, scale, color, bold) -> pygame.Surface (SRCALPHA)
    scale_for(size)             -> integer scale a layout size snaps to

Scaling is nearest-neighbour by whole integers: scale 1 draws the 12px strike,
scale 7 draws it at 84px with square pixels and no grey.  Colours are applied by
multiplying a white atlas, so alpha stays hard-edged (0 or 255) at any scale.
"""
from __future__ import annotations

import json
import os

import pygame

ASSET_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "font")
ATLAS_PNG = "pixel12.png"
ATLAS_JSON = "pixel12.json"
WHITE = (255, 255, 255, 255)
CACHE_LIMIT = 4096

_state = {
    "tried": False,
    "ok": False,
    "base": 12,
    "cell": (12, 12),
    "line_height": 14,
    "atlas": None,
    "bold_atlas": None,
    "glyphs": {},
    "bold_glyphs": {},
    "meta": {},
}
_cache = {}


# ---------------------------------------------------------------- loading
def _asset_dir():
    override = os.environ.get("NVR_FONT_DIR")
    return override or ASSET_DIR


def _load():
    """Load the atlas once.  A missing or broken atlas is not an error here."""
    if _state["tried"]:
        return _state["ok"]
    _state["tried"] = True
    root = _asset_dir()
    try:
        with open(os.path.join(root, ATLAS_JSON), "r", encoding="utf-8") as fh:
            meta = json.load(fh)
        atlas = pygame.image.load(os.path.join(root, meta.get("png", ATLAS_PNG)))
        cell_w = int(meta.get("cell", 12))
        cell_h = int(meta.get("cell_h", cell_w))
        bold_meta = meta.get("bold") or {}
        bold_atlas = None
        if bold_meta.get("png"):
            bold_path = os.path.join(root, bold_meta["png"])
            if os.path.exists(bold_path):
                bold_atlas = pygame.image.load(bold_path)
                bold_atlas = _prepare(bold_atlas)
        atlas = _prepare(atlas)
        glyphs = _rects(meta.get("glyphs", {}), cell_w, cell_h)
        bold_glyphs = _rects(
            bold_meta.get("glyphs", {}),
            int(bold_meta.get("cell", cell_w)),
            int(bold_meta.get("cell_h", cell_h)),
        )
    except (OSError, ValueError, KeyError, TypeError, pygame.error):
        _state.update(ok=False, meta={})
        return False
    _state.update(
        ok=bool(glyphs),
        base=int(meta.get("size", 12)) or 12,
        cell=(cell_w, cell_h),
        line_height=int(meta.get("line_height", cell_h)) or cell_h,
        atlas=atlas,
        bold_atlas=bold_atlas,
        glyphs=glyphs,
        bold_glyphs=bold_glyphs,
        meta=meta,
    )
    return _state["ok"]


def _prepare(surface):
    """convert_alpha when a display exists (faster blits); raw surface otherwise."""
    try:
        if pygame.display.get_surface() is not None:
            return surface.convert_alpha()
    except pygame.error:
        pass
    return surface


def _rects(table, cell_w, cell_h):
    out = {}
    for ch, entry in table.items():
        try:
            col, row, adv = int(entry["col"]), int(entry["row"]), int(entry["adv"])
        except (KeyError, TypeError, ValueError):
            continue
        out[ch] = (pygame.Rect(col * cell_w, row * cell_h, cell_w, cell_h), adv)
    return out


# ------------------------------------------------------------------- api
def ready():
    """True when the atlas is on disk and loaded."""
    return _load()


def info():
    """Geometry of the loaded atlas (empty dict when unavailable)."""
    _load()
    return dict(_state["meta"]) if _state["ok"] else {}


def base():
    """Pixel size of one atlas cell before scaling (12)."""
    _load()
    return int(_state["base"])


def line_height(scale=1):
    """Vertical advance of one line at the given integer scale."""
    _load()
    return int(_state["line_height"]) * max(1, int(scale))


# A layout size is intent, not pixel truth: there is no 15px strike, so a 15px
# label becomes 24px type.  This table is the single place that decision lives,
# which keeps the snapping consistent across HUD, menus and the title wordmark.
SCALE_RULE = "table"      # "table" (snap bands) or "nearest" (round(size/base))
# Upper bound -> scale.  The bounds are *nominal layout sizes*, not pixels: body
# copy is authored 12-19 and stays at 1x, whatever strike the atlas holds (Cubic
# 11 ships at 11px, Ark Pixel at 12px), so swapping the face never re-lays-out a
# screen.  Only the wordmark band reaches 7x.
# There is no 4x band on purpose: 60-79 snaps to 5x so rising sizes never step
# backwards in apparent weight.
SCALE_BANDS = ((19, 1), (33, 2), (59, 3), (79, 5))
SCALE_TOP = 7             # 80 and up: the 84px title wordmark
BAND_BASE = 12            # reference strike, for scale_for(rule="nearest")
BOLD_MAX_SCALE = 2        # bold is honest at 1x-2x; from 3x it fills ideographs in


def _bands():
    """The size->scale table; kept as a function so callers can introspect it."""
    return SCALE_BANDS


def scale_for(size, rule=None):
    """Integer scale factor for a layout size (1x = one strike, 7x = 7 strikes)."""
    rule = rule or SCALE_RULE
    try:
        size = float(size)
    except (TypeError, ValueError):
        return 1
    _load()
    base = float(_state["base"] if _state["ok"] else BAND_BASE) or 12.0
    if rule == "nearest":
        return max(1, min(SCALE_TOP, int(round(size / base))))
    for limit, factor in _bands():
        if size <= limit:
            return factor
    return SCALE_TOP


def pixel_size(size):
    """Pixel height text actually gets for a layout size, after snapping."""
    return base() * scale_for(size)


def charset():
    """Every character the atlas can draw."""
    _load()
    return set(_state["glyphs"])


def _table(bold):
    _load()
    if bold and _state["bold_glyphs"]:
        return _state["bold_glyphs"], _state["bold_atlas"]
    return _state["glyphs"], _state["atlas"]


def _adv(ch, table):
    entry = table.get(ch)
    if entry is not None:
        return entry[1]
    return _state["cell"][0]


def covers(text):
    """True when every character of text has an atlas glyph."""
    if not text:
        return ready()
    if not _load():
        return False
    table = _state["glyphs"]
    return all(ch in table for ch in text)


def missing(text):
    """The characters of text the atlas cannot draw (empty set when it can)."""
    if not text or not _load():
        return set(text or "")
    table = _state["glyphs"]
    return {ch for ch in text if ch not in table}


def tracking(scale):
    """Extra atlas pixels between glyphs: 1 at 2x and above.

    A 12px CJK cell is inked to its edges, so at 2x neighbouring characters
    touch and the line fuses into a wall of pixels.  One atlas pixel of air
    (scaled with the glyphs) is enough to separate them.
    """
    return 1 if int(scale) >= 2 else 0


def _wide(ch, table):
    return _adv(ch, table) >= _state["cell"][0] - 1


def _gaps(text, table, extra):
    """Count the seams that get extra air: wide CJK glyphs next to each other."""
    if not text or not extra:
        return 0
    return sum(1 for a, b in zip(text, text[1:])
               if _wide(a, table) and _wide(b, table))


def _faces(bold):
    """(regular, bold) as (table, atlas, cell_w, cell_h); bold may equal regular."""
    _load()
    regular = (_state["glyphs"], _state["atlas"], _state["cell"][0], _state["cell"][1])
    if bold and _state["bold_glyphs"] and _state["bold_atlas"] is not None:
        meta = _state["meta"].get("bold") or {}
        strong = (_state["bold_glyphs"], _state["bold_atlas"],
                  int(meta.get("cell", regular[2])), int(meta.get("cell_h", regular[3])))
        return regular, strong
    return regular, regular


def _face(ch, faces, bold, scale):
    """The face one character is drawn with.

    Above BOLD_MAX_SCALE an ideograph keeps the regular weight: the bold atlas is
    the regular one dilated by a pixel, which closes the counters of dense glyphs
    (置, 暂, 摊) and turns a 36px heading into a blob.  Latin and digits keep
    their bold at every size.
    """
    regular, strong = faces
    if strong is regular or not bold:
        return regular
    if int(scale) > BOLD_MAX_SCALE and _wide(ch, regular[0]):
        return regular
    return strong


def _layout(text, faces, bold, scale, extra):
    """(width at 1x, tallest cell) with the per-character face choice applied."""
    regular = faces[0]
    width = 0
    height = 0
    for index, ch in enumerate(text):
        face = _face(ch, faces, bold, scale)
        width += _adv(ch, face[0])
        height = max(height, face[3])
        if index + 1 < len(text):
            nxt = text[index + 1]
            if extra and _wide(ch, regular[0]) and _wide(nxt, regular[0]):
                width += extra
    return width, height


def measure(text, scale=1, bold=False):
    """(width, height) of text at an integer scale, in pixels."""
    _load()
    scale = max(1, int(scale))
    width, height = _layout(text, _faces(bold), bold, scale, tracking(scale))
    return (width * scale, height * scale)


def render(text, scale=1, color=(255, 255, 255, 255), bold=False):
    """A cached SRCALPHA surface holding text as hard pixel glyphs."""
    scale = max(1, int(scale))
    key = (text, scale, tuple(color), bool(bold))
    hit = _cache.get(key)
    if hit is not None:
        return hit
    surf = _draw(text, scale, color, bold)
    if len(_cache) > CACHE_LIMIT:
        _cache.clear()
    _cache[key] = surf
    return surf


def _draw(text, scale, color, bold):
    faces = _faces(bold)
    regular = faces[0]
    if regular[1] is None or not text:
        cell_w, cell_h = _cell_for(bold)
        return pygame.Surface((max(1, cell_w * scale), max(1, cell_h * scale)),
                              pygame.SRCALPHA)
    extra = tracking(scale)
    width, height = _layout(text, faces, bold, scale, extra)
    surf = pygame.Surface((max(1, width), max(1, height)), pygame.SRCALPHA)
    x = 0
    for index, ch in enumerate(text):
        face = _face(ch, faces, bold, scale)
        entry = face[0].get(ch)
        if entry is not None:
            surf.blit(face[1], (x, 0), entry[0])
        x += _adv(ch, face[0])
        if index + 1 < len(text):
            nxt = text[index + 1]
            if extra and _wide(ch, regular[0]) and _wide(nxt, regular[0]):
                x += extra
    if scale != 1:
        surf = pygame.transform.scale(surf, (surf.get_width() * scale, surf.get_height() * scale))
    tint = _rgba(color)
    if tint != WHITE:
        surf.fill(tint, special_flags=pygame.BLEND_RGBA_MULT)
    return surf


def _cell_for(bold):
    """Cell size actually used: bold cells are one pixel larger (the dilation)."""
    if bold and _state["bold_glyphs"]:
        bold_meta = _state["meta"].get("bold") or {}
        return (int(bold_meta.get("cell", _state["cell"][0])),
                int(bold_meta.get("cell_h", _state["cell"][1])))
    return tuple(_state["cell"])


def _rgba(color):
    try:
        values = tuple(int(v) for v in color)
    except (TypeError, ValueError):
        return WHITE
    if len(values) == 3:
        return (values[0], values[1], values[2], 255)
    if len(values) >= 4:
        return (values[0], values[1], values[2], values[3])
    return WHITE


def clear_cache():
    """Drop every cached surface (tests and A/B comparisons)."""
    _cache.clear()
