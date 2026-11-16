p = "tests/_audit.py"
s = open(p, encoding="utf-8").read()
s = s.replace('pal = {tuple(v) for v in json.load(open("data/palette.json", encoding="utf-8"))["names"].values()}',
'''def _rgb(v):
    if isinstance(v, str):
        v = v.lstrip("#")
        return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))
    return tuple(v)


pal = {_rgb(v) for v in json.load(open("data/palette.json", encoding="utf-8"))["names"].values()}''')
open(p, "w", encoding="utf-8").write(s)

h = "tools/pixel/chef_art.py"
t = open(h, encoding="utf-8").read()
t = t.replace("a.vline(px, bob + 8, bob + 11, mix(IVORY, SAND, 0.75))", "a.vline(px, bob + 9, bob + 11, mix(IVORY, SAND, 0.45))")
open(h, "w", encoding="utf-8").write(t)
print("ok")
