"""Chef sprite frames: 44x64, feet on the bottom edge, three facings x four steps."""
from tools.pixel.pxlib import Art, col, mix, finish

INK, NIGHT, WHITE, IVORY = col("ink"), col("night"), col("white"), col("ivory")
SAND, CLAY, WOOD, TEAL = col("sand"), col("clay"), col("wood"), col("teal")
MINT, STEEL, SL, AMBER, LEATHER = col("mint"), col("steel"), col("steel_light"), col("amber"), col("leather")

RAMP = ["ink", "night", "white", "ivory", "sand", "clay", "wood", "teal", "mint", "steel", "steel_light", "leather"]
SKIN = mix(CLAY, SAND, 0.35)
SKIN_D = mix(CLAY, WOOD, 0.45)
HAIR = mix(LEATHER, CLAY, 0.15)
COAT_D = mix(IVORY, SAND, 0.65)
TEAL_L = mix(TEAL, MINT, 0.30)


def rr(a, x, y, w, h, r, c):
    """Rounded rect: solid interior with only the four corners knocked off."""
    for i in range(h):
        inset = 0
        if i < r:
            d = r - i - 0.5
            inset = int(round(r - max(0.0, r * r - d * d) ** 0.5))
        elif i >= h - r:
            d = i - (h - r) + 0.5
            inset = int(round(r - max(0.0, r * r - d * d) ** 0.5))
        a.hline(x + inset, x + w - 1 - inset, y + i, c)


def _hat(a, bob, x0, w):
    a.ellipse(x0 - 1, bob - 3, w, 12, WHITE)
    a.ellipse(x0 + 1, bob - 1, 9, 8, WHITE)
    a.ellipse(x0 + w - 10, bob - 1, 9, 8, WHITE)
    a.ellipse(x0 + 5, bob - 4, 11, 8, WHITE)
    a.rect(x0 + 2, bob + 7, w - 4, 6, IVORY)
    a.hline(x0 + 2, x0 + w - 3, bob + 7, WHITE)
    a.hline(x0 + 2, x0 + w - 3, bob + 12, COAT_D)
    for px in range(x0 + 5, x0 + w - 4, 4):
        a.vline(px, bob + 9, bob + 11, mix(IVORY, SAND, 0.45))


def _head(a, bob, back=False):
    rr(a, 12, 13 + bob, 20, 18, 5, SKIN)
    a.hline(15, 28, 13 + bob, mix(SKIN, WHITE, 0.35))
    a.vline(12, 18 + bob, 27 + bob, SKIN_D)
    a.vline(31, 18 + bob, 27 + bob, SKIN_D)
    a.hline(15, 28, 30 + bob, SKIN_D)
    if back:
        a.rect(13, 21 + bob, 18, 10, HAIR)
        a.hline(14, 29, 21 + bob, mix(HAIR, SKIN, 0.35))
        a.hline(14, 29, 30 + bob, SKIN_D)
        return
    a.hline(16, 18, 17 + bob, HAIR)
    a.hline(25, 27, 17 + bob, HAIR)
    a.rect(16, 19 + bob, 2, 3, INK)
    a.rect(26, 19 + bob, 2, 3, INK)
    a.px(16, 19 + bob, WHITE)
    a.px(26, 19 + bob, WHITE)
    a.px(21, 22 + bob, SKIN_D)
    a.px(22, 23 + bob, SKIN_D)
    a.hline(20, 23, 25 + bob, INK)
    a.hline(20, 23, 26 + bob, SKIN_D)
    a.px(14, 23 + bob, mix(SKIN, col("tomato"), 0.30))
    a.px(29, 23 + bob, mix(SKIN, col("tomato"), 0.30))


def _legs(a, bob, ll, rl):
    for x0, lift in ((14, ll), (23, rl)):
        a.rect(x0, 47 + bob, 7, 12 - lift, STEEL)
        a.vline(x0 + 1, 47 + bob, 57 - lift, mix(STEEL, SL, 0.45))
        a.hline(x0, x0 + 6, 46 + bob, mix(STEEL, NIGHT, 0.35))
    for x0, lift in ((12, ll), (22, rl)):
        a.rect(x0, 58 - lift, 10, 6, NIGHT)
        a.hline(x0, x0 + 9, 58 - lift, mix(NIGHT, SL, 0.60))
        a.hline(x0, x0 + 9, 62 - lift, INK)
    a.vline(21, 58 - ll, 63, INK)


def _body(a, bob, back=False):
    rr(a, 10, 31 + bob, 24, 18, 3, IVORY)
    a.hline(12, 31, 31 + bob, WHITE)
    a.vline(10, 34 + bob, 48 + bob, COAT_D)
    a.vline(33, 34 + bob, 48 + bob, COAT_D)
    if back:
        a.line((14, 32 + bob), (22, 42 + bob), mix(IVORY, SAND, 0.80))
        a.line((30, 32 + bob), (22, 42 + bob), mix(IVORY, SAND, 0.80))
        a.poly([(18, 43 + bob), (26, 43 + bob), (26, 49 + bob), (18, 49 + bob)], TEAL)
    else:
        a.line((14, 32 + bob), (18, 37 + bob), MINT)
        a.line((30, 32 + bob), (26, 37 + bob), MINT)
        a.poly([(14, 35 + bob), (30, 35 + bob), (29, 49 + bob), (15, 49 + bob)], TEAL)
        a.poly([(15, 36 + bob), (19, 36 + bob), (18, 48 + bob), (16, 48 + bob)], TEAL_L)
        a.hline(18, 26, 43 + bob, mix(TEAL, MINT, 0.50))
        a.px(27, 39 + bob, AMBER)
    a.hline(10, 33, 48 + bob, COAT_D)


def _arms(a, bob, dl, dr):
    for x0, dy, inner in ((6, dl, 11), (32, dr, 32)):
        a.rect(x0, 33 + bob + dy, 6, 13, IVORY)
        a.vline(inner, 33 + bob + dy, 45 + bob + dy, mix(IVORY, SAND, 0.55))
        a.hline(x0, x0 + 5, 45 + bob + dy, COAT_D)
        a.rect(x0, 46 + bob + dy, 6, 4, SKIN)
        a.hline(x0, x0 + 5, 49 + bob + dy, SKIN_D)


def chef_frame(dirn, step):
    a = Art(44, 64)
    bob = [0, -1, 0, -1][step]
    ll = [0, 2, 1, 0][step]
    rl = [0, 0, 1, 2][step]
    sw = [0, 1, 0, -1][step]

    if dirn in ("down", "up"):
        front = dirn == "down"
        _legs(a, bob, ll if front else rl, rl if front else ll)
        _arms(a, bob, sw if front else -sw, -sw if front else sw)
        _body(a, bob, back=not front)
        a.rect(19, 29 + bob, 6, 3, SKIN_D)
        _head(a, bob, back=not front)
        _hat(a, bob, 10, 25)
    else:
        a.rect(12, 47 + bob, 7, 12 - rl, mix(STEEL, NIGHT, 0.30))
        a.rect(13, 58 - rl, 9, 6, mix(NIGHT, STEEL, 0.45))
        a.rect(18, 47 + bob, 7, 12 - ll, STEEL)
        a.vline(19, 47 + bob, 58 - ll, mix(STEEL, SL, 0.45))
        a.rect(17, 58 - ll, 14, 6, NIGHT)
        a.hline(17, 30, 58 - ll, mix(NIGHT, SL, 0.60))
        a.hline(17, 30, 63, INK)
        rr(a, 9, 31 + bob, 21, 18, 3, IVORY)
        a.hline(11, 27, 31 + bob, WHITE)
        a.poly([(12, 35 + bob), (27, 35 + bob), (26, 49 + bob), (13, 49 + bob)], TEAL)
        a.poly([(13, 36 + bob), (17, 36 + bob), (16, 48 + bob), (14, 48 + bob)], TEAL_L)
        a.rect(20, 33 + bob + sw, 6, 13, IVORY)
        a.hline(20, 25, 45 + bob + sw, COAT_D)
        a.rect(20, 46 + bob + sw, 6, 4, SKIN)
        a.hline(20, 25, 49 + bob + sw, SKIN_D)
        a.rect(17, 29 + bob, 6, 3, SKIN_D)
        rr(a, 12, 13 + bob, 18, 18, 5, SKIN)
        a.hline(15, 27, 13 + bob, mix(SKIN, WHITE, 0.35))
        a.rect(12, 15 + bob, 5, 13, HAIR)
        a.hline(13, 16, 15 + bob, mix(HAIR, SKIN, 0.30))
        a.hline(23, 26, 17 + bob, HAIR)
        a.rect(24, 19 + bob, 2, 3, INK)
        a.px(24, 19 + bob, WHITE)
        a.rect(29, 20 + bob, 2, 3, SKIN)
        a.hline(24, 26, 25 + bob, INK)
        a.hline(24, 26, 26 + bob, SKIN_D)
        a.hline(15, 28, 30 + bob, SKIN_D)
        _hat(a, bob, 10, 24)
    return finish(a, RAMP, outline="ink")
