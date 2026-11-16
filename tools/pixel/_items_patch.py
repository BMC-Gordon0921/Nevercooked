import re

p = "tools/pixel/make_items.py"
s = open(p, encoding="utf-8").read()

NEW = {}

NEW["item_stardust"] = '''def item_stardust(a):
    a.ellipse(4, 20, 20, 6, mix(TEAL, C("ink"), 0.55))
    a.poly([(14, 3), (21, 13), (18, 24), (10, 24), (8, 14)], TEAL)
    a.poly([(13, 6), (17, 12), (15, 21), (11, 19), (11, 12)], GLASS)
    a.poly([(17, 13), (19, 21), (16, 23)], mix(TEAL, C("mint"), 0.35))
    a.poly([(7, 13), (11, 17), (10, 24), (5, 22)], mix(TEAL, STEEL_L, 0.25))
    a.poly([(21, 15), (25, 19), (22, 24), (19, 22)], mix(TEAL, MINT, 0.30))
    a.px(12, 9, C("white"))
    a.px(13, 8, C("white"))
    a.px(15, 14, C("white"))
    for x, y in ((6, 8), (22, 7), (19, 3)):
        a.px(x, y, AMBER)
        a.px(x - 1, y, mix(AMBER, C("white"), 0.5))
        a.px(x + 1, y, mix(AMBER, C("white"), 0.5))
        a.px(x, y - 1, mix(AMBER, C("white"), 0.5))
        a.px(x, y + 1, mix(AMBER, C("white"), 0.5))
    a.hline(5, 22, 24, mix(TEAL, C("ink"), 0.45))
    return px.finish(a, ["ink", "teal", "mint", "glass", "white", "amber", "steel_light", "steel", "sand", "fog"])


'''

NEW["item_dough"] = '''def item_dough(a):
    a.ellipse(2, 12, 24, 13, mix(CREAM, SAND, 0.65))
    a.ellipse(3, 12, 22, 11, mix(CREAM, SAND, 0.35))
    a.ellipse(5, 12, 18, 8, CREAM)
    a.ellipse(7, 13, 13, 5, IVORY)
    a.hline(9, 15, 16, mix(CREAM, SAND, 0.55))
    a.hline(7, 20, 18, mix(CREAM, SAND, 0.75))
    a.hline(4, 23, 22, mix(CREAM, SAND, 0.55))
    for x, y in ((10, 10), (16, 11), (19, 14), (6, 15), (21, 17), (12, 19)):
        a.px(x, y, C("white"))
    return px.finish(a, ["ink", "cream", "ivory", "white", "sand", "fog"])


'''

NEW["item_bun"] = '''def item_bun(a):
    a.ellipse(3, 6, 22, 18, CREAM)
    a.ellipse(4, 7, 20, 16, IVORY)
    a.ellipse(6, 7, 14, 10, C("white"))
    for sx, sy in ((9, 13), (13, 11), (17, 13)):
        a.line((sx, sy), (sx + 1, sy + 7), mix(CREAM, SAND, 0.55))
    a.line((14, 9), (14, 19), mix(CREAM, SAND, 0.65))
    a.hline(9, 18, 20, mix(CREAM, SAND, 0.60))
    a.hline(5, 22, 23, mix(CREAM, SAND, 0.55))
    a.px(14, 5, AMBER)
    a.px(15, 5, mix(AMBER, C("white"), 0.4))
    return px.finish(a, ["ink", "cream", "ivory", "white", "sand", "fog", "amber"])


'''

NEW["item_meat_cut"] = '''def item_meat_cut(a):
    a.ellipse(3, 19, 22, 7, mix(TOMATO, C("ink"), 0.45))
    for x0, y0, w, h, tone in ((5, 12, 13, 8, mix(TOMATO, C("blush"), 0.30)),
                               (10, 7, 13, 8, mix(TOMATO, C("blush"), 0.50)),
                               (13, 15, 11, 7, mix(TOMATO, C("blush"), 0.15))):
        a.rrect(x0, y0, w, h, tone, 3)
        a.hline(x0 + 1, x0 + w - 2, y0, mix(tone, C("white"), 0.35))
        a.hline(x0 + 1, x0 + w - 2, y0 + h - 1, mix(tone, C("ink"), 0.30))
    a.line((7, 15), (15, 14), CREAM)
    a.line((12, 10), (20, 9), CREAM)
    a.line((15, 18), (22, 17), CREAM)
    a.px(9, 13, mix(TOMATO, C("blush"), 0.65))
    a.px(18, 11, mix(TOMATO, C("blush"), 0.65))
    return px.finish(a, ["ink", "tomato", "blush", "cream", "sand", "leather", "wood", "fog", "ivory"])


'''


def replace_func(src, name, body):
    pat = re.compile(r"^def %s\(.*?(?=^def |^ITEMS|\Z)" % name, re.S | re.M)
    if not pat.search(src):
        return src.replace("\nITEMS = {", "\n" + body + "\nITEMS = {", 1)
    return pat.sub(body, src, count=1)


for name, body in NEW.items():
    s = replace_func(s, name, body)

s = s.replace('"stardust": lambda a: new_item_stardust(),', '"stardust": item_stardust,')
s = s.replace('"meat_cut": lambda a: new_item_meat_cut(),', '"meat_cut": item_meat_cut,')
s = s.replace("from tools.pixel._blocks import new_item_stardust, new_item_meat_cut, new_item_veg",
              "from tools.pixel._blocks import new_item_veg")
s = s.replace("from tools.pixel.pxlib import Art, col, dk, li, mix", "from tools.pixel.pxlib import Art, col, dk, li, mix")
open(p, "w", encoding="utf-8").write(s)
print("patched")
