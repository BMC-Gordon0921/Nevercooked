"""Replacement blocks spliced into make_art.py by _splice.py (pass 2)."""
from tools.pixel.pxlib import Art, col, dk, li, mix
from tools.pixel import pxlib as px

C = col
T = 64


def chef_frame(dirn, step):
    """Chef: toque, ivory coat, teal apron, dark shoes. Feet on the frame bottom."""
    HAT, COAT, APRON, TRIM = C("white"), C("ivory"), C("teal"), C("mint")
    SKIN = C("sand")
    SKIN_D = mix(C("sand"), C("clay"), 0.45)
    MOUTH = mix(C("sand"), C("cocoa"), 0.6)
    PANTS = C("slate")
    SHOE = C("ink")
    SHOE_HI = mix(C("slate"), C("steel_light"), 0.30)
    a = Art(44, 64)
    bob = (0, -1, 0, -1)[step]
    lift = ((0, 0), (1, 0), (0, 1), (0, 0))[step]
    swing = (-1, 0, 1, 0)[step]

    def feet(lx, rx, y):
        for x, lf in ((lx, lift[0]), (rx, lift[1])):
            leg_h = 12 - lf * 2
            a.rect(x, y, 6, leg_h, PANTS)
            a.vline(x, y, y + leg_h - 1, mix(PANTS, C("steel"), 0.45))
            a.vline(x + 5, y, y + leg_h - 1, C("ink"))
            sy = y + leg_h
            a.rect(x - 2, sy, 10, 63 - sy, SHOE)
            a.hline(x - 2, x + 7, sy, SHOE_HI)
            a.hline(x - 2, x + 7, 63, C("black"))

    def body(y, w=22, x0=11):
        a.rect(x0, y, w, 19, COAT)
        a.rect(x0 - 1, y, w + 2, 3, COAT)
        a.hline(x0 - 1, x0 + w, y, HAT)
        a.hline(x0 - 1, x0 + w, y + 1, mix(COAT, HAT, 0.5))
        # apron
        a.rect(x0 + 3, y + 4, w - 6, 14, APRON)
        a.hline(x0 + 3, x0 + w - 4, y + 4, li(APRON, 0.28))
        a.hline(x0 + 3, x0 + w - 4, y + 17, dk(APRON, 0.30))
        a.vline(x0 + 3, y + 4, y + 17, li(APRON, 0.16))
        a.vline(x0 + w - 4, y + 4, y + 17, dk(APRON, 0.25))
        # apron straps over the shoulders
        a.line((x0 + 5, y + 4), (x0 + 8, y + 1), dk(APRON, 0.15))
        a.line((x0 + w - 6, y + 4), (x0 + w - 9, y + 1), dk(APRON, 0.15))
        # coat seams + buttons
        a.vline(x0 + 2, y + 3, y + 18, mix(COAT, C("sand"), 0.30))
        a.px(x0 + 6, y + 3, dk(COAT, 0.35))
        a.px(x0 + w - 7, y + 3, dk(COAT, 0.35))
        # pocket
        a.hline(x0 + 4, x0 + 8, y + 20, mix(COAT, C("sand"), 0.45))

    def arm(x, y, cuff=False):
        a.rect(x, y, 5, 12, COAT)
        a.vline(x, y, y + 11, mix(COAT, HAT, 0.45))
        a.vline(x + 4, y, y + 11, mix(COAT, C("sand"), 0.45))
        a.rect(x, y + 9, 5, 3, TRIM)          # rolled cuff
        a.rect(x, y + 12, 5, 4, SKIN)
        a.px(x, y + 12, SKIN_D)

    def head(y, cx=22, back=False, side=False):
        # toque
        a.ellipse(cx - 13, y - 17, 26, 16, HAT)
        a.hline(cx - 11, cx + 9, y - 16, C("white"))
        a.px(cx - 9, y - 14, C("white"))
        a.hline(cx - 12, cx + 11, y - 5, mix(HAT, COAT, 0.55))
        a.rect(cx - 12, y - 4, 24, 4, COAT)
        a.hline(cx - 12, cx + 11, y - 4, HAT)
        a.hline(cx - 12, cx + 11, y - 1, mix(COAT, C("sand"), 0.35))
        # face
        if back:
            a.rect(cx - 8, y, 16, 15, mix(SKIN, SKIN_D, 0.45))
            a.hline(cx - 8, cx + 7, y, dk(SKIN, 0.15))
            a.hline(cx - 6, cx + 5, y + 9, mix(SKIN_D, SKIN, 0.4))
            a.hair = None
        else:
            a.rect(cx - 8, y, 16, 15, SKIN)
            a.vline(cx + 7, y, y + 14, SKIN_D)
            a.hline(cx - 8, cx + 7, y + 14, SKIN_D)
            a.hline(cx - 8, cx + 7, y, mix(SKIN, dk(SKIN, 0.15), 0.5))
            if side:
                a.rect(cx - 8, y, 5, 12, mix(SKIN_D, SKIN, 0.3))   # hair at the back
                a.px(cx + 8, y + 6, SKIN)                          # nose
                a.rect(cx + 2, y + 6, 2, 2, C("ink"))
                a.px(cx + 2, y + 6, C("steel_light"))
                a.rect(cx - 1, y + 11, 4, 1, MOUTH)
            else:
                a.rect(cx - 5, y + 6, 2, 2, C("ink"))
                a.rect(cx + 3, y + 6, 2, 2, C("ink"))
                a.px(cx - 5, y + 7, C("steel_light"))
                a.px(cx + 3, y + 7, C("steel_light"))
                a.hline(cx - 3, cx + 2, y + 11, MOUTH)
                a.px(cx - 4, y + 9, mix(SKIN, C("tomato"), 0.25))
                a.px(cx + 3, y + 9, mix(SKIN, C("tomato"), 0.25))

    if dirn == "down":
        feet(15, 23, 47)
        body(29 + bob)
        arm(5, 30 + bob + (swing > 0), 0)
        arm(34, 30 + bob + (swing < 0), 0)
        head(15 + bob)
    elif dirn == "up":
        feet(15, 23, 47)
        body(29 + bob)
        # apron bow at the back
        a.rect(19, 33 + bob, 6, 3, dk(APRON, 0.10))
        a.px(18, 35 + bob, APRON)
        a.px(25, 35 + bob, APRON)
        arm(5, 30 + bob + (swing < 0), 0)
        arm(34, 30 + bob + (swing > 0), 0)
        head(15 + bob, back=True)
    else:
        feet(20 + (1 if swing > 0 else 0), 14 - (1 if swing < 0 else 0), 47)
        body(29 + bob, w=18, x0=13)
        # the side apron sits on the front of the body
        a.rect(22, 33 + bob, 8, 14, APRON)
        a.hline(22, 29, 33 + bob, li(APRON, 0.28))
        a.hline(22, 29, 46 + bob, dk(APRON, 0.30))
        a.rect(19, 30 + bob + swing, 5, 9, COAT)
        a.rect(19, 39 + bob + swing, 5, 4, TRIM)
        a.rect(19, 42 + bob + swing, 5, 4, SKIN)
        head(15 + bob, side=True)
    return px.finish(a, ["ink", "black", "white", "ivory", "sand", "clay", "slate", "steel",
                         "steel_light", "teal", "mint", "cocoa"])


def new_station_board():
    a = Art(T, 92)
    steel_w = mix(STEEL_L, STEEL, 0.40)
    wood_c = mix(CLAY, SAND, 0.28)
    # backsplash
    a.rect(4, 2, 56, 28, steel_w)
    a.hline(4, 59, 2, mix(steel_w, C("silver"), 0.45))
    a.hline(4, 59, 3, mix(steel_w, C("silver"), 0.25))
    a.hline(4, 59, 28, C("ink"))
    a.rect(9, 7, 46, 2, C("silver"))          # tool rail
    a.rect(9, 7, 46, 1, C("white"))
    # knife
    a.rect(15, 8, 3, 4, C("cocoa"))
    a.poly([(14, 12), (20, 12), (20, 26), (14, 23)], C("silver"))
    a.poly([(15, 13), (19, 13), (19, 24), (15, 22)], mix(C("silver"), C("steel_light"), 0.40))
    a.hline(16, 16, 14, C("white"))
    # ladle
    a.vline(38, 10, 22, C("silver"))
    a.ellipse(33, 20, 10, 8, C("silver"))
    a.ellipse(35, 21, 6, 5, mix(C("silver"), steel_w, 0.55))
    # towel
    a.rect(44, 11, 9, 12, C("mint"))
    a.hline(44, 52, 11, li(C("mint"), 0.30))
    a.hline(44, 52, 22, dk(C("mint"), 0.30))
    a.vline(44, 11, 22, li(C("mint"), 0.20))
    # counter
    top_face(a, 30, 44, wood_c, lip=3)
    a.rect(4, 32, 56, 9, wood_c)
    for x in range(5, 59):
        if px.h2(x, 36, 5) > 0.80:
            a.px(x, 34 + (x % 3), mix(CLAY, C("wood"), 0.55))
    # cutting board
    a.rect(9, 31, 30, 12, mix(C("cream"), C("sand"), 0.30))
    a.hline(9, 38, 31, mix(C("cream"), C("white"), 0.5))
    a.hline(9, 38, 42, dk(C("sand"), 0.30))
    a.vline(9, 31, 42, li(C("sand"), 0.20))
    # chef knife on the board
    a.rect(12, 35, 3, 5, C("cocoa"))
    a.poly([(15, 34), (30, 36), (15, 39)], C("silver"))
    a.line((16, 36), (27, 36), mix(C("silver"), C("white"), 0.5))
    # scraps
    for x, y, c in ((20, 40, C("leaf")), (22, 41, C("lime")), (25, 40, C("tomato")),
                    (33, 40, C("leaf")), (36, 39, C("lime")), (30, 42, C("tomato"))):
        a.px(x, y, c)
        a.px(x, y + 1, dk(c, 0.30))
    # prep bowl
    a.ellipse(36, 32, 16, 10, C("silver"))
    a.ellipse(37, 33, 14, 8, mix(C("silver"), C("steel_light"), 0.5))
    a.ellipse(39, 34, 10, 5, C("teal"))
    a.hline(39, 47, 33, C("white"))
    # front cabinet
    a.rect(3, 44, 58, 38, wood_c)
    a.hline(3, 60, 44, li(wood_c, 0.35))
    a.hline(3, 60, 45, li(wood_c, 0.15))
    for x0 in (8, 36):
        a.rect(x0, 49, 20, 24, mix(wood_c, CLAY, 0.35))
        a.frame(x0, 49, 20, 24, li(wood_c, 0.28), dk(wood_c, 0.35))
        a.rect(x0 + 8, 58, 4, 2, C("silver"))
    a.rect(3, 76, 58, 4, mix(CLAY, C("wood"), 0.45))
    a.hline(3, 60, 76, li(CLAY, 0.25))
    plinth(a, 80, mix(CLAY, C("wood"), 0.55), 12)
    return px.finish(a, ["ink", "black", "steel", "steel_light", "silver", "white", "cream",
                         "sand", "ivory", "clay", "wood", "cocoa"])


def new_station_steamer():
    a = Art(T, 120)
    for i, cx in enumerate((19, 30, 41)):
        a.steam(cx, 0, 20 - i * 2, C("white"), C("steam"), seed=i, width=3, phase=i * 1.4)
    # three stacked bamboo baskets
    for idx, (y, h, ins) in enumerate(((14, 30, 1), (44, 26, 2), (70, 20, 3))):
        x0, x1 = 4 + ins, 59 - ins
        a.rrect(x0, y, x1 - x0 + 1, h, CLAY, 5)
        a.hline(x0 + 4, x1 - 4, y + 1, mix(C("cream"), CLAY, 0.45))
        a.hline(x0 + 4, x1 - 4, y + 2, li(CLAY, 0.30))
        for by in range(y + 6, y + h - 3, 6):
            a.hline(x0 + 1, x1 - 1, by, dk(CLAY, 0.22))
            a.hline(x0 + 1, x1 - 1, by + 1, mix(CLAY, C("cream"), 0.30))
        for x in range(x0 + 5, x1 - 3, 8):
            a.vline(x, y + 4, y + h - 3, mix(CLAY, C("wood"), 0.30))
        a.hline(x0 + 1, x1 - 1, y + h - 1, C("ink"))
        a.vline(x0, y, y + h - 1, li(CLAY, 0.20))
        a.vline(x1, y, y + h - 1, dk(CLAY, 0.35))
        if idx < 2:
            a.rect(x0 - 2, y + 8, 3, 5, dk(CLAY, 0.35))
            a.rect(x1, y + 8, 3, 5, dk(CLAY, 0.35))
            a.px(x0 - 1, y + 9, li(CLAY, 0.30))
            a.px(x1 + 1, y + 9, li(CLAY, 0.30))
    # lid handle
    a.rect(28, 10, 9, 5, mix(CLAY, C("wood"), 0.45))
    a.hline(28, 36, 10, mix(C("cream"), CLAY, 0.55))
    a.px(32, 11, C("cream"))
    # stove base with burner glow
    base = STEEL_L
    a.rect(4, 90, 56, 4, STEEL)
    a.hline(4, 59, 90, mix(C("silver"), STEEL_L, 0.4))
    a.rect(10, 88, 44, 3, mix(C("flame_deep"), C("ink"), 0.45))
    for x in range(14, 50, 5):
        a.px(x, 88, C("flame"))
        a.px(x + 1, 87, C("amber"))
    plinth(a, 92, base, 28)
    a.rect(6, 93, 52, 3, mix(base, STEEL, 0.35))
    panel(a, 8, 99, 24, 14, base)
    a.screen(10, 101, 20, 9, GLOW, rows=2)
    dial(a, 44, 104, AMBER, 4)
    a.lamp(54, 98, MINT)
    a.vents(38, 112, 18, 4, base)
    a.hline(6, 57, 114, dk(base, 0.25))
    return px.finish(a, ["ink", "clay", "wood", "cream", "sand", "ivory", "steel", "steel_light",
                         "silver", "mint", "teal", "flame"])


def new_station_serve():
    a = Art(T, 104)
    frame_c = mix(STEEL_L, SAND, 0.30)
    # header
    a.rect(3, 2, 58, 13, frame_c)
    a.hline(3, 60, 2, li(frame_c, 0.40))
    a.rect(10, 4, 44, 9, mix(TEAL, C("slate"), 0.30))
    a.hline(13, 50, 7, GLOW)
    a.hline(13, 42, 9, MINT)
    a.hline(13, 46, 10, mix(TEAL, GLOW, 0.35))
    a.px(52, 6, AMBER)
    a.px(6, 7, MINT)
    # hatch: dark interior, warm back wall
    a.rect(4, 17, 56, 48, mix(STEEL, C("slate"), 0.45))
    a.rect(7, 20, 50, 42, mix(C("ink"), TEAL, 0.30))
    a.vgrad(8, 21, 48, 40, mix(C("amber"), C("cocoa"), 0.45), mix(C("ink"), TEAL, 0.55))
    # shelf backsplash inside
    a.hline(9, 54, 26, mix(C("amber"), C("flame"), 0.30))
    a.hline(9, 54, 27, mix(C("cocoa"), C("ink"), 0.30))
    # plate with bun on the sill
    a.ellipse(16, 44, 32, 11, C("silver"))
    a.ellipse(18, 45, 28, 9, mix(C("silver"), C("steel_light"), 0.55))
    a.hline(20, 43, 45, C("white"))
    a.ellipse(23, 37, 18, 11, mix(C("cream"), C("sand"), 0.25))
    a.ellipse(24, 38, 16, 9, C("cream"))
    a.ellipse(26, 38, 12, 6, C("ivory"))
    a.hline(27, 36, 40, mix(C("cream"), C("sand"), 0.55))
    a.hline(34, 39, 45, mix(C("cream"), C("sand"), 0.55))
    # neon rim (2px) around the hatch
    a.frame(4, 17, 56, 48, GLOW, mix(GLOW, TEAL, 0.35), t=1)
    a.hline(5, 58, 18, C("cyan"))
    a.hline(5, 58, 17, mix(GLOW, C("white"), 0.35))
    a.rect(4, 17, 2, 48, mix(GLOW, TEAL, 0.25))
    a.rect(58, 17, 2, 48, mix(GLOW, TEAL, 0.25))
    # sill
    a.rect(2, 64, 60, 10, mix(STEEL_L, SAND, 0.50))
    a.hline(2, 61, 64, li(frame_c, 0.50))
    a.hline(2, 61, 65, GLOW)
    a.hline(2, 61, 74, dk(frame_c, 0.30))
    # front counter: wood with a steel rail
    a.rect(3, 74, 58, 24, mix(CLAY, SAND, 0.35))
    a.hline(3, 60, 74, li(CLAY, 0.30))
    a.rect(6, 79, 52, 2, mix(CLAY, C("wood"), 0.45))
    a.rect(6, 79, 52, 1, li(CLAY, 0.25))
    for tx, tw in ((9, 15), (34, 15)):
        a.rect(tx, 82, tw, 11, C("ivory"))
        a.hline(tx, tx + tw - 1, 82, C("white"))
        a.hline(tx, tx + tw - 1, 92, mix(C("sand"), C("ink"), 0.30))
        a.hline(tx + 2, tx + tw - 3, 85, mix(C("sand"), C("ink"), 0.35))
        a.hline(tx + 2, tx + tw - 5, 88, mix(C("sand"), C("ink"), 0.20))
        a.px(tx + 2, 81, C("steel"))
        a.px(tx + tw - 3, 81, C("steel"))
    a.vline(3, 74, 97, li(CLAY, 0.20))
    a.vline(60, 74, 97, dk(CLAY, 0.25))
    plinth(a, 98, mix(CLAY, C("wood"), 0.50), 6)
    return px.finish(a, ["ink", "steel", "steel_light", "silver", "sand", "ivory", "cream",
                         "clay", "wood", "amber", "flame", "glow"])


def new_item_stardust():
    a = Art(28, 28)

    def shard(x, y, w, h, lean=0):
        a.poly([(x, y), (x + w, y), (x + w + lean, y + h), (x + w // 2 + lean, y + h + 3), (x + lean, y + h)], C("glass"))
        a.poly([(x + 1, y + 1), (x + w // 2, y + 1), (x + w // 2 + lean, y + h + 1), (x + 1 + lean, y + h)], mix(C("glass"), C("glow"), 0.35))
        a.line((x + w // 2, y + 2), (x + w // 2 + lean, y + h + 1), C("white"))

    shard(11, 4, 8, 16)
    shard(6, 10, 6, 11, -1)
    shard(18, 9, 6, 12, 1)
    # base glow
    a.ellipse(4, 22, 20, 5, mix(C("glow"), C("teal"), 0.35))
    a.ellipse(7, 22, 14, 3, C("glow"))
    for x, y in ((9, 24), (14, 23), (19, 24)):
        a.px(x, y, C("white"))
    # sparkles
    for x, y in ((4, 6), (23, 5), (24, 16), (3, 17)):
        a.px(x, y, C("spark"))
        a.px(x + 1, y, mix(C("spark"), C("white"), 0.5))
    a.px(14, 2, C("spark"))
    return px.finish(a, ["ink", "glass", "glow", "teal", "white", "spark", "mint", "steel_light"])


def new_item_meat_cut():
    a = Art(28, 28)
    for cx, cy, w, h in ((4, 13, 10, 9), (14, 14, 10, 8), (8, 5, 10, 8)):
        a.rect(cx, cy, w, h, mix(C("tomato"), C("leather"), 0.45))
        a.rect(cx, cy, w, 3, mix(C("tomato"), C("cream"), 0.20))
        a.hline(cx, cx + w - 1, cy, mix(C("tomato"), C("blush"), 0.45))
        a.hline(cx, cx + w - 1, cy + h - 1, C("ink"))
        a.vline(cx, cy, cy + h - 1, mix(C("tomato"), C("blush"), 0.30))
        a.vline(cx + w - 1, cy, cy + h - 1, mix(C("leather"), C("ink"), 0.30))
        a.px(cx + 2, cy + 4, C("cream"))
        a.px(cx + 5, cy + 5, C("blush"))
        a.px(cx + 3, cy + 6, C("cream"))
    a.hline(4, 23, 23, mix(C("leather"), C("ink"), 0.35))
    a.px(6, 24, C("tomato"))
    a.px(20, 24, C("tomato"))
    return px.finish(a, ["ink", "tomato", "leather", "cocoa", "cream", "blush", "wine", "sand"])


def new_item_veg():
    a = Art(28, 28)
    # scalloped outer leaves
    for cx, cy, w, h in ((3, 8, 10, 12), (15, 8, 10, 12), (8, 4, 11, 10), (10, 13, 10, 10)):
        a.ellipse(cx, cy, w, h, C("leaf"))
    a.ellipse(5, 7, 17, 16, mix(C("leaf"), C("lime"), 0.35))
    a.ellipse(8, 9, 13, 12, C("lime"))
    a.ellipse(10, 11, 9, 7, mix(C("lime"), C("cream"), 0.35))
    a.line((14, 6), (14, 20), dk(C("leaf"), 0.25))
    a.line((7, 12), (13, 9), dk(C("leaf"), 0.10))
    a.line((15, 9), (21, 13), dk(C("leaf"), 0.10))
    a.px(12, 12, C("cream"))
    a.px(16, 14, C("cream"))
    a.px(13, 16, mix(C("cream"), C("mint"), 0.4))
    a.hline(9, 18, 23, dk(C("leaf"), 0.40))
    return px.finish(a, ["ink", "leaf", "lime", "cream", "mint", "sand"])
